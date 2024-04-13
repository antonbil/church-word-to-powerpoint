import chess
import chess.pgn
import chess.svg
import PySimpleGUI as sg
import os

class PGNViewer:
    """header dialog class"""
    def __init__(self, gui, window):
        self.pgn_lines = []
        self.positions = []
        self.gui = gui
        # window.find_element('comment_k').update(visible=False)
        # window.find_element('pgn_row').update(visible=True)
        window.find_element('_gamestatus_').Update('Mode     PGN-Viewer')
        self.window = window
        self.moves = []
        self.pgn = ""
        self.my_game = ""
        self.game_descriptions = []
        self.move_number = 0
        self.move_squares = [0,0,0,0]
        self.current_move = None
        try:
            game_name = self.gui.preferences.preferences["pgn_game"] if "pgn_game" in self.gui.preferences.preferences \
                else ""
            file_name = self.gui.preferences.preferences["pgn_file"]
            self.open_pgn_file(file_name)
            self.pgn = file_name
            self.my_game = game_name
            self.select_game()

        except:
            pass
        self.execute_pgn()
        """
        end()→ GameNode[source] Follows the main variation to the end and returns the last node
        turn()→ chess.Color[source] Gets the color to move at this node.
        variations: List[ChildNode] A list of child nodes
        """

    def get_description_pgn(self, game):
        return "{}-{} {} ({})".format(game.headers['White'],game.headers['Black'],game.headers['Date'],game.headers['Result'])

    def execute_pgn(self):

        self.display_move()

        while True:
            button, value = self.window.Read(timeout=50)
            if button == 'Neutral':
                is_exit_game = True
                self.gui.entry_game = False
                self.gui.start_entry_mode = False
                break
            if button == "Select":
                layout = [
                    [sg.Combo(self.game_descriptions, key='game_k', default_value=self.my_game, font=self.gui.text_font)],
                    [sg.Ok(font=self.gui.text_font), sg.Cancel(font=self.gui.text_font)]
                ]

                w = sg.Window("Read PGN", layout,
                              icon='Icon/pecg.png')
                while True:
                    e, v = w.Read(timeout=10)
                    if e is None or e == 'Cancel':
                        w.Close()
                        break
                    if e == 'Ok':
                        w.Close()
                        self.my_game = v['game_k']
                        self.select_game()
                        break

            if button == 'Read':
                # use: filename = sg.popup_get_file('message will not be shown', no_window=True)
                #see: https://docs.pysimplegui.com/en/latest/documentation/module/popups/
                layout = [
                    [sg.Text('PGN', font=self.gui.text_font, size=(4, 1)),
                     sg.Input(size=(40, 1), font=self.gui.text_font, key='pgn_k'),
                     sg.FileBrowse('Select PGN File',
                                   font=self.gui.text_font, file_types=(("PGN files", "*.pgn")))],
                    [sg.Ok(font=self.gui.text_font), sg.Cancel(font=self.gui.text_font)]
                ]

                w = sg.Window("Read PGN", layout,
                              icon='Icon/pecg.png')
                while True:
                    e, v = w.Read(timeout=10)
                    if e is None or e == 'Cancel':
                        w.Close()
                        break
                    if e == 'Ok':
                        w.Close()
                        self.pgn = v['pgn_k']
                        print("pgn chosen", self.pgn)
                        self.gui.save_pgn_file_in_preferences(self.pgn)
                        pgn_file = self.pgn
                        self.open_pgn_file(pgn_file)
                        break

            if button == 'Next':
                self.move_number = self.execute_next_move(self.move_number)
            if button == 'Previous':
                self.move_number = self.execute_previous_move(self.move_number)
            if type(button) is tuple:
                # If fr_sq button is pressed
                move_from = button
                fr_row, fr_col = move_from
                col = chr(fr_col + ord('a'))
                row = str(7 - fr_row + 1)
                coord = col+row
                my_variation = False
                counter = 0
                for variation in self.current_move.variations:
                    move = str(variation.move)

                    if move.startswith(coord):
                        self.moves.append(variation)
                        self.current_move = variation
                        self.move_number = self.move_number + 1
                        my_variation = True
                    if my_variation:
                        window = self.window.find_element('comment_k')
                        window.Update('')
                        if counter > 0:
                             window.Update(
                                    self.current_move.mainline_moves(), append=True, disabled=True)

                        # comment_k
                        self.display_move()
                    counter = counter + 1
                if not my_variation:
                    if fr_col < 4:
                        self.move_number = self.execute_previous_move(self.move_number)
                    else:
                        self.move_number = self.execute_next_move(self.move_number)

    def select_game(self):
        pgn = open(self.pgn)
        # Reading the game
        game1 = chess.pgn.read_game(pgn)
        while not (self.get_description_pgn(game1) == self.my_game):
            game1 = chess.pgn.read_game(pgn)
            if game1 is None:
                break  # end of file
        self.init_game(game1)
        self.gui.save_pgn_game_in_preferences(self.my_game)
        self.display_move()

    def open_pgn_file(self, pgn_file):
        pgn = open(pgn_file)
        # Reading the game
        game = chess.pgn.read_game(pgn)
        self.game_descriptions = []
        self.game_descriptions.append(self.get_description_pgn(game))
        self.my_game = self.get_description_pgn(game)
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
        self.move_squares = [0, 0, 0, 0]
        self.display_pgn(game)
        self.moves.clear()
        self.current_move = game.game()
        self.moves.append(self.current_move)
        #moves = game.mainline_moves()
        #self.display_move_list(moves, 0)
        self.set_players(game)
        info = "{} ({})".format(
            (game.headers['Site'].replace('?', "") + game.headers['Date'].replace('?', "")).strip(),
            game.headers['Result'])
        self.window.find_element('advise_info_k').Update(info)
        # 'advise_info_k'
        window = self.window.find_element('_movelist_')
        window.Update('')
        try:
            window.Update(
                self.current_move.mainline_moves(), append=True, disabled=True)
        except:
            pass
        self.move_number = 0

    def set_players(self, game):
        self.window.find_element('_Black_').Update(game.headers['Black'])
        self.window.find_element('_White_').Update(game.headers['White'])

    def display_move_list(self, moves, number = 5, move_str = "Nothing"):
        move_list = moves.split("\n")
        movelist = self.window.find_element('_movelist_')
        if len(move_list) < number+2:
            movelist.Update(
                self.current_move.mainline_moves(), append=True, disabled=True)
            return
        firstpart = "\n".join(move_list[:number])
        last_part = "\n".join(move_list[number+1:])
        bold_part = move_list[number]
        splits = bold_part.split(move_str)
        # if len(splits) == 2:
        #     firstpart = firstpart + splits[0]
        #     last_part = splits[1] + last_part +"\n"
        #     bold_part = move_str
        movelist.Update('')

        movelist.print(
            firstpart,font=self.gui.text_font, autoscroll=False)
        movelist.print(
            bold_part, font=("Helvetica", self.gui.font_size_ui,'bold'), autoscroll=False)
        movelist.print(
            last_part,font=self.gui.text_font, autoscroll=False)

    def execute_previous_move(self, move_number):
        if move_number > 0:
            move_number = move_number - 1
            self.moves.pop()
            self.current_move = self.moves[-1]
            #print("move number:", move_number)
            self.display_part_pgn(move_number, self.current_move)
            self.display_move()
        return move_number
    def get_all_moves(self, game):
        #print("move:")
        current_move = game.game()
        #print("move:", current_move)
        moves=[current_move]
        while len(current_move.variations) > 0:
            current_move = current_move.variations[0]
            moves.append(current_move)
            #print("move:", current_move)
        return moves
    def split_line(self, line):
        max_len_line = 70
        line = line.strip().replace("_ ", "_")
        if len(line) <= max_len_line:
            return line
        line = line.replace(".  ", ".H")
        words = line.split(" ")
        prefix_number = words[0].count("_")
        len_line = len(words[0])
        line=words[0]
        words.pop(0)
        for word in words:
            if len_line + len(word) > max_len_line:
                line = line+"\n"+("_"*prefix_number)
                len_line = len(word)
            else:
                len_line = len_line + 1
                line = line + " "
            len_line = len_line + len(word)
            line = line + word
        line = line.replace( ".H",".  ")
        return line

    def display_pgn(self, game):
        string = str(game.game())
        """
        set_vscroll_position(
    percent_from_top
)
        """
        string = list(string)
        indent = 0
        inside_comment = False

        for index, item in enumerate(string):

                if item == "(" and not inside_comment:
                    indent = indent + 1
                    string[index] = "\n"+("_"*indent)
                if item == "{":
                    indent = indent + 1
                    string[index] = "\n"+("_"*indent)
                    inside_comment = True
                if item == ")" and not inside_comment:
                    indent = indent - 1
                    string[index] = "\n"+("_"*indent)
                if item == "}":
                    indent = indent - 1
                    string[index] = "\n"+("_"*indent)
                    inside_comment = False

        lines = "".join(string).split("\n")
        lines = [self.split_line(l).replace("_", " ") for l in lines if len(l.replace("_","").strip())>0 and not l.startswith("[")]
        lines = "\n".join(lines).split("\n")
        self.pgn_lines = lines
        string = "\n".join(lines)
        print(string)
        moves = self.get_all_moves(game)
        previous = ""
        self.positions = []
        for move in moves:
            move_item = str(move).split(" ")[:2]
            s = " ".join(move_item)
            i = 0
            line_number = -1
            for line in lines:
                if not line.startswith("_"):
                    if s in line:
                        line_number = i
                    else:
                        if "..." in s:
                            s_total = previous + " " + move_item[1]
                            if s_total in line:
                                line_number = i
                i = i + 1
            self.positions.append(line_number)
            print("move", s, line_number)
            previous = s

    def execute_next_move(self, move_number):
        if len(self.current_move.variations) > 0:
            move_number = move_number + 1
            next_move = self.current_move.variations[0]
            self.moves.append(next_move)
            self.current_move = next_move
            self.display_part_pgn(move_number, next_move)
            self.display_move()
        return move_number

    def display_part_pgn(self, move_number, next_move):
        if next_move.is_mainline():
            line_number = self.positions[move_number]
            display_number = 5
            #print("line number:", line_number)
            if line_number - 5 < 0:
                display_number = line_number
                line_number = 5

            str1 = "\n".join(self.pgn_lines[line_number - 5: line_number + 15])
            # self.pgn_lines
            part = str(next_move).split(" ")[1]
            self.display_move_list(str1, display_number, part)
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
        if len(last_variation) > 1:
            for move_variation in last_variation:
                #print("variation", move_variation.move)
                move_str = str(move_variation.move)
                fr_col = ord(move_str[0]) - ord('a')
                fr_row = 8 - int(move_str[1])

                self.gui.change_square_color(self.window, fr_row, fr_col)
        if self.move_squares[1]+ self.move_squares[0] + self.move_squares[2]+ self.move_squares[3] >0:
            #self.gui.change_square_color_red(self.window, self.move_squares[1], self.move_squares[0])
            self.gui.change_square_color_red(self.window, self.move_squares[3], self.move_squares[2])
        return fen
