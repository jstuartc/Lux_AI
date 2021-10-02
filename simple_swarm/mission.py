from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from collections import defaultdict
from typing import DefaultDict, List
from lux.game_objects import Unit


class Mission:

    def __init__(self, mission_type):
        self.mission_type = mission_type
        self.target_pos = None
        self.unit = None

    def update_unit(self, unit: Unit):
        self.unit = unit
