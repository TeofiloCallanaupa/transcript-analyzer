# Transcript Analyzer — User Guide

## Running the App for the First Time (macOS)

Because this app was built internally and not "signed" by Apple, macOS will block it by default. You need to manually allow it **once**.

1. **Do NOT** double-click the app initially.
2. **Right-click** (or Control-click) on the `TranscriptAnalyzer` icon.
3. Select **Open** from the menu.
4. A popup will appear saying it is from an unidentified developer. Click **Open** again.

> You only have to do this the very first time. After that, you can double-click it normally.

---

## Using the App

### Step 1: Enter Your API Key

- Paste your OpenAI API Key (starts with `sk-...`) into the input field at the top.
- If you have a `.env` file in the same folder with `OPENAI_API_KEY=...`, the app will load it automatically.

### Step 2: Select Your Transcript Files

- Click **"Select DOCX Files"**.
- Navigate to your folder and select one or more `.docx` interview transcripts.

### Step 3: Convert to CSV

- Click **"Step 1: Convert to CSV"**.
- The app will extract speaker names, timestamps, and statements from your DOCX files.
- The activity log at the bottom will show progress.

### Step 4: Classify with AI

- Select your preferred GPT model from the dropdown.
- Click **"Step 2: Classify with AI"**.
- Each statement will be categorized into your configured themes.

### Step 5: Access Your Results

- The finished CSV file will be saved in the **same folder** as the first file you selected.
- The filename will look like `analysis_output_12345678.csv`.
- Click **"Open in Finder"** to quickly locate the file.

---

## Configuration (Settings ⚙️)

Click the **Settings (⚙️)** icon in the top-right corner to customize the app.

### Speaker Names

Enter the names of the people in your transcripts, one per line. This tells the app how to identify who is speaking.

**Example:**
```
Laura
Dana
InterviewerM
```

### Categories

Enter the themes or topics you want the AI to look for, one per line.

**Example:**
```
Governance Gaps
Employee Trust
Market Pressures
```

### System Instruction

(Optional) Provide a custom instruction to guide the AI's behavior. This is the "persona" the AI will adopt when classifying your text.

---

## Building from Source

If you need to rebuild the macOS app:

```bash
# Make sure you are in the project directory with the venv active
source venv/bin/activate

# Build the app
flet pack gui_app.py --name TranscriptAnalyzer --add-data ".env:."
```

The app will be created in the `dist/` folder as `TranscriptAnalyzer.app`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **App won't open** | Right-click → Open (see "Running the App" above) |
| **"Unidentified Developer" warning** | This is normal for unsigned apps — follow the steps above |
| **Classification fails** | Check that your API Key is valid and has credits |
| **No speakers detected** | Verify speaker names in Settings match your transcript exactly |
| **App crashes** | Check the activity log for error messages |
