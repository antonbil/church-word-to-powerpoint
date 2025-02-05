import json
import os

class Settings:
    """
    Loads the settings from settings.json and provides access to these settings.
    """

    def __init__(self, current_dir):
        """
        Initializes the Settings class and loads the settings from the JSON file.

        Args:
            current_dir (str): The path to the directory where the settings.json file is located.
        """
        self.settings = {}
        self.current_dir = current_dir
        self.json_filename = self.get_json_filename()
        self.load_settings()

    def get_json_filename(self):
        """
        Returns the full path to the settings.json file.
        """
        return os.path.join(self.current_dir, "settings.json")

    def load_settings(self):
        """
        Loads the settings from the JSON file.
        """
        try:
            with open(self.json_filename, "r") as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            print(f"Error: Settings file '{self.json_filename}' not found.")
            self.settings = {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON syntax in '{self.json_filename}'.")
            self.settings = {}

    def get_setting(self, key, default=None):
        """
        Retrieves a specific setting.

        Args:
            key (str): The name of the setting.
            default (any): The default value to return if the setting is not found.

        Returns:
            any: The value of the setting, or the default value if the setting is not found.
        """
        return self.settings.get(key, default)

    def get_tags(self):
        """
        Returns the tags dictionary
        """
        return self.get_setting("tags",{})