document.getElementById('startBtn').addEventListener('click', () => {
    const maxPages = parseInt(document.getElementById('maxPages').value, 10);
    chrome.storage.local.set({ isScraping: true, maxPages: maxPages, pagesScraped: 0 }, () => {
        chrome.runtime.sendMessage({ action: "start_scraping" });
        updateStatus("Scraping started...");
    });
});

document.getElementById('stopBtn').addEventListener('click', () => {
    chrome.storage.local.set({ isScraping: false }, () => {
        chrome.runtime.sendMessage({ action: "stop_scraping" });
        updateStatus("Scraping stopped.");
    });
});

function updateStatus(msg) {
    document.getElementById('status').textContent = msg;
}

// Restore status on open
chrome.storage.local.get(['isScraping'], (result) => {
    if (result.isScraping) {
        updateStatus("Scraping in progress...");
    }
});

function checkServerStatus() {
    const dot = document.getElementById('serverDot');
    const text = document.getElementById('serverStatus');

    fetch('http://localhost:5001/health')
        .then(response => {
            if (response.ok) {
                dot.className = "dot connected";
                text.textContent = "Server Connected";
            } else {
                throw new Error('Server error');
            }
        })
        .catch(error => {
            dot.className = "dot disconnected";
            text.textContent = "Server Disconnected";
        });
}

checkServerStatus();
setInterval(checkServerStatus, 5000); // Check every 5 seconds
