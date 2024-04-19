#!python
"""
This file contains a Dialog class that handles the preferences dialog.
It also contains two utility functions to load and save the preferences to a json file.

"""

import PySimpleGUI as sg
import json
from datetime import date

PREF = {}
"""
        pgn_game.headers['Event'] = header_dialog.event
        pgn_game.headers['White'] = header_dialog.white
        pgn_game.headers['Black'] = header_dialog.black
        pgn_game.headers['Site'] = header_dialog.site
        pgn_game.headers['Date'] = header_dialog.date
        pgn_game.headers['Round'] = header_dialog.round
"""

class HeaderDialog:
    """header dialog class"""
    def __init__(self, white, black, sites_list, events_list, players, pgn_game):
        self.ok = False
        self.pgn_game = pgn_game
        self.white = white
        self.black = black
        self.result = "*"
        self.event = ""
        self.site = ""
        self.round = ""
        self.add_to_library = False
        current_date = pgn_game.headers['Date'].replace("/", "").replace("?", "").replace(".", "")
        self.date = pgn_game.headers['Date']
        if len(self.date) == 0:
            today = date.today()
            formatted_date = today.strftime('%Y/%m/%d')
            self.date = formatted_date
        PREF = {'white': white, 'black': black, 'date': self.date}
        results = ["1-0", "1/2-1/2", "0-1", "*"]
        rounds = [str(l) for l in range(1,50)]
        sg.theme('default')
        self.layout = [
            [[sg.Text("Event:"),
              sg.Combo(events_list, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                       readonly=False, key='event', default_value=self.default_value("Event"))]],
            [[sg.Text("Site:"),
              sg.Combo(sites_list, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                       readonly=False, key='site', default_value=self.default_value("Site"))]],
            [[sg.Text("Date:"),
              sg.Input(key='date',
                       size=(20, 1)), sg.CalendarButton('Calendar', target='date',
                                                                    format='%Y/%m/%d',
                                                                    locale='nl_NL',
                                                                    begin_at_sunday_plus=1)]],
            [[sg.Text("Round:"),
              sg.Combo(rounds, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                       readonly=False, key='round', default_value=self.default_value("Round"))]],
            [[sg.Text("White:"),
                    sg.Combo(players, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                                readonly=False, key='white', default_value=self.default_value("White"))]],
            [[sg.Text("Black:"),
             sg.Combo(players, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                       readonly=False, key='black', default_value=self.default_value("Black"))]],
            [[sg.Text("Result:"),
              sg.Combo(results, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                       readonly=False, key='result', default_value=self.default_value("Result"))]],
            [
              sg.CBox('Add to library', key='add_to_library',
                      default=False)],
                    [sg.Button("Save"), sg.Button("Close")]
                    ]

        window = sg.Window("Game data", self.layout, font=("Ubuntu", 12), size=(600, 450),
                        finalize=True, modal=True, keep_on_top=True)

        sg.fill_form_with_values(window=window, values_dict=PREF)
        while True:
            event, values = window.read()
            if event in ("Close", sg.WIN_CLOSED):
                break
            elif event == "Save":
                # load the PREF dictionary with the fields values.
                self.white = values['white']
                self.black = values['black']
                self.result = values['result']
                self.event = values['event']
                self.site = values['site']
                self.date = str(values['date'])
                self.round = values['round']
                self.add_to_library = values['add_to_library']
                self.ok = True
                break

        window.close()

    def default_value(self, title):
        s = self.pgn_game.headers[title]
        if "?" in s:
            return ""
        return s


def load_preferences():
    """ Load the json preferences file if it exists.  Otherwise, set some defaults.
    The PREF dictionary keys have the same values as the form input keys."""
    global PREF
    try:
        with open("preferences.json", "r") as in_file:
            PREF = json.load(in_file)
    except FileNotFoundError:
        PREF = {'white': 'Player 1', 'black': 'Player 2'}


def save_preferences():
    """Write out the PREF dictionary to a json preferences file"""
    with open("preferences.json", "w") as out_file:
        json.dump(PREF, out_file, indent=4)


if __name__ == '__main__':
    load_preferences()
    Dialog()