import chess
import chess.pgn
import chess.svg
import PySimpleGUI as sg
import os

class PGNViewer:
    """header dialog class"""
    def __init__(self, gui, window):
        self.gui = gui
        # window.find_element('comment_k').update(visible=False)
        # window.find_element('pgn_row').update(visible=True)
        window.find_element('_gamestatus_').Update('Mode     PGN-Viewer')
        self.window = window
        self.moves = []
        self.pgn = ""
        self.game_descriptions = []
        self.move_number = 0
        self.current_move = None
        try:
            file_name = self.gui.preferences.preferences["pgn_file"]
            self.open_pgn_file(file_name)
            self.pgn = file_name
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
                    [sg.Combo(self.game_descriptions, key='game_k')],
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
                        my_game = v['game_k']
                        pgn = open(self.pgn)

                        # Reading the game
                        game1 = chess.pgn.read_game(pgn)
                        while not (self.get_description_pgn(game1) == my_game):
                            game1 = chess.pgn.read_game(pgn)
                            if game1 is None:
                                break  # end of file

                        self.init_game(game1)

                        self.display_move()
                        break

            if button == 'Read':
                # use: filename = sg.popup_get_file('message will not be shown', no_window=True)
                #see: https://docs.pysimplegui.com/en/latest/documentation/module/popups/
                layout = [
                    [sg.Text('PGN', font=self.gui.text_font, size=(4, 1)),
                     sg.Input(size=(40, 1), font=self.gui.text_font, key='pgn_k'), sg.FileBrowse('Select PGN File', file_types=(("PGN files", "*.pgn")))],
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

    def open_pgn_file(self, pgn_file):
        pgn = open(pgn_file)
        # Reading the game
        game = chess.pgn.read_game(pgn)
        self.game_descriptions = []
        self.game_descriptions.append(self.get_description_pgn(game))
        while True:
            game1 = chess.pgn.read_game(pgn)
            if game1 is None:
                break  # end of file

            self.game_descriptions.append(self.get_description_pgn(game1))
        print(self.game_descriptions)
        self.init_game(game)
        self.display_move()

    def init_game(self, game):
        self.moves.clear()
        self.current_move = game.game()
        self.moves.append(self.current_move)
        self.window.find_element('_movelist_').Update(
            game.mainline_moves(), append=True, disabled=True)
        self.window.find_element('_Black_').Update(game.headers['Black'])
        self.window.find_element('_White_').Update(game.headers['White'])
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

    def execute_previous_move(self, move_number):
        if move_number > 0:
            move_number = move_number - 1
            self.moves.pop()
            self.current_move = self.moves[-1]
            print("move number:", move_number)
            self.display_move()
        return move_number

    def execute_next_move(self, move_number):
        if len(self.current_move.variations) > 0:
            move_number = move_number + 1
            next_move = self.current_move.variations[0]
            self.moves.append(next_move)
            self.current_move = next_move
            print("move nmber:", move_number)
            self.display_move()
        return move_number

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
        return fen
