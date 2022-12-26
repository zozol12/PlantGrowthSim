"""Game that simulates plant growth.
Plant grows on a 2D map which is a grid of cells."""

#
# Imports
#
import sys
from random import randint

import pygame

#
# Constants
#

MAP_WIDTH = 1920
MAP_HEIGHT = 1080
CELL_SIZE = 5
TICKS_PER_SECOND = 120
ROCK_CHANCE = 5

MAX_AIR_SUNLIGHT = 100

#
# Classes
#

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
        adjacent_cells = []
        for x in range(self.x - 1, self.x + 2):
            for y in range(self.y - 1, self.y + 2):
                if 0 <= x < len(MAP.grid) and 0 <= y < len(MAP.grid[x]):
                    adjacent_cells.append(MAP.grid[x][y])
        return adjacent_cells

    def update(self):
        """Updates the object."""
        pass

    def clone(self, x, y):
        """Creates same object at new coordinates."""
        return create_cell(x, y, self.name)

    def draw(self, screen):
        """Draws the object on the screen."""
        pygame.draw.rect(screen, self.color, self.rect)


# Terrain Cells

class Air(CellObject):
    """Represents air."""

    def __init__(self, x, y):
        super().__init__(x, y, "air", (0, 100, 255))
        self.sunlight = 0
        # set color based on sunlight, lighter is more sunlight
        self.color = (0, 100 + self.sunlight, 255 - self.sunlight)
        self.rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    # set update function. Update adjacent air cells to increase sunlight
    # reduce one sunlight from self
    def update(self):
        if self.sunlight >= 10:
            self.sunlight -= 10
        for cell in self.get_adjacent_cells():
            if isinstance(cell, Air):
                cell.sunlight += self.sunlight / 2
                g = 100 + cell.sunlight
                b = 255 - cell.sunlight
                if g > 255:
                    g = 255
                if b < 0:
                    b = 0
                cell.color = (0, g, b)


class Dirt(CellObject):
    """Represents dirt.
    """

    def __init__(self, x, y, color=(100, 100, 100)):
        super().__init__(x, y, "dirt", color)
        self.humidity = 5
        self.x = x
        self.y = y

    @classmethod
    def generate_dirt(cls, x, y):
        """Generates dirt with random humnidity.
        Max humidity is 10."""
        dirt = cls(x, y)
        dirt.humidity = randint(1, 5)
        dirt.color = (139 + (dirt.humidity * 2), 69 + (dirt.humidity * 2), 19)
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
        self.cells = []

    def get_adjacent_cells(self):
        """Returns list of adjacent cells to the plant.
        Adjacent cells are cells that are next to the plant.
        """
        adjacent_cells = []
        for cell in self.cells:
            if cell.x > 0:
                adjacent_cells.append(MAP.grid[cell.x - 1][cell.y])
            if cell.x < MAP_WIDTH // CELL_SIZE - 1:
                adjacent_cells.append(MAP.grid[cell.x + 1][cell.y])
            if cell.y > 0:
                adjacent_cells.append(MAP.grid[cell.x][cell.y - 1])
            if cell.y < MAP_HEIGHT // CELL_SIZE - 1:
                adjacent_cells.append(MAP.grid[cell.x][cell.y + 1])
        return adjacent_cells

    def update(self):
        """Updates all cells in complex object."""
        for cell in self.cells:
            cell.update()

    def __generate__(self):
        """Generates a complex object at given coordinates."""
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
        self.cell_type = "sun"
        self.starting_look = ([0, 1, 0],
                              [1, 1, 1],
                              [0, 1, 0])
        self.__generate__()

    def update(self):
        # for each adjacent air cell, add sunlight
        for cell in self.get_adjacent_cells():
            if isinstance(cell, Air):
                cell.sunlight = 100
        self.draw()

    def draw(self):
        for cell in self.cells:
            MAP.grid[cell.x][cell.y] = cell


# Plant

class Plant(ComplexObject):
    """Represents plant, which is a collection of cells.
    Cells have their coordinates relative to map."""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = "plant"
        self.cell_type = "seed"
        self.starting_look = ([1])
        self.cells: list[CellObject] = []
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

        # add one sunlight for each stem and leaf
        self.sunlight += (len([cell for cell in self.cells if isinstance(cell, Stem) or isinstance(cell, Leaf)]) / 10)

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

    def grow_root(self):
        """Grows root to dirt cell with highest humidity.
        Can only grow down, right or left"""
        adjacent_cells = self.get_adjacent_cells()
        dirt_cells = [cell for cell in adjacent_cells if isinstance(cell, Dirt)]
        if dirt_cells:
            # Only get dirt cells which y coordinate is the same or one lower as the plant's lowest y coordinate
            dirt_cells = [cell for cell in dirt_cells if cell.y > min([cell.y for cell in self.cells])]

            dirt_cells.sort(key=lambda cell: cell.humidity, reverse=True)
            dirt_cell = dirt_cells[0]
            # add dirts humidity to plants water
            self.water += dirt_cell.humidity
            self.cells.append(Root(dirt_cell.x, dirt_cell.y))

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
            new_stem.color = (0, 255 - new_stem.y * 2, 0)
            self.cells.append(new_stem)

    def grow_leaf(self):
        """Grows one leaf cell to one of the adjacent air cells to the plant.
        Never grows on top of a stem cell."""
        adjacent_cells = self.get_adjacent_cells()
        air_cells = [cell for cell in adjacent_cells if isinstance(cell, Air)]
        stems = [cell for cell in self.cells if isinstance(cell, Stem)]
        if air_cells:
            for stem in stems:
                air_cells = [cell for cell in air_cells if cell.y != stem.y]
            air_cells.sort(key=lambda cell: cell.y, reverse=True)
            air_cell = air_cells[0]
            self.cells.append(Leaf(air_cell.x, air_cell.y))

    def grow(self):
        """Grow plant.
        It chooses to grow:
        - stem or leaf if there is only seed, or if there is less sunlight than water.
        - root if there is more sunlight than water.
        """
        if len(self.cells) == 1:
            self.grow_stem()
        elif self.sunlight < self.water:
            random = randint(1, 2)
            if random == 1:
                self.grow_stem()
            else:
                self.grow_leaf()
        else:
            self.grow_root()

    def draw(self):
        """Draws the plant on the map."""
        for cell in self.cells:
            MAP.grid[cell.x][cell.y] = cell


class Map:
    """Map class.
    Contains list of lists of cells.
    """

    def __init__(self):
        """Initializes map.
        Creates empty map of air cells.
        """
        super().__init__()
        self.complex_objects: list[ComplexObject] = []
        self.grid: list[list[CellObject]] = []

    @classmethod
    def generate(cls):
        """Generates map.
        Generates dirt and water cells.
        """
        # generate emty map
        map = cls()
        for x in range(MAP_WIDTH // CELL_SIZE):
            map.grid.append([])
            for y in range(MAP_HEIGHT // CELL_SIZE):
                if y < MAP_HEIGHT // CELL_SIZE // 2:
                    map.grid[x].append(Air(x, y))
                else:
                    map.grid[x].append(Dirt.generate_dirt(x, y))

        # generate rocks in dirt
        for x in range(MAP_WIDTH // CELL_SIZE):
            for y in range(MAP_HEIGHT // CELL_SIZE):
                if isinstance(map.grid[x][y], Dirt):
                    if randint(1, 100) <= ROCK_CHANCE:
                        map.grid[x][y] = Rock(x, y)

        # add sun to map
        # sun = Sun(5, 5)
        # map.complex_objects.append(sun)
        return map

    def __str__(self):
        """Returns string representation of map.
        Contains all cells in the map.
        """
        return f"{super().__str__()}\n{self.complex_objects}"

    def __list__(self):
        """Returns list representation of map.
        Contains all cells in the map.
        """
        return self.grid

    def update(self):
        """Updates the map.
        Updates all cells in the map.
        """
        for complex_object in self.complex_objects:
            complex_object.update()
        for row in self.grid:
            for cell in row:
                cell.update()
        self.draw()

    def draw(self):
        """Draws the map.
        Draws all cells in the map.
        """
        for row in self.grid:
            for cell in row:
                cell.draw(SCREEN)


#
# Functions
#

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
        return Sun(x, y)
    else:
        raise ValueError(f"Invalid cell type: {cell_type}")


def choice(items):
    """Returns random item from list."""
    return items[randint(0, len(items) - 1)]


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

if __name__ == "__main__":
    pygame.init()
    SCREEN = pygame.display.set_mode((MAP_WIDTH, MAP_HEIGHT))
    CLOCK = pygame.time.Clock()

    while True:
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
                if isinstance(MAP.grid[x][y], Dirt):
                    # spawn on highest dirt cell
                    while y > 0 and not isinstance(MAP.grid[x][y - 1], Air):
                        y -= 1
                    MAP.complex_objects.append(Plant(x, y))
                elif isinstance(MAP.grid[x][y], Air):
                    MAP.grid[x][y] = WaterDrop(x, y)

        # update plants
        MAP.update()

        pygame.display.flip()
