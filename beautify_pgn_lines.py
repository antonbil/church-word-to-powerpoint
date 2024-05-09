class PgnDisplay:
    def __init__(self, line_len = 69):
        self.line_len = line_len

    def beautify_lines(self, string):
        """
            set_vscroll_position(
        percent_from_top
    )
            """
        string = list(string)
        indent = 0
        inside_comment = False
        for index, item in enumerate(string):

            if item == "(" and not inside_comment:
                indent = indent + 1
                string[index] = "\n" + ("_" * indent)
            if item == "{":
                indent = indent + 1
                string[index] = "\n" + ("_" * indent)
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

    def split_line(self, line):
        max_len_line = self.line_len
        line = line.strip().replace("_ ", "_")
        if len(line) <= max_len_line:
            return line
        line = line.replace(".  ", ".H")
        words = line.split(" ")
        prefix_number = words[0].count("_")
        len_line = len(words[0])
        line = words[0]
        words.pop(0)
        for word in words:
            if len_line + len(word) > max_len_line:
                line = line + "\n" + ("_" * prefix_number)
                len_line = len(word)
            else:
                len_line = len_line + 1
                line = line + " "
            len_line = len_line + len(word)
            line = line + word
        line = line.replace(".H", ".  ")
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

    def get_line_number(self, next_move, pgn_lines, board):
        part_text = self.beautify_lines(str(next_move))
        line_number = -1
        # see if line number can be retrieved by comparing the first part of the partial moves
        part_found = False
        if len(part_text) > 0:
            part_top_line = part_text[0]
            parts = part_top_line.split(" ")
            is_black = False
            black_search = "rubbish"
            black_move_with_white_before = "rubbish"
            # if line is starting with ... (black move), remove this first part
            if len(parts) > 0 and parts[0].endswith("..."):
                black_search = parts[0] + " " + parts[1]
                # black_move_with_white_before has the black move preceded by the white move
                # it is a black move, so there has to be a parent. No checking for parent-existence is needed
                white_move = " ".join(str(next_move.parent).split(" ")[:2])
                black_move_with_white_before = white_move + " " + parts[1]
                # print("black_search",black_search2)
                parts = parts[1:]
                is_black = True
            parts_end = len(parts) == 1
            # create the significant first line of the partial moves
            line_to_search = " ".join(parts).strip()
            if is_black:
                line_to_search = " " + line_to_search
            #print("search line:"+line_to_search+":", is_black, parts_end)
            # loop through the pgn_lines to see if there is exactly one line that contains it
            number = -1
            numbers=[]
            i = 0
            times = 0
            for line in pgn_lines:
                line_plus_1 = line

                if i + 1 < len(pgn_lines):
                    st_sp_1 = self.start_spaces(line)
                    second_line = pgn_lines[i + 1]
                    st_sp_2 = self.start_spaces(second_line)
                    if st_sp_1 == st_sp_2:
                        line_plus_1 = line.strip() + " " + second_line.strip()

                if (line.startswith(black_search) or parts_end and line.endswith(line_to_search) or
                            black_move_with_white_before in line or line_to_search in line):
                    part_found = True
                    number = i
                elif not parts_end and line_to_search in line_plus_1 :
                    number = i + 1
                    part_found = True
                if part_found:
                    numbers.append(number)
                    times = times + 1
                    if line.startswith(black_search) or black_move_with_white_before in line:
                        numbers = [i]
                        break
                i = i + 1
            # if there is one hit, this line is used for the line_number
            # > 1: ambiguous->use the last one; the first occurrence must be an analysis?
            if times > 0:
                line_number = numbers[0]
            else:
                part_found = False
        return (line_number, part_found)

    def start_spaces(self, line):
        if len(line.strip()) == 0:
            return 0
        i = 0
        while line[i] == " ":
            i = i + 1
        return i

    def get_position_move_from_pgn_line(self, item):
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
        return new_pos

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




