let scrapingState = {
    isScraping: false,
    maxPages: 5,
    pagesScraped: 0,
    candidateQueue: [],
    currentTabId: null
};

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "start_scraping") {
        chrome.storage.local.get(['maxPages'], (result) => {
            scrapingState.maxPages = result.maxPages || 5;
            scrapingState.isScraping = true;
            scrapingState.pagesScraped = 0;
            scrapingState.candidateQueue = [];

            // Get the current active tab to start scraping the list
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (tabs[0]) {
                    scrapingState.listTabId = tabs[0].id;
                    chrome.tabs.sendMessage(tabs[0].id, { action: "scrape_list" }, (response) => {
                        if (chrome.runtime.lastError) {
                            console.error("Connection error:", chrome.runtime.lastError.message);
                            scrapingState.isScraping = false;
                            chrome.storage.local.set({ isScraping: false });
                            console.log("Please refresh the target page and reload the extension.");
                        }
                    });
                }
            });
        });
    } else if (request.action === "stop_scraping") {
        scrapingState.isScraping = false;
    } else if (request.action === "list_data") {
        // Received links from list page
        if (!scrapingState.isScraping) return;

        const newLinks = request.links;
        scrapingState.candidateQueue.push(...newLinks);
        console.log(`Added ${newLinks.length} candidates. Queue size: ${scrapingState.candidateQueue.length}`);

        // If we have candidates, start processing them
        processNextCandidate();

    } else if (request.action === "detail_data") {
        // Received data from detail page
        const candidateData = request.data;
        console.log("Scraped candidate:", candidateData.name);

        // Send to backend
        console.log("DEBUG: Sending data to backend:", candidateData.name);
        fetch('http://localhost:5001/api/save_candidate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(candidateData)
        })
            .then(response => {
                console.log("DEBUG: Fetch response status:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("Backend response:", data);

                // Only close if it's NOT a manual trigger AND not the list tab
                if (!request.isManual && sender.tab.id !== scrapingState.listTabId) {
                    console.log("Closing tab:", sender.tab.id);
                    chrome.tabs.remove(sender.tab.id);
                } else {
                    console.log("Keeping tab open (Manual trigger or List tab)");
                }

                sendResponse({ status: "success", data: data });

                // Process next
                setTimeout(processNextCandidate, 1000);
            })
            .catch(err => {
                console.error("Error sending to backend:", err);
                sendResponse({ status: "error", error: err.toString() });
                // Even if error, we might want to close? Or keep open for debug?
                // Let's keep open if error to see what happened
            });


    } else if (request.action === "next_page_needed") {
        if (scrapingState.pagesScraped < scrapingState.maxPages) {
            scrapingState.pagesScraped++;
            chrome.tabs.sendMessage(scrapingState.listTabId, { action: "go_next_page" });
        } else {
            console.log("Max pages reached.");
            scrapingState.isScraping = false;
            chrome.storage.local.set({ isScraping: false });
        }
    }
    return true; // Keep channel open for async response
});

function processNextCandidate() {
    if (!scrapingState.isScraping) return;

    if (scrapingState.candidateQueue.length > 0) {
        const nextUrl = scrapingState.candidateQueue.shift();
        chrome.tabs.create({ url: nextUrl, active: true }, (tab) => {
            // The content script in the new tab will trigger automatically
            // We store the tab ID if needed, but for now we rely on message passing
        });
    } else {
        // Queue is empty, check if we need to go to next page
        if (scrapingState.listTabId) {
            chrome.tabs.sendMessage(scrapingState.listTabId, { action: "check_next_page" }, (response) => {
                if (chrome.runtime.lastError) {
                    console.log("Error sending check_next_page:", chrome.runtime.lastError.message);
                }
            });
        } else {
            console.error("List tab ID not found");
            scrapingState.isScraping = false;
        }
    }
}
