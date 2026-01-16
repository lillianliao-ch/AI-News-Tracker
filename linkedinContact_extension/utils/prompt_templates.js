// Prompt Template Manager

// Default prompt template for candidate analysis
export const DEFAULT_PROMPT_TEMPLATE = `Please analyze the following LinkedIn candidate profile and extract key information in a structured format.

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

**Important:** Please ensure your response includes valid JSON that can be parsed programmatically. The fit_score should be a number from 1-10.`;

// Alternative template for technical roles
export const TECHNICAL_ROLE_TEMPLATE = `Analyze this LinkedIn profile for a technical role:

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
\`\`\``;

// Get active template from storage or return default
export async function getActiveTemplate() {
    try {
        const result = await chrome.storage.sync.get(['activeTemplate', 'customTemplate']);

        if (result.activeTemplate === 'custom' && result.customTemplate) {
            return result.customTemplate;
        } else if (result.activeTemplate === 'technical') {
            return TECHNICAL_ROLE_TEMPLATE;
        }

        return DEFAULT_PROMPT_TEMPLATE;
    } catch (error) {
        console.error('Error getting template:', error);
        return DEFAULT_PROMPT_TEMPLATE;
    }
}

// Save custom template
export async function saveCustomTemplate(template) {
    try {
        await chrome.storage.sync.set({
            customTemplate: template,
            activeTemplate: 'custom'
        });
        return { success: true };
    } catch (error) {
        console.error('Error saving template:', error);
        return { success: false, error: error.message };
    }
}

// Set active template type
export async function setActiveTemplate(templateType) {
    try {
        await chrome.storage.sync.set({ activeTemplate: templateType });
        return { success: true };
    } catch (error) {
        console.error('Error setting active template:', error);
        return { success: false, error: error.message };
    }
}

// Fill template with candidate data
export function fillTemplate(template, data) {
    let filled = template;

    // Replace all placeholders
    for (const [key, value] of Object.entries(data)) {
        const placeholder = new RegExp(`\\{${key}\\}`, 'g');
        filled = filled.replace(placeholder, value || 'N/A');
    }

    return filled;
}

// Get available template variables
export function getTemplateVariables() {
    return [
        'name',
        'title',
        'company',
        'location',
        'summary',
        'profileUrl'
    ];
}

// Validate template (check if it has required placeholders)
export function validateTemplate(template) {
    const errors = [];

    if (!template || template.trim().length === 0) {
        errors.push('Template cannot be empty');
    }

    if (!template.includes('{name}')) {
        errors.push('Template should include {name} placeholder');
    }

    if (!template.toLowerCase().includes('json')) {
        errors.push('Template should request JSON format response');
    }

    return {
        valid: errors.length === 0,
        errors
    };
}

// Preview template with sample data
export function previewTemplate(template) {
    const sampleData = {
        name: 'John Doe',
        title: 'Senior Software Engineer',
        company: 'Tech Corp',
        location: 'San Francisco, CA',
        summary: 'Experienced software engineer with 8+ years in full-stack development...',
        profileUrl: 'https://linkedin.com/in/johndoe'
    };

    return fillTemplate(template, sampleData);
}
