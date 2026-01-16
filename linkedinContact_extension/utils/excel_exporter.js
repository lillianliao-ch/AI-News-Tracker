// Excel Exporter using SheetJS (xlsx)
// Note: This requires the xlsx library to be loaded

/**
 * Export candidates to Excel file
 * @param {Array} candidates - Array of candidate objects
 * @param {string} filename - Optional filename (defaults to date-based name)
 * @returns {Promise<Object>} Result with success status
 */
export async function exportToExcel(candidates, filename = null) {
    try {
        // Check if xlsx library is available
        if (typeof XLSX === 'undefined') {
            console.warn('XLSX library not loaded, will download JSON instead');
            return await exportToJSON(candidates, filename);
        }

        const data = prepareCandidateData(candidates);
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(data);

        // Set column widths
        const colWidths = [
            { wch: 20 }, // Name
            { wch: 25 }, // Title
            { wch: 20 }, // Company
            { wch: 15 }, // Location
            { wch: 30 }, // Skills
            { wch: 12 }, // Experience
            { wch: 10 }, // Fit Score
            { wch: 40 }, // Summary
            { wch: 50 }, // LinkedIn URL
            { wch: 20 }  // Analyzed At
        ];
        ws['!cols'] = colWidths;

        XLSX.utils.book_append_sheet(wb, ws, 'Candidates');

        // Generate filename
        const finalFilename = filename || `candidates_${getTodayString()}.xlsx`;

        // Write file
        const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

        // Download file
        await downloadBlob(blob, finalFilename);

        return { success: true, filename: finalFilename };
    } catch (error) {
        console.error('Error exporting to Excel:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Export today's candidates to Excel
 * @returns {Promise<Object>} Result with success status
 */
export async function exportTodayToExcel() {
    try {
        // Get today's candidates from storage
        const { getCandidates } = await import('./storage.js');
        const candidates = await getCandidates();

        if (candidates.length === 0) {
            return { success: false, error: 'No candidates to export for today' };
        }

        return await exportToExcel(candidates);
    } catch (error) {
        console.error('Error exporting today\'s candidates:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Append candidate to existing Excel file (or create new one)
 * Note: This is a simplified version - actual implementation would need to read existing file
 * @param {Object} candidate - Single candidate object
 * @returns {Promise<Object>} Result with success status
 */
export async function appendToTodayExcel(candidate) {
    try {
        // Get all candidates for today
        const { getCandidates } = await import('./storage.js');
        const candidates = await getCandidates();

        // Export all (including the new one)
        return await exportToExcel(candidates);
    } catch (error) {
        console.error('Error appending to Excel:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Prepare candidate data for Excel export
 * @param {Array|Object} candidates - Candidate(s) to prepare
 * @returns {Array} Array of flattened candidate objects
 */
function prepareCandidateData(candidates) {
    const candidateArray = Array.isArray(candidates) ? candidates : [candidates];

    return candidateArray.map(candidate => {
        const analysis = candidate.aiAnalysis || {};

        return {
            'Name': analysis.name || candidate.name || 'N/A',
            'Title': analysis.title || candidate.title || 'N/A',
            'Company': analysis.company || candidate.company || 'N/A',
            'Location': analysis.location || candidate.location || 'N/A',
            'Skills': Array.isArray(analysis.skills) ? analysis.skills.join(', ') : (analysis.skills || 'N/A'),
            'Experience (Years)': analysis.experience_years || 'N/A',
            'Fit Score': analysis.fit_score || 'N/A',
            'Summary': analysis.summary || candidate.summary || 'N/A',
            'Strengths': analysis.strengths || 'N/A',
            'Education': analysis.education || 'N/A',
            'LinkedIn URL': candidate.linkedinUrl || candidate.profileUrl || 'N/A',
            'Analyzed At': candidate.analyzedAt || candidate.savedAt || new Date().toISOString()
        };
    });
}

/**
 * Fallback: Export to JSON if XLSX is not available
 * @param {Array} candidates - Candidates to export
 * @param {string} filename - Optional filename
 * @returns {Promise<Object>} Result with success status
 */
async function exportToJSON(candidates, filename = null) {
    try {
        const data = prepareCandidateData(candidates);
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });

        const finalFilename = filename || `candidates_${getTodayString()}.json`;
        await downloadBlob(blob, finalFilename);

        return { success: true, filename: finalFilename, format: 'json' };
    } catch (error) {
        console.error('Error exporting to JSON:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Download blob as file
 * @param {Blob} blob - Blob to download
 * @param {string} filename - Filename
 */
async function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);

    // Use Chrome downloads API
    await chrome.downloads.download({
        url: url,
        filename: filename,
        saveAs: false // Auto-save to downloads folder
    });

    // Clean up
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/**
 * Get today's date as string (YYYY-MM-DD)
 * @returns {string} Date string
 */
function getTodayString() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Load XLSX library dynamically if not already loaded
 * @returns {Promise<boolean>} True if loaded successfully
 */
export async function loadXLSXLibrary() {
    if (typeof XLSX !== 'undefined') {
        return true;
    }

    try {
        // Load from CDN
        const script = document.createElement('script');
        script.src = 'https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js';

        return new Promise((resolve, reject) => {
            script.onload = () => resolve(true);
            script.onerror = () => reject(new Error('Failed to load XLSX library'));
            document.head.appendChild(script);
        });
    } catch (error) {
        console.error('Error loading XLSX library:', error);
        return false;
    }
}
