from lux.game import Game
from lux.game_map import Position
from lux.game_objects import Player, Unit
from mission import Mission
from typing import Dict

"""Job of this is to produce which can calculate routes for units to achieve their tasks"""

"""
Need to think about priority
Plan is to move with build people having priority, then guard then travel
"""


def create_action(worker: Unit, mission: Mission, player: Player, game_state: Game,
                  occupied_pos: Dict[str, Position], unit_acted: Dict[str, bool], is_night: bool):
    def move_to_location():
        current_pos = worker.pos
        next_direction = current_pos.direction_to(mission.target_pos)
        next_location = current_pos.translate(next_direction, 1)
        if next_location not in occupied_pos.values():
            action = worker.move(next_direction)
            occupied_pos[worker.id] = next_location
            unit_acted[worker.id] = True  # Doing this so that things later down the list get chance move as well
            # Too simplistic
        else:
            action = None

        return action

    def build_action():
        action = None
        if worker.can_act():
            if worker.pos == mission.target_pos and worker.can_build(game_state.map):
                if not is_night:
                    action = worker.build_city()
                    unit_acted[worker.id] = True
            elif worker.pos != mission.target_pos:
                action = move_to_location()
        else:
            unit_acted[worker.id] = True
        return action

    def guard_action():
        action = None
        if worker.can_act():
            if worker.pos != mission.target_pos:
                action = move_to_location()
            else:
                unit_acted[worker.id] = True
        else:
            unit_acted[worker.id] = True
        return action

    def travel_action():
        action = None
        if worker.can_act():
            if worker.pos != mission.target_pos:  # Double checking
                action = move_to_location()
            else:
                unit_acted[worker.id] = True
        else:
            unit_acted[worker.id] = True
        return action

    if mission.mission_type == "Build":
        unit_action = build_action()
    elif mission.mission_type == "Guard":
        unit_action = guard_action()
    elif mission.mission_type == "Travel":
        unit_action = travel_action()
    else:
        unit_action = None

    return unit_action, occupied_pos, unit_acted
