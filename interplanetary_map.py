import pygame
import math
import copy
import sqlite3
import datetime as dt

MAP_GRAVITY = 6.67
MAP_GAME_SPEED = 1
FPS = 60
con = sqlite3.connect("game_database.db")


class InterplanetaryMap:
    def __init__(self, size):
        self.map_surface = pygame.Surface(size, pygame.SRCALPHA, 32)
        self.background_surface = self.draw_background()
        self.labels = dict()
        self.font = pygame.font.SysFont(None, 20)
        self.objects = []
        self.buttons = []
        self.hero = None

        self.btn_1 = Button(size[0] - 120, 20, 100, 20, 'Начать заново', 1)
        self.btn_2 = Button(size[0] - 120, 42, 100, 20, 'Рекорды', 2)
        self.btn_3 = Button(size[0] - 120, 64, 100, 20, 'Выход', 3)

        self.buttons = [self.btn_1, self.btn_2, self.btn_3]
        self.result = []
        self.record_surface = pygame.surface.Surface((0, 0))
        self.show_records = False

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
        self.map_surface.blit(self.font.render('NAVCOM power ON', True, 'green'), (20, 20))

        if self.hero.in_travel:
            self.map_surface.blit(self.font.render('ENGINE power ON', True, 'green'), (20, 45))
            self.map_surface.blit(self.font.render('hibernation mode ON', True, 'green'), (20, 70))

        else:
            self.map_surface.blit(self.font.render('ENGINE power OFF', True, 'green'), (20, 45))
            self.map_surface.blit(self.font.render('hibernation mode OFF', True, 'green'), (20, 70))

        if self.show_records:
            self.map_surface.blit(self.record_surface, (self.map_surface.get_width() - 220, 100))

        self.draw_cursor()

        if self.hero.in_travel:
            self.hero.move()

        for object in self.objects:
            object.update()
            object.render()

        for button in self.buttons:
            self.map_surface.blit(button.surface, (button.x, button.y))

        if self.hero:
           self.hero.render()

        self.draw_label()

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
        for button in self.buttons:
            if button.x < pos[0] < button.x + button.width and button.y < pos[1] < button.y + button.height:
                if button.cmd == 2 and not self.hero.in_travel:
                    self.show_records = not self.show_records
                    if self.show_records:
                        self.draw_records()

                return button.cmd

        for object in self.objects:
            if ((pos[0] - object.x) ** 2 + (pos[1] - object.y) ** 2) ** 0.5 <= object.radius + 5:
                self.show_records = False
                self.hero.launch(object)
                return None

        return None

    def draw_records(self):
        req = """
                SELECT start_time, game_time
                FROM records
                WHERE planet_id = ?
              """

        cur = con.cursor()
        self.result = list(cur.execute(req, (str(self.hero.planet.id),)))

        surface = pygame.surface.Surface((300, len(self.result) * 30), pygame.SRCALPHA, 32)

        for i, line in enumerate(sorted(self.result, key=lambda x: int(x[1]))):
            if i <= 5:

                start_time = dt.datetime.fromtimestamp(int(line[0])).strftime('%d %b %Y %H:%M')
                game_time = str(int(line[1]) // 3600).rjust(2, '0') +\
                            ':' +\
                            str((int(line[1]) % 3600) // 60).rjust(2, '0') +\
                            ':' +\
                            str((int(line[1]) % 3600) % 60).rjust(2, '0')

                surface.blit(self.font.render(str(i + 1) + ':  ' + start_time + ' --- ' + game_time, True, 'green'), (0, i * 30))

        self.record_surface = surface


# отвечает за движение планет по карте и рисование эллипсов
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
        a = self.orbit_parent.mass * MAP_GRAVITY / (delta_x ** 2 + delta_y ** 2)
        a_x = delta_x * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)
        a_y = delta_y * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)

        self.speed_x += a_x * MAP_GAME_SPEED / FPS
        self.speed_y += a_y * MAP_GAME_SPEED / FPS

        self.x += self.speed_x * MAP_GAME_SPEED / FPS
        self.y += self.speed_y * MAP_GAME_SPEED / FPS

    def draw_ellipse(self):
        distanse = ((self.orbit_parent.x - self.x) ** 2 + (self.orbit_parent.y - self.y) ** 2) ** 0.5
        speed = (self.speed_x ** 2 + self.speed_y ** 2) ** 0.5

        a = 1 / (2 / distanse - speed ** 2 / (MAP_GRAVITY * self.orbit_parent.mass))
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


# создает звезду - центр системы
class StarOnMap:
    def __init__(self, map, name, mass=100000, radius=20):
        self.map = map
        self.name = name
        self.mass = mass
        self.radius = radius
        self.x, self.y = self.start_position_calculation()
        self.map.objects.append(self)

    def start_position_calculation(self):
        return self.map.map_surface.get_rect().center

    def render(self):
        pygame.draw.circle(self.map.map_surface, 'green', (self.x, self.y), self.radius, 1)

    def update(self):
        self.map.add_text_to_label(self, self.name, 'x: ' + str(self.x), 'y: ' + str(self.y))

    def pos(self):
        return self.x, self.y


# создет планету которая движется вокруг звезды родителя
# при нажатии на карте класс карты возвращает этот объект
# можно получить id уровня на этой планете уровня на этой планете
class PlanetOnMap(StarOnMap, PhysicalObjectOnMap):
    def __init__(self, map, name, id, start_height, start_speed, orbital_parent, apsis_argument, radius=5, mass=0):
        self.id = id

        self.start_height = start_height
        self.start_speed = start_speed
        self.apsis_argument = apsis_argument
        self.orbital_parent = orbital_parent

        StarOnMap.__init__(self, map, name, mass=mass, radius=radius)
        PhysicalObjectOnMap.__init__(self, self.orbital_parent, self.x, self.y, *self.start_speed_calculation(), apsis_argument)

        ellipse_surface, ellipse_surface_coords_delta = self.draw_ellipse()
        self.map.background_surface.blit(ellipse_surface, ellipse_surface_coords_delta)

    def start_position_calculation(self):
        return self.start_height * math.cos(math.radians(self.apsis_argument)) + self.orbital_parent.x, \
               self.start_height * math.sin(math.radians(self.apsis_argument)) + self.orbital_parent.y

    def update(self):
        self.physical_move()
        self.map.add_text_to_label(self, self.name, 'x: ' + str(int(self.x)), 'y: ' + str(int(self.y)))

    def start_speed_calculation(self):
        return self.start_speed * math.cos(math.radians(self.apsis_argument + 90)), \
               self.start_speed * math.sin(math.radians(self.apsis_argument + 90))


class HeroOnMap:
    def __init__(self, map, start_planet):
        self.planet = start_planet
        self.in_travel = False
        self.map = map
        self.map.hero = self
        self.particles = []
        self.particle_counter = 0

        self.angle_for_render = 0

    def render(self):
        for particle in self.particles:
            pygame.draw.rect(self.map.map_surface, 'green', particle)

        if self.in_travel:
            pygame.draw.circle(self.map.map_surface, 'green', (self.x, self.y), 3)

        else:
            pygame.draw.circle(self.map.map_surface, 'green',
                               (self.planet.x +
                                math.cos(math.radians(self.angle_for_render)) * (self.planet.radius + 10),
                                self.planet.y +
                                math.sin(math.radians(self.angle_for_render)) * (self.planet.radius + 10)), 3)

            self.angle_for_render += 180 * MAP_GAME_SPEED / FPS

    def launch(self, target):
        if type(target) != PlanetOnMap:
            return None

        if not self.in_travel:
            self.x, self.y = (self.planet.x +
                                math.cos(math.radians(self.angle_for_render)) * (self.planet.radius + 10),
                                self.planet.y +
                                math.sin(math.radians(self.angle_for_render)) * (self.planet.radius + 10))

            self.planet = target
            self.in_travel = True

            self.particles = []
            self.particle_counter = 0

    def move(self):
        delta_x = self.x - self.planet.x
        delta_y = self.y - self.planet.y
        distanse = (delta_x ** 2 + delta_y ** 2) ** 0.5

        if distanse < self.planet.radius + 10:
            self.in_travel = False
            self.angle_for_render = math.degrees(math.atan(delta_y / delta_x))

            if delta_x < 0:
                self.angle_for_render += 180

        else:
            if type(self.planet) == PlanetOnMap:
                a = (self.planet.speed_x ** 2 + self.planet.speed_y ** 2) ** 0.5 * 1.5 * MAP_GAME_SPEED / FPS

            else:
                a = 60 * MAP_GAME_SPEED / FPS

            self.x += delta_x * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)
            self.y += delta_y * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)

            self.particle_counter = (self.particle_counter + 1) % (10 // a)
            if not self.particle_counter:
                self.particles.append((self.x - 1, self.y - 1, 2, 2))


class Button:
    def __init__(self, x, y, width, heigth, label, cmd):
        self.x = x
        self.y = y
        self.width = width
        self.height = heigth
        self.surface = pygame.surface.Surface((width, heigth), pygame.SRCALPHA, 32)
        self.surface.fill((0, 0, 0, 0))
        pygame.draw.rect(self.surface, 'green', (0, 0, width, heigth), 1)

        font = pygame.font.SysFont(None, 20)
        text = font.render(label, False, (100, 255, 100))
        text_x = width // 2 - text.get_width() // 2
        text_y = heigth // 2 - text.get_height() // 2
        self.surface.blit(text, (text_x, text_y))
        self.cmd = cmd

