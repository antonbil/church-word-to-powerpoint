import PySimpleGUI as sg
import PIL
from PIL import Image
import io


def convert_to_bytes(file_or_bytes, resize=None):
    """
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (Union[str, bytes])
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    :param fill: If True then the image is filled/padded so that the image is not distorted
    :type fill: (bool)
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    """
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        try:
            img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = PIL.Image.open(dataBytesIO)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height / cur_height, new_width / cur_width)
        img = img.resize((int(cur_width * scale), int(cur_height * scale)), PIL.Image.LANCZOS)
    with io.BytesIO() as bio:
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()

class LeftBoard:
    """
    help-functions for the board to distinguish between black- and white (board is flipped if user == black)
    """
    def __init__(self, gui, images):
        self.button_square_ids_white = []
        self.frame_square_ids_white = []
        self.button_square_ids_black = []
        self.frame_square_ids_black = []
        self.gui = gui
        self.images = images

    def get_field_id(self, field_tuple):
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

    def create_board(self, is_user_white=True):
        """
        Returns board layout based on color of user. If user is white,
        the white pieces will be at the bottom, otherwise at the top.

        :param is_user_white: user has handling the white pieces
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
                piece_image = self.images[self.gui.psg_board[i][j]]
                button_square_id = (i, j)
                square = self.render_square(piece_image, key=button_square_id, location=(i, j))
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
        Change the color of a square based on square row and col.
        """
        btn_sq = window.find_element(key=self.get_field_id((row, col + 64)))
        # btn_sq.Update(border_width=4)
        btn_sq.widget.configure(background=color, borderwidth=4, relief="flat")

    def change_square_color(self, window, row, col):
        """
        Change the color of a square based on square row and col.
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
        Redraw board at start and afte a move.

        :param window:
        :return:
        """
        for i in range(8):
            for j in range(8):
                color = self.gui.sq_dark_color if (i + j) % 2 else \
                    self.gui.sq_light_color
                piece_image = self.images[self.gui.psg_board[i][j]]
                elem = window.find_element(key=self.get_field_id((i, j)))
                imgbytes = convert_to_bytes(piece_image, (self.gui.FIELD_SIZE, self.gui.FIELD_SIZE))
                elem.Update(button_color=('white', color),
                            image_data=imgbytes, image_size=(self.gui.FIELD_SIZE, self.gui.FIELD_SIZE))

    def render_square(self, image, key, location):
        """ Returns an RButton (Read Button) with image image """
        if (location[0] + location[1]) % 2:
            color = self.gui.sq_dark_color  # Dark square
        else:
            color = self.gui.sq_light_color
        imgbytes = convert_to_bytes(image, (self.gui.FIELD_SIZE, self.gui.FIELD_SIZE))
        return sg.Frame('', [
            [sg.RButton('', image_data=imgbytes, size=(1, 1), image_size=(self.gui.FIELD_SIZE, self.gui.FIELD_SIZE),
                        border_width=0, button_color=('white', color),
                        pad=(0, 0), key=key)]],
                        background_color=color, pad=(0, 0),
                        border_width=4, key=(key[0], key[1] + 64)
                        , relief=sg.RELIEF_FLAT)




