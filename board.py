import PySimpleGUI as sg


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
                square = self.gui.render_square(piece_image, key=button_square_id, location=(i, j))
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
