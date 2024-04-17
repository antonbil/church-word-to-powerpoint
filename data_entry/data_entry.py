import chess
import chess.pgn
import chess.svg
import PySimpleGUI as sg
import os
from io import StringIO
from annotator import annotator
import copy
import collections


class DataEntry:
    """header dialog class"""

    def __init__(self, gui, window):
        self.board = chess.Board()
        self.pgn_lines = []
        self.positions = []
        self.gui = gui
        self.move_number = 0

        self.mode = "entry"
        window.find_element('_gamestatus_').Update('Mode     PGN-Entry')
        self.window = window
        self.moves = []
        self.all_moves = []
        self.game = chess.pgn.Game()
        self.game.setup(self.board)
        self.current_move = self.game.game()
        self.move_squares = [0, 0, 0, 0]

        self.execute_data_entry()

    def board_to_game(self):
        self.game = chess.pgn.Game()
        self.board.pop()
        self.moves.clear()

        # Undo all moves.
        switchyard = collections.deque()
        while self.board.move_stack:
            switchyard.append(self.board.pop())

        self.game.setup(self.board)
        node = self.game

        # Replay all moves.
        while switchyard:
            move = switchyard.pop()
            node = node.add_variation(move)
            self.moves.append(node)
            self.board.push(move)
        self.current_move = node
        self.all_moves = [m for m in self.moves]

    def execute_data_entry(self):

        self.display_move()
        move_state = 0
        fr_row = 0
        fr_col = 0
        self.mode = "entry"

        while True:
            button, value = self.window.Read(timeout=50)
            if button == 'Neutral':
                self.gui.entry_game = False
                self.gui.start_entry_mode = False
                break
            if button == 'Switch mode':
                window_element = self.window.find_element('_gamestatus_')
                if self.mode == "entry":
                    self.mode = "annotate"
                    self.move_number = len(self.all_moves) - 1
                    window_element.Update('Mode     PGN-Annotate')
                else:
                    self.mode = "entry"
                    window_element.Update('Mode     PGN-Entry')
                self.moves = [m for m in self.all_moves]
                self.display_move()
            if button == 'Next' and self.mode == "annotate":
                self.execute_next_move(self.move_number)

            if button == 'Previous' and self.mode == "annotate":
                self.execute_previous_move(self.move_number)

            if button == 'Comment' and self.mode == "annotate":
                text = sg.popup_get_text('Enter comment', title="Input comment")
                self.moves[-1].comment = text
                self.update_pgn_display()

            if button == 'Alternative' and self.mode == "annotate":
                self.analyse_move()
                self.update_pgn_display()

            if button == "Back" and self.mode == "entry":
                self.board_to_game()
                window = self.window.find_element('_movelist_')
                exporter = chess.pgn.StringExporter(headers=False, variations=False, comments=False)
                pgn_string = self.game.accept(exporter)
                # window.Update('')
                try:
                    window.Update(self.split_line(pgn_string))
                except (Exception, ):
                    return

                self.display_move()
            if button == 'Analyse game':
                value_white = value['_White_']
                value_black = value['_Black_']
                self.gui.analyse_game(value_white, value_black, self.game)

            if button == 'Save':
                value_white = value['_White_']
                value_black = value['_Black_']
                self.gui.save_game_pgn(value_white, value_black, self.game)

            if type(button) is tuple and self.mode == "annotate":
                move_from = button
                fr_row, fr_col = move_from

                if fr_col < 4:
                    self.execute_previous_move(self.move_number)
                else:
                    self.execute_next_move(self.move_number)

                pass
            if type(button) is tuple and self.mode == "entry":
                if move_state == 0:
                    # If fr_sq button is pressed
                    move_from = button
                    fr_row, fr_col = move_from

                    # Change the color of the "fr" board square
                    self.gui.change_square_color(self.window, fr_row, fr_col)

                    move_state = 1
                elif move_state == 1:
                    move_from = button
                    to_row, to_col = move_from

                    self.gui.default_board_borders(self.window)

                    self.execute_move(fr_col, fr_row, to_col, to_row)
                    move_state = 0

    def uci_string2_moves(self, str_moves):
        return [chess.Move.from_uci(move) for move in str_moves.split()]

    def execute_previous_move(self, move_number):
        if move_number > 0:
            self.move_number = move_number - 1
            self.moves.pop()
            self.define_moves_squares()
            self.display_move()

    def execute_next_move(self, move_number):
        if move_number < len(self.all_moves) - 1:
            self.move_number = move_number + 1
            self.moves.append(self.all_moves[self.move_number])
            self.define_moves_squares()
            self.display_move()

    def callback(self, advice):
        self.window.Read(timeout=5)
        window = self.window.find_element('comment_k')
        window.Update('')
        window.Update(
            advice, append=True, disabled=True)
        self.window.Read(timeout=10)

    def analyse_move(self):
        # str_line3 = "a7a6 g1f3 g8f6"
        # move2_main.add_line(UCIString2Moves(str_line3))
        advice, score, pv, pv_original, alternatives = self.gui.get_advice(self.board, self.callback)
        is_black = not self.board.turn == chess.WHITE
        move_number = self.move_number // 2
        print("pv original:", pv_original)
        a_list = list(alternatives)
        max_alt = 3
        if len(a_list) < 3:
            max_alt = len(a_list)
        print("alternatives", sorted(a_list, key=lambda item: -item[0], reverse=True)[0:max_alt])
        str_line3 = " ".join([str(m) for m in pv_original])
        print("add line variation", str_line3)
        self.moves[-1].add_line(self.uci_string2_moves(str_line3))
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


    def execute_move(self, fr_col, fr_row, to_col, to_row):
        fr_sq = chess.square(fr_col, 7 - fr_row)
        to_sq = chess.square(to_col, 7 - to_row)
        moved_piece = self.board.piece_type_at(chess.square(fr_col, 7 - fr_row))  # Pawn=1

        # Change the color of the "fr" board square
        self.gui.change_square_color(self.window, to_row, to_col)
        # If user move is a promote
        user_move = None
        if self.gui.relative_row(to_sq, self.board.turn) == 7 and \
                moved_piece == chess.PAWN:
            # is_promote = True
            pyc_promo, psg_promo = self.gui.get_promo_piece(
                user_move, self.board.turn, True)
            user_move = chess.Move(fr_sq, to_sq, promotion=pyc_promo)
        else:
            user_move = chess.Move(fr_sq, to_sq)
        if user_move not in list(self.board.legal_moves):
            print("illegal move")
            return 0
        try:
            self.board.push(user_move)
        except (Exception,):
            # illegal move
            print("illegal move")
            return
        move = self.board.pop()

        self.board.push(user_move)
        self.current_move = self.current_move.add_variation(move)
        self.moves.append(self.current_move)
        self.all_moves.append(self.current_move)
        self.update_pgn_display()

        self.move_squares = []
        self.move_squares.append(fr_col)
        self.move_squares.append(fr_row)
        self.move_squares.append(to_col)
        self.move_squares.append(to_row)
        self.display_move()

    def define_moves_squares(self):
        move_str = str(self.moves[-1].move)
        fr_col = ord(move_str[0]) - ord('a')
        fr_row = 8 - int(move_str[1])
        self.move_squares = []
        self.move_squares.append(fr_col)
        self.move_squares.append(fr_row)

        fr_col = ord(move_str[2]) - ord('a')
        fr_row = 8 - int(move_str[3])
        self.move_squares.append(fr_col)
        self.move_squares.append(fr_row)

    def update_pgn_display(self):
        window = self.window.find_element('_movelist_')
        exporter = chess.pgn.StringExporter(headers=False, variations=True, comments=True)
        pgn_string = self.game.accept(exporter)
        window.Update(self.split_line(pgn_string))

    def split_line(self, line):
        max_len_line = 58

        words = line.split(" ")
        len_line = len(words[0])
        line = words[0]
        words.pop(0)
        for word in words:
            if len_line + len(word) > max_len_line:
                line = line+"\n"
                len_line = len(word)
            else:
                len_line = len_line + 1
                line = line + " "
            len_line = len_line + len(word)
            line = line + word
        return line.split("\n")

    def display_move(self):
        board = chess.Board()
        if len(self.moves) > 0:
            moves_ = " ".join(str(self.moves[-1]).split(" ")[:2])
            self.window.find_element('b_base_time_k').Update(moves_)
        for main_move in self.moves:
            move = main_move.move

            # It copies the move played by each
            # player on the virtual board
            try:
                # print("move", move)
                board.push(move)
            except (Exception, ):
                pass

        fen = board.fen()
        self.gui.fen = fen
        self.gui.fen_to_psg_board(self.window)
        self.gui.default_board_borders(self.window)
        self.board = board
        if self.move_squares[1] + self.move_squares[0] + self.move_squares[2] + self.move_squares[3] > 0:
            self.gui.change_square_color_border(self.window, self.move_squares[1], self.move_squares[0], '#ff0000')
            self.gui.change_square_color_border(self.window, self.move_squares[3], self.move_squares[2], '#ff0000')
