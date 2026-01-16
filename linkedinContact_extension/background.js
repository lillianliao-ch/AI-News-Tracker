// Background Service Worker for LinkedIn-Atlas Candidate Analyzer

console.log('LinkedIn-Atlas Analyzer: Background service worker started');

// Store registered Atlas frames
let atlasInstances = new Set(); // Stores objects: { tabId, frameId }

// Handle Atlas registration
function handleAtlasRegister(sender) {
    console.log('📨 Received ATLAS_REGISTER from:', JSON.stringify(sender));

    // Determine Tab ID (might be absent in Side Panel?)
    const tabId = sender.tab ? sender.tab.id : (sender.id || 'unknown');
    const frameId = sender.frameId;

    if (tabId && frameId !== undefined) {
        console.log(`✅ Registered Atlas instance: Tab ${tabId}, Frame ${frameId}`);

        // Check if ready exists
        const exists = Array.from(atlasInstances).some(i => i.tabId === tabId && i.frameId === frameId);
        if (!exists) {
            atlasInstances.add({ tabId: tabId, frameId: frameId, url: sender.url });
        }
    } else {
        console.warn('⚠️ Received registration but missing Tab ID or Frame ID', sender);
    }
}


// Message handler for communication between content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Background received message:', message.type);

    switch (message.type) {
        case 'ATLAS_REGISTER':
            handleAtlasRegister(sender);
            return false; // No response needed

        case 'SEND_PROMPT_TO_ATLAS':
            handleSendPromptToAtlas(message.prompt, sender, sendResponse);
            return true;

        case 'ATLAS_RESPONSE_READY':
            handleAtlasResponse(message, sendResponse);
            return true;

        case 'SEND_TO_ATLAS_DIRECT':
            handleSendToAtlasDirect(message.url, sender, sendResponse);
            return true;

        case 'SEND_TO_ATLAS':
            handleSendToAtlas(message.data, sender, sendResponse);
            return true; // Keep channel open for async response

        case 'ANALYZE_CANDIDATE':
            handleAnalyzeCandidate(message.data, sender, sendResponse);
            return true; // Keep channel open for async response

        case 'ATLAS_RESPONSE':
            handleAtlasResponse(message.data, sendResponse);
            return true;

        case 'SAVE_TO_STORAGE':
            handleSaveToStorage(message.data, sendResponse);
            return true;

        case 'EXPORT_TO_EXCEL':
            handleExportToExcel(message.data, sendResponse);
            return true;

        case 'GET_STATUS':
            sendResponse({
                success: true,
                atlasCount: atlasInstances.size,
                instances: Array.from(atlasInstances)
            });
            return true;

        default:
            console.warn('Unknown message type:', message.type);
            sendResponse({ success: false, error: 'Unknown message type' });
    }
});

// Handle send prompt to Atlas Side Chat
// Handle send prompt to Atlas Side Chat
async function handleSendPromptToAtlas(prompt, sender, sendResponse) {
    try {
        console.log('=== SEND PROMPT TO ATLAS ===');
        console.log('Prompt:', prompt.substring(0, 100) + '...');

        // Determine target tab and frame
        let targetTabId = sender.tab ? sender.tab.id : null;
        let targetFrameId = null;

        // Strategy 1: Search Global Registry
        // First, prefer one in the SAME tab (iframe scenario)
        let atlasInstance = Array.from(atlasInstances).find(i => i.tabId === targetTabId);

        // If not in same tab, take ANY registered instance (Side Panel scenario)
        if (!atlasInstance && atlasInstances.size > 0) {
            atlasInstance = Array.from(atlasInstances)[0]; // Pick the first one (usually the active one)
            console.log(`✅ Found Atlas in separate tab / panel: Tab ${atlasInstance.tabId} `);
        }

        if (atlasInstance) {
            targetTabId = atlasInstance.tabId;
            targetFrameId = atlasInstance.frameId;
            console.log(`✅ Routing to Atlas: Tab ${targetTabId}, Frame ${targetFrameId} `);
        }

        // Strategy 2: Active Discovery (only works for current tab iframes)
        if (!atlasInstance && targetFrameId === null) {
            console.log('⚠️ No registered frame in cache, attempting active discovery (PING)...');
            try {
                // Broadcast to all frames in the current tab
                const frames = await chrome.scripting.executeScript({
                    target: { tabId: targetTabId, allFrames: true },
                    func: () => {
                        // LOGGING ENABLED
                        const isTop = window === window.top;
                        console.log(`🔍 Probe: Frame ${window.location.href} (Top: ${isTop})`);

                        // Shadow DOM Crawler
                        function findInShadows(root) {
                            if (!root) return null;

                            // Check current root
                            const textarea = root.querySelector('textarea[placeholder*="Ask"]') ||
                                root.querySelector('textarea[placeholder*="Message"]') ||
                                root.querySelector('button[aria-label*="Ask"]') ||
                                root.querySelector('button[data-testid="send-button"]');
                            if (textarea) return root;

                            // Search deeper
                            const allNodes = root.querySelectorAll('*');
                            for (const node of allNodes) {
                                if (node.shadowRoot) {
                                    const found = findInShadows(node.shadowRoot);
                                    if (found) return found;
                                }
                            }
                            return null;
                        }

                        // If top frame, check Shadow DOMs
                        if (isTop) {
                            console.log('🔍 Checking Shadow DOMs in Top Frame...');
                            const foundRoot = findInShadows(document);
                            if (foundRoot) {
                                console.log('✅ FOUND ATLAS IN SHADOW DOM!');
                                return 'SHADOW_DOM';
                            }
                        }

                        // Also check iframes explicitly from top frame to see if we missed any
                        if (isTop) {
                            const iframes = document.querySelectorAll('iframe');
                            console.log(`🔍 Top Frame sees ${iframes.length} iframes: `);
                            iframes.forEach((f, i) => {
                                console.log(`   [${i}]src: ${f.src}, id: ${f.id}, class: ${f.className} `);
                            });
                        }

                        // Standard check (for iframes and top frame)
                        try {
                            const isAtlas = document.querySelector('textarea[placeholder*="Ask"]') ||
                                document.querySelector('textarea[placeholder*="Message"]') ||
                                document.querySelector('button[data-testid="send-button"]') ||
                                document.querySelector('#prompt-textarea'); // User identified selector

                            if (isAtlas) {
                                console.log('✅ FOUND ATLAS FRAME HERE! (Selector matched)');
                                return true;
                            }
                            return false;
                        } catch (e) {
                            console.error('Probe error:', e);
                            return false;
                        }
                    }
                });

                // Handle findings
                const shadowFrame = frames.find(f => f.result === 'SHADOW_DOM');
                if (shadowFrame) {
                    console.log('🎯 Discovery: Atlas is in SHADOW DOM of Main Frame!');
                    sendResponse({
                        success: false,
                        error: 'ATLAS_IN_SHADOW_DOM',
                        message: 'Atlas found in Shadow DOM. Extension will attempt direct access.'
                    });
                    return;
                }

                // Find the frame that returned true
                const atlasFrameResult = frames.find(f => f.result === true);
                if (atlasFrameResult) {
                    targetFrameId = atlasFrameResult.frameId;
                    console.log(`✅ Discovered Atlas frame via injection: Frame ${targetFrameId} `);

                    // Register it for future use (in global registry)
                    atlasInstances.add({ tabId: targetTabId, frameId: targetFrameId });
                }
            } catch (e) {
                console.warn('Active discovery failed:', e);
            }
        }

        // Strategy 3: Fallback to searching standalone tabs (if no registry and no injection)
        if (!targetFrameId && targetFrameId !== 0 && targetTabId) {
            console.log('Searching for standalone Atlas tabs...');
            const tabs = await chrome.tabs.query({
                url: ['https://chat.openai.com/*', 'https://chatgpt.com/*']
            });
            if (tabs.length > 0) {
                targetTabId = tabs[0].id;
                targetFrameId = 0;
                console.log(`Found standalone Atlas tab: ${targetTabId} `);
            }
        }

        if (!targetFrameId && targetFrameId !== 0) {
            console.error('❌ No Atlas instance found after all strategies');
            sendResponse({
                success: false,
                error: 'Could not connect to ChatGPT Atlas. Please make sure the Side Chat is open and loaded.'
            });
            return;
        }

        // Send message to specific frame
        console.log(`📤 Sending to Tab ${targetTabId}, Frame ${targetFrameId} `);
        const msgOptions = { frameId: targetFrameId };

        chrome.tabs.sendMessage(targetTabId, {
            action: 'SEND_PROMPT_TO_ATLAS',
            prompt: prompt
        }, msgOptions, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error sending to Atlas:', chrome.runtime.lastError);
                // Remove dead instance from registry (simplified)
                // atlasInstances cleanup would require finding the object, skipping for now to avoid errors

                sendResponse({
                    success: false,
                    error: 'Communication failed. Please reload the page and try again.'
                });
            } else {
                console.log('✅ Prompt sent successfully!');
                sendResponse({ success: true });
            }
        });

    } catch (error) {
        console.error('Error in handleSendPromptToAtlas:', error);
        sendResponse({ success: false, error: 'Internal error: ' + error.message });
    }
}

// Handle send to Atlas directly with just URL (simplified - just open ChatGPT)
async function handleSendToAtlasDirect(linkedinUrl, sender, sendResponse) {
    try {
        console.log('=== OPENING CHATGPT ===');
        console.log('LinkedIn URL:', linkedinUrl);

        // Simply open ChatGPT in a new tab
        // User can manually paste the URL or we can put it in the URL as a parameter
        const chatgptUrl = `https://chatgpt.com/?q=${encodeURIComponent('Please analyze this LinkedIn page: ' + linkedinUrl)}`;

        console.log('Opening ChatGPT URL:', chatgptUrl);

        const newTab = await chrome.tabs.create({
            url: chatgptUrl,
            active: true
        });

        console.log('ChatGPT tab created:', newTab.id);
        sendResponse({ success: true, atlasTabId: newTab.id });

    } catch (error) {
        console.error('Error in handleSendToAtlasDirect:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle send to Atlas directly (simplified version)
async function handleSendToAtlas(candidateData, sender, sendResponse) {
    try {
        console.log('Sending directly to Atlas:', candidateData);

        // Get prompt template from storage
        const config = await chrome.storage.sync.get(['promptTemplate']);
        const template = config.promptTemplate || getDefaultPromptTemplate();

        // Fill template with candidate data
        const prompt = fillPromptTemplate(template, candidateData);

        // Find or create ChatGPT Atlas tab
        const atlasTab = await findOrCreateAtlasTab();

        // Send prompt to Atlas content script
        chrome.tabs.sendMessage(atlasTab.id, {
            type: 'SEND_PROMPT',
            prompt: prompt
        }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error sending to Atlas:', chrome.runtime.lastError);
                sendResponse({ success: false, error: 'Failed to communicate with Atlas' });
            } else {
                sendResponse({ success: true, atlasTabId: atlasTab.id });
            }
        });

    } catch (error) {
        console.error('Error in handleSendToAtlas:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle candidate analysis request from LinkedIn page
async function handleAnalyzeCandidate(candidateData, sender, sendResponse) {
    try {
        console.log('Starting candidate analysis:', candidateData);

        // Get prompt template from storage
        const config = await chrome.storage.sync.get(['promptTemplate']);
        const template = config.promptTemplate || getDefaultPromptTemplate();

        // Fill template with candidate data
        const prompt = fillPromptTemplate(template, candidateData);

        // Find or create ChatGPT Atlas tab
        const atlasTab = await findOrCreateAtlasTab();

        // Store the analysis context
        await chrome.storage.local.set({
            currentAnalysis: {
                candidateData,
                prompt,
                linkedinTabId: sender.tab.id,
                atlasTabId: atlasTab.id,
                timestamp: Date.now()
            }
        });

        // Send prompt to Atlas content script
        chrome.tabs.sendMessage(atlasTab.id, {
            type: 'SEND_PROMPT',
            prompt: prompt
        }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error sending to Atlas:', chrome.runtime.lastError);
                sendResponse({ success: false, error: 'Failed to communicate with Atlas' });
            } else {
                sendResponse({ success: true, atlasTabId: atlasTab.id });
            }
        });

    } catch (error) {
        console.error('Error in handleAnalyzeCandidate:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle response from Atlas
async function handleAtlasResponse(data, sendResponse) {
    try {
        console.log('Received Atlas response');

        // Get current analysis context
        const { currentAnalysis } = await chrome.storage.local.get(['currentAnalysis']);

        if (!currentAnalysis) {
            throw new Error('No active analysis found');
        }

        // Combine candidate data with Atlas analysis
        const completeData = {
            ...currentAnalysis.candidateData,
            aiAnalysis: data.analysis,
            analyzedAt: new Date().toISOString(),
            linkedinUrl: currentAnalysis.candidateData.profileUrl
        };

        // Save to storage
        await saveCandidate(completeData);

        // Export to Excel
        await exportToExcel(completeData);

        // Notify LinkedIn tab
        chrome.tabs.sendMessage(currentAnalysis.linkedinTabId, {
            type: 'ANALYSIS_COMPLETE',
            data: completeData
        });

        // Clear current analysis
        await chrome.storage.local.remove(['currentAnalysis']);

        sendResponse({ success: true });

    } catch (error) {
        console.error('Error in handleAtlasResponse:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Find existing Atlas tab or create new one
async function findOrCreateAtlasTab() {
    const tabs = await chrome.tabs.query({
        url: ['https://chat.openai.com/*', 'https://chatgpt.com/*']
    });

    if (tabs.length > 0) {
        // Use existing tab
        await chrome.tabs.update(tabs[0].id, { active: true });
        return tabs[0];
    } else {
        // Create new tab
        return await chrome.tabs.create({
            url: 'https://chatgpt.com/',
            active: true
        });
    }
}

// Get default prompt template
function getDefaultPromptTemplate() {
    return `Please analyze the following LinkedIn candidate profile and extract key information:

Name: {name}
Current Title: {title}
Company: {company}
Location: {location}
Summary: {summary}

Please provide a structured analysis in JSON format with the following fields:
{
  "name": "Full name",
  "title": "Current job title",
  "company": "Current company",
  "location": "Location",
  "skills": ["skill1", "skill2", "..."],
  "experience_years": "Estimated years of experience",
  "education": "Education background summary",
  "strengths": "Key strengths and highlights",
  "fit_score": "Candidate fit score (1-10)",
  "summary": "Brief professional summary"
}

Please ensure the response is valid JSON.`;
}

// Fill prompt template with candidate data
function fillPromptTemplate(template, data) {
    let filled = template;
    for (const [key, value] of Object.entries(data)) {
        const placeholder = `{${key}}`;
        filled = filled.replace(new RegExp(placeholder, 'g'), value || 'N/A');
    }
    return filled;
}

// Save candidate to storage
async function saveCandidate(candidateData) {
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    const storageKey = `candidates_${today}`;

    const result = await chrome.storage.local.get([storageKey]);
    const candidates = result[storageKey] || [];

    candidates.push(candidateData);

    await chrome.storage.local.set({ [storageKey]: candidates });
    console.log(`Saved candidate to ${storageKey}`);
}

// Export to Excel (placeholder - will be implemented with SheetJS)
async function exportToExcel(candidateData) {
    console.log('Excel export will be implemented with SheetJS library');
    // This will be implemented in the excel_exporter.js utility
}

// Handle save to storage request
async function handleSaveToStorage(data, sendResponse) {
    try {
        await saveCandidate(data);
        sendResponse({ success: true });
    } catch (error) {
        console.error('Error saving to storage:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle export to Excel request
async function handleExportToExcel(data, sendResponse) {
    try {
        await exportToExcel(data);
        sendResponse({ success: true });
    } catch (error) {
        console.error('Error exporting to Excel:', error);
        sendResponse({ success: false, error: error.message });
    }
}
