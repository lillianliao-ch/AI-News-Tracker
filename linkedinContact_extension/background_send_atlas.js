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
