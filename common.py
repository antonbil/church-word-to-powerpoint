menu_def_entry = [
        ['&Mode', ['Neutral', "Play", "PGN-Viewer", 'Variations Edit']],
        ['&Move', ["Back", '---', "Restore alternative"]],
        ['&Game', ['Save', 'Clear', 'Analyse game']],
]
menu_def_annotate = [
        ['&Mode', ['Neutral', "Play", "PGN-Viewer", 'PGN Move entry']],
        ['&Move', ['Previous', "Next", '---', "Promote alternative", "Restore alternative", "Remove alternative"
                   , '---', 'Remove from this move onward']],
        ['&Annotate', ['Comment', '---', 'Alternative', "Alternative manual", '---', 'Manual variation']],
        ['&Game', ['Save', 'Clear', 'Analyse game']],
]

menu_def_pgnviewer = [
        ['&Mode', ['Neutral', "Play", 'PGN-Editor']],
        ['Move', ['Comment', 'Alternative', '---', "Add move"]],
        ['&Game', ['Read', "Select", 'From clipboard', 'Clipboard to current db', '---', "Replace in db", "Remove from db", "Add to db"
                , "Add to current db", '---'
                , "Next Game",
                   "Previous Game", '---', "Switch Sides", '---', "Classify Opening"]],
        ['Tools', ['Analyse move', 'Analyse game', 'Analyse db', '---', 'Play from here', '---', 'Select games', '---'
                ,'Find in db', 'Classify db']]
]

temp_file_name = 'tempsave.pgn'