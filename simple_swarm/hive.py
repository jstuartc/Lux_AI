import math

from lux.game import Game
from lux.game_map import GameMap, Cell, Position, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from collections import defaultdict
from typing import Dict, List
from mission import Mission
from lux.game_objects import Player, Position, Unit


class Hive:
    """
    resource_type: wood,coal,uranium
    number_of workers: int
    workers: list(Workers)
    cities: list(cities)
    resource_tile_numbers
    resource_tiles
    """

    def __init__(self, initial_tile: Cell, game: Game):
        """Create a Hive by giving it a resource tile"""
        self.game = game
        self.workers: List[str] = []  # Worker ID
        self.city_locations: List[Position] = []  # cell pos
        self.resource_tiles: List[Position] = [initial_tile.pos]
        self.resource_type = initial_tile.resource.type
        self._add_tiles(initial_tile)
        self._add_city_locations()
        self.empty_city_locations = self.city_locations.copy()
        self.missions = []
        if self.resource_type == "wood":
            self.active = True
        else:
            self.active = False

    def _add_tiles(self, tile: Cell):
        """recursive function
        takes a resource tile and will find the resource tiles around it and
        add it to the resource tiles list"""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if (tile.pos.x + dx > -1) and (tile.pos.x + dx < self.game.map_width):
                    if (tile.pos.y + dy > -1) and (tile.pos.y + dy < self.game.map_height):
                        new_tile = self.game.map.get_cell(tile.pos.x + dx, tile.pos.y + dy)
                        if new_tile.has_resource():
                            if self.resource_type == new_tile.resource.type:
                                if new_tile.pos not in self.resource_tiles:
                                    self.resource_tiles.append(new_tile.pos)
                                    self._add_tiles(new_tile)

    def _add_city_locations(self):
        """iterates through resource tiles and creates new list which contain the cells surrounding cluster where
        cities can be built """
        for position in self.resource_tiles:  # Iterates through all the hive resources
            tile = self.game.map.get_cell_by_pos(position)
            for dx in [-1, 1]:  # Check horizontal tiles West and East
                if (tile.pos.x + dx > -1) and (tile.pos.x + dx < self.game.map_width):
                    new_tile = self.game.map.get_cell(tile.pos.x + dx, tile.pos.y)
                    if new_tile.resource is None:
                        if new_tile.pos not in self.city_locations:
                            self.city_locations.append(new_tile.pos)
            for dy in [-1, 1]:  # Check vertical tiles North and South
                if (tile.pos.y + dy > -1) and (tile.pos.y + dy < self.game.map_height):
                    new_tile = self.game.map.get_cell(tile.pos.x, tile.pos.y + dy)
                    if new_tile.resource is None:
                        if new_tile.pos not in self.city_locations:
                            self.city_locations.append(new_tile.pos)

    def _check_hive_active(self, game_state: Game, player: Player):
        # Checks if research is good enough
        if not self.active:
            if player.researched_coal() and self.resource_type == "coal":
                self.active = True
            elif player.researched_uranium() and self.resource_type == "uranium":
                self.active = True
        # Checks if there is still fuel
        resource_total = 0
        for pos in self.resource_tiles:
            tile = game_state.map.get_cell_by_pos(pos)
            if tile.has_resource():
                resource_total += game_state.map.get_cell_by_pos(pos).resource.amount
        if resource_total == 0:
            self.active = False

    def remove(self, worker_id):
        self.workers.remove(worker_id)

    def find_travel_location(self, current_pos: Position):
        """Finds the nearest location for a potential worker to travel to"""
        # this position is the nearest city location
        closest_distance, closest_loc = math.inf, Position(0, 0)
        for city_loc in self.city_locations:
            distance = current_pos.distance_to(city_loc)
            if distance < closest_distance:
                closest_distance, closest_loc = distance, city_loc

        return closest_loc

    def update(self, player: Player, game_state: Game, unit_dict: Dict[str, Unit], step:int):
        """
        check if hive is active
        updates city list and
        worker list

        FILL THIS OUT

        DO SOMETHING ABOUT NIGHTTIME
        """
        self.game = game_state

        if step%40 ==0:
            self.missions = []

        self._check_hive_active(game_state, player)
        if not self.active:
            self.workers = []
            return

        alive_units = [
            unit_id for unit_id in self.workers if unit_id in [u.id for u in player.units]
        ]
        self.workers = alive_units

        missing_cities = [tile for tile in self.city_locations if self.game.map.get_cell_by_pos(tile).citytile is None]
        self.empty_city_locations = missing_cities

        missions_remaining = []
        for mission in self.missions:
            if mission.unit_id in unit_dict.keys():
                unit_position = unit_dict[mission.unit_id].pos
                if mission.check_mission_complete(game_state, unit_position) is False:
                    missions_remaining.append(mission)
        self.missions = missions_remaining
        assigned_workers = [mission.unit_id for mission in missions_remaining]

        unassigned_workers = [unit for unit in self.workers if unit not in assigned_workers]

        cities_assigned = [mission.target_pos for mission in missions_remaining if mission.mission_type == "Build"]

        cities_unassigned = [pos for pos in self.empty_city_locations if pos not in cities_assigned]

        guard_tiles_assigned = [mission.target_pos for mission in missions_remaining if mission.mission_type == "Guard"]

        guard_tiles_unassigned = [pos for pos in self.resource_tiles if pos not in guard_tiles_assigned]

        """THIS IS A BORING WAY OF ASSIGNING WORKERS. CAN DO A LOT BETTER"""

        for worker in unassigned_workers:
            if len(cities_unassigned) > 0:
                new_mission = Mission("Build", cities_unassigned.pop(0), worker)
                self.missions.append(new_mission)
            elif len(guard_tiles_unassigned) > 0:
                new_mission = Mission("Guard", guard_tiles_unassigned.pop(0), worker)
                self.missions.append(new_mission)
            else:
                self.remove(worker)  # Hive doesnt need the worker

        """
            Previous missions from last time
            Check that none are completed or unassigned
            Look at cities which need to be built and add them to mission list
            Collate empty workers
            Assign missions to empty workers
            """

    def hive_score(self, worker_position, is_night: bool):
        """Returns a score rating how much the hive should have a unit"""
        if not self.active:
            return -math.inf
        hive_score = 0
        hive_score += len(self.city_locations) * 1  # Multiplier for type
        hive_score -= len(self.workers)
        hive_score *= 4  # To account for the fact that the number of workers is much more important
        distance_to_target = self.find_travel_location(worker_position).distance_to(worker_position)
        if is_night:  # penalise more if at night, as don't want to risk travelling
            hive_score -= math.exp(distance_to_target)  # Further away the more unlikely
        else:
            hive_score -= math.exp(distance_to_target/10)
        if self.resource_type == "coal":
            hive_score *= 10
        elif self.resource_type == "uranium":
            hive_score *= 100
        return hive_score
