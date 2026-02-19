import json
import os
import shutil

class SettingsManager:
    def __init__(self, settings_file="settings.json", default_settings_file="default_settings.json"):
        self.settings_file = settings_file
        self.default_settings_file = default_settings_file
        self.settings = {}
        self._load_or_create_settings()

    def _load_or_create_settings(self):
        """Loads settings from file, or creates it from defaults if missing."""
        if not os.path.exists(self.settings_file):
            if self.default_settings_file and os.path.exists(self.default_settings_file):
                try:
                    shutil.copy(self.default_settings_file, self.settings_file)
                    print(f"Created {self.settings_file} from defaults.")
                except Exception as e:
                    print(f"Error copying default settings: {e}")
                    # Fallback to empty context if copy fails, though unlikely
                    self.settings = {}
            else:
                # If defaults are also missing, initialize with empty structure
                print(f"Warning: {self.default_settings_file} not found. Initializing empty settings.")
                self.settings = {
                    "speaker_names": [],
                    "categories": [],
                    "system_instruction": "",
                    "model": "gpt-5.1"
                }
                self.save_settings()
                return

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = {}

    def get_settings(self):
        return self.settings

    def save_settings(self, new_settings=None):
        if new_settings is not None:
            self.settings = new_settings
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            print(f"Settings saved to {self.settings_file}")
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_speaker_names(self):
        return self.settings.get("speaker_names", [])

    def get_categories(self):
        return self.settings.get("categories", [])
    
    def get_system_instruction(self):
        return self.settings.get("system_instruction", "")

    def get_model(self):
        return self.settings.get("model", "gpt-5.1")
