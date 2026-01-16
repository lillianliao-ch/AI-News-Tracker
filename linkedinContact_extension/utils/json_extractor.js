// JSON Extractor Utility
// Extracts and parses JSON from various text formats

/**
 * Extract JSON object from text that may contain markdown, code blocks, or mixed content
 * @param {string} text - Text containing JSON
 * @returns {Object|null} Parsed JSON object or null if not found
 */
export function extractJSON(text) {
    if (!text || typeof text !== 'string') {
        return null;
    }

    // Strategy 1: Try to extract from markdown code blocks
    const codeBlockPatterns = [
        /```json\s*([\s\S]*?)\s*```/i,
        /```\s*([\s\S]*?)\s*```/,
    ];

    for (const pattern of codeBlockPatterns) {
        const match = text.match(pattern);
        if (match && match[1]) {
            try {
                return JSON.parse(match[1].trim());
            } catch (e) {
                console.warn('Failed to parse JSON from code block:', e);
            }
        }
    }

    // Strategy 2: Find JSON object boundaries
    const jsonObjectMatch = text.match(/\{[\s\S]*\}/);
    if (jsonObjectMatch) {
        try {
            return JSON.parse(jsonObjectMatch[0]);
        } catch (e) {
            console.warn('Failed to parse JSON object:', e);
        }
    }

    // Strategy 3: Try to find and extract the largest valid JSON
    const largestJSON = findLargestValidJSON(text);
    if (largestJSON) {
        return largestJSON;
    }

    return null;
}

/**
 * Find the largest valid JSON object in text
 * @param {string} text - Text to search
 * @returns {Object|null} Largest valid JSON object or null
 */
function findLargestValidJSON(text) {
    let largestJSON = null;
    let maxLength = 0;

    // Find all potential JSON start positions
    for (let i = 0; i < text.length; i++) {
        if (text[i] === '{') {
            // Try to parse from this position
            let braceCount = 0;
            let inString = false;
            let escape = false;

            for (let j = i; j < text.length; j++) {
                const char = text[j];

                if (escape) {
                    escape = false;
                    continue;
                }

                if (char === '\\') {
                    escape = true;
                    continue;
                }

                if (char === '"') {
                    inString = !inString;
                    continue;
                }

                if (!inString) {
                    if (char === '{') braceCount++;
                    if (char === '}') braceCount--;

                    if (braceCount === 0) {
                        // Found matching closing brace
                        const jsonStr = text.substring(i, j + 1);
                        try {
                            const parsed = JSON.parse(jsonStr);
                            if (jsonStr.length > maxLength) {
                                maxLength = jsonStr.length;
                                largestJSON = parsed;
                            }
                        } catch (e) {
                            // Not valid JSON, continue searching
                        }
                        break;
                    }
                }
            }
        }
    }

    return largestJSON;
}

/**
 * Validate if extracted JSON has expected candidate fields
 * @param {Object} json - Parsed JSON object
 * @returns {Object} Validation result with valid flag and missing fields
 */
export function validateCandidateJSON(json) {
    if (!json || typeof json !== 'object') {
        return { valid: false, errors: ['Not a valid object'] };
    }

    const requiredFields = ['name'];
    const recommendedFields = ['title', 'company', 'skills', 'fit_score', 'summary'];

    const missing = requiredFields.filter(field => !json[field]);
    const missingRecommended = recommendedFields.filter(field => !json[field]);

    return {
        valid: missing.length === 0,
        errors: missing.length > 0 ? [`Missing required fields: ${missing.join(', ')}`] : [],
        warnings: missingRecommended.length > 0 ? [`Missing recommended fields: ${missingRecommended.join(', ')}`] : [],
        data: json
    };
}

/**
 * Clean and normalize extracted JSON
 * @param {Object} json - Raw extracted JSON
 * @returns {Object} Normalized JSON with consistent field types
 */
export function normalizeJSON(json) {
    if (!json) return null;

    const normalized = { ...json };

    // Ensure arrays
    if (normalized.skills && !Array.isArray(normalized.skills)) {
        normalized.skills = [normalized.skills];
    }

    if (normalized.areas_of_expertise && !Array.isArray(normalized.areas_of_expertise)) {
        normalized.areas_of_expertise = [normalized.areas_of_expertise];
    }

    // Ensure numbers
    if (normalized.fit_score && typeof normalized.fit_score === 'string') {
        normalized.fit_score = parseInt(normalized.fit_score, 10);
    }

    if (normalized.experience_years && typeof normalized.experience_years === 'string') {
        const match = normalized.experience_years.match(/\d+/);
        if (match) {
            normalized.experience_years = parseInt(match[0], 10);
        }
    }

    // Trim strings
    for (const key in normalized) {
        if (typeof normalized[key] === 'string') {
            normalized[key] = normalized[key].trim();
        }
    }

    return normalized;
}

/**
 * Extract and validate JSON in one call
 * @param {string} text - Text containing JSON
 * @returns {Object} Result with extracted, validated, and normalized JSON
 */
export function extractAndValidateJSON(text) {
    const extracted = extractJSON(text);

    if (!extracted) {
        return {
            success: false,
            error: 'No JSON found in text',
            data: null
        };
    }

    const validation = validateCandidateJSON(extracted);

    if (!validation.valid) {
        return {
            success: false,
            error: validation.errors.join(', '),
            warnings: validation.warnings,
            data: extracted
        };
    }

    const normalized = normalizeJSON(extracted);

    return {
        success: true,
        data: normalized,
        warnings: validation.warnings
    };
}
