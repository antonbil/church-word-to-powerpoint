import chess
import chess.pgn
import chess.svg
from cairosvg import svg2png
class PGNViewer:
    """header dialog class"""
    def __init__(self, gui, window):
        self.gui = gui
        window.find_element('comment_k').update(visible=False)
        window.find_element('pgn_row').update(visible=True)
        self.window = window
        self.execute_pgn()

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

        # Converting the string into StringIO object
        pgn = StringIO(pgn_string)
        pgn = open('2023-09-28-Anton-Gerrit.pgn')

        # Reading the game
        game = chess.pgn.read_game(pgn)
        self.window.find_element('_movelist_').Update(
            game.mainline_moves(), append=True, disabled=True)
        self.window.find_element('_Black_').Update(game.headers['Black'])
        self.window.find_element('_White_').Update(game.headers['White'])
        # username of the player playing with white
        white_username = game.headers['White']

        # username of the player playing with black
        black_username = game.headers['Black']
        #time_control = game.headers['TimeControl']

        # time format of the game
        # who won the game
        game_result = game.headers['Result']

        # Make sure that each header name
        # used above is present in the PGN
        print("White's chess.com Username:", white_username)
        print("Black's chess.com Username:", black_username)
        #print("Game's Time Control:", time_control, "seconds")
        print("Game Result:", game_result)

        # If white wins: 1-0
        # If black wins: 0-1
        # If game drawn: 1/2-1/2
        # The move number for which we want the FEN
        move_number = 8

        fen = self.display_move(board, game, move_number)
        print(fen)
        print(board)
        chess.svg.board(board, size=350)
        svg_text = chess.svg.board(
            board,
            fill=dict.fromkeys(board.attacks(chess.E4), "#cc0000cc"),
            arrows=[chess.svg.Arrow(chess.E4, chess.F6, color="#0000cccc")],
            squares=chess.SquareSet(chess.BB_DARK_SQUARES & chess.BB_FILE_B),
            size=350)

        with open('example-board.svg', 'w') as f:
            f.write(svg_text)

        svg2png(bytestring=svg_text, write_to='example-board.png')

        while True:
            button, value = self.window.Read(timeout=50)
            if button == 'Neutral':
                is_exit_game = True
                self.entry_game = False
                self.start_entry_mode = False
                break
            if button == 'Next':
                move_number = move_number + 1
                print("move nmber:", move_number)
                self.display_move(board, game, move_number)
            if button == 'Previous':
                move_number = move_number - 1
                print("move nmber:", move_number)
                self.display_move(board, game, move_number)

    def display_move(self, board, game, move_number):
        board = chess.Board()
        # Go through each move in the game until
        # we reach the required move number
        for number, move in enumerate(game.mainline_moves()):

            # It copies the move played by each
            # player on the virtual board
            print("move", move)
            board.push(move)

            # Remember that number starts from 0
            if number == move_number:
                break
        fen = board.fen()
        self.gui.fen = fen
        self.gui.fen_to_psg_board(self.window)
        return fen
