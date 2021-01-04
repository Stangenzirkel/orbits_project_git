import os
import pygame
import random
import math
import copy

pygame.init()
pygame.mouse.set_visible(False)

GRAVITY = 6.67
FPS = 60
GAME_SPEED = 1
MAP_VIEW_SIZE = 250

"""
УПРАВЛЕНИЕ
карта - M
повороты - стрелки
двигатель - пробел
время +/- - [/]
"""


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname).convert()

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()

    return image


class InterplanetaryMap:
    def __init__(self, size):
        self.map_surface = pygame.Surface(size, pygame.SRCALPHA, 32)
        self.background_surface = self.draw_background()
        self.labels = dict()
        self.font = pygame.font.SysFont(None, 20)
        self.objects = []

    def draw_cursor(self, rect_size=10):
        pygame.draw.rect(self.map_surface, 'green', (pygame.mouse.get_pos()[0] - rect_size // 2,
                                                     pygame.mouse.get_pos()[1] - rect_size // 2,
                                                     rect_size, rect_size), 1)

        pygame.draw.line(self.map_surface, 'green', (0, pygame.mouse.get_pos()[1]),
                         (pygame.mouse.get_pos()[0] - rect_size // 2, pygame.mouse.get_pos()[1]))

        pygame.draw.line(self.map_surface, 'green', (self.map_surface.get_size()[0],
                                                     pygame.mouse.get_pos()[1]),
                         (pygame.mouse.get_pos()[0] + rect_size // 2, pygame.mouse.get_pos()[1]))

        pygame.draw.line(self.map_surface, 'green', (pygame.mouse.get_pos()[0], 0),
                         (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1] - rect_size // 2))

        pygame.draw.line(self.map_surface, 'green',
                         (pygame.mouse.get_pos()[0], self.map_surface.get_size()[1]),
                         (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1] + rect_size // 2))

    def draw_background(self):
        grid_surface = pygame.Surface(self.map_surface.get_size(), pygame.SRCALPHA, 32)
        grid_surface.fill((0, 0, 0, 0))
        for i in range(1, 160):
            pygame.draw.line(grid_surface, (0, 15, 0), (i * 9, 0), (i * 9, self.map_surface.get_height()))

        for i in range(1, 100):
            pygame.draw.line(grid_surface, (0, 15, 0), (0, i * 9), (self.map_surface.get_width(), i * 9))

        for i in range(1, 16):
            pygame.draw.line(grid_surface, (0, 35, 0), (i * 90, 0), (i * 90, self.map_surface.get_height()))

        for i in range(1, 10):
            pygame.draw.line(grid_surface, (0, 35, 0), (0, i * 90), (self.map_surface.get_width(), i * 90))

        return grid_surface

    def update(self):
        self.map_surface = copy.copy(self.background_surface)
        self.draw_cursor()

        for object in self.objects:
            object.update()
            object.render()

        self.draw_label()

        return self.map_surface

    def draw_label(self):
        for key in self.labels.keys():
            pygame.draw.line(self.map_surface, 'green', key.pos(),
                             (key.x + 50, key.y - 50))

            out = self.font.render(' '.join(self.labels[key]), True, 'green')
            self.map_surface.blit(out, (key.x + 55, key.y - 68))

            pygame.draw.line(self.map_surface, 'green', (key.x + 50, key.y - 50),
                             (key.x + 50 + out.get_width(), key.y - 50))

    def add_text_to_label(self, obj, *args):
        self.labels[obj] = list(map(str, args))

    def surface(self):
        return self.map_surface

    def click_object(self, pos):
        for object in self.objects:
            if ((pos[0] - object.x) ** 2 + (pos[1] - object.y) ** 2) ** 0.5 <= object.radius + 5:
                return object

        return None


class PhysicalObjectOnMap:
    def __init__(self, orbit_parent, x, y, speed_x, speed_y, apsis_argument):
        self.x = x
        self.y = y

        self.orbit_parent = orbit_parent

        self.speed_x = speed_x
        self.speed_y = speed_y

        self.apsis_argument = apsis_argument

    def physical_move(self):
        delta_x = self.x - self.orbit_parent.x
        delta_y = self.y - self.orbit_parent.y
        a = self.orbit_parent.mass * GRAVITY / (delta_x ** 2 + delta_y ** 2)
        a_x = delta_x * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)
        a_y = delta_y * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)

        self.speed_x += a_x * GAME_SPEED / FPS
        self.speed_y += a_y * GAME_SPEED / FPS

        self.x += self.speed_x * GAME_SPEED / FPS
        self.y += self.speed_y * GAME_SPEED / FPS

    def draw_ellipse(self):
        distanse = ((self.orbit_parent.x - self.x) ** 2 + (self.orbit_parent.y - self.y) ** 2) ** 0.5
        speed = (self.speed_x ** 2 + self.speed_y ** 2) ** 0.5

        a = 1 / (2 / distanse - speed ** 2 / (GRAVITY * self.orbit_parent.mass))
        e = (a - distanse) / a
        b = a * (1 - e ** 2) ** 0.5

        apoapsis = a * (1 + e)
        periapsis = a * (1 - e)

        ellipse_surface = pygame.Surface((int(a * 2), int(b * 2)), pygame.SRCALPHA, 32)
        ellipse_surface.fill((0, 0, 0, 0))

        pygame.draw.ellipse(ellipse_surface, (0, 100, 0), (0, 0, int(a * 2), int(b * 2)), 1)

        delta_x = apoapsis
        delta_y = b

        ellipse_surface, x, y = self.blitRotate(self.orbit_parent.pos(), (delta_x, delta_y), self.apsis_argument, ellipse_surface)

        return ellipse_surface, (x, y)

    def blitRotate(self, pos, originPos, angle, or_image):

        angle = - angle
        # calcaulate the axis aligned bounding box of the rotated image
        w, h = or_image.get_size()
        box = [pygame.math.Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
        box_rotate = [p.rotate(angle) for p in box]
        min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
        max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])

        # calculate the translation of the pivot
        pivot = pygame.math.Vector2(originPos[0], -originPos[1])
        pivot_rotate = pivot.rotate(angle)
        pivot_move = pivot_rotate - pivot

        # calculate the upper left origin of the rotated image
        origin_x, origin_y = pos[0] - originPos[0] + min_box[0] - pivot_move[0], pos[1] - originPos[1] - max_box[1] + pivot_move[1]

        # get a rotated image
        image = pygame.transform.rotate(or_image, angle)

        return image, origin_x, origin_y


class StarOnMap:
    def __init__(self, map, name, id, mass=100000, radius=20):
        self.map = map
        self.name = name
        self.id = id
        self.mass = mass
        self.radius = radius
        self.x, self.y = self.start_position()
        self.map.objects.append(self)

    def start_position(self):
        return self.map.map_surface.get_rect().center

    def render(self):
        pygame.draw.circle(self.map.map_surface, 'green', (self.x, self.y), self.radius, 1)

    def update(self):
        self.map.add_text_to_label(self, self.name, 'x: ' + str(self.x), 'y: ' + str(self.y))

    def pos(self):
        return self.x, self.y


class PlanetOnMap(StarOnMap, PhysicalObjectOnMap):
    def __init__(self, map, name, id, start_height, speed, orbital_parent, apsis_argument=0, mass=0, radius=5):
        self.start_height = start_height
        self.speed = speed
        self.apsis_argument = apsis_argument
        self.orbital_parent = orbital_parent

        StarOnMap.__init__(self, map, name, id, mass=mass, radius=radius)
        PhysicalObjectOnMap.__init__(self, self.orbital_parent, self.x, self.y, *self.start_speed(), apsis_argument)

        ellipse_surface, ellipse_surface_coords_delta = self.draw_ellipse()
        self.map.background_surface.blit(ellipse_surface, ellipse_surface_coords_delta)

    def start_position(self):
        return self.start_height * math.cos(math.radians(self.apsis_argument)) + self.orbital_parent.x, \
               self.start_height * math.sin(math.radians(self.apsis_argument)) + self.orbital_parent.y

    def update(self):
        self.physical_move()
        self.map.add_text_to_label(self, self.name, 'x: ' + str(int(self.x)), 'y: ' + str(int(self.y)))

    def start_speed(self):
        return self.speed * math.cos(math.radians(self.apsis_argument + 90)), \
               self.speed * math.sin(math.radians(self.apsis_argument + 90))


infoObject = pygame.display.Info()
window_size = (infoObject.current_w, infoObject.current_h)
screen = pygame.display.set_mode(window_size, pygame.FULLSCREEN)
screen.fill('black')

interplanetary_map = InterplanetaryMap(window_size)

star = StarOnMap(interplanetary_map, 'star', 99)
planet_1 = PlanetOnMap(interplanetary_map, 'planet', 1, 500, 20, star, apsis_argument=45)
planet_2 = PlanetOnMap(interplanetary_map, 'planet', 2, 500, 20, star, apsis_argument=0)
planet_3 = PlanetOnMap(interplanetary_map, 'planet', 3, 100, 90, star, apsis_argument=0)

all_sprites = pygame.sprite.Group()
pygame.mouse.set_visible(False)

running = True
clock = pygame.time.Clock()

REDRAW_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(REDRAW_EVENT, 1000 // FPS)

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == REDRAW_EVENT:
            screen.fill('black')
            interplanetary_map.update()
            screen.blit(interplanetary_map.surface(), (0, 0))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            object = interplanetary_map.click_object(event.pos)
            print(object.name, object.id)

    pygame.display.flip()
pygame.quit()