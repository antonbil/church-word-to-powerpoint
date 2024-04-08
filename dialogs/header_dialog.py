#!python
"""
This file contains a Dialog class that handles the preferences dialog.
It also contains two utility functions to load and save the preferences to a json file.

"""

import PySimpleGUI as sg
import json
from datetime import date

PREF = {}


class HeaderDialog:
    """header dialog class"""
    def __init__(self, white, black, sites_list, events_list, players):
        self.white = white
        self.black = black
        self.result = "*"
        self.event = ""
        self.site = ""
        self.round = ""
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
                       readonly=False, key='event')]],
            [[sg.Text("Site:"),
              sg.Combo(sites_list, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                       readonly=False, key='site')]],
            [[sg.Text("Date:"),
              sg.Input(key='date', size=(20, 1)), sg.CalendarButton('Calendar', target='date',
                                                                    format='%Y/%m/%d',
                                                                    locale='nl_NL',
                                                                    begin_at_sunday_plus=1)]],
            [[sg.Text("Round:"),
              sg.Combo(rounds, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                       readonly=False, key='round')]],
            [[sg.Text("White:"),
                    sg.Combo(players, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                                readonly=False, key='white')]],
            [[sg.Text("Black:"),
             sg.Combo(players, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                       readonly=False, key='black')]],
            [[sg.Text("Result:"),
              sg.Combo(results, font=('Arial Bold', 14), expand_x=True, enable_events=True,
                       readonly=False, key='result')]],
                    [sg.Button("Save"), sg.Button("Close")]
                    ]

        window = sg.Window("Game data", self.layout, font=("Ubuntu", 12), size=(500, 350),
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
                self.date = values['date']
                self.round = values['round']
                break

        window.close()


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