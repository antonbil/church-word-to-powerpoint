import PySimpleGUI as sg


class LeftBoard:
    def __init__(self, gui, images):
        self.button_square_ids = []
        self.frame_square_ids = []
        self.button_square_ids_black = []
        self.frame_square_ids_black = []
        self.gui = gui
        self.images = images

    def get_field_id(self, field_tuple):
        if self.gui.is_user_white:
            return field_tuple
        row = field_tuple[0]
        col = field_tuple[1]
        if (row, col) in self.frame_square_ids:
            return self.frame_square_ids_black[self.frame_square_ids.index((row, col))]
        else:
            return self.button_square_ids_black[self.button_square_ids.index((row, col))]

    def convert_element_key(self, row, col):
        if self.gui.is_user_white:
            return (row, col)
        if (row, col) in self.frame_square_ids:
            return self.frame_square_ids_black[self.frame_square_ids.index((row, col))]
        else:
            return self.button_square_ids_black[self.button_square_ids.index((row, col))]

    def create_board(self, is_user_white=True):
        """
        Returns board layout based on color of user. If user is white,
        the white pieces will be at the bottom, otherwise at the top.

        :param is_user_white: user has handling the white pieces
        :return: board layout
        """
        file_char_name = 'abcdefgh'

        board_layout = []

        if True:  # is_user_white:
            # Save the board with black at the top.
            start = 0
            end = 8
            step = 1
        else:
            start = 7
            end = -1
            step = -1
            file_char_name = file_char_name[::-1]

        # Loop through the board and create buttons with images
        self.frame_square_ids = []
        self.button_square_ids = []
        self.frame_square_ids_black = []
        self.button_square_ids_black = []
        for i in range(start, end, step):
            # Row numbers at left of board is blank
            row = []
            for j in range(start, end, step):
                piece_image = self.images[self.gui.psg_board[i][j]]
                square = self.gui.render_square(piece_image, key=(i, j), location=(i, j))
                row.append(square)
                self.frame_square_ids.append(square.key)
                self.frame_square_ids_black.append(square.key)
            board_layout.append(row)
        for square in self.frame_square_ids:
            self.button_square_ids.append((square[0], square[1] - 64))
            self.button_square_ids_black.append((square[0], square[1] - 64))
        self.button_square_ids_black.reverse()
        self.frame_square_ids_black.reverse()
        return board_layout
