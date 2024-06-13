#!/usr/bin/env python3
"""
python_swan_chess.py

Requirements:
    Python 3.7.3 and up

PySimpleGUI Square Mapping
board = [
    56, 57, ... 63
    ...
    8, 9, ...
    0, 1, 2, ...
]

row = [
    0, 0, ...
    1, 1, ...
    ...
    7, 7 ...
]

col = [
    0, 1, 2, ... 7
    0, 1, 2, ...
    ...
    0, 1, 2, ... 7
]


Python-Chess Square Mapping
board is the same as in PySimpleGUI
row is reversed
col is the same as in PySimpleGUI

"""

import PIL
from PIL import Image
import io
import PySimpleGUI as sg
import os
import sys
import subprocess
import threading
from pathlib import Path, PurePath  # Python 3.4 and up
import queue
import copy
import time
import argparse
from datetime import datetime
import json
import pyperclip
import chess
import chess.pgn
import chess.engine
import chess.polyglot
import logging
import platform as sys_plat
from annotator import annotator
from board import (ChessBoard, convert_to_bytes)
from dialogs.header_dialog import HeaderDialog
from pgn_viewer.pgn_viewer import PGNViewer
from pgn_editor.pgn_editor import PgnEditor
from preferences.preferences import Preferences
from common import (menu_def_pgnviewer, menu_def_entry, temp_file_name, MAX_ALTERNATIVES, APP_NAME, APP_VERSION,
                    BOX_TITLE, ico_path, menu_def_play, get_button_id, menu_def_neutral, board_colors)
from Tools.translations import  get_translation, set_language, GUI_THEME
from toolbar import ToolBar
from dialogs.input_actions import InputDialog

log_format = '%(asctime)s :: %(funcName)s :: line: %(lineno)d :: %(levelname)s :: %(message)s'
logging.basicConfig(
    filename='pecg_log.txt',
    filemode='w',
    level=logging.ERROR,
    format=log_format
)

MAX_ADVISER_DEPTH = 50

platform = sys.platform
sys_os = sys_plat.system()

MIN_DEPTH = 1
MAX_DEPTH = 1000
MANAGED_UCI_OPTIONS = ['ponder', 'uci_chess960', 'multipv', 'uci_analysemode', 'ownbook']


BLANK = 0  # piece names

# Absolute rank based on real chess board, white at bottom, black at the top.
# This is also the rank mapping used by python-chess modules.
RANK_8 = 7
RANK_7 = 6
RANK_6 = 5
RANK_5 = 4
RANK_4 = 3
RANK_3 = 2
RANK_2 = 1
RANK_1 = 0

HELP_MSG = """The GUI has 4 modes, Play and Neutral, Pgn-viewer and Pgn-editor. 
By default you are in Neutral mode, but you can select another startup-mode 
using the startmode in the command-line-options.

This part of the help-menu describes the Play, and Neutral mode.
You can go from mode Neutral to mode Play through Mode menu.

All games are auto-saved in pecg_auto_save_games.pgn.
Visit Game menu in Play mode to see other options to save the game.

It has to be noted you need to setup an engine to make the GUI works.
You can view which engines are ready for use via:
Engine->Set Engine Opponent.

(A) To setup an engine, you should be in Neutral mode.
1. Engine->Manage->Install, press the add button.
2. After engine setup, you can configure the engine options with:
  a. Engine->Manage-Edit
  b. Select the engine you want to edit and press Modify.

Before playing a game, you should select an engine opponent via
Engine->Set Engine Opponent.

You can also set an engine Adviser in the Engine menu.
During a game you can ask help from Adviser by right-clicking
the Adviser label and press show.

(B) To play a game
You should be in Play mode.
1. Mode->Play
2. Make move on the board

(C) To play as black
You should be in Neutral mode
1. Board->Flip
2. Mode->Play
3. Engine->Go
If you are already in Play mode, go back to
Neutral mode via Mode->Neutral

(D) To flip board
You should be in Neutral mode
1. Board->Flip

(E) To paste FEN
You should be in Play mode
1. Mode->Play
2. FEN->Paste

(F) To show engine search info after the move
1. Right-click on the Opponent Search Info and press Show

(G) To Show book 1 and 2
1. Right-click on Book 1 or 2 press Show

(H) To change board color
1. You should be in Neutral mode.
2. Board->Color.

(I) To change board theme
1. You should be in Neutral mode.
2. Board->Theme.
"""


INIT_PGN_TAG = {
    'Event': 'Human vs computer',
    'White': 'Human',
    'Black': 'Computer'
}

#


# (1) Mode: Neutral

# (2) Mode: Play, info: hide


class Timer:
    def __init__(self, tc_type: str = 'fischer', base: int = 300000, inc: int = 10000, period_moves: int = 40) -> None:
        """Manages time control.

        Args:
          tc_type: time control type ['fischer, delay, classical']
          base: base time in ms
          inc: increment time in ms can be negative and 0
          period_moves: number of moves in a period
        """
        self.tc_type = tc_type  # ['fischer', 'delay', 'timepermove']
        self.base = base
        self.inc = inc
        self.period_moves = period_moves
        self.elapse = 0
        self.init_base_time = self.base

    def update_base(self) -> None:
        """Updates base time after every move."""
        if self.tc_type == 'delay':
            self.base += min(0, self.inc - self.elapse)
        elif self.tc_type == 'fischer':
            self.base += self.inc - self.elapse
        elif self.tc_type == 'timepermove':
            self.base = self.init_base_time
        else:
            self.base -= self.elapse

        self.base = max(0, self.base)
        self.elapse = 0


class GuiBook:
    def __init__(self, book_file: str, board, is_random: bool = True) -> None:
        """Handles gui polyglot book for engine opponent.

        Args:
          book_file: polgylot book filename
          board: given board position
          is_random: randomly select move from book
        """
        self.book_file = book_file
        self.board = board
        self.is_random = is_random
        self.__book_move = None

    def get_book_move(self) -> None:
        """Gets book move either random or best move."""
        reader = chess.polyglot.open_reader(self.book_file)
        try:
            if self.is_random:
                entry = reader.weighted_choice(self.board)
            else:
                entry = reader.find(self.board)
            self.__book_move = entry.move
        except IndexError:
            logging.warning('No more book move.')
        except Exception:
            logging.exception('Failed to get book move.')
        finally:
            reader.close()

        return self.__book_move

    def get_all_moves(self):
        """
        Read polyglot book and get all legal moves from a given positions.

        :return: move string
        """
        is_found = False
        total_score = 0
        book_data = {}
        cnt = 0

        if os.path.isfile(self.book_file):
            moves = '{:4s}   {:<5s}   {}\n'.format('move', 'score', 'weight')
            with chess.polyglot.open_reader(self.book_file) as reader:
                for entry in reader.find_all(self.board):
                    is_found = True
                    san_move = self.board.san(entry.move)
                    score = entry.weight
                    total_score += score
                    bd = {cnt: {'move': san_move, 'score': score}}
                    book_data.update(bd)
                    cnt += 1
        else:
            moves = '{:4s}  {:<}\n'.format('move', 'score')

        # Get weight for each move
        if is_found:
            for _, v in book_data.items():
                move = v['move']
                score = v['score']
                weight = score / total_score
                moves += '{:4s}   {:<5d}   {:<2.1f}%\n'.format(move, score, 100 * weight)

        return moves, is_found


class RunEngine(threading.Thread):
    pv_length = 9
    move_delay_sec = 3.0

    def __init__(self, eng_queue, engine_config_file, engine_path_and_file,
                 engine_id_name, max_depth=MAX_DEPTH,
                 base_ms=300000, inc_ms=1000, tc_type='fischer',
                 period_moves=0, is_stream_search_info=True, is_computer_move=False,
                 skill_level=1, use_skill = True):
        """
        Run engine as opponent or as adviser.

        :param eng_queue:
        :param engine_config_file: pecg_engines.json
        :param engine_path_and_file:
        :param engine_id_name:
        :param max_depth:
        """
        threading.Thread.__init__(self)
        self.pv_original = []
        self._kill = threading.Event()
        self.engine_config_file = engine_config_file
        self.engine_path_and_file = engine_path_and_file
        self.engine_id_name = engine_id_name
        self.own_book = False
        self.bm = None
        self.pv = None
        self.score = None
        self.depth = None
        self.time = None
        self.nps = 0
        self.max_depth = max_depth
        self.eng_queue = eng_queue
        self.engine = None
        self.board = None
        self.analysis = is_stream_search_info
        self.is_nomove_number_in_variation = True
        self.base_ms = base_ms
        self.inc_ms = inc_ms
        self.tc_type = tc_type
        self.period_moves = period_moves
        self.is_ownbook = False
        self.is_move_delay = True
        self.is_computer_move = is_computer_move
        self.skill_level = skill_level
        self.use_skill = use_skill


    def stop(self):
        """Interrupt engine search."""
        self._kill.set()

    def get_board(self, board):
        """Get the current board position."""
        self.board = board

    def configure_engine(self):
        """Configures the engine internal settings.
         
        Read the engine config file pecg_engines.json and set the engine to
        use the user_value of the value key. Our option name has 2 values,
        default_value and user_value.

        Example for hash option
        'name': Hash
        'default': default_value
        'value': user_value

        If default_value and user_value are not the same, we will set the
        engine to use the user_value by the command,
        setoption name Hash value user_value

        However if default_value and user_value are the same, we will not send
        commands to set the option value because the value is default already.
        """
        #print("try to open", self.engine_config_file)
        with open(self.engine_config_file, 'r') as json_file:
            #print("opened",self.engine_config_file)
            data = json.load(json_file)
            for p in data:
                if p['name'] == self.engine_id_name:
                    for n in p['options']:

                        if n['name'].lower() == 'ownbook':
                            self.is_ownbook = True

                        # Ignore button type for a moment.
                        if n['type'] == 'button':
                            continue

                        if n['type'] == 'spin':
                            user_value = int(n['value'])
                            user_value = self.set_skill_option(n, user_value)
                            default_value = int(n['default'])
                        else:
                            user_value = n['value']
                            user_value = self.set_skill_option(n, user_value)
                            default_value = n['default']
                        # print("option", n['name'], user_value, default_value)

                        if user_value != default_value:
                            try:
                                self.engine.configure({n['name']: user_value})
                                logging.info('Set ' + n['name'] + ' to ' + str(user_value))
                            except Exception:
                                logging.exception('Failed to configure engine.')

    def set_skill_option(self, n, user_value):
        """
        set skill-level for engine
        experimental code; only working right now for StockFish, Deuterium and  Dragon
        StockFish and Deuterium have the "uci_limitstrength" and "uci_elo" properties
        Dragon only has the "skill"-property
        :param n:
        :param user_value:
        :return:
        """
        if not self.use_skill:
            return user_value
        skill_options = [{"skill Level":2,#level 1
                          "skill":2,
                          "uci_limitstrength":True,
                          "uci_elo":800},
                         {"skill Level": 5,#level 2
                          "skill": 5,
                          "uci_limitstrength": True,
                          "uci_elo": 1100},
                         {"skill Level": 8,#level 3
                          "skill": 10,
                          "uci_limitstrength": True,
                          "uci_elo": 1400},
                         {"skill Level": 12,#level 4
                          "skill": 15,
                          "uci_limitstrength": True,
                          "uci_elo": 1700},
                         {"skill Level": 16,#level 5
                          "skill": 20,
                          "uci_limitstrength": True,
                          "uci_elo": 2000},
                         {"skill Level": 20,#level 6
                          "skill": 25,
                          "uci_limitstrength": True,
                          "uci_elo": 2500}
                         ]

        for option in skill_options[self.skill_level - 1]:
            if n['name'].lower() == option:
                user_value = skill_options[self.skill_level - 1][option]

        return user_value

    def run(self):
        """Run engine to get search info and bestmove.
         
        If there is error we still send bestmove None.
        """
        folder = Path(self.engine_path_and_file)
        folder = folder.parents[0]

        try:
            if sys_os == 'Windows':
                self.engine = chess.engine.SimpleEngine.popen_uci(
                    self.engine_path_and_file, cwd=folder,
                    creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                self.engine = chess.engine.SimpleEngine.popen_uci(
                    self.engine_path_and_file, cwd=folder)
        except chess.engine.EngineTerminatedError:
            logging.warning('Failed to start {}.'.format(self.engine_path_and_file))
            self.eng_queue.put('bestmove {}'.format(self.bm))
            return
        except Exception:
            logging.exception('Failed to start {}.'.format(
                self.engine_path_and_file))
            self.eng_queue.put('bestmove {}'.format(self.bm))
            return

        # Set engine option values
        try:
            #print("configure engine")
            self.configure_engine()
        except e as Exception:
            print(e)
            logging.exception('Failed to configure engine.')

        # Set search limits
        if self.is_computer_move:
            limit = self.get_computer_limit()
        elif self.tc_type == 'delay':
            limit = chess.engine.Limit(
                depth=self.max_depth if self.max_depth != MAX_DEPTH else None,
                white_clock=self.base_ms / 1000,
                black_clock=self.base_ms / 1000,
                white_inc=self.inc_ms / 1000,
                black_inc=self.inc_ms / 1000)
        elif self.tc_type == 'timepermove':
            limit = chess.engine.Limit(time=self.base_ms / 1000,
                                       depth=self.max_depth if
                                       self.max_depth != MAX_DEPTH else None)
        else:
            limit = chess.engine.Limit(
                depth=self.max_depth if self.max_depth != MAX_DEPTH else None,
                white_clock=self.base_ms / 1000,
                black_clock=self.base_ms / 1000,
                white_inc=self.inc_ms / 1000,
                black_inc=self.inc_ms / 1000)
        start_time = time.perf_counter()
        if self.analysis:
            is_time_check = False

            with self.engine.analysis(self.board, limit) as analysis:
                for info in analysis:

                    if self._kill.wait(0.1):
                        break

                    try:
                        if 'depth' in info:
                            self.depth = int(info['depth'])

                        if 'score' in info:
                            self.score = int(info['score'].relative.score(mate_score=32000)) / 100

                        self.time = info['time'] if 'time' in info else time.perf_counter() - start_time

                        if 'pv' in info and not ('upperbound' in info or
                                                 'lowerbound' in info):
                            self.pv = info['pv'][0:self.pv_length]

                            if self.is_nomove_number_in_variation:
                                spv = self.short_variation_san()
                                self.pv = spv
                            else:
                                self.pv_original = self.get_pv_original()
                                self.pv = self.board.variation_san(self.pv)

                            self.eng_queue.put('{} pv'.format(self.pv))
                            self.bm = info['pv'][0]

                        # score, depth, time, pv
                        if self.score is not None and \
                                self.pv is not None and self.depth is not None:
                            info_to_send = '{:+5.2f} | {} | {:0.1f}s | {} info_all'.format(
                                self.score, self.depth, self.time, self.pv)
                            self.eng_queue.put('{}'.format(info_to_send))

                        # Send stop if movetime is exceeded
                        if not is_time_check and self.tc_type != 'fischer' \
                                and self.tc_type != 'delay' and \
                                time.perf_counter() - start_time >= \
                                self.base_ms / 1000:
                            logging.info('Max time limit is reached.')
                            is_time_check = True
                            break

                        # Send stop if max depth is exceeded
                        if 'depth' in info:
                            if int(info['depth']) >= self.max_depth \
                                    and self.max_depth != MAX_DEPTH:
                                logging.info('Max depth limit is reached.')
                                break
                    except Exception:
                        logging.exception('Failed to parse search info.')
        else:
            result = self.engine.play(self.board, limit, info=chess.engine.INFO_ALL)
            logging.info('result: {}'.format(result))
            try:
                self.depth = result.info['depth']
            except KeyError:
                self.depth = 1
                logging.exception('depth is missing.')
            try:
                self.score = int(result.info['score'].relative.score(
                    mate_score=32000)) / 100
            except KeyError:
                self.score = 0
                logging.exception('score is missing.')
            try:
                self.time = result.info['time'] if 'time' in result.info \
                    else time.perf_counter() - start_time
            except KeyError:
                self.time = 0
                logging.exception('time is missing.')
            try:
                if 'pv' in result.info:
                    self.pv = result.info['pv'][0:self.pv_length]

                if self.is_nomove_number_in_variation:
                    spv = self.short_variation_san()
                    self.pv = spv
                else:
                    self.pv_original = self.get_pv_original()
                    self.pv = self.board.variation_san(self.pv)
            except Exception:
                self.pv = None
                logging.exception('pv is missing.')

            if self.pv is not None:
                info_to_send = '{:+5.2f} | {} | {:0.1f}s | {} info_all'.format(
                    self.score, self.depth, self.time, self.pv)
                self.eng_queue.put('{}'.format(info_to_send))
            self.bm = result.move

        # Apply engine move delay if movetime is small
        if self.is_move_delay:
            while True:
                if time.perf_counter() - start_time >= self.move_delay_sec:
                    break
                logging.info('Delay sending of best move {}'.format(self.bm))
                time.sleep(1.0)

        # If bm is None, we will use engine.play()
        if self.bm is None:
            logging.info('bm is none, we will try engine,play().')
            try:
                result = self.engine.play(self.board, limit)
                self.bm = result.move
            except Exception:
                logging.exception('Failed to get engine bestmove.')
        self.eng_queue.put(f'bestmove {self.bm}')
        logging.info(f'bestmove {self.bm}')

    def get_computer_limit(self):
        """
        define the uci-settings to be used for the computer-opponent while playing.
        engines are so good nowadays that the time can be very low (a few seconds will do)
        :return: Limit-object to be used by the uci-engine
        """
        return chess.engine.Limit(
            depth=self.max_depth if self.max_depth != MAX_DEPTH else None,
            time=self.skill_level if self.use_skill else 6)

    def get_pv_original(self):
        try:
            return [m for m in self.pv]
        except:
            return []

    def quit_engine(self):
        """Quit engine."""
        logging.info('quit engine')
        try:
            self.engine.quit()
        except AttributeError:
            logging.info('AttributeError, self.engine is already None')
        except Exception:
            logging.exception('Failed to quit engine.')

    def short_variation_san(self):
        """Returns variation in san but without move numbers."""
        if self.pv is None:
            return None
        self.pv_original = self.get_pv_original()

        short_san_pv = []
        tmp_board = self.board.copy()
        for pc_move in self.pv:
            san_move = tmp_board.san(pc_move)
            short_san_pv.append(san_move)
            tmp_board.push(pc_move)

        return ' '.join(short_san_pv)


def parse_args():
    """
    Define an argument parser and return the parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='play-annotator',
        description='play chess, or annotate game')
    parser.add_argument("--engine", "-e",
                        help="analysis engine (default: %(default)s)",
                        default="no_engine")
    parser.add_argument("--startmode", "-s",
                        help="startmode program (default: %(default)s)",
                        default="neutral-default")
    parser.add_argument("--threads", "-t",
                        help="threads for use by the engine \
                            (default: %(default)s)",
                        type=int,
                        default=2)
    parser.add_argument("--maxdepth", "-d",
                        help="max depth for use by the engine \
                            (default: %(default)s)",
                        type=int,
                        default=32)

    return parser.parse_args()


class EasyChessGui:
    queue = queue.Queue()
    is_user_white = True  # White is at the bottom in board layout

    def __init__(self, theme, engine_config_file, user_config_file,
                 gui_book_file, computer_book_file, human_book_file,
                 is_use_gui_book, is_random_book, max_book_ply,
                 engine='',
                 max_depth=MAX_DEPTH, start_mode="neutral", num_threads=128):
        # self.engine_id_name used inside "Engine/manage/install etc, and in "Engine/Set engine oponent"
        self.board = ChessBoard(self)
        self.engine_id_name = None
        self.move_string = ""
        self.window = None
        self.node = None
        self.move_cnt = None
        self.is_engine_ready = None
        self.is_exit_app = None
        self.is_user_resigns = None
        self.is_user_wins = None
        self.is_user_draws = None
        self.fen_from_here = None
        self.is_exit_game = None
        self.is_new_game = None
        self.engine_timer = None
        self.human_timer = None
        self.num_threads = num_threads
        self.mode_indicator = None
        self.piece = None
        self.is_search_stop_for_user_draws = None
        self.is_search_stop_for_user_wins = None
        self.is_search_stop_for_resign = None
        self.is_search_stop_for_neutral = None
        self.is_search_stop_for_new_game = None
        self.is_search_stop_for_exit = None
        self.is_hide_book2 = None
        self.is_hide_book1 = None
        self.is_hide_search_info = None
        self.is_human_stm = None
        self.psg_promo = None
        self.fr_row = None
        self.fr_col = None
        self.to_col = None
        self.to_row = None
        self.move_state = None
        self.returning_from_playing = False
        self.game = None
        self.theme = theme
        # the engine-name passed by the command-line
        self.engine = engine.replace("no_engine", "")
        self.user_config_file = user_config_file
        self.engine_config_file = engine_config_file
        self.gui_book_file = gui_book_file
        self.computer_book_file = computer_book_file
        self.human_book_file = human_book_file
        self.max_depth = max_depth
        self.is_use_gui_book = is_use_gui_book
        self.is_random_book = is_random_book
        self.max_book_ply = max_book_ply
        self.opp_path_and_file = None
        self.opp_file = None
        self.opp_id_name = None
        self.adviser_file = None
        self.adviser_path_and_file = None
        self.adviser_id_name = None
        self.adviser_hash = 128
        self.adviser_threads = 2
        self.adviser_movetime_sec = 15
        self.pecg_auto_save_game = 'pecg_auto_save_games.pgn'
        self.my_games = 'pecg_my_games.pgn'
        self.repertoire_file = {
            'white': 'pecg_white_repertoire.pgn',
            'black': 'pecg_black_repertoire.pgn'
        }
        self.init_game()
        self.fen = None
        self.menu_elem = None
        self.engine_id_name_list = []
        self.engine_file_list = []
        self.username = 'Human'

        self.human_base_time_ms = 30 * 60 * 1000  # 5 minutes
        self.human_inc_time_ms = 10 * 1000  # 10 seconds
        self.human_period_moves = 0
        self.human_tc_type = 'fischer'

        self.engine_base_time_ms = 13 * 60 * 1000  # 13 minutes
        self.engine_inc_time_ms = 2 * 1000  # 10 seconds
        self.engine_period_moves = 0
        self.engine_tc_type = 'fischer'

        # Default board color is brown
        self.sq_light_color = '#F0D9B5'
        self.sq_dark_color = '#B58863'

        # Move highlight, for brown board
        self.move_sq_light_color = '#E8E18E'
        self.move_sq_dark_color = '#B8AF4E'

        self.preferences = Preferences()

        my_preferences = self.preferences.preferences
        self.is_save_time_left = my_preferences["is_save_time_left"] if "is_save_time_left" in my_preferences else False
        self.start_mode = my_preferences["start_mode"] if "start_mode" in my_preferences else False
        if start_mode in ["play", "pgnviewer", "pgneditor"]:
            self.start_mode = start_mode
        else:
            # default
            self.start_mode = 'pgnviewer'
        self.start_mode_used = self.start_mode
        self.sites_list = my_preferences["sites_list"] if "sites_list" in my_preferences else []
        self.events_list = my_preferences["events_list"] if "events_list" in my_preferences else []
        self.players = my_preferences["players"] if "players" in my_preferences else []
        self.menu_font_size = my_preferences["menu_font_size"] if "menu_font_size" in my_preferences else 12
        self.FIELD_SIZE = my_preferences["field_size"] if "field_size" in my_preferences else 60
        self.gui_theme = my_preferences["gui_theme"] if "gui_theme" in my_preferences else "SandyBeach"
        self.font_size_ui = my_preferences["font_size_ui"] if "font_size_ui" in my_preferences else 10
        self.window_width = my_preferences["window_width"] if "window_width" in my_preferences else 1500
        self.window_height = my_preferences["window_height"] if "window_height" in my_preferences else 800
        self.scrollbar_width = int(int(self.menu_font_size) * 16 / 12)
        self.board_color = my_preferences["board_color"] if "board_color" in my_preferences else "Brown::board_color_k"
        self.pgn_file = my_preferences["pgn_file"] if "pgn_file" in my_preferences else ""
        self.default_png_dir = my_preferences["default_png_dir"] if "default_png_dir" in my_preferences else "./"
        self.adviser_engine = my_preferences["adviser_engine"] if "adviser_engine" in my_preferences else ""
        self.is_save_user_comment = True
        #
        self.opponent_engine = my_preferences["opponent_engine"] if "opponent_engine" in my_preferences else ""
        self.skill_level = my_preferences["skill_level"] if "skill_level" in my_preferences else 1
        self.use_skill = my_preferences["use_skill"] if "use_skill" in my_preferences else True
        self.text_font = ('Consolas', self.font_size_ui)
        self.set_color_board(self.board_color, False)
        # on startup the layout-options are changed if default-window is not 'neutral'
        self.toolbar = ToolBar(self.text_font)
        self.play_toolbar = ToolBar(self.text_font, bar_id='play_button_frame')
        keyboard_visible_at_start = my_preferences[
            "keyboard_visible_at_start"] if "keyboard_visible_at_start" in my_preferences else False
        self.input_dialog = InputDialog(self, self.default_png_dir, keyboard_visible_at_start)
        self.language = my_preferences["language"] if "language" in my_preferences else "en"
        set_language(self.language)

    def update_game(self, mc: int, user_move: str, time_left: int, user_comment: str):
        """Saves moves in the game.

        Args:
          mc: move count
          user_move: user's move
          time_left: time left
          user_comment: Can be a 'book' from the engine
        """
        # Save user comment
        if self.is_save_user_comment:
            # If comment is empty
            if not (user_comment and user_comment.strip()):
                if mc == 1:
                    self.node = self.game.add_variation(user_move)
                else:
                    self.node = self.node.add_variation(user_move)

                # Save clock (time left after a move) as move comment
                if self.is_save_time_left:
                    rem_time = self.get_time_h_mm_ss(time_left, False)
                    self.node.comment = '[%clk {}]'.format(rem_time)
            else:
                if mc == 1:
                    self.node = self.game.add_variation(user_move)
                else:
                    self.node = self.node.add_variation(user_move)

                # Save clock, add clock as comment after a move
                if self.is_save_time_left:
                    rem_time = self.get_time_h_mm_ss(time_left, False)
                    self.node.comment = '[%clk {}] {}'.format(rem_time, user_comment)
                else:
                    self.node.comment = user_comment
        # Do not save user comment
        else:
            if mc == 1:
                self.node = self.game.add_variation(user_move)
            else:
                self.node = self.node.add_variation(user_move)

            # Save clock, add clock as comment after a move
            if self.is_save_time_left:
                rem_time = self.get_time_h_mm_ss(time_left, False)
                self.node.comment = '[%clk {}]'.format(rem_time)

    def display_button_bar(self):
        buttons = [self.play_toolbar.new_button(get_translation("Engine"), auto_size_button=True),
                   self.play_toolbar.new_button(get_translation("Skill"), auto_size_button=True),
                   sg.VerticalSeparator(),
                   self.play_toolbar.new_button(get_translation("New"), auto_size_button=True),
                   ]
        self.play_toolbar.buttonbar_add_buttons(self.window, buttons)


    def swap_visible_columns_window(self, window):
        # on startup the menu-options are changed if default-window is not 'neutral'
        menu_def = menu_def_neutral()
        pgn = False
        if self.start_mode_used == "pgnviewer":
            menu_def = menu_def_pgnviewer()
            pgn = True
        if self.start_mode_used == "pgneditor":
            menu_def = menu_def_entry()
            pgn = True

        self.menu_elem = sg.Menu(menu_def, tearoff=False, font=("Default", str(self.menu_font_size), ''))#"_pgn_tab_", visible=pgn
        window.find_element("_pgn_tab_").Update(visible=pgn)
        window.find_element("_play_tab_").Update(visible=not pgn)
        window.find_element("_main_menu_").Update(menu_def)
        self.menu_elem = window.find_element("_main_menu_")
        return window

    def create_new_window(self, window, flip=False):
        """Hide current window and creates a new window."""
        loc = window.CurrentLocation()
        if flip:
            self.flip_board(window)
            return window

        window.Hide()
        layout = self.build_main_layout(self.is_user_white)

        w = sg.Window(
            '{} {}'.format(APP_NAME, APP_VERSION),
            layout,
            default_button_element_size=(12, 1),
            auto_size_buttons=False, resizable=True,
            location=(loc[0], loc[1]), size=(self.window_width, self.window_height),
            icon=ico_path[platform]['pecg']
        )

        # Initialize White and black boxes
        while True:
            button, value = w.Read(timeout=50)
            self.update_labels_and_game_tags(w, human=self.username)
            break

        window.Close()
        self.window = w
        return w

    def flip_board(self, window):
        self.is_user_white = not self.is_user_white
        self.board.redraw_board(window)

    def delete_player(self, name, pgn, que):
        """
        Delete games of player name in pgn.

        :param name:
        :param pgn:
        :param que:
        :return:
        """
        logging.info('Enters delete_player()')

        pgn_path = Path(pgn)
        folder_path = pgn_path.parents[0]

        file = PurePath(pgn)
        pgn_file = file.name

        # Create backup of orig
        backup = pgn_file + '.backup'
        backup_path = Path(folder_path, backup)
        backup_path.touch()
        origfile_text = Path(pgn).read_text()
        backup_path.write_text(origfile_text)
        logging.info(f'backup copy {backup_path} is successfully created.')

        # Define output file
        output = 'out_' + pgn_file
        output_path = Path(folder_path, output)
        logging.info(f'output {output_path} is successfully created.')

        logging.info(f'Deleting player {name}.')
        gcnt = 0

        # read pgn and save each game if player name to be deleted is not in
        # the game, either white or black.
        with open(output_path, 'a') as f:
            with open(pgn_path) as h:
                game = chess.pgn.read_game(h)
                while game:
                    gcnt += 1
                    que.put('Delete, {}, processing game {}'.format(
                        name, gcnt))
                    wp = game.headers['White']
                    bp = game.headers['Black']

                    # If this game has no player with name to be deleted
                    if wp != name and bp != name:
                        f.write('{}\n\n'.format(game))
                    game = chess.pgn.read_game(h)

        if output_path.exists():
            logging.info(f'Deleting player {name} is successful.')

            # Delete the orig file and rename the current output to orig file
            pgn_path.unlink()
            logging.info('Delete orig pgn file')
            output_path.rename(pgn_path)
            logging.info('Rename output to orig pgn file')

        que.put('Done')

    def get_players(self, pgn, q):
        logging.info('Enters get_players()')
        players = []
        games = 0
        with open(pgn) as h:
            while True:
                headers = chess.pgn.read_headers(h)
                if headers is None:
                    break

                wp = headers['White']
                bp = headers['Black']

                players.append(wp)
                players.append(bp)
                games += 1

        p = list(set(players))
        ret = [p, games]

        q.put(ret)

    def get_engine_id_name(self, path_and_file, q):
        """ Returns id name of uci engine """
        id_name = None
        folder = Path(path_and_file)
        folder = folder.parents[0]

        try:
            if sys_os == 'Windows':
                engine = chess.engine.SimpleEngine.popen_uci(
                    path_and_file, cwd=folder,
                    creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                engine = chess.engine.SimpleEngine.popen_uci(
                    path_and_file, cwd=folder)
            id_name = engine.id['name']
            engine.quit()
        except Exception:
            logging.exception('Failed to get id name.')

        q.put(['Done', id_name])

    def get_engine_hash(self, eng_id_name):
        """ Returns hash value from engine config file """
        eng_hash = None
        with open(self.engine_config_file, 'r') as json_file:
            data = json.load(json_file)
            for p in data:
                if p['name'] == eng_id_name:
                    # There engines without options
                    try:
                        for n in p['options']:
                            if n['name'].lower() == 'hash':
                                return n['value']
                    except KeyError:
                        logging.info(f'This engine {eng_id_name} has no option.')
                        break
                    except Exception:
                        logging.exception('Failed to get engine hash.')

        return eng_hash

    def get_engine_threads(self, eng_id_name):
        """
        Returns number of threads of eng_id_name from pecg_engines.json.

        :param eng_id_name: the engine id name
        :return: number of threads
        """
        eng_threads = None
        with open(self.engine_config_file, 'r') as json_file:
            data = json.load(json_file)
            for p in data:
                if p['name'] == eng_id_name:
                    try:
                        for n in p['options']:
                            if n['name'].lower() == 'threads':
                                return n['value']
                    except KeyError:
                        logging.info(f'This engine {eng_id_name} has no options.')
                        break
                    except Exception:
                        logging.exception('Failed to get engine threads.')

        return eng_threads

    def get_engine_file(self, eng_id_name):
        """
        Returns eng_id_name's filename and path from pecg_engines.json file.

        :param eng_id_name: engine id name
        :return: engine file and its path
        """
        eng_file, eng_path_and_file = None, None
        with open(self.engine_config_file, 'r') as json_file:
            data = json.load(json_file)
            for p in data:
                if p['name'] == eng_id_name:
                    eng_file = p['command']
                    eng_path_and_file = Path(p['workingDirectory'],
                                             eng_file).as_posix()
                    break

        return eng_file, eng_path_and_file

    def get_engine_id_name_list(self):
        """
        Read engine config file.

        :return: list of engine id names
        """
        eng_id_name_list = []
        with open(self.engine_config_file, 'r') as json_file:
            data = json.load(json_file)
            for p in data:
                if p['protocol'] == 'uci':
                    eng_id_name_list.append(p['name'])

        eng_id_name_list = sorted(eng_id_name_list)

        return eng_id_name_list

    def update_user_config_file(self, username):
        """
        Update user config file. If username does not exist, save it.
        :param username:
        :return:
        """
        with open(self.user_config_file, 'r') as json_file:
            data = json.load(json_file)

        # Add the new entry if it does not exist
        is_name = False
        for i in range(len(data)):
            if data[i]['username'] == username:
                is_name = True
                break

        if not is_name:
            data.append({'username': username})

            # Save
            with open(self.user_config_file, 'w') as h:
                json.dump(data, h, indent=4)

    def check_user_config_file(self):
        """
        Check presence of pecg_user.json file, if nothing we will create
        one with ['username': 'Human']

        :return:
        """
        user_config_file_path = Path(self.user_config_file)
        if user_config_file_path.exists():
            with open(self.user_config_file, 'r') as json_file:
                data = json.load(json_file)
                for p in data:
                    username = p['username']
            self.username = username
        else:
            # Write a new user config file
            data = []
            data.append({'username': 'Human'})

            # Save data to pecg_user.json
            with open(self.user_config_file, 'w') as h:
                json.dump(data, h, indent=4)

    def update_engine_to_config_file(self, eng_path_file, new_name, old_name, user_opt):
        """
        Update engine config file based on params.

        :param eng_path_file: full path of engine
        :param new_name: new engine id name
        :param new_name: old engine id name
        :param user_opt: a list of dict, i.e d = ['a':a, 'b':b, ...]
        :return:
        """
        folder = Path(eng_path_file)
        folder = folder.parents[0]
        folder = Path(folder)
        folder = folder.as_posix()

        file = PurePath(eng_path_file)
        file = file.name

        with open(self.engine_config_file, 'r') as json_file:
            data = json.load(json_file)

        for p in data:
            command = p['command']
            work_dir = p['workingDirectory']

            if file == command and folder == work_dir and old_name == p['name']:
                p['name'] = new_name
                for k, v in p.items():
                    if k == 'options':
                        for d in v:
                            # d = {'name': 'Ponder', 'default': False,
                            # 'value': False, 'type': 'check'}

                            default_type = type(d['default'])
                            opt_name = d['name']
                            opt_value = d['value']
                            for u in user_opt:
                                # u = {'name': 'CDrill 1400'}
                                for k1, v1 in u.items():
                                    if k1 == opt_name:
                                        v1 = int(v1) if default_type == int else v1
                                        if v1 != opt_value:
                                            d['value'] = v1
                break

        # Save data to pecg_engines.json
        with open(self.engine_config_file, 'w') as h:
            json.dump(data, h, indent=4)

    def is_name_exists(self, name):
        """

        :param name: The name to check in pecg.engines.json file.
        :return:
        """
        with open(self.engine_config_file, 'r') as json_file:
            data = json.load(json_file)

        for p in data:
            jname = p['name']
            if jname == name:
                return True

        return False

    def add_engine_to_config_file(self, engine_path_and_file, pname, que):
        """
        Add pname config in pecg_engines.json file.

        :param engine_path_and_file:
        :param pname: id name of uci engine
        :return:
        """
        folder = Path(engine_path_and_file).parents[0]
        file = PurePath(engine_path_and_file)
        file = file.name

        option = []

        with open(self.engine_config_file, 'r') as json_file:
            data = json.load(json_file)

        try:
            if sys_os == 'Windows':
                engine = chess.engine.SimpleEngine.popen_uci(
                    engine_path_and_file, cwd=folder,
                    creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                engine = chess.engine.SimpleEngine.popen_uci(
                    engine_path_and_file, cwd=folder)
        except Exception:
            logging.exception(f'Failed to add {pname} in config file.')
            que.put('Failure')
            return

        try:
            opt_dict = engine.options.items()
        except Exception:
            logging.exception('Failed to get engine options.')
            que.put('Failure')
            return

        engine.quit()

        for opt in opt_dict:
            o = opt[1]

            if o.type == 'spin':
                # Adjust hash and threads values
                if o.name.lower() == 'threads':
                    value = 1
                    logging.info(f'config {o.name} is set to {value}')
                elif o.name.lower() == 'hash':
                    value = 32
                    logging.info(f'config {o.name} is set to {value}')
                else:
                    value = o.default

                option.append({'name': o.name,
                               'default': o.default,
                               'value': value,
                               'type': o.type,
                               'min': o.min,
                               'max': o.max})
            elif o.type == 'combo':
                option.append({'name': o.name,
                               'default': o.default,
                               'value': o.default,
                               'type': o.type,
                               'choices': o.var})
            else:
                option.append({'name': o.name,
                               'default': o.default,
                               'value': o.default,
                               'type': o.type})

        # Save engine filename, working dir, name and options
        wdir = Path(folder).as_posix()
        protocol = 'uci'  # Only uci engine is supported so far
        self.engine_id_name_list.append(pname)
        data.append({'command': file, 'workingDirectory': wdir,
                     'name': pname, 'protocol': protocol,
                     'options': option})

        # Save data to pecg_engines.json
        with open(self.engine_config_file, 'w') as h:
            json.dump(data, h, indent=4)

        que.put('Success')

    def check_engine_config_file(self):
        """
        Check presence of engine config file pecg_engines.json. If not
        found we will create it, with entries from engines in Engines folder.

        :return:
        """
        ec = Path(self.engine_config_file)
        if ec.exists():
            return

        data = []
        cwd = Path.cwd()

        self.engine_file_list = self.get_engines()

        for fn in self.engine_file_list:
            # Run engine and get id name and options
            option = []

            # cwd=current working dir, engines=folder, fn=exe file
            epath = Path(cwd, 'Engines', fn)
            engine_path_and_file = str(epath)
            folder = epath.parents[0]

            try:
                if sys_os == 'Windows':
                    engine = chess.engine.SimpleEngine.popen_uci(
                        engine_path_and_file, cwd=folder,
                        creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    engine = chess.engine.SimpleEngine.popen_uci(
                        engine_path_and_file, cwd=folder)
            except Exception:
                logging.exception(f'Failed to start engine {fn}!')
                continue

            engine_id_name = engine.id['name']
            opt_dict = engine.options.items()
            engine.quit()

            for opt in opt_dict:
                o = opt[1]

                if o.type == 'spin':
                    # Adjust hash and threads values
                    if o.name.lower() == 'threads':
                        value = 1
                    elif o.name.lower() == 'hash':
                        value = 32
                    else:
                        value = o.default

                    option.append({'name': o.name,
                                   'default': o.default,
                                   'value': value,
                                   'type': o.type,
                                   'min': o.min,
                                   'max': o.max})
                elif o.type == 'combo':
                    option.append({'name': o.name,
                                   'default': o.default,
                                   'value': o.default,
                                   'type': o.type,
                                   'choices': o.var})
                else:
                    option.append({'name': o.name,
                                   'default': o.default,
                                   'value': o.default,
                                   'type': o.type})

            # Save engine filename, working dir, name and options
            wdir = Path(cwd, 'Engines').as_posix()
            name = engine_id_name
            protocol = 'uci'
            self.engine_id_name_list.append(name)
            data.append({'command': fn, 'workingDirectory': wdir,
                         'name': name, 'protocol': protocol,
                         'options': option})

        # Save data to pecg_engines.json
        with open(self.engine_config_file, 'w') as h:
            json.dump(data, h, indent=4)

    def get_time_mm_ss_ms(self, time_ms):
        """ Returns time in min:sec:millisec given time in millisec """
        s, ms = divmod(int(time_ms), 1000)
        m, s = divmod(s, 60)

        return '{:02d}m:{:02d}s'.format(m, s)

    def get_time_h_mm_ss(self, time_ms, symbol=True):
        """
        Returns time in h:mm:ss format.

        :param time_ms:
        :param symbol:
        :return:
        """
        s, ms = divmod(int(time_ms), 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)

        if not symbol:
            return '{:01d}:{:02d}:{:02d}'.format(h, m, s)
        return '{:01d}h:{:02d}m:{:02d}s'.format(h, m, s)

    def update_text_box(self, window, msg, is_hide):
        """ Update text elements """
        best_move = None
        msg_str = str(msg)

        if 'bestmove ' not in msg_str:
            if 'info_all' in msg_str:
                info_all = ' '.join(msg_str.split()[0:-1]).strip()
                msg_line = '{}\n'.format(info_all)
                window.find_element('search_info_all_k').Update(
                    '' if is_hide else msg_line)
        else:
            # Best move can be None because engine dies
            try:
                best_move = chess.Move.from_uci(msg.split()[1])
            except Exception:
                logging.exception(f'Engine sent {best_move}')
                sg.Popup(
                    f'Engine error, it sent a {best_move} bestmove.\n \
                    Back to Neutral mode, it is better to change engine {self.opp_id_name}.',
                    icon=ico_path[platform]['pecg'],
                    title=BOX_TITLE
                )

        return best_move

    def get_tag_date(self):
        """ Return date in pgn tag date format """
        return datetime.today().strftime('%Y.%m.%d')

    def init_game(self):
        """ Initialize game with initial pgn tag values """
        self.game = chess.pgn.Game()
        self.node = None
        self.game.headers['Event'] = INIT_PGN_TAG['Event']
        self.game.headers['Date'] = self.get_tag_date()
        self.game.headers['White'] = INIT_PGN_TAG['White']
        self.game.headers['Black'] = INIT_PGN_TAG['Black']

    def set_new_game(self):
        """ Initialize new game but save old pgn tag values"""
        old_event = self.game.headers['Event']
        old_white = self.game.headers['White']
        old_black = self.game.headers['Black']

        # Define a game object for saving game in pgn format
        self.game = chess.pgn.Game()

        self.game.headers['Event'] = old_event
        self.game.headers['Date'] = self.get_tag_date()
        self.game.headers['White'] = old_white
        self.game.headers['Black'] = old_black

    def clear_elements(self, window):
        if self.is_png_layout():
            return
        """ Clear movelist, score, pv, time, depth and nps boxes """
        window.find_element('search_info_all_k').Update('')
        window.find_element('_movelist_').Update(disabled=False)
        window.find_element('_movelist_').Update('', disabled=True)
        window.find_element('polyglot_book1_k').Update('')
        window.find_element('polyglot_book2_k').Update('')
        window.find_element('advise_info_k').Update('')
        window.find_element('comment_k').Update('')

        window.Element('w_base_time_k').Update('')
        window.Element('b_base_time_k').Update('')
        window.Element('w_elapse_k').Update('')
        window.Element('b_elapse_k').Update('')
        # set play-button-bar
        self.set_neutral_button_bar(window)

    def set_neutral_button_bar(self, window):
        buttons = [self.play_toolbar.new_button(get_translation("Play"), auto_size_button=True),
                   self.play_toolbar.new_button(get_translation("PGN-Editor"), auto_size_button=True),
                   self.play_toolbar.new_button(get_translation("PGN-Viewer"), auto_size_button=True)]
        self.play_toolbar.buttonbar_add_buttons(window, buttons)

    def update_labels_and_game_tags(self, window, human='Human'):
        """ Update player names """
        engine_id = self.opp_id_name
        element_exists = '_White_' in window.AllKeysDict
        if not element_exists:
            return
        if self.is_user_white:
            window.find_element('_White_').Update(human)
            window.find_element('_Black_').Update(engine_id)
            self.game.headers['White'] = human
            self.game.headers['Black'] = engine_id
        else:
            window.find_element('_White_').Update(engine_id)
            window.find_element('_Black_').Update(human)
            self.game.headers['White'] = engine_id
            self.game.headers['Black'] = human

    def get_fen(self):
        """ Get fen from clipboard """
        self.fen = pyperclip.paste()

        # Remove empty char at the end of FEN
        if self.fen.endswith(' '):
            self.fen = self.fen[:-1]

    def get_advice(self, board, callback):
        self.adviser_threads = self.get_engine_threads(
            self.adviser_id_name)
        self.adviser_threads = self.adviser_threads if self.num_threads > self.adviser_threads else self.num_threads
        self.adviser_hash = self.get_engine_hash(
            self.adviser_id_name)
        adviser_base_ms = self.adviser_movetime_sec * 1000
        adviser_inc_ms = 0

        search = RunEngine(
            self.queue, self.engine_config_file,
            self.adviser_path_and_file, self.adviser_id_name,
            MAX_ADVISER_DEPTH, adviser_base_ms, adviser_inc_ms,
            tc_type='timepermove',
            period_moves=0,
            is_stream_search_info=True
        )
        search.get_board(board)
        search.daemon = True
        search.start()
        msg_line = ""
        alternatives = {}

        while True:
            try:
                msg = self.queue.get_nowait()
                if 'pv' in msg:
                    # Reformat msg, remove the word pv at the end
                    msg_line = ' '.join(msg.split()[0:-1])
                    alternatives[msg_line] = [search.score, search.pv_original]
                    callback(msg_line)
            except Exception:
                continue

            if 'bestmove' in msg:
                # bestmove can be None so we do try/except
                try:
                    # Shorten msg line to 3 ply moves (.split()[0:3])
                    msg_line = join(msg_line)
                except Exception:
                    logging.exception('Adviser engine error')
                break

        search.join()
        search.quit_engine()
        alternatives[msg_line] = [search.score, search.pv_original]
        return msg_line, search.score, search.pv, search.pv_original, alternatives

    def relative_row(self, s, stm):
        """
        The board can be viewed, as white at the bottom and black at the
        top. If stm is white the row 0 is at the bottom. If stm is black
        row 0 is at the top.
        :param s: square
        :param stm: side to move
        :return: relative row
        """
        return 7 - self.get_row(s) if stm else self.get_row(s)

    def get_row(self, s):
        """
        This row is based on PySimpleGUI square mapping that is 0 at the
        top and 7 at the bottom.
        In contrast Python-chess square mapping is 0 at the bottom and 7
        at the top. chess.square_rank() is a method from Python-chess that
        returns row given square s.

        :param s: square
        :return: row
        """
        return 7 - chess.square_rank(s)

    def get_col(self, s):
        """ Returns col given square s """
        return chess.square_file(s)

    def update_ep(self, window, move, stm):
        """
        Update board for e.p move.

        :param window:
        :param move: python-chess format
        :param stm: side to move
        :return:
        """
        to = move.to_square
        if stm:
            capture_sq = to - 8
        else:
            capture_sq = to + 8

        self.board.psg_board_set_piece(self.get_row(capture_sq), self.get_col(capture_sq), BLANK)
        self.board.redraw_board(window)

    def set_depth_limit(self):
        """ Returns max depth based from user setting """
        user_depth = sg.PopupGetText(
            get_translation("_get_depth_").format(self.max_depth,MIN_DEPTH, MAX_DEPTH),
            title=BOX_TITLE, font=self.text_font,
            icon=ico_path[platform]['pecg']
        )

        try:
            user_depth = int(user_depth)
        except Exception:
            user_depth = self.max_depth
            logging.exception(get_translation('Failed to get user depth.'))

        self.max_depth = min(MAX_DEPTH, max(MIN_DEPTH, user_depth))

    def define_timer(self, window, name='human'):
        """
        Returns Timer object for either human or engine.
        """
        if name == 'human':
            timer = Timer(
                self.human_tc_type, self.human_base_time_ms,
                self.human_inc_time_ms, self.human_period_moves
            )
        else:
            timer = Timer(
                self.engine_tc_type, self.engine_base_time_ms,
                self.engine_inc_time_ms, self.engine_period_moves
            )

        elapse_str = self.get_time_h_mm_ss(timer.base)
        is_white_base = (self.is_user_white and name == 'human') or (not self.is_user_white and name != 'human')
        window.Element('w_base_time_k' if is_white_base else 'b_base_time_k').Update(elapse_str)

        return timer

    def get_item_from_list(self, list_items, title_window, width=30):
        """
        display items from list, and return selected item if ok is rpessed
        :param width:
        :param list_items: a list of strings
        :param title_window: the title on top of the window
        :return: the item selected if ok, empty string if cancel is pressed
        """
        layout = [
            [sg.Listbox(list_items, key='game_k', expand_y=True, enable_events=True, font=self.text_font,
                        size=(width, 20), sbar_width=self.scrollbar_width, sbar_arrow_width=self.scrollbar_width)],
            [sg.Ok(font=self.text_font), sg.Cancel(font=self.text_font)
                , sg.Button("Down",
                            font=self.text_font, key='scroll_down'),
             sg.Button("Up", key='scroll_up', font=self.text_font)
             ]
        ]
        w = sg.Window(title_window, layout,
                      icon='Icon/pecg.png')
        index = 0
        selected_item = ""
        while True:
            e, v = w.Read(timeout=10)
            if e is None or e == 'Cancel':
                w.Close()
                selected_item = ""
                break
            if e == 'scroll_down':
                # print("Down button")
                index = index + 30
                if index >= len(list_items):
                    index = len(list_items) - 1
                w.find_element('game_k').Update(set_to_index=index, scroll_to_index=index - 3)
            if e == "scroll_up":
                # print("Up button")
                index = index - 30
                if index < 0:
                    index = 0
                w.find_element('game_k').Update(set_to_index=index, scroll_to_index=index - 3)

            if e == 'Ok':
                w.Close()
                # print(v['game_k'])
                try:
                    selected_item = v['game_k'][0]
                except:
                    selected_item = ""
                break
        return selected_item

    def play_game(self, window: sg.Window, board: chess.Board):
        """Play a game against an engine or human.

        Args:
          window: A PySimplegUI window.
          board: current board position
        """
        window.find_element('_movelist_').Update(disabled=False)
        window.find_element('_movelist_').Update('', disabled=True)

        self.is_human_stm = True if self.is_user_white else False

        self.move_state = 0
        move_from, move_to = None, None
        self.is_new_game, self.is_exit_game, self.is_exit_app = False, False, False

        # Do not play immediately when stm is computer
        self.is_engine_ready = True if self.is_human_stm else False

        # For saving game
        self.move_cnt = 0

        self.is_user_resigns = False
        self.is_user_wins = False
        self.is_user_draws = False
        self.is_search_stop_for_exit = False
        self.is_search_stop_for_new_game = False
        self.is_search_stop_for_neutral = False
        self.is_search_stop_for_resign = False
        self.is_search_stop_for_user_wins = False
        self.is_search_stop_for_user_draws = False
        self.is_hide_book1 = True
        self.is_hide_book2 = True
        self.is_hide_search_info = True

        # Init timer
        self.human_timer = self.define_timer(window)
        self.engine_timer = self.define_timer(window, 'engine')

        # Game loop
        while not board.is_game_over(claim_draw=True):
            moved_piece = None

            # Mode: Play, Hide book 1
            if self.is_hide_book1:
                window.Element('polyglot_book1_k').Update('')
            else:
                # Load 2 polyglot book files.
                ref_book1 = GuiBook(self.computer_book_file, board,
                                    self.is_random_book)
                all_moves, is_found = ref_book1.get_all_moves()
                if is_found:
                    window.Element('polyglot_book1_k').Update(all_moves)
                else:
                    window.Element('polyglot_book1_k').Update('no book moves')

            # Mode: Play, Hide book 2
            if self.is_hide_book2:
                window.Element('polyglot_book2_k').Update('')
            else:
                ref_book2 = GuiBook(self.human_book_file, board,
                                    self.is_random_book)
                all_moves, is_found = ref_book2.get_all_moves()
                if is_found:
                    window.Element('polyglot_book2_k').Update(all_moves)
                else:
                    window.Element('polyglot_book2_k').Update('no book moves')

            # Mode: Play, Stm: computer (first move), Allow user to change settings.
            # User can start the engine by Engine->Go.
            self.mode_indicator = 'Mode     Play'

            if not self.is_engine_ready:
                board = self.check_engine_ready_and_settings_first_move(board, window)

                if self.is_exit_app or self.is_exit_game or self.is_new_game:
                    break

            # If side to move is human
            if self.is_human_stm:
                board = self.do_human_move(move_from, moved_piece, board, window)
                if (self.is_new_game or self.is_exit_game or self.is_exit_app or
                        self.is_user_resigns or self.is_user_wins or self.is_user_draws):
                    break

            # Else if side to move is not human
            elif not self.is_human_stm and self.is_engine_ready:
                no_best_move = (
                    self.do_computer_move(board, window)
                ) or self.is_exit_game or self.is_exit_app
                if no_best_move:
                    break

            if self.start_mode_used in ["pgneditor", "pgnviewer"]:
                self.returning_from_playing = True
                break

        # Auto-save game
        logging.info('Saving game automatically')
        if self.is_user_resigns:
            self.game.headers['Result'] = '0-1' if self.is_user_white else '1-0'
            self.game.headers['Termination'] = '{} resigns'.format(
                'white' if self.is_user_white else 'black')
        elif self.is_user_wins:
            self.game.headers['Result'] = '1-0' if self.is_user_white else '0-1'
            self.game.headers['Termination'] = 'Adjudication'
        elif self.is_user_draws:
            self.game.headers['Result'] = '1/2-1/2'
            self.game.headers['Termination'] = 'Adjudication'
        else:
            self.game.headers['Result'] = board.result(claim_draw=True)

        base_h = int(self.human_base_time_ms / 1000)
        inc_h = int(self.human_inc_time_ms / 1000)
        base_e = int(self.engine_base_time_ms / 1000)
        inc_e = int(self.engine_inc_time_ms / 1000)

        if self.is_user_white:
            if self.human_tc_type == 'fischer':
                self.game.headers['WhiteTimeControl'] = str(base_h) + '+' + \
                                                        str(inc_h)
            elif self.human_tc_type == 'delay':
                self.game.headers['WhiteTimeControl'] = str(base_h) + '-' + \
                                                        str(inc_h)
            if self.engine_tc_type == 'fischer':
                self.game.headers['BlackTimeControl'] = str(base_e) + '+' + \
                                                        str(inc_e)
            elif self.engine_tc_type == 'timepermove':
                self.game.headers['BlackTimeControl'] = str(1) + '/' + str(base_e)
        else:
            if self.human_tc_type == 'fischer':
                self.game.headers['BlackTimeControl'] = str(base_h) + '+' + \
                                                        str(inc_h)
            elif self.human_tc_type == 'delay':
                self.game.headers['BlackTimeControl'] = str(base_h) + '-' + \
                                                        str(inc_h)
            if self.engine_tc_type == 'fischer':
                self.game.headers['WhiteTimeControl'] = str(base_e) + '+' + \
                                                        str(inc_e)
            elif self.engine_tc_type == 'timepermove':
                self.game.headers['WhiteTimeControl'] = str(1) + '/' + str(base_e)
        # if game is transferred to pgn-viewer/pgn-editor, do not auto-save it
        if self.start_mode_used not in ["pgneditor", "pgnviewer"]:
            self.save_game()
        else:
            # store the headers and the game-data in the move_string to use it in pgn-mode
            self.move_string = '{}\n\n'.format(self.game)

        if board.is_game_over(claim_draw=True):
            sg.Popup('Game is over.', title=BOX_TITLE,
                     icon=ico_path[platform]['pecg'])

        if self.is_exit_app:
            window.Close()
            sys.exit(0)

        self.clear_elements(window)

        return False if self.is_exit_game else self.is_new_game

    def check_engine_ready_and_settings_first_move(self, board, window):
        window.find_element('_gamestatus_').Update(
            'Mode     Play, press Engine->Go')
        while True:
            button, value = window.Read(timeout=100)
            #hier
            button = get_button_id(button)

            if self.start_mode_used in ["pgneditor", "pgnviewer"]:
                print("start-mode set to data-entry..")
                break

            # Mode: Play, Stm: computer (first move)
            if 'new_game_k' in button:
                self.is_new_game = True
                break

            # Mode: Play, Stm: Computer first move
            if button == 'Play Settings' or self.start_mode_used == "pgnviewer":
                self.is_exit_game = True
                self.start_mode_used = ""
                break

            if button == 'PGN-Editor':
                self.play_to_pgn_editor(window)
                # do something with current game
                break

            if button == 'PGN-Viewer':
                self.play_to_pgn_viewer(window)
                break

            if button == 'GUI':
                sg.PopupScrolled(HELP_MSG, title=BOX_TITLE)
                continue

            if button == '_paste-fen_' or self.fen_from_here:
                try:
                    if button == '_paste-fen_':
                        self.get_fen()
                    else:
                        self.fen = self.fen_from_here
                        self.fen_from_here = None
                    self.set_new_game()
                    board = chess.Board(self.fen)
                except Exception:
                    logging.exception('Error in parsing FEN from clipboard.')
                    continue

                self.board.fen_to_psg_board(window)

                # If user is black and side to move is black
                if not self.is_user_white and not board.turn:
                    self.is_human_stm = True
                    window.find_element('_gamestatus_').Update(
                        self.mode_indicator)

                # Elif user is black and side to move is white
                elif not self.is_user_white and board.turn:
                    self.is_human_stm = False
                    window.find_element('_gamestatus_').Update(
                        'Mode     Play, press Engine->Go')

                # When computer is to move in the first move, don't
                # allow the engine to search immediately, wait for the
                # user to press Engine->Go menu.
                self.is_engine_ready = True if self.is_human_stm else False

                self.game.headers['FEN'] = self.fen
                break

            if button == 'Go':
                self.is_engine_ready = True
                break

            if button is None:
                logging.info('Quit app X is pressed.')
                self.is_exit_app = True
                break
        return board

    def play_to_pgn_viewer(self, window):
        self.start_mode_used = "pgnviewer"
        self.store_current_game_for_pgn(window)

    def store_current_game_for_pgn(self, window):
        _, values2 = window.read(1)
        # get content of current game
        self.move_string = values2['_movelist_']
        self.is_exit_game = True
        self.swap_visible_columns_window(window)

    def play_to_pgn_editor(self, window):
        self.start_mode_used = "pgneditor"
        self.store_current_game_for_pgn(window)

    def do_human_move(self, move_from, moved_piece, board, window):
        self.move_state = 0
        while True:
            button, value = window.Read(timeout=100)
            #hier
            button = get_button_id(button)
            if button == sg.WIN_CLOSED:
                logging.warning('User closes the window while the engine is thinking.')
                try:
                    search.stop()
                except:
                    logging.exception('search is not defined')
                    pass
                sys.exit(0)  # the engine is run on daemon threads so it will quit as well

            # Update elapse box in m:s format
            elapse_str = self.get_time_mm_ss_ms(self.human_timer.elapse)
            k = 'w_elapse_k'
            if not self.is_user_white:
                k = 'b_elapse_k'
            window.Element(k).Update(elapse_str)
            self.human_timer.elapse += 100

            if not self.is_human_stm:
                break

            if button == 'PGN-Editor':
                self.play_to_pgn_editor(window)
                break
            if button == 'PGN-Viewer':
                self.play_to_pgn_viewer(window)
                break

            if self.check_game_setting_button(button, self.window):
                window = self.window
                continue

            # Mode: Play, Stm: User, Run adviser engine
            if button == 'adviser_k':
                self.give_advice(board, window)
                break

            # Mode: Play, Stm: user
            if button == 'search_info_k':
                self.is_hide_search_info = not self.is_hide_search_info
                if self.is_hide_search_info:
                    window.Element('search_info_all_k').Update('')
                break

            # Mode: Play, Stm: user
            if 'right_book1_k' in button:
                self.is_hide_book1 = False
                break

            # Mode: Play, Stm: user
            # todo: check....
            if 'right_book1_k' in button:
                self.is_hide_book1 = True
                break

            # Mode: Play, Stm: user
            if 'right_book2_k' in button:
                self.is_hide_book2 = False
                break

            # Mode: Play, Stm: user
            # todo: check..
            if 'right_book2_k' in button:
                self.is_hide_book2 = True
                break

            if button is None:
                logging.info('Quit app X is pressed.')
                self.is_exit_app = True
                break

            if self.is_search_stop_for_exit:
                self.is_exit_app = True
                logging.warning('Search is stopped for exit.')
                break

            # Mode: Play, Stm: User
            if 'new_game_k' in button or self.is_search_stop_for_new_game:
                self.is_new_game = True
                self.clear_elements(window)
                break

            if button == 'Analyse game':
                value_white = value['_White_']
                value_black = value['_Black_']

                self.analyse_game(value_white, value_black, self.game)
                break

            if 'save_game_k' in button:
                logging.info('Saving game manually')
                self.input_dialog.add_pgn_to_file(self.game)
                # with open(self.my_games, mode='a+') as f:
                #     self.game.headers['Event'] = 'My Games'
                #     f.write('{}\n\n'.format(self.game))
                break

            # Mode: Play, Stm: user
            if button == 'Save to White Repertoire':
                with open(os.path.join(self.default_png_dir, self.repertoire_file['white']), mode='a+') as f:
                    self.game.headers['Event'] = 'White Repertoire'
                    f.write('{}\n\n'.format(self.game))
                break

            # Mode: Play, Stm: user
            if button == 'Save to Black Repertoire':
                with open(os.path.join(self.default_png_dir,self.repertoire_file['black']), mode='a+') as f:
                    self.game.headers['Event'] = 'Black Repertoire'
                    f.write('{}\n\n'.format(self.game))
                break

            if self.check_button_bar_press(button, window):
                break

            # Mode: Play, stm: User
            if 'resign_game_k' in button or self.is_search_stop_for_resign:
                logging.info('User resigns')

                # Verify resign
                reply = sg.Popup('Do you really want to resign?',
                                 button_type=sg.POPUP_BUTTONS_YES_NO,
                                 title=BOX_TITLE,
                                 icon=ico_path[platform]['pecg'])
                if reply == 'Yes':
                    self.is_user_resigns = True
                    self.is_new_game = True
                    break
                else:
                    if self.is_search_stop_for_resign:
                        self.is_search_stop_for_resign = False
                    continue

            # Mode: Play, stm: User
            if 'user_wins_k' in button or self.is_search_stop_for_user_wins:
                logging.info('User wins by adjudication')
                self.is_user_wins = True
                self.is_new_game = True
                break

            # Mode: Play, stm: User
            if 'user_draws_k' in button or self.is_search_stop_for_user_draws:
                logging.info('User draws by adjudication')
                self.is_user_draws = True
                self.is_new_game = True
                break

            # Mode: Play, Stm: User
            if button == 'Play Settings' or self.is_search_stop_for_neutral:
                self.is_exit_game = True
                self.start_mode_used = ""
                self.clear_elements(window)
                window.find_element("play_top_frame").Update(visible=False)
                break

            # Mode: Play, stm: User
            if button == 'GUI':
                sg.PopupScrolled(HELP_MSG, title=BOX_TITLE, )
                break

            # Mode: Play, stm: User
            if button == 'Go':
                if self.is_human_stm:
                    self.is_human_stm = False
                else:
                    self.is_human_stm = True
                self.is_engine_ready = True
                window.find_element('_gamestatus_').Update(
                    'Mode     Play, Engine is thinking ...')
                break

            # Mode: Play, stm: User
            if button == '_paste-fen_' or self.fen_from_here:
                # Pasting fen is only allowed before the game starts.
                if len(self.game.variations):
                    sg.Popup('Press Game->New then paste your fen.',
                             title='Mode Play')
                    continue
                try:
                    if button == '_paste-fen_':
                        self.get_fen()
                    else:
                        # here it is read
                        self.fen = self.fen_from_here
                        self.fen_from_here = None

                    self.set_new_game()
                    board = chess.Board(self.fen)
                except Exception:
                    logging.exception('Error in parsing FEN from clipboard.')
                    continue

                self.board.fen_to_psg_board(window)

                self.is_human_stm = True if board.turn else False
                self.is_engine_ready = True if self.is_human_stm else False

                window.find_element('_gamestatus_').Update(
                    'Mode     Play, side: {}'.format(
                        'white' if board.turn else 'black'))

                self.game.headers['FEN'] = self.fen
                break

            self.check_depth_button(button)

            # Mode: Play, stm: User, user starts moving
            if type(button) is tuple:
                # If fr_sq button is pressed
                if self.move_state == 0:
                    move_from, self.fr_row, self.fr_col = self.board.get_chess_row_col(button)
                    self.piece = self.board.psg_board_get_piece(self.fr_row, self.fr_col)  # get the move-from piece

                    # Change the color of the "from" board square
                    self.board.change_square_color_move(window, self.fr_row, self.fr_col)

                    self.move_state = 1
                    moved_piece = board.piece_type_at(chess.square(self.fr_col, 7 - self.fr_row))  # Pawn=1

                # Else if to_sq button is pressed
                elif self.move_state == 1:
                    move_to, self.to_row, self.to_col = self.board.get_chess_row_col(button)
                    button_square = window.find_element(key=self.board.get_field_id((self.fr_row, self.fr_col)))

                    # If move is cancelled, pressing same button twice
                    if move_to == move_from:
                        # Restore the color of the pressed board square
                        color = self.sq_dark_color if (self.to_row + self.to_col) % 2 else self.sq_light_color

                        # Restore the color of the from-square
                        button_square.Update(button_color=('white', color))
                        self.move_state = 0
                        continue
                    illegal_move = self.do_user_move(move_from, moved_piece, value['comment_k'], window, board)
                    if illegal_move:
                        self.move_state = 0
                        color = self.sq_dark_color \
                            if (move_from[0] + move_from[1]) % 2 else self.sq_light_color

                        # Restore the color of the from-square
                        button_square.Update(button_color=('white', color))
                        continue
        return board

    def check_button_bar_press(self, button, window):
        is_break = False
        if self.play_toolbar.get_button_id(button) == get_translation('Engine'):
            self.opponent_engine, is_engine_set = self.define_engine(self.opponent_engine, window)
            if is_engine_set:
                pass
        if self.play_toolbar.get_button_id(button) == get_translation('Skill'):
            self.get_settings_pgn(window)
        if self.play_toolbar.get_button_id(button) == get_translation('New'):
            self.is_new_game = True
            is_break = True
        return is_break

    def do_computer_move(self, board, window):
        is_promote = False
        best_move = None
        do_break = False

        is_book_from_gui = True
        # Mode: Play, stm: Computer, If using gui book
        if self.is_use_gui_book and self.move_cnt <= self.max_book_ply:
            # Verify presence of a book file
            if os.path.isfile(self.gui_book_file):
                gui_book = GuiBook(self.gui_book_file, board, self.is_random_book)
                best_move = gui_book.get_book_move()
                logging.info('Book move is {}.'.format(best_move))
            else:
                logging.warning('GUI book is missing.')
        # Mode: Play, stm: Computer, If there is no book move,
        # let the engine search the best move
        if best_move is None:
            search = RunEngine(
                self.queue, self.engine_config_file, self.opp_path_and_file,
                self.opp_id_name, self.max_depth, self.engine_timer.base,
                self.engine_timer.inc, tc_type=self.engine_timer.tc_type,
                period_moves=board.fullmove_number, is_computer_move=True, skill_level=self.skill_level,
                use_skill=self.use_skill
            )
            search.get_board(board)
            search.daemon = True
            search.start()
            window.find_element('_gamestatus_').Update(
                'Mode     Play, Engine is thinking ...')

            while True:
                button, value = window.Read(timeout=100)
                #hier
                button = get_button_id(button)

                if button == sg.WIN_CLOSED:
                    logging.warning('User closes the window while the engine is thinking.')
                    search.stop()
                    sys.exit(0)  # the engine is run on daemon threads so it will quit as well

                # Update elapse box in m:s format
                elapse_str = self.get_time_mm_ss_ms(self.engine_timer.elapse)
                k = 'b_elapse_k'
                if not self.is_user_white:
                    k = 'w_elapse_k'
                window.Element(k).Update(elapse_str)
                self.engine_timer.elapse += 100

                if self.check_game_setting_button(button, self.window):
                    window = self.window
                    continue

                # Hide/Unhide engine searching info while engine is thinking
                if button == 'search_info_k':
                    self.is_hide_search_info = not self.is_hide_search_info
                    if self.is_hide_search_info:
                        window.Element('search_info_all_k').Update('')

                # Show book 1 while engine is searching
                if button == 'Show::right_book1_k':
                    self.is_hide_book1 = False
                    ref_book1 = GuiBook(self.computer_book_file,
                                        board, self.is_random_book)
                    all_moves, is_found = ref_book1.get_all_moves()
                    if is_found:
                        window.Element('polyglot_book1_k').Update(all_moves)
                    else:
                        window.Element('polyglot_book1_k').Update('no book moves')

                # Hide book 1 while engine is searching
                if button == 'Hide::right_book1_k':
                    self.is_hide_book1 = True
                    window.Element('polyglot_book1_k').Update('')

                # Show book 2 while engine is searching
                if button == 'Show::right_book2_k':
                    self.is_hide_book2 = False
                    ref_book2 = GuiBook(self.human_book_file, board,
                                        self.is_random_book)
                    all_moves, is_found = ref_book2.get_all_moves()
                    if is_found:
                        window.Element('polyglot_book2_k').Update(all_moves)
                    else:
                        window.Element('polyglot_book2_k').Update('no book moves')

                # Hide book 2 while engine is searching
                if button == 'Hide::right_book2_k':
                    self.is_hide_book2 = True
                    window.Element('polyglot_book2_k').Update('')

                # Exit app while engine is thinking.
                if button is None:
                    search.stop()
                    self.is_search_stop_for_exit = True

                # Forced engine to move now and create a new game
                if 'new_game_k' in button:
                    search.stop()
                    self.is_search_stop_for_new_game = True

                # Forced engine to move now
                if button == 'Move Now':
                    search.stop()
                self.check_depth_button(button)

                # Mode: Play, Computer is thinking
                if button in ['Play Settings', 'PGN-Viewer', 'PGN-Editor']:
                    search.stop()
                    if button == 'PGN-Viewer':
                        self.play_to_pgn_viewer(window)
                    if button == 'PGN-Editor':
                        self.play_to_pgn_editor(window)
                    self.is_search_stop_for_neutral = True

                if self.check_button_bar_press(button, window):
                    search.stop()
                    break

                if 'resign_game_k' in button:
                    search.stop()
                    self.is_search_stop_for_resign = True

                if 'user_wins_k' in button:
                    search.stop()
                    self.is_search_stop_for_user_wins = True

                if 'user_draws_k' in button:
                    search.stop()
                    self.is_search_stop_for_user_draws = True

                # Get the engine search info and display it in GUI text boxes
                try:
                    msg = self.queue.get_nowait()
                except Exception:
                    continue

                msg_str = str(msg)
                best_move = self.update_text_box(window, msg, self.is_hide_search_info)
                if 'bestmove' in msg_str:
                    logging.info('engine msg: {}'.format(msg_str))
                    break

            search.join()
            search.quit_engine()
            is_book_from_gui = False
        # If engine failed to send a legal move
        if best_move is None:
            do_break = True
        else:
            # Update board with computer move
            self.update_board_with_computer_move(best_move, is_book_from_gui, is_promote, board, window)
        return do_break

    def update_board_with_computer_move(self, best_move, is_book_from_gui, is_promote, board, window):
        move_str = str(best_move)
        self.fr_col = ord(move_str[0]) - ord('a')
        self.fr_row = 8 - int(move_str[1])
        self.to_col = ord(move_str[2]) - ord('a')
        self.to_row = 8 - int(move_str[3])
        self.piece = self.board.psg_board_get_piece(self.fr_row, self.fr_col)
        self.board.psg_board_set_piece(self.fr_row, self.fr_col, BLANK)
        # Update rook location if this is a castle move
        if board.is_castling(best_move):
            self.board.update_rook(window, move_str)

        # Update board if e.p capture
        elif board.is_en_passant(best_move):
            self.update_ep(window, best_move, board.turn)

        # Update board if move is a promotion
        elif best_move.promotion is not None:
            is_promote = True
            _, self.psg_promo = self.board.get_promo_piece(best_move, board.turn, False)
        # Update board to_square if move is a promotion
        if is_promote:
            self.board.psg_board_set_piece(self.to_row, self.to_col, self.psg_promo)
        # Update the to_square if not a promote move
        else:
            # Place piece in the move to_square
            self.board.psg_board_set_piece(self.to_row, self.to_col, self.piece)
        self.board.redraw_board(window)
        board.push(best_move)
        self.move_cnt += 1
        # Update timer
        self.engine_timer.update_base()
        # Update game, move from engine
        time_left = self.engine_timer.base
        if is_book_from_gui:
            engine_comment = 'book'
        else:
            engine_comment = ''
        self.update_game(self.move_cnt, best_move, time_left, engine_comment)
        window.find_element('_movelist_').Update(disabled=False)
        window.find_element('_movelist_').Update('')
        window.find_element('_movelist_').Update(
            self.game.variations[0], append=True, disabled=True)
        # Change the color of the "from" and "to" board squares
        self.board.change_square_color_move(window, self.fr_row, self.fr_col)
        self.board.change_square_color_move(window, self.to_row, self.to_col)
        self.is_human_stm = not self.is_human_stm
        # Engine has done its move
        k1 = 'b_elapse_k'
        k2 = 'b_base_time_k'
        if not self.is_user_white:
            k1 = 'w_elapse_k'
            k2 = 'w_base_time_k'
        # Update elapse box
        elapse_str = self.get_time_mm_ss_ms(self.engine_timer.elapse)
        window.Element(k1).Update(elapse_str)
        # Update remaining time box
        elapse_str = self.get_time_h_mm_ss(self.engine_timer.base)
        window.Element(k2).Update(elapse_str)
        window.find_element('_gamestatus_').Update(self.mode_indicator)

    def give_advice(self, board, window):
        self.adviser_threads = self.get_engine_threads(
            self.adviser_id_name)
        self.adviser_threads = self.adviser_threads if self.num_threads > self.adviser_threads else self.num_threads
        self.adviser_hash = self.get_engine_hash(
            self.adviser_id_name)
        adviser_base_ms = self.adviser_movetime_sec * 1000
        adviser_inc_ms = 0
        search = RunEngine(
            self.queue, self.engine_config_file,
            self.adviser_path_and_file, self.adviser_id_name,
            MAX_ADVISER_DEPTH, adviser_base_ms, adviser_inc_ms,
            tc_type='timepermove',
            period_moves=0,
            is_stream_search_info=True
        )
        search.get_board(board)
        search.daemon = True
        search.start()
        while True:
            button, value = window.Read(timeout=10)

            if button == 'adviser_k':
                search.stop()

            # Exit app while adviser is thinking.
            if button is None:
                search.stop()
                self.is_search_stop_for_exit = True
            try:
                msg = self.queue.get_nowait()
                if 'pv' in msg:
                    # Reformat msg, remove the word pv at the end
                    msg_line = ' '.join(msg.split()[0:-1])
                    window.Element('advise_info_k').Update(msg_line)
            except Exception:
                continue

            if 'bestmove' in msg:
                # bestmove can be None so we do try/except
                try:
                    # Shorten msg line to 3 ply moves
                    msg_line = ' '.join(msg_line.split()[0:3])
                    msg_line += ' - ' + self.adviser_id_name
                    window.Element('advise_info_k').Update(msg_line)
                except Exception:
                    logging.exception('Adviser engine error')
                    sg.Popup(
                        f'Adviser engine {self.adviser_id_name} error.\n \
                                        It is better to change this engine.\n \
                                        Change to Neutral mode first.',
                        icon=ico_path[platform]['pecg'],
                        title=BOX_TITLE
                    )
                break
        search.join()
        search.quit_engine()

    def do_user_move(self, move_from, moved_piece, value_comment, window, board):
        is_promote = False
        # Create a move in python-chess format based from user input
        user_move = None
        pyc_promo = None
        self.psg_promo = None
        illegal_move = False
        # Get the fr_sq and to_sq of the move from user, based from this info
        # we will create a move based from python-chess format.
        # Note chess.square() and chess.Move() are from python-chess module
        self.fr_row, self.fr_col = move_from
        fr_sq = chess.square(self.fr_col, 7 - self.fr_row)
        to_sq = chess.square(self.to_col, 7 - self.to_row)
        # If user move is a promote
        if self.relative_row(to_sq, board.turn) == RANK_8 and \
                moved_piece == chess.PAWN:
            is_promote = True
            pyc_promo, self.psg_promo = self.board.get_promo_piece(
                user_move, board.turn, True)
            user_move = chess.Move(fr_sq, to_sq, promotion=pyc_promo)
        else:
            user_move = chess.Move(fr_sq, to_sq)
        # Check if user move is legal
        if user_move in list(board.legal_moves):
            self.move_state = 0
            # Update rook location if this is a castle move
            if board.is_castling(user_move):
                self.board.update_rook(window, str(user_move))

            # Update board if e.p capture
            elif board.is_en_passant(user_move):
                self.update_ep(window, user_move, board.turn)

            # Empty the board from_square, applied to any types of move
            self.board.psg_board_set_piece(move_from[0], move_from[1], BLANK)

            # Update board to_square if move is a promotion
            if is_promote:
                self.board.psg_board_set_piece(self.to_row, self.to_col, self.psg_promo)
            # Update the to_square if not a promote move
            else:
                # Place piece in the move to_square
                self.board.psg_board_set_piece(self.to_row, self.to_col, self.piece)

            self.board.redraw_board(window)

            board.push(user_move)
            self.move_cnt += 1

            # Update clock, reset elapse to zero
            self.human_timer.update_base()

            # Update game, move from human
            time_left = self.human_timer.base
            user_comment = value_comment
            self.update_game(self.move_cnt, user_move, time_left, user_comment)

            window.find_element('_movelist_').Update(disabled=False)
            window.find_element('_movelist_').Update('')
            window.find_element('_movelist_').Update(
                self.game.variations[0], append=True, disabled=True)

            # Clear comment and engine search box
            window.find_element('comment_k').Update('')
            window.Element('search_info_all_k').Update('')

            # Change the color of the "from" and "to" board squares
            self.board.change_square_color_move(window, self.fr_row, self.fr_col)
            self.board.change_square_color_move(window, self.to_row, self.to_col)

            self.is_human_stm = not self.is_human_stm
            # Human has done its move

            k1 = 'w_elapse_k'
            k2 = 'w_base_time_k'
            if not self.is_user_white:
                k1 = 'b_elapse_k'
                k2 = 'b_base_time_k'

            # Update elapse box
            elapse_str = self.get_time_mm_ss_ms(
                self.human_timer.elapse)
            window.Element(k1).Update(elapse_str)

            # Update remaining time box
            elapse_str = self.get_time_h_mm_ss(
                self.human_timer.base)
            window.Element(k2).Update(elapse_str)

            window.Element('advise_info_k').Update('')

        # Else if move is illegal
        else:
            illegal_move = True
        return illegal_move

    def save_game_pgn(self, value_white, value_black, pgn_game):
        header_dialog, name_file = self.get_game_data(value_white, value_black, pgn_game)
        if header_dialog.ok:
            self.input_dialog.save_file(name_file)
            if self.input_dialog.filename:
                with open(self.input_dialog.filename, mode='w') as f:
                    f.write('{}\n\n'.format(pgn_game))
                if header_dialog.add_to_library:
                    with open(os.path.join(self.default_png_dir, "library.pgn"), 'a') as file1:
                        file1.write('{}\n\n'.format(pgn_game))

                sg.popup_ok("PGN is saved as:{}".format(self.input_dialog.filename), title="Save PGN")

    def analyse_game(self, value_white, value_black, pgn_game, save_file=True):
        header_dialog, name_file = self.get_game_data(value_white, value_black, pgn_game)
        if header_dialog.ok:
            layout = [
                [sg.Text(text=get_translation("Analyse game"), size=(20, 1),
                         justification='center', font=self.text_font, key='INDICATOR')],
            ]

            window = sg.Window(get_translation("_wait-moment_"), layout, finalize=True)
            window.Read(timeout=50)
            pgn_file = temp_file_name
            with open(pgn_file, mode='w') as f:
                f.write('{}\n\n'.format(pgn_game))
                #print("engine used:", self.get_adviser_engine_path())
            analysed_game = annotator.start_analise(pgn_file,
                                                    self.get_adviser_engine_path(), name_file,
                                                    header_dialog.add_to_library, self,
                                                    save_file=save_file,
                                                    num_threads=self.num_threads)
            window.close()
            message = get_translation("_pgn-annotated_")
            if save_file:
                message = message + " "+get_translation("_and-saved_")
            sg.popup_ok(message, title=get_translation("_analyse-pgn_"))
            return analysed_game
        return None

    def get_adviser_engine_path(self):
        if self.engine and len(self.engine) > 0:
            return self.engine
        else:
            return self.adviser_path_and_file

    def get_game_data(self, value_white, value_black, pgn_game, display_library=True):
        header_dialog = HeaderDialog(value_white, value_black, self.sites_list, self.events_list,
                                     self.players, pgn_game, self, display_library)
        if header_dialog.ok:
            logging.info('Saving game manually')
            pgn_game.headers['Event'] = header_dialog.event
            pgn_game.headers['White'] = header_dialog.white
            pgn_game.headers['Black'] = header_dialog.black
            pgn_game.headers['Site'] = header_dialog.site
            pgn_game.headers['Date'] = header_dialog.date
            pgn_game.headers['Round'] = header_dialog.round
            pgn_game.headers['Result'] = header_dialog.result

            name_file = header_dialog.date.replace("/", "-") + "-" + header_dialog.white.replace(" ", "_") \
                        + "-" + header_dialog.black.replace(" ", "_") + ".pgn"
        else:
            name_file = None
        return header_dialog, name_file

    def check_depth_button(self, button):
        if button == 'Set Depth':
            self.set_depth_limit()
            return True
        return False

    def save_game(self):
        """ Save game in append mode """
        # store in game-directory
        with open(os.path.join(self.default_png_dir, self.pecg_auto_save_game), mode='a+') as f:
            f.write('{}\n\n'.format(self.game))

    def get_engines(self):
        """
        Get engine filenames [a.exe, b.exe, ...]

        :return: list of engine filenames
        """
        engine_list = []
        engine_path = Path('Engines')
        files = os.listdir(engine_path)
        for file in files:
            if not file.endswith('.gz') and not file.endswith('.dll') \
                    and not file.endswith('.DS_Store') \
                    and not file.endswith('.bin') \
                    and not file.endswith('.dat'):
                engine_list.append(file)

        return engine_list

    def create_board(self, is_user_white=True):
        """
        Returns board layout based on color of user. If user is white,
        the white pieces will be at the bottom, otherwise at the top.

        :param is_user_white: user has handling the white pieces
        :return: board layout
        """
        file_char_name = 'abcdefgh'
        self.board.create_initial_board()
        return self.board.create_board()

    def default_board_borders(self, window):
        """
        Set the borders of the squares to the default color
        """

        if self.is_user_white:
            # Save the board with black at the top.
            start = 0
            end = 8
            step = 1
        else:
            start = 7
            end = -1
            step = -1

        # Loop through the board and create buttons with images
        for i in range(start, end, step):
            # Row numbers at left of board is blank
            for j in range(start, end, step):
                if (i + j) % 2:
                    color = self.sq_dark_color  # Dark square
                else:
                    color = self.sq_light_color
                self.board.change_square_color(window, i, j, color)

    def build_main_layout(self, is_user_white=True):
        """
        Creates all elements for the GUI, icluding the board layout.

        :param is_user_white: if user is white, the white pieces are
        oriented such that the white pieces are at the bottom.
        :return: GUI layout
        """
        sg.ChangeLookAndFeel(self.gui_theme)
        sg.SetOptions(margins=(0, 3), border_width=1)

        # Define board
        board_layout = self.create_board(is_user_white)

        board_tab = [[sg.Column(board_layout)]]

        # on startup the menu-options are changed if default-window is not 'neutral'
        menu_def = menu_def_neutral()
        pgn = False
        if self.start_mode_used == "pgnviewer":
            menu_def = menu_def_pgnviewer()
            pgn = True
        if self.start_mode_used == "pgneditor":
            menu_def = menu_def_entry()
            pgn = True

        self.menu_elem = sg.Menu(menu_def, tearoff=False, font=("Default", str(self.menu_font_size), ''), key="_main_menu_")

        # White board layout, mode: Neutral
        layout = [
            [self.menu_elem],
#            [sg.Column(board_tab), sg.Column(board_controls)]
            [sg.Column(board_tab), sg.Column(self.get_png_layout(), key="_pgn_tab_", visible=pgn),
             sg.Column(self.get_neutral_layout(), key="_play_tab_", visible=not pgn)]
        ]

        return layout

    def get_neutral_layout(self):
        board_controls = [
            [sg.Text('{}     {}'.format(get_translation("Mode"), get_translation("Play Settings")),
                     size=(36, 1), font=self.text_font, key='_gamestatus_')],
            [sg.Frame('', [[sg.Text(get_translation('White'), size=(7, 1), font=self.text_font),
             sg.InputText('Human', font=self.text_font, key='_White_',
                          size=(24, 1)),
             sg.Text('', font=self.text_font, key='w_base_time_k',
                     size=(11, 1), relief='sunken'),
             sg.Text('', font=self.text_font, key='w_elapse_k', size=(7, 1),
                     relief='sunken')
             ],
            [sg.Text(get_translation('Black'), size=(7, 1), font=self.text_font),
             sg.InputText('Computer', font=self.text_font, key='_Black_',
                          size=(24, 1)),
             sg.Text('', font=self.text_font, key='b_base_time_k',
                     size=(11, 1), relief='sunken'),
             sg.Text('', font=self.text_font, key='b_elapse_k', size=(7, 1),
                     relief='sunken')
             ],
            [sg.Button(get_translation('Adviser'), size=(9, 1),
                       font=self.text_font, key='adviser_k', ),
             sg.Text('', font=self.text_font, key='advise_info_k', relief='sunken',
                     size=(46, 1))],
            [sg.Frame(visible=False, font=self.text_font, key='pgn_row',
                      layout=[
                          [sg.Button("previous", font=self.text_font, key='Previous'),
                           sg.Button("next", font=self.text_font, key='Next'), sg.Button("b1")]
                      ],
                      title="Cool subpanel",
                      relief=sg.RELIEF_GROOVE,
                      ),

             sg.Text('Invisible', size=(16, 1), visible=False, font=self.text_font, key='pgn_row')],
            [sg.Text(get_translation('Move list'), size=(16, 1), font=self.text_font)],
            [sg.Multiline('', do_not_clear=True, autoscroll=True, size=(52, 8),
                          font=self.text_font, key='_movelist_', disabled=True, sbar_width=self.scrollbar_width,
                          sbar_arrow_width=self.scrollbar_width)],

            [sg.Text(get_translation('Comment'), size=(12, 1), font=self.text_font)],
            [sg.Multiline('', do_not_clear=True, autoscroll=True, size=(52, 3),
                          font=self.text_font, key='comment_k', sbar_width=self.scrollbar_width,
                          sbar_arrow_width=self.scrollbar_width)],

            [sg.Text('BOOK 1, Comp games', visible=False, size=(26, 1),
                     font=self.text_font,
                     right_click_menu=['Right', ['Show::right_book1_k', 'Hide::right_book1_k']]),
             sg.Text('BOOK 2, Human games',visible=False,
                     font=self.text_font,
                     right_click_menu=['Right', ['Show::right_book2_k', 'Hide::right_book2_k']])],
            [sg.Multiline('', visible=False, do_not_clear=True, autoscroll=False, size=(23, 4),
                          font=self.text_font, key='polyglot_book1_k', disabled=True, sbar_width=self.scrollbar_width,
                          sbar_arrow_width=self.scrollbar_width),
             sg.Multiline('', visible=False, do_not_clear=True, autoscroll=False, size=(25, 4),
                          font=self.text_font, key='polyglot_book2_k', disabled=True, sbar_width=self.scrollbar_width,
                          sbar_arrow_width=self.scrollbar_width)],

            [sg.Button(get_translation('Opponent Search Info'),
                       size=(25, 1),
                       font=self.text_font, key='search_info_k', )],

            [sg.Text('', key='search_info_all_k', size=(55, 1),
                     font=self.text_font, relief='sunken')]], key="play_top_frame", visible=False)],
            [sg.Frame('', [[]], key="play_button_frame")],
        ]
        return board_controls

    def get_png_layout(self):
        variation_buttons = []
        for i in range(1, MAX_ALTERNATIVES):
            button = sg.Button('....', size=(5, 1), key="variation" + str(i))
            variation_buttons.append(button)
        board_controls = [
            [sg.Text('Mode     PGN-Viewer', size=(70, 1), font=self.text_font, key='_gamestatus_2')],
            [sg.Text(get_translation('White'), size=(7, 1), font=self.text_font),
             sg.InputText('Human', font=self.text_font, key='_White_2',
                          size=(24, 1)),
             ],
            [sg.Text(get_translation('Black'), size=(7, 1), font=self.text_font),
             sg.InputText('Computer', font=self.text_font, key='_Black_2',
                          size=(24, 1))
             ],
            [sg.Button('', font=self.text_font, key='overall_game_info',
                       size=(71, 1))],
            [sg.Listbox('', size=(70, 18), expand_y=True, enable_events=True,
                        font=self.text_font, key='_movelist_2', sbar_width=self.scrollbar_width,
                        sbar_arrow_width=self.scrollbar_width)],
            [sg.Text('{}:'.format(get_translation("Move")), size=(7, 1), font=self.text_font),
             sg.Text('', font=self.text_font, key='_currentmove_',
                     size=(13, 1), relief='sunken'),
             sg.Frame('', [variation_buttons], key="variation_frame", visible=False)],
            [sg.Push(background_color=None), sg.Frame('', [[]], key="button_frame")],
            [sg.Frame('', [[sg.Text(get_translation("Info"), size=(7, 1), font=self.text_font), sg.Text('', size=(60, 1),
                                                                                       font=self.text_font,
                                                                                       key='comment_k_2')]],
                      key="info_frame", visible=False)],

        ]
        return board_controls

    def set_default_adviser_engine(self):
        try:
            self.adviser_id_name = self.adviser_engine if len(self.adviser_engine) > 0 else \
                self.engine_id_name_list[1] \
                if len(self.engine_id_name_list) >= 2 \
                else self.engine_id_name_list[0]
            self.adviser_file, self.adviser_path_and_file = \
                self.get_engine_file(self.adviser_id_name)
        except IndexError as e:
            logging.warning(e)
        except Exception:
            logging.exception('Error in getting adviser engine!')

    def set_color_board(self, button, store):
        self.board_color = button
        """see: https://omgchess.blogspot.com/2015/09/chess-board-color-schemes.html
        Coral
Dark 112,162,163 #70A2A3 (https://www.rgbtohex.net/)
Light 177,228,185 #B1E4B9
Marine
Dark 111,115,210 #6F76D2
Light 157,172,255 #9DACFF

Emerald
Dark 111,143,114
Light 173,189,143

on chromebook only works if colors with rgb: r and b are the same!???

        """
        # Mode: Neutral, Change board to gray
        if button == 'Gray::board_color_k':
            self.sq_light_color = '#D8D8D8'
            self.sq_dark_color = '#808080'
            self.move_sq_light_color = '#e0e0ad'
            self.move_sq_dark_color = '#999966'

        if button == 'Coral::board_color_k':
            self.sq_light_color = '#B1E4B9'
            self.sq_dark_color = '#70A2A3'
            self.move_sq_light_color = '#e0e0ad'
            self.move_sq_dark_color = '#999966'
        if button == 'Marine::board_color_k':
            self.sq_light_color = '#9DACFF'
            self.sq_dark_color = '#6F76D2'
            self.move_sq_light_color = '#e0e0ad'
            self.move_sq_dark_color = '#999966'
        if button == 'Emerald::board_color_k':
            self.sq_light_color = '#A0BDA0'
            self.sq_dark_color = '#708F70'
            self.move_sq_light_color = '#e0e0e0'
            self.move_sq_dark_color = '#999999'
        # Mode: Neutral, Change board to green
        if button == 'Green::board_color_k':
            self.sq_light_color = '#b9d6b9'
            self.sq_dark_color = '#479047'
            self.move_sq_light_color = '#bae58f'
            self.move_sq_dark_color = '#6fbc55'

        # Mode: Neutral, Change board to blue
        if button == 'Blue::board_color_k':
            self.sq_light_color = '#b9d6e8'
            self.sq_dark_color = '#4790c0'
            self.move_sq_light_color = '#d2e4ba'
            self.move_sq_dark_color = '#91bc9c'

        # Mode: Neutral, Change board to brown, default
        if button == 'Brown::board_color_k':
            self.sq_light_color = '#F0D9B5'
            self.sq_dark_color = '#B58863'
            self.move_sq_light_color = '#E8E18E'
            self.move_sq_dark_color = '#B8AF4E'
        # Mode: Neutral, Change board to brown, default
        if button == 'Rosy::board_color_k':
            self.sq_light_color = 'sandy brown'
            self.sq_dark_color = 'rosy brown'
            self.move_sq_light_color = '#E8E18E'
            self.move_sq_dark_color = '#B8AF4E'

        if store:
            self.preferences.preferences["board_color"] = button
            self.preferences.save_preferences()

    def save_pgn_file_in_preferences(self, pgn_file):
        if not (pgn_file == temp_file_name):
            self.preferences.preferences["pgn_file"] = pgn_file
            self.preferences.save_preferences()

    def save_pgn_game_in_preferences(self, pgn_file):
        self.preferences.preferences["pgn_game"] = pgn_file
        self.preferences.save_preferences()

    def get_default_engine_opponent(self):

        engine_id_name = None
        try:
            engine_id_name = self.opp_id_name = self.engine_id_name_list[0]
            if len(self.opponent_engine)>0:
                engine_id_name = self.opp_id_name = self.opponent_engine
            self.opp_file, self.opp_path_and_file = self.get_engine_file(
                engine_id_name)
        except IndexError as e:
            logging.warning(e)
        except Exception:
            logging.exception('Error in getting opponent engine!')

        return engine_id_name

    def board_start_position(self, window):
        board = chess.Board()
        fen = board.fen()
        self.fen = fen
        self.board.fen_to_psg_board(window)
        self.default_board_borders(window)

    def main_loop(self):
        """
        Build GUI, read user and engine config files and take user inputs.
        Select play/pgn-editor/pgn-viewer mode (and execute it) if user selects it

        :return:
        """
        layout = self.build_main_layout(True)

        # Use white layout as default window
        self.window = sg.Window('{} {}'.format(APP_NAME, APP_VERSION),
                           layout, default_button_element_size=(12, 1),
                           auto_size_buttons=False,resizable=True,
                           icon=ico_path[platform]['pecg'], size=(self.window_width, self.window_height))
        #self.window = window

        # Read user config file, if missing create and new one
        self.check_user_config_file()

        # If engine config file (pecg_engines.json) is missing, then create it.
        self.check_engine_config_file()
        self.engine_id_name_list = self.get_engine_id_name_list()

        # Define default opponent engine, user can change this later.
        self.engine_id_name = self.get_default_engine_opponent()

        # Define default adviser engine, user can change this later.
        self.set_default_adviser_engine()

        self.init_game()

        # Initialize White and black boxes
        while True:
            _, value = self.window.Read(timeout=50)
            self.update_labels_and_game_tags(self.window, human=self.username)
            break
        self.set_neutral_button_bar(self.window)

        # Mode: Neutral, main loop starts here
        # main loop start
        while True:
            button, value = self.window.Read(timeout=50)
            button = get_button_id(button)

            # Mode: Neutral
            if button is None:
                logging.info('Quit app from main loop, X is pressed.')
                break

            # check for play-settings
            if self.check_game_setting_button(button, self.window):
                window = self.window
                continue

            # experimental code; only works if color-option in menu_def_play1-menu is switched on
            if self.check_color_button(button, self.window):
                self.default_board_borders(window)
                continue

            # check for pgn-viewer-mode
            if (button == 'PGN-Viewer' or self.start_mode_used == "pgnviewer"
                    or self.play_toolbar.get_button_id(button) == get_translation('PGN-Viewer')):
                # set window-layout and menu-def
                self.window = self.set_window_column_and_menu(button, self.window, "pgnviewer", 'PGN-Viewer', menu_def_pgnviewer())
                # execute pgn-viewer
                pgn_viewer = PGNViewer(self, self.window, play_move_string=self.get_movestring_clear())

                # 'neutral' is selected in PGNViewer-menu
                # check if window is forced close
                self.window = self.check_if_neutral_layout_must_be_applied(pgn_viewer, self.window)
                continue

            # check for pgn-editor-mode
            if (button == 'PGN-Editor' or self.start_mode_used == "pgneditor"
                    or self.play_toolbar.get_button_id(button) == get_translation('PGN-Editor')):
                # set window-layout and menu-def
                self.window = self.set_window_column_and_menu(button, self.window, "pgneditor",
                                                              'PGN-Editor', menu_def_entry())
                # execute pgn-editor

                data_entry = PgnEditor(self, self.window, play_move_string=self.get_movestring_clear())
                # 'neutral' is selected in DataEntry-menu

                # check if window is forced close
                pgn_object = data_entry
                self.window = self.check_if_neutral_layout_must_be_applied(pgn_object, self.window)
                continue

            # check for play-mode
            if (button == 'Play' or self.start_mode_used == "play" or
                    self.play_toolbar.get_button_id(button) == get_translation('Play')):

                if self.engine_id_name is None:
                    logging.warning('Install engine first!')
                    sg.Popup('Install engine first! in Engine/Manage/Install',
                             icon=ico_path[platform]['pecg'], title='Mode')
                    self.start_mode_used = ""
                    if self.is_png_layout():
                        self.window = self.swap_visible_columns_window(self.window)

                    continue

                self.play_human_computer(self.window)

                # Restore Neutral menu
                self.menu_elem.Update(menu_def_neutral())
                self.board.create_initial_board()
                self.window.find_element('_gamestatus_').Update(get_translation('Play Settings'))
                board = chess.Board()
                self.set_new_game()
                continue
                # main loop end

        self.window.Close()

    def get_movestring_clear(self):
        """
        get move-string from object, and clear it afterwards
        :return: the move-string before it is cleared
        """
        move_string = self.move_string
        self.move_string = ""
        return move_string

    def check_if_neutral_layout_must_be_applied(self, pgn_object, window):
        if not pgn_object.is_win_closed:
            # only replace this description; the start-mode-used can also contain: "play"
            if self.is_png_layout() or pgn_object.start_play_mode:
                pgn_object.start_play_mode = False
                window = self.swap_visible_columns_window(window)
            self.menu_elem.Update(menu_def_neutral())
        return window

    def set_window_column_and_menu(self, button, window, mode_name, viewer_description, menu):
        if self.play_toolbar.get_button_id(button) == get_translation(viewer_description) or button == viewer_description:
            # in neutral mode; mode pgn-viewer is selected
            self.start_mode_used = mode_name
            self.swap_visible_columns_window(window)
        # if default-window is not 'neutral', layout and menu are already changed
        if self.returning_from_playing and not self.is_png_layout():
            window = self.swap_visible_columns_window(window)
            self.returning_from_playing = False
        self.menu_elem.Update(menu)
        self.start_mode_used = self.start_mode_used.replace(mode_name, "")
        return window

    def check_game_setting_button(self, button, window):
        button_action = False
        # Mode: Neutral, Delete player
        if button == 'delete_player_k':
            self.delete_player_in_neutral_mode(window)
            button_action = True
        # Mode: Neutral, Set User time control
        if button == 'tc_k_user':
            self.set_user_time_control(window)
            button_action = True
        # Mode: Neutral, Set engine time control
        if button == 'tc_k_engine':
            self.set_engine_time_control(window)
            button_action = True
        # Mode: Neutral, set username
        if button == 'user_name_k':
            self.set_user_name(window)
            button_action = True
        # Mode: Neutral
        self.engine_id_name, is_engine_action = self.manage_engine(button, window, self.engine_id_name)
        if is_engine_action:
            button_action = True
        # Mode: Neutral, Allow user to change opponent engine settings
        if button == 'Set Engine Opponent':
            self.engine_id_name, is_engine_set = self.define_engine(self.engine_id_name, window)
            button_action = True
        # Mode: Neutral, Set Adviser engine
        if button == 'Set Engine Adviser':
            self.get_adviser_engine(window)
            button_action = True
        # Mode: Neutral
        if self.check_depth_button(button):
            button_action = True
        # Mode: Neutral, Allow user to change book settings
        if button == 'book_set_k':
            self.change_book_settings(window)
            button_action = True
        # Mode: Neutral, Settings menu
        if button == 'settings_game_k':
            self.get_settings_pgn(window)
            button_action = True
        # Mode: Neutral, Change theme
        theme_changed, self.window = self.change_theme(button, window)
        if theme_changed:
            button_action = True
        # Mode: Neutral, Change board to ['Brown', "Gray", "Green", "Blue"], default
        if self.check_color_button(button, window):
            self.default_board_borders(window)
            button_action = True
        # Mode: Neutral
        if button == 'Flip':
            window.find_element('_gamestatus_').Update(get_translation('Play Settings'))
            self.clear_elements(window)
            self.window = self.create_new_window(window, True)
            button_action = True
        # Mode: Neutral
        if button == 'GUI':
            sg.PopupScrolled(HELP_MSG, title='Help/GUI')
            button_action = True
        return button_action

    def delete_player_in_neutral_mode(self, window):
        win_title = 'Tools/Delete Player'
        player_list = []
        sum_games = 0
        layout = [
            [sg.Text('PGN', font=self.text_font, size=(4, 1)),
             sg.Input(size=(40, 1), font=self.text_font, key='pgn_k'), sg.FileBrowse()],
            [sg.Button('Display Players', font=self.text_font, size=(48, 1))],
            [sg.Text('Status:', font=self.text_font, size=(48, 1), key='status_k', relief='sunken')],
            [sg.T('Current players in the pgn', font=self.text_font, size=(43, 1))],
            [sg.Listbox([], font=self.text_font, size=(53, 10), key='player_k')],
            [sg.Button('Delete Player', font=self.text_font), sg.Cancel(font=self.text_font)]
        ]
        window.Hide()
        w = sg.Window(win_title, layout,
                      icon=ico_path[platform]['pecg'])
        while True:
            e, v = w.Read(timeout=10)
            if e is None or e == 'Cancel':
                break
            if e == 'Display Players':
                pgn = v['pgn_k']
                if pgn == '':
                    logging.info('Missing pgn file.')
                    sg.Popup(
                        'Please locate your pgn file by pressing \
                        the Browse button followed by Display Players.',
                        title=win_title,
                        icon=ico_path[platform]['pecg']
                    )
                    break

                t1 = time.perf_counter()
                que = queue.Queue()
                t = threading.Thread(
                    target=self.get_players,
                    args=(pgn, que,),
                    daemon=True
                )
                t.start()
                msg = None
                while True:
                    e1, _ = w.Read(timeout=100)
                    w.Element('status_k').Update(
                        'Display Players: processing ...')
                    try:
                        msg = que.get_nowait()
                        elapse = int(time.perf_counter() - t1)
                        w.Element('status_k').Update(
                            'Players are displayed. Done! in ' +
                            str(elapse) + 's')
                        break
                    except Exception:
                        continue
                t.join()
                player_list = msg[0]
                sum_games = msg[1]
                w.Element('player_k').Update(sorted(player_list))

            if e == 'Delete Player':
                try:
                    player_name = v['player_k'][0]
                except IndexError as e:
                    logging.info(e)
                    sg.Popup('Please locate your pgn file by '
                             'pressing the Browse button followed by Display Players.',
                             title=win_title,
                             icon=ico_path[platform]['pecg'])
                    break
                except Exception:
                    logging.exception('Failed to get player.')
                    break

                t1 = time.perf_counter()
                que = queue.Queue()
                t = threading.Thread(
                    target=self.delete_player,
                    args=(player_name, v['pgn_k'], que,),
                    daemon=True
                )
                t.start()
                msg = None
                while True:
                    e1, _ = w.Read(timeout=100)
                    w.Element('status_k').Update(
                        'Status: Delete: processing ...')
                    try:
                        msg = que.get_nowait()
                        if msg == 'Done':
                            elapse = int(time.perf_counter() - t1)
                            w.Element('status_k').Update(
                                player_name + ' was deleted. Done! '
                                              'in ' + str(elapse) + 's')
                            break
                        else:
                            w.Element('status_k').Update(
                                msg + '/' + str(sum_games))
                    except Exception:
                        continue
                t.join()

                # Update player list in listbox
                player_list.remove(player_name)
                w.Element('player_k').Update(sorted(player_list))
        w.Close()
        window.UnHide()

    def set_user_time_control(self, window):
        win_title = '{}/{}'.format(get_translation("Time"), get_translation("User"))
        layout = [
            [sg.T(get_translation('Base time (minute)'), font=self.text_font, size=(20, 1)),
             sg.Input(self.human_base_time_ms / 60 / 1000, font=self.text_font,
                      key='base_time_k', size=(8, 1))],
            [sg.T(get_translation('Increment (second)'), font=self.text_font, size=(20, 1)),
             sg.Input(self.human_inc_time_ms / 1000, font=self.text_font, key='inc_time_k',
                      size=(8, 1))],
            [sg.T(get_translation('Period moves'), font=self.text_font, size=(16, 1), visible=False),
             sg.Input(self.human_period_moves, font=self.text_font, key='period_moves_k',
                      size=(8, 1), visible=False)],
            [sg.Radio(get_translation('Fischer'), 'tc_radio', font=self.text_font, key='fischer_type_k',
                      default=True if self.human_tc_type == 'fischer' else False),
             sg.Radio(get_translation('Delay'), 'tc_radio', font=self.text_font, key='delay_type_k',
                      default=True if self.human_tc_type == 'delay' else False)],
            [sg.OK(font=self.text_font), sg.Cancel(font=self.text_font)]
        ]
        window.Hide()
        w = sg.Window(win_title, layout,
                      icon=ico_path[platform]['pecg'])
        while True:
            e, v = w.Read(timeout=10)
            if e is None:
                break
            if e == 'Cancel':
                break
            if e == 'OK':
                base_time_ms = int(1000 * 60 * float(v['base_time_k']))
                inc_time_ms = int(1000 * float(v['inc_time_k']))
                period_moves = int(v['period_moves_k'])

                tc_type = 'fischer'
                if v['fischer_type_k']:
                    tc_type = 'fischer'
                elif v['delay_type_k']:
                    tc_type = 'delay'

                self.human_base_time_ms = base_time_ms
                self.human_inc_time_ms = inc_time_ms
                self.human_period_moves = period_moves
                self.human_tc_type = tc_type
                break
        w.Close()
        window.UnHide()

    def set_engine_time_control(self, window):
        win_title = '{}/{}'.format(get_translation("Time"), get_translation("Engine"))
        layout = [
            [sg.T(get_translation('Base time (minute)'), font=self.text_font, size=(20, 1)),
             sg.Input(self.engine_base_time_ms / 60 / 1000,
                      key='base_time_k', font=self.text_font, size=(8, 1))],
            [sg.T(get_translation('Increment (second)'), font=self.text_font, size=(20, 1)),
             sg.Input(self.engine_inc_time_ms / 1000, font=self.text_font,
                      key='inc_time_k',
                      size=(8, 1))],
            [sg.T(get_translation('Period moves'), font=self.text_font, size=(16, 1), visible=False),
             sg.Input(self.engine_period_moves, font=self.text_font,
                      key='period_moves_k', size=(8, 1),
                      visible=False)],
            [sg.Radio(get_translation('Fischer'), 'tc_radio', font=self.text_font, key='fischer_type_k',
                      default=True if
                      self.engine_tc_type == 'fischer' else False),
             sg.Radio(get_translation('Time Per Move'), 'tc_radio', font=self.text_font, key='timepermove_k',
                      default=True if
                      self.engine_tc_type == 'timepermove' else
                      False, tooltip='Only base time will be used.')
             ],
            [sg.OK(font=self.text_font), sg.Cancel(font=self.text_font)]
        ]
        window.Hide()
        w = sg.Window(win_title, layout,
                      icon=ico_path[platform]['pecg'])
        while True:
            e, v = w.Read(timeout=10)
            if e is None:
                break
            if e == 'Cancel':
                break
            if e == 'OK':
                base_time_ms = int(
                    1000 * 60 * float(v['base_time_k']))
                inc_time_ms = int(1000 * float(v['inc_time_k']))
                period_moves = int(v['period_moves_k'])

                tc_type = 'fischer'
                if v['fischer_type_k']:
                    tc_type = 'fischer'
                elif v['timepermove_k']:
                    tc_type = 'timepermove'

                self.engine_base_time_ms = base_time_ms
                self.engine_inc_time_ms = inc_time_ms
                self.engine_period_moves = period_moves
                self.engine_tc_type = tc_type
                break
        w.Close()
        window.UnHide()

    def set_user_name(self, window):
        win_title = '{}/{}'.format(get_translation("User"), get_translation("username"))
        layout = [
            [sg.Text(get_translation('Current username')+': {}'.format(
                self.username))],
            [sg.T(get_translation('Name'), size=(4, 1)), sg.Input(
                self.username, key='username_k', size=(32, 1))],
            [sg.OK(font=self.text_font), sg.Cancel(font=self.text_font)]
        ]
        window.Hide()
        w = sg.Window(win_title, layout,
                      icon=ico_path[platform]['pecg'])
        while True:
            e, v = w.Read(timeout=10)
            if e is None:
                break
            if e == 'Cancel':
                break
            if e == 'OK':
                backup = self.username
                username = self.username = v['username_k']
                if username == '':
                    username = backup
                self.update_user_config_file(username)
                break
        w.Close()
        window.UnHide()
        self.update_labels_and_game_tags(window, human=self.username)

    def change_book_settings(self, window):
        # Backup current values, we will restore these value in case
        # the user presses cancel or X button
        current_is_use_gui_book = self.is_use_gui_book
        current_is_random_book = self.is_random_book
        current_max_book_ply = self.max_book_ply
        layout = [
            [sg.Text(get_translation('This is the book used by your engine opponent.'), font=self.text_font)],
            [sg.T(get_translation('Book File'), font=self.text_font, size=(15, 1)),
             sg.T(self.gui_book_file, font=self.text_font, size=(36, 1), relief='sunken')],
            [sg.T(get_translation('Max Ply'), font=self.text_font, size=(15, 1)),
             sg.Spin([t for t in range(1, 33, 1)], font=self.text_font,
                     initial_value=self.max_book_ply,
                     size=(6, 1), key='book_ply_k')],
            [sg.CBox(get_translation('Use book'), font=self.text_font, key='use_gui_book_k',
                     default=self.is_use_gui_book)],
            [sg.Radio(get_translation('Best move'), 'Book Radio', font=self.text_font,
                      default=False if self.is_random_book else True),
             sg.Radio(get_translation('Random move'), 'Book Radio', font=self.text_font,
                      key='random_move_k',
                      default=True if self.is_random_book else False)],
            [sg.OK(font=self.text_font), sg.Cancel(font=self.text_font)],
        ]
        w = sg.Window(BOX_TITLE + '/'+get_translation('Set Book'), layout,
                      icon=ico_path[platform]['pecg'])
        window.Hide()
        while True:
            e, v = w.Read(timeout=10)

            # If user presses X button
            if e is None:
                self.is_use_gui_book = current_is_use_gui_book
                self.is_random_book = current_is_random_book
                self.max_book_ply = current_max_book_ply
                logging.info('Book setting is exited.')
                break

            if e == 'Cancel':
                self.is_use_gui_book = current_is_use_gui_book
                self.is_random_book = current_is_random_book
                self.max_book_ply = current_max_book_ply
                logging.info('Book setting is cancelled.')
                break

            if e == 'OK':
                self.max_book_ply = int(v['book_ply_k'])
                self.is_use_gui_book = v['use_gui_book_k']
                self.is_random_book = v['random_move_k']
                logging.info('Book setting is OK')
                break
        window.UnHide()
        w.Close()

    def play_human_computer(self, window):
        # Change menu from Neutral to Play
        self.menu_elem.Update(menu_def_play())
        self.start_mode_used = self.start_mode_used.replace("play", "")
        self.board.create_initial_board()
        board = chess.Board()
        self.display_button_bar()
        window.find_element("play_top_frame").Update(visible=True)
        while True:
            _, value = window.Read(timeout=100)
            self.mode_indicator = '{}     {}'.format(get_translation("Mode"), get_translation("Play"))

            window.find_element('_gamestatus_').Update(self.mode_indicator)
            window.find_element('_movelist_').Update(disabled=False)
            window.find_element('_movelist_').Update('', disabled=True)

            start_new_game = self.play_game(window, board)
            window.find_element('_gamestatus_').Update('{}     {}'.format(get_translation("Mode"), get_translation("Play")))

            self.board.create_initial_board()
            self.board.redraw_board(window)
            board = chess.Board()
            self.set_new_game()

            if not start_new_game:
                break

    def get_settings_pgn(self, window):
        font_sizes = ['10', '12', '20', '32']
        skill_levels = ['1','2','3','4','5','6']
        languages = ['en', 'nl']
        font_ui_sizes = ['10', '12', '20', '32']
        field_sizes = ['60', '70', '80', '90', '100', '105']
        win_title = 'Settings/Game'
        layout = [

            [sg.CBox(get_translation('Save time left in game notation'), font=self.text_font,
                     key='save_time_left_k',
                     default=self.is_save_time_left,
                     tooltip='[%clk h:mm:ss] will appear as\n' +
                             'move comment and is shown in move\n' +
                             'list and saved in pgn file.')],
            [[sg.Text(get_translation("Start mode")+":", size=(16, 1), font=self.text_font),
              sg.Combo(["", "pgnviewer", "pgneditor"], font=self.text_font, expand_x=True,
                       enable_events=True,
                       readonly=False, default_value=str(self.start_mode), key='start_mode')]],
            # [sg.CBox('Start in game-entry-mode', font=self.text_font,
            #          key='start_mode',
            #          default=self.preferences.preferences['start_mode'])],
            [[sg.Text(get_translation("Menu-font-size")+":", size=(16, 1), font=self.text_font),
              sg.Combo(font_sizes, font=self.text_font, expand_x=True, enable_events=True,
                       readonly=False, default_value=self.menu_font_size, key='menu_font_size')]],
            [[sg.Text(get_translation("Font-size UI")+":", size=(16, 1), font=self.text_font),
              sg.Combo(font_ui_sizes, font=self.text_font, expand_x=True, enable_events=True,
                       readonly=False, default_value=self.font_size_ui, key='font_size_ui')]],
            [[sg.Text(get_translation("Chess-field-size")+":", size=(16, 1), font=self.text_font),
              sg.Combo(field_sizes, font=self.text_font, expand_x=True, enable_events=True,
                       readonly=False, default_value=str(self.FIELD_SIZE), key='field_size')]],
            [sg.Text(get_translation('Sites'), size=(7, 1), font=self.text_font),
             sg.InputText(",".join(self.sites_list), font=self.text_font, key='sites_list_k',
                          size=(60, 1))],
            [sg.Text(get_translation('Events'), size=(7, 1), font=self.text_font),
             sg.InputText(",".join(self.events_list), font=self.text_font, key='events_list_k',
                          size=(60, 1))],
            [sg.Text(get_translation('Players'), size=(7, 1), font=self.text_font),
             sg.InputText(",".join(self.players), font=self.text_font, key='players_k',
                          size=(60, 1))],
            [sg.CBox(get_translation('Use skill-level for opponent'), font=self.text_font,
                     key='use_skill',
                     default=self.use_skill,
                     tooltip='Use the skill level while playing against the compute')],
            [[sg.Text(get_translation("Language")+":", size=(16, 1), font=self.text_font),
              sg.Combo(languages, font=self.text_font, expand_x=True, enable_events=True,
                       readonly=False, default_value=self.language, key='language')]],
            [[sg.Text(get_translation("Skill opponent")+":", size=(16, 1), font=self.text_font),
              sg.Combo(skill_levels, font=self.text_font, expand_x=True, enable_events=True,
                       readonly=False, default_value=skill_levels[self.skill_level - 1], key='skill_level')]],
            [sg.Button(get_translation("OK"), font=self.text_font),
                   sg.Button(get_translation("Cancel"), font=self.text_font)],

        ]
        w = sg.Window(win_title, layout,
                      icon=ico_path[platform]['pecg'])
        window.Hide()
        while True:
            e, v = w.Read(timeout=10)
            if e is None or e == get_translation('Cancel'):
                break
            if e == get_translation('OK'):
                self.menu_font_size = v['menu_font_size']
                self.font_size_ui = int(v['font_size_ui'])
                self.FIELD_SIZE = int(v['field_size'])
                self.is_save_time_left = v['save_time_left_k']
                self.start_mode = v['start_mode']
                self.skill_level = int(v['skill_level'])
                self.use_skill = v['use_skill']
                self.language = v['language']
                set_language( v['language'])
                self.sites_list = [s.strip() for s in v['sites_list_k'].split(",")]
                self.events_list = [s.strip() for s in v['events_list_k'].split(",")]
                self.players = [s.strip() for s in v['players_k'].split(",")]
                self.preferences.preferences["menu_font_size"] = self.menu_font_size
                self.preferences.preferences["font_size_ui"] = self.font_size_ui
                self.preferences.preferences["sites_list"] = self.sites_list
                self.preferences.preferences["events_list"] = self.events_list
                self.preferences.preferences["players"] = self.players
                self.preferences.preferences["is_save_time_left"] = self.is_save_time_left
                self.preferences.preferences["skill_level"] = self.skill_level
                self.preferences.preferences["use_skill"] = self.use_skill
                self.preferences.preferences["language"] = self.language
                self.preferences.preferences["start_mode"] = self.start_mode
                self.preferences.preferences["field_size"] = self.FIELD_SIZE
                self.preferences.save_preferences()
                break
        window.UnHide()
        w.Close()

    def manage_engine(self, button, window, engine_id_name):
        msg = None
        if button == 'Install':
            button_title = '/{}/{}/'.format(get_translation("Engine"), get_translation("Manage")) + button
            new_engine_path_file, new_engine_id_name = None, None

            install_layout = [
                [sg.Text(get_translation('Current configured engine names'), font=self.text_font)],
                [sg.Listbox(values=self.engine_id_name_list,
                            size=(48, 10), font=self.text_font, disabled=True)],
                [sg.Button(get_translation('Add'), font=self.text_font), sg.Button(get_translation('Cancel'), font=self.text_font)]
            ]

            window.Hide()
            install_win = sg.Window(title=button_title,
                                    layout=install_layout,
                                    icon=ico_path[platform]['pecg'])

            while True:
                e, v = install_win.Read(timeout=100)
                if e is None or e == get_translation('Cancel'):
                    break
                if e == get_translation('Add'):
                    button_title += '/' + e

                    add_layout = [
                        [sg.Text(get_translation('Engine'), font=self.text_font, size=(6, 1)), sg.Input(key='engine_path_file_k'),
                         sg.FileBrowse()],
                        [
                            sg.Text(get_translation('Name'), font=self.text_font, size=(6, 1)),
                            sg.Input(key='engine_id_name_k', font=self.text_font, tooltip='Input name'),
                            sg.Button(get_translation('Get Id Name'), font=self.text_font)
                        ],
                        [sg.OK(font=self.text_font), sg.Cancel(font=self.text_font)]
                    ]

                    install_win.Hide()
                    add_win = sg.Window(button_title, add_layout)
                    is_cancel_add_win = False
                    while True:
                        e1, v1 = add_win.Read(timeout=100)
                        if e1 is None:
                            is_cancel_add_win = True
                            break
                        if e1 == 'Cancel':
                            is_cancel_add_win = True
                            break
                        if e1 == get_translation('Get Id Name'):
                            new_engine_path_file = v1['engine_path_file_k']

                            # We can only get the engine id name if the engine is defined.
                            if new_engine_path_file:
                                que = queue.Queue()
                                t = threading.Thread(
                                    target=self.get_engine_id_name,
                                    args=(new_engine_path_file, que,),
                                    daemon=True
                                )
                                t.start()
                                is_update_list = False
                                while True:
                                    try:
                                        msg = que.get_nowait()
                                        break
                                    except Exception:
                                        pass
                                t.join()

                                if msg[0] == 'Done' and msg[1] is not None:
                                    is_update_list = True
                                    new_engine_id_name = msg[1]
                                else:
                                    is_cancel_add_win = True
                                    sg.Popup(
                                        get_translation("_engine_not_installed_"),
                                        title=button_title + '/'+get_translation("Get Id Name"))

                                if is_update_list:
                                    add_win.Element('engine_id_name_k').Update(
                                        new_engine_id_name)

                                # If we fail to install the engine, we exit
                                # the install window
                                if is_cancel_add_win:
                                    break

                            else:
                                sg.Popup(
                                    get_translation('Please define the engine or browse to the location of the engine file first.'),
                                    title=button_title + '/'+get_translation("Get Id Name")
                                )

                        if e1 == 'OK':
                            try:
                                new_engine_path_file = v1[
                                    'engine_path_file_k']
                                new_engine_id_name = v1['engine_id_name_k']
                                if new_engine_id_name != '':
                                    # Check if new_engine_id_name is already existing
                                    if self.is_name_exists(new_engine_id_name):
                                        sg.Popup(
                                            get_translation("_existing-engine_").format(new_engine_id_name,
                                                                                        '/{}/{}/'.format(get_translation("Engine"), get_translation("Manage"))),
                                            title=button_title,
                                            icon=ico_path[platform]['pecg']
                                        )
                                        continue
                                    break
                                else:
                                    sg.Popup(
                                        get_translation('Please input engine id name, or press {} button.'.format(
                                            get_translation("Get Id Name"))),
                                        title=button_title,
                                        icon=ico_path[platform]['pecg']
                                    )
                            except Exception:
                                logging.exception('Failed to get engine '
                                                  'path and file')

                    # Outside add window while loop
                    add_win.Close()
                    install_win.UnHide()

                    # Save the new configured engine to pecg_engines.json.
                    if not is_cancel_add_win:
                        que = queue.Queue()
                        t = threading.Thread(
                            target=self.add_engine_to_config_file,
                            args=(new_engine_path_file,
                                  new_engine_id_name, que,), daemon=True)
                        t.start()
                        while True:
                            try:
                                msg = que.get_nowait()
                                break
                            except Exception:
                                continue
                        t.join()

                        if msg == 'Failure':
                            sg.Popup(
                                'Failed to add {} in config file!'.format(new_engine_id_name),
                                title=button_title,
                                icon=ico_path[platform]['pecg']
                            )

                        self.engine_id_name_list = \
                            self.get_engine_id_name_list()
                    break

            install_win.Close()
            window.UnHide()

            # Define default engine opponent and adviser
            if engine_id_name is None:
                engine_id_name = self.get_default_engine_opponent()
            if self.adviser_id_name is None:
                self.set_default_adviser_engine()

            self.update_labels_and_game_tags(window, human=self.username)

            return engine_id_name, True
        # Mode: Neutral
        if button == 'Edit':
            button_title = '/{}/{}/'.format(get_translation("Engine"), get_translation("Manage")) + button
            opt_name = []
            ret_opt_name = []
            engine_path_file, engine_id_name = None, None

            edit_layout = [
                [sg.Text(get_translation('Current configured engine names'), font=self.text_font)],
                [
                    sg.Listbox(
                        values=self.engine_id_name_list, font=self.text_font,
                        size=(48, 10),
                        key='engine_id_name_k'
                    )
                ],
                [sg.Button(get_translation('Modify'), font=self.text_font), sg.Button(get_translation('Cancel'), font=self.text_font)]
            ]

            window.Hide()
            edit_win = sg.Window(
                button_title,
                layout=edit_layout,
                icon=ico_path[platform]['pecg']
            )
            is_cancel_edit_win = False
            while True:
                e, v = edit_win.Read(timeout=100)
                if e is None or e == get_translation('Cancel'):
                    is_cancel_edit_win = True
                    break
                if e == get_translation('Modify'):
                    option_layout, option_layout2 = [], []
                    button_title += '/' + e

                    try:
                        orig_idname = engine_id_name = v['engine_id_name_k'][0]
                    except Exception:
                        sg.Popup('{} {}.'.format(get_translation('Please select an engine to'),get_translation('Modify')),
                                 title='/{}/{}'.format(get_translation("Manage"), get_translation("Modify")),
                                 icon=ico_path[platform]['pecg'])
                        continue

                    # Read engine config file
                    with open(self.engine_config_file, 'r') as json_file:
                        data = json.load(json_file)

                    # First option that can be set is the config name
                    option_layout.append(
                        [sg.Text('name', size=(4, 1)),
                         sg.Input(engine_id_name, size=(38, 1),
                                  key='string_name_k')])
                    opt_name.append(['name', 'string_name_k'])

                    for p in data:
                        name = p['name']
                        path = p['workingDirectory']
                        file = p['command']
                        engine_path_file = Path(path, file)
                        option = p['options']

                        if name == engine_id_name:
                            num_opt = len(option)
                            opt_cnt = 0
                            for o in option:
                                opt_cnt += 1
                                name = o['name']
                                value = o['value']
                                type_ = o['type']

                                if type_ == 'spin':
                                    min_ = o['min']
                                    max_ = o['max']

                                    key_name = type_ + '_' + name.lower() + '_k'
                                    opt_name.append([name, key_name])

                                    ttip = 'min {} max {}'.format(min_, max_)
                                    spin_layout = \
                                        [sg.Text(name, size=(16, 1)),
                                         sg.Input(value, size=(8, 1),
                                                  key=key_name,
                                                  tooltip=ttip)]
                                    if num_opt > 10 and opt_cnt > num_opt // 2:
                                        option_layout2.append(spin_layout)
                                    else:
                                        option_layout.append(spin_layout)

                                elif type_ == 'check':
                                    key_name = type_ + '_' + name.lower() + '_k'
                                    opt_name.append([name, key_name])

                                    check_layout = \
                                        [sg.Text(name, size=(16, 1)),
                                         sg.Checkbox('', key=key_name,
                                                     default=value)]
                                    if num_opt > 10 and opt_cnt > num_opt // 2:
                                        option_layout2.append(check_layout)
                                    else:
                                        option_layout.append(check_layout)

                                elif type_ == 'string':
                                    key_name = type_ + '_' + name + '_k'
                                    opt_name.append([name, key_name])

                                    # Use FolderBrowse()
                                    if 'syzygypath' in name.lower():
                                        sy_layout = \
                                            [sg.Text(name, size=(16, 1)),
                                             sg.Input(value,
                                                      size=(12, 1),
                                                      key=key_name),
                                             sg.FolderBrowse()]

                                        if num_opt > 10 and opt_cnt > num_opt // 2:
                                            option_layout2.append(sy_layout)
                                        else:
                                            option_layout.append(sy_layout)

                                    # Use FileBrowse()
                                    elif 'weightsfile' in name.lower():
                                        weight_layout = \
                                            [sg.Text(name, size=(16, 1)),
                                             sg.Input(value,
                                                      size=(12, 1),
                                                      key=key_name),
                                             sg.FileBrowse()]

                                        if num_opt > 10 and opt_cnt > num_opt // 2:
                                            option_layout2.append(
                                                weight_layout)
                                        else:
                                            option_layout.append(
                                                weight_layout)
                                    else:
                                        str_layout = \
                                            [sg.Text(name, size=(16, 1)),
                                             sg.Input(value, size=(16, 1),
                                                      key=key_name)]

                                        if num_opt > 10 and opt_cnt > num_opt // 2:
                                            option_layout2.append(
                                                str_layout)
                                        else:
                                            option_layout.append(
                                                str_layout)

                                elif type_ == 'combo':
                                    key_name = type_ + '_' + name + '_k'
                                    opt_name.append([name, key_name])
                                    var = o['choices']
                                    combo_layout = [
                                        sg.Text(name, size=(16, 1)),
                                        sg.Combo(var, default_value=value,
                                                 size=(12, 1),
                                                 key=key_name)]
                                    if num_opt > 10 and opt_cnt > num_opt // 2:
                                        option_layout2.append(combo_layout)
                                    else:
                                        option_layout.append(combo_layout)
                            break

                    option_layout.append([sg.OK(font=self.text_font), sg.Cancel(font=self.text_font)])

                    if len(option_layout2) > 1:
                        tab1 = [[sg.Column(option_layout)]]
                        tab2 = [[sg.Column(option_layout2)]]
                        modify_layout = [[sg.Column(tab1), sg.Column(tab2)]]
                    else:
                        modify_layout = option_layout

                    edit_win.Hide()
                    modify_win = sg.Window(button_title,
                                           layout=modify_layout,
                                           icon=ico_path[platform]['pecg'])
                    is_cancel_modify_win = False
                    while True:
                        e1, v1 = modify_win.Read(timeout=100)
                        if e1 is None or e1 == 'Cancel':
                            is_cancel_modify_win = True
                            break
                        if e1 == 'OK':
                            engine_id_name = v1['string_name_k']
                            for o in opt_name:
                                d = {o[0]: v1[o[1]]}
                                ret_opt_name.append(d)
                            break

                    edit_win.UnHide()
                    modify_win.Close()
                    break  # Get out of edit_win loop

            # Outside edit_win while loop

            # Save the new configured engine to pecg_engines.json file
            if not is_cancel_edit_win and not is_cancel_modify_win:
                self.update_engine_to_config_file(
                    engine_path_file, engine_id_name,
                    orig_idname, ret_opt_name)
                self.engine_id_name_list = self.get_engine_id_name_list()

            edit_win.Close()
            window.UnHide()
            return engine_id_name, True
        # Mode: Neutral
        if button == 'Delete':
            button_title = '/{}/{}/'.format(get_translation("Engine"), get_translation("Manage")) + button
            delete_layout = [
                [sg.Text(get_translation('Current configured engine names'), font=self.text_font)],
                [sg.Listbox(values=self.engine_id_name_list, font=self.text_font, size=(48, 10),
                            key='engine_id_name_k')],
                [sg.Button(get_translation('Delete'), font=self.text_font), sg.Cancel(font=self.text_font)]
            ]
            window.Hide()
            delete_win = sg.Window(
                button_title,
                layout=delete_layout,
                icon=ico_path[platform]['pecg']
            )
            is_cancel = False
            while True:
                e, v = delete_win.Read(timeout=100)
                if e is None or e == 'Cancel':
                    is_cancel = True
                    break
                if e == get_translation('Delete'):
                    try:
                        engine_id_name = v['engine_id_name_k'][0]
                    except Exception:
                        sg.Popup('{} {}.'.format(get_translation('Please select an engine to'),get_translation('Delete')),
                                 title=button_title,
                                 icon=ico_path[platform]['pecg'])
                        continue
                    with open(self.engine_config_file, 'r') as json_file:
                        data = json.load(json_file)

                    for i in range(len(data)):
                        if data[i]['name'] == engine_id_name:
                            if engine_id_name == self.adviser_engine:
                                self.adviser_engine = ""
                                self.preferences.preferences["adviser_engine"] = ""
                                self.preferences.save_preferences()

                            logging.info('{} is found for deletion.'.format(
                                engine_id_name))
                            data.pop(i)
                            break

                    # Save data to pecg_engines.json
                    with open(self.engine_config_file, 'w') as h:
                        json.dump(data, h, indent=4)

                    break

            # Save the new configured engine to pecg_engines.json file
            if not is_cancel:
                self.engine_id_name_list = self.get_engine_id_name_list()

            delete_win.Close()
            window.UnHide()

            return engine_id_name, True
        return engine_id_name, False

    def get_adviser_engine(self, window):
        current_adviser_engine_file = self.adviser_file
        current_adviser_path_and_file = self.adviser_path_and_file
        layout = [
            [sg.T(get_translation('Current Adviser')+': {}'.format(self.adviser_id_name), font=self.text_font,
                  size=(40, 1))],
            [sg.Listbox(values=self.engine_id_name_list, font=self.text_font, size=(48, 10),
                        key='adviser_id_name_k')],
            [sg.T(get_translation('Movetime (sec)'), font=self.text_font, size=(14, 1)),
             sg.Spin([t for t in range(1, 3600, 1)], font=self.text_font,
                     initial_value=self.adviser_movetime_sec,
                     size=(8, 1), key='adviser_movetime_k')],
            [sg.OK(font=self.text_font), sg.Cancel(font=self.text_font)]
        ]
        # Create new window and disable the main window
        w = sg.Window(BOX_TITLE + '/'+get_translation('Select Adviser'), layout,
                      icon=ico_path[platform]['adviser'])
        window.Hide()
        while True:
            e, v = w.Read(timeout=10)

            if e is None or e == 'Cancel':
                self.adviser_file = current_adviser_engine_file
                self.adviser_path_and_file = current_adviser_path_and_file
                break

            if e == 'OK':
                movetime_sec = int(v['adviser_movetime_k'])
                self.adviser_movetime_sec = min(3600, max(1, movetime_sec))

                # We use try/except because user can press OK without selecting an engine
                try:
                    adviser_eng_id_name = self.adviser_id_name = v['adviser_id_name_k'][0]
                    self.adviser_file, self.adviser_path_and_file = self.get_engine_file(
                        adviser_eng_id_name)
                    self.adviser_engine = adviser_eng_id_name
                    self.preferences.preferences["adviser_engine"] = adviser_eng_id_name
                    self.preferences.save_preferences()
                    # set the engine-name passed by the command-line to None
                    self.engine = None
                except IndexError:
                    logging.info('User presses OK but did not select an engine')
                except Exception:
                    logging.exception('Failed to set engine.')
                break
        window.UnHide()
        w.Close()

    def define_engine(self, engine_id_name, window):
        current_engine_file = self.opp_file
        current_engine_id_name = self.opp_id_name
        logging.info('Backup current engine list and file.')
        logging.info('Current engine file: {}'.format(
            current_engine_file))
        layout = [
            [sg.T(get_translation('Current Opponent')+': {}'.format(self.opp_id_name), size=(40, 1))],
            [sg.Listbox(values=self.engine_id_name_list, size=(48, 10), key='engine_id_k')],
            [sg.OK(font=self.text_font), sg.Cancel(font=self.text_font)]
        ]
        # Create new window and disable the main window
        w = sg.Window(BOX_TITLE + '/'+get_translation('Select opponent'), layout,
                      icon=ico_path[platform]['enemy'])
        window.Hide()
        while True:
            e, v = w.Read(timeout=10)

            if e is None or e == 'Cancel':
                # Restore current engine list and file
                logging.info('User cancels engine selection. ' +
                             'We restore the current engine data.')
                self.opp_file = current_engine_file
                logging.info('Current engine data were restored.')
                logging.info('current engine file: {}'.format(
                    self.opp_file))
                break

            if e == 'OK':
                # We use try/except because user can press OK without
                # selecting an engine
                try:
                    engine_id_name = self.opp_id_name = v['engine_id_k'][0]
                    self.opp_file, self.opp_path_and_file = self.get_engine_file(
                        engine_id_name)
                    self.opponent_engine = engine_id_name
                    self.preferences.preferences["opponent_engine"] = engine_id_name
                    self.preferences.save_preferences()

                except IndexError:
                    logging.info('User presses OK but did not select '
                                 'an engine.')
                except Exception:
                    logging.exception('Failed to set engine.')
                finally:
                    if current_engine_id_name != self.opp_id_name:
                        logging.info('User selected a new opponent {'
                                     '}.'.format(self.opp_id_name))
                break
        window.UnHide()
        w.Close()
        # Update the player box in main window
        self.update_labels_and_game_tags(window, human=self.username)
        is_engine_set = True
        return engine_id_name, is_engine_set

    def change_theme(self, button, window):
        if button in GUI_THEME:
            self.gui_theme = button
            self.preferences.preferences["gui_theme"] = self.gui_theme
            self.preferences.save_preferences()
            window = self.create_new_window(window)
            self.window = window
            theme_changed = True
            return theme_changed, window
        return False, window

    def check_color_button(self, button, window):
        for color in board_colors:
            last = color.split("::")[1]
            if last == button:
                button = color.split("::")[0]+"::board_color_k"

        for color in [c.split("::")[0] for c in board_colors]:
            if button == color + '::board_color_k':
                self.set_color_board(button, True)
                self.board.redraw_board(window)
                return True
        return False

    def is_png_layout(self):
        """
        check if current defined layout is png_layout
        the png-column is visible yes/no
        :return: boolean
        """
        return self.window.find_element("_pgn_tab_").visible


def main(engine, start_mode, max_depth, threads):
    engine_config_file = 'pecg_engines.json'
    user_config_file = 'pecg_user.json'

    pecg_book = 'Book/pecg_book.bin'
    book_from_computer_games = 'Book/computer.bin'
    book_from_human_games = 'Book/human.bin'

    is_use_gui_book = True
    is_random_book = True  # If false then use best book move
    max_book_ply = 8
    theme = 'Reddit'

    pecg = EasyChessGui(theme, engine_config_file, user_config_file,
                        pecg_book, book_from_computer_games,
                        book_from_human_games, is_use_gui_book, is_random_book,
                        max_book_ply, engine, max_depth, start_mode, num_threads=threads)

    pecg.main_loop()


if __name__ == "__main__":
    args = parse_args()
    engine = args.engine.split()[0]
    start_mode = args.startmode.split()[0]
    max_depth = args.maxdepth
    threads = args.threads
    main(engine, start_mode, max_depth, threads)
