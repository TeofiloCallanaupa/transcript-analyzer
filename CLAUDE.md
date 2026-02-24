# CLAUDE.md — Lessons & Conventions for This Codebase

## Project Overview
- **Flet desktop + web app** (Python) for converting DOCX interview transcripts to CSV and classifying with OpenAI
- Run desktop: `flet run gui_app.py`
- Run web: `flet run --web gui_app.py`
- Tests: `python -m unittest discover -s tests -v`

## Testing Rules
- **Always run the full test suite** (`python -m unittest discover -s tests`) after any code change
- **Always verify visually through the web version** via Chrome browser — the desktop app cannot be visually inspected by the agent
- **Always verify the desktop app still launches** after web-related changes (`flet run gui_app.py` — confirm no errors in output)
- Current test count: **149 tests** (1 skipped)

## Flet 0.80 Specifics (Mistakes Made & Lessons Learned)

### FilePicker is a Service, NOT a visual control
- ❌ `page.overlay.append(ft.FilePicker())` — renders as a giant red "Unknown control: FilePicker" block
- ✅ Just create `file_picker = ft.FilePicker()` and call methods on it directly — it's a Service

### Web mode file handling
- In web mode, `FilePicker.pick_files()` returns files with `f.path = None` (files are uploaded, not local)
- Must use `file_picker.upload()` with `FilePickerUploadFile` objects and `page.get_upload_url()`
- Requires `upload_dir="uploads"` in `ft.run()` and `FLET_SECRET_KEY` environment variable
- ❌ `ft.run(main, secret_key=...)` — `secret_key` is NOT a parameter of `ft.run()`
- ✅ `os.environ["FLET_SECRET_KEY"] = secrets.token_hex(16)` before `ft.run()`

### Background threads and macOS repaint bug
- ❌ `threading.Thread(target=func).start()` — `page.update()` from raw threads does NOT trigger macOS desktop repaints. The UI only updates when the user moves the window.
- ✅ `page.run_thread(func, *args)` — runs in Flet's executor with proper context wrapping so `page.update()` works correctly on all platforms

### Progress bars for fast tasks
- Determinate progress bars (`value=0` to `value=1.0`) are invisible for tasks completing in <1 second — macOS can't render frames fast enough
- ✅ Use indeterminate mode (`progress_bar.value = None`) for an animated sliding bar that always shows activity
- Percentage text updates alongside the indeterminate bar

### Platform detection
- `page.web` — `True` if running in browser, `False` if desktop
- Use this to conditionally show/hide desktop-only features (e.g., "Open in Finder")
- `page.window_width`/`page.window_height` should only be set when `not page.web`

### URL opening
- ❌ `webbrowser.open(url)` — doesn't work reliably in web mode
- ✅ `page.launch_url(url)` — cross-platform, works on both desktop and web

## File Conventions
- `uploads/` — runtime directory for web file uploads, gitignored
- `settings.json` — user settings, gitignored (tracked template is `default_settings.json`)
- `docx_to_csv/` — core conversion logic (pure Python, no Flet dependency)
- `gui_app.py` — Flet UI, all UI code in one file
- Tests live in `tests/` directory

## Git Conventions
- Main branch: `main`
- Versioning: Git tags (e.g., `v1.0.0`)
- CI/CD: GitHub Actions (`.github/workflows/build-and-release.yml`) packages desktop apps for macOS + Windows
