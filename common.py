ico_path = {
    'win32': {'pecg': 'Icon/pecg.ico', 'enemy': 'Icon/enemy.ico', 'adviser': 'Icon/adviser.ico'},
    'linux': {'pecg': 'Icon/pecg.png', 'enemy': 'Icon/enemy.png', 'adviser': 'Icon/adviser.png'},
    'darwin': {'pecg': 'Icon/pecg.png', 'enemy': 'Icon/enemy.png', 'adviser': 'Icon/adviser.png'}
}

GUI_THEME = [
    'Green', 'GreenTan', 'LightGreen', 'BluePurple', 'Purple', 'BlueMono', 'GreenMono', 'BrownBlue',
    'BrightColors', 'NeutralBlue', 'Kayak', 'SandyBeach', 'TealMono', 'Topanga', 'Dark', 'Black', 'DarkAmber'
]

settings_menu = ['Color', ['Brown::board_color_k',
                               'Blue::board_color_k',
                               'Green::board_color_k',
                               'Gray::board_color_k'],
                     'Theme', GUI_THEME,
                 'Engine',['Adviser engine','Manage', ['Install', 'Edit', 'Delete']],
                 "Other Settings"]

menu_def_entry = [
        ['&Game', ['Save', 'New', '---', 'Set Headers', 'Strip', 'Analyse game', '---', "Switch Sides"]],
        ['&Move', ["Back", '---', "Restore alternative"]],
        ['&Mode', ["Play", "PGN-Viewer", 'Variations Edit']],
        ['Settings', settings_menu],
         ['Help', ["Gui"]],
]
menu_def_annotate = [
        ['&Game', ['Save', 'New', '---', 'Analyse game', '---', "Switch Sides"]],
        ['&Move', ['Previous', "Next", '---', "Promote alternative", "Restore alternative", "Remove alternative"
                   , '---', 'Remove from this move onward']],
        ['&Annotate', ['Comment', '---', 'Alternative', "Alternative manual", '---', 'Manual variation']],
        ['&Mode', ["Play", "PGN-Viewer", 'PGN Move entry']],
       ['Settings', settings_menu],
         ['Help', ["Gui"]],
]

menu_def_pgnviewer = [
        ['&Game', ['Read', "Select", 'From clipboard', 'Save', '---', "Replace in db", "Remove from db", "Add to db"
                , "Add to current db", '---', "Switch Sides", '---', "Classify Opening"]],
        ['Move', ['Comment', 'Alternative', '---', "Add move"]],
        ['Database', ['Find in db', 'Classify db', 'Clipboard to current db', '---'
                , "Next Game",
                   "Previous Game", '---', 'New db', 'Remove db']],
        ['Tools', ['Analyse move', 'Analyse game', 'Analyse db', '---', 'Play from here', '---', 'Select games', '---'
                ,]],
        ['&Mode', ["Play", 'PGN-Editor']],
        ['Settings', settings_menu],
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
- add the specific move on the board.
- the sub-mode is automatically changed to PGN Move entry mode so you can add the rest of the variation-moves manually

(C) Pgn-viewer mode
This allows for replaying any pgn-game.
(C1) Read game
this option reads a game from a PGN.
If this pgn contains more than one game, the first is selected and presented as the current game
The program starts automatically with the last game displayed. 
based on the pgn Read and Select-ed in the previous session
In this manual the PGN with the games and the term Database (DB) are used as synonym
(C2) Select game
Select a game in the pgn currently read and displayed.
If this pgn contains only one game, this game can be re-selected
(C3) Replace in DB
Replaces the current displayed game in the database (currently opened PGN)
If this game is modified the changes are saved inside the currently opened PGN 
(C4) Add to DB (alternative: Add to current DB)
Adds the current PGN to a PGN-file (DB) on file.
You have to provide the pgn-file on disk first (unless you select: Add to current DB)
"Add to current DB" is a shortcut to add the current displayed game to the currently opened DB.

Several tools are available to add information to the currently displayed game:
(C5a)Classify opening
finds the opening closest to the opening moves, and stores the information in the headers (tags: ECO and Opening)
and also in the comments of the game itself (as comment of the last move that is found to be in the opening)
(C5b)Simple analysis of moves is provided in this mode so you will not have to change the mode to "Pgn-editor"
- Analyse move
Uses the engine to (re-)analyse the move selected.
You are given the opportunity to replace the current move-analysis with the newly found analysis
("Analyse game" and "Analyse DB" are convenience-shortcuts to anlyse the entire game or DB so you can do batch-processing)
- Comment
changes the current comment of a move; if the comment is empty it is created.
- Alternative
an alternative is searched for a particular move.
you can add the provided analysis yes/no 
(example: if the move provided is already in the analysis you will likely say: no)
- Add move
You can add manually an alternative for a move.
This is an easy way to create an entirely new variation:
first add the move manually, then select this alternative and afterwards: "Analyse move"
(C6) Selecting moves inside PGN-Viewer
- the button-bar at the bottom provides two buttons at the right: Previous and next
- clicking on the left- or right side of the board has the same effects
- the top row of the board displayed provides a crude and fast way to navigate inside the game
- clicking on the move-list will select the move or variation that was clicked on
- the board itself will indicate with yellow squares if alternatives are available
Clicking on such a yellow square will start the variation
- alternatives are also display as buttons after the move-description itself
"""

APP_NAME = 'Python Swan Chess'
APP_VERSION = 'v0.2'
BOX_TITLE = f'{APP_NAME} {APP_VERSION}'
GAME_DIVIDER = "--++xxx--"

def display_help(sg):
        sg.PopupScrolled(HELP_MSG_PGN_VIEW, title=BOX_TITLE)
