// ChatGPT Atlas Content Script - Handles DOM manipulation for Side Chat

console.log('✅ Atlas content script loaded');

let isProcessing = false;
let responseObserver = null;
let lastResponseText = '';
let stableTimer = null;

// Function to simulate user typing
function simulateInput(text) {
    // Try standard textarea first
    const textarea = document.querySelector('textarea[placeholder*="Ask"]') ||
        document.querySelector('textarea[placeholder*="Message"]');

    if (textarea) {
        textarea.value = text;
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        textarea.focus();
        return true;
    }

    // Try ProseMirror div (Side Chat)
    const proseMirror = document.querySelector('#prompt-textarea');
    if (proseMirror) {
        console.log('📝 Found ProseMirror input, simulating text...');
        // Clear existing content
        proseMirror.innerHTML = '';

        // Create paragraph with text
        const p = document.createElement('p');
        p.textContent = text;
        proseMirror.appendChild(p);

        // Dispatch events
        proseMirror.dispatchEvent(new Event('input', { bubbles: true }));
        proseMirror.focus();
        return true;
    }

    return false;
}

// Function to simulate sending
function simulateSend() {
    const sendButton = document.querySelector('button[data-testid="send-button"]') ||
        document.querySelector('button[aria-label*="Send"]');
    if (sendButton) {
        sendButton.click();
        console.log('✅ Send button clicked');
        return true;
    }

    // Try pressing Enter on the input
    const input = document.querySelector('#prompt-textarea') || document.querySelector('textarea');
    if (input) {
        input.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Enter',
            code: 'Enter',
            keyCode: 13,
            which: 13,
            bubbles: true
        }));
        return true;
    }

    return false;
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('📩 Message received in Atlas Content:', request.action); // Debug log

    if (request.action === 'SEND_PROMPT_TO_ATLAS') {
        const { prompt } = request;
        console.log(`📝 Received prompt: ${prompt.substring(0, 50)}...`);

        const success = simulateInput(prompt);

        if (success) {
            setTimeout(() => {
                simulateSend();
                sendResponse({ success: true });

                // Start observing for response
                observeResponse();
            }, 500);
        } else {
            console.error('❌ Could not find input element (textarea or ProseMirror)');
            sendResponse({ success: false, error: 'Input element not found' });
        }

        // Return true to indicate async response
        return true;
    }
});

// Function to register this frame as Atlas
function registerAsAtlas() {
    console.log('🔗 Registering as Atlas instance (Unconditional)...');
    chrome.runtime.sendMessage({
        type: 'ATLAS_REGISTER',
        url: window.location.href
    });
}

// Run registration immediately and periodically
registerAsAtlas();
setInterval(registerAsAtlas, 5000);

// Start monitoring for ChatGPT response using MutationObserver
function observeResponse() {
    console.log('👀 Starting response monitoring...');

    lastResponseText = '';

    // Clean up existing observer
    if (responseObserver) {
        responseObserver.disconnect();
    }

    // Create new observer
    responseObserver = new MutationObserver(() => {
        const blocks = document.querySelectorAll('.markdown');
        if (!blocks.length) return;

        // Get the latest response block
        const latest = blocks[blocks.length - 1];
        const text = latest.innerText.trim();

        if (!text || text === lastResponseText) return;

        lastResponseText = text;
        console.log('📝 Response updated, length:', text.length);

        // Wait 1 second for stability (no changes = GPT finished)
        clearTimeout(stableTimer);
        stableTimer = setTimeout(() => {
            console.log('✅ Response stable, sending to background');

            // Send response back to background
            chrome.runtime.sendMessage({
                type: 'ATLAS_RESPONSE_READY',
                text: lastResponseText
            });

            // Clean up
            responseObserver.disconnect();
            isProcessing = false;

        }, 1000);
    });

    // Start observing
    responseObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Add visual indicator when script is active
function addActiveIndicator() {
    if (document.getElementById('linkedin-atlas-indicator')) return;

    const indicator = document.createElement('div');
    indicator.id = 'linkedin-atlas-indicator';
    indicator.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    background: #10a37f;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    z-index: 10000;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  `;
    indicator.textContent = '🔗 LinkedIn Analyzer Connected';
    document.body.appendChild(indicator);

    // Remove after 3 seconds
    setTimeout(() => {
        indicator.style.opacity = '0';
        indicator.style.transition = 'opacity 0.3s';
        setTimeout(() => indicator.remove(), 300);
    }, 3000);
}

// Show indicator when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addActiveIndicator);
} else {
    addActiveIndicator();
}
