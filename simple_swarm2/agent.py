from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES, Position
from lux.constants import Constants
from lux import annotate
from hive import Hive
from typing import List, Dict
from mission import Mission
import unit_operator as UnitOperator
import city_operator as CityOperator

DIRECTIONS = Constants.DIRECTIONS
game_state = None
hives: List[Hive]


def is_nighttime(observation):
    game_turn = observation["step"]
    game_turn = game_turn % 40
    if game_turn < 30:
        is_night = False
    else:
        is_night = True
    return is_night


def get_resource_tiles(state_of_game: Game):
    width, height = state_of_game.map.width, state_of_game.map.height
    resource_tiles: List[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = state_of_game.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    return resource_tiles


def get_best_hive(worker_pos, hive_list):
    """Determines best hive a worker should go to. Upgrade idea to optimise this for all unassigned workers"""
    pass


def agent(observation, configuration):
    global game_state
    global hives

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
        """Create some hives"""

        hives = []
        resource_tiles = get_resource_tiles(game_state)
        for tile in resource_tiles:
            not_added = True
            for hive in hives:
                if tile.pos in hive.resource_tiles:
                    not_added = False
            if not_added:
                new_hive = Hive(tile, game_state)
                hives.append(new_hive)

    else:
        game_state._update(observation["updates"])

    actions = []

    ### AI Code goes down here! ###
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height
    step = observation["step"]

    assigned_workers = []
    unit_dict = {}
    for worker in player.units:
        unit_dict[worker.id] = worker  # Makes a dict so worker object can be found with unique id
    # Update the hives + collect assigned workers ids
    workers_with_hives = []
    for hive in hives:
        hive.update(player, game_state, unit_dict, step)
        assigned_workers.append(len(hive.workers))
        workers_with_hives.extend(hive.workers)

    # Collate all the workers without hives
    workers_without_hives_id = []
    for worker in player.units:
        if worker.id not in workers_with_hives:
            workers_without_hives_id.append(worker.id)
    # Assign all the workers to hives (algorithm to determine this)
    is_night = is_nighttime(observation)
    # Set them missions to travel to hive
    for worker_id in workers_without_hives_id:
        worker_pos = unit_dict[worker_id].pos
        get_best_hive(worker_pos, hives)  # stuff below needs to be encompassed within this function
        ranked_hives_for_workers = sorted(hives, key=lambda cluster: cluster.hive_score(worker_pos, is_night))
        hive_to_join = ranked_hives_for_workers[-1]

        hive_to_join.workers.append(worker_id)
        new_mission = Mission("Travel", (hive_to_join.find_travel_location(worker_pos))[0], worker_id)
        hive_to_join.missions.append(new_mission)

    # Now need to make the units do their actions
    # Find occupied positions
    occupied_positions: Dict[str, Position] = {}
    unit_acted: Dict[str, bool] = {}
    for unit in player.units:
        occupied_positions[unit.id] = unit.pos
        unit_acted[unit.id] = False

    for enemy_unit in opponent.units:  # Adds enemy units
        occupied_positions[enemy_unit.id] = enemy_unit.pos

    for enemy_city in opponent.cities.values():  # Adds unmovable enemy cities
        num = 0
        for enemy_city_tile in enemy_city.citytiles:
            occupied_positions[enemy_city_tile.cityid + "_" + str(num)] = enemy_city_tile.pos
    for hive in hives:
        for unit_mission in hive.missions:
            unit = unit_dict[unit_mission.unit_id]  # Gives the unit
            results = UnitOperator.create_action(unit, unit_mission, player, game_state, occupied_positions, unit_acted,
                                                 is_night)
            unit_acted = results[2]
            occupied_positions = results[1]
            if unit_acted[unit.id] and results[0] is not None:  # If the unit acted append action otherwise don't
                actions.append(results[0])
    # Now do this a 2nd time, to see if more actions can be achieved

    for hive in hives:
        for unit_mission in hive.missions:
            if unit_acted[unit_mission.unit_id]:
                continue
            unit = unit_dict[unit_mission.unit_id]
            results = UnitOperator.create_action(unit, unit_mission, player, game_state, occupied_positions, unit_acted,
                                                 is_night)
            unit_acted = results[2]
            occupied_positions = results[1]
            if unit_acted[unit.id] and results[0] is not None:  # If the unit acted append action otherwise don't
                actions.append(results[0])

    # Make the cities do their actions
    city_actions = CityOperator.city_action(game_state, player, hives)
    actions.extend(city_actions)
    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))

    """
    What needs to be done every turn
    Check Hives update workers and cities and list missions
    Update mission
    Assign missions to hive workers
    Assign missions to non hive assigned workers along with hives
    
    """
    return actions
