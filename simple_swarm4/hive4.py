import math
import numpy as np

from lux.game import Game
from lux.game_map import GameMap, Cell, Position, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from typing import Dict, List
from mission4 import Mission
from lux.game_objects import Player, Position, Unit, City, CityTile


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
        if self.resource_type == RESOURCE_TYPES.WOOD:
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
            if player.research_points > 42 and self.resource_type == RESOURCE_TYPES.COAL:
                self.active = True
            elif player.research_points > 175 and self.resource_type == RESOURCE_TYPES.URANIUM:
                self.active = True
        # Checks if there is still fuel
        resource_total = 0
        for pos in self.resource_tiles:
            tile = game_state.map.get_cell_by_pos(pos)
            if tile.has_resource():
                resource_total += game_state.map.get_cell_by_pos(pos).resource.amount
        if resource_total == 0:
            self.active = False

    def _update_hive_area(self):
        """Aim is to update the hive. Removing tiles if they don't have resources and then updating city locations"""
        new_tiles: List[Position] = []  # Updates hive resource area
        for tile_pos in self.resource_tiles:
            if self.game.map.get_cell_by_pos(tile_pos).has_resource():
                new_tiles.append(tile_pos)
        self.resource_tiles = new_tiles

        self.city_locations: List[Position] = []  # locations may change depending on what resources are left so update
        self._add_city_locations()

    def remove(self, worker_id):
        self.workers.remove(worker_id)

    def remove_mission(self, worker_id):
        for mission in self.missions:
            if mission.unit_id == worker_id:
                self.missions.remove(mission)

    """Not finished with here. Need to reevaluate what to do"""

    def analyse_hive_cities(self, player: Player):
        """Not in use yet"""

        # This will also find enemy cities
        city_tiles_alive_pos = [pos for pos in self.city_locations if pos not in self.empty_city_locations]
        cities_alive: Dict[str, List] = {}
        city_time_left = {}
        #  Sort all the occupied city tiles into relevant cities and work out how long they have to live
        for city_tile_pos in city_tiles_alive_pos:
            city_id = self.game.map.get_cell_by_pos(city_tile_pos).citytile.cityid
            if city_id in cities_alive.keys():
                city_tile_pos_list = cities_alive[city_id]
                city_tile_pos_list.append(city_tile_pos)
            else:
                cities_alive[city_id] = [city_tile_pos]
                city = player.cities[city_id]
                city_time_left[city_id] = city.fuel // city.light_upkeep

    pass

    def find_travel_location(self, current_pos: Position):
        """Finds the nearest location for a potential worker to travel to"""
        # this position is the nearest city location
        closest_distance, closest_loc = math.inf, Position(0, 0)
        for city_loc in self.empty_city_locations:  # Use city locations
            distance = current_pos.distance_to(city_loc)
            if distance < closest_distance:
                closest_distance, closest_loc = distance, city_loc

        return closest_loc, closest_distance

    def rank_builder(self, builder: Unit, target_pos: Position):
        # Average way of ranking a builder suitability
        score = 0
        if builder.can_build(self.game.map) and builder.pos == target_pos:
            score = 1000
            score += target_pos.x  # To differentiate
            score += target_pos.y * 3
            return score
        if builder.can_build(self.game.map):
            score += 1
        distance = target_pos.distance_to(builder.pos)
        score -= math.exp((distance - 1))
        return score

    def update(self, player: Player, game_state: Game, unit_dict: Dict[str, Unit], step: int, is_night, home_cities_pos: List):
        """
        Need proper description here
        """
        self.game = game_state
        self._update_hive_area()

        if step % 40 == 0:  # Hard reset
            self.missions = []

        self._check_hive_active(game_state, player)
        if not self.active:
            self.workers = []
            self.missions = []
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

        self.optimise_worker_missions(unit_dict, is_night, step, home_cities_pos)

        """
        
        assigned_workers = [mission.unit_id for mission in missions_remaining]

        unassigned_workers = [unit for unit in self.workers if unit not in assigned_workers]

        cities_assigned = [mission.target_pos for mission in missions_remaining if mission.mission_type == "Build"]

        cities_unassigned = [pos for pos in self.empty_city_locations if pos not in cities_assigned]

        guard_tiles_assigned = [mission.target_pos for mission in missions_remaining if mission.mission_type == "Guard"]

        guard_tiles_unassigned = [pos for pos in self.resource_tiles if pos not in guard_tiles_assigned]

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

    def hive_score(self, worker_position):
        """Returns a score rating how much the hive should have a unit"""
        """Work on this it is real garbage"""
        if not self.active:
            return -math.inf
        hive_score = 100
        hive_score += len(self.city_locations) * 1  # Multiplier for type
        hive_score -= len(self.workers) * 2

        #  Avoid the corners
        centre_pos = Position(self.game.map_width, self.game.map_height)
        distance_from_centre = self.find_travel_location(centre_pos)[1]
        hive_score -= distance_from_centre / 8

        hive_score *= 4  # To account for the fact that the number of workers is much more important
        distance_to_target = self.find_travel_location(worker_position)[1]

        hive_score -= math.exp(distance_to_target / 2)

        #  Don't want to oversubscribe a hive
        if len(self.workers) >= len(self.city_locations) + 1:
            hive_score -= 10000
        #  To prioritise coal and uranium
        if self.resource_type == RESOURCE_TYPES.COAL:
            hive_score *= 5
        elif self.resource_type == RESOURCE_TYPES.URANIUM:
            hive_score *= 10

        return hive_score

    def nearest_city_in_list(self, target_position: Position, home_cities_pos: List):
        active_city_tiles = [pos for pos in self.city_locations if
                             pos in home_cities_pos]
        closest_distance = math.inf
        closest_position = None
        for position in active_city_tiles:
            distance = target_position.distance_to(position)
            if distance < closest_distance:
                closest_distance = distance
                closest_position = position
        return closest_position

    def optimise_worker_missions(self, unit_dict: Dict[str, Unit], is_night, step, home_cities_pos: List):
        worker_num_assigned = 0
        city_locations_to_use = self.empty_city_locations
        new_mission_list = []
        travel_units: List[Unit] = []
        for mission in self.missions:
            if mission.mission_type == "Travel":
                travel_units.append(mission.unit_id)
                new_mission_list.append(mission)
                worker_num_assigned += 1
        units_to_use: List[Unit] = [unit_dict[worker_id] for worker_id in self.workers if worker_id not in travel_units]

        x_length, y_length = len(units_to_use), len(city_locations_to_use)
        if x_length > y_length:
            short_side = y_length
            need_guards = True
        else:
            short_side = x_length
            need_guards = False

        # Build the graph
        graph = np.zeros([x_length, y_length])
        for x in range(x_length):
            for y in range(y_length):
                graph[x, y] = self.rank_builder(units_to_use[x], city_locations_to_use[y])

        # Find the index of the highest scorers, create mission remove until graph destroyed
        for a in range(short_side):
            indices = np.where(graph == np.amax(graph))
            city_loc = city_locations_to_use[indices[1][0]]
            unit = units_to_use[indices[0][0]]
            new_mission = Mission("Build", city_loc, unit.id, self.nearest_city_in_list(unit.pos, home_cities_pos), self.resource_type)
            new_mission_list.append(new_mission)
            graph = np.delete(graph, indices[0][0], 0)  # Delete row
            graph = np.delete(graph, indices[1][0], 1)  # Delete column
            units_to_use.remove(unit)
            city_locations_to_use.remove(city_loc)
            worker_num_assigned += 1
        """
        Assign a certain number of guards and a location for them to sit on.
        For wood tiles they should avoid the cities at night but for coal and uranium they should always sit on a city 
        tile
        """
        if need_guards:
            if self.resource_type == RESOURCE_TYPES.WOOD and step < 320:
                guard_tiles_unassigned = [pos for pos in self.resource_tiles]
            else:
                guard_tiles_unassigned = [pos for pos in self.city_locations if
                                          pos in home_cities_pos]
            for worker in units_to_use:
                if len(guard_tiles_unassigned) > 0:
                    if is_night or worker_num_assigned <= len(self.resource_tiles) + 1:
                        new_mission = Mission("Guard", guard_tiles_unassigned.pop(0), worker.id)
                        new_mission_list.append(new_mission)
                        worker_num_assigned += 1
                else:
                    self.remove(worker.id)

        if not is_night and worker_num_assigned > len(self.resource_tiles) + 1:
            for unit in travel_units:
                self.remove(unit.id)

        self.missions = new_mission_list
