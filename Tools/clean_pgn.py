import argparse
# example call: python3 /home/user/Schaken/stockfish-python/Python-Easy-Chess-GUI/Tools/clean_pgn.py --file /home/user/Schaken/nep-ding.pgn
def parse_args():
    """
    Define an argument parser and return the parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='clean_pgn',
        description='takes chess games in a PGN file and cleans it')
    parser.add_argument("--file", "-f",
                        help="input PGN file",
                        required=True,
                        metavar="FILE.pgn")

    return parser.parse_args()


def main():
    """
    Main function

    - Load games from the PGN file
    - Annotate each game, and print the game with the annotations
    """
    args = parse_args()

    pgnfile = args.file
    try:
        res = ""
        with (open(pgnfile) as pgn):
            data = pgn.read()
            res = get_cleaned_string_pgn(data)
        print(res)
        text_file = open(pgnfile, "w")
        text_file.write(res)
        text_file.close()


    except PermissionError:
        errormsg = "Input file not readable. Aborting..."


def get_cleaned_string_pgn(data):
    splits = data.split('[%c_effect')
    lines = [splits.pop(0)]
    for line in splits:
        line1 = line.split(';true]')
        lines.append(line1[1])
    res = " ".join(lines)
    """
            {[%evp }"""
    fp = '{'
    sp = '}'
    # [%cal
    res = replace_remove(res, '[%c_arrow', ']')
    res = replace_remove(res, '{[%evp', ']}')
    res = replace_between(res, fp, sp)
    res = res.replace('{ }', '').replace('{  ', '{').replace('  ', ' ').replace('\n\n', '\n').replace('\n\n', '\n')
    return res


def replace_between(res, fp, sp):
    splits = res.split(fp)
    lines = [splits.pop(0)]
    for line in splits:
        line1 = line.split(sp)
        first = line1.pop(0)
        if len(line1) > 1:
            second = " ".join(line1)
        elif len(line1) == 1:
            second = line1[0]
        else:
            second = ""
        first = first.replace("\n", " ")
        line1 = first + sp + second
        lines.append(line1)
    res = fp.join(lines)
    return res

def replace_remove(res, fp, sp):
    splits = res.split(fp)
    lines = [splits.pop(0)]
    for line in splits:
        line1 = line.split(sp)
        first = line1.pop(0)
        if len(line1) > 1:
            second = " ".join(line1)
        elif len(line1) == 1:
            second = line1[0]
        else:
            second = ""
        first = first.replace("\n", " ")
        line1 = second
        lines.append(line1)
    res = " ".join(lines)
    return res


if __name__ == "__main__":
    main()