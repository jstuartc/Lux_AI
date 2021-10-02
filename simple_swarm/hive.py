from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from collections import defaultdict
from typing import DefaultDict, List


class Hive:
    """
    resource_type: wood,coal,uranium
    number_of workers: int
    workers: list(Workers)
    cities: list(cities)
    resource_tile_numbers
    resource_tiles
    """

    def __init__(self, initial_tile, game, player):
        """Create a Hive by giving it a resource tile"""
        self.player = player
        self.game = game
        self.worker_numbers = 0
        self.workers : List[str] = [] # Worker ID
        self.city_numbers = 0
        self.city_locations = [] # cells
        self.resource_tile_number = 1
        self.resource_tiles = [initial_tile.pos]
        self.resource_type = initial_tile.resource.type
        self._add_tiles(initial_tile)
        self._add_city_locations()
        self.empty_city_locations = self.city_locations.copy()
        self.missions = []
        if self.resource_type == "wood":
            self.active = True

    def _add_tiles(self, tile):
        """recursive function
        takes a resource tile and will find the resource tiles around it and
        add it to the resource tiles list"""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if (tile.pos.x + dx > -1) and (tile.pos.x + dx < self.game.map_width):
                    if (tile.pos.y + dy > -1) and (tile.pos.y + dy < self.game.map_height):
                        new_tile = self.game.map.get_cell(tile.pos.x + dx, tile.pos.y + dy)
                        if new_tile.resource.type == self.resource_type:
                            if new_tile.pos not in self.resource_tiles:
                                self.resource_tiles.append(new_tile.pos)
                                self._add_tiles(new_tile)

    def _cell_not_in_list(self, position, list_to_check):
        for tile in list_to_check:
            if position == tile.pos:
                return False
        return True

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
                            self.city_locations.append(new_tile)
            for dy in [-1, 1]:  # Check vertical tiles North and South
                if (tile.pos.y + dy > -1) and (tile.pos.y + dy < self.game.map_height):
                    new_tile = self.game.map.get_cell(tile.pos.x, tile.pos.y + dy)
                    if new_tile.resource is None:
                        if new_tile.pos not in self.city_locations:
                            self.city_locations.append(new_tile)

    def add_worker(self,worker):
        """Assigns a worker to the hive, and sets it to travel to the nearest (empty) city location (or any)"""
        pass

    def assign_mission(self):
        """Assigns workers to either one of two jobs"""
        cities_needed = len(self.empty_city_locations)
        if cities_needed ==0:
            for worker in self.workers:
                if worker.travelling:
                worker.job = "Guard"
        elif cities_needed > len(self.workers):
            for worker in self.workers:
                worker.job = "Build"
        else:
            for worker in self.workers:
                """NEED TO ADD IN TRAVEL SECTION"""

    def update(self,player,game_state):
        """
        check if hive is active
        updates city list and
        worker list"""
        self.player = player
        self.game = game_state

        alive_units = [
            id for id in self.workers if id in [u.id for u in player.units]
        ]
        self.workers = alive_units

        missing_cities = [tile for tile in self.city_locations if self.game.map.get_cell_by_pos(tile).citytile is None]
        self.empty_city_locations = missing_cities




