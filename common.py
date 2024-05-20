menu_def_entry = [
        ['&Mode', ['Neutral', "Play", "PGN-Viewer", 'Variations Edit']],
        ['&Move', ["Back", '---', "Restore alternative"]],
        ['&Game', ['Save', 'Clear', 'Analyse game']],
         ['Help', ["Gui"]],
]
menu_def_annotate = [
        ['&Mode', ['Neutral', "Play", "PGN-Viewer", 'PGN Move entry']],
        ['&Move', ['Previous', "Next", '---', "Promote alternative", "Restore alternative", "Remove alternative"
                   , '---', 'Remove from this move onward']],
        ['&Annotate', ['Comment', '---', 'Alternative', "Alternative manual", '---', 'Manual variation']],
        ['&Game', ['Save', 'Clear', 'Analyse game']],
         ['Help', ["Gui"]],
]

menu_def_pgnviewer = [
        ['&Mode', ['Neutral', "Play", 'PGN-Editor']],
        ['Move', ['Comment', 'Alternative', '---', "Add move"]],
        ['&Game', ['Read', "Select", 'From clipboard', '---', "Replace in db", "Remove from db", "Add to db"
                , "Add to current db", '---', "Switch Sides", '---', "Classify Opening"]],
        ['Database', ['Find in db', 'Classify db', 'Clipboard to current db', '---'
                , "Next Game",
                   "Previous Game", '---', 'New db', 'Remove db']],
        ['Tools', ['Analyse move', 'Analyse game', 'Analyse db', '---', 'Play from here', '---', 'Select games', '---'
                ,]],
         ['Help', ["Gui"]]
]

temp_file_name = 'tempsave.pgn'
MAX_ALTERNATIVES = 7

HELP_MSG_PGN_VIEW = """The GUI has 4 modes, Play and Neutral, Pgn-viewer and Pgn-editor. 
By default you are in Neutral mode, but you can select another startup-mode 
using the startmode in the command-line-options.

This part of the help-menu describes the Pgn-viewer and Pgn-editor mode.

PGN-Viewer-mode.
(A)

"""

APP_NAME = 'Python Swan Chess'
APP_VERSION = 'v0.2'
BOX_TITLE = f'{APP_NAME} {APP_VERSION}'

def display_help(sg):
        sg.PopupScrolled(HELP_MSG_PGN_VIEW, title=BOX_TITLE)
