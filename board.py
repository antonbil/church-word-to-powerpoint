import PySimpleGUI as sg
import PIL
from PIL import Image
import io
import os
import chess
import copy
import sys
from common import ico_path, APP_NAME, APP_VERSION

IMAGE_PATH = 'Images/60'  # path to the chess pieces

BLANK = 0  # piece names
PAWNB = 1
KNIGHTB = 2
BISHOPB = 3
ROOKB = 4
KINGB = 5
QUEENB = 6
PAWNW = 7
KNIGHTW = 8
BISHOPW = 9
ROOKW = 10
KINGW = 11
QUEENW = 12

# Images/60
blank = os.path.join(IMAGE_PATH, 'blank.png')
bishopB = os.path.join(IMAGE_PATH, 'bB.png')
bishopW = os.path.join(IMAGE_PATH, 'wB.png')
pawnB = os.path.join(IMAGE_PATH, 'bP.png')
pawnW = os.path.join(IMAGE_PATH, 'wP.png')
knightB = os.path.join(IMAGE_PATH, 'bN.png')
knightW = os.path.join(IMAGE_PATH, 'wN.png')
rookB = os.path.join(IMAGE_PATH, 'bR.png')
rookW = os.path.join(IMAGE_PATH, 'wR.png')
queenB = os.path.join(IMAGE_PATH, 'bQ.png')
queenW = os.path.join(IMAGE_PATH, 'wQ.png')
kingB = os.path.join(IMAGE_PATH, 'bK.png')
kingW = os.path.join(IMAGE_PATH, 'wK.png')

images = {
    BISHOPB: bishopB, BISHOPW: bishopW, PAWNB: pawnB, PAWNW: pawnW,
    KNIGHTB: knightB, KNIGHTW: knightW, ROOKB: rookB, ROOKW: rookW,
    KINGB: kingB, KINGW: kingW, QUEENB: queenB, QUEENW: queenW, BLANK: blank
}

initial_board = [[ROOKB, KNIGHTB, BISHOPB, QUEENB, KINGB, BISHOPB, KNIGHTB, ROOKB],
                 [PAWNB, ] * 8,
                 [BLANK, ] * 8,
                 [BLANK, ] * 8,
                 [BLANK, ] * 8,
                 [BLANK, ] * 8,
                 [PAWNW, ] * 8,
                 [ROOKW, KNIGHTW, BISHOPW, QUEENW, KINGW, BISHOPW, KNIGHTW, ROOKW]]

white_init_promote_board = [[QUEENW, ROOKW, BISHOPW, KNIGHTW]]

black_init_promote_board = [[QUEENB, ROOKB, BISHOPB, KNIGHTB]]
# Promote piece from psg (pysimplegui) to pyc (python-chess)
promote_psg_to_pyc = {
    KNIGHTB: chess.KNIGHT, BISHOPB: chess.BISHOP,
    ROOKB: chess.ROOK, QUEENB: chess.QUEEN,
    KNIGHTW: chess.KNIGHT, BISHOPW: chess.BISHOP,
    ROOKW: chess.ROOK, QUEENW: chess.QUEEN
}

def convert_to_bytes(file_or_bytes, resize=None):
    """
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (Union[str, bytes])
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    """
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        try:
            img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as _:
            data_bytes_io = io.BytesIO(file_or_bytes)
            img = PIL.Image.open(data_bytes_io)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height / cur_height, new_width / cur_width)
        img = img.resize((int(cur_width * scale), int(cur_height * scale)), PIL.Image.LANCZOS)
    with io.BytesIO() as bio:
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()

class ChessBoard:
    """
    class for the chaess-board to manage the display and editing of the chess-board

    """
    def __init__(self, gui):
        self.button_square_ids_white = []
        self.frame_square_ids_white = []
        self.button_square_ids_black = []
        self.frame_square_ids_black = []
        self.gui = gui
        # psg_board1 is an 8 x 8 matrix representing a chessboard.
        # each element represents a square with a piece, or BLANK (empty)
        self.psg_board1 = None

    def get_field_id(self, field_tuple):
        """

        :param field_tuple: (x,y)-tuple that holds the x-y-coordinates of the square involved
        :return: an (x,y)-tuple that is the same as the input if white is playing from bottom to top
        if white is playing from top to bottom (not is_user_white) the reverse-tuple is returned
        """
        if self.gui.is_user_white:
            return field_tuple
        row = field_tuple[0]
        col = field_tuple[1]
        if (row, col) in self.frame_square_ids_white:  # col > 64
            return self.frame_square_ids_black[self.frame_square_ids_white.index((row, col))]
        else:
            return self.button_square_ids_black[self.button_square_ids_white.index((row, col))]

    def get_field_id_from_row_col(self, row, col):
        return self.get_field_id((row, col))

    def create_board(self):
        """
        Returns board layout based on color of user. If user is white,
        the white pieces will be at the bottom.
        The case that white-pieces are at the top is handled by the get_field_id-method.
        :return: board layout
        """
        file_char_name = 'abcdefgh'

        board_layout = []

        start = 0
        end = 8
        step = 1

        # Loop through the board and create buttons with images
        self.frame_square_ids_white = []
        self.button_square_ids_white = []
        self.frame_square_ids_black = []
        self.button_square_ids_black = []
        for i in range(start, end, step):
            # Row numbers at left of board is blank
            row = []
            for j in range(start, end, step):
                piece_image = images[self.psg_board1[i][j]]
                button_square_id = (i, j)
                square = self.render_square(piece_image, key=button_square_id, location=(i, j),
                                            piece_id=self.psg_board1[i][j])
                row.append(square)
                # save key to white- and black-lists
                #   frame-square has 64 added to it, to distinguish it from a button-square
                frame_square_id = (i, j + 64)
                self.frame_square_ids_white.append(frame_square_id)
                self.frame_square_ids_black.append(frame_square_id)
                self.button_square_ids_white.append(button_square_id)
                self.button_square_ids_black.append(button_square_id)
            board_layout.append(row)
        # reverse the black-lists
        self.button_square_ids_black.reverse()
        self.frame_square_ids_black.reverse()
        return board_layout

    def change_square_color_border(self, window, row, col, color):
        """
        Change the color of a square-background based on square row and col.
        """
        btn_sq = window.find_element(key=self.get_field_id((row, col + 64)))
        # btn_sq.Update(border_width=4)
        btn_sq.widget.configure(background=color, borderwidth=4, relief="flat")

    def change_square_color(self, window, row, col, color):
        """
        Change the color of a square-background based on square row and col.
        """
        btn_sq = window.find_element(key=self.get_field_id((row, col + 64)))
        # btn_sq.Update(border_width=4)
        btn_sq.widget.configure(background=color, borderwidth=4, relief="flat")
        window.find_element(key=self.get_field_id((row, col))).widget.configure(background=color,
                                                                                activeforeground=color, activebackground=color)

    def change_square_color_move(self, window, row, col):
        """
        Change the color of a square based on square row and col indicating a move from human or computer.
        """
        btn_sq = window.find_element(key=self.get_field_id((row, col)))
        is_dark_square = True if (row + col) % 2 else False
        bd_sq_color = self.gui.move_sq_dark_color if is_dark_square else self.gui.move_sq_light_color
        btn_sq.Update(button_color=('white', bd_sq_color))

    def get_square_color_pos(self, window, row, col):
        """
        Change the color of a square based on square row and col.
        """
        btn_sq = window.find_element(key=self.get_field_id((row, col)))
        return btn_sq.widget.winfo_x(), btn_sq.widget.winfo_y()

    def redraw_board(self, window):
        """
        Redraw board at start and after a move.

        :param window:
        :return:
        """
        for i in range(8):
            for j in range(8):
                color = self.gui.sq_dark_color if (i + j) % 2 else \
                    self.gui.sq_light_color
                piece_id = self.psg_board1[i][j]
                color = self.get_reverse_color(color, piece_id)
                piece_image = images[piece_id]
                elem = window.find_element(key=self.get_field_id((i, j)))
                imgbytes = convert_to_bytes(piece_image, (self.gui.FIELD_SIZE, self.gui.FIELD_SIZE))
                elem.Update(button_color=('white', color),
                            image_data=imgbytes, image_size=(self.gui.FIELD_SIZE, self.gui.FIELD_SIZE))

    def render_square(self, image, key, location, piece_id=BLANK):
        """
        Returns an RButton (Read Button) with image image
        :param image: image of the piece at the square
        :param key: the key= (x,y)-tuple of the square
        :param location:
        :param piece_id: id of piece to be rendered
        :return:
        """
        if (location[0] + location[1]) % 2:
            color = self.gui.sq_dark_color  # Dark square
        else:
            color = self.gui.sq_light_color
        color = self.get_reverse_color(color, piece_id)
        imgbytes = convert_to_bytes(image, (self.gui.FIELD_SIZE, self.gui.FIELD_SIZE))
        return sg.Frame('', [
            [sg.RButton('', image_data=imgbytes, size=(1, 1), image_size=(self.gui.FIELD_SIZE, self.gui.FIELD_SIZE),
                        border_width=0, button_color=('white', color),
                        pad=(0, 0), key=key)]],
                        background_color=color, pad=(0, 0),
                        border_width=4, key=(key[0], key[1] + 64)
                        , relief=sg.RELIEF_FLAT)

    def get_reverse_color(self, color, piece_id):
        if False and not piece_id == BLANK:
            reverse_color = "#{}{}{}".format(color[5:7], color[3:5], color[1:3])
            color = reverse_color
        return color

    def fen_to_psg_board(self, window):
        """ Update psg_board based on FEN
        :param window: the window the board is part of
        """
        psgboard = []

        # Get piece locations only to build psg board
        pc_locations = self.gui.fen.split()[0]

        board = chess.BaseBoard(pc_locations)
        old_r = None

        for s in chess.SQUARES:
            r = chess.square_rank(s)

            if old_r is None:
                piece_r = []
            elif old_r != r:
                psgboard.append(piece_r)
                piece_r = []
            elif s == 63:
                psgboard.append(piece_r)

            try:
                pc = board.piece_at(s ^ 56)
            except Exception:
                pc = None
                logging.exception('Failed to get piece.')

            if pc is not None:
                pt = pc.piece_type
                c = pc.color
                if c:
                    if pt == chess.PAWN:
                        piece_r.append(PAWNW)
                    elif pt == chess.KNIGHT:
                        piece_r.append(KNIGHTW)
                    elif pt == chess.BISHOP:
                        piece_r.append(BISHOPW)
                    elif pt == chess.ROOK:
                        piece_r.append(ROOKW)
                    elif pt == chess.QUEEN:
                        piece_r.append(QUEENW)
                    elif pt == chess.KING:
                        piece_r.append(KINGW)
                else:
                    if pt == chess.PAWN:
                        piece_r.append(PAWNB)
                    elif pt == chess.KNIGHT:
                        piece_r.append(KNIGHTB)
                    elif pt == chess.BISHOP:
                        piece_r.append(BISHOPB)
                    elif pt == chess.ROOK:
                        piece_r.append(ROOKB)
                    elif pt == chess.QUEEN:
                        piece_r.append(QUEENB)
                    elif pt == chess.KING:
                        piece_r.append(KINGB)

            # Else if pc is None or square is empty
            else:
                piece_r.append(BLANK)

            old_r = r

        self.psg_board1 = psgboard
        self.redraw_board(window)

    def get_promo_piece(self, move, stm, human):
        """
        Returns promotion piece.

        :param move: python-chess format
        :param stm: side to move
        :param human: if side to move is human this is True
        :return: promoted piece in python-chess and pythonsimplegui formats
        """
        # If this move is from a user, we will show a window with piece images
        if human:
            psg_promo = self.select_promotion_piece(stm)

            # If user pressed x we set the promo to queen
            if psg_promo is None:
                logging.info('User did not select a promotion piece, set this to queen.')
                psg_promo = QUEENW if stm else QUEENB

            pyc_promo = promote_psg_to_pyc[psg_promo]
        # Else if move is from computer
        else:
            pyc_promo = move.promotion  # This is from python-chess
            if stm:
                if pyc_promo == chess.QUEEN:
                    psg_promo = QUEENW
                elif pyc_promo == chess.ROOK:
                    psg_promo = ROOKW
                elif pyc_promo == chess.BISHOP:
                    psg_promo = BISHOPW
                elif pyc_promo == chess.KNIGHT:
                    psg_promo = KNIGHTW
            else:
                if pyc_promo == chess.QUEEN:
                    psg_promo = QUEENB
                elif pyc_promo == chess.ROOK:
                    psg_promo = ROOKB
                elif pyc_promo == chess.BISHOP:
                    psg_promo = BISHOPB
                elif pyc_promo == chess.KNIGHT:
                    psg_promo = KNIGHTB

        return pyc_promo, psg_promo

    def select_promotion_piece(self, stm):
        """
        Allow user to select a piece type to promote to.

        :param stm: side to move
        :return: promoted piece, i.e QUEENW, QUEENB ...
        """
        piece = None
        board_layout, row = [], []

        psg_promote_board = copy.deepcopy(white_init_promote_board) if stm else copy.deepcopy(black_init_promote_board)

        # Loop through board and create buttons with images.
        for i in range(1):
            for j in range(4):
                piece_image = images[psg_promote_board[i][j]]
                row.append(self.render_square(piece_image, key=(i, j),
                                              location=(i, j), piece_id=psg_promote_board[i][j]))

            board_layout.append(row)

        platform = sys.platform
        promo_window = sg.Window('{} {}'.format(APP_NAME, APP_VERSION),
                                 board_layout,
                                 default_button_element_size=(12, 1),
                                 auto_size_buttons=False,
                                 icon=ico_path[platform]['pecg'])

        while True:
            button, value = promo_window.Read(timeout=0)
            if button is None:
                break
            if type(button) is tuple:
                move_from = button
                fr_row, fr_col = move_from
                piece = psg_promote_board[fr_row][fr_col]
                break

        promo_window.Close()

        return piece

    def create_initial_board(self):
        """
        create the initial board
        :return:
        """
        self.psg_board1 = copy.deepcopy(initial_board)

    def psg_board_get_piece(self, row, col):
        """
        get the id of the chess-piece that is located on the square identified with row and col
        :param row: the row of the square
        :param col: the col of the square
        :return:
        """
        return self.psg_board1[row][col]

    def psg_board_set_piece(self, row, col, piece):
        """
        set the piece on the square identified with row and col
        :param row: the row of the square
        :param col: the col of the square
        :param piece:  the piece to be set
        :return:
        """
        self.psg_board1[row][col] = piece

    def update_rook(self, window, move):
        """
        Update rook location for castle move.

        :param window:
        :param move: uci move format
        :return:
        """
        if move == 'e1g1':
            fr = chess.H1
            to = chess.F1
            pc = ROOKW
        elif move == 'e1c1':
            fr = chess.A1
            to = chess.D1
            pc = ROOKW
        elif move == 'e8g8':
            fr = chess.H8
            to = chess.F8
            pc = ROOKB
        elif move == 'e8c8':
            fr = chess.A8
            to = chess.D8
            pc = ROOKB

        self.psg_board1[self.gui.get_row(fr)][self.gui.get_col(fr)] = BLANK
        self.psg_board1[self.gui.get_row(to)][self.gui.get_col(to)] = pc
        self.redraw_board(window)

    def get_chess_coordinates(self, button_square):
        """
        get the coordinates of the chess square
        :param button_square: the id of the chess square that is selected
        :return: the chess-coordinate (like b6 etc.) and the col and row of the square
        """
        square_selected = self.get_field_id(button_square)
        row_nr, col_nr = square_selected
        col = chr(col_nr + ord('a'))
        row = str(7 - row_nr + 1)
        coord = col + row
        return coord, col_nr, row_nr

    def get_chess_row_col(self, physical_square_id):
        """
        get the logical id of the chess square, and returns it
        :param physical_square_id:
        :return:
        """
        locical_square_id = self.get_field_id(physical_square_id)
        row, col = locical_square_id
        return locical_square_id, row, col
