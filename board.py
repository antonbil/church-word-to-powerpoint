import PySimpleGUI as sg

class LeftBoard:
    def __init__(self, gui, images):
        self.squares = []
        self.gui = gui
        self.images = images

    def get_field_id(self, field_tuple):
        return field_tuple

    def create_board(self, is_user_white=True):
        """
        Returns board layout based on color of user. If user is white,
        the white pieces will be at the bottom, otherwise at the top.

        :param is_user_white: user has handling the white pieces
        :return: board layout
        """
        file_char_name = 'abcdefgh'

        board_layout = []

        if is_user_white:
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
        self.squares = []
        for i in range(start, end, step):
            # Row numbers at left of board is blank
            row = []
            for j in range(start, end, step):
                piece_image = self.images[self.gui.psg_board[i][j]]
                square = self.gui.render_square(piece_image, key=(i, j), location=(i, j))
                row.append(square)
            board_layout.append(row)
        for square in self.squares:
            print("square", square.Key)
        return board_layout