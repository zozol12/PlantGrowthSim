"""Game that simulates plant growth.
Plant grows on a 2D map which is a grid of cells."""

#
# Imports
#
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from math import sqrt
from random import randint

import pygame

#
# Constants
#

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
CELL_SIZE = 5

# number of cells in a row
MAP_WIDTH = SCREEN_WIDTH // CELL_SIZE
# number of cells in a column
MAP_HEIGHT = SCREEN_HEIGHT // CELL_SIZE

TICKS_PER_SECOND = 60
ROCK_CHANCE = 5

MAX_AIR_SUNLIGHT = 1000


class Direction(Enum):
    """Enum for directions. (x, y)"""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    LEFT_UP = (-1, -1)
    LEFT_DOWN = (-1, 1)
    RIGHT_UP = (1, -1)
    RIGHT_DOWN = (1, 1)


#
# Classes
#

def memoise(func):
    """Memoisation decorator."""
    cache = {}

    def wrapper(*args, **kwargs):
        key = args + tuple(kwargs.items())
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper


# Temporary "profiler"
class performance_test:
    def __init__(self, name):
        self.name = name
        self.start = datetime.now()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"{self.name} took {datetime.now() - self.start} seconds")


class CellObject:
    """Base class for all objects in the game."""

    def __init__(self, x, y, name, color):
        self.name = name
        self.color = color
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    def __str__(self):
        return self.name

    @classmethod
    def create_by_type(cls, x, y, type):
        """Creates same object at new coordinates."""
        return create_cell(x, y, type)

    def get_adjacent_cells(self):
        """Returns a list of adjacent cells on map.
        Map is list of lists of cells."""
        surrounding_cell_coordinates = [(self.x + direction.value[0], self.y + direction.value[1])
                                        for direction in Direction]
        surrounding_cells = []
        for x, y in surrounding_cell_coordinates:
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                surrounding_cells.append(MAP.grid[y][x])
        return surrounding_cells

    def get_cell_in_direction(self, direction):
        """Returns cell in given direction."""
        x = self.x + direction.value[0]
        y = self.y + direction.value[1]
        if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
            return MAP.grid[y][x]
        return None

    def update(self):
        """Updates the object."""
        # if MAP.grid[self.y][self.x] != self:
        #    MAP.grid[self.y][self.x] = self
        pass

    def clone(self, x, y):
        """Creates same object at new coordinates."""
        return create_cell(x, y, self.name)

    def draw(self, screen):
        """Draws the object on the screen."""
        pygame.draw.rect(screen, fix_color(self.color), self.rect)


# Terrain Cells

class Air(CellObject):
    """Represents air."""
    base_color: tuple = (0, 91, 150)

    def __init__(self, x, y):
        super().__init__(x, y, "air", self.base_color)
        self.sunlight = 0
        self.last_sun_position = None
        self.color = (
            self.base_color[0], self.base_color[1] + self.sunlight, self.base_color[2] + self.sunlight)
        self.rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    def __str__(self):
        return self.name + " " + str(self.sunlight) + " "

    # Update air sunlight and color depending on sun position
    def update(self):
        sun = MAP.complex_objects["sun"]
        sun_pos = (sun.x, sun.y)
        if sun_pos != self.last_sun_position:
            self.last_sun_position = (sun.x, sun.y)
            closest_distance = abs(sun.x - self.x) + abs(sun.y - self.y)  # Calculate distance to sun
            self.sunlight = 100 - (closest_distance * 1.2)  # Calculate sunlight based on distance
            self.color = (self.base_color[0], self.base_color[1] + self.sunlight, self.base_color[2] + self.sunlight)


class Dirt(CellObject):
    """Represents dirt.
    """
    base_color = (139, 69, 19)

    def __init__(self, x, y):
        super().__init__(x, y, "dirt", self.base_color)
        self.humidity = 5
        self.x = x
        self.y = y

    @classmethod
    def generate(cls, x, y):
        """Generates dirt with random humnidity.
        Max humidity is 10."""
        dirt = cls(x, y)
        dirt.humidity = randint(1, 5)
        dirt.color = (cls.base_color[0] + (dirt.humidity * 2),
                      cls.base_color[1] + (dirt.humidity * 2),
                      cls.base_color[2])
        return dirt


class Rock(CellObject):
    """Represents rock."""

    def __init__(self, x, y):
        super().__init__(x, y, "rock", (112, 128, 144))


# Special Cells

class WaterDrop(CellObject):
    """falls down one cell per tick
    adds humidity to dirt, or water to plants if it encounters them.
    it replaces
    """

    def __init__(self, x, y):
        super().__init__(x, y, "waterdrop", (0, 0, 255))
        self.rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        self.y = y
        self.x = x
        self.humidity = 5
        self.color = (0, 0, 100)
        self.stopped = False

    def update(self):
        encountered_cell = MAP.grid[self.x][self.y + 1]
        MAP.grid[self.x][self.y] = Air(self.x, self.y)
        if isinstance(encountered_cell, Air):
            self.y += 1
            self.rect = pygame.Rect(self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            MAP.grid[self.x][self.y] = self
        else:
            self.stopped = True
            if isinstance(encountered_cell, Dirt):
                encountered_cell.humidity += self.humidity
                encountered_cell.color = (139 + encountered_cell.humidity, 69 + encountered_cell.humidity, 19)


# Plant Cells

class Seed(CellObject):
    """Represents a seed.
    Attributes:
    """

    def __init__(self, x, y):
        super().__init__(x, y, "seed", (100, 0, 0))


class Stem(CellObject):
    """Represents a stem. Stem is part of a plant.
    Attributes:
    """

    def __init__(self, x, y):
        super().__init__(x, y, "stem", (0, 200, 0))


class Leaf(CellObject):
    """Represents a leaf. Leaf is part of a plant.
    Attributes:
    """

    def __init__(self, x, y):
        super().__init__(x, y, "leaf", (0, 255, 0))


class Root(CellObject):
    """Represents a root. Root is part of a plant.
    Attributes:
    """

    def __init__(self, x, y):
        super().__init__(x, y, "root", (188, 143, 143))


class Wood(CellObject):
    """Represents a wood. Wood is part of a plant.
    Attributes:
    """

    def __init__(self, x, y):
        super().__init__(x, y, "wood", (160, 82, 45))


# Sun Cells

class SunCell(CellObject):
    """Represents a sun cell.
    Attributes:
    """

    def __init__(self, x, y):
        super().__init__(x, y, "sun", (255, 255, 0))
        self.color = (255, 255, 0)


# Complex Objects

class ComplexObject:
    """Base class for complex objects.
    Complex objects are made up of multiple cells.
    """
    old_cells = {}
    old_adjacent_cells = []

    def __init__(self, x, y):
        # starting position of complex object
        self.x = x
        self.y = y
        # look of the object, 0 is no cell, 1 is cell, represented as touple with rows
        self.starting_look = ([1, 0, 1],
                              [0, 1, 0],
                              [1, 0, 1])
        # default cell of the object
        self.cell_type = "air"
        # cells of the object with coordinates based on starting position and look
        self.cells: list[CellObject] = []

    def get_adjacent_cells(self):
        """Returns list of adjacent cells to the plant.
        Adjacent cells are cells that are next to the plant.
        """
        adjacent_cells = []
        for cell in self.cells:
            adjacent_cells.extend(cell.get_adjacent_cells())
        return adjacent_cells

    def update(self):
        """Updates all cells in complex object."""
        for cell in self.cells:
            cell.update()

    def __generate__(self):
        """Generates a complex object at given coordinates."""
        self.cells = []
        if type(self.starting_look) == list and len(self.starting_look) == 1:
            self.cells.append(create_cell(self.cell_type, self.x, self.y))
            return
        # create cells
        for y in range(len(self.starting_look)):
            for x in range(len(self.starting_look[y])):
                if self.starting_look[y][x] == 1:
                    self.cells.append(create_cell(self.cell_type, self.x + x, self.y + y))


# Sun

class Sun(ComplexObject):
    """Represents the sun. Which is collection of sun cells.
    Air cells get sunlight from the sun.
    Nearer cells get more sunlight."""

    def __init__(self, x, y):
        super().__init__(x, y)
        # spawn the sun cells
        self.name = "sun"
        self.cell_type = "sun"
        self.cells = []
        self.starting_look = ([0, 0, 1, 1, 1, 0, 0],
                              [0, 1, 1, 1, 1, 1, 0],
                              [1, 1, 1, 1, 1, 1, 1],
                              [1, 1, 1, 1, 1, 1, 1],
                              [1, 1, 1, 1, 1, 1, 1],
                              [0, 1, 1, 1, 1, 1, 0],
                              [0, 0, 1, 1, 1, 0, 0])
        self.__generate__()

    def update(self):
        # if sun is out of bounds, move it to the left
        if self.x > MAP_WIDTH:
            self.x = 5
            self.__generate__()
        # move the sun to the right
        self.x += 1
        # update cells
        for cell in self.cells:
            cell.x += 1
            cell.rect = pygame.Rect(cell.x * CELL_SIZE, cell.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        self.draw()

    def draw(self):
        # draw sun cells
        for cell in self.cells:
            cell.draw(SCREEN)


# Plant

class Plant(ComplexObject):
    """Represents plant, which is a collection of cells.
    Cells have their coordinates relative to map."""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = "plant"
        self.cell_type = "seed"
        self.starting_look = ([1])
        self.cells = []
        self.age = 0
        self.water = 10
        self.sunlight = 10
        self.__generate__()

    def __str__(self):
        """returns string representation of plant.
        Contains its attributes and number of cells."""
        return f"{self.name} age: {self.age} water: {self.water} sunlight: {self.sunlight} cells: {len(self.cells)}"

    def update(self):
        """Updates the plant.
        Plant grows if it has enough water and sunlight.
        """
        super(Plant, self).update()
        self.age += 1

        adjacent_cells = self.get_adjacent_cells()
        # add one sunlight for each stem and leaf
        air_cells = [cell for cell in adjacent_cells if isinstance(cell, Air)]
        average_sunlight = sum([cell.sunlight for cell in air_cells]) / len(air_cells)
        if average_sunlight > 0:
            self.sunlight += (average_sunlight / 2)

        if self.water > 1 and self.sunlight >= 6:
            self.grow()
            self.water -= 2
            self.sunlight -= 6
            # TODO
            # convert roots adjacent to air to wood
            # for cell in self.cells:
            #    if isinstance(cell, Root):
            #        for adjacent_cell in cell.get_adjacent_cells(map):
            #            if isinstance(adjacent_cell, Air):
            #                self.cells[self.cells.index(cell)] = Wood(cell.x, cell.y)
        else:
            pass
            # self.die(map)

        self.draw()
        print(self)

    def grow_root(self):
        """Grows root to dirt cell with highest humidity.
        Can only grow down, right or left"""
        # get all dirt cells with highest humidity
        highest_humidity = 0
        highest_humidity_cells = []
        for cell in self.get_adjacent_cells():
            if isinstance(cell, Dirt):
                if cell.humidity > highest_humidity:
                    highest_humidity = cell.humidity
                    highest_humidity_cells = [cell]
                elif cell.humidity == highest_humidity:
                    highest_humidity_cells.append(cell)
        # if there are no dirt cells, return
        if not highest_humidity_cells:
            return
        # get random dirt cell from list
        dirt_cell = choice(highest_humidity_cells)
        # add water to dirt cell
        self.water += dirt_cell.humidity
        # create root cell
        root_cell = Root(dirt_cell.x, dirt_cell.y)
        # add root cell to plant
        self.cells.append(root_cell)

    def grow_stem(self):
        """Grows stem up one cell, from highest stem on map.
        If no stems, grows stem from seed."""
        stems = [cell for cell in self.cells if isinstance(cell, Stem)]
        new_stem: Stem = None
        if stems:
            stems.sort(key=lambda cell: cell.y)
            stem = stems[0]
            if stem.y > 0:
                new_stem = Stem(stem.x, stem.y - 1)
                self.cells.append(new_stem)
        else:
            seed = [cell for cell in self.cells if isinstance(cell, Seed)][0]
            if seed.y > 0:
                new_stem = Stem(seed.x, seed.y - 1)
        if new_stem is not None:
            new_stem.color = (0, 255 - new_stem.y, 0)
            self.cells.append(new_stem)

    def grow_leaf(self):
        """Grows one leaf cell to one of the adjacent air cells to the plant.
        Never grows on top of a stem cell."""
        adjacent_cells = self.get_adjacent_cells()
        air_cells = [cell for cell in adjacent_cells if isinstance(cell, Air)]
        if air_cells:
            air_cells.sort(key=lambda cell: cell.y, reverse=True)
            air_cell = air_cells[randint(0, len(air_cells) - 1)]
            self.cells.append(Leaf(air_cell.x, air_cell.y))

    def grow(self):
        """Grow plant.
        It chooses to grow:
        - stem or leaf if there is only seed, or if there is less sunlight than water.
        - root if there is more sunlight than water.
        """
        if len(self.cells) == 1:
            self.grow_stem()
        elif self.sunlight < self.water and self.water > 3:
            random = randint(1, 2)
            stems = [cell for cell in self.cells if isinstance(cell, Stem)]
            if stems:
                stems.sort(key=lambda cell: cell.y)
                stem = stems[0]
                if random == 1 and stem.y > 0:
                    self.grow_leaf()
                else:
                    self.grow_stem()
        else:
            self.grow_root()

    def draw(self):
        """Draws the plant on the map."""
        for cell in self.cells:
            MAP.grid[cell.y][cell.x] = cell


class Map:
    """Map class.
    Contains list of lists of cells.
    """

    def __init__(self):
        """Initializes map.
        Creates empty map of air cells.
        """
        super().__init__()
        self.complex_objects: dict = {}
        self.grid: dict = {}

    @classmethod
    def generate(cls):
        """Generates map.
        Generates dirt and water cells."""
        # generate empty map
        map = cls()
        for y in range(MAP_HEIGHT):
            # create empty row
            row = {}
            for x in range(MAP_WIDTH):
                if y < MAP_HEIGHT // 2:
                    # append map grid with air cells
                    row[x] = Air(x, y)
                else:
                    if randint(1, 100) <= ROCK_CHANCE:
                        row[x] = Rock(x, y)
                    else:
                        row[x] = Dirt.generate(x, y)
            map.grid[y] = row

        # add sun to map
        sun = Sun(5, 5)
        map.complex_objects[sun.name] = sun
        return map

    def __str__(self):
        """Returns string representation of map.
        Contains all cells in the map.
        """
        return f"{super().__str__()}\n{self.complex_objects}"

    def update(self):
        """Updates the map.
        Updates all cells in the map.
        """

        # multithread chunked map
        chunked_map = chunked(self.grid, 6)
        with ThreadPoolExecutor(max_workers=4) as executor:
            for chunk in chunked_map:
                executor.submit(update_chunk, chunk)

        # for complex_object in self.complex_objects:
        #    print(complex_object)
        self.draw()

        for key, complex_object in self.complex_objects.items():
            complex_object.update()

    def draw(self):
        """Draws the map.
        Draws all cells in the map.
        """
        for y, row in self.grid.items():
            for x, cell in row.items():
                cell.draw(SCREEN)


#
# Functions
#

def update_chunk(chunk):
    """Updates a chunk of the map.
    Updates all cells in the chunk.
    """
    for y, row in chunk.items():
        for x, cell in row.items():
            cell.update()


def chunked(iterable, n):
    """Yield successive n-sized chunks from iterable."""
    for i in range(0, len(iterable), n):
        yield {k: iterable[k] for k in list(iterable)[i:i + n]}


@memoise
def fix_color(color: tuple[int, int, int]):
    """Fixes color tuple.
    Makes sure all values are between 0 and 255.
    """
    return tuple([max(0, min(255, value)) for value in color])


@memoise
def create_cell(cell_type: str, x: int, y: int):
    """Creates cell of given type.
    Returns cell.
    """
    if cell_type == "air":
        return Air(x, y)
    elif cell_type == "dirt":
        return Dirt(x, y)
    elif cell_type == "rock":
        return Rock(x, y)
    elif cell_type == "seed":
        return Seed(x, y)
    elif cell_type == "stem":
        return Stem(x, y)
    elif cell_type == "leaf":
        return Leaf(x, y)
    elif cell_type == "sun":
        return SunCell(x, y)
    else:
        raise ValueError(f"Invalid cell type: {cell_type}")


def choice(items):
    """Returns random item from list."""
    return items[randint(0, len(items) - 1)]


@memoise
def distance(x1: int, y1: int, x2: int, y2: int):
    """Calculates distance between two points."""
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


#
# Static variables
#

# Map of cells
SCREEN: pygame.display
CLOCK: pygame.time.Clock
MAP = Map.generate()


#
# Main
#


def main():
    while True:
        with performance_test("update"):
            CLOCK.tick(TICKS_PER_SECOND)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # if users clicks on dirt, spawn plant
                # if users clicks on air, spawn waterdrop
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    x = x // CELL_SIZE
                    y = y // CELL_SIZE
                    # print cell attributes
                    print(f"x:{x} y:{y} {MAP.grid[y][x]}")
                    if isinstance(MAP.grid[y][x], Dirt):
                        # spawn on highest dirt cell
                        while y > 0 and not isinstance(MAP.grid[y - 1][x], Air):
                            y -= 1
                        plant = Plant(x, y)
                        MAP.complex_objects[f"plant({x}, {y})"] = plant
                    # elif isinstance(MAP.grid[y][x], Air):
                    #    MAP.grid = WaterDrop(x, y)

            # update map
            MAP.update()
        pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    CLOCK = pygame.time.Clock()
    main()
