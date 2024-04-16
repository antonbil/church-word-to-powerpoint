import chess
import chess.pgn
import chess.svg
import PySimpleGUI as sg
import os
from io import StringIO
from annotator import annotator


class DataEntry:
    """header dialog class"""

    def __init__(self, gui, window):
        self.board = chess.Board()
        self.pgn_lines = []
        self.positions = []
        self.gui = gui
        window.find_element('_gamestatus_').Update('Mode     PGN-Viewer')
        self.window = window
        self.moves = []
        self.game = chess.pgn.Game()
        self.game.setup(self.board)
        self.current_move = self.game.game()
        self.move_squares = [0, 0, 0, 0]

        self.execute_data_entry()

    def execute_data_entry(self):

        self.display_move()
        move_state = 0
        move_str = ""
        piece = None
        moved_piece = None
        fr_sq = None
        fr_row = 0
        fr_col = 0

        while True:
            button, value = self.window.Read(timeout=50)
            if button == 'Neutral':
                is_exit_game = True
                self.gui.entry_game = False
                self.gui.start_entry_mode = False
                break
            if type(button) is tuple:
                if move_state == 0:
                    # If fr_sq button is pressed
                    move_from = button
                    fr_row, fr_col = move_from
                    col = chr(fr_col + ord('a'))
                    row = str(7 - fr_row + 1)
                    move_str = col + row
                    piece = self.gui.psg_board[fr_row][fr_col]  # get the move-from piece
                    fr_sq = chess.square(fr_col, 7 - fr_row)

                    # Change the color of the "fr" board square
                    self.gui.change_square_color(self.window, fr_row, fr_col)

                    move_state = 1
                    moved_piece = self.board.piece_type_at(chess.square(fr_col, 7 - fr_row))  # Pawn=1
                    print("selected piece", moved_piece)
                    move_state = 1
                elif move_state == 1:
                    move_from = button
                    to_row, to_col = move_from
                    col = chr(to_col + ord('a'))
                    row = str(7 - to_row + 1)
                    move_str = move_str + col + row
                    to_sq = chess.square(to_col, 7 - to_row)
                    self.gui.default_board_borders(self.window)

                    self.execute_move(fr_col, fr_row, fr_sq, to_col, to_row, to_sq, moved_piece, move_str)
                    move_str = ""
                    move_state = 0

    def execute_move(self, fr_col, fr_row, fr_sq, to_col, to_row, to_sq, moved_piece, move_str):
        # Change the color of the "fr" board square
        self.gui.change_square_color(self.window, to_row, to_col)
        # If user move is a promote
        if self.gui.relative_row(to_sq, self.board.turn) == 7 and \
                moved_piece == chess.PAWN:
            is_promote = True
            pyc_promo, psg_promo = self.gui.get_promo_piece(
                user_move, self.board.turn, True)
            user_move = chess.Move(fr_sq, to_sq, promotion=pyc_promo)
        else:
            user_move = chess.Move(fr_sq, to_sq)
        if user_move not in list(self.board.legal_moves):
            print("illegal move")
            return 0
        print("my move", move_str)
        try:
            print("user_move", user_move)
            self.board.push(user_move)
        except Exception as e:
            # illegal move
            print("exception, e")
            return
        move = self.board.pop()

        print("added move", move)
        self.board.push(user_move)
        self.current_move = self.current_move.add_variation(move)
        self.moves.append(self.current_move)
        window = self.window.find_element('_movelist_')
        exporter = chess.pgn.StringExporter(headers=False, variations=False, comments=False)
        pgn_string = self.game.accept(exporter)
        # window.Update('')
        try:
            window.Update(self.split_line(pgn_string))
        except:
            return
        print("node:", self.current_move)
        self.move_squares = []
        self.move_squares.append(fr_col)
        self.move_squares.append(fr_row)
        self.move_squares.append(to_col)
        self.move_squares.append(to_row)
        self.display_move()

    def split_line(self, line):
        max_len_line = 58

        words = line.split(" ")
        len_line = len(words[0])
        line=words[0]
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
        for main_move in self.moves:
            move = main_move.move

            # It copies the move played by each
            # player on the virtual board
            try:
                # print("move", move)
                board.push(move)
            except:
                pass

        fen = board.fen()
        self.gui.fen = fen
        self.gui.fen_to_psg_board(self.window)
        self.gui.default_board_borders(self.window)
        self.board = board
        if self.move_squares[1] + self.move_squares[0] + self.move_squares[2] + self.move_squares[3] > 0:
            self.gui.change_square_color_border(self.window, self.move_squares[1], self.move_squares[0], '#ff0000')
            self.gui.change_square_color_border(self.window, self.move_squares[3], self.move_squares[2], '#ff0000')
