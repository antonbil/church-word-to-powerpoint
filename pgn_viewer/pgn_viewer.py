import chess
import chess.pgn
import chess.svg
import PySimpleGUI as sg
import os
from annotator import annotator
from common import menu_def_entry, temp_file_name, menu_def_pgnviewer
from beautify_pgn_lines import PgnDisplay


class PGNViewer:
    """header dialog class"""
    def __init__(self, gui, window):
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
        # window.find_element('comment_k').update(visible=False)
        # window.find_element('pgn_row').update(visible=True)
        window.find_element('_gamestatus_').Update('Mode     PGN-Viewer')
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
        self.execute_pgn()
        """
        end()→ GameNode[source] Follows the main variation to the end and returns the last node
        turn()→ chess.Color[source] Gets the color to move at this node.
        variations: List[ChildNode] A list of child nodes
        """

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
        return "{}-{} {} ({})".format(game.headers['White'],game.headers['Black'],game.headers['Date'],game.headers['Result'])

    def execute_pgn(self):

        self.display_move()
        buttons = [self.gui.toolbar.new_button("Previous"), self.gui.toolbar.new_button("Next"), self.gui.toolbar.new_button("Crop")]
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

            if button == 'Play from here':
                self.play_from_here()
                break

            if button == 'Turn board':
                self.gui.is_user_white = not self.gui.is_user_white
                self.restart = True
                break

            if button == 'PGN-Editor':
                # import later, to avoid recursive import
                from pgn_editor.pgn_editor import PgnEditor
                name_file = temp_file_name
                if not name_file == self.pgn:
                    with open(name_file, mode='w') as f:
                        f.write('{}\n\n'.format(self.game))
                self.gui.menu_elem.Update(menu_def_entry)
                data_entry = PgnEditor(self.gui, self.window, name_file)
                self.is_win_closed = data_entry.is_win_closed
                break
            #list_items = self.game_descriptions
            if button == "Select":
                if self.check_edit_single_pgn():
                    title_window = "Read PGN"
                    selected_item = self.gui.get_item_from_list(self.game_descriptions, title_window)
                    if selected_item:
                        self.my_game = selected_item
                        self.select_game()

            if button == 'Read':
                # use: filename = sg.popup_get_file('message will not be shown', no_window=True)
                #see: https://docs.pysimplegui.com/en/latest/documentation/module/popups/
                self.gui.file_dialog.read_file()
                # filename = sg.popup_get_file('message will not be shown', no_window=True,
                #                              # remember to place the "," in file_types
                #                    font=self.gui.text_font, file_types=(("PGN files", ".pgn"),))
                if self.gui.file_dialog.filename:
                    self.pgn = self.gui.file_dialog.filename
                    self.gui.save_pgn_file_in_preferences(self.pgn)
                    pgn_file = self.pgn
                    self.open_pgn_file(pgn_file)

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

            if button == 'Next Game':
                if self.check_edit_single_pgn():
                    index = self.game_descriptions.index(self.my_game)
                    if index < len(self.game_descriptions) - 1:
                        self.my_game = self.game_descriptions[index + 1]
                        self.select_game()

            if button == 'Analyse move':
                self.analyse_move()

            if button == "Analyse game":
                self.game.headers['White'] = value['_White_']
                self.game.headers['Black'] = value['_Black_']

                self.analyse_game()

            if button == "Analyse db":
                if self.check_edit_single_pgn():
                    self.analyse_db()

            if button == 'Previous Game':
                if self.check_edit_single_pgn():
                    index = self.game_descriptions.index(self.my_game)
                    if index > 0:
                        self.my_game = self.game_descriptions[index - 1]
                        self.select_game()

            if self.gui.toolbar.get_button_id(button) == 'Crop':
                self.variation_bool = not self.variation_bool
                self.display_part_pgn(self.move_number, self.current_move)
            if self.gui.toolbar.get_button_id(button) == 'Next':
                self.move_number = self.execute_next_move(self.move_number)
            if self.gui.toolbar.get_button_id(button) == 'Previous':
                self.move_number = self.execute_previous_move(self.move_number)
            if type(button) is tuple:
                # If fr_sq button is pressed
                move_from = button
                fr_row, fr_col = move_from
                col = chr(fr_col + ord('a'))
                row = str(7 - fr_row + 1)
                coord = col+row

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
        if new_pos > 1:
            self.moves.pop()
        self.current_move = self.moves.pop()
        self.moves.append(self.current_move)
        self.move_number = len(self.moves) - 1
        self.move_number = self.execute_next_move(self.move_number)

    def analyse_db(self):
        number_games = len(self.game_descriptions)
        layout = [
            [sg.Text("Analyse pgn's in file: {}".format(self), font=self.gui.text_font, size=(40, 1))],
            [sg.Multiline("Analyse {} games.".format(number_games), do_not_clear=True, autoscroll=True, size=(70, 8),
                          font=self.gui.text_font, key='result_list', disabled=True)]
        ]

        w = sg.Window("Analyse PGN", layout,
                      icon='Icon/pecg.png')
        w.Read(timeout=10)

        i = 1
        for game_string in self.game_descriptions:
            self.my_game = game_string
            window = w.find_element('result_list')
            window.Update(
                "\n{} ({} of {})".format(game_string, i, number_games), append=True, disabled=True)
            w.Read(timeout=10)
            self.select_game()
            self.analyse_game_func(True)
            i = i + 1
        w.Close()

    def analyse_game(self):
        store_in_db = False
        self.analyse_game_func(store_in_db)

    def analyse_game_func(self, store_in_db):
        pgn_file = temp_file_name
        with open(pgn_file, mode='w') as f:
            f.write('{}\n\n'.format(self.game))
        name_file = self.game.headers['Date'].replace("/", "-").replace(".??", "") + "-" + self.game.headers[
            'White'].replace(" ", "_") \
                    + "-" + self.game.headers['Black'].replace(" ", "_") + ".pgn"
        analysed_game = annotator.start_analise(pgn_file,
                                self.gui.engine, name_file, store_in_db, self.gui)
        return analysed_game

    def callback(self, advice):
        self.window.Read(timeout=5)
        window = self.window.find_element('comment_k')
        window.Update('')
        window.Update(
            advice, append=True, disabled=True)
        self.window.Read(timeout=10)

    def analyse_move(self):
        advice, score, pv = self.gui.get_advice(self.board, self.callback)
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

        window = self.window.find_element('comment_k')
        window.Update('')
        window.Update(
            "{} {}".format(" ".join(res_moves), score), append=True, disabled=True)

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
        game = chess.pgn.read_game(pgn)
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
            #print(self.game_descriptions)
        self.init_game(game)
        self.display_move()

    def init_game(self, game):
        self.go_up = True
        self.game = game
        self.move_squares = [0, 0, 0, 0]
        self.display_pgn(game)
        self.moves.clear()
        self.current_move = game.game()
        self.moves.append(self.current_move)
        self.set_players(game)
        site = game.headers['Site'].replace('?', "")
        if len(site) > 0:
            site = site + " "
        info = "{} ({})".format(
            (site + game.headers['Date'].replace('?', "").replace('..', "")
             .replace('//', "")).strip(),
            game.headers['Result'])
        self.window.find_element('overall_game_info').Update(info) # previously: advise_info_k
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
        self.window.find_element('_currentmove_').Update(move_string + alternatives)
        # get formatted partial moves: rest of moves from current-move on
        part_text = self.pgn_display.beautify_lines(str(next_move))
        if self.variation_bool:
            window = self.window.find_element('_movelist_')
            window.Update(part_text)
            return

        # see if line number can be retrieved by comparing the first part of the partial moves
        line_number, is_available = self.pgn_display.get_line_number(next_move, self.pgn_lines)

        if line_number > -1:
            str1 = "\n".join(self.pgn_lines)+"\n"
            # self.pgn_lines
            part = str(next_move).split(" ")[1]
            self.display_move_list(str1, line_number, part)
            #print("move nmber:", move_number, part)
            # print("variation", move_variation.move)
            move_str = str(next_move.move)
            fr_col = ord(move_str[0]) - ord('a')
            fr_row = 8 - int(move_str[1])
            self.move_squares=[]
            self.move_squares.append(fr_col)
            self.move_squares.append(fr_row)

            fr_col = ord(move_str[2]) - ord('a')
            fr_row = 8 - int(move_str[3])
            self.move_squares.append(fr_col)
            self.move_squares.append(fr_row)
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
