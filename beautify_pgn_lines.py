import chess

HARD_SPACE = u"\u00A0"


class PgnDisplay:
    def __init__(self, line_len = 69):
        self.line_len = line_len

    def beautify_lines(self, string):
        """
            set_vscroll_position(
        percent_from_top
    )
            """
        lines = string.split("\n")
        lines = [l for l in lines if not (l.startswith("[") and l.endswith('"]'))]
        string = "\n".join(lines)
        string = list(string)
        indent = 0
        inside_comment = False
        for index, item in enumerate(string):

            if item == "\n":
                if not inside_comment:
                    string[index] = "\n" + ("_" * indent)
                else:
                    string[index] = " "
            if item == "(" and not inside_comment:
                indent = indent + 1
                string[index] = "\n" + ("_" * indent)
            if item == "{":
                indent = indent + 1
                string[index] = "\n" + ("|" * indent)
                inside_comment = True
            if item == ")" and not inside_comment:
                indent = indent - 1
                string[index] = "\n" + ("_" * indent)
            if item == "}":
                indent = indent - 1
                string[index] = "\n" + ("_" * indent)
                inside_comment = False
        lines = "".join(string).split("\n")
        lines = [self.split_line(l).replace("_", " ") for l in lines if
                 len(l.replace("_", "").strip()) > 0 and not l.startswith("[")]
        lines = [self.change_nag(line) for line in lines]
        lines = "\n".join(lines).split("\n")
        return lines

    def color_lines(self, move_list, move_list_gui_element):
        for index in range(0, len(move_list)):
            fg = 'black'  # default color
            if HARD_SPACE in move_list[index]:  # comment
                fg = '#a91d3a'
            elif move_list[index].startswith(" "):  # alternative line
                fg = "#226622"  # dark-grey
            move_list_gui_element.Widget.itemconfig(index, fg=fg)


    def split_line(self, line):
        comment_line = "|" in line
        line = line.replace("|", "_")
        comment_char = HARD_SPACE if comment_line else ""
        max_len_line = self.line_len
        line = line.strip().replace("_ ", "_")
        if len(line) <= max_len_line:
            return line + comment_char
        line = line.replace(".  ", ".H")
        words = line.split(" ")
        prefix_number = words[0].count("_")
        len_line = len(words[0])
        line = words[0]
        words.pop(0)
        for word in words:
            if len_line + len(word) > max_len_line:
                line = line + comment_char + "\n" + ("_" * prefix_number)
                len_line = len(word)
            else:
                len_line = len_line + 1
                line = line + " "
            len_line = len_line + len(word)
            line = line + word
        line = line.replace(".H", ".  ") + comment_char
        return line

    def change_nag(self, line):
            nags = {"1":"!", "2":"?","3":"!!","4":"??","5":"!?","6":"?!", "9":".."}
            if "$" in line:
                for i in range(0, 10):
                    line = line.replace("$"+str(i), "")
                    for k in nags:
                        key = "$"+k
                        line = line.replace(key, nags[k])
                return line

            else:
                return line

    def is_comment_line(self, line):
        for gone in ["!", "!?", "??", "!!", "?", "?!", "+", "#"]:
            line = line.replace(gone, "")
        # get all words
        words = [l for l in line.split(" ") if sum(c.isdigit() for c in line) == 0]
        return len(words) > 0 or HARD_SPACE in line

    def get_line_number(self, next_move, pgn_lines, board):
        part_text = self.beautify_lines(str(next_move))
        endswith_enter = len(next_move.comment) > 0
        line_number = -1
        # see if line number can be retrieved by comparing the first part of the partial moves
        part_found = False
        if len(part_text) > 0:
            part_top_line = part_text[0]
            parts = part_top_line.split(" ")
            white_move = "rubbish"
            new_variation = False
            start_move = "rubbish"
            is_black = next_move.turn() == chess.WHITE
            parent = next_move.parent
            if parent is not None:
                new_variation = not str(parent.variations[0].move) == str(next_move.move) or len(parent.comment) > 0 \
                                or str(parent.variations[0].move) == str(next_move.move) and len(parent.variations) > 1
                if new_variation and len(parts) > 1:
                    # move is start-move of new variation/line
                    start_move = parts[0] + " " + parts[1]
                    if is_black and len(next_move.variations) == 1 and len(next_move.comment) == 0 \
                            and not len(parent.variations) > 1:
                        # add the white-move after this black-move, to make it more specific
                        start_move += " " + " ".join(str(next_move.variations[0]).split(" ")[:2])
                    # print("start-move:", start_move)

            black_move_with_white_before = "rubbish"
            # if line is starting with ... (black move), remove this first part
            if is_black and not new_variation and len(parts) > 1:
                # black_move_with_white_before has the black move preceded by the white move
                # it is a black move, so there has to be a parent. No checking for parent-existence is needed
                white_before_move = " ".join(str(parent).split(" ")[:2])
                # black_move_with_white_before contains move-number and algebraic notation for white and black
                black_move_with_white_before = white_before_move + " " + parts[1]
                # print("black_move_with_white_before",black_move_with_white_before)
                parts = parts[1:]

            parts_end = len(parts) == 1
            if len(parts) > 1:
                # white_move contains move-number and algebraic notation
                white_move = " ".join(str(next_move).split(" ")[:2])
            # create the significant first line of the partial moves
            line_to_search = " ".join(parts).strip()
            if is_black:
                line_to_search = " " + line_to_search
            #print("search line:"+line_to_search+":", is_black, parts_end)
            # loop through the pgn_lines to see if there is exactly one line that contains it
            numbers=[]
            i = 0
            times = 0
            for line in pgn_lines:
                if (line.startswith(" ") and next_move.is_mainline()  # annotation-line and mainline-move
                        # not annotation-line and annotation-move
                        or not line.startswith(" ") and not next_move.is_mainline()) or self.is_comment_line(line):
                    i = i + 1
                    continue
                line_plus_1 = line

                if i + 1 < len(pgn_lines):
                    st_sp_1 = self.start_spaces(line)
                    second_line = pgn_lines[i + 1]
                    st_sp_2 = self.start_spaces(second_line)
                    if st_sp_1 == st_sp_2:
                        line_plus_1 = line.strip() + " " + second_line.strip()

                if (#line.strip().startswith(black_search) or
                        # start move of new variation
                        new_variation and line.strip().startswith(start_move)
                        or parts_end and line.endswith(line_to_search) or
                        not parts_end and line_to_search in line_plus_1):
                    part_found = True
                    number = i
                    numbers.append(number)
                    times = times + 1
                    if (#line.startswith(black_search) or
                            not endswith_enter and black_move_with_white_before in line
                            or endswith_enter and line.endswith(black_move_with_white_before) or
                            not endswith_enter and white_move in line or endswith_enter and line.endswith(white_move)):
                        numbers=[i]
                        break
                i = i + 1
            # if there is one hit, this line is used for the line_number
            # > 1: ambiguous->use the first one; the second occurrence must be an annotation?
            if times > 0:
                line_number = numbers[0]
            else:
                part_found = False
        return line_number, part_found

    def start_spaces(self, line):
        if len(line.strip()) == 0:
            return 0
        i = 0
        while line[i] == " ":
            i = i + 1
        return i

    def get_variations(self, node, all_variations, in_variation = False):
        variations = [v for v in node.variations]
        last_variation = []
        if len(all_variations) > 0:
            last_variation = all_variations[-1]
        if len(variations) > 0:
            if in_variation:
                last_variation.append(variations[0])
                self.get_variations(variations[0], all_variations, True)
            variations.pop(0)
            for variation in variations:
                all_variations.append([variation])
                # print("add variation", variation.move)
                self.get_variations(variation, all_variations, True)
        else:
            if in_variation:
                last_variation.append(node)

    def get_nodes(self, parts, nodes):
        algebraics = {}
        for node in nodes:
            s = str(node).split(" ")[1].replace("+", "")
            algebraics[node] = s
        # for node in algebraics:
        #     print(algebraics[node])
        res = []
        first_is_black = "..." in parts[0]
        move_num_exists = False
        for elem in parts:
            try:
                move_number = int(elem.replace(".", ""))
                move_num_exists = True
            except:
                pass
        if not move_num_exists:
            # no move numbers available. Do a guess based on the move-descriptions themselves
            for node in nodes:
                if algebraics[node] in parts:
                    res.append(node)
            return res

        num = 0
        for elem in parts:
            # only check first move if it starts with 34...
            if num > 1:
                # rest of the moves can be white and black
                first_is_black = False
            try:
                move_number = int(elem.replace(".", ""))
                # print("lastblack", last_black,num,len(parts))
                for node in nodes:
                    if algebraics[node] in parts:
                        # print(algebraics[node], node.ply(), 2*move_number-1, 2*move_number)
                        if node.ply() in [2 * move_number - 1, 2 * move_number] and algebraics[node] in parts:
                            if node.turn() == chess.BLACK and first_is_black:
                                # white move, and the starting move for this line is a black move
                                continue
                            if node.turn() == chess.WHITE and len(res) >= len(parts) / 2:
                                # it is a black move, and is not printed on this line
                                continue
                            # print("node added:", node.move, move_number, node.ply())
                            res.append(node)
            except:
                pass
            num += 1
        return res

    def get_position_move_from_pgn_line(self, game, item):
        found_nodes = []
        for gone in ["!", "!?", "?", "?!", "+", "#"]:
            item = item.replace(gone, "")
        #print("check for:", item)
        if not (game is None or HARD_SPACE in item):
            parts = [p for p in item.split(" ") if len(p) > 0]
            #print("get nodes")
            if item.startswith(" "):
                #print("variation")
                all_variations = []
                node = game.game()

                while len(node.variations) > 0:
                    self.get_variations(node, all_variations)
                    node = node.variations[0]
                max_found = 0
                found_variation = []
                for variation in all_variations:
                    nodes = self.get_nodes(parts, variation)
                    if len(nodes) > max_found:
                        max_found = len(nodes)
                        found_variation = nodes
                found_nodes = found_variation
                if len(found_nodes) > 0:
                    found_nodes = [found_nodes[0]]
            else:
                # get all items from mainline
                node = game.game()
                nodes_main_line = [node]
                while len(node.variations) > 0:
                    node = node.variations[0]
                    nodes_main_line.append(node)
                found_nodes = self.get_nodes(parts, nodes_main_line)
                if len(found_nodes) > 0:
                    found_nodes = [found_nodes[-1]]

        items = item.split(" ")
        # if line starts with a " ", it is a comment or a variation
        is_variation = item.startswith(" ")
        if not is_variation:
            items.reverse()
        new_pos = -1
        for move in items:
            is_black = "..." in move
            var = move.replace(".", "")
            try:
                # try converting to integer
                val = int(var)
                if is_variation:
                    # go to previous move to allow for selection of the variation
                    val = max(0, val - 1)
                # the new position is per default at the start (white-move)
                new_pos = val * 2
                if is_variation or not is_variation and is_black:
                    # move move-cursor one up, because the move-number itself is even (val * 2)
                    new_pos = new_pos + 1

                break

            except ValueError:
                pass
        return found_nodes, new_pos

    def get_move_string(self, move):
        move_string = str(move)
        if move_string.startswith("{"):
            l1 = move_string.split("}")
            l1.pop(0)
            move_string = "}".join(l1).strip()

        move_item = move_string.split(" ")[:2]
        return " ".join(move_item)

    def get_nice_move_string(self, next_move):
        move_string = self.get_move_string(next_move)
        alternatives = ""
        if len(next_move.variations) > 1:
            alternatives = [self.get_move_string(item) for item in next_move.variations]
            # get next move-number; display it only once at start of alternatives
            first = alternatives[0].split(" ")[0]
            alternatives = "({}->{})".format(first, ",".join([item.replace(first, "") for item in alternatives]))
        return alternatives, move_string




