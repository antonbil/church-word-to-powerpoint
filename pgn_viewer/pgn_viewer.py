import chess
import chess.pgn
import chess.svg
import PySimpleGUI as sg
import os
import shutil
import pyperclip
from io import StringIO
import datetime
from time import perf_counter as pc
from annotator import annotator
from common import menu_def_entry, temp_file_name, menu_def_pgnviewer
from beautify_pgn_lines import PgnDisplay
from analyse_db.analyse_db import AnalyseDb
from Tools.clean_pgn import get_cleaned_string_pgn
import json
from Tools.add_variation import get_and_add_variation, uci_string2_moves

# free pgn's at: https://www.pgnmentor.com/files.html#world
class PGNViewer:
    """pgn viewer class"""
    def __init__(self, gui, window):
        self.mode = "viewer"
        self.move_description = ""
        self.restart = False
        self.is_black = False
        self.is_win_closed = False
        self.variation_bool = False
        self.board = None
        self.go_up = True
        self.current_line = -1
        self.pgn_lines = []
        self.positions = []
        self.gui = gui
        self.previous_move = ""
        self.window = window
        self.moves = []
        self.pgn = ""
        self.game = None
        self.my_game = ""
        self.game_descriptions = []
        self.move_number = 0
        self.move_squares = [0,0,0,0]
        self.current_move = None
        self.pgn_display = PgnDisplay()
        try:
            self.load_start_pgn()

        except:
            pass
        self.set_mode_display()
        self.execute_pgn()
        """
        end()→ GameNode[source] Follows the main variation to the end and returns the last node
        turn()→ chess.Color[source] Gets the color to move at this node.
        variations: List[ChildNode] A list of child nodes
        """

    def set_mode_display(self):
        mode = "PGN-Viewer" if self.mode == "viewer" else "PGN-Move-entry"
        file_name = self.pgn.split("/")[-1].replace(".pgn", "")
        self.window.find_element('_gamestatus_').Update('Mode     {} ({})'.format(mode, file_name))

    def load_start_pgn(self):
        game_name = self.gui.preferences.preferences["pgn_game"] if "pgn_game" in self.gui.preferences.preferences \
            else ""
        file_name = self.gui.preferences.preferences["pgn_file"]
        self.open_pgn_file(file_name)
        self.pgn = file_name
        self.my_game = game_name
        if game_name:
            self.select_game()

    def get_description_pgn(self, game):
        try:
            date = game.headers['Date'].replace("?", "").replace("..", "") if 'Date' in game.headers else ""
            opening = game.headers['Opening'] if 'Opening' in game.headers else ""
            result_ = game.headers['Result'] if 'Result' in game.headers else ""
            white_ = game.headers['White'] if 'White' in game.headers else ""
            black_ = game.headers['Black'] if 'Black' in game.headers else ""
            max_title = 50
            filler_width = 0
            if len(white_)+len(black_) + 1 <= max_title:
                filler_width = max_title - (len(white_)+len(black_) + 1)
            filler = " " * filler_width
            return "{}-{}{} {} ({}){}".format(white_, black_, filler, date, result_, opening)
        except:
            return ""

    def execute_pgn(self):

        self.display_move()
        buttons = [self.gui.toolbar.new_button("<--", auto_size_button=True),
                   self.gui.toolbar.new_button("-->", auto_size_button=True),
                   self.gui.toolbar.new_button("Add", auto_size_button=True),
                   self.gui.toolbar.new_button("Line", auto_size_button=True),
                   self.gui.toolbar.new_button("<--|", auto_size_button=True),
                   self.gui.toolbar.new_button("|-->", auto_size_button=True)]
        self.gui.toolbar.buttonbar_add_buttons(self.window, buttons)

        while True:
            button, value = self.window.Read(timeout=50)
            if button in (sg.WIN_CLOSED, '_EXIT_', 'Close'):
                self.is_win_closed = True
                break
            if button == 'Neutral':
                is_exit_game = True
                self.gui.entry_game = False
                self.gui.start_entry_mode = False
                break
            if button == 'Play':
                self.gui.entry_game = False
                self.gui.start_entry_mode = False
                self.gui.start_mode_used = "play"
                break

            if button == 'Select games':
                self.select_games()

            if button == 'From clipboard':
                self.from_clipboard()

            if button == 'Clipboard to current db':
                self.always_to_clipboard()
                self.classify_opening()
                self.add_to_current_db()

            if button == 'Classify Opening':
                self.classify_opening()
                self.redraw_all()

            if button == 'Classify db':
                self.classify_opening_db()

            if button == 'Play from here':
                self.play_from_here()
                break

            if button == 'Switch Sides':
                self.gui.is_user_white = not self.gui.is_user_white
                self.restart = True
                break

            if button == 'Find in db':
                self.find_in_db()

            if button == 'Add move' or self.gui.toolbar.get_button_id(button) == 'Add':
                self.mode = "entry"
                self.set_mode_display()
                sg.popup("Enter move \nby picking a start/end field on the board",
                         title="Enter move for " + ("White" if self.moves[-1].turn() else "Black"),
                         font=self.gui.text_font)
                continue

            if button == 'PGN-Editor':
                # import later, to avoid recursive import
                from pgn_editor.pgn_editor import PgnEditor
                name_file = temp_file_name
                if not name_file == self.pgn:
                    with open(name_file, mode='w') as f:
                        f.write('{}\n\n'.format(self.game))
                self.gui.menu_elem.Update(menu_def_entry)
                previous_move_number = self.move_number
                data_entry = PgnEditor(self.gui, self.window, name_file,from_pgn_viewer=True, pgn_viewer_move=previous_move_number)
                #return from entry
                self.game = data_entry.game

                string = str(self.game.game())
                self.set_new_position(min(previous_move_number, len(self.get_all_moves(self.game))-1))
                lines = self.pgn_display.beautify_lines(string)
                self.pgn_lines = lines
                self.display_part_pgn(self.move_number, self.current_move)

                #self.is_win_closed = data_entry.is_win_closed
                #break

            if button == "Select":
                if self.check_edit_single_pgn():
                    title_window = "Read PGN from {}".format(self.pgn.split("/")[-1])
                    selected_item = self.gui.get_item_from_list(self.game_descriptions, title_window, width=100)
                    if selected_item:
                        self.my_game = selected_item
                        self.select_game()

            if button == 'Replace in db':
                index, file_name = self.do_action_with_pgn_db("replace")
                if index >= 0:
                    sg.Popup('PGN saved in {}'.format(file_name), title='PGN saved')
                else:
                    sg.Popup('PGN not in database in {}\nPGN is not saved'.format(file_name), title='PGN NOT saved')

            if button == 'Add to db':
                self.gui.file_dialog.read_file()
                if self.gui.file_dialog.filename:
                    filename = self.gui.file_dialog.filename
                    with open(filename, 'a') as f:
                        f.write('\n\n{}'.format(self.game))
                    sg.Popup('PGN added to {}'.format(filename.split("/")[-1]), title='PGN added')

            if button == 'Add to current db':
                self.add_to_current_db()

            if button == 'Remove from db':
                index, file_name = self.do_action_with_pgn_db("remove")

                sg.Popup('PGN removed from {}'.format(file_name), title='PGN removed')
                self.game_descriptions.remove(self.my_game)
                if index < len(self.game_descriptions) - 1:
                    self.my_game = self.game_descriptions[index + 1]
                    self.select_game()
                elif index > 0:
                    self.my_game = self.game_descriptions[index - 1]
                    self.select_game()

            if button == 'Alternative' or self.gui.toolbar.get_button_id(button) == 'Line':
                get_and_add_variation(self.current_move, self.move_number, self.board, self.callback,
                                      self.window.find_element('comment_k'), self.gui)
                self.redraw_all()

            if button == 'Comment':
                #<Cmd+Return> = return in comment
                current_move = self.current_move
                ok = self.gui.file_dialog.get_comment(current_move, self.gui)
                if ok:
                    self.redraw_all()

            if button == 'Read':
                self.gui.file_dialog.read_file()
                if self.gui.file_dialog.filename:
                    temp_pgn = self.pgn
                    self.pgn = self.gui.file_dialog.filename
                    pgn_file = self.pgn
                    if not self.open_pgn_file(pgn_file):
                        sg.popup_error("Error reading game from {}".format(pgn_file), title="Error reading db",
                                       font=self.gui.text_font)
                        self.pgn = temp_pgn
                    else:
                        self.gui.save_pgn_file_in_preferences(self.pgn)

            if button == '_movelist_':
                selection = value[button]
                if selection:
                    item = selection[0]
                    index = self.pgn_lines.index(item)
                    self.current_line = index
                    self.go_up = True
                    new_pos = self.pgn_display.get_position_move_from_pgn_line(item)
                    if new_pos >=1:
                        self.set_new_position(new_pos)

            if button == 'Next Game' or self.gui.toolbar.get_button_id(button) == '|-->':
                if self.check_edit_single_pgn():
                    index = self.game_descriptions.index(self.my_game)
                    if index < len(self.game_descriptions) - 1:
                        self.my_game = self.game_descriptions[index + 1]
                        self.select_game()

            if button == 'Analyse move':
                self.analyse_move()

            if button == 'New db':
                text = sg.popup_get_text('name for new db:', title="Create db",
                                         font=self.gui.text_font)
                if text:
                    if not text.endswith(".pgn"):
                        text += ".pgn"
                    file_name = os.path.join(self.gui.default_png_dir, text)
                    open(file_name, 'a').close()

            if button == 'Remove db':
                self.gui.file_dialog.read_file()
                if self.gui.file_dialog.filename:
                    read_file = self.gui.file_dialog.filename
                    # ask for confirmation
                    file_name = read_file.split('/')[-1]
                    if sg.popup_yes_no('Remove db {}?'.format(file_name) , title="Remove db") == 'Yes':
                        os.remove(read_file)

            if button == "Analyse game":
                self.game.headers['White'] = value['_White_']
                self.game.headers['Black'] = value['_Black_']

                self.analyse_game()
                self.redraw_all()

            if button == "Analyse db":
                if self.check_edit_single_pgn():
                    self.analyse_db()

            if button == 'Previous Game' or self.gui.toolbar.get_button_id(button) == '<--|':
                if self.check_edit_single_pgn():
                    index = self.game_descriptions.index(self.my_game)
                    if index > 0:
                        self.my_game = self.game_descriptions[index - 1]
                        self.select_game()

            # if self.gui.toolbar.get_button_id(button) == 'Add':
            #     self.variation_bool = not self.variation_bool
            #     self.display_part_pgn(self.move_number, self.current_move)
            if self.gui.toolbar.get_button_id(button) == '-->':
                self.move_number = self.execute_next_move(self.move_number)
            if self.gui.toolbar.get_button_id(button) == '<--':
                self.move_number = self.execute_previous_move(self.move_number)
            if type(button) is tuple:
                # If fr_sq button is pressed
                move_from = button
                fr_row, fr_col = move_from
                col = chr(fr_col + ord('a'))
                row = str(7 - fr_row + 1)
                coord = col+row
                if self.mode == "entry":
                    self.mode = "viewer"
                    self.set_mode_display()
                    self.add_move(coord)
                    continue

                # first check if a square representing a variation is pressed
                my_variation = False
                for variation in self.current_move.variations:
                    #print("str(variation.move):",str(variation.move))
                    move = str(variation.move)

                    if move.startswith(coord) or coord == move[2]+move[3]:
                        self.moves.append(variation)
                        self.current_move = variation
                        self.move_number = self.move_number + 1
                        my_variation = True
                    if my_variation:
                        self.display_part_pgn(self.move_number, self.current_move)
                        #print("self.current_move.fen", variation.move.fen())
                        #print("self.current_move", self.current_move)
                        self.display_move()

                if not my_variation:
                    # check for first row; first row acts like a slider for the move-number
                    if not self.gui.is_user_white:
                        fr_row = 7 - fr_row
                        fr_col = 7 - fr_col
                    if fr_row == 0:
                        all_moves = self.get_all_moves(self.game)
                        new_number = max(min(int(fr_col * (len(all_moves) - 1) / 7), len(all_moves)), 2)
                        self.set_new_position(new_number)
                        self.display_part_pgn(new_number, self.current_move)
                        self.display_move()
                    else:
                        # previous / next?
                        if fr_col < 4:
                            self.move_number = self.execute_previous_move(self.move_number)
                        else:
                            self.move_number = self.execute_next_move(self.move_number)

    def add_to_current_db(self):
        if not self.pgn == temp_file_name:
            with open(self.pgn, 'a') as f:
                f.write('\n\n{}'.format(self.game))
            sg.Popup('PGN added to {}'.format(self.pgn.split("/")[-1]), title='PGN added')
        else:
            sg.Popup('PGN cannot be added to temporary file {}'.format(self.pgn.split("/")[-1]),
                     title='PGN NOT added')

    def redraw_all(self):
        string = str(self.game.game())
        lines = self.pgn_display.beautify_lines(string)
        self.pgn_lines = lines
        self.display_part_pgn(self.move_number, self.current_move)
        self.display_move()

    def add_move(self, coord):
        """
        add move to game, based on pressed coordinate (chess-field)
        if destination-chess-field is unique, the destination-piece is chosen
        if origin-chess-field is unique, the origin-piece is chosen
        otherwise a selection of destinations is shown, one of which the user can choose
        :param coord:
        :return:
        """
        chosen_move = None
        list_items_start = [list_item for list_item in list(self.board.legal_moves) if str(list_item).startswith(coord)]
        list_items_end = [list_item for list_item in list(self.board.legal_moves) if str(list_item).endswith(coord)]
        # if destination-chess-field is unique, the destination-piece-move is chosen
        if len(list_items_end) == 1:
            chosen_move = list_items_end[0]
        if not chosen_move:
            # if origin-chess-field is unique, the origin-piece-move is chosen
            if len(list_items_start) == 1:
                chosen_move = list_items_start[0]

        if not chosen_move and len(list_items_start) > 0:
            # otherwise a selection of destinations is shown, one of which the user can choose
            list_items_algebraic = [self.board.san(list_item) for list_item in list_items_start]
            title_window = "Get move"
            selected_item = self.gui.get_item_from_list(list_items_algebraic, title_window)
            if selected_item:
                # move is selected by user
                # now get Move itself
                index = list_items_algebraic.index(selected_item)
                chosen_move = list_items_start[index]
        if chosen_move:
            if str(chosen_move) in [str(m.move) for m in self.current_move.variations]:
                sg.popup("Move {} is already part of variations of node {}!\nMove not inserted.."
                         .format(chosen_move, str(self.current_move.move)))
                return
            self.current_move.add_line(uci_string2_moves(str(chosen_move)))
            self.redraw_all()

    def find_in_db(self):
        """
        locate games in db's (pgn-files) in default_png_dir
        :return:
        """
        keys = ["QWERTYUIOP", "ASDFGHJKL,", "ZXCVBNM"]
        chars = ''.join(keys)
        lines = list(map(list, keys))
        lines[0] += ["\u232B", "Esc"]
        col = [[sg.Push()] + [sg.Button(key) for key in line] + [sg.Push()] for line in lines]

        layout = [[sg.Text('Player', size=(7, 1), font=self.gui.text_font),
         sg.InputText('', font=self.gui.text_font, key='_Player_',
                      size=(50, 1))],
                  [sg.Text('Opening', size=(7, 1), font=self.gui.text_font),
                   sg.InputText('', font=self.gui.text_font, key='_Opening_',
                                size=(50, 1))],
                  [sg.Text('Event', size=(7, 1), font=self.gui.text_font),
                   sg.InputText('', font=self.gui.text_font, key='_Event_',
                                size=(50, 1))],
                  [sg.Text('Date', size=(7, 1), font=self.gui.text_font),
                   sg.InputText('', font=self.gui.text_font, key='_Date_',
                                size=(50, 1))],
                  [sg.Button("Search", font=self.gui.text_font), sg.Button("Cancel", font=self.gui.text_font),sg.Push(), sg.Button("Keyboard")],
    [sg.pin(sg.Column(col, visible=False, expand_x=True, key='Column', metadata=False), expand_x=True)]
        ]
        window = sg.Window("Search db", layout, font=self.gui.text_font, size=(800, 450),
                           finalize=True, modal=True, keep_on_top=True)
        while True:
            event, values = window.read()
            if event in ("Cancel", sg.WIN_CLOSED):
                window.close()
                break
            if event == "Keyboard":
                visible = window["Column"].metadata = not window["Column"].metadata
                window["Column"].update(visible=visible)
            elif event in chars:
                element = window.find_element_with_focus()
                if isinstance(element, sg.Input):
                    if element.widget.select_present():
                        element.widget.delete(sg.tk.SEL_FIRST, sg.tk.SEL_LAST)
                    element.widget.insert(sg.tk.INSERT, event)
            elif event == "\u232B":
                element = window.find_element_with_focus()
                if element.widget.select_present():
                    element.widget.delete(sg.tk.SEL_FIRST, sg.tk.SEL_LAST)
                else:
                    insert = element.widget.index(sg.tk.INSERT)
                    if insert > 0:
                        element.widget.delete(insert - 1, insert)
            if event == "Search":
                # search button invokes action
                window.close()
                db_analyse = AnalyseDb(self.gui.default_png_dir)
                temp_file_name2 = os.path.join(self.gui.default_png_dir, "found_files.pgn")
                db_analyse.name_file = temp_file_name2
                player__ = values['_Player_'].lower()
                opening__ = values['_Opening_'].lower()
                event__ = values['_Event_'].lower()
                date__ = values['_Date_'].lower()
                num_games = db_analyse.search(player=player__, opening=opening__,
                                              event=event__, date=date__)
                if num_games > 0:
                    self.pgn = temp_file_name2
                    self.open_pgn_file(temp_file_name2)
                    selected_item = self.gui.get_item_from_list(self.game_descriptions, "Found games", width=100)
                    if selected_item:
                        self.my_game = selected_item
                        self.select_game()
                else:
                    sg.popup("No games found")
                break

    def classify_opening(self):
        """
        Classify game opening
        :return:
        """
        game, root_node, ply_count = annotator.classify_opening(self.game)

    def classify_opening_db(self):
        """
        Classify opening for all games in database
        :return:
        """
        # get file from user-input
        self.gui.file_dialog.read_file()
        if self.gui.file_dialog.filename:
            read_file = self.gui.file_dialog.filename
            # copy file to backup
            file_name = read_file.split('/')[-1]
            new_file = file_name + ".bak"
            new_file = os.path.join(self.gui.default_png_dir, new_file)
            #os.rename(read_file, new_file)
            try:
                os.remove(new_file)
            except:
                pass
            shutil.copyfile(read_file, new_file)
            # clear the contents of the out-file
            with open(read_file, 'w') as f:
                f.write('\n')
            # read the content of the backup (old file); it contains the data to be changed
            pgn = open(new_file, 'r')
            # read first game
            game = chess.pgn.read_game(pgn)
            # for all games
            while game:
                annotator.classify_opening(game)
                # do action; append to file
                with open(read_file, 'a') as f:
                    f.write('{}\n\n'.format(game))
                # read next game
                game = chess.pgn.read_game(pgn)

            sg.popup("DB with name {} openings are classified".format(file_name))

    def do_action_with_pgn_db(self, action):
        old_file = self.pgn
        file_name = self.pgn.split('/')[-1]
        new_file = file_name + ".bak"
        new_file = os.path.join(self.gui.default_png_dir, new_file)
        #os.rename(old_file, new_file)
        try:
            os.remove(new_file)
        except:
            pass
        shutil.copyfile(old_file, new_file)
        # empty old file
        with open(old_file, 'w') as f:
            f.write('\n')

        pgn = open(new_file)
        game1 = chess.pgn.read_game(pgn)
        if self.my_game not in self.game_descriptions:
            sg.popup("The description: {} is not in current games-list".format(self.my_game))
            return
        index = self.game_descriptions.index(self.my_game)
        games_index = 0
        while game1:
            # if index == games_index:
            #     game1 = self.game
            # with open(old_file, 'a') as f:
            #         f.write('{}\n\n'.format(game1))
            if action == "remove":
                if not index == games_index:
                    with open(old_file, 'a') as f:
                        f.write('{}\n\n'.format(game1))
            elif action=="replace":
                if index == games_index:
                    game1 = self.game
                with open(old_file, 'a') as f:
                    f.write('{}\n\n'.format(game1))

            # action(old_file, index, games_index, game1)
            game1 = chess.pgn.read_game(pgn)
            games_index = games_index + 1
        return index, file_name

    def from_clipboard(self):
        if sg.popup_yes_no('Put pgn in clipboard, and press Yes', title="PGN from clipboard") == 'Yes':
            self.always_to_clipboard()

    def always_to_clipboard(self):
        pgn_data = pyperclip.paste()
        pgn_data = get_cleaned_string_pgn(pgn_data)
        pgn = StringIO(pgn_data)
        if len(self.moves) > 0:
            self.current_move = self.moves[0]
        self.open_pgn_io(pgn, temp_file_name)

    def select_games(self):
        players = []
        pgn = open(self.pgn)
        # Reading the game
        game1 = chess.pgn.read_game(pgn)
        while game1:
            player_white = game1.headers['White']
            # print("player white", player_white)
            player_black = game1.headers['Black']
            if player_white not in players:
                players.append(player_white)
            if player_black not in players:
                players.append(player_black)
            game1 = chess.pgn.read_game(pgn)
        column_players = []
        for index, player in enumerate(players):
            column_players.append([sg.Checkbox(player, key='player'+str(index), enable_events=True)])
        layout = [[[sg.Column([[sg.Checkbox("Skip draws", default = True, key='skip_draws',
                                            enable_events=True)]], size=(170, 300)),
                    sg.Column(column_players, size=(300, 400), vertical_scroll_only=True, scrollable=True)]],
                    [sg.Button('OK', font=self.gui.text_font), sg.Cancel(font=self.gui.text_font),
                     sg.Button('Select all', font=self.gui.text_font),
                     sg.Button('Select none', font=self.gui.text_font)
                     ]
                ]

        form = sg.Window('Select players',layout)
        selected_players = []
        while True:
            event, values = form.read()
            for index, player in enumerate(players):
                if 'player'+str(index) == event:
                    print("player selected:", player)
                    if player in selected_players:
                        selected_players.remove(player)
                    else:
                        selected_players.append(player)
            if event in ("Cancel", sg.WIN_CLOSED):
                break

            if event in ("Select none"):
                for index, player in enumerate(players):
                    form.find_element('player' + str(index)).Update(False)
                selected_players = []

            if event in ("Select all"):
                for index, player in enumerate(players):
                    form.find_element('player' + str(index)).Update(True)
                selected_players = players

            if event in ("OK"):
                skip_draws = values["skip_draws"]
                pgn = open(self.pgn)
                # Reading the game
                game1 = chess.pgn.read_game(pgn)
                temp_file_name2 = os.path.join(self.gui.default_png_dir, temp_file_name)
                with open(temp_file_name2, 'w') as f:
                    f.write('\n')
                nr_copied_games = 0
                while game1:
                    player_white = game1.headers['White']
                    player_black = game1.headers['Black']
                    result = game1.headers['Result']
                    if (player_white in selected_players or player_black in selected_players)\
                            and (not skip_draws or result in ["1-0", "0-1"]):
                        #print("player white", player_white)
                        nr_copied_games = nr_copied_games + 1
                        with open(temp_file_name2, 'a') as f:
                            f.write('{}\n\n'.format(game1))

                    game1 = chess.pgn.read_game(pgn)
                if nr_copied_games > 0:
                    if sg.popup_yes_no('{} Selected games stored in {}\nOpen this file?'
                                           .format(nr_copied_games, temp_file_name2.split("/")[-1]) +
                                   '', "Open created file?") == 'Yes':
                        self.open_pgn_file(temp_file_name2)
                else:
                    sg.popup("No games selected")

                break

        form.close()

    def play_from_here(self):
        board = chess.Board()
        # Go through each move in the game until
        # we reach the required move number
        last_move = None
        for main_move in self.moves:
            move = main_move.move
            try:
                board.push(move)
                last_move = main_move
            except:
                pass

        fen = board.fen()
        self.gui.fen_from_here = fen
        if last_move:
            self.is_black = board.turn == chess.BLACK
            self.gui.is_user_white = not self.is_black
        self.gui.start_mode_used = "play"

    def set_new_position(self, new_pos):
        all_moves = self.get_all_moves(self.game)
        if new_pos >= len(all_moves):
            new_pos = len(all_moves) - 1
        self.moves = all_moves[:new_pos]
        if new_pos > 1 and len(self.moves) > 0:
            self.moves.pop()
        if len(self.moves) > 0:
            self.current_move = self.moves.pop()
            self.moves.append(self.current_move)
        self.move_number = max(len(self.moves) - 1, 0)
        try:
            self.move_number = self.execute_next_move(self.move_number)
        except:
            pass

    def analyse_db(self):
        number_games = len(self.game_descriptions)
        layout = [
            [sg.Text("Analyse pgn's in file: {}".format(self.pgn.split("/")[-1]), font=self.gui.text_font, size=(40, 1))],
            [sg.Multiline("Analyse {} games.".format(number_games), do_not_clear=True, autoscroll=True, size=(70, 8),
                          font=self.gui.text_font, key='result_list', disabled=True)]
        ]

        w = sg.Window("Analyse PGN", layout,
                      icon='Icon/pecg.png')
        start = pc()
        w.Read(timeout=10)

        i = 1
        for game_string in self.game_descriptions:
            self.my_game = game_string
            result_list_element = w.find_element('result_list')
            end = pc() - start
            time_str = ":".join(str(datetime.timedelta(seconds=end)).split(".")[0].split(":")[1:])
            result_list_element.Update(
                "\n({}) {} ({} of {})".format(time_str, game_string, i, number_games), append=True, disabled=True)
            w.Read(timeout=10)
            self.select_game()
            try:
                self.analyse_game_func_silent(True)
            except:
                result_list_element.Update('\nerror in analysing game!!')
            i = i + 1
        w.Close()

    def analyse_game(self):
        store_in_db = False
        self.analyse_game_func()

    def analyse_game_func_silent(self, store_in_db):
        pgn_file = temp_file_name
        with open(pgn_file, mode='w') as f:
            f.write('{}\n\n'.format(self.game))
        name_file = self.game.headers['Date'].replace("/", "-").replace(".??", "") + "-" + self.game.headers[
            'White'].replace(" ", "_") \
                    + "-" + self.game.headers['Black'].replace(" ", "_") + ".pgn"
        analysed_game = annotator.start_analise(pgn_file,
                                self.gui.engine, name_file, store_in_db, self.gui)

    def analyse_game_func(self):
        value_white = self.game.headers['White']
        value_black = self.game.headers['Black']
        analysed_game = self.gui.analyse_game(value_white, value_black, self.game, save_file=False)
        #if sg.popup_yes_no('Merge into current game?', title="Merge into game?") == 'Yes':
        self.merge_into_current_game(analysed_game)
        #
        # else:
        #     pgn = StringIO(analysed_game)
        #     self.open_pgn_io(pgn, temp_file_name)

    def merge_into_current_game(self, analysed_game):
        first_game = self.game
        pgn = StringIO(analysed_game)
        game2 = chess.pgn.read_game(pgn)
        current_move = first_game.game()
        current_move_second = game2.game()
        while len(current_move.variations) > 0:
            if current_move_second.comment:
                current_move.comment = current_move_second.comment + " " + current_move.comment
            variations_first = [l for l in current_move.variations]
            variations_first.pop(0)
            variations_second = [l for l in current_move_second.variations]
            variations_second.pop(0)
            for variation_second in variations_second:
                found_move = False
                move_second = str(variation_second.move)
                for v1 in variations_first:
                    if move_second == str(v1.move):
                        v1.comment = variation_second.comment + " " + v1.comment
                        found_move = True
                        break
                if not found_move:
                    current_move.variations.append(variation_second)
            current_move = current_move.variations[0]
            current_move_second = current_move_second.variations[0]

    def callback(self, advice):
        self.window.Read(timeout=5)
        window = self.window.find_element('comment_k')
        window.Update('')
        window.Update(
            advice, append=True, disabled=True)
        self.window.Read(timeout=10)

    def analyse_move(self):
        advice, score, pv, pv_original, alternatives = self.gui.get_advice(self.board, self.callback)
        is_black = not self.board.turn == chess.WHITE
        move_number = self.move_number // 2
        moves = advice.split(" ")
        res_moves = []
        if is_black:
            res_moves.append("{}... {}".format(move_number, moves.pop(0)))
            is_black = False
        move_number = move_number + 1
        previous = ""
        for move in moves:
            if is_black:
                previous = previous + " " + move
                move_number = move_number + 1
                res_moves.append(previous)
                previous = ""
            else:
                previous = "{}. {}".format(move_number, move)
            is_black = not is_black
        if previous:
            res_moves.append(previous)
        sg.popup("{} ({})".format(" ".join(res_moves), score), title="Advice")
        #print("add:", pv_original)

        # window = self.window.find_element('comment_k')
        # window.Update('')
        # window.Update(
        #     "{} ({})".format(" ".join(res_moves), score), append=True, disabled=True)

    def select_game(self):
        print("open pgn:", self.pgn)
        pgn = open(self.pgn)
        # Reading the game
        game1 = chess.pgn.read_game(pgn)
        start_game = game1
        while not (self.get_description_pgn(game1) == self.my_game):
            game1 = chess.pgn.read_game(pgn)
            if game1 is None:
                break  # end of file
        if not game1:
            self.init_game(start_game)
            return
        self.init_game(game1)
        self.gui.save_pgn_game_in_preferences(self.my_game)
        self.display_move()

    def check_edit_single_pgn(self):
        file_name = self.gui.preferences.preferences["pgn_file"]
        if file_name == temp_file_name:
            if sg.popup_yes_no('Currently not available because you are editing a pgn'+
                               '\nReread pgn?\n(changes on this pgn will be lost!!)') == 'Yes':
                self.gui.preferences.preferences = self.gui.preferences.load_preferences()
                self.load_start_pgn()
                return True
            else:
                # user says: No!
                return False
        else:
            # no editing right now; continue as usual
            return True

    def open_pgn_file(self, pgn_file):
        pgn = open(pgn_file)
        # Reading the game
        return self.open_pgn_io(pgn, pgn_file)

    def open_pgn_io(self, pgn, pgn_file):
        game = chess.pgn.read_game(pgn)
        if not game:
            return False
        self.game = game
        self.game_descriptions = []
        self.game_descriptions.append(self.get_description_pgn(game))
        self.my_game = self.get_description_pgn(game)
        if not (pgn_file == temp_file_name):
            self.gui.save_pgn_game_in_preferences(self.my_game)
            while True:
                game1 = chess.pgn.read_game(pgn)
                if game1 is None:
                    break  # end of file

                self.game_descriptions.append(self.get_description_pgn(game1))
            # print(self.game_descriptions)
        self.init_game(game)
        self.display_move()
        self.set_mode_display()
        return True

    def init_game(self, game):
        self.go_up = True
        self.game = game
        self.move_squares = [0, 0, 0, 0]
        self.display_pgn(game)
        self.moves.clear()
        self.current_move = game.game()
        self.moves.append(self.current_move)
        self.set_players(game)
        site = game.headers['Site'].replace('?', "") if "Site" in game.headers else ""
        event = game.headers['Event'] if "Event" in game.headers else ""
        round = game.headers['Round'] if "Round" in game.headers else ""
        if len(event) > 0:
            site = (site + " " + event).strip()
        if len(round) > 0:
            site = (site + " " + round).strip()
        if len(site) > 0:
            site = site + " "
        info = "{} ({})".format(
            (site + game.headers['Date'].replace('?', "").replace('..', "")
             .replace('//', "")).strip(),
            game.headers['Result'])
        self.window.find_element('overall_game_info').Update(info)
        move_list_gui_element = self.window.find_element('_movelist_')
        move_list_gui_element.Update(self.pgn_lines)
        self.move_number = 0

    def set_players(self, game):
        self.window.find_element('_Black_').Update(game.headers['Black'])
        self.window.find_element('_White_').Update(game.headers['White'])

    def display_move_list(self, moves, number = 5, move_str = "Nothing"):
        move_list = moves.split("\n")
        move_list_gui_element = self.window.find_element('_movelist_')
        if len(move_list) < number+2:
            move_list_gui_element.Update(
                move_list)
            return

        move_list_gui_element.Update(
            move_list, set_to_index=number, scroll_to_index=number - 3 if number > 2 else 0)

    def execute_previous_move(self, move_number):
        if move_number > 0:
            self.go_up = False
            move_number = move_number - 1
            self.moves.pop()
            self.current_move = self.moves[-1]
            self.display_part_pgn(move_number, self.current_move)
            self.display_move()
        return move_number

    def get_all_moves(self, game):
        current_move = game.game()
        moves=[current_move]
        while len(current_move.variations) > 0:
            current_move = current_move.variations[0]
            moves.append(current_move)
        return moves

    def display_pgn(self, game):
        string = str(game.game())
        lines = self.pgn_display.beautify_lines(string)
        self.pgn_lines = lines
        string = "\n".join(lines)
        #print(string)
        moves = self.get_all_moves(game)
        previous = ""
        self.positions = []
        self.move_number = 0
        self.go_up = True
        self.current_line = -1
        self.move_number = 0

    def execute_next_move(self, move_number):
        if len(self.current_move.variations) > 0:
            self.go_up = True
            move_number = move_number + 1
            next_move = self.current_move.variations[0]
            self.moves.append(next_move)
            self.current_move = next_move
            self.display_part_pgn(move_number, next_move)
            self.display_move()
        return move_number

    def display_part_pgn(self, move_number, next_move):
        window = self.window.find_element('comment_k')
        window.Update('')
        window.Update(
            next_move.comment, append=True, disabled=True)

        alternatives, move_string = self.pgn_display.get_nice_move_string(next_move)
        self.move_description = move_string + alternatives
        self.window.find_element('_currentmove_').Update(self.move_description)
        # get formatted partial moves: rest of moves from current-move on
        part_text = self.pgn_display.beautify_lines(str(next_move))
        if self.variation_bool:
            window = self.window.find_element('_movelist_')
            window.Update(part_text)
            return

        # see if line number can be retrieved by comparing the first part of the partial moves
        line_number, is_available = self.pgn_display.get_line_number(next_move, self.pgn_lines)

        if line_number > -1 and len(self.moves) > 0:
            str1 = "\n".join(self.pgn_lines)+"\n"
            # self.pgn_lines
            part = str(next_move).split(" ")[1]
            self.display_move_list(str1, line_number, part)
            #print("move nmber:", move_number, part)
            # print("variation", move_variation.move)
            move_str = str(next_move.move)
            fr_col = ord(move_str[0]) - ord('a')
            no_row = False
            fr_row = 0
            try:
                fr_row = 8 - int(move_str[1])
            except:
                no_row = True
            self.move_squares=[]
            self.move_squares.append(fr_col)
            self.move_squares.append(fr_row)

            fr_col = ord(move_str[2]) - ord('a')
            try:
                fr_row = 8 - int(move_str[3])
            except:
                no_row = True
            self.move_squares.append(fr_col)
            self.move_squares.append(fr_row)
            if no_row:
                self.move_squares = [0,0,0,0]
        self.previous_move = move_string

    def display_move(self):
        board = chess.Board()
        # Go through each move in the game until
        # we reach the required move number
        last_variation = []
        fen = None
        for main_move in self.moves:
            move = main_move.move

            # It copies the move played by each
            # player on the virtual board
            try:
                #print("move", move)
                board.push(move)
                last_variation = main_move.variations
            except:
                pass

        fen = board.fen()
        self.gui.fen = fen
        self.gui.fen_to_psg_board(self.window)
        self.gui.default_board_borders(self.window)
        if len(last_variation) > 1:
            num_var = 0
            for move_variation in last_variation:
                if num_var == 0:
                    color = "#0000ff"
                else:
                    color = "#00ffff"
                #print("variation", move_variation.move)
                move_str = str(move_variation.move)
                fr_col = ord(move_str[0]) - ord('a')
                fr_row = 8 - int(move_str[1])
                to_col = ord(move_str[2]) - ord('a')
                to_row = 8 - int(move_str[3])
                num_var = num_var + 1

                self.gui.change_square_color(self.window, fr_row, fr_col)
                self.gui.change_square_color_border(self.window, fr_row, fr_col, color)
                self.gui.change_square_color_border(self.window, to_row, to_col, color)
        if self.move_squares[1]+ self.move_squares[0] + self.move_squares[2]+ self.move_squares[3] >0:
            self.gui.change_square_color_border(self.window, self.move_squares[1], self.move_squares[0], '#ff0000')
            self.gui.change_square_color_border(self.window, self.move_squares[3], self.move_squares[2], '#ff0000')
            # print("from coords:", self.gui.get_square_color_pos(self.window, self.move_squares[1], self.move_squares[0]))
            # print("to coords:", self.gui.get_square_color_pos(self.window, self.move_squares[3], self.move_squares[2]))
        self.board = board

        return fen
