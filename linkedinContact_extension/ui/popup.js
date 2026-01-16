// Popup Script for LinkedIn-Atlas Analyzer

document.addEventListener('DOMContentLoaded', init);

async function init() {
    await loadStats();
    await loadRecentCandidates();
    setupEventListeners();
    checkConnectivity();
    setInterval(checkConnectivity, 2000); // Poll every 2s
}

// Check Atlas connectivity
function checkConnectivity() {
    chrome.runtime.sendMessage({ type: 'GET_STATUS' }, response => {
        const footer = document.getElementById('status-footer');
        if (response && response.success) {
            const count = response.atlasCount;
            const text = count > 0
                ? `✅ Connected to ${count} Atlas Instance(s)`
                : '❌ No Atlas Connection (Please Open Side Chat)';

            footer.textContent = text;
            footer.style.color = count > 0 ? '#10a37f' : '#ef4444';
        } else {
            footer.textContent = '❌ Background Service Error';
            footer.style.color = '#ef4444';
        }
    });
}

// Load and display statistics
async function loadStats() {
    try {
        // Import storage module
        const { getStats, getCandidates } = await importModule('./utils/storage.js');

        const stats = await getStats();
        const todayCandidates = await getCandidates();

        document.getElementById('todayCount').textContent = todayCandidates.length;
        document.getElementById('totalCount').textContent = stats.totalCandidates || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('todayCount').textContent = '?';
        document.getElementById('totalCount').textContent = '?';
    }
}

// Load recent candidates
async function loadRecentCandidates() {
    try {
        const { getCandidates } = await importModule('./utils/storage.js');
        const candidates = await getCandidates();

        const recentList = document.getElementById('recentList');

        if (candidates.length === 0) {
            recentList.innerHTML = '<div class="empty-state">No analyses yet today</div>';
            return;
        }

        // Show last 3 candidates
        const recent = candidates.slice(-3).reverse();

        recentList.innerHTML = recent.map(candidate => {
            const analysis = candidate.aiAnalysis || {};
            const name = analysis.name || candidate.name || 'Unknown';
            const title = analysis.title || candidate.title || 'N/A';
            const company = analysis.company || candidate.company || 'N/A';
            const time = new Date(candidate.analyzedAt || candidate.savedAt).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            });

            return `
        <div class="candidate-item">
          <div class="candidate-name">${escapeHtml(name)}</div>
          <div class="candidate-info">${escapeHtml(title)} at ${escapeHtml(company)}</div>
          <div class="candidate-info">Analyzed at ${time}</div>
        </div>
      `;
        }).join('');

    } catch (error) {
        console.error('Error loading recent candidates:', error);
        document.getElementById('recentList').innerHTML = '<div class="empty-state">Error loading data</div>';
    }
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('analyzeCurrentBtn').addEventListener('click', handleAnalyzeCurrent);
    document.getElementById('exportBtn').addEventListener('click', handleExport);
    document.getElementById('viewDataBtn').addEventListener('click', handleViewData);
    document.getElementById('settingsBtn').addEventListener('click', handleSettings);
    document.getElementById('helpLink').addEventListener('click', handleHelp);
}

// Handle analyze current profile button click
async function handleAnalyzeCurrent() {
    const btn = document.getElementById('analyzeCurrentBtn');
    const originalHTML = btn.innerHTML;

    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span><span>Opening ChatGPT...</span>';

        // Get current active tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const currentUrl = tab.url || 'No URL';

        console.log('Current page:', currentUrl);

        // Send message to background to send prompt to Atlas
        const prompt = `Please analyze this LinkedIn page: ${currentUrl}

Visit the page and provide insights about the person or content.`;

        chrome.runtime.sendMessage({
            type: 'SEND_PROMPT_TO_ATLAS',
            prompt: prompt
        }, (response) => {
            if (chrome.runtime.lastError) {
                alert('Error: ' + chrome.runtime.lastError.message);
                console.error(chrome.runtime.lastError);
                btn.innerHTML = originalHTML;
                btn.disabled = false;
            } else if (response && response.success) {
                btn.innerHTML = '<span>✅</span><span>Sent!</span>';
                console.log('Successfully sent to Atlas');
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.disabled = false;
                }, 2000);
            } else {
                alert('Failed: ' + (response?.error || 'Unknown error'));
                console.error('Failed:', response);
                btn.innerHTML = originalHTML;
                btn.disabled = false;
            }
        });

    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

// Handle export button click
async function handleExport() {
    const btn = document.getElementById('exportBtn');
    const originalHTML = btn.innerHTML;

    try {
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span><span>Exporting...</span>';

        const { getCandidates } = await importModule('./utils/storage.js');
        const candidates = await getCandidates();

        if (candidates.length === 0) {
            alert('No candidates to export for today');
            return;
        }

        // Send message to background to handle export
        chrome.runtime.sendMessage({
            type: 'EXPORT_TO_EXCEL',
            data: { candidates }
        }, (response) => {
            if (response && response.success) {
                btn.innerHTML = '<span>✅</span><span>Exported!</span>';
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.disabled = false;
                }, 2000);
            } else {
                alert('Export failed: ' + (response?.error || 'Unknown error'));
                btn.innerHTML = originalHTML;
                btn.disabled = false;
            }
        });

    } catch (error) {
        console.error('Error exporting:', error);
        alert('Export failed: ' + error.message);
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

// Handle view data button click
function handleViewData() {
    // Open a new tab with data viewer (to be implemented)
    chrome.tabs.create({
        url: chrome.runtime.getURL('ui/data_viewer.html')
    });
}

// Handle settings button click
function handleSettings() {
    chrome.runtime.openOptionsPage();
}

// Handle help link click
function handleHelp(e) {
    e.preventDefault();
    chrome.tabs.create({
        url: 'https://github.com/yourusername/linkedin-atlas-analyzer#readme'
    });
}

// Helper function to import ES modules in extension context
async function importModule(path) {
    // In Chrome extensions, we need to use dynamic import
    // This is a workaround since popup.js is loaded as a regular script
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
            type: 'IMPORT_MODULE',
            path: path
        }, (response) => {
            if (response && response.success) {
                resolve(response.module);
            } else {
                // Fallback: use chrome.storage directly
                resolve({
                    getCandidates: async (date) => {
                        const key = date || getTodayKey();
                        const result = await chrome.storage.local.get([key]);
                        return result[key] || [];
                    },
                    getStats: async () => {
                        const result = await chrome.storage.local.get(['stats']);
                        return result.stats || { totalCandidates: 0, byDate: {} };
                    }
                });
            }
        });
    });
}

function getTodayKey() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `candidates_${year}-${month}-${day}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
