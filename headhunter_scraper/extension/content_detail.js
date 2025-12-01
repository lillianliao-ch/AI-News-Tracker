// Debug Mode: Set to true to prevent auto-closing tabs and enable verbose logging
const DEBUG_MODE = false;

let hasInitialized = false;
let urlCheckInterval = null;

function initializeExtension() {
    // Prevent double initialization
    if (hasInitialized) {
        console.log("Headhunter Scraper: Already initialized, skipping.");
        return;
    }

    // Check if we are on a detail page
    const currentUrl = window.location.href;
    console.log("Headhunter Scraper: Current URL:", currentUrl);

    if (!currentUrl.includes('candidate/detail')) {
        console.log("Headhunter Scraper: Not a candidate detail page, skipping.");
        return;
    }

    console.log("Headhunter Scraper: Initializing extension on detail page...");
    hasInitialized = true;

    // Stop URL polling once initialized
    if (urlCheckInterval) {
        clearInterval(urlCheckInterval);
        urlCheckInterval = null;
    }

    // Always add the manual trigger button for debugging
    addManualTriggerButton();

    // In debug mode, we don't auto-scrape immediately.
    // We wait for the user to click the button.
    if (!DEBUG_MODE) {
        console.log("Headhunter Scraper: Waiting 5 seconds before automatic scraping...");
        setTimeout(() => {
            console.log("Headhunter Scraper: Starting automatic scraping...");
            scrapeDetail();
        }, 5000); // Increased from 3000 to 5000ms to allow more time for page load
    } else {
        console.log("Headhunter Scraper: DEBUG_MODE is ON. Auto-scrape disabled. Please click the '手动抓取数据' button.");
    }
}

// Monitor URL changes for SPA navigation
function checkUrlAndInitialize() {
    const currentUrl = window.location.href;
    if (currentUrl.includes('candidate/detail') && !hasInitialized) {
        console.log("Headhunter Scraper: Detail page detected, initializing...");
        initializeExtension();
    }
}

// Start polling for URL changes (important for new tabs created by chrome.tabs.create)
console.log("Headhunter Scraper: Starting URL monitoring...");
urlCheckInterval = setInterval(checkUrlAndInitialize, 200); // Check every 200ms

// Initial check
checkUrlAndInitialize();

// For SPA: Monitor hash changes (for navigation within same tab)
window.addEventListener('hashchange', () => {
    console.log("Headhunter Scraper: Hash changed to:", window.location.hash);
    hasInitialized = false; // Reset for new page
    checkUrlAndInitialize();
});

// Stop polling after 10 seconds to avoid infinite checking
setTimeout(() => {
    if (urlCheckInterval) {
        console.log("Headhunter Scraper: Stopping URL monitoring after 10 seconds.");
        clearInterval(urlCheckInterval);
        urlCheckInterval = null;
    }
}, 10000);

function addManualTriggerButton() {
    if (document.getElementById('manual-scrape-button')) return;

    const button = document.createElement('button');
    button.id = 'manual-scrape-button';
    button.textContent = '手动抓取数据 (Debug)';
    Object.assign(button.style, {
        position: 'fixed', top: '80px', right: '20px', zIndex: '999999',
        backgroundColor: '#d32f2f', color: 'white', border: 'none',
        padding: '12px 20px', borderRadius: '4px', cursor: 'pointer',
        fontWeight: 'bold', boxShadow: '0 4px 8px rgba(0,0,0,0.2)'
    });

    button.addEventListener('click', () => {
        console.log("Manual scrape triggered");
        scrapeDetail(null, true);
    });

    document.body.appendChild(button);
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "scrape_detail") {
        scrapeDetail(sendResponse);
        return true;
    }
});

async function scrapeDetail(sendResponse, isManualTrigger = false) {
    console.log("Starting scrape...");

    // --- 0. Reveal Hidden Info (Phone/Email) ---
    // Look for "查看" buttons next to Phone/Email labels
    const viewButtons = Array.from(document.querySelectorAll('a, span, button')).filter(el => el.innerText.trim() === '查看');

    if (viewButtons.length > 0) {
        console.log(`Found ${viewButtons.length} 'View' buttons. Clicking them...`);

        const clickPromises = viewButtons.map(btn => {
            return new Promise(resolve => {
                btn.click();
                // Check if the text changes or element is removed (indicating data revealed)
                const checkInterval = setInterval(() => {
                    if (btn.innerText.trim() !== '查看' || !document.body.contains(btn)) {
                        clearInterval(checkInterval);
                        resolve();
                    }
                }, 100);
                // Timeout after 2 seconds to prevent hanging
                setTimeout(() => {
                    clearInterval(checkInterval);
                    resolve();
                }, 2000);
            });
        });

        await Promise.all(clickPromises);
        // Extra wait to ensure DOM settles and any animations finish
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    const data = { url: window.location.href };

    // --- Extract Active Status (e.g., "2天前联系") ---
    // Look for elements that might contain activity status
    let activeStatus = '';
    const statusElements = Array.from(document.querySelectorAll('span, div')).filter(el => {
        const text = el.innerText.trim();
        return text.includes('天前') || text.includes('小时前') || text.includes('分钟前') || text.includes('刚刚');
    });
    if (statusElements.length > 0) {
        activeStatus = statusElements[0].innerText.trim();
    }
    data.active_status = activeStatus;

    // --- 1. Extract Name ---
    // Strategy: The name is usually displayed next to the ID (e.g., #1255022 王熙诚).
    // We will look for the element containing the ID pattern.
    const idRegex = /#\d{6,}/;

    // Search in common header tags first
    let nameFound = false;
    const headers = document.querySelectorAll('h1, h2, h3, .candidate-name, span');

    for (let el of headers) {
        const text = el.innerText.trim();
        if (idRegex.test(text)) {
            // Found the ID. The name is likely in this text or a child/sibling.
            // Example text: "#1255022 王熙诚"
            // We want to extract "王熙诚".
            // Remove the ID and any icons/extra text.
            const parts = text.split(/\s+/);
            // Assuming format "#ID Name ..."
            const idIndex = parts.findIndex(p => p.startsWith('#'));
            if (idIndex !== -1 && parts[idIndex + 1]) {
                data.name = parts[idIndex + 1];
                // Clean up any trailing punctuation or status text if attached
                data.name = data.name.replace(/[^\u4e00-\u9fa5a-zA-Z]/g, ''); // Keep only Chinese/English
                nameFound = true;
                break;
            }
        }
    }

    if (!nameFound) {
        // Fallback: Try document title again but be smarter
        // Title might be "王熙诚 - ..."
        const titleParts = document.title.split(/[-_|\s]/);
        if (titleParts.length > 0 && !titleParts[0].includes('gllue')) {
            data.name = titleParts[0].trim();
        } else {
            data.name = "Unknown";
        }
    }

    // --- 2. Extract Basic Info (Key-Value Pairs) ---
    // The previous issue was capturing the "next container" instead of the value.
    // We need to check if the value is a sibling *within* the same container, 
    // or if the label and value are in a table structure.

    data.basic_info = {};
    // Get all text nodes or spans that look like labels
    const candidates = document.querySelectorAll('td, th, span, div, label');

    const knownLabels = ['姓名', '所在城市', '手机', '邮箱', '性别', '行业', '年薪', '拥有者', '学历', '学校', '专业', '生日', '职能', '当前公司', '当前职位'];

    candidates.forEach(el => {
        let text = el.innerText.trim();
        // Remove colon if present
        text = text.replace(/[:：]$/, '');

        if (knownLabels.includes(text)) {
            let value = '';

            // Strategy A: Table Cell (TD/TH)
            if (el.tagName === 'TD' || el.tagName === 'TH') {
                const nextCell = el.nextElementSibling;
                if (nextCell) value = nextCell.innerText.trim();
            }
            // Strategy B: Flex/Grid Item (Label + Value in separate elements)
            else if (el.nextElementSibling) {
                // Check if next element is a value (not another label)
                const nextText = el.nextElementSibling.innerText.trim();
                // Heuristic: If next text is short and doesn't contain a newline, it's likely the value.
                // If it contains a newline, it might be a container for the *next* field (as seen in the "Gender" -> "Birthday" bug).
                if (!nextText.includes('\n')) {
                    value = nextText;
                }
            }
            // Strategy C: Parent Container (Label + Value in same parent)
            else if (el.parentElement) {
                // Sometimes text is "Label: Value" in one element
                const parentText = el.parentElement.innerText.trim();
                if (parentText.includes(text) && parentText.length > text.length) {
                    value = parentText.replace(text, '').replace(/[:：]/, '').trim();
                }
            }

            // Important: Only save if it's NOT "查看" (meaning click failed or didn't update yet)
            if (value && value !== '查看' && !knownLabels.includes(value)) {
                data.basic_info[text] = value;
            }
        }
    });

    // --- 3. Extract Work Experience & Education (Text Slicing Approach) ---
    // This approach finds the section headers, gets the full text between them, 
    // and then splits by date to ensure we capture descriptions and separate sections correctly.

    function getSectionText(startKeywords, endKeywords) {
        // 1. Find the Start Header Element
        const allHeaders = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, div, span, p, strong, b'));
        const headerEl = allHeaders.find(el => {
            const text = el.innerText.trim();
            // Match exact or close to exact header (short length)
            return startKeywords.some(kw => text.includes(kw)) && text.length < 20;
        });

        if (!headerEl) return null;

        // 2. Find the Container holding the content
        // Traverse up until we find a container that likely holds the whole section 
        // (e.g., contains the header AND some content, or contains the next header)
        let container = headerEl.parentElement;
        let foundContainer = null;

        // We look for a container that has significantly more text than the header
        // and ideally contains one of the endKeywords (if they exist on page)
        for (let i = 0; i < 6; i++) {
            if (!container) break;
            const text = container.innerText;

            // If text is long enough, it's a candidate. 
            // We prefer the smallest container that has the content.
            if (text.length > 100) {
                foundContainer = container;
                // If we see the End Keyword, this is definitely the wrapper (or a parent of it). 
                // We can stop going up if we found a container that has both Start and End.
                if (endKeywords.some(kw => text.includes(kw))) {
                    break;
                }
            }
            container = container.parentElement;
        }

        if (!foundContainer) return null;

        // 3. Extract Text between Start and End
        let fullText = foundContainer.innerText;
        // Normalize
        const headerText = headerEl.innerText.trim();
        const startIndex = fullText.indexOf(headerText);

        if (startIndex === -1) return null;

        let relevantText = fullText.substring(startIndex + headerText.length);

        // Find the earliest occurrence of any End Keyword
        let bestEndIndex = relevantText.length;
        for (let kw of endKeywords) {
            const idx = relevantText.indexOf(kw);
            // We want to ensure this keyword is actually a header, not just text.
            // Heuristic: It should be preceded by a newline or be at start.
            if (idx !== -1 && idx < bestEndIndex) {
                // Check for newline before match to avoid matching inside a sentence
                // (Simple check, not perfect but helps)
                const charBefore = relevantText.charAt(idx - 1);
                if (charBefore === '\n' || charBefore === '' || charBefore === ' ') {
                    bestEndIndex = idx;
                }
            }
        }

        return relevantText.substring(0, bestEndIndex).trim();
    }

    function parseEntriesFromText(text) {
        if (!text) return [];
        // Regex for Date Range (Start of entry)
        // Matches "YYYY-MM - YYYY-MM" or "YYYY.MM-YYYY.MM" or "YYYY-MM - 至今"
        const dateRegex = /(\d{4}[-./]\d{2}\s*[-~至]\s*\d{4}[-./]\d{2})|(\d{4}[-./]\d{2}\s*[-~至]\s*至今)/g;

        const indices = [];
        let match;
        while ((match = dateRegex.exec(text)) !== null) {
            indices.push(match.index);
        }

        const entries = [];
        for (let i = 0; i < indices.length; i++) {
            const start = indices[i];
            const end = (i + 1 < indices.length) ? indices[i + 1] : text.length;
            const entryText = text.substring(start, end).trim();
            if (entryText.length > 10) {
                entries.push(entryText);
            }
        }
        return entries;
    }

    // Extract Work
    const workText = getSectionText(['工作经历'], ['教育经历', '教育背景', '项目经历', '语言能力', '证书', '社交主页']);
    data.work_experience = parseEntriesFromText(workText);

    // Extract Education
    const eduText = getSectionText(['教育经历', '教育背景'], ['工作经历', '项目经历', '语言能力', '证书', '社交主页']);
    data.education = parseEntriesFromText(eduText);

    // Fallback: If text slicing failed (e.g. empty), try the old DOM method for Work
    if (data.work_experience.length === 0) {
        console.log("Text slicing failed for Work, using fallback DOM method.");
        // ... (Insert simplified DOM fallback if needed, or just rely on text)
        // For now, let's trust the text slicing as it's usually better for "Description" capture.
    }

    console.log("Scraped Data:", data);

    if (isManualTrigger) {
        alert("Scraped!\nName: " + data.name +
            "\nWork Exp Count: " + data.work_experience.length +
            "\nEducation Count: " + data.education.length);
    }

    const responsePayload = { action: "detail_data", data: data, isManual: isManualTrigger };
    console.log("DEBUG: Sending message to background:", responsePayload);
    if (sendResponse) {
        console.log("DEBUG: Using sendResponse");
        sendResponse(responsePayload);
    } else {
        console.log("DEBUG: Using chrome.runtime.sendMessage");
        chrome.runtime.sendMessage(responsePayload, (response) => {
            console.log("DEBUG: Message sent, response:", response);
            if (chrome.runtime.lastError) {
                console.error("DEBUG: Error sending message:", chrome.runtime.lastError);
            }
        });
    }
}
