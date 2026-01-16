// Storage Manager for Candidate Data

/**
 * Save candidate analysis to Chrome storage
 * @param {Object} candidateData - Candidate data with AI analysis
 * @returns {Promise<Object>} Result with success status
 */
export async function saveCandidate(candidateData) {
    try {
        const today = getTodayKey();
        const timestamp = new Date().toISOString();

        // Add metadata
        const enrichedData = {
            ...candidateData,
            savedAt: timestamp,
            id: generateId()
        };

        // Get existing candidates for today
        const result = await chrome.storage.local.get([today]);
        const candidates = result[today] || [];

        // Add new candidate
        candidates.push(enrichedData);

        // Save back to storage
        await chrome.storage.local.set({ [today]: candidates });

        // Update statistics
        await updateStats(today, candidates.length);

        console.log(`Saved candidate to ${today}:`, enrichedData.name);

        return { success: true, id: enrichedData.id };
    } catch (error) {
        console.error('Error saving candidate:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Get candidates for a specific date
 * @param {string} date - Date in YYYY-MM-DD format (optional, defaults to today)
 * @returns {Promise<Array>} Array of candidates
 */
export async function getCandidates(date = null) {
    try {
        const key = date || getTodayKey();
        const result = await chrome.storage.local.get([key]);
        return result[key] || [];
    } catch (error) {
        console.error('Error getting candidates:', error);
        return [];
    }
}

/**
 * Get all candidates from all dates
 * @returns {Promise<Object>} Object with dates as keys and candidate arrays as values
 */
export async function getAllCandidates() {
    try {
        const allData = await chrome.storage.local.get(null);
        const candidates = {};

        for (const [key, value] of Object.entries(allData)) {
            if (key.startsWith('candidates_')) {
                candidates[key] = value;
            }
        }

        return candidates;
    } catch (error) {
        console.error('Error getting all candidates:', error);
        return {};
    }
}

/**
 * Get statistics about saved candidates
 * @returns {Promise<Object>} Statistics object
 */
export async function getStats() {
    try {
        const result = await chrome.storage.local.get(['stats']);
        return result.stats || {
            totalCandidates: 0,
            lastUpdated: null,
            byDate: {}
        };
    } catch (error) {
        console.error('Error getting stats:', error);
        return { totalCandidates: 0, byDate: {} };
    }
}

/**
 * Update statistics
 * @param {string} date - Date key
 * @param {number} count - Number of candidates for this date
 */
async function updateStats(date, count) {
    try {
        const stats = await getStats();

        stats.byDate = stats.byDate || {};
        stats.byDate[date] = count;
        stats.totalCandidates = Object.values(stats.byDate).reduce((sum, c) => sum + c, 0);
        stats.lastUpdated = new Date().toISOString();

        await chrome.storage.local.set({ stats });
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

/**
 * Delete candidate by ID
 * @param {string} id - Candidate ID
 * @param {string} date - Date key (optional)
 * @returns {Promise<Object>} Result with success status
 */
export async function deleteCandidate(id, date = null) {
    try {
        let targetDate = date;

        // If date not provided, search all dates
        if (!targetDate) {
            const allCandidates = await getAllCandidates();
            for (const [dateKey, candidates] of Object.entries(allCandidates)) {
                if (candidates.some(c => c.id === id)) {
                    targetDate = dateKey;
                    break;
                }
            }
        }

        if (!targetDate) {
            return { success: false, error: 'Candidate not found' };
        }

        const candidates = await getCandidates(targetDate);
        const filtered = candidates.filter(c => c.id !== id);

        await chrome.storage.local.set({ [targetDate]: filtered });
        await updateStats(targetDate, filtered.length);

        return { success: true };
    } catch (error) {
        console.error('Error deleting candidate:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Clear all data (with confirmation)
 * @returns {Promise<Object>} Result with success status
 */
export async function clearAllData() {
    try {
        const allData = await chrome.storage.local.get(null);
        const candidateKeys = Object.keys(allData).filter(k => k.startsWith('candidates_'));

        for (const key of candidateKeys) {
            await chrome.storage.local.remove(key);
        }

        await chrome.storage.local.remove(['stats']);

        return { success: true, cleared: candidateKeys.length };
    } catch (error) {
        console.error('Error clearing data:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Export all data as JSON
 * @returns {Promise<Object>} All candidate data
 */
export async function exportAllData() {
    try {
        const allCandidates = await getAllCandidates();
        const stats = await getStats();

        return {
            exportedAt: new Date().toISOString(),
            stats,
            candidates: allCandidates
        };
    } catch (error) {
        console.error('Error exporting data:', error);
        return null;
    }
}

/**
 * Import data from JSON
 * @param {Object} data - Data to import
 * @returns {Promise<Object>} Result with success status
 */
export async function importData(data) {
    try {
        if (!data || !data.candidates) {
            throw new Error('Invalid import data');
        }

        // Import candidates
        for (const [dateKey, candidates] of Object.entries(data.candidates)) {
            await chrome.storage.local.set({ [dateKey]: candidates });
        }

        // Recalculate stats
        const allCandidates = await getAllCandidates();
        const byDate = {};
        for (const [dateKey, candidates] of Object.entries(allCandidates)) {
            byDate[dateKey] = candidates.length;
        }

        const totalCandidates = Object.values(byDate).reduce((sum, c) => sum + c, 0);

        await chrome.storage.local.set({
            stats: {
                totalCandidates,
                byDate,
                lastUpdated: new Date().toISOString()
            }
        });

        return { success: true, imported: totalCandidates };
    } catch (error) {
        console.error('Error importing data:', error);
        return { success: false, error: error.message };
    }
}

// Helper functions

function getTodayKey() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `candidates_${year}-${month}-${day}`;
}

function generateId() {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
