class BeautifyPgnLines:
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
        max_len_line = 69
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

