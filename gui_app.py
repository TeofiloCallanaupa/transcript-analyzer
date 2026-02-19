import flet as ft
import os
import sys
import threading
import time
import json
import webbrowser

# Import the logic functions from our refactored scripts
# Ensure these scripts are in the same directory or PYTHONPATH
try:
    from docx_to_csv.docx_to_csv import process_docx_files
    from csv_classifier import process_csv_with_llm
    from settings_manager import SettingsManager
except ImportError as e:
    print(f"Critical Error: Could not import helper scripts: {e}")
    # Try different path for PyInstaller bundle if needed, 
    # but usually the above works if the folder is in path.
    # Fallback for flat structure if build flattens it (unlikely with onedir)
    try:
        from docx_to_csv import process_docx_files
        from settings_manager import SettingsManager
    except:
        pass
    print(f"DEBUG: sys.path: {sys.path}")
    sys.exit(1)

def main(page: ft.Page):
    page.title = "Transcript Analyzer"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 900
    page.window_height = 950
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO  # Enable scrolling

    # --- Initialize Settings ---
    settings_manager = SettingsManager()
    
    # --- State Variables ---
    selected_files = []
    processing = False
    csv_output_path = None
    cancel_requested = False
    current_thread = None
    
    # --- UI Elements ---
    
    # Header
    title = ft.Text("Transcript Analyzer", size=32, weight=ft.FontWeight.BOLD)
    subtitle = ft.Text("Convert Interview DOCX to CSV and Classify with AI", size=16, color=ft.Colors.GREY_700)
    
    # API Key Input
    api_key_field = ft.TextField(
        label="OpenAI API Key", 
        password=True, 
        can_reveal_password=True, 
        hint_text="sk-...", 
        width=500
    )
    
    # Model Selection
    model_dropdown = ft.Dropdown(
        label="GPT Model",
        value=settings_manager.get_model(),
        width=300,
        options=[
            ft.dropdown.Option("gpt-5.1"),
            ft.dropdown.Option("gpt-5-mini"),
            ft.dropdown.Option("gpt-4o"),
            ft.dropdown.Option("gpt-4o-mini"),
        ],
        hint_text="Select model"
    )
    
    model_warning = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_700, size=20),
                ft.Text("Model Selection Warning", weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700)
            ]),
            ft.Text(
                "Only change this if you know the exact model name. Using an incorrect model name will cause errors.",
                size=12,
                color=ft.Colors.GREY_700
            ),
            ft.TextButton(
                "View OpenAI Pricing & Models →",
                icon=ft.Icons.OPEN_IN_NEW,
                on_click=lambda _: webbrowser.open("https://platform.openai.com/docs/pricing")
            )
        ]),
        bgcolor=ft.Colors.ORANGE_50,
        border=ft.Border.all(1, ft.Colors.ORANGE_300),
        border_radius=5,
        padding=10,
    )
    
    # File Selection Display
    files_text = ft.Text("No files selected", italic=True, color=ft.Colors.GREY_500)
    files_chip_row = ft.Row(wrap=True, spacing=5, run_spacing=5)
    
    # Settings reminder (shown after files are selected)
    settings_reminder = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_700, size=20),
            ft.Text(
                "Tip: Make sure the speaker names in Settings (⚙️) match the names in your transcripts, "
                "otherwise the app won't be able to extract any statements.",
                size=13, color=ft.Colors.BLUE_800, expand=True
            ),
        ]),
        bgcolor=ft.Colors.BLUE_50,
        border=ft.Border.all(1, ft.Colors.BLUE_200),
        border_radius=5,
        padding=10,
        visible=False,
    )
    
    # Step status indicators
    step1_status = ft.Text("⏸ Pending", color=ft.Colors.GREY_500, weight=ft.FontWeight.BOLD)
    step2_status = ft.Text("⏸ Pending", color=ft.Colors.GREY_500, weight=ft.FontWeight.BOLD)
    
    # Error display
    error_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_700, size=24),
                ft.Text("Error", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700, size=16)
            ]),
            ft.Text("", size=13, selectable=True, color=ft.Colors.RED_900)
        ]),
        bgcolor=ft.Colors.RED_50,
        border=ft.Border.all(2, ft.Colors.RED_300),
        border_radius=8,
        padding=15,
        visible=False
    )
    
    def show_error(message):
        """Display error in a prominent container"""
        error_text = error_container.content.controls[1]
        error_text.value = message
        error_container.visible = True
        page.update()
    
    def hide_error():
        """Hide error container"""
        error_container.visible = False
        page.update()
    
    # CSV result display
    csv_path_text = ft.Text("", selectable=True, size=12)
    csv_result_container = ft.Container(
        content=ft.Column([
            ft.Text("CSV File Created:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
            csv_path_text,
            ft.Button(
                "Open in Finder",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: reveal_in_finder(csv_output_path) if csv_output_path else None
            )
        ]),
        bgcolor=ft.Colors.GREEN_50,
        border=ft.Border.all(2, ft.Colors.GREEN_300),
        border_radius=8,
        padding=15,
        visible=False
    )
    
    # Final result display
    final_path_text = ft.Text("", selectable=True, size=12)
    final_result_container = ft.Container(
        content=ft.Column([
            ft.Text("✓ Analysis Complete!", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700, size=18),
            ft.Text("Classified CSV saved to:", weight=ft.FontWeight.BOLD),
            final_path_text,
            ft.Button(
                "Open in Finder",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda _: reveal_in_finder(csv_output_path) if csv_output_path else None
            )
        ]),
        bgcolor=ft.Colors.BLUE_50,
        border=ft.Border.all(2, ft.Colors.BLUE_300),
        border_radius=8,
        padding=15,
        visible=False
    )
    
    # Logs
    log_view = ft.Column(scroll=ft.ScrollMode.AUTO, height=200, expand=True)
    log_container = ft.Container(
        content=log_view,
        border=ft.Border.all(1, ft.Colors.GREY_300),
        border_radius=5,
        padding=10,
        bgcolor=ft.Colors.GREY_50,
        height=250
    )

    # Progress Bar
    progress_bar = ft.ProgressBar(width=600, visible=False)

    # --- Settings Dialog ---
    
    speaker_input = ft.TextField(
        multiline=True, 
        min_lines=5, 
        max_lines=10, 
        label="Speaker Names (one per line)",
        hint_text="Example:\nLaura\nDana\nInterviewerM"
    )
    
    categories_input = ft.TextField(
        multiline=True, 
        min_lines=5, 
        max_lines=10, 
        label="Classification Categories (one per line)",
        hint_text="Example:\nGovernance Gaps\nEmployee Trust\nMarket Pressures"
    )
    
    instruction_input = ft.TextField(
        multiline=True,
        min_lines=3,
        max_lines=8,
        label="AI System Instruction (Advanced)",
        hint_text="You are an expert text analyst..."
    )

    def close_settings(e):
        page.pop_dialog()
        page.update()

    def save_settings_submit(e):
        # Parse inputs
        speakers = [s.strip() for s in speaker_input.value.split('\n') if s.strip()]
        categories = [c.strip() for c in categories_input.value.split('\n') if c.strip()]
        instruction = instruction_input.value.strip()
        
        # Save
        new_settings = settings_manager.get_settings()
        new_settings["speaker_names"] = speakers
        new_settings["categories"] = categories
        new_settings["system_instruction"] = instruction
        settings_manager.save_settings(new_settings)
        
        log_message("Settings updated.")
        page.pop_dialog()
        page.update()

    settings_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Configuration"),
        content=ft.Column([
            ft.Text("Adjust how the app processes your files.", size=14, color=ft.Colors.GREY_700),
            
            ft.Divider(),
            
            # --- Extraction Section ---
            ft.Text("📝 Extraction — Speaker Names", weight=ft.FontWeight.BOLD, size=14),
            ft.Text("Define who the speakers are in your DOCX transcripts.", size=12, italic=True, color=ft.Colors.GREY_600),
            speaker_input,
            ft.Container(
                content=ft.Text("Example:\nLaura\nInterviewerM", size=11, font_family="monospace", color=ft.Colors.GREY_600),
                bgcolor=ft.Colors.GREY_100, padding=5, border_radius=4
            ),
            
            ft.Divider(),
            
            # --- Classification Section ---
            ft.Text("🏷 Classification — Categories", weight=ft.FontWeight.BOLD, size=14),
            ft.Text("Define the themes/categories for the AI to detect.", size=12, italic=True, color=ft.Colors.GREY_600),
            categories_input,
            ft.Container(
                content=ft.Text("Example:\nPositive Sentiment\nNegative Sentiment", size=11, font_family="monospace", color=ft.Colors.GREY_600),
                bgcolor=ft.Colors.GREY_100, padding=5, border_radius=4
            ),
            
            ft.Divider(),
            
            # --- Advanced Section ---
            ft.Text("⚙️ Advanced — System Instruction", weight=ft.FontWeight.BOLD, size=14),
            ft.Text("Customize the core instruction given to the AI.", size=12, italic=True, color=ft.Colors.GREY_600),
            instruction_input,
            
        ], width=600, height=500, scroll=ft.ScrollMode.AUTO, tight=True),
        actions=[
            ft.TextButton("Cancel", on_click=close_settings),
            ft.TextButton("Save Settings", on_click=save_settings_submit),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_settings_click(e):
        # Load current settings into fields
        speaker_input.value = "\n".join(settings_manager.get_speaker_names())
        categories_input.value = "\n".join(settings_manager.get_categories())
        instruction_input.value = settings_manager.get_system_instruction()
        
        page.show_dialog(settings_dialog)
        page.update()

    # --- Event Handlers ---

    def log_message(msg):
        """Append message to the log window."""
        log_view.controls.append(ft.Text(f"[{time.strftime('%H:%M:%S')}] {msg}", size=12, font_family="monospace"))
        page.update()

    def update_file_display():
        """Refresh the file list UI (chips + text) based on selected_files."""
        files_chip_row.controls.clear()
        if selected_files:
            for file_path in selected_files:
                chip = ft.Chip(
                    label=ft.Text(os.path.basename(file_path), size=12),
                    delete_icon=ft.Icons.CLOSE,
                    on_delete=lambda e, path=file_path: remove_file(path),
                )
                files_chip_row.controls.append(chip)
            files_text.value = f"{len(selected_files)} file(s) selected"
            files_text.color = ft.Colors.BLACK
            files_text.italic = False
            btn_convert.disabled = False
            settings_reminder.visible = True
        else:
            files_text.value = "No files selected"
            files_text.color = ft.Colors.GREY_500
            files_text.italic = True
            btn_convert.disabled = True
            settings_reminder.visible = False
        page.update()

    def remove_file(path):
        """Remove a single file from the selected list."""
        nonlocal selected_files
        selected_files = [f for f in selected_files if f != path]
        log_message(f"Removed: {os.path.basename(path)}")
        update_file_display()

    async def handle_pick_files(e):
        nonlocal selected_files
        files = await ft.FilePicker().pick_files(allow_multiple=True, allowed_extensions=["docx"])
        if files:
            new_paths = [f.path for f in files]
            # Append without duplicates
            existing = set(selected_files)
            added = [p for p in new_paths if p not in existing]
            selected_files.extend(added)
            if added:
                log_message(f"Added {len(added)} file(s). Total: {len(selected_files)}.")
            else:
                log_message("No new files added (already selected).")
            update_file_display()

    def reveal_in_finder(path):
        """Open Finder and select the file"""
        import subprocess
        subprocess.run(["open", "-R", path])

    def convert_to_csv(e):
        nonlocal processing, csv_output_path, cancel_requested, current_thread
        if processing:
            return

        if not selected_files:
            log_message("Error: No files selected.")
            return
        
        cancel_requested = False
        processing = True
        btn_convert.disabled = True
        btn_select.disabled = True
        btn_cancel.visible = True
        progress_bar.visible = True
        step1_status.value = "⏳ Converting..."
        step1_status.color = ft.Colors.ORANGE_700
        csv_result_container.visible = False
        hide_error()
        page.update()

        # Run in a separate thread
        current_thread = threading.Thread(target=run_conversion, args=(selected_files,))
        current_thread.start()

    def run_conversion(files):
        nonlocal processing, csv_output_path, cancel_requested
        try:
            log_message("--- Step 1: Converting DOCX to CSV ---")
            
            output_csv_name = f"analysis_output_{int(time.time())}.csv"
            output_dir = os.path.dirname(files[0])
            csv_output_path = os.path.join(output_dir, output_csv_name)
            
            # Load speakers from settings
            speakers = settings_manager.get_speaker_names()
            log_message(f"Using {len(speakers)} speaker names from settings.")

            log_message(f"Converting {len(files)} document(s)...")
            
            # Pass speaker list to conversion function
            process_docx_files(files, csv_output_path, log_callback=log_message, speaker_list=speakers)
            
            if cancel_requested:
                log_message("Conversion cancelled by user.")
                step1_status.value = "⏸ Cancelled"
                step1_status.color = ft.Colors.GREY_500
                return
            
            if not os.path.exists(csv_output_path):
                step1_status.value = "❌ No matches"
                step1_status.color = ft.Colors.RED_700
                show_error(
                    "No statements were extracted from your files. "
                    "This usually means the speaker names in Settings (⚙️) don't match "
                    "the names in your transcripts. Check the Activity Log below for details."
                )
                return

            log_message(f"✓ CSV created: {csv_output_path}")
            step1_status.value = "✓ Complete"
            step1_status.color = ft.Colors.GREEN_700
            
            # Show CSV result
            csv_path_text.value = csv_output_path
            csv_result_container.visible = True
            
            # Enable step 2
            btn_classify.disabled = False

        except Exception as e:
            log_message(f"ERROR: {e}")
            step1_status.value = "❌ Failed"
            step1_status.color = ft.Colors.RED_700
            show_error(f"Conversion error: {str(e)}")
        finally:
            processing = False
            btn_convert.disabled = False
            btn_select.disabled = False
            btn_cancel.visible = False
            progress_bar.visible = False
            page.update()

    def classify_with_ai(e):
        nonlocal processing, cancel_requested, current_thread
        if processing:
            return

        api_key = api_key_field.value.strip()
        if not api_key:
            log_message("Error: Please enter an OpenAI API Key.")
            show_error("Please enter an OpenAI API Key.")
            return

        if not csv_output_path or not os.path.exists(csv_output_path):
            log_message("Error: No CSV file to classify.")
            show_error("No CSV file to classify. Please run Step 1 first.")
            return
        
        model = model_dropdown.value
        if not model:
            log_message("Error: Please select a model.")
            show_error("Please select a GPT model.")
            return
        
        # Save model selection to settings
        settings = settings_manager.get_settings()
        settings["model"] = model
        settings_manager.save_settings(settings)
        
        cancel_requested = False
        processing = True
        btn_classify.disabled = True
        btn_cancel.visible = True
        progress_bar.visible = True
        step2_status.value = "⏳ Classifying..."
        step2_status.color = ft.Colors.ORANGE_700
        final_result_container.visible = False
        hide_error()
        page.update()

        # Run in a separate thread
        current_thread = threading.Thread(target=run_classification, args=(csv_output_path, api_key, model))
        current_thread.start()

    def run_classification(csv_path, key, model):
        nonlocal processing, cancel_requested
        try:
            log_message("--- Step 2: AI Classification ---")
            log_message(f"Using model: {model}")
            
            # Load settings
            categories = settings_manager.get_categories()
            instruction = settings_manager.get_system_instruction()
            
            log_message(f"Using {len(categories)} classification categories.")
            log_message("Classifying with OpenAI (this may take a while)...")
            
            # Pass settings to the classifier
            process_csv_with_llm(
                csv_path, 
                api_key=key, 
                model=model, 
                log_callback=log_message,
                categories=categories,
                system_instruction=instruction
            )
            
            if cancel_requested:
                log_message("Classification cancelled by user.")
                step2_status.value = "⏸ Cancelled"
                step2_status.color = ft.Colors.GREY_500
                return

            log_message(f"✓ Classification complete!")
            step2_status.value = "✓ Complete"
            step2_status.color = ft.Colors.GREEN_700
            
            # Show final result
            final_path_text.value = csv_path
            final_result_container.visible = True

        except Exception as e:
            error_msg = str(e)
            log_message(f"ERROR: {error_msg}")
            step2_status.value = "❌ Failed"
            step2_status.color = ft.Colors.RED_700
            
            # Check for common errors
            if "insufficient_quota" in error_msg.lower() or "quota" in error_msg.lower():
                show_error("⚠️ Insufficient OpenAI credits. Please add credits to your account at https://platform.openai.com/account/billing")
            elif "invalid_api_key" in error_msg.lower():
                show_error("❌ Invalid API key. Please check your OpenAI API key.")
            elif "model" in error_msg.lower() and "does not exist" in error_msg.lower():
                show_error(f"❌ Model '{model}' not found. Please check the model name or visit the pricing page.")
            else:
                show_error(f"Classification error: {error_msg}")
        finally:
            processing = False
            btn_classify.disabled = False
            btn_cancel.visible = False
            progress_bar.visible = False
            page.update()
    
    def cancel_processing(e):
        nonlocal cancel_requested
        cancel_requested = True
        log_message("⏸ Cancellation requested...")
        btn_cancel.disabled = True
        page.update()

    # --- Buttons ---
    btn_settings = ft.IconButton(
        icon=ft.Icons.SETTINGS,
        tooltip="Configuration Settings",
        on_click=open_settings_click
    )

    btn_select = ft.Button(
        "Select DOCX Files", 
        icon=ft.Icons.UPLOAD_FILE, 
        on_click=handle_pick_files
    )

    btn_convert = ft.Button(
        "Step 1: Convert to CSV", 
        icon=ft.Icons.TRANSFORM, 
        bgcolor=ft.Colors.GREEN_600,
        color=ft.Colors.WHITE,
        on_click=convert_to_csv,
        disabled=True
    )

    btn_classify = ft.Button(
        "Step 2: Classify with AI", 
        icon=ft.Icons.PSYCHOLOGY, 
        bgcolor=ft.Colors.BLUE_600,
        color=ft.Colors.WHITE,
        on_click=classify_with_ai,
        disabled=True
    )
    
    btn_cancel = ft.Button(
        "Cancel",
        icon=ft.Icons.CANCEL,
        bgcolor=ft.Colors.RED_600,
        color=ft.Colors.WHITE,
        on_click=cancel_processing,
        visible=False
    )

    # --- Layout Assembly ---
    page.add(
        ft.Row([title, btn_settings], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        subtitle,
        ft.Divider(),
        
        # File selection
        ft.Text("1. Select Files", size=18, weight=ft.FontWeight.BOLD),
        ft.Row([btn_select], alignment=ft.MainAxisAlignment.START),
        files_text,
        files_chip_row,
        settings_reminder,
        
        ft.Divider(),
        
        # Step 1: Convert
        ft.Row([
            ft.Text("2. Convert to CSV", size=18, weight=ft.FontWeight.BOLD),
            step1_status
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        btn_convert,
        csv_result_container,
        
        ft.Divider(),
        
        # Step 2: Classify
        ft.Row([
            ft.Text("3. Classify with AI", size=18, weight=ft.FontWeight.BOLD),
            step2_status
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        api_key_field,
        ft.Row([
            model_dropdown,
        ]),
        model_warning,
        btn_classify,
        final_result_container,
        
        ft.Divider(),
        
        # Progress, cancel, and error
        ft.Row([
            progress_bar,
            btn_cancel
        ], alignment=ft.MainAxisAlignment.START),
        error_container,
        
        # Logs
        ft.Text("Activity Log:", weight=ft.FontWeight.BOLD),
        log_container,
    )

if __name__ == "__main__":
    ft.run(main)
