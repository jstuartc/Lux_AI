from lux.game import Game
from lux.game_map import Position, DIRECTIONS, RESOURCE_TYPES
from lux.game_objects import Player, Unit, City, CityTile
from mission4 import Mission
from typing import Dict, List
import random

"""Job of this is to produce which can calculate routes for units to achieve their tasks"""

"""
Need to think about priority
Plan is to move with build people having priority, then guard then travel
"""

"""PLAN - if position occupied move left or right depending on what next movements are"""


def is_cell_survivable(game_state: Game, centre_pos: Position, city_tile_locations):
    """Checks that the cell is survivable for a unit with zero resources"""
    if centre_pos in city_tile_locations:
        return True
    if game_state.map.get_cell_by_pos(centre_pos).citytile is not None:
        return False
    check_dirs = [
        DIRECTIONS.NORTH,
        DIRECTIONS.EAST,
        DIRECTIONS.SOUTH,
        DIRECTIONS.WEST,
        DIRECTIONS.CENTER
    ]
    for direction in check_dirs:
        position = centre_pos.translate(direction, 1)
        if position.x < 0 or position.x >= game_state.map_width:
            if position.y < 0 or position.y >= game_state.map_height:
                if game_state.map.get_cell_by_pos(position).has_resource():
                    return True

    return False


def create_action(worker: Unit, mission: Mission, player: Player, game_state: Game,
                  occupied_pos: Dict[str, Position], unit_acted: Dict[str, bool], city_tile_locations: List[Position], is_night: bool, turns_until_change: int,
                  resource_type: str):

    def move_to_location(target):
        current_pos = worker.pos
        next_direction = current_pos.direction_to(target)
        next_location = current_pos.translate(next_direction, 1)

        # Checks worker is not going to die from moving location
        worker_days_surviving_at_night = worker.cargo.wood // 4 + worker.cargo.coal + worker.cargo.uranium
        if is_night is False or worker_days_surviving_at_night > 0:
            situation_safe_to_move = True
        else:
            situation_safe_to_move = False

        safe_to_move = situation_safe_to_move or is_cell_survivable(game_state, next_location, city_tile_locations)

        if next_location not in occupied_pos.values() and safe_to_move:
            action = worker.move(next_direction)
            occupied_pos[worker.id] = next_location
            unit_acted[worker.id] = True  # Doing this so that things later down the list get chance move as well
            # Too simplistic
        elif next_location in city_tile_locations and safe_to_move:
            action = worker.move(next_direction)
            occupied_pos[worker.id] = next_location
            unit_acted[worker.id] = True
        else:
            # Find the next direction to travel which is not "next_direction"
            reached_location = False
            current_pos_in_loop = current_pos
            while not reached_location:
                new_direction = current_pos_in_loop.direction_to(target)
                if new_direction != next_direction:
                    next_location = current_pos.translate(new_direction, 1)
                    safe_to_move = situation_safe_to_move or is_cell_survivable(game_state, next_location, city_tile_locations)
                    if next_location not in occupied_pos.values() and safe_to_move:
                        action = worker.move(new_direction)
                        occupied_pos[worker.id] = next_location
                        unit_acted[worker.id] = True
                        break
                new_location = current_pos_in_loop.translate(new_direction, 1)
                if new_location == target:
                    reached_location = True
                    action = None
                current_pos_in_loop = new_location

            # Maybe try a random location

        return action

    def build_action():
        action = None
        # If not night or has 4 (assuming one move away + cool down reset) days left proceed to target
        if (not is_night) or mission.resource_type == RESOURCE_TYPES.WOOD or turns_until_change <= 4 or mission.night_position\
                is None:
            if worker.can_act():
                if worker.pos == mission.target_pos and worker.can_build(game_state.map)\
                        and turns_until_change > 1 and (not is_night):
                    action = worker.build_city()
                    unit_acted[worker.id] = True
                elif worker.pos != mission.target_pos:
                    action = move_to_location(mission.target_pos)
            else:
                unit_acted[worker.id] = True
        else:
            if worker.can_act() and worker.pos != mission.night_position:
                action = move_to_location(mission.night_position)
                unit_acted[worker.id] = True
            else:
                unit_acted[worker.id] = True

        return action

    def guard_action():
        """The action is dependent on the resource type. For coal and uranium tiles, the unit will sit on the city
        tile"""
        action = None
        if worker.can_act():
            if worker.pos != mission.target_pos:
                action = move_to_location(mission.target_pos)
            else:
                new_guard_pos = find_adjacent_resource(worker.pos)
                action = move_to_location(new_guard_pos)
                unit_acted[worker.id] = True
        else:
            unit_acted[worker.id] = True
        return action

    def travel_action():
        action = None
        if worker.can_act():
            if worker.pos != mission.target_pos:  # Double checking
                action = move_to_location(mission.target_pos)
            else:
                unit_acted[worker.id] = True
        else:
            unit_acted[worker.id] = True
        return action

    def find_adjacent_resource(current_pos):
        """Finds a new position for the unit to guard. Must contain a resource and must not be occupied"""
        """Currently shuffles directions randomly but could be changed to make it more aggressive"""
        directions = ["n", "s", "e", "w"]
        random.shuffle(directions)
        for direction in directions:
            new_position = current_pos.translate(direction, 1)
            if new_position.x < 0 or new_position.x >= game_state.map_width:
                continue
            if new_position.y < 0 or new_position.y >= game_state.map_height:
                continue
            if new_position not in occupied_pos.values() and game_state.map.get_cell_by_pos(
                    new_position).has_resource():
                return new_position
        return current_pos

    if mission.mission_type == "Build":
        unit_action = build_action()
    elif mission.mission_type == "Guard":
        unit_action = guard_action()
    elif mission.mission_type == "Travel":
        unit_action = travel_action()
    else:
        unit_action = None

    return unit_action, occupied_pos, unit_acted
