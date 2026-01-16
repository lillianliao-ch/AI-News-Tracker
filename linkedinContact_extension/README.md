# LinkedIn-Atlas Candidate Analyzer

> 🎯 AI-Powered LinkedIn Candidate Analysis using ChatGPT Atlas

A Chrome browser extension that automatically analyzes LinkedIn candidate profiles using ChatGPT Atlas AI, extracts structured data, and exports to Excel.

## ✨ Features

- 🔍 **One-Click Analysis**: Analyze LinkedIn profiles with a single button click
- 🤖 **AI-Powered**: Leverages ChatGPT Atlas for intelligent candidate evaluation
- 📊 **Auto Export**: Automatically saves data to Chrome Storage and Excel files
- 🎨 **Customizable Prompts**: Configure AI prompts for different role types
- 💾 **Data Management**: Import/export data, view statistics, manage history
- 🎯 **Smart Extraction**: Automatically extracts JSON from AI responses
- 📈 **Daily Reports**: Organizes candidates by date with Excel export

## 🚀 Quick Start

### Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `linkedinContact_extension` directory
5. Pin the extension to your toolbar

### Usage

1. Visit any LinkedIn profile page (e.g., `https://www.linkedin.com/in/username/`)
2. Click the **"Analyze with AI"** button that appears on the page
3. The extension will:
   - Extract candidate information
   - Open ChatGPT Atlas
   - Send the analysis prompt
   - Extract the AI response
   - Save to storage and export to Excel
4. Check your Downloads folder for the Excel file: `candidates_YYYY-MM-DD.xlsx`

## 📋 Requirements

- Google Chrome browser
- ChatGPT Plus account (for Atlas access)
- LinkedIn account

## 🎨 Configuration

### Prompt Templates

The extension includes three built-in templates:

1. **Default**: General candidate analysis
2. **Technical Role**: Focused on technical skills assessment
3. **Custom**: Create your own template

To configure:
1. Click the extension icon
2. Click "Settings"
3. Select or edit your template
4. Save changes

### Available Variables

Use these variables in your custom prompts:

- `{name}` - Candidate name
- `{title}` - Current job title
- `{company}` - Current company
- `{location}` - Geographic location
- `{summary}` - Profile summary/about section
- `{profileUrl}` - LinkedIn profile URL

## 📊 Data Export

### Excel Format

Exported Excel files include:

| Column | Description |
|--------|-------------|
| Name | Candidate name |
| Title | Current position |
| Company | Current employer |
| Location | Geographic location |
| Skills | Comma-separated skills |
| Experience (Years) | Estimated years of experience |
| Fit Score | AI-generated fit score (1-10) |
| Summary | Professional summary |
| Strengths | Key strengths |
| Education | Education background |
| LinkedIn URL | Profile link |
| Analyzed At | Timestamp |

### Data Storage

- All data is stored locally in Chrome Storage
- Organized by date (YYYY-MM-DD)
- Can be exported to JSON for backup
- Can be imported from previous exports

## 🏗️ Architecture

```
Extension Components:
├── manifest.json           # Extension configuration
├── background.js           # Service worker (message coordination)
├── content/
│   ├── linkedin_content.js # LinkedIn page integration
│   └── atlas_content.js    # ChatGPT Atlas automation
├── utils/
│   ├── prompt_templates.js # Template management
│   ├── json_extractor.js   # JSON parsing
│   ├── storage.js          # Data persistence
│   └── excel_exporter.js   # Excel generation
└── ui/
    ├── popup.html/js       # Extension popup
    ├── options.html/js     # Settings page
    └── styles.css          # Styling
```

### Message Flow

```
LinkedIn Page → Background Script → ChatGPT Atlas
      ↓                                    ↓
   Extract Data                    Send Prompt & Get Response
      ↓                                    ↓
   Chrome Storage ← Background Script ← Extract JSON
      ↓
   Excel Export
```

## 🔧 Development

### Project Structure

```bash
linkedinContact_extension/
├── manifest.json
├── background.js
├── content/
│   ├── linkedin_content.js
│   └── atlas_content.js
├── utils/
│   ├── prompt_templates.js
│   ├── json_extractor.js
│   ├── storage.js
│   └── excel_exporter.js
├── ui/
│   ├── popup.html
│   ├── popup.js
│   ├── options.html
│   ├── options.js
│   └── styles.css
├── config/
│   └── default_config.json
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md
```

### Key Technologies

- **Manifest V3**: Latest Chrome extension standard
- **Chrome Storage API**: Local data persistence
- **Chrome Downloads API**: Excel file export
- **MutationObserver**: DOM change detection for Atlas responses
- **SheetJS (xlsx)**: Excel file generation (optional, falls back to JSON)

## 🐛 Troubleshooting

### Button doesn't appear on LinkedIn

- Refresh the page
- Ensure you're on a profile page (`/in/username/`)
- Check if extension is enabled in `chrome://extensions/`

### Atlas doesn't respond

- Verify you're logged into ChatGPT
- Check your ChatGPT Plus subscription
- Open browser console (F12) for error messages

### JSON extraction fails

- Improve your prompt template to explicitly request JSON format
- Add example JSON structure in the prompt
- Use code blocks in the prompt: \`\`\`json ... \`\`\`

### Excel export fails

- Ensure you have analyzed candidates today
- Check Chrome download permissions
- Try exporting to JSON instead

## 📝 Version History

### v2.0.0 (Current)
- Complete rewrite with LinkedIn-Atlas integration
- Configurable prompt templates
- Chrome Storage persistence
- Excel export functionality
- Modern UI with gradient design

### v1.0.0 (Legacy)
- Basic LinkedIn profile fetching
- Local backend service integration

## 📄 License

MIT License - feel free to use and modify

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## 📧 Support

For issues or questions, please check the troubleshooting section in the user guide.

---

**Made with ❤️ for recruiters and hiring managers**
