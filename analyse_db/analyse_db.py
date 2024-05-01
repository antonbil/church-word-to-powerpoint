from os import listdir
from os.path import isfile, join
import argparse
import chess
import chess.pgn

class AnalyseDb:
    """header dialog class"""
    def __init__(self, path):
        # used for search
        self.dates = None
        self.events = None
        self.openings = None
        self.players = None
        self.num_games = None

        self.path = path
        self.name_file = join(self.path, "tempsave.pgn")

    def search(self, player="", opening="", event="", date=''):
        self.num_games = 0
        self.players = [p.strip() for p in player.split(",") if len(p.strip()) > 0]
        self.openings = [p.strip() for p in opening.split(",") if len(p.strip()) > 0]
        self.events = [p.strip() for p in event.split(",") if len(p.strip()) > 0]
        self.dates = [p.strip() for p in date.split(",") if len(p.strip()) > 0]
        #print("players",players)
        with open(self.name_file, mode='w') as f:
            f.write('\n\n')


        onlyfiles = [f for f in listdir(self.path) if isfile(join(self.path, f)) and f.lower().endswith((".pgn"))]
        for file in onlyfiles:
            path = join(self.path, file)

            self.do_action_with_pgn_db(path, self.action)
        return self.num_games

    def check_elements(self, elements_tosearch, element_in, do_print):
        if not do_print:
            return False
        if len(elements_tosearch) > 0 and not element_in:
            do_print = False
        if len(elements_tosearch) > 0 and element_in:
            do_print = False
            for element in elements_tosearch:
                if element in element_in:
                    do_print = True
        return do_print

    def action(self, games_index, game1):
        player_white = game1.headers['White'].lower() if 'White' in game1.headers else None
        player_black = game1.headers['Black'].lower() if 'Black' in game1.headers else None
        opening_game = game1.headers['Opening'].lower() if 'Opening' in game1.headers else None
        event_game = game1.headers['Event'].lower() if 'Event' in game1.headers else None
        date_game = game1.headers['Date'].lower() if 'Date' in game1.headers else None
        do_print = True
        do_print = self.check_elements(self.openings, opening_game, do_print)
        do_print = self.check_elements(self.dates, date_game, do_print)
        do_print = self.check_elements(self.events, event_game, do_print)
        do_print = self.check_elements(self.players, player_white+player_black, do_print)

        if do_print:
            self.num_games = self.num_games + 1
            #print("game1", game1.headers['White'], game1.headers['Black'], opening_game)
            with open(self.name_file, 'a') as f:
                f.write('{}\n\n'.format(game1))

    def do_action_with_pgn_db(self, path, action):

        pgn, game1 = self.read_game(path, None)
        games_index = 0
        while game1:
            # if index == games_index:
            #     game1 = self.game
            # with open(old_file, 'a') as f:
            #         f.write('{}\n\n'.format(game1))
            action(games_index, game1)
            pgn, game1 = self.read_game(path, pgn)
            games_index = games_index + 1

    def read_game(self, path, pgn):
        #
        if not pgn:
            pgn = open(path)
            #print("Reading game", path)
        try:
            game1 = chess.pgn.read_game(pgn)
        except:
            game1 = None
        return pgn, game1



def parse_args():
    """
    Define an argument parser and return the parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='analyse db',
        description='analyses all pgn files in a given directory '
        'and stores result in a file')
    parser.add_argument("--dir", "-d",
                        help="directory where pgn-files are stored",
                        required=True,
                        default=".")
    parser.add_argument("--player", "-p",
                        help="players to be searched",
                        default="")
    parser.add_argument("--opening", "-o",
                        help="opening to be searched",
                        default="")
    parser.add_argument("--verbose", "-v", help="increase verbosity",
                        action="count")

    return parser.parse_args()



def main():
    """
    Main function

    - Load games from the PGN file
    - Annotate each game, and print the game with the annotations
    """
    args = parse_args()
    path = args.dir
    db_analyse = AnalyseDb(path)
    num_games = db_analyse.search(player=args.player, opening=args.opening)
    print("{} games found".format(num_games))


if __name__ == "__main__":
    main()