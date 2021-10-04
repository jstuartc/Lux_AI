from lux.game import Game
from lux.game_objects import Player


def city_action(game_state: Game, player: Player):
    city_list = player.cities.values()
    actions = []

    actionable_city_tile = []
    for city in city_list:
        for city_tile in city.citytiles:
            if city_tile.can_act():
                actionable_city_tile.append(city_tile)

    worker_numbers = len(player.units)
    city_numbers = player.city_tile_count

    sorted_actionable_cities = actionable_city_tile  # Make this clever

    for city_tile in sorted_actionable_cities:
        if worker_numbers < city_numbers:  # Workers to be produced if less
            actions.append(city_tile.build_worker())
            worker_numbers += 1
        else:
            actions.append(city_tile.research())

    return actions
