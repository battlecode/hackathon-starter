from __future__ import print_function

'''Play battlecode hackathon games.'''

import socket
import math
import io
import time
import os
import sys
import signal
try:
    import cPickle as pickle
except:
    import pickle
try:
    import ujson as json
except:
    import json
import threading
try:
    from queue import Queue
except:
    from Queue import Queue

# pylint: disable = too-many-instance-attributes, invalid-name

GRASS = 'G'
DIRT = 'D'

THROW_RANGE = 7
THROW_HEDGE_DAMAGE = 1
THROW_ENTITY_DAMAGE = 4
THROW_ENTITY_RECOIL = 2
THROW_ENTITY_DIRT = 1

PICKUP_DELAY = 0
THROW_DELAY = 10
MOVEMENT_DELAY = 1
BUILD_DELAY = 10

# terminal formatting
_TERM_RED = '\033[31m'
_TERM_END = '\033[0m'


class Direction(object):
    ''' This is an enum for direction '''
    @staticmethod
    def directions():
        '''
        returns an array of all compass directions. It starts with SOUTH_WEST
        and proceeds counter-clockwise around the compass.
        This array is deterministic.
        Returns:
            [Direction]: An array of all compass directions
        '''
        return [Direction.SOUTH_WEST, Direction.SOUTH,
                Direction.SOUTH_EAST, Direction.EAST,
                Direction.NORTH_EAST, Direction.NORTH,
                Direction.NORTH_WEST, Direction.WEST]

    @staticmethod
    def from_delta(dx, dy):
        '''
        Initializes a Direction from a delta dx, dy. This finds the cardinal
        direction closest to the desired delta.
        Args:
            dx (int): delta in x direction
            dy (int): delta in y direction
            Both arguments cannot be zero
        Returns:
            Direction: a new Direction for that delta
        '''
        # This is code to approximate the the closest movement
        if abs(dx) >= 2.414*abs(dy):
            dy = 0
        elif abs(dy) >= 2.414*abs(dx):
            dx = 0

        if dx < 0:
            if dy < 0:
                return Direction.SOUTH_WEST
            elif dy == 0:
                return Direction.WEST
            elif dy > 0:
                return Direction.NORTH_WEST
        elif dx == 0:
            if dy < 0:
                return Direction.SOUTH
            elif dy == 0:
                raise BattlecodeError("not a valid delta: "+str(dx)+","+str(dy))
            elif dy > 0:
                return Direction.NORTH
        elif dx > 0:
            if dy < 0:
                return Direction.SOUTH_EAST
            elif dy == 0:
                return Direction.EAST
            elif dy > 0:
                return Direction.NORTH_EAST

    @staticmethod
    def all():
        '''
        returns an generator to Directions
        Returns:
            Direction: An generator of all compass directions
        '''
        for direction in Direction.directions():
            yield direction

    def __eq__(self, other):
        if type(other) is not Direction:
            return False
        return self.dx == other.dx and self.dy == other.dy

    def __init__(self, dx, dy):
        '''
        Initialize a Direction with given delta x and delta y.
        Args:
            dx (int): the delta in the x direction which has to be in range 1,0,-1
            dy (int): the delta in the y direction which has to be in range 1,0,-1

        Returns:
            Direction: A new direction with given dx and dy
        '''

        if __debug__:
            assert dx<=1 and dx >= -1, "dx is not in the right range"
            assert dy<=1 and dy >= -1, "dy is not in the right range"
        self.dx = dx
        self.dy = dy

    def rotate_left(self):
        '''
        Return a direction that is 90 degrees left from the original.
        Returns:
            Direction: A new Direction rotated 90 degrees to the left
        '''
        return direction.rotate_counter_clockwise_degrees(90)

    def rotate_right(self):
        '''
        Return a direction that is 90 degrees right from the original.
        Returns:
            Direction: A new Direction rotated 90 degrees to the right
        '''
        return direction.rotate_counter_clockwise_degrees(270)

    def rotate_opposite(self):
        '''
        Return a direction that is 180 degrees rotated from the original.
        Returns:
            Direction: A new direction opposite to the original
        '''
        return direction.rotate_counter_clockwise_degrees(180)

    def rotate_counter_clockwise_degrees(self, degrees):
        '''Rotate an angle by given number of degrees.
        Args:
             degree (int): degree to rotate counter clockwise by. Must be
                        degree%45==0

        Returns:
            Direction: a new rotated Direction
        '''
        if __debug__:
            assert degrees%45==0
        rotations = degrees//45
        index = Direction.directions().index(self)
        length = len(Direction.directions())
        return Direction.directions()[(index+rotations)%length]



'''The direction (-1, -1).'''
Direction.SOUTH_WEST = Direction(-1, -1)
'''The direction (1, -1).'''
Direction.SOUTH_EAST = Direction(1, -1)
'''The direction (0, -1).'''
Direction.SOUTH = Direction(0, -1)
'''The direction (1,  1).'''
Direction.NORTH_EAST = Direction(1,  1)
'''The direction (0,  1).'''
Direction.NORTH = Direction(0,  1)
'''The direction (-1,  1).'''
Direction.NORTH_WEST = Direction(-1,  1)
'''The direction (1, 0).'''
Direction.EAST = Direction(1, 0)
'''The direction (-1,  0).'''
Direction.WEST = Direction(-1,  0)

class Entity(object):
    '''
    An entity in the world: a Thrower, Hedge, or Statue.

    Do not modify the properties of this object; it won't do anything
    Instead, call the queue functions such as entity.queue_move() and other
    methods to tell the game to do something next turn.
    Attributes:
        id (int): the id of a entity
        type (string): String type of a given entity
        team (Team): team of entity
        hp (int): hp of entity
        cooldown_end (int): turn when cooldown is 0
        held_by (Entity): Entity holding this object. If not held held_by is
                          None
        holding (Entity): Entity held by this. If nothing is held holding is
                          None
    '''

    def __init__(self, state):
        '''
        Do not initialize new entities. This will cause errors in your
        bot.
        '''
        self._state = state

        self.id = None
        self.type = None
        self.location = None
        self.team = None
        self.hp = None
        self.cooldown_end = None
        self.holding_end = None
        self.held_by = None
        self.holding = None
        self._disintegrated = False

    def __str__(self):
        contents = '<id:{},type:{},team:{},location:{},hp:{}'.format(
            self.id, self.type, self.team, self.location, self.hp)
        if self.cooldown > 0:
            contents += ',cooldown:{}'.format(self.cooldown)
        if self.holding is not None:
            contents += ',holding:{},holding_end:{}'.format(self.holding.id, self.holding_end)
        if self.held_by is not None:
            contents += ',held_by:{}'.format(self.held_by.id)
        contents += '>'
        return contents

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        if self.holding is not None and other.holding is not None \
            and self.holding.id != other.holding.id:
            return False
        if self.held_by is not None and other.held_by is not None \
            and self.held_by.id != other.held_by.id:
            return False

        return self.id == other.id \
            and self.type == other.type \
            and self.location == other.location \
            and self.team == other.team \
            and self.hp == other.hp \
            and self.cooldown_end == other.cooldown_end \
            and self.holding_end == other.holding_end

    def __ne__(self, other):
        return not (self == other)

    def _update(self, data):
        if self.location in self._state.map._occupied and \
            self._state.map._occupied[self.location].id == self.id:
            del self._state.map._occupied[self.location]

        if __debug__:
            if self.id is not None:
                assert data['id'] == self.id
            if self.type is not None:
                assert data['type'] == self.type
            if self.team is not None:
                assert data['teamID'] == self.team.id

        self.id = data['id']
        self.type = data['type']
        self.team = self._state.teams[data['teamID']]
        self.hp = data['hp']
        self.location = Location(data['location']['x'], data['location']['y'])

        if 'cooldownEnd' in data:
            self.cooldown_end = data['cooldownEnd']
        else:
            self.cooldown_end = None

        if 'holdingEnd' in data:
            self.holding_end = data['holdingEnd']
        else:
            self.holding_end = None

        if 'heldBy' in data:
            self.held_by = self._state.entities[data['heldBy']]
        else:
            self.held_by = None
            self._state.map._occupied[self.location] = self

        if 'holding' in data:
            self.holding = self._state.entities[data['holding']]
        else:
            self.holding = None

    @property
    def cooldown(self):
        '''
         Returns:
             int: The number of turns left in this entity's cooldown. If
                there is no cooldown then is a 0.
         '''
        if self.cooldown_end is None:
            return 0
        if self.cooldown_end <= self._state.turn:
            return 0

        return self.cooldown_end - self._state.turn

    @property
    def is_thrower(self):
        '''
        Returns:
            bool: True if a entity is a THROWER else False.
        '''
        return self.type == Entity.THROWER

    @property
    def is_statue(self):
        '''
        Returns:
            bool: True if a entity is a STATUE else False.
        '''
        return self.type == Entity.STATUE

    @property
    def is_hedge(self):
        '''
        Returns:
            bool: True if a entity is a HEDGE else False.
        '''
        return self.type == Entity.HEDGE

    @property
    def is_holding(self):
        '''
        Returns:
            bool: True if holding an entity else False
        '''
        return self.holding != None

    @property
    def is_held(self):
        '''
        Returns:
            bool: True if held by an entity else False
        '''
        return self.held_by != None

    @property
    def can_act(self):
        '''
        Returns:
            bool: True if this unit can perform actions this turn.
        '''
        return self.cooldown == 0 and self.is_thrower and (self.held_by is None) and \
                not self._disintegrated

    @property
    def can_be_picked(self):
        '''
        Returns:
            bool: True if this entity can be picked up
        '''
        return self.is_thrower and not self.is_holding and not self.is_held

    def can_throw(self, direction):
        '''
        To throw an entity.
        Self has to be holding a unit and self has to be able to act.
        The adjacent square in the given direction has to be on the map and not
        occupied.

        Args:
            direction (Direction): Direction this entity desires to throw its
                                   held entity
        Returns:
            bool: True if this entity thrown in given direction
        '''
        if not self.is_holding or not self.can_act:
            return

        held = self.holding
        initial = self.location
        target_loc = Location(initial.x+direction.dx, \
                initial.y+direction.dy)
        on_map = self._state.map.location_on_map(target_loc)
        is_occupied = target_loc in self._state.map._occupied

        if ((not on_map) or is_occupied):
            return False
        return True

    def can_move(self, direction):
        '''
        Args:
            direction (Direction): Direction this entity desires to move in
        Returns:
            bool: True if a unit can move in this direction
        '''

        if not self.can_act:
            return False

        location = self.location.adjacent_location_in_direction(direction)
        on_map = self._state.map.location_on_map(location)
        is_occupied = location in self._state.map._occupied


        if ((not on_map) or is_occupied):
            return False

        return True

    def can_build(self, direction):
        '''
        This is true if there is no object in the adjacent tile in that
        direction and the tile is on the map.
        Args:
            direction (Direction): Direction this entity desires to build in
        Returns:
            bool: True if a unit can build in this direction
        '''
        return self.can_move(direction)

    def can_pickup(self, entity):
        '''
        This is true if the other entity can be picked up which means.
        The entity cannot be self.
        Self cannot be holding anything, and the entity cannot be held
        The two entities must be adjacent.
        The entity cannot has to be a THROWER.
        Args:
            entity (Entity): The entity this entity desires to pickup
        Returns:
            bool: True if this can pickup said entity
        '''

        if __debug__:
            assert isinstance(entity, Entity), 'Parameter ' + str(entity) + \
                "is not an entity"
            assert (self != entity), "You can't pickup yourself"

        # Can't pickup self or if current'y holding
        if entity == self or self.holding != None:
            return False

        # If you can't act then you can't do anything
        if not self.can_act:
            return False

        distance_to = self.location.distance_to_squared(entity.location)
        if entity == None or not entity.can_be_picked or not distance_to <=2 or \
            entity._disintegrated:
            return False
        else:
            return True

    def queue_move(self, direction):
        '''
        Queues Move to take place next turn. Throws an assertion error if cannot
        move in given direction.
        Args:
            direction (Direction): Direction this entity desires to move in
        '''
        if __debug__:
            location = self.location.adjacent_location_in_direction(direction)
            assert isinstance(location, Location), "Can't move to a non-location!"
            assert self.can_move(direction), "Invalid move cannot move in given direction"

        if(self.team != self._state.my_team):
            return

        self._state._queue({
            'action': 'move',
            'id': self.id,
            'dx': direction.dx,
            'dy': direction.dy
        })

        if self._state.speculate:
            if self.can_move(direction):
                del self._state.map._occupied[self.location]
                self.location = self.location.adjacent_location_in_direction(direction)
                if self.holding != None:
                    self.holding.location = self.location
                self._state.map._occupied[self.location] = self
                self.cooldown_end = self._state.turn + 1

    def queue_build(self, direction):
        '''
        Queues build to take place next turn. Throws an assertion error if cannot
        build in given direction.
        Args:
            direction (Direction): Direction this entity desires to build in
        '''
        location = self.location.adjacent_location_in_direction(direction)

        if __debug__:
            assert isinstance(location, Location), "Can't move to a non-location!"
            assert self.can_build(direction), "Invalid action cannot build in given direction"

        if(self.team != self._state.my_team):
            return

        self._state._queue({
            'action': 'build',
            'id': self.id,
            'dx': direction.dx,
            'dy': direction.dy
        })

        if self._state.speculate:
            if self.can_build(direction):
                self.cooldown_end = self._state.turn + 10
                self._state._build_statue(location)

    def _deal_damage(self, damage):
        if self._disintegrated:
            return

        self.hp -= damage
        if(self.hp>0):
            return

        if self.held_by == None:
            del self._state.map._occupied[self.location]

        if self.holding != None:
            self.holding.held_by = None
            self._state.map._occupied[self.location] = self.holding

        self._disintegrated = True
        del self._state.entities[self.id]

    def queue_disintegrate(self):
        '''
        Queues a disintegration, so that this object will disintegrate in the
        next turn.
        '''

        if(self.team != self._state.my_team):
            return

        self._state._queue({
            'action': 'disintegrate',
            'id': self.id
        })

        if self._state.speculate:
            self._deal_damage(self.hp+1)


    def queue_throw(self, direction):
        '''
        Queue this entity to throw a bot in given direction next turn. If this
        cannot throw, will throw an assertion.
        Args:
            direction (Direction): Direction this entity desires to throw its
                                   held entity
        '''

        if __debug__:
            assert self.holding != None, "Not Holding anything"
            assert self.can_throw(direction), "Not Enough space to throw"

        if(self.team != self._state.my_team):
            return

        self._state._queue({
            'action': 'throw',
            'id': self.id,
            'dx': direction.dx,
            'dy': direction.dy
        })

        if self._state.speculate:
            if not self.can_throw(direction):
                return

            held = self.holding
            self.holding = None
            self.holding_end = None
            initial = self.location
            target_loc = Location(initial.x+direction.dx, \
                    initial.y+direction.dy)

            for i in range(THROW_RANGE+1):
                on_map = self._state.map.location_on_map(target_loc)
                is_occupied = target_loc in self._state.map._occupied

                if ((not on_map) or is_occupied):
                    break

                target_loc = Location(target_loc.x + direction.dx, \
                        target_loc.y + direction.dy)

            target = self._state.map._occupied.get(target_loc, None)
            if(target != None):
                if(target.type == Entity.HEDGE):
                    target._deal_damage(THROW_HEDGE_DAMAGE)
                else:
                    target._deal_damage(THROW_ENTITY_DAMAGE)
                held._deal_damage(THROW_ENTITY_RECOIL)

            landing_location = Location(target_loc.x - direction.dx, \
                                        target_loc.y - direction.dy)
            held.location = landing_location
            if self._state.map.tile_at(landing_location)  == DIRT:
                held._deal_damage(THROW_ENTITY_DIRT)
            if not held._disintegrated:
                self._state.map._occupied[landing_location] = held
            held.held_by = None

            self.cooldown_end = self._state.turn + 10

    def queue_pickup(self, entity):
        '''
        Queues this to pickup entity next turn. If this cannot pickup entity
        will throw an assertion error.
        Args:
            entity (Entity): The entity this entity desires to pickup
        '''

        if(self.team != self._state.my_team):
            return

        if __debug__:
            assert self.can_pickup(entity), "Invalid Pickup Command"

        self._state._queue({
            'action': 'pickup',
            'id': self.id ,
            'pickupID': entity.id
        })

        if self._state.speculate:
            if self.can_pickup(entity):
                del self._state.map._occupied[entity.location]
                self.holding = entity
                entity.held_by = self
                entity.location = self.location
                self.holding_end = self._state.turn + 10
                self.cooldown_end = self._state.turn + 10
    def entities_within_adjacent_distance(self, distance, include_held=False,
            iterator=None):
        '''
        Returns all the entities within a certain adjacency distance from this
        bot as an generator.
        Adjacency distance is the number of adjacent blocks needed to traverse
        to get to a tile, which is equivalent to max(abs(deltax), abs(deltay))
        Args:
            distance (float): returns all entities with distance less than <=
                              distance

        Options Args:
            include_held (bool): Defaults to false. If true held units will be
                                  included in the iterator
            iterator (iterator or list): A subset of bots to iterate through.
                                         Will only search the bots in this
                                         iterator

        Returns:
            [Entities]: Returns a generator for the entities within distance of
                        of this robot
        '''

        if iterator != None:
            for entity in iterator:
                if entity is self:
                    continue
                if not include_held and entity.held_by is not None:
                    continue
                if self.location.adjacent_distance_to(entity.location) <= distance:
                    yield entity

            return

        for entity in self._state.get_entities():
            if entity is self:
                continue
            if not include_held and entity.held_by is not None:
                continue
            if self.location.adjacent_distance_to(entity.location) <= distance:
                yield entity

    def entities_within_euclidean_distance(self, distance, include_held=False,
            iterator=None):
        '''
        Returns all the entities within a certain Euclidean distance from this
        bot as an generator.
        Euclidean distance is defined as sqrt(deltax^2+deltay^2)
        Not to be confused with displacement difference, which is
        max(deltax,deltay)
        Args:
            distance (float): returns all entities with distance less than <=
                              distance

        Options Args:
            include_held (bool): Defaults to false. If true held units will be
                                  included in the iterator
            iterator (iterator or list): A subset of bots to iterate through.
                                         Will only search the bots in this
                                         iterator

        Returns:
            [Entities]: Returns a generator for the entities within distance of
                        of this robot
        '''

        if iterator != None:
            for entity in iterator:
                if entity is self:
                    continue
                if not include_held and entity.held_by is not None:
                    continue
                if self.location.distance_to(entity.location) <= distance:
                    yield entity

            return

        for entity in self._state.get_entities():
            if entity is self:
                continue
            if not include_held and entity.held_by is not None:
                continue
            if self.location.distance_to(entity.location) <= distance:
                yield entity

Entity.THROWER = 'thrower'
Entity.HEDGE = 'hedge'
Entity.STATUE = 'statue'


class Location(tuple):
    '''
    An x,y tuple representing a location in the world.
    This class is immutable.
    Attributes:
        x (int): x coordinate of location
        y (int): y coordinate of location
    '''

    __slots__ = []

    def __new__(cls, x=None, y=None):
        if isinstance(x, int) and isinstance(y, int):
            return tuple.__new__(cls, (x, y))
        elif x is not None:
            # used by pickle
            return tuple.__new__(cls, x)
        else:
            raise Exception('invalid Location x,y: {},{}'.format(x,y))

    @property
    def x(self):
        return tuple.__getitem__(self, 0)

    @property
    def y(self):
        return tuple.__getitem__(self, 1)

    def __str__(self):
        return '<{},{}>'.format(self.x, self.y)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if type(other) is not Location:
            return False
        return self[0] == other[0] and self[1] == other[1]

    __hash__ = tuple.__hash__

    def distance_to_squared(self, location):
        '''
        Return squared distance from self to other location.
        Args:
            location (Location): location we are trying to find the distance to
        Returns:
            int: Distance squared to the location
        '''
        return (location.x-self.x)**2+(location.y-self.y)**2

    def distance_to(self, location):
        '''
        Return Euclidean distance from self to other location.
        This is sqrt(deltax^2+deltay^2)
        Args:
            location (Location): location we are trying to find the distance to
        Returns:
            float: Distance squared to the location
        '''
        return math.sqrt((location.x-self.x)**2+(location.y-self.y)**2)

    def adjacent_distance_to(self, location):
        '''
        Return adjacent distance from self to other location.
        This is defined as max(abs(deltax),abs(deltay)), and is the number of
        adjacent moves needed to get to a location.
        Args:
            location (Location): location we are trying to find the distance to
        Returns:
            float: Distance squared to the location
        '''
        return max(abs(self.x-location.x), abs(self.x-location.y))

    def direction_to(self, location):
        '''
        Return a Direction from self to location. It will round to the most
        closest cardinal direction.
        Args:
            location (Location): location we are trying to find the direction to
        Returns:
            Direction: The direction to the location
        '''
        if __debug__:
            assert location != self, "Can not find direction to same location"

        dx = location.x - self.x
        dy = location.y - self.y

        return Direction.from_delta(dx, dy)

    def adjacent_location_in_direction(self, direction):
        '''
        Returns the location the is adjacent to a this in a certain direction.
        Args:
            direction (Direction): Direction that adjacency is desired
        Returns:
            Location: Location of the adjacent tile. Note this is not
                      necessarily on the map.
        '''

        return Location(self.x+direction.dx, self.y+direction.dy)

    def is_adjacent(self, location):
        '''
        Return True if a tile is adjacent to given location.
        Args:
            location (Location): location we are trying to find if adjacent
        Returns:
            bool: True if adjacent else false
        '''
        return self.distance_to_squared(location)<=2

class Sector(object):
    '''
    Representation of a sector on the map
    Attributes:
        top_left (Location): Location of top_left corner of sector. This is the
                             max y and min x of the square.
        team (Team): the team controlling this sector. If neither player team controls
                     this sector then the neutral team will control it
    '''

    def __init__(self, state, top_left):
        '''
        Do not touch this function. It initializes sectors before the game
        starts
        '''
        self._state = state
        self.top_left = top_left
        self.team = None

    def _update(self, data):
        if __debug__:
            assert self.top_left.x == data['topLeft']['x']
            assert self.top_left.y == data['topLeft']['y']

        assert data['controllingTeamID']!=-1, "We Done goof"
        self.team = self._state.teams[data['controllingTeamID']]

    def __eq__(self, other):
        if not isinstance(other, Sector):
            return False
        return self.top_left == other.top_left and self.team == other.team

    def __ne__(self, other):
        return not (self == other)

    def entities_in_sector(self):
        '''
        returns an iterator for entities in this sector
        Returns:
            Entities: entities in this sector
        '''
        for entity in self._state.get_entities():
            entity_sector = self._state.map.sector_at(entity.location)
            if(entity_sector != self):
               continue
            yield entity


class Map(object):
    '''
    A representation of the Game Map.
    Attributes:
        height (int): The max height, y.
        width (int): The max width, x.
        tiles ([string]): An array for the type of tile at each location.
        sector_size (int): The size of each sector
    '''

    def __init__(self, state, height, width, tiles, sector_size):
        self._state = state
        self.height = height
        self.width = width
        self.tiles = tiles
        self.sector_size = sector_size
        self._sectors = {}

        # occupied maps Location to Entity
        self._occupied = {}
        for x in range(0, self.width, self.sector_size):
            for y in range(0, self.height, self.sector_size):
                top_left = Location(x, y)
                self._sectors[top_left] = Sector(self._state, top_left)

    def tile_at(self, location):
        '''
        Returns the string for the tile at a given Location
        This throws an assertion error if the location is out of bounds of the
        map.
        Args:
            location (Location): the location we want to find out about
        Returns:
            String: The string describing the tile type. Either 'G' or 'D'
        '''
        assert self.location_on_map(location), "No Tile location not on map"
        return self.tiles[len(self.tiles)-location.y-1][location.x]

    def location_on_map(self, location):
        '''
        Checks whether a given location exists on this map.
        Args:
            location (Location): the location we want to find out about
        Returns:
            bool: True if this location exists on the map. else false
        '''

        if __debug__:
            assert isinstance(location, Location), "Must pass a location"
        x = location.x
        y = location.y
        return ((y>=0 and y < self.height) and (x>=0 and x < self.width))

    def sector_at(self, location):
        '''
        Determine the sector for a given location
        Args:
            location (Location): the location we want to find out about
        Returns:
            Sector: The sector containing this location
        '''

        if __debug__:
            assert self.location_on_map(location)
        loc = Location(
            location.x - location.x % self.sector_size,
            location.y - location.y % self.sector_size
        )
        return self._sectors[loc]

    def _update_sectors(self, data):
        for sector_data in data:
            top_left = Location(sector_data['topLeft']['x'], sector_data['topLeft']['y'])
            if __debug__:
                assert top_left.x % self.sector_size == 0
                assert top_left.y % self.sector_size == 0
            self._sectors[top_left]._update(sector_data)

class Team(object):
    '''
    Information about the teams
    This is immutable, please don't touch this. Or your bot will break.
    Attributes:
        id (int): The id, index, of the team
        name (string): the string name of the team
    '''

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Team) and other.id == self.id

    def __str__(self):
        return '<team "{}" ({})>'.format(self.name, self.id)

    def __repr__(self):
        return str(self)

class State(object):
    '''
    This is the state of the game at this turn
    It contains all of the important, and generated by the game.
    Do not modify any thing in this directly
    Attributes:
        map (Map): This is the map
        turn (int): The turn number in this state
        teams ([Teams]): An array of teams indexed by id
        my_team (Team): My team
        my_team_id (int): The id of my team
        speculate (bool): Pretends that the engine is running locally so it
                          makes sure the code is good. Don't teach.
    '''

    def __init__(self, game, teams, my_team_id, initialState):
        self._game = game
        self._max_id = 0

        self.map = Map(
            self,
            initialState['height'],
            initialState['width'],
            initialState['tiles'],
            initialState['sectorSize']
        )

        # initialize other state
        self.turn = 0
        self.entities = {}
        self.teams = teams
        self.my_team = teams[my_team_id]
        if(len(teams) ==3):
            # This is jank code to convert a 1 to a 2 and a 2 to a 1 to get the
            # opposiing team
            self.other_team = teams[((my_team_id+1)**2+1)%3] 
        else:
            self.other_team = teams[0]
        self.my_team_id = my_team_id

        self._action_queue = []

        self._update_entities(initialState['entities'])
        self.map._update_sectors(initialState['sectors'])

        self.speculate = True

    @property
    def turn_next_spawn(self):
        ''' Turn when next spawn occurs'''
        return ((self.turn-1)//10+1)*10


    def _queue(self, action):
        self._game._queue(action)

    def _update_entities(self, data):
        for entity in data:
            id = entity['id']
            self._max_id = max(self._max_id, id)
            if id not in self.entities:
                self.entities[id] = Entity(self)
            self.entities[id]._update(entity)

    def _build_statue(self, location):
        ''' Build a statue in this state at locatiion location '''
        self._max_id+=1

        data ={
            'id': self._max_id,
            'teamID': self.my_team_id,
            'type': Entity.STATUE,
            'location': {
                'x': location.x,
                'y': location.y
            },
            'hp': 1
        }
        self.entities[self._max_id] = Entity(self)
        self.entities[self._max_id]._update(data)

    def _kill_entities(self, entities):
        for dead in entities:
            ent = self.entities[dead]
            if(ent.held_by == None):
                if self.map._occupied[ent.location].id == ent.id:
                    del self.map._occupied[ent.location]
            del self.entities[dead]

    def _validate(self):
        for ent in self.entities.values():
            if not ent.is_held:
                assert self.map._occupied[ent.location] == ent

    def _validate_keyframe(self, keyframe):
        altstate = State(self._game, self.teams, self.my_team.id, keyframe['state'])
        for id in self.entities:
            assert id in altstate.entities
            assert self.entities[id] == altstate.entities[id],\
                (self.entities[id], altstate.entities[id])
        for top_left in self.map._sectors:
            assert top_left in altstate.map._sectors
            assert self.map._sectors[top_left] == altstate.map._sectors[top_left],\
                (self.map._sectors[top_left] == altstate.map._sectors[top_left])

        self._validate()


    def get_entities(self, entity_id=-1,entity_type=None,location=None,
            team=None):

        ''' Get an iterator of all the entities.
            Can filter with the parameters:
                entity_id gets the entity with a given id
                entity_type filters to only entities of a given type
                team filters all entities are part of a given team'''

        for i in range(self._max_id+1):
            entity = self.entities.get(i)
            if entity == None:
                continue
            if entity_id != -1 and entity.id != entity_id:
                continue
            if entity_type != None and entity.type != entity_type:
                continue
            if location != None and entity.location != location:
                continue
            if team != None and entity.team != team:
                continue
            yield entity

if 'BATTLECODE_IP' not in os.environ:
    DEFAULT_SERVER = ('localhost', 6147)
else:
    print('Connecting to', (os.environ['BATTLECODE_IP'], 6147))
    DEFAULT_SERVER = (os.environ['BATTLECODE_IP'], 6147)

class Game(object):
    '''
    This is the game that is being played.
    Running the init connects your code to the engine to play the game
    Create a for loop which iterates through game.turns to play the game. It
    will give a state for each turn with which you can see and perform
    actions.
    '''

    def __init__(self, name, server=DEFAULT_SERVER):
        '''Connect to the server and wait for the first turn.
        name is the name this bot would like to be called; it will be ignored on the
        scrimmage server.
        Server is the address to connect to. Leave it as None to connect to a default local
        server; you shouldn't need to mess with it unless you're making custom matchmaking stuff.'''

        assert isinstance(name, str) \
               and len(name) > 5 and len(name) < 100, \
               'invalid team name: '+unicode(name)

        # setup connection
        if isinstance(server, str) and server.startswith('/') and os.name != 'nt':
            # unix domain socket
            conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM);
        else:
            # tcp socket
            conn = socket.socket()
        # connect to the server
        conn.connect(server)

        self._socket = conn.makefile('rwb', 2**16)

        # send login command
        login = {
            'command': 'login',
            'name': name,
        }
        if 'BATTLECODE_PLAYER_KEY' in os.environ:
            key = os.environ['BATTLECODE_PLAYER_KEY']
            print('Logging in with key:', key)
            login['key'] = key

        self._send(login)

        self._recv_queue = Queue()

        self._missed_turns = set()

        commThread = threading.Thread(target=self._recv_thread, name='Battlecode Communication Thread')
        commThread.daemon = True
        commThread.start()

        # handle login response
        resp = self._recv()
        assert resp['command'] == 'loginConfirm'

        self.my_team_id = resp['teamID']

        # wait for the start command
        start = self._recv()
        assert start['command'] == 'start'

        teams = {}
        for team in start['teams']:
            team = Team(team['teamID'], team['name'])
            teams[team.id] = team

        # initialize state info

        initialState = start['initialState']

        self.state = State(self, teams, self.my_team_id, initialState)

        self.winner = None

        # wait for our first turn
        self._next_team = None
        self._await_turn()

    def _send(self, message):
        '''Send a dictionary as JSON to the server.
        See server/src/schema.ts for valid messages.'''

        message = json.dumps(message)

        self._socket.write(message.encode('utf-8'))
        self._socket.write(b'\n')
        self._socket.flush()

    def _recv_thread(self):
        '''Loop, receiving '\n'-delimited JSON messages from the server.
        See server/src/schema.ts for valid messages.'''
        while True:
            # next() reads lines from a file object
            try:
                message = next(self._socket)
            except:
                self._recv_queue.put(None)
                return

            message = message.decode()
            result = json.loads(message)

            if "command" not in result:
                self._recv_queue.put(None)
                raise BattlecodeError("Unknown result: "+str(result))
            elif result['command'] == 'error':
                if result['reason'].startswith('wrong turn'):
                    sys.stderr.write('Battlecode warning: missed turn, speed up your code!\n')
                else:
                    raise BattlecodeError(result['reason'])
            elif result['command'] == 'missedTurn':
                sys.stderr.write('Battlecode warning: missed turn {}, speed up your code!\n'.format(result['turn']))
                self._missed_turns.add(result['turn'])
            else:
                self._recv_queue.put(result)

    def _recv(self):
        '''Pull a message from our queue; blocking.'''
        while True:
            try:
                item = self._recv_queue.get(block=True, timeout=.1)
                return item
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                continue

    def _can_recv_more(self):
        return not self._recv_queue.empty()

    def _finish(self, winner_id):
        if self._socket is not None:
            self._socket = None
        self.winner = self.state.teams[winner_id]

    def next_turn(self):
        '''Submit queued actions, and wait for our next turn.'''
        self._submit_turn()
        self._await_turn()

    def _await_turn(self):
        while True:
            turn = self._recv()

            if turn is None:
                self._finish(0)
                return

            if turn['command'] == 'keyframe':
                self.state._validate_keyframe(turn)
                continue

            assert turn['command'] == 'nextTurn'

            self.state._update_entities(turn['changed'])
            self.state._kill_entities(turn['dead'])
            self.state.map._update_sectors(turn['changedSectors'])

            self.state.turn = turn['turn'] + 1

            if 'winnerID' in turn:
                self._finish(turn['winnerID'])
                return

            if __debug__:
                if turn['lastTeamID'] == self.state.my_team.id:
                    # handle what happened last turn
                    for action, reason in zip(turn['failed'], turn['reasons']):
                        print('failed: {}:{} reason: {}'.format(
                            action['id'],
                            action['action'],
                            self.state.turn,
                            reason,
                        ))

            if turn['nextTeamID'] == self.state.my_team.id and not self._can_recv_more():
                return

    def _submit_turn(self):
        if self.state.turn in self._missed_turns:
            self.state._action_queue = []
            return
        if self._socket is None:
            return
        self._send({
            'command': 'makeTurn',
            'turn': self.state.turn,
            'actions': self.state._action_queue
        })
        self.state._action_queue = []

    def _queue(self, action):
        self.state._action_queue.append(action)

    def turns(self, copy=True, speculate=True):
        '''
        Returns an iterator. You should for loop over this function to get a
        copy of state for each turn.
        Returns:
            State: a state that you can play on
        '''

        if speculate:
            copy = True
        while True:
            self.next_turn()
            if self.winner:
                return
            else:
                self.state.speculate = speculate
                if copy:
                    self.state._game = None
                    speculative = _deepcopy(self.state)
                    speculative._game = self
                    self.state._game = self
                    yield speculative
                else:
                    yield self.state

class BattlecodeError(Exception):
    def __init__(self, *args, **kwargs):
        super(BattlecodeError, self).__init__(self, *args, **kwargs)

def _deepcopy(x):
    # significantly faster than copy.deepcopy
    return pickle.loads(pickle.dumps(x))
