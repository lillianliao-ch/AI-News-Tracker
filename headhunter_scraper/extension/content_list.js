chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "scrape_list") {
        console.log("Received scrape_list command");
        scrapeLinks();
        sendResponse({ status: "scraping" });
    } else if (request.action === "go_next_page") {
        console.log("Received go_next_page command");
        goToNextPage();
        sendResponse({ status: "navigating" });
    } else if (request.action === "check_next_page") {
        console.log("Received check_next_page command");
        // Trigger next page logic
        chrome.runtime.sendMessage({ action: "next_page_needed" });
        sendResponse({ status: "checking" });
    }
    return true; // Keep the message channel open for async responses
});

function scrapeLinks() {
    console.log("Starting to scrape links from list page...");
    console.log("Current URL:", window.location.href);

    const links = [];

    // Strategy 1: Find all links in the name column (姓名)
    // Look for links that contain candidate names
    const nameLinks = document.querySelectorAll('a[href*="#candidate/detail"]');
    console.log(`Strategy 1: Found ${nameLinks.length} links with #candidate/detail`);

    nameLinks.forEach((link, index) => {
        const fullUrl = link.href;
        console.log(`  Link ${index + 1}:`, fullUrl);
        links.push(fullUrl);
    });

    // Strategy 2: If no hash links found, try to find links with 'detail' in href
    if (links.length === 0) {
        const detailLinks = document.querySelectorAll('a[href*="detail"]');
        console.log(`Strategy 2 (Fallback): Found ${detailLinks.length} links with 'detail'`);
        detailLinks.forEach((link, index) => {
            if (link.href && link.href.includes('candidate')) {
                console.log(`  Link ${index + 1}:`, link.href);
                links.push(link.href);
            }
        });
    }

    // Strategy 3: Last resort - find all table rows and extract IDs
    if (links.length === 0) {
        console.log("Strategy 3 (Last resort): Trying to extract from table rows...");
        const rows = document.querySelectorAll('tr');
        console.log(`  Found ${rows.length} table rows`);
        const baseUrl = window.location.origin + window.location.pathname;

        rows.forEach((row, rowIndex) => {
            // Look for ID in the row (usually in second column)
            const cells = row.querySelectorAll('td');
            if (cells.length > 1) {
                const idCell = cells[1]; // Assuming ID is in second column
                const idText = idCell.textContent.trim();
                // Check if it looks like an ID (number)
                if (/^\d+$/.test(idText)) {
                    const url = `${baseUrl}#candidate/detail?id=${idText}`;
                    console.log(`  Row ${rowIndex}: Constructed URL from ID ${idText}:`, url);
                    links.push(url);
                }
            }
        });
    }

    // Remove duplicates
    const uniqueLinks = [...new Set(links)];

    console.log(`Total unique links found: ${uniqueLinks.length}`);
    chrome.runtime.sendMessage({ action: "list_data", links: uniqueLinks });
}

function goToNextPage() {
    console.log("Attempting to find and click next page button...");

    let nextBtn = null;

    // Look for the right chevron icon (fa-chevron-right)
    const rightChevron = document.querySelector('i.fa-chevron-right');

    if (rightChevron) {
        // Get the parent <a> tag
        const parentLink = rightChevron.closest('a');
        if (parentLink) {
            // Check if the parent <li> is disabled
            const parentLi = parentLink.closest('li');
            if (parentLi && !parentLi.classList.contains('disabled')) {
                nextBtn = parentLink;
                console.log("Found next page button via fa-chevron-right icon");
            } else {
                console.log("Next page button is disabled (last page reached)");
            }
        }
    }

    if (nextBtn) {
        console.log("Clicking next page button...");
        nextBtn.click();

        // Wait for page to load, then scrape links again
        console.log("Waiting 3 seconds for next page to load...");
        setTimeout(() => {
            console.log("Scraping links from new page...");
            scrapeLinks();
        }, 3000);
    } else {
        console.log("Next page button not found - reached last page or pagination not available");
        chrome.runtime.sendMessage({ action: "stop_scraping" });
    }
}
