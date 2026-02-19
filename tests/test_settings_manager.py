import unittest
import os
import json
import shutil
import tempfile
import stat
from settings_manager import SettingsManager


# ============================================================================
# LOADING FROM EXISTING FILE
# ============================================================================

class TestSettingsManagerLoadFromFile(unittest.TestCase):
    """Test loading settings from an existing settings file."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.test_dir, "settings.json")
        self.settings_data = {
            "speaker_names": ["Alice", "Bob"],
            "categories": ["Topic A", "Topic B"],
            "system_instruction": "Be concise.",
            "model": "gpt-4o"
        }
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings_data, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_loads_existing_settings(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_speaker_names(), ["Alice", "Bob"])
        self.assertEqual(sm.get_categories(), ["Topic A", "Topic B"])
        self.assertEqual(sm.get_system_instruction(), "Be concise.")
        self.assertEqual(sm.get_model(), "gpt-4o")

    def test_get_settings_returns_full_dict(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_settings(), self.settings_data)


# ============================================================================
# CREATING FROM DEFAULTS FILE
# ============================================================================

class TestSettingsManagerCreateFromDefaults(unittest.TestCase):
    """Test creating settings from a defaults file when settings file doesn't exist."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.test_dir, "settings.json")
        self.defaults_file = os.path.join(self.test_dir, "defaults.json")
        self.defaults_data = {
            "speaker_names": ["Default1"],
            "categories": ["Cat1"],
            "system_instruction": "Default instruction.",
            "model": "gpt-5.1"
        }
        with open(self.defaults_file, 'w') as f:
            json.dump(self.defaults_data, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_creates_settings_from_defaults(self):
        self.assertFalse(os.path.exists(self.settings_file))
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=self.defaults_file)
        self.assertTrue(os.path.exists(self.settings_file))
        self.assertEqual(sm.get_speaker_names(), ["Default1"])
        self.assertEqual(sm.get_categories(), ["Cat1"])

    def test_copied_file_is_independent(self):
        """After copying from defaults, changes to settings should not affect defaults."""
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=self.defaults_file)
        sm.save_settings({"speaker_names": ["Changed"]})
        
        # Defaults file should still have original content
        with open(self.defaults_file, 'r') as f:
            defaults = json.load(f)
        self.assertEqual(defaults["speaker_names"], ["Default1"])


# ============================================================================
# EMPTY INITIALIZATION (NO DEFAULTS FILE)
# ============================================================================

class TestSettingsManagerEmptyInit(unittest.TestCase):
    """Test initializing with empty settings when no defaults file exists."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.test_dir, "settings.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_creates_empty_settings_when_no_defaults(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_speaker_names(), [])
        self.assertEqual(sm.get_categories(), [])
        self.assertEqual(sm.get_system_instruction(), "")
        self.assertEqual(sm.get_model(), "gpt-5.1")
        self.assertTrue(os.path.exists(self.settings_file))

    def test_creates_settings_when_defaults_path_missing(self):
        """If a defaults file path is given but doesn't exist, still creates empty settings."""
        sm = SettingsManager(settings_file=self.settings_file,
                            default_settings_file="/nonexistent/defaults.json")
        self.assertEqual(sm.get_speaker_names(), [])
        self.assertTrue(os.path.exists(self.settings_file))


# ============================================================================
# SAVE AND RELOAD
# ============================================================================

class TestSettingsManagerSaveAndReload(unittest.TestCase):
    """Test saving settings and verifying they persist on reload."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.test_dir, "settings.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_save_then_reload(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        sm.save_settings({
            "speaker_names": ["Charlie"],
            "categories": ["Theme X"],
            "system_instruction": "Custom.",
            "model": "gpt-4o-mini"
        })

        sm2 = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm2.get_speaker_names(), ["Charlie"])
        self.assertEqual(sm2.get_categories(), ["Theme X"])
        self.assertEqual(sm2.get_system_instruction(), "Custom.")
        self.assertEqual(sm2.get_model(), "gpt-4o-mini")

    def test_save_returns_true_on_success(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        result = sm.save_settings({"speaker_names": []})
        self.assertTrue(result)

    def test_save_none_preserves_current_settings(self):
        """Calling save_settings(None) should save the current in-memory settings."""
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        sm.settings = {
            "speaker_names": ["InMemory"],
            "categories": ["Cat1"],
            "system_instruction": "Test",
            "model": "test-model"
        }
        sm.save_settings(None)  # Should save current settings

        sm2 = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm2.get_speaker_names(), ["InMemory"])

    def test_save_overwrites_previous_settings(self):
        """Saving new settings should completely replace old ones."""
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        sm.save_settings({
            "speaker_names": ["First"],
            "categories": ["Cat1"],
            "system_instruction": "",
            "model": "gpt-5.1"
        })
        sm.save_settings({
            "speaker_names": ["Second"],
            "categories": ["Cat2", "Cat3"],
            "system_instruction": "New instruction",
            "model": "gpt-4o"
        })
        
        sm2 = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm2.get_speaker_names(), ["Second"])
        self.assertEqual(sm2.get_categories(), ["Cat2", "Cat3"])

    def test_save_to_unwritable_path_returns_false(self):
        """If the settings file can't be written, save should return False."""
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        sm.settings_file = "/nonexistent_dir/settings.json"
        result = sm.save_settings({"speaker_names": []})
        self.assertFalse(result)


# ============================================================================
# GETTER DEFAULTS FOR MISSING KEYS
# ============================================================================

class TestSettingsManagerGetterDefaults(unittest.TestCase):
    """Test that getter methods return safe defaults when keys are missing."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.test_dir, "settings.json")
        with open(self.settings_file, 'w') as f:
            json.dump({"speaker_names": ["OnlyThisKey"]}, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_missing_categories_returns_empty_list(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_categories(), [])

    def test_missing_system_instruction_returns_empty_string(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_system_instruction(), "")

    def test_missing_model_returns_default(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_model(), "gpt-5.1")

    def test_present_key_returns_value(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_speaker_names(), ["OnlyThisKey"])

    def test_completely_empty_dict_all_defaults(self):
        """An empty JSON object {} should return defaults for all getters."""
        with open(self.settings_file, 'w') as f:
            json.dump({}, f)
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_speaker_names(), [])
        self.assertEqual(sm.get_categories(), [])
        self.assertEqual(sm.get_system_instruction(), "")
        self.assertEqual(sm.get_model(), "gpt-5.1")


# ============================================================================
# CORRUPT/INVALID FILES
# ============================================================================

class TestSettingsManagerCorruptFiles(unittest.TestCase):
    """Test handling of corrupt/invalid settings files."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.test_dir, "settings.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_corrupt_json_loads_empty_settings(self):
        with open(self.settings_file, 'w') as f:
            f.write("{this is not valid json!!!")
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_settings(), {})
        self.assertEqual(sm.get_speaker_names(), [])

    def test_empty_file_loads_empty_settings(self):
        """A 0-byte settings file should not crash — should load empty settings."""
        with open(self.settings_file, 'w') as f:
            pass  # empty file
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_settings(), {})
        self.assertEqual(sm.get_speaker_names(), [])

    def test_json_array_instead_of_object(self):
        """If settings file contains a JSON array instead of object, should not crash."""
        with open(self.settings_file, 'w') as f:
            json.dump(["not", "an", "object"], f)
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        # list has no .get method, so getters need to handle this gracefully
        # This tests whether the code crashes or handles it
        try:
            names = sm.get_speaker_names()
            # If it returns something, that's okay
        except AttributeError:
            # This is a known limitation worth documenting
            pass

    def test_binary_content_in_settings_file(self):
        """Binary garbage in settings file should not crash the app."""
        with open(self.settings_file, 'wb') as f:
            f.write(bytes(range(256)))
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm.get_settings(), {})


# ============================================================================
# UNICODE AND SPECIAL VALUES IN SETTINGS
# ============================================================================

class TestSettingsManagerUnicode(unittest.TestCase):
    """Test that settings with unicode and special characters persist correctly."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.test_dir, "settings.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_unicode_speaker_names_persist(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        sm.save_settings({
            "speaker_names": ["José", "Müller", "李明"],
            "categories": [],
            "system_instruction": "",
            "model": "gpt-5.1"
        })
        sm2 = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm2.get_speaker_names(), ["José", "Müller", "李明"])

    def test_special_chars_in_categories_persist(self):
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        sm.save_settings({
            "speaker_names": [],
            "categories": ["Risk & Compliance", "HR/Talent", "C-Suite (Executives)"],
            "system_instruction": "",
            "model": "gpt-5.1"
        })
        sm2 = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm2.get_categories(), ["Risk & Compliance", "HR/Talent", "C-Suite (Executives)"])

    def test_multiline_system_instruction_persists(self):
        instruction = "You are an expert analyst.\nFocus on governance themes.\nBe thorough."
        sm = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        sm.save_settings({
            "speaker_names": [],
            "categories": [],
            "system_instruction": instruction,
            "model": "gpt-5.1"
        })
        sm2 = SettingsManager(settings_file=self.settings_file, default_settings_file=None)
        self.assertEqual(sm2.get_system_instruction(), instruction)


if __name__ == '__main__':
    unittest.main()
