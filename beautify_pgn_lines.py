class BeautifyPgnLines:
    def __init__(self, line_len = 69):
        self.line_len = line_len

    def execute(self, string):
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
    def get_line_number(self, next_move, pgn_lines):
        part_text = self.execute(str(next_move))
        line_number = -1
        # see if line number can be retrieved by comparing the first part of the partial moves
        part_found = False
        if len(part_text) > 0:
            part_top_line = part_text[0]
            parts = part_top_line.split(" ")
            is_black = False
            black_search = "rubbish"
            # if line is starting with ... (black move), remove this first part
            if len(parts) > 0 and parts[0].endswith("..."):
                black_search = parts[0] + " " + parts[1]
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

                if line.startswith(black_search) or parts_end and line.endswith(line_to_search) or not parts_end and line_to_search in line_plus_1:
                    part_found = True
                    number = i
                    times = times + 1
                    if line.startswith(black_search):
                        break
                i = i + 1
            # if there is one hit, this line is used for the line_number
            # > 1: ambiguous->use the last one; the first occurrence must be an analysis?
            if times > 0:
                line_number = number
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


