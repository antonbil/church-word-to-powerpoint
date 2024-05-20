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

PGN-Editor-mode.
In this mode you can manually add and edit moves.
This mode has two sub-modes:
- PGN Move entry mode
- Variations-edit mode
(A)PGN Move entry mode
In this mode you can enter moves in a sequential way.
You can add moves using the board, or remove the last move.
(B) In this mode you can restore the last alternative that you started in Variations-edit mode. 
(B) Variations-edit mode
In the mode you can add and modify alternative lines for a particular move.
(B1) got to particular move using Previous and Next
-use the top-line of the board to go to a relative position
- or select the move in the moves-list by clicking it
(B2) Add an alternative using Alternative and Alternative Manual
- Alternative: add alternative that the engine suggests
- Alternative Manual: add move manually, and ask the engine to add the rest of the alternative line
(B3) Modify alternatives inside moves
- promote an alternative/variation so it will temporarily act as main line
If a variation as selected in the way, moves can be added using the PGN Move Entry sub-mode
Do not forget to Restore the original order of the variations ("Restore alternative" option in both sub-modes)
- remove an alternative variation
(B4) Add a Manual variation
- add the spefific move on the board.
- the sub-mode is automatically changed to PGN Move entry mode so you can add the rest of the variation-moves manually

"""

APP_NAME = 'Python Swan Chess'
APP_VERSION = 'v0.2'
BOX_TITLE = f'{APP_NAME} {APP_VERSION}'

def display_help(sg):
        sg.PopupScrolled(HELP_MSG_PGN_VIEW, title=BOX_TITLE)
