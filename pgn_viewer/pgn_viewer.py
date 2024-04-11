import chess
import chess.pgn
import chess.svg
from cairosvg import svg2png
class PGNViewer:
    """header dialog class"""
    def __init__(self, gui, window):
        self.gui = gui
        # window.find_element('comment_k').update(visible=False)
        # window.find_element('pgn_row').update(visible=True)
        window.find_element('_gamestatus_').Update('Mode     PGN-Viewer')
        self.window = window
        self.moves = []
        self.current_move = None
        self.execute_pgn()
        """
        end()→ GameNode[source] Follows the main variation to the end and returns the last node
        turn()→ chess.Color[source] Gets the color to move at this node.
        variations: List[ChildNode] A list of child nodes
        """

    def execute_pgn(self):
        # creating a virtual chessboard
        board = chess.Board()

        print(board)
        # We need to convert the PGN string into a StringIO object
        # to use a string in python-chess
        from io import StringIO

        # Paste your PGN string here
        pgn_string = """[Event "Live Chess"]
        [Site "Chess.com"]
        [Date "2021.08.05"]
        [Round "-"]
        [White "urvishmhjn"]
        [Black "yannickhs"]
        [Result "1-0"]
        [CurrentPosition "r1b1q1r1/p2nbk2/4pp1Q/1p1p3B/2pP3N/1PP1P3/P4PPP/R4RK1 b - -"]
        [Timezone "UTC"]
        [ECO "A45"]
        [UTCDate "2021.08.05"]
        [UTCTime "09:25:32"]
        [WhiteElo "1220"]
        [BlackElo "1140"]
        [TimeControl "900+10"]
        [Termination "urvishmhjn won by resignation"]

        1. d4 Nf6 2. Bf4 e6 3. e3 d5 4. Bd3 c5 5. c3 c4 6. Be2 Nc6
        7. Nf3 Be7 8. Nbd2 O-O 9. O-O Nh5 10. Be5 Nxe5 11. Nxe5 Nf6
        12. b3 b5 13. Qc2 Nd7 14. Ndf3 f6 15. Ng4 h5 16. Nh6+ gxh6
        17. Qg6+ Kh8 18. Qxh6+ Kg8 19. Qxh5 Qe8 20. Qg4+ Kf7
        21. Nh4 Rg8 22. Qh5+ Kf8 23. Qh6+ Kf7 24. Bh5+ 1-0
        """

        pgn = open('2023-09-28-Anton-Gerrit.pgn')

        # Reading the game
        game = chess.pgn.read_game(pgn)
        self.current_move = game.game()
        self.moves.append(self.current_move)
        self.window.find_element('_movelist_').Update(
            game.mainline_moves(), append=True, disabled=True)
        self.window.find_element('_Black_').Update(game.headers['Black'])
        self.window.find_element('_White_').Update(game.headers['White'])
        info = "{} ({})".format((game.headers['Site'].replace('?', "")+game.headers['Date'].replace('?', "")).strip(),game.headers['Result'])
        self.window.find_element('advise_info_k').Update(info)
        #'advise_info_k'

        move_number = 0

        self.display_move()

        while True:
            button, value = self.window.Read(timeout=50)
            if button == 'Neutral':
                is_exit_game = True
                self.entry_game = False
                self.start_entry_mode = False
                break
            if button == 'Next':
                move_number = self.execute_next_move(move_number)
            if button == 'Previous':
                move_number = self.execute_previous_move(move_number)
            if type(button) is tuple:
                # If fr_sq button is pressed
                move_from = button
                fr_row, fr_col = move_from
                col = chr(fr_col + ord('a'))
                row = str(7 - fr_row + 1)
                coord = col+row
                my_variation = False
                for variation in self.current_move.variations:
                    move = str(variation.move)

                    if move.startswith(coord):
                        self.moves.append(variation)
                        self.current_move = variation
                        move_number = move_number + 1
                        my_variation = True
                    if my_variation:
                        self.display_move()
                if not my_variation:
                    if fr_col < 4:
                        move_number = self.execute_previous_move(move_number)
                    else:
                        move_number = self.execute_next_move(move_number)

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
        window = self.window.find_element('_movelist_')
        window.Update('')
        window.Update(
            self.current_move.mainline_moves(), append=True, disabled=True)
        return fen
