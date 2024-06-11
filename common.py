ico_path = {
    'win32': {'pecg': 'Icon/pecg.ico', 'enemy': 'Icon/enemy.ico', 'adviser': 'Icon/adviser.ico'},
    'linux': {'pecg': 'Icon/pecg.png', 'enemy': 'Icon/enemy.png', 'adviser': 'Icon/adviser.png'},
    'darwin': {'pecg': 'Icon/pecg.png', 'enemy': 'Icon/enemy.png', 'adviser': 'Icon/adviser.png'}
}

GUI_THEME = [
    'Green', 'GreenTan', 'LightGreen', 'BluePurple', 'Purple', 'BlueMono', 'GreenMono', 'BrownBlue',
    'BrightColors', 'NeutralBlue', 'Kayak', 'SandyBeach', 'TealMono', 'Topanga', 'Dark', 'Black', 'DarkAmber'
]

colors = ['Brown::board_color_k',
      'Blue::board_color_k',
      'Green::board_color_k',
      'Gray::board_color_k']
settings_menu = ['Color', colors,
                     'Theme', GUI_THEME,
                 'Engine', ['Adviser engine','Manage', ['Install::Install', 'Edit::Edit', 'Delete::Delete']],
                 "Other Settings::Other Settings"]

menu_def_entry1 = [
        ['&Game', ['Save::Save', 'New::New', '---', 'Set Headers::Set Headers', 'Strip::Strip',
                   'Analyse game::Analyse game', '---', "Switch Sides::Switch Sides"]],
        ['&Move', ["Back::Back", '---', "Restore alternative::Restore alternative"]],
        ['&Mode', ["Play::Play", "PGN-Viewer::PGN-Viewer", 'Variations Edit::Variations Edit']],
        ['Settings', settings_menu],
         ['Help', ["Gui::Gui"]],
]
menu_def_annotate1 = [
        ['&Game', ['Save::Save', 'New::New', '---', 'Analyse game::Analyse game', '---', "Switch Sides::Switch Sides"]],
        ['&Move', ['Previous::Previous', "Next::Next", '---', "Promote alternative::Promote alternative",
                   "Restore alternative::Restore alternative", "Remove alternative::Remove alternative"
                   , '---', 'Remove from this move onward::Remove from this move onward']],
        ['&Annotate', ['Comment::Comment', '---', 'Alternative::Alternative',
                       "Alternative manual::Alternative manual", '---', 'Manual variation::Manual variation']],
        ['&Mode', ["Play::Play", "PGN-Viewer::PGN-Viewer", 'PGN Move entry::PGN Move entry']],
       ['Settings', settings_menu],
         ['Help', ["Gui::Gui"]],
]

menu_def_pgnviewer1 = [
        ['&Game', ['Read::Read', "Select::Select", 'From clipboard::From clipboard', 'Headers::Headers', 'Save::Save', '---',
                   "Replace in db::Replace in db", "Remove from db::Remove from db",
                   "Add to db::Add to db", "Add to current db::Add to current db", '---',
                   "Switch Sides::Switch Sides", '---', "Classify Opening::Classify Opening"]],
        ['Move', ['Comment::Comment', 'Alternative::Alternative', '---', "Add move::Add move"]],
        ['Database', ['Find in db::Find in db', 'Classify db::Classify db', 'Clipboard to current db::Clipboard to current db', '---'
                , "Next Game::Next Game",
                   "Previous Game::Previous Game", '---', 'New db::New db', 'Remove db::Remove db']],
        ['Tools', ['Analyse move::Analyse move', 'Analyse game::Analyse game', 'Analyse db::Analyse db', '---',
                   'Play from here::Play from here', '---', 'Select games::Select games', '---'
                ,]],
        ['&Mode', ["Play::Play", 'PGN-Editor::PGN-Editor']],
        ['Settings', settings_menu],
         ['Help', ["Gui::Gui"]]
]

translations = {"en":{
                    'White': "White",
                    'Black': "Black",
          "PGN-Editor Entry":"PGN-Editor Entry",
"Move":"Move",
"Info":"Info",
"Back":"Back",
          "_flip_":"Draai",
          "_add_":"Add",
          "_line_":"Line",
"_autoplay_":"Autoplay",
    'PGN-Variations Edit': 'PGN-Variations Edit',
    'Manual Move Entry': 'Manual Move Entry',
    'Manual Variation Entry': 'Manual Variation Entry',
          '_previous_':'Previous',
          '_next_':'Next',
          '_add_move_':'Add move',
          '_best_':'Best?',
    '_move-present-not-inserted_': "Move {} is already part of variations of node {}!\nMove not inserted..",
          "_db-classified_":"DB with name {} openings are classified",
          "_description-not-in-db_": "The description: {} is not in current database",
          '__put-pgn-clipboard':'Put pgn in clipboard, and press Yes',
          "_stored-in-open_":'{} Selected games stored in {}\nOpen this file?',
          "_analyse-in-file_":"Analyse pgn's in file",
          "_analyse-nr-games_":"Analyse {} games.",
          "_error-analysing-game_":'error in analysing game!!',
          "_not-available-reread_":'Currently not available because you are editing a pgn\nReread pgn?\n(changes on this pgn will be lost!!)',
"_clear-current-match_":"Clear current match",
"_clear-match-sure_":"You will clear the moves for the current match\nAre you sure?",
"Remove alternative":"Remove alternative",
"_ok-remove-alternative_":"OK to remove alternative:'{}'?",
"_no-legal-move_":"No legal move:{}",
"_error-enter-move_":"Error enter move",
"_enter remainder-variation_":"You can now enter the remainder of the moves of the variation\n"+
                                     "Execute \"Restore alternative\" at the end of the variation-line",
"_input-moves-variation_":"Input moves variation",
"_no-legal-move2_":"No legal move",
"_enter-move_":"Enter move \nby moving pieces on the board",
"_enter-move-for_":"Enter move for",
"_cannot-save-mainline_":"You cannot save mainline \nif you are behind the previous mainline to be restored",
"_error-promote-variation_":"Error promote variation",
"_variation-to-be-added_":'variation to be added',
"_add-variation_":"Add variation",
"_on-first-move_":"Already at the first move",
"_error-previous-move_":"Error previous move",
"_on-last-move_":"Already at the last move",
"_error-next-move_":"Error next move",
"_no-analysis-last-move_":"No analysis for last move",
"_error-analysis_":"Error analysis",
"_select-new-mainline_":"select new main line",
"_get-move_":"Get move",
"_variation-exists_":"Variation exists",
"_replace-variation_":"Replace this variation?",
"_variation-exists-message_":"A variation starting with {} already exists",
"_wait-moment_":'Wait a minute...',
"_pgn-annotated_":"PGN is annotated",
"_and-saved_":"and saved",
"_analyse-pgn_":"Analyse PGN"
},
    "nl":{'Headers': 'Headers',
                   'Select': 'Selecteer',
                   'Game':'Partij',
                   'Read':'Open',
                   'From clipboard': 'Uit klembord',
                   'Save': 'Bewaar',
                   'Move':'Zet',
                   'Color':'Kleur',
                   'Theme':'Thema',
                   'Engine':'schaak-AI ',
                   'Other Settings':'Andere Instellingen',
                   'Adviser engine':'AI Adviseur',
                   'Manage':'Beheer',
                   'Install':'Installeren',
                   'Edit':'Aanpassen',
                   'Delete':'Verwijder',

                   'Add move':'Toevoegen',
                   'Comment':'Commentaar',
                   'Replace in db':'Vervang in db',
                    "Remove from db":"Verwijder uit db",
                    "Add to db":"Toevoegen aan db",
                    "Add to current db":"Toevoegen aan huidige db",
                    "Switch Sides":"Verander van kleur",
                    "Classify Opening":"Classificeer Opening",
                    "Alternative":"Alternatief",
                    "Find in db":"Zoek in db",
                    "Classify db":"Classificeer db",
                    "Clipboard to current db":"Klembord naar huidige db",
                    "Next Game":"Volgende partij",
                    "Previous Game":"Vorige partij",
                    "New db":"Nieuwe db",
                    "Remove db":"Verwijder db",
                    "Analyse move":"Analyseer zet",
                    "Analyse game":"Analyseer game",
                    "Analyse db":"Analyseer db",
                    "Play from here":"Speel vanaf hier",
                    "Select games":"Selecteer partij",
                    "Play":"Speel",
                    "PGN-Editor":"PGN-Aanpassen",
                    "Help":"Hulp",
                    "Settings":"Instellingen",
                    "Mode":"Modus",
                    "Tools":"Tooling",
                    "Database":"Database",
                    'White': "Wit",
                    'Black': "Zwart",
          "PGN-Editor Entry":"PGN-Editor Invoer",
"Info":"Informatie",
"Back":"Terug",
          "_flip_":"Draai",
          "_add_":"+",
          "_line_":"Variant",
"_autoplay_":"Autoplay",
'PGN-Variations Edit': 'PGN-Varianten Invoer',
'Manual Move Entry':'Handmatige Zet Invoer',
'Manual Variation Entry':'Handmatige Variant Invoer',
          '_previous_':'Vorige',
          '_next_':'Volgende',
          '_add_move_':'Zet erbij',
          '_best_':'Beste?',
                    'Strip': "Strippen",
                    'New': "Nieuw",
                    'Set Headers': "Headers Aanpseen",
                    'Restore alternative': "Variant herstellen",
                    'PGN-Viewer': "PGN-Viewer",
                    'Variations Edit': "Varianten Aanpassen",
                    'Previous': "Vorige",
                    'Next': "Volgende",
                    'Promote alternative': "Variant promoveren",
                    'Remove alternative': "Verwijder variant",
                    'Remove from this move onward': "Verwijder na deze zet",
                    'Annotate': "Annoteren",
                    'Alternative manual': "Variant handmatig",
                    'Manual variation': "Handmatige variant",
                    'PGN Move entry': "PGN zet invoer",
                    'PGN saved':'PGN bewaard',
'PGN saved in':'PGN bewaard in',
'PGN is not saved':'PGN is niet bewaard',
'PGN not in database in':'PGN niet in database in',
'PGN added to':'PGN toegevoegd aan',
'PGN added':'PGN toegevoegd',
'PGN removed from':'PGN verwijderd uit',
'PGN removed':'PGN verwijderd',
"Error reading game from":"Fout bij lezen partij uit",
"Error reading db":"Fout bij lezen db",
'name for new db':'naam voor nieuwe db',
"Create db":"Creeer db",
'PGN cannot be added to temporary file':'PGN kan niet toegevoegd aan tijdelijk bestand',
'PGN NOT added':'PGN NIET toegevoegd',
          '_move-present-not-inserted_': "Zet {} is al onderdeel van variatie {}!\nZet niet toegevoegd..",
"Illegal move": "Geen geldige zet",
"Get move": "Zet invoeren",
'Player':'Speler',
'Opening':'Opening',
'Event':'Event',
'Date':'Datum',
"Search":'Zoeken',
"Cancel":'Terug',
"Search db": "Zoek in db",
"No games found": "Geen partijen gevonden",
          "_db-classified_":"openingen in DB met naam {} zijn herkend",
          "_description-not-in-db_": "De beschrijving: {} staat niet in de huidige database",
          '__put-pgn-clipboard':'Zet pgn in klembord, en kies "Ja"',
"PGN from clipboard":"PGN uit klembord",
"Skip draws":"Negeer remises",
'Select all':'Selecteer alles',
'Select none':'Selecteer niets',
'Select players':'Selecteer spelers',
          "_stored-in-open_":'{} geselecteerde partijen bewaard in {}\nDit bestand openen?',
"Open created file":"Open het gemaakte bestand",
"No games selected":"geen partijen geselecteerd",
          "_analyse-in-file_":"Analiseer pgn's in bestand",
          "_analyse-nr-games_":"Analiseer {} partijen.",
"Analyse PGN":"Analiseer PGN",
          "_error-analysing-game_":'fout bij analiseren partij!!',
"Advice":"Advies",
          "_not-available-reread_":'Niet mogelijk omdat er een pgn wordt bewerkt\nHeropenen pgn?\n(veranderingen in de huidige pgn gaan verloren!!)',
"_clear-current-match_":"Maak huidige partij leeg",
"_clear-match-sure_":"Dit zal de inhoud van de huidige partij weglaten\nWeet je het zeker?",
"_ok-remove-alternative_":"OK om variant te verwijderen:'{}'?",
"_no-legal-move_":"Geen geldige zet:{}",
"_error-enter-move_":"Fout bij invoeren zet",
"_enter remainder-variation_":"Je kunt nu de rest van de zetten van de variant invoeren\n"+
                                     "Voer uit: \"Herstel variant\" aan het eind van de variant",
"_input-moves-variation_":"Invoer zetten variant",
"_no-legal-move2_":"Geen geldige zet",
"_enter-move_":"Voer in zet \ndoor de zet op het bord uit te voeren",
"_enter-move-for_":"Voer zet int",
"_cannot-save-mainline_":"Je kunt de variant niet wijzigen \nals je achter de hoofd-variant zit die nog hersteld moet worden",
"_error-promote-variation_":"Fout om de variant tot de hoofd-variant te maken",
"_variation-to-be-added_":'variant om toe te voegen',
"_add-variation_":"Toevoegen variant",
"_on-first-move_":"Je bent al bij de eerste zet",
"_error-previous-move_":"Fout vorige zet",
"_on-last-move_":"Je bent al bij de laatste zet",
"_error-next-move_":"Fout volgende zet",
"_no-analysis-last-move_":"Geen analyse voor laatste zet",
"_error-analysis_":"Fout bij analyse",
"_select-new-mainline_":"Selecteer nieuwe hoofd-variant",
"_get-move_":"In te voeren zet",
"_variation-exists_":"Variant bestaat al",
"_replace-variation_":"Vervang deze variant?",
"_variation-exists-message_":"Een variant die begint met {} bestaat al",
"Close":"Sluit",
'Add to library':'Toevoegen aan bibliotheek',
"Result":"Resultaat",
"Round":"Ronde",
'Calendar':'Kalender',
"Site":"Site",
"Game data":"Partij-gegevens",
"_wait-moment_":'Wacht een minuutje...',
"_pgn-annotated_":"PGN is geannoteerd",
"_and-saved_":"en bewaard",
"_analyse-pgn_":"Analyseer PGN"
                   }
                }
language = "nl"

def set_language(new_language):
    global language
    language = new_language

def replace(data):
    if isinstance(data, list):
        for k, v in enumerate(data):
            if type(v) is str and '::' in v:
                key = v.split('::')[1]
                if key in translations[language]:
                    data[k] = "{}::{}".format(translations[language][key], key)
            else:
                id = v[0]
                if type(id) is str and '::' not in id:
                    for t in translations[language]:
                        if t in id:
                            data[k] = [id.replace(t, translations[language][t])]
                            for v1 in v[1:]:
                                if type(v1) is str and '::' not in v1:
                                    if v1 in translations[language]:
                                        v1 = translations[language][v1]
                                data[k].append(v1)
            replace(v)

def menu_def_entry():
    menu_res = menu_def_entry1.copy()
    replace(menu_res)
    return menu_res

def menu_def_annotate():
    menu_res = menu_def_annotate1.copy()
    replace(menu_res)
    return menu_res

def menu_def_pgnviewer():
    menu_res = menu_def_pgnviewer1.copy()
    replace(menu_res)
    return menu_res

temp_file_name = 'tempsave.pgn'
MAX_ALTERNATIVES = 7

HELP_MSG_PGN_VIEW = """The GUI has 3 modes, Play, Pgn-viewer and Pgn-editor. 
By default you are in Play mode, but you can select another startup-mode 
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

def get_button_id(button):
    if button in colors:
        return button
    if type(button) is str:
        parts = button.split('::')
        if len(parts) > 1:
            return parts[1]
        return button
    return button

def get_translation(key):
    if key in translations[language]:
        return translations[language][key]
    return key

