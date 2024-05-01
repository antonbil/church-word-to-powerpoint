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
from common import menu_def_entry, menu_def_annotate, temp_file_name
from beautify_pgn_lines import PgnDisplay

class PgnEditor:
    """
    class for data-entry of new pgn-file
    """

    def __init__(self, gui, window, file_name = "", from_pgn_viewer=False, pgn_viewer_move=0):
        self.from_pgn_viewer = from_pgn_viewer
        self.pgn_viewer_move = pgn_viewer_move
        self.current_line = None
        self.move_squares = None
        self.game = None
        self.current_move = None
        self.moves = []
        self.all_moves = []
        self.is_win_closed = False
        self.board = chess.Board()
        self.pgn_lines = []
        self.positions = []
        self.gui = gui
        self.promoted = []
        self.move_number = 0

        self.mode = "editor-entry"
        window.find_element('_gamestatus_').Update('Mode     PGN-Editor Entry')
        self.window = window
        self.start_empty_game()
        self.pgn_display = PgnDisplay(69)

        if file_name:
            pgn = open(file_name)
            self.read_file_from_io(pgn)

        self.execute_data_entry()

    def start_empty_game(self):
        self.moves = []
        self.all_moves = []
        self.game = chess.pgn.Game()
        self.game.setup(self.board)
        self.current_move = self.game.game()
        self.move_squares = [0, 0, 0, 0]

    def read_file_from_io(self, pgn):
        self.game = chess.pgn.read_game(pgn)
        node = self.game.root()
        while len(node.variations) > 0:
            node = node.variations[0]
            # print("node", node)
            self.moves.append(node)
            self.all_moves.append(node)
        self.current_move = node
        self.update_pgn_display()

    def remove_from_this_move_onward(self):
        """
        remove current move and all successors in the line, and restore moves and board
        only restores one line: the main-line currently displayed on the self. board
        :return:
        """
        old_move = self.current_move
        index_moves = self.moves.index(old_move)
        index_all_moves = self.all_moves.index(old_move)
        parent = self.current_move.parent
        parent.variations.remove(self.current_move)
        self.moves = self.moves[:index_moves]
        self.all_moves = self.all_moves[:index_all_moves]
        self.current_move = parent

    def remove_last_move(self):
        """
        remove last move and restore moves and board
        only restores one line: the main-line currently displayed on the self. board
        :return:
        """
        parent = self.current_move.parent
        parent.variations.remove(self.current_move)
        self.moves.pop()
        self.all_moves.pop()
        self.current_move = parent
        # return
        # self.game = chess.pgn.Game()
        # self.board.pop()
        # self.moves.clear()
        #
        # # Undo all moves.
        # switchyard = collections.deque()
        # while self.board.move_stack:
        #     switchyard.append(self.board.pop())
        #
        # self.game.setup(self.board)
        # node = self.game
        #
        # # Replay all moves.
        # while switchyard:
        #     move = switchyard.pop()
        #     node = node.add_variation(move)
        #     self.moves.append(node)
        #     self.board.push(move)
        # self.current_move = node
        # self.all_moves = [m for m in self.moves]

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
        self.set_entry_mode()

        while True:
            button, value = self.window.Read(timeout=50)
            if button in (sg.WIN_CLOSED, '_EXIT_', 'Close'):
                self.is_win_closed = True
                break
            if button == 'Neutral':
                self.gui.entry_game = False
                self.gui.start_entry_mode = False
                break

            if button == 'Manual variation' and self.mode == "annotate":
                move_state = self.move_add_manual("manual variation")

            if button == 'Remove from this move onward':
                self.remove_from_this_move_onward()
                self.display_new_situation()

            if button == 'Play':
                self.gui.entry_game = False
                self.gui.start_entry_mode = False
                self.gui.start_mode_used = "play"
                break

            if button == 'Clear':
                if sg.popup_yes_no("Clear current match", "You will clear the moves for the current match\nAre you sure?")=="Yes":
                    self.board = chess.Board()
                    self.start_empty_game()
                    self.update_pgn_display()
                    self.display_move_and_line_number()
                    self.window.find_element('comment_k').Update('')

            if button == 'PGN-Viewer':
                name_file = temp_file_name
                self.game.headers['White'] = value['_White_']
                self.game.headers['Black'] = value['_Black_']
                with open(name_file, mode='w') as f:
                    f.write('{}\n\n'.format(self.game))
                self.gui.menu_elem.Update(menu_def_pgnviewer)
                self.gui.preferences.preferences["pgn_file"] = name_file
                self.gui.preferences.preferences["pgn_game"] = ""
                if not self.from_pgn_viewer:
                    pgn_viewer = PGNViewer(self.gui, self.window)
                    self.is_win_closed = pgn_viewer.is_win_closed
                break

            if button == 'PGN Move entry' or button == 'Variations Edit' or self.pgn_viewer_move>0:
                if self.mode == "editor-entry" or self.pgn_viewer_move>0:
                    self.set_mode_to_annotate()
                else:
                    self.set_entry_mode()
                    self.gui.menu_elem.Update(menu_def_entry)
                    self.set_status()
                self.moves = [m for m in self.all_moves]
                if self.pgn_viewer_move>0:
                    self.set_position_move(self.pgn_viewer_move)
                    self.pgn_viewer_move = 0
                    self.display_move_and_line_number()
                if button == 'Variations Edit':
                    self.display_move_and_line_number()
                else:
                    self.display_move()
            if self.gui.toolbar.get_button_id(button) == 'Next' and self.mode == "annotate":
                self.execute_next_move(self.move_number)

            if self.gui.toolbar.get_button_id(button) == 'Previous' and self.mode == "annotate":
                self.execute_previous_move(self.move_number)

            if button == 'Comment' and self.mode == "annotate":
                ok = self.gui.file_dialog.get_comment(self.moves[-1], self.gui)
                if ok:
                    self.update_pgn_display()

            if (button == 'Alternative manual' or self.gui.toolbar.get_button_id(button) == 'Add Move') \
                    and self.mode == "annotate":
                move_state = self.move_add_manual("manual move")

            if (button == 'Alternative' or self.gui.toolbar.get_button_id(button) == 'Best?') \
                    and self.mode == "annotate":
                self.analyse_move()
                self.update_pgn_display()
                self.display_move_and_line_number()

            if self.gui.toolbar.get_button_id(button) == "Back" and self.mode == "editor-entry":
                self.remove_last_move()
                self.display_new_situation()

            if button == 'Analyse game':
                value_white = value['_White_']
                value_black = value['_Black_']
                analysed_game = self.gui.analyse_game(value_white, value_black, self.game)
                pgn = StringIO(analysed_game)
                self.read_file_from_io(pgn)

            if button == 'Save':
                value_white = value['_White_']
                value_black = value['_Black_']
                self.gui.save_game_pgn(value_white, value_black, self.game)
                self.update_player_data()
            #
            if button == "Restore alternative":
                if len(self.promoted) > 0:
                    to_be_restored = self.promoted.pop()
                    # set current node to parent-node of the variation-node to be restored
                    parent_node = to_be_restored[0]
                    parent_node.promote_to_main(to_be_restored[1])
                    # get index of parent-node; it is the new current move
                    index = self.moves.index(parent_node)
                    self.moves = self.moves[:index]
                    move_number = len(self.moves) - 1
                    # restore the moves
                    self.restore_moves()
                    self.set_mode_to_annotate()
                    # restore the state of the current move (move-number and the from/to-squares)
                    self.move_number = move_number
                    self.define_moves_squares()
                    # display the restored baord
                    self.display_move()
                if self.mode == "manual variation":
                    self.mode = "editor-entry"
                    self.set_status()

            if button == "Remove alternative" and self.mode == "annotate":
                current_move = self.moves[-1]
                variations = current_move.variations
                list_items = [" ".join(str(v).split(" ")[0:2]) for v in variations]
                list_items.pop(0)
                if len(list_items) > 1:
                    index = 1
                    title_window = "select new main line"
                    selected_item = self.gui.get_item_from_list(list_items, title_window)
                    if selected_item:
                        # first item is removed.... so add 1 to the found index
                        index = list_items.index(selected_item) + 1
                        self.remove_variation(current_move, index)
                        self.update_pgn_display()
                        self.display_move_and_line_number()

                else:
                    if sg.popup_yes_no("Remove alternative", "OK to remove alternative:'{}'?".format(list_items[0]))=="Yes":
                        self.remove_variation(current_move, 1)
                        self.update_pgn_display()
                        self.display_move_and_line_number()

            if button == "Promote alternative" and self.mode == "annotate":
                # last one of moves is active on the board
                current_move = self.moves[-1]
                variations = current_move.variations
                #print("variations:", variations)
                if len(variations) > 1:
                    #print("number variations > 1")
                    list_items = [" ".join(str(v).split(" ")[0:2]) for v in variations]
                    index = 1
                    list_items.pop(0)
                    if len(list_items) > 1:
                        title_window = "select new main line"
                        selected_item = self.gui.get_item_from_list(list_items, title_window)
                        if selected_item:
                            # first item is removed.... so add 1 to the found index
                            index = list_items.index(selected_item) + 1
                        else:
                            # no promoting
                            index = 0

                    if index > 0:
                        self.promote_variation_to_mainline(current_move, index)

            if button == '_movelist_' and self.mode == "annotate":
                selection = value[button]
                if selection:
                    item = selection[0]
                    index = self.pgn_lines.index(item)
                    self.current_line = index
                    self.go_up = True
                    new_pos = self.pgn_display.get_position_move_from_pgn_line(item)
                    if new_pos >=1:
                        self.set_position_move(new_pos)

            if type(button) is tuple and self.mode == "annotate":
                move_from = button
                fr_row, fr_col = move_from
                if not self.gui.is_user_white:
                    fr_row = 7 - fr_row
                    fr_col = 7 - fr_col

                if fr_row == 0:
                    new_number = min(int(fr_col * (len(self.all_moves) - 1) / 7), len(self.all_moves))
                    self.set_position_move(new_number)

                elif fr_col < 4:
                    self.execute_previous_move(self.move_number)
                else:
                    self.execute_next_move(self.move_number)

            if type(button) is tuple and self.mode in ["editor-entry", "manual move", "manual variation"]:
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
                    if self.mode == "manual move":
                        legal_move, user_move = self.get_algebraic_move_from_coordinates(fr_col, fr_row, to_col, to_row)
                        if legal_move:
                            self.analise_new_move(user_move)
                            self.update_pgn_display()
                            self.update_move_display_element()
                        else:
                            sg.popup_error("No legal move", title="Error enter move",
                                           font=self.gui.text_font)
                        self.mode = "annotate"
                        self.set_status()
                        move_state = 0
                        self.display_move_and_line_number()
                    elif self.mode == "manual variation":
                        legal_move, user_move = self.get_algebraic_move_from_coordinates(fr_col, fr_row, to_col, to_row)
                        if legal_move:
                            self.analise_new_move(user_move)
                            self.set_entry_mode()
                            self.gui.menu_elem.Update(menu_def_entry)
                            self.set_status()
                            self.moves = [m for m in self.all_moves]
                            self.move_squares = []
                            self.move_squares.append(fr_col)
                            self.move_squares.append(fr_row)
                            self.move_squares.append(to_col)
                            self.move_squares.append(to_row)

                            self.display_move()
                            move_state = 0
                            sg.popup("You can now enter the remainder of the moves of the variation\n"+
                                     "Execute \"Restore alternative\" at the end of the variation-line",
                                     title="Input moves variation",
                                     font=self.gui.text_font)

                        else:
                            sg.popup_error("No legal move", title="Error enter move",
                                           font=self.gui.text_font)

                    else:
                        self.execute_move(fr_col, fr_row, to_col, to_row)
                        move_state = 0

    def set_mode_to_annotate(self):
        self.mode = "annotate"
        buttons = [self.gui.toolbar.new_button("Previous"), self.gui.toolbar.new_button("Next")
            , self.gui.toolbar.new_button("Add Move"), self.gui.toolbar.new_button("Best?")]
        self.gui.toolbar.buttonbar_add_buttons(self.window, buttons)
        self.gui.menu_elem.Update(menu_def_annotate)
        self.move_number = len(self.all_moves) - 1
        self.set_status()

    def display_new_situation(self):
        window = self.window.find_element('_movelist_')
        exporter = chess.pgn.StringExporter(headers=False, variations=True, comments=True)
        pgn_string = self.game.accept(exporter)
        # window.Update('')
        try:
            window.Update(self.split_line(pgn_string))
        except (Exception,):
            pass
        self.display_move()

    def update_player_data(self):
        self.window.find_element('_White_').Update(self.game.headers['White'])
        self.window.find_element('_Black_').Update(self.game.headers['Black'])

    def remove_variation(self, current_move, index):
        current_move.remove_variation(index)

    def move_add_manual(self, new_mode):
        sg.popup("Enter move \nby moving pieces on the board",
                 title="Enter move for " + ("White" if self.moves[-1].turn() else "Black"),
                 font=self.gui.text_font)
        self.mode = new_mode
        move_state = 0
        self.set_status()
        return move_state

    def set_status(self):
        window_element = self.window.find_element('_gamestatus_')
        if self.mode == "annotate":
            window_element.Update('Mode     PGN-Variations Edit')
        elif self.mode == "editor-entry":
            window_element.Update('Mode     PGN-Editor Entry')
        elif self.mode == "manual move":
            window_element.Update('Mode     Manual Move Entry')
        elif self.mode == "manual variation":
            window_element.Update('Mode     Manual Variation Entry')

    def set_position_move(self, new_number):
        self.moves = self.all_moves[0:new_number]
        self.move_number = len(self.moves) - 1
        if len(self.moves) > 0:
            self.current_move = self.moves[-1]
        else:
            self.game.game()
        self.display_move_and_line_number()

    def set_entry_mode(self):
        self.mode = "editor-entry"
        buttons = [self.gui.toolbar.new_button("Back")]
        self.gui.toolbar.buttonbar_add_buttons(self.window, buttons)

    def promote_variation_to_mainline(self, current_move, index):
        previous_mainline = current_move.variations[0]
        moves_index = self.all_moves.index(current_move)
        if len(self.promoted) > 0 and self.promoted[-1][2] > moves_index:
            sg.popup_error("You cannot save mainline \nif you are behind the previous mainline to be restored",
                           title="Error promote variation", font=self.gui.text_font)
            return
        self.promoted.append([current_move, previous_mainline, moves_index])
        main = current_move.variations[index]
        current_move.promote_to_main(main)
        self.restore_moves()

    def restore_moves(self):
        move_number = len(self.moves)
        self.moves = []
        self.all_moves = []
        node = self.game.root()
        i = 1
        while len(node.variations) > 0:
            node = node.variations[0]
            if i <= move_number:
                self.moves.append(node)
            self.all_moves.append(node)
            i = i + 1
        self.current_move = node
        self.update_pgn_display()

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
            self.analise_new_move(move_new)

    def analise_new_move(self, move_new):
        board = chess.Board()
        for main_move in self.moves:
            move = main_move.move
            board.push(move)
        board.push(move_new)
        str_line3 = str(move_new)
        advice = str_line3
        score = 0
        if self.mode == "manual move":
            # get engine advice for this new situation
            advice, score, pv, pv_original, alternatives = self.gui.get_advice(board, self.callback)
            # add all moves as coordinates in one line with spaces inbetween
            str_line3 = str(move_new) + " " + " ".join([str(m) for m in pv_original])
        # ask user if he/she wants to add this new variation
        text = sg.popup_get_text('variation to be added:', default_text=advice, title="Add variation?",
                                 font=self.gui.text_font)
        # add new variation if user agrees
        if text:
            current_move = self.moves[-1]
            current_move.add_line(self.uci_string2_moves(str_line3))
            if self.mode == "manual move":
                current_move.variations[-1].comment = str(score)
            else:
                self.promote_variation_to_mainline(current_move, len(current_move.variations) - 1)

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
            self.display_move_and_line_number()
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
            self.display_move_and_line_number()
        else:
            sg.popup_error("Already at the last move", title="Error next move", font=self.gui.text_font)

    def display_move_and_line_number(self):
        move_list_gui_element = self.window.find_element('_movelist_')
        if len(self.moves) > 0:
            line_number, is_available = self.pgn_display.get_line_number(self.moves[-1], self.pgn_lines)
            # print("line-number", line_number, is_available)
            move_list_gui_element.Update(
                self.pgn_lines, set_to_index=line_number, scroll_to_index=line_number - 3 if line_number > 2 else 0)
            self.define_moves_squares()
        else:
            move_list_gui_element.Update(
                self.pgn_lines)

        self.display_move()

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
        legal_move, user_move = self.get_algebraic_move_from_coordinates(fr_col, fr_row, to_col, to_row)
        if not legal_move:
            print("illegal move", fr_col, fr_row, to_col, to_row)
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

    def get_algebraic_move_from_coordinates(self, fr_col, fr_row, to_col, to_row):
        legal_move = True
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
            legal_move = False
        return legal_move, user_move

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
        pgn_string = str(self.game.game())#accept(exporter)
        lines = self.pgn_display.beautify_lines(pgn_string)
        self.pgn_lines = lines
        window.Update(lines)

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
        self.update_move_display_element()

        for main_move in self.moves:
            move = main_move.move

            # It copies the move played by each
            # player on the virtual board
            try:
                #print("move", move)
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

    def update_move_display_element(self):
        if len(self.moves) > 0:
            alternatives, move_string = self.pgn_display.get_nice_move_string(self.moves[-1])
            self.window.find_element('_currentmove_').Update(move_string + alternatives)
            self.window.find_element('comment_k').Update(self.moves[-1].comment)
