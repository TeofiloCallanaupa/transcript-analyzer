# Transcript Analyzer

A desktop application for converting interview transcripts from DOCX to CSV and classifying them using OpenAI's GPT models.

## Features

- **Two-Step Workflow**
  - Step 1: Convert DOCX interview transcripts to structured CSV
  - Step 2: Classify transcript content using AI (GPT models)

- **User-Friendly Interface**
  - File picker for selecting multiple DOCX files
  - Real-time progress tracking and activity logs
  - Clear status indicators for each step
  - Error handling with helpful messages

- **Flexible AI Configuration**
  - Choose from multiple GPT models (gpt-5.1, gpt-4o, gpt-4o-mini, etc.)
  - Configurable API key
  - Direct link to OpenAI pricing documentation

- **Fully Customizable**
  - Define your own list of speaker names for extraction
  - Configure custom classification categories and themes
  - Adjust the AI system instruction for different use cases

- **Result Management**
  - View output file locations
  - "Open in Finder" buttons to quickly locate files
  - Selectable file paths for easy copying

## Prerequisites

- macOS (for the packaged app)
- Python 3.12+ (for development)
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation

### Option 1: Use Pre-built App (macOS)

1. Download the latest release from the [Releases](../../releases) page
2. Open `TranscriptAnalyzer.app`
3. If macOS blocks it (first time only):
   - Right-click → Open
   - Click "Open" in the dialog

### Option 2: Run from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/transcript-analyzer.git
   cd transcript-analyzer
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python gui_app.py
   ```

## Usage

1. **Enter API Key**: Paste your OpenAI API key
2. **Select Files**: Click "Select DOCX Files" and choose your interview transcripts
3. **Convert to CSV**: Click "Step 1: Convert to CSV" to extract the transcript data
4. **Review CSV**: Check the output location and verify the CSV file
5. **Classify with AI**: Select your preferred GPT model and click "Step 2: Classify with AI"
6. **Access Results**: Use "Open in Finder" to locate your classified CSV file

See [USER_GUIDE.md](USER_GUIDE.md) for detailed step-by-step instructions.

## Project Structure

```
transcript-analyzer/
├── gui_app.py                  # Main GUI application (Flet)
├── csv_classifier.py           # AI classification logic (OpenAI API)
├── settings_manager.py         # Settings persistence (JSON)
├── docx_to_csv/
│   ├── __init__.py
│   └── docx_to_csv.py         # DOCX → CSV conversion engine
├── tests/
│   ├── __init__.py
│   ├── test_classifier.py      # Prompt generation + LLM classification tests
│   ├── test_docx.py            # DOCX processing + edge case tests
│   └── test_settings_manager.py # Settings load/save/corrupt file tests
├── examples/                   # Sample interview transcripts and outputs
├── scripts/
│   └── build.py                # PyInstaller build script
├── .github/workflows/
│   └── build-and-release.yml   # CI/CD: test → build → release
├── default_settings.json       # Default configuration template
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment file
├── USER_GUIDE.md               # End-user guide
├── LICENSE                     # MIT License
└── README.md                   # This file
```

## Configuration

### API Key Setup

You can provide your OpenAI API key in two ways:

1. **Recommended: Enter in the app** (easiest for end users)
   - Just paste your key in the "OpenAI API Key" field when you run the app

2. **Optional: Use `.env` file** (convenient for developers)
   - Copy the example and add your key:
     ```bash
     cp .env.example .env
     # Edit .env and replace 'your-api-key-here' with your actual key
     ```
   - The app will use this as a fallback if no key is entered in the GUI

> **Note:** The `.env` file is in `.gitignore` and will never be committed to version control.

### Speaker Names & Categories

Click the **Settings (⚙️)** icon in the app to customize:

- **Speaker Names**: The names of people in your transcripts (used for parsing)
- **Categories**: The themes/topics for AI classification
- **System Instruction**: Custom prompt to guide the AI's behavior

Default settings are stored in `default_settings.json`.

## Supported Models

| Model | Description |
|-------|-------------|
| gpt-5.1 | Latest model (default) |
| gpt-5-mini | Smaller, faster variant |
| gpt-4o | Previous generation |
| gpt-4o-mini | Budget-friendly option |

See [OpenAI Pricing](https://platform.openai.com/docs/pricing) for costs.

## Development

### Running Tests

```bash
source venv/bin/activate
python -m unittest discover -s tests -v
```

The test suite includes **105 tests** covering:
- DOCX → CSV conversion (37 tests): timestamps, speaker matching, encoding, error handling
- AI classification pipeline (38 tests): prompt generation, mocked API calls, CSV processing
- Settings management (26 tests): load/save, defaults, corruption recovery
- End-to-end integration (4 tests): full DOCX → CSV → classification pipeline

### Building Locally

```bash
source venv/bin/activate

# macOS (produces dist/TranscriptAnalyzer.app)
flet pack gui_app.py --name TranscriptAnalyzer --add-data "default_settings.json:."

# Windows (produces dist/TranscriptAnalyzer.exe) — use ; instead of :
flet pack gui_app.py --name TranscriptAnalyzer --add-data "default_settings.json;."
```

> **Note:** You can only build for the OS you're running on.

### Releasing via GitHub Actions (macOS + Windows)

The repo includes a CI workflow that automatically builds for **both platforms**:

1. Push your code to GitHub
2. Tag a release: `git tag v1.0.0 && git push --tags`
3. GitHub Actions will run tests → build macOS `.app` + Windows `.exe` → create a Release page with both zips attached

See [`.github/workflows/build-and-release.yml`](.github/workflows/build-and-release.yml) for details.

## Error Handling

The app provides clear error messages for common issues:

- **Insufficient credits**: Link to OpenAI billing page
- **Invalid API key**: Prompt to check your key
- **Model not found**: Suggestion to verify model name
- **File errors**: Detailed error messages in activity log

## Troubleshooting

**App won't open on macOS**
- Right-click the app → Open (first time only)
- Check System Preferences → Security & Privacy

**"Unknown control: FilePicker" error**
- Rebuild using `flet pack` (not manual PyInstaller)

**Classification fails**
- Verify your API key is correct
- Check you have sufficient OpenAI credits
- Ensure the model name is spelled correctly

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Flet](https://flet.dev/) for the GUI
- Uses [OpenAI API](https://platform.openai.com/) for text classification
- DOCX parsing with [python-docx](https://python-docx.readthedocs.io/)
