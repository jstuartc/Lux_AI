from lux.game import Game
from lux.game_objects import Player, CityTile
from typing import List
from hive2 import Hive
import math


def best_city_to_produce_from(player: Player, city_list: List[CityTile], hive_list: List[Hive]):
    """Rank the hives from the cities"""
    city_score_dict = {}  # Key is score and value is the city tile
    for city_tile in city_list:
        best_score = - math.inf
        for hive in hive_list:
            score = hive.hive_score(city_tile.pos, False)
            if score > best_score:
                best_score = score
        city_score_dict[city_tile] = best_score

    return city_score_dict


def city_action(game_state: Game, player: Player, hive_list: List[Hive]):
    city_list = player.cities.values()
    actions = []

    actionable_city_tile = []
    for city in city_list:
        for city_tile in city.citytiles:
            if city_tile.can_act():
                actionable_city_tile.append(city_tile)

    worker_numbers = len(player.units)
    city_numbers = player.city_tile_count

    """
    Get a dictionary which ranks the best places to build a worker
    WARNING!!!!!! IT WONT WORK FOR THE 2nd WORKER
    """
    the_dict = best_city_to_produce_from(player, actionable_city_tile, hive_list)
    sorted_actionable_cities = sorted(actionable_city_tile, key=lambda tile: the_dict[tile])

    for city_tile in sorted_actionable_cities:
        if worker_numbers < city_numbers:  # Workers to be produced if less
            actions.append(city_tile.build_worker())
            worker_numbers += 1
        else:
            if not player.researched_uranium():
                actions.append(city_tile.research())

    return actions
