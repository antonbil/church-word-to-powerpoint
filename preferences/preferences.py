import json
class Preferences:
    def __init__(self):
        self.preferences_name = "preferences.json"
        #print("load preferences")
        self.preferences = self.load_preferences()

    def load_preferences(self):
            """ Load the json preferences file if it exists.  Otherwise, set some defaults.
            The PREF dictionary keys have the same values as the form input keys."""
            preferences = {}
            try:
                with open(self.preferences_name, "r") as in_file:
                    preferences = json.load(in_file)
                    #print("preferences loaded", preferences)
            except:
                #print("error in loading preferences")
                preferences = {'is_save_time_left': False, 'sites_list': ["OostKapelle", "Middelburg"],
                               'events_list':["Interne competitie Oostkapelle", "Zeeuwse competitie"],
                               'players':["Anton Bil"], "start_entry_mode": False}
            return preferences

    def save_preferences(self):
        """Write out the PREF dictionary to a json preferences file"""
        with open(self.preferences_name, "w") as out_file:
            json.dump(self.preferences, out_file, indent=4)

