import chess
import PySimpleGUI as sg
from io import StringIO


# tool-library for pgn_editor and pgn_viewer
def get_and_add_variation(current_move, ply_number, board, callback, comment_element, gui):
    """
    get variation from advisor, and add it to the current_move.
    replace existing variation if user grants it
    :param current_move:
    :param ply_number:
    :param board:
    :param callback:
    :param comment_element:
    :param gui:
    :return:
    """
    advice, score, pv, pv_original, alternatives = gui.get_advice(board, callback)
    is_black = not board.turn == chess.WHITE
    move_number = ply_number // 2
    test = False
    if test:
        # test-code to examine alternatives; not clear yet what scores in Stockfish really mean, so not use it yet
        a_list = [item for item in alternatives.items() if len(item[0].split(" ")) > 7]
        max_alt = 3
        if len(a_list) < 3:
            max_alt = len(a_list)
        reverse_sort = not board.turn == chess.WHITE
        alt_1 = sorted(a_list, key=lambda item: item[1][0], reverse=reverse_sort)[0:max_alt]
        alt_2 = sorted(a_list, key=lambda item: item[1][0], reverse=not reverse_sort)[0:max_alt]
        print("alternatives", [[list_item[0], list_item[1][0]] for list_item in alt_1])
        print("alternatives2", [[list_item[0], list_item[1][0]] for list_item in alt_2])
    str_line3 = " ".join([str(m) for m in pv_original])
    text = gui.input_dialog.popup_get_text(sg, gui, 'variation to be added:', title="Add variation?",
                                           default_text=advice)
    if text:
        first_move = str_line3.split(" ")[0].strip()
        check_for_variation_replace(current_move, first_move)

        current_move.add_line(uci_string2_moves(str_line3))
        current_move.variations[-1].comment = str(score)
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

        comment_element.Update('')
        comment_element.Update(
            "{} {}".format(" ".join(res_moves), score))


def check_for_variation_replace(current_move, first_move):
    """
    asks user if existing variation is to be replaced
    :param current_move:
    :param first_move:
    :return:
    """
    move_present = False
    variation_nr = 0
    for variation in current_move.variations:
        if str(variation.move) == first_move:
            move_present = True
            break
        variation_nr = variation_nr + 1
    if move_present:
        if sg.popup_yes_no(
                "Variation exists", "A variation starting with {} already exists\n".format(first_move) +
                                    "Replace this variation?") == "Yes":
            remove_variation(current_move, variation_nr)


def remove_variation(current_move, index):
    current_move.remove_variation(index)


def uci_string2_moves(str_moves):
    """
    change moves in coordinates to uci-moves
    :param str_moves: string with all moves (using coordinates), separated by spaces
    :return: uci-representation of list of moves
    """
    return [chess.Move.from_uci(move) for move in str_moves.split()]


def merge_into_current_game(first_game, analysed_game):
    pgn = StringIO(analysed_game)
    game2 = chess.pgn.read_game(pgn)
    current_move = first_game.game()
    current_move_second = game2.game()
    while len(current_move.variations) > 0:
        if current_move_second.comment:
            # current_move.comment = current_move_second.comment + " " + current_move.comment
            current_move.comment = create_new_comment(current_move.comment, current_move_second.comment)

        variations_first = [l for l in current_move.variations]
        variations_first.pop(0)
        variations_second = [l for l in current_move_second.variations]
        variations_second.pop(0)
        for variation_second in variations_second:
            found_move = False
            move_second = str(variation_second.move)
            for v1 in variations_first:
                if move_second == str(v1.move):
                    # get comment from variation-second
                    comments_second = []
                    vs = variation_second
                    while len(vs.variations) > 0:
                        if vs.comment:
                            comments_second.append(vs.comment)
                        vs = vs.variations[0]
                    if vs.comment:
                        comments_second.append(vs.comment)

                    # add comments to last node in v1-variation
                    vf = v1
                    while len(vf.variations) > 0:
                        vf = vf.variations[0]
                    vf.comment = create_new_comment(vf.comment, " ".join(comments_second)).strip()
                    found_move = True
                    break
            if not found_move:
                current_move.variations.append(variation_second)
        current_move = current_move.variations[0]
        current_move_second = current_move_second.variations[0]
    return first_game


def create_new_comment(first_comment, second_comment):
    """
    merge two comments into one new comment
    if one is part of the other, only the string that is the greatest is returned
    :param first_comment:
    :param second_comment:
    :return: a new comment
    """
    # clean up comments to be able to compare them
    comment_second = " ".join(second_comment.split()).lower().strip()
    comment_first = " ".join(first_comment.split()).lower().strip()
    if comment_first in comment_second:
        first_comment = second_comment
    elif comment_second in comment_first:
        pass
    else:
        first_comment = second_comment + " " + first_comment
    return first_comment
