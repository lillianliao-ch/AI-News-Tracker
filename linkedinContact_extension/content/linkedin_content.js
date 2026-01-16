// LinkedIn Content Script - Candidate Analyzer

console.log('LinkedIn-Atlas Analyzer: Content script loaded');

// Initialize when page is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

function init() {
    console.log('Initializing LinkedIn analyzer');
    // Re-enable page button injection for fixed bottom-left button
    injectAnalyzeButton();
    setupMessageListener();
}

// Inject "Analyze with AI" button into LinkedIn profile page
function injectAnalyzeButton() {
    console.log('Starting button injection...');

    // Wait for profile section to load with multiple selector attempts
    const checkInterval = setInterval(() => {
        // Try multiple possible containers (LinkedIn changes their structure frequently)
        const profileSection =
            document.querySelector('main.scaffold-layout__main') ||
            document.querySelector('main') ||
            document.querySelector('.scaffold-layout__main') ||
            document.querySelector('.pv-top-card') ||
            document.querySelector('[data-view-name="profile-view"]') ||
            document.querySelector('.profile-background-image') ||
            document.querySelector('section.artdeco-card');

        console.log('Checking for container...', profileSection ? 'Found!' : 'Not found');

        if (profileSection && !document.getElementById('ai-analyze-button')) {
            clearInterval(checkInterval);
            console.log('Container found, creating button...');
            createAnalyzeButton(profileSection);
        }
    }, 1000);

    // Stop checking after 15 seconds
    setTimeout(() => {
        clearInterval(checkInterval);
        console.log('Button injection timeout - container not found');
    }, 15000);
}

function createAnalyzeButton(container) {
    console.log('Creating analyze button in container:', container.className);

    const button = document.createElement('button');
    button.id = 'ai-analyze-button';
    button.className = 'ai-analyze-btn';

    // Add inline styles to ensure visibility
    button.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 20px;
      background: white;
      color: #667eea;
      border: none;
      border-radius: 6px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      transition: all 0.3s ease;
    `;

    button.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8 0C3.6 0 0 3.6 0 8s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm0 14c-3.3 0-6-2.7-6-6s2.7-6 6-6 6 2.7 6 6-2.7 6-6 6z"/>
        <path d="M8 4c-.6 0-1 .4-1 1v2H5c-.6 0-1 .4-1 1s.4 1 1 1h2v2c0 .6.4 1 1 1s1-.4 1-1V9h2c.6 0 1-.4 1-1s-.4-1-1-1H9V5c0-.6-.4-1-1-1z"/>
      </svg>
      <span>Analyze with AI</span>
    `;

    button.addEventListener('click', handleAnalyzeClick);

    // Add hover effect
    button.addEventListener('mouseenter', () => {
        button.style.transform = 'translateY(-2px)';
        button.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        button.style.background = '#f8f9ff';
    });

    button.addEventListener('mouseleave', () => {
        if (!button.disabled) {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
            button.style.background = 'white';
        }
    });

    // Insert button at the top of the profile
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'ai-analyze-container';

    // Add inline styles to container
    buttonContainer.appendChild(button);

    // Fixed position in bottom-left corner, always visible
    buttonContainer.style.cssText = `
    position: fixed !important;
    bottom: 20px !important;
    left: 20px !important;
    z-index: 999999 !important;
    margin: 0 !important;
    padding: 12px !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
  `;

    document.body.appendChild(buttonContainer);
    console.log('Button inserted as fixed position in bottom-left corner');

    console.log('Analyze button injected successfully!');
}

// Handle analyze button click
async function handleAnalyzeClick(event) {
    const button = event.currentTarget;

    // Prevent multiple clicks
    if (button.disabled) return;

    button.disabled = true;
    button.classList.add('loading');
    button.innerHTML = `
    <span class="spinner"></span>
    <span>Sending to Atlas...</span>
  `;

    try {
        const currentUrl = window.location.href;
        console.log('Sending to Atlas Side Chat:', currentUrl);

        // Create prompt
        const prompt = `Please analyze this LinkedIn page: ${currentUrl}

Visit the page and provide insights about the person or content.`;

        // Send to background.js to forward to Atlas Side Chat
        chrome.runtime.sendMessage({
            type: 'SEND_PROMPT_TO_ATLAS',
            prompt: prompt
        }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error:', chrome.runtime.lastError);
                showError('Failed to communicate with extension');
                resetButton(button);
            } else if (response && response.success) {
                button.classList.remove('loading');
                button.classList.add('success');
                button.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M13.5 2.5l-7 7-3-3L2 8l4.5 4.5L15 4z"/>
          </svg>
          <span>Sent to Atlas!</span>
        `;
                setTimeout(() => resetButton(button), 3000);
            } else {
                showError(response?.error || 'Failed to send to Atlas');
                resetButton(button);
            }
        });

    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
        resetButton(button);
    }
}

// Extract candidate information from LinkedIn profile page
function extractCandidateData() {
    const data = {
        profileUrl: window.location.href,
        name: '',
        title: '',
        company: '',
        location: '',
        summary: ''
    };

    try {
        // Extract name - try multiple selectors
        const nameSelectors = [
            'h1.text-heading-xlarge',
            '.pv-text-details__left-panel h1',
            '.pv-top-card--list li:first-child',
            '[class*="top-card"] h1',
            'h1'
        ];

        for (const selector of nameSelectors) {
            const el = document.querySelector(selector);
            if (el && el.textContent.trim()) {
                data.name = el.textContent.trim();
                break;
            }
        }

        // Extract title - try multiple selectors
        const titleSelectors = [
            '.text-body-medium.break-words',
            '.pv-text-details__left-panel .text-body-medium',
            '.pv-top-card--list-bullet li:first-child',
            '[class*="top-card"] .text-body-medium'
        ];

        for (const selector of titleSelectors) {
            const el = document.querySelector(selector);
            if (el && el.textContent.trim() && !el.textContent.includes('联系方式')) {
                data.title = el.textContent.trim();
                break;
            }
        }

        // Extract company from title if it contains "at"
        if (data.title && data.title.includes(' at ')) {
            const parts = data.title.split(' at ');
            data.title = parts[0].trim();
            data.company = parts[1].trim();
        }

        // Extract location
        const locationSelectors = [
            '.text-body-small.inline.t-black--light.break-words',
            '.pv-text-details__left-panel .text-body-small',
            '.pv-top-card--list-bullet li:last-child'
        ];

        for (const selector of locationSelectors) {
            const el = document.querySelector(selector);
            if (el && el.textContent.trim()) {
                data.location = el.textContent.trim();
                break;
            }
        }

        // Extract summary/about
        const summarySelectors = [
            '#about ~ div .inline-show-more-text span[aria-hidden="true"]',
            '.pv-about-section .pv-about__summary-text',
            '[data-field="summary"] .pv-shared-text-with-see-more',
            '.pv-shared-text-with-see-more span[aria-hidden="true"]'
        ];

        for (const selector of summarySelectors) {
            const el = document.querySelector(selector);
            if (el && el.textContent.trim()) {
                data.summary = el.textContent.trim();
                break;
            }
        }

        console.log('Extracted data:', data);

        // Validate that we at least got a name
        if (!data.name) {
            throw new Error('Could not extract candidate name from page');
        }

        return data;

    } catch (error) {
        console.error('Error extracting candidate data:', error);
        throw error;
    }
}

// Reset button to initial state
function resetButton(button) {
    button.disabled = false;
    button.classList.remove('loading', 'success', 'error');
    button.innerHTML = `
        < svg width = "16" height = "16" viewBox = "0 0 16 16" fill = "currentColor" >
      <path d="M8 0C3.6 0 0 3.6 0 8s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm0 14c-3.3 0-6-2.7-6-6s2.7-6 6-6 6 2.7 6 6-2.7 6-6 6z"/>
      <path d="M8 4c-.6 0-1 .4-1 1v2H5c-.6 0-1 .4-1 1s.4 1 1 1h2v2c0 .6.4 1 1 1s1-.4 1-1V9h2c.6 0 1-.4 1-1s-.4-1-1-1H9V5c0-.6-.4-1-1-1z"/>
    </svg >
        <span>Analyze with AI</span>
    `;
}

// Show success message
function showSuccess(message) {
    showNotification(message, 'success');
}

// Show error message
function showError(message) {
    showNotification(message, 'error');
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.getElementById('ai-analyzer-notification');
    if (existing) {
        existing.remove();
    }

    const notification = document.createElement('div');
    notification.id = 'ai-analyzer-notification';
    notification.className = `ai - notification ai - notification - ${type} `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Listen for messages from background script
function setupMessageListener() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        console.log('LinkedIn content received message:', message.type);

        switch (message.type) {
            case 'TRIGGER_ANALYSIS':
                // Trigger analysis from popup
                triggerAnalysisFromPopup(sendResponse);
                return true; // Keep channel open

            case 'ANALYSIS_COMPLETE':
                handleAnalysisComplete(message.data);
                sendResponse({ success: true });
                break;

            case 'ANALYSIS_ERROR':
                handleAnalysisError(message.error);
                sendResponse({ success: true });
                break;
        }
    });
}

// Trigger analysis when called from popup
async function triggerAnalysisFromPopup(sendResponse) {
    try {
        console.log('Analysis triggered from popup');

        // Extract candidate data
        const candidateData = extractCandidateData();

        if (!candidateData.name) {
            sendResponse({ success: false, error: 'Could not extract candidate information from page' });
            return;
        }

        console.log('Extracted candidate data:', candidateData);

        // Send to background script
        chrome.runtime.sendMessage({
            type: 'ANALYZE_CANDIDATE',
            data: candidateData
        }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error:', chrome.runtime.lastError);
                sendResponse({ success: false, error: 'Failed to start analysis' });
            } else {
                sendResponse(response);
                if (response.success) {
                    showSuccess('Analysis started! Check the ChatGPT Atlas tab.');
                }
            }
        });

    } catch (error) {
        console.error('Error in triggerAnalysisFromPopup:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle analysis completion
function handleAnalysisComplete(data) {
    console.log('Analysis complete:', data);

    const button = document.getElementById('ai-analyze-button');
    if (button) {
        button.classList.remove('loading');
        button.classList.add('success');
        button.innerHTML = `
        < svg width = "16" height = "16" viewBox = "0 0 16 16" fill = "currentColor" >
            <path d="M13.5 2.5l-7 7-3-3L2 8l4.5 4.5L15 4z" />
      </svg >
        <span>Analysis Complete!</span>
    `;

        setTimeout(() => resetButton(button), 3000);
    }

    showSuccess(`Analysis complete! Candidate: ${data.name || 'Unknown'} `);
}

// Handle analysis error
function handleAnalysisError(error) {
    console.error('Analysis error:', error);

    const button = document.getElementById('ai-analyze-button');
    if (button) {
        resetButton(button);
    }

    showError(`Analysis failed: ${error} `);
}
