from lux.game import Game
from lux.game_objects import Unit, Player
from lux.game_map import Position, RESOURCE_TYPES


class Mission:

    def __init__(self, mission_type, target: Position, unit_id, night_position: Position = None,
                 resource_type: RESOURCE_TYPES = None):
        self.mission_type = mission_type
        self.target_pos = target
        self.unit_id = unit_id  # Unit id
        self.night_position = night_position
        self.resource_type = resource_type

    def update_unit(self, unit: Unit):
        self.unit_id = unit

    def check_unit_alive(self, alive_units_ids):
        if self.unit_id in alive_units_ids:
            return True
        else:
            return False

    def check_mission_complete(self, game_state: Game, unit_pos):

        if self.mission_type == "Build":
            target_pos = self.target_pos
            cell = game_state.map.get_cell_by_pos(target_pos)
            if cell.citytile is not None:
                return True

        if self.mission_type == "Guard":
            if unit_pos == self.target_pos:
                return True

        if self.mission_type == "Travel":
            if unit_pos == self.target_pos:
                return True

        else:
            return False
