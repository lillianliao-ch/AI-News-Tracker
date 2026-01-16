// Options Page Script

// Template definitions (imported from utils/prompt_templates.js concepts)
const TEMPLATES = {
    default: `Please analyze the following LinkedIn candidate profile and extract key information in a structured format.

**Candidate Information:**
- Name: {name}
- Current Title: {title}
- Company: {company}
- Location: {location}
- Profile URL: {profileUrl}

**About/Summary:**
{summary}

**Analysis Request:**
Please provide a comprehensive analysis of this candidate and return the information in the following JSON format:

\`\`\`json
{
  "name": "Full name of the candidate",
  "title": "Current job title",
  "company": "Current company name",
  "location": "Geographic location",
  "skills": ["skill1", "skill2", "skill3"],
  "experience_years": "Estimated total years of professional experience",
  "education": "Education background summary",
  "strengths": "Key strengths and professional highlights",
  "areas_of_expertise": ["area1", "area2"],
  "fit_score": 8,
  "fit_reasoning": "Explanation of the fit score",
  "summary": "Brief professional summary (2-3 sentences)",
  "recommendations": "Hiring recommendations or next steps"
}
\`\`\`

**Important:** Please ensure your response includes valid JSON that can be parsed programmatically. The fit_score should be a number from 1-10.`,

    technical: `Analyze this LinkedIn profile for a technical role:

**Profile Data:**
Name: {name}
Title: {title}
Company: {company}
Location: {location}
Summary: {summary}

**Technical Assessment Required:**
Please evaluate and return JSON with:
- Technical skills and proficiency levels
- Years of experience in key technologies
- Project complexity indicators
- Leadership and collaboration signals
- Cultural fit indicators

Return in this JSON format:
\`\`\`json
{
  "name": "{name}",
  "title": "{title}",
  "company": "{company}",
  "technical_skills": [{"skill": "name", "level": "beginner/intermediate/advanced/expert"}],
  "experience_years": "number",
  "key_projects": ["project1", "project2"],
  "leadership_indicators": "assessment",
  "technical_fit_score": 8,
  "cultural_fit_score": 7,
  "overall_recommendation": "hire/maybe/pass",
  "reasoning": "detailed explanation"
}
\`\`\``
};

let currentTemplate = 'default';

document.addEventListener('DOMContentLoaded', init);

async function init() {
    await loadSettings();
    setupEventListeners();
}

// Load saved settings
async function loadSettings() {
    try {
        const result = await chrome.storage.sync.get(['activeTemplate', 'customTemplate']);

        currentTemplate = result.activeTemplate || 'default';

        // Set active template option
        document.querySelectorAll('.template-option').forEach(option => {
            option.classList.remove('active');
            if (option.dataset.template === currentTemplate) {
                option.classList.add('active');
            }
        });

        // Load template content
        if (currentTemplate === 'custom' && result.customTemplate) {
            document.getElementById('promptTemplate').value = result.customTemplate;
        } else {
            document.getElementById('promptTemplate').value = TEMPLATES[currentTemplate] || TEMPLATES.default;
        }

    } catch (error) {
        console.error('Error loading settings:', error);
        showAlert('Error loading settings', 'error');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Template selection
    document.querySelectorAll('.template-option').forEach(option => {
        option.addEventListener('click', handleTemplateSelect);
    });

    // Buttons
    document.getElementById('saveTemplateBtn').addEventListener('click', handleSaveTemplate);
    document.getElementById('previewTemplateBtn').addEventListener('click', handlePreviewTemplate);
    document.getElementById('resetTemplateBtn').addEventListener('click', handleResetTemplate);
    document.getElementById('exportAllBtn').addEventListener('click', handleExportAll);
    document.getElementById('exportTodayBtn').addEventListener('click', handleExportToday);
    document.getElementById('importBtn').addEventListener('click', () => document.getElementById('importFile').click());
    document.getElementById('importFile').addEventListener('change', handleImport);
    document.getElementById('clearAllBtn').addEventListener('click', handleClearAll);
}

// Handle template selection
function handleTemplateSelect(e) {
    const option = e.currentTarget;
    const templateType = option.dataset.template;

    // Update UI
    document.querySelectorAll('.template-option').forEach(opt => opt.classList.remove('active'));
    option.classList.add('active');

    currentTemplate = templateType;

    // Load template content
    if (templateType === 'custom') {
        // Keep current custom template or clear
        chrome.storage.sync.get(['customTemplate'], (result) => {
            if (result.customTemplate) {
                document.getElementById('promptTemplate').value = result.customTemplate;
            } else {
                document.getElementById('promptTemplate').value = '';
            }
        });
    } else {
        document.getElementById('promptTemplate').value = TEMPLATES[templateType];
    }
}

// Handle save template
async function handleSaveTemplate() {
    try {
        const template = document.getElementById('promptTemplate').value.trim();

        if (!template) {
            showAlert('Template cannot be empty', 'error');
            return;
        }

        // Validate template
        if (!template.includes('{name}')) {
            showAlert('Warning: Template should include {name} variable', 'error');
            return;
        }

        // Save to storage
        const saveData = { activeTemplate: currentTemplate };

        if (currentTemplate === 'custom') {
            saveData.customTemplate = template;
        }

        await chrome.storage.sync.set(saveData);

        showAlert('Template saved successfully!', 'success');

    } catch (error) {
        console.error('Error saving template:', error);
        showAlert('Error saving template: ' + error.message, 'error');
    }
}

// Handle preview template
function handlePreviewTemplate() {
    const template = document.getElementById('promptTemplate').value;

    // Sample data
    const sampleData = {
        name: 'John Doe',
        title: 'Senior Software Engineer',
        company: 'Tech Corp',
        location: 'San Francisco, CA',
        summary: 'Experienced software engineer with 8+ years in full-stack development, specializing in React and Node.js...',
        profileUrl: 'https://linkedin.com/in/johndoe'
    };

    // Fill template
    let preview = template;
    for (const [key, value] of Object.entries(sampleData)) {
        preview = preview.replace(new RegExp(`\\{${key}\\}`, 'g'), value);
    }

    // Show in alert (or could open modal)
    alert('Preview:\n\n' + preview);
}

// Handle reset template
async function handleResetTemplate() {
    if (!confirm('Reset template to default? This will discard any custom changes.')) {
        return;
    }

    currentTemplate = 'default';
    document.getElementById('promptTemplate').value = TEMPLATES.default;

    // Update UI
    document.querySelectorAll('.template-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector('[data-template="default"]').classList.add('active');

    await chrome.storage.sync.set({ activeTemplate: 'default' });
    showAlert('Template reset to default', 'success');
}

// Handle export all data
async function handleExportAll() {
    try {
        const allData = await chrome.storage.local.get(null);
        const candidates = {};
        let stats = null;

        for (const [key, value] of Object.entries(allData)) {
            if (key.startsWith('candidates_')) {
                candidates[key] = value;
            } else if (key === 'stats') {
                stats = value;
            }
        }

        const exportData = {
            exportedAt: new Date().toISOString(),
            version: '2.0.0',
            stats,
            candidates
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const filename = `linkedin-atlas-export-${new Date().toISOString().split('T')[0]}.json`;

        await chrome.downloads.download({
            url: url,
            filename: filename,
            saveAs: true
        });

        setTimeout(() => URL.revokeObjectURL(url), 1000);

        showAlert('Data exported successfully!', 'success');

    } catch (error) {
        console.error('Error exporting data:', error);
        showAlert('Error exporting data: ' + error.message, 'error');
    }
}

// Handle export today's Excel
async function handleExportToday() {
    try {
        chrome.runtime.sendMessage({ type: 'EXPORT_TO_EXCEL' }, (response) => {
            if (response && response.success) {
                showAlert('Excel file exported successfully!', 'success');
            } else {
                showAlert('Error exporting Excel: ' + (response?.error || 'Unknown error'), 'error');
            }
        });
    } catch (error) {
        console.error('Error exporting Excel:', error);
        showAlert('Error exporting Excel: ' + error.message, 'error');
    }
}

// Handle import data
async function handleImport(e) {
    const file = e.target.files[0];
    if (!file) return;

    try {
        const text = await file.text();
        const data = JSON.parse(text);

        if (!data.candidates) {
            throw new Error('Invalid import file format');
        }

        if (!confirm(`Import ${Object.keys(data.candidates).length} date(s) of candidate data? This will merge with existing data.`)) {
            return;
        }

        // Import candidates
        for (const [dateKey, candidates] of Object.entries(data.candidates)) {
            await chrome.storage.local.set({ [dateKey]: candidates });
        }

        // Recalculate stats
        const allData = await chrome.storage.local.get(null);
        const byDate = {};
        for (const [key, value] of Object.entries(allData)) {
            if (key.startsWith('candidates_')) {
                byDate[key] = value.length;
            }
        }

        const totalCandidates = Object.values(byDate).reduce((sum, c) => sum + c, 0);

        await chrome.storage.local.set({
            stats: {
                totalCandidates,
                byDate,
                lastUpdated: new Date().toISOString()
            }
        });

        showAlert(`Successfully imported ${totalCandidates} candidates!`, 'success');

        // Reset file input
        e.target.value = '';

    } catch (error) {
        console.error('Error importing data:', error);
        showAlert('Error importing data: ' + error.message, 'error');
    }
}

// Handle clear all data
async function handleClearAll() {
    if (!confirm('⚠️ WARNING: This will permanently delete ALL candidate data. This cannot be undone!\n\nAre you sure you want to continue?')) {
        return;
    }

    if (!confirm('Final confirmation: Delete all data?')) {
        return;
    }

    try {
        const allData = await chrome.storage.local.get(null);
        const keysToRemove = Object.keys(allData).filter(k => k.startsWith('candidates_') || k === 'stats');

        await chrome.storage.local.remove(keysToRemove);

        showAlert(`Deleted ${keysToRemove.length} data entries`, 'success');

    } catch (error) {
        console.error('Error clearing data:', error);
        showAlert('Error clearing data: ' + error.message, 'error');
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    const container = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;

    container.appendChild(alert);

    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.3s';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}
