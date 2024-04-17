import chess
import chess.pgn
import chess.svg
import PySimpleGUI as sg
import os
from io import StringIO
from annotator import annotator
import copy
import collections
from pgn_viewer.pgn_viewer import PGNViewer
from common import menu_def_pgnviewer



class DataEntry:
    """
    class for data-entry of new pgn-file
    """

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

    def remove_last_move(self):
        """
        remove last move and restore moves and board
        :return:
        """
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
        """
        start the data-entry
        main loop to enter data and add comments and variations
        :return:
        """

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
            if button == 'PGN-Viewer':
                name_file = "tempsave.pgn"
                with open(name_file, mode='w') as f:
                    f.write('{}\n\n'.format(self.game))
                self.gui.menu_elem.Update(menu_def_pgnviewer)
                self.gui.preferences.preferences["pgn_file"] = name_file
                self.gui.preferences.preferences["pgn_game"] = ""
                PGNViewer(self.gui, self.window)

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
                text = sg.popup_get_text('Enter comment', title="Input comment", font=self.gui.text_font)
                self.moves[-1].comment = text
                self.update_pgn_display()

            if button == 'Alternative manual' and self.mode == "annotate":
                self.analyse_manual_move()
                self.update_pgn_display()

            if button == 'Alternative' and self.mode == "annotate":
                self.analyse_move()
                self.update_pgn_display()

            if button == "Back" and self.mode == "entry":
                self.remove_last_move()
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

            if type(button) is tuple and self.mode == "entry":
                if move_state == 0:
                    # If fr_sq button is pressed
                    move_from = button
                    fr_row, fr_col = move_from

                    # Change the color of the "from" board square
                    self.gui.change_square_color(self.window, fr_row, fr_col)

                    move_state = 1
                elif move_state == 1:
                    move_from = button
                    to_row, to_col = move_from
                    # remove all colors from squares
                    self.gui.default_board_borders(self.window)

                    self.execute_move(fr_col, fr_row, to_col, to_row)
                    move_state = 0

    def analyse_manual_move(self):
        """
        user enters possible move, and engine adds most likely variation with score to current pgn
        :return:
        """
        # display all current possible moves to user
        list_items = [list_item for list_item in list(self.board.legal_moves)]
        list_items_algebraic = [self.board.san(list_item) for list_item in list_items]
        title_window = "Get move"
        selected_item = self.gui.get_item_from_list(list_items_algebraic, title_window)
        if selected_item:
            # move is selected by user
            # now get Move itself
            index = list_items_algebraic.index(selected_item)
            move_new = list_items[index]
            # add previous moves with new_move to board
            board = chess.Board()
            for main_move in self.moves:
                move = main_move.move
                board.push(move)

            board.push(move_new)
            # get engine advice for this new situation
            advice, score, pv, pv_original, alternatives = self.gui.get_advice(board, self.callback)
            # add all moves as coordinates in one line with spaces inbetween
            str_line3 = str(move_new) + " " + " ".join([str(m) for m in pv_original])
            # ask user if he/she wants to add this new variation
            text = sg.popup_get_text('variation to be added:', default_text=advice, title="Add variation?",
                                     font=self.gui.text_font)
            # add new variation if user agrees
            if text:
                self.moves[-1].add_line(self.uci_string2_moves(str_line3))
                self.moves[-1].variations[-1].comment = str(score)

    def uci_string2_moves(self, str_moves):
        """
        change moves in coordinates to uci-moves
        :param str_moves: string with all moves (using coordinates), separated by spaces
        :return: uci-representation of list of moves
        """
        return [chess.Move.from_uci(move) for move in str_moves.split()]

    def execute_previous_move(self, move_number):
        """
        ececute previous move (in analysis-mode)
        :param move_number: the current move-number
        :return:
        """
        if move_number > 0:
            self.move_number = move_number - 1
            self.moves.pop()
            self.define_moves_squares()
            self.display_move()
        else:
            sg.popup_error("Already at the first move", title="Error previous move", font=self.gui.text_font)

    def execute_next_move(self, move_number):
        """
        execute next move (in analysis-mode)
        :param move_number:
        :return:
        """
        if move_number < len(self.all_moves) - 1:
            self.move_number = move_number + 1
            self.moves.append(self.all_moves[self.move_number])
            self.define_moves_squares()
            self.display_move()
        else:
            sg.popup_error("Already at the last move", title="Error next move", font=self.gui.text_font)

    def callback(self, advice):
        self.window.Read(timeout=5)
        window = self.window.find_element('comment_k')
        window.Update('')
        window.Update(
            advice, append=True, disabled=True)
        self.window.Read(timeout=10)

    def analyse_move(self):
        if len(self.moves) >= len(self.all_moves):
            sg.popup_error("No analysis for last move", title="Error analysis", font=self.gui.text_font)
            return
        # str_line3 = "a7a6 g1f3 g8f6"
        # move2_main.add_line(UCIString2Moves(str_line3))
        advice, score, pv, pv_original, alternatives = self.gui.get_advice(self.board, self.callback)
        is_black = not self.board.turn == chess.WHITE
        move_number = self.move_number // 2
        test = False
        if test:
            # test-code to examine alternatives; not clear yet what scores in Stockfish really mean, so not use it yet
            a_list = [item for item in alternatives.items() if len(item[0].split(" ")) > 7]
            max_alt = 3
            if len(a_list) < 3:
                max_alt = len(a_list)
            reverse_sort = not self.board.turn == chess.WHITE
            alt_1 = sorted(a_list, key=lambda item: item[1][0], reverse=reverse_sort)[0:max_alt]
            alt_2 = sorted(a_list, key=lambda item: item[1][0], reverse=not reverse_sort)[0:max_alt]
            print("alternatives", [[list_item[0], list_item[1][0]] for list_item in alt_1])
            print("alternatives2", [[list_item[0], list_item[1][0]] for list_item in alt_2])
        str_line3 = " ".join([str(m) for m in pv_original])
        print("add line variation", str_line3, score)
        text = sg.popup_get_text('variation to be added:', default_text=advice, title="Add variation?",
                                 font=self.gui.text_font)
        if text:
            self.moves[-1].add_line(self.uci_string2_moves(str_line3))
            self.moves[-1].variations[-1].comment = str(score)
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
