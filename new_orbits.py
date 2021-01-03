import os
import pygame
import random
import math
import copy

pygame.init()
pygame.mouse.set_visible(False)

GRAVITY = 50
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


class Interface:
    def __init__(self, surface):
        self.interface_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA, 32)
        self.grid_surface = self.draw_background()
        self.labels = dict()
        self.font = pygame.font.SysFont(None, 20)

    def draw_cursor(self, rect_size=10):
        pygame.draw.rect(self.interface_surface, 'green', (pygame.mouse.get_pos()[0] - rect_size // 2,
                                                           pygame.mouse.get_pos()[1] - rect_size // 2,
                                                           rect_size, rect_size), 1)

        pygame.draw.line(self.interface_surface, 'green', (0, pygame.mouse.get_pos()[1]),
                         (pygame.mouse.get_pos()[0] - rect_size // 2, pygame.mouse.get_pos()[1]))

        pygame.draw.line(self.interface_surface, 'green', (self.interface_surface.get_size()[0],
                                                           pygame.mouse.get_pos()[1]),
                         (pygame.mouse.get_pos()[0] + rect_size // 2, pygame.mouse.get_pos()[1]))

        pygame.draw.line(self.interface_surface, 'green', (pygame.mouse.get_pos()[0], 0),
                         (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1] - rect_size // 2))

        pygame.draw.line(self.interface_surface, 'green', (pygame.mouse.get_pos()[0], self.interface_surface.get_size()[1]),
                         (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1] + rect_size // 2))

    def draw_background(self):
        grid_surface = pygame.Surface(self.interface_surface.get_size(), pygame.SRCALPHA, 32)
        grid_surface.fill((0, 0, 0, 0))
        for i in range(1, 160):
            pygame.draw.line(grid_surface, (0, 15, 0), (i * 9, 0), (i * 9, self.interface_surface.get_height()))

        for i in range(1, 100):
            pygame.draw.line(grid_surface, (0, 15, 0), (0, i * 9), (self.interface_surface.get_width(), i * 9))

        for i in range(1, 16):
            pygame.draw.line(grid_surface, (0, 35, 0), (i * 90, 0), (i * 90, self.interface_surface.get_height()))

        for i in range(1, 10):
            pygame.draw.line(grid_surface, (0, 35, 0), (0, i * 90), (self.interface_surface.get_width(), i * 90))

        return grid_surface

    def get_cursor_global_pos(self):
        return map_cam_pos_x - (self.interface_surface.get_width() // 2 - pygame.mouse.get_pos()[0]) * MAP_VIEW_SIZE,\
               map_cam_pos_y - (self.interface_surface.get_height() // 2 - pygame.mouse.get_pos()[1]) * MAP_VIEW_SIZE

    def render_on_map(self):
        self.interface_surface = copy.copy(self.grid_surface)
        self.draw_cursor()
        self.draw_label()

    def draw_label(self):
        for key in self.labels.keys():
            pygame.draw.line(self.interface_surface, 'green', key.pos_on_map(), (key.pos_on_map()[0] + 50, key.pos_on_map()[1] - 50))

            out = self.font.render(' '.join(self.labels[key]), True, 'green')
            self.interface_surface.blit(out, (key.pos_on_map()[0] + 55, key.pos_on_map()[1] - 68))

            pygame.draw.line(self.interface_surface, 'green', (key.pos_on_map()[0] + 50, key.pos_on_map()[1] - 50),
                             (key.pos_on_map()[0] + 50 + out.get_width(), key.pos_on_map()[1] - 50))

    def add_text_to_label(self, obj, *args):
        self.labels[obj] = list(map(str, args))


class OrbitMarker:
    def __init__(self, line_life=0):
        self.marker_on = True
        self.line_life = line_life
        self.particles = []
        self.particle_counter = 0
        self.render_counter = 0
        self.marker_surface = pygame.Surface((0, 0), pygame.SRCALPHA, 32)
        self.render_shift = random.randrange(0, 5)

    def make_line(self):
        self.particle_counter = (self.particle_counter + 1) % 2

        if self.line_life != 0:
            if self.marker_on and self.particle_counter == 0:
                self.particles.append([(self.x, self.y), self.line_life])

            self.particles = list(map(lambda x: [x[0], x[1] - 1], self.particles))
            self.particles = list(filter(lambda x: x[1] > 10, self.particles))

    def render_line(self, surface):
        self.render_counter = (self.render_counter + 1) % 5

        if self.render_counter == self.render_shift:
            self.marker_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA, 32)
            self.marker_surface.fill((0, 0, 0, 0))

            coef = 200 / self.line_life
            for particle in self.particles:
                pygame.draw.circle(self.marker_surface, (int(particle[1] * coef), int(particle[1] * coef), int(particle[1] * coef)),
                                   particle[0], 2, 0)

        surface.blit(self.marker_surface, (0, 0))


class PhysicalObject:
    def __init__(self, x, y, speed_x=0, speed_y=0, orbit_parent=None):
        self.render_counter = 0

        self.x = x + 1
        self.y = y + 1

        # moon.x and y != planet.x and y !!!
        self.orbit_parent = orbit_parent
        # orbit_parent uses only for stable orbit

        self.speed_x = speed_x
        self.speed_y = speed_y

        # semi-axis of an ellipse

        if orbit_parent:
            self.calclulate_orbit_ellipse_semi_axis()
            self.orbit_type = 'Unknown orbit'

            self.x_ellipse, self.y_ellipse = 0, 0

        else:
            self.orbit_type = 'Unstable orbit'

        self.draw_orbit_ellipse()

    def physical_move(self, a_x=0, a_y=0, planets=None):
        if self.orbit_parent is None:
            for planet in planets:
                if planet.mass == 0:
                    continue
                delta_x = self.x - planet.x
                delta_y = self.y - planet.y
                a = planet.mass * GRAVITY / (delta_x ** 2 + delta_y ** 2)
                a_x += delta_x * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)
                a_y += delta_y * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)

        else:
            delta_x = self.x - self.orbit_parent.x
            delta_y = self.y - self.orbit_parent.y
            a = self.orbit_parent.mass * GRAVITY / (delta_x ** 2 + delta_y ** 2)
            a_x += delta_x * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)
            a_y += delta_y * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)

        self.speed_x += a_x * GAME_SPEED
        self.speed_y += a_y * GAME_SPEED

        self.x += self.speed_x / FPS * GAME_SPEED
        self.y += self.speed_y / FPS * GAME_SPEED

    def calclulate_orbit_ellipse_semi_axis(self):
        distanse = ((self.orbit_parent.x - self.x) ** 2 + (self.orbit_parent.y - self.y) ** 2) ** 0.5
        speed = (self.speed_x ** 2 + self.speed_y ** 2) ** 0.5

        self.a = 1 / (2 / distanse - speed ** 2 / (GRAVITY * self.orbit_parent.mass) / FPS)
        self.e = (self.a - distanse) / self.a
        self.b = self.a * (1 - self.e ** 2) ** 0.5

    def calculate_periapsis(self):
        return self.a * (1 - self.e)

    def calculate_apoapsis(self):
        return self.a * (1 + self.e)

    def draw_orbit_ellipse(self):
        self.calculate_orbit_ellipse()

        if self.orbit_type != 'Stable orbit':
            return None

        x_ellipse = map_view.get_width() // 2 - (
                    map_cam_pos_x - int(self.orbit_parent.x - self.calculate_periapsis())) / MAP_VIEW_SIZE
        y_ellipse = map_view.get_height() // 2 - (
                    map_cam_pos_y - int(self.orbit_parent.y - self.b)) / MAP_VIEW_SIZE

        pygame.draw.ellipse(map_view, (0, 100, 0),
                            (x_ellipse, y_ellipse, int(self.a * 2 / MAP_VIEW_SIZE), int(self.b * 2 / MAP_VIEW_SIZE)), 1)

    def calculate_orbit_ellipse(self):
        if self.orbit_type == 'Unknown orbit' and -1 < abs(self.on_apse_line()) - 90 < 1:
            self.orbit_type = 'Stable orbit'
            self.apocenter_argument = math.degrees(math.atan((self.orbit_parent.x - self.x) / (self.orbit_parent.y - self.y)))

            self.ellipse_surface = pygame.Surface((int(self.a * 2 / 250), int(self.b * 2 / 250)), pygame.SRCALPHA, 32)
            self.ellipse_surface.fill((0, 0, 0, 0))

            # pygame.draw.ellipse(self.ellipse_surface, (0, 100, 0),
                                # (0, 0, int(self.a * 2 / MAP_VIEW_SIZE), int(self.b * 2 / MAP_VIEW_SIZE)), 1)

        else:
            return None

    def on_apse_line(self):
        speed_angle = math.degrees(math.atan(self.speed_x / self.speed_y))
        pos_angle = math.degrees(math.atan((self.orbit_parent.x - self.x) / (self.orbit_parent.y - self.y)))
        return speed_angle + pos_angle


class EngineObject:
    def __init__(self, angle, max_thrust=0.5,
                 begin_color=(255, 0, 0), end_color=(0, 0, 0),
                 engine_particle_speed=200, engine_particle_angle=15, engine_particle_life=30, engine_position=(13, 0)):

        self.angle = angle
        self.max_thrust = max_thrust

        self.begin_color = begin_color
        self.end_color = end_color
        self.engine_particle_speed = engine_particle_speed
        self.engine_particle_angle = engine_particle_angle
        self.engine_particle_life = engine_particle_life
        self.engine_position = engine_position

        self.engine_particles = []
        self.engine_particles_counter = 0

    def engine_on(self):
        if GAME_SPEED != 1:
            return 0, 0

        if self.engine_particles_counter == 0:
            self.engine_particles.append([(self.x - self.engine_position[0] * math.cos(math.radians(self.angle + self.engine_position[1])),
                                           self.y - self.engine_position[0] * math.sin(math.radians(self.angle + self.engine_position[1]))),
                                          ((self.speed_x - self.engine_particle_speed * math.cos(math.radians(self.angle + random.randrange(-self.engine_particle_angle, self.engine_particle_angle)))) / FPS,
                                           (self.speed_y - self.engine_particle_speed * math.sin(math.radians(self.angle + random.randrange(-self.engine_particle_angle, self.engine_particle_angle)))) / FPS),
                                          self.engine_particle_life + random.randrange(-10, 10)])

        return self.max_thrust * math.cos(math.radians(self.angle)),\
               self.max_thrust * math.sin(math.radians(self.angle))

    def update_and_render_engine_particles(self, surface):
        self.engine_particles_counter = (self.engine_particles_counter + 1) % 2

        self.engine_particles = list(map(lambda x: [(x[0][0] + x[1][0], x[0][1] + x[1][1]), x[1], x[2] - 1], self.engine_particles))
        self.engine_particles = list(filter(lambda x: x[2] > 3, self.engine_particles))

        for i, particle in enumerate(self.engine_particles):
            pygame.draw.circle(surface, self.calculate_particle_color(particle),
                               (particle[0][0] - self.x + surface.get_width() // 2, particle[0][1] - self.y + surface.get_height() // 2), 3, 0)

    def calculate_particle_color(self, particle):
        new_color = []
        for i in range(3):
            new_color.append((self.begin_color[i] * particle[2] + self.end_color[i] * (self.engine_particle_life - particle[2])) / (self.engine_particle_life + 10))

        return tuple(new_color)


class Spaceship(pygame.sprite.Sprite, PhysicalObject, EngineObject, OrbitMarker):
    def __init__(self, group, name, x, y, angle=0, speed_x=0, speed_y=0, rotation_speed=1, collision_radius=0.75):
        pygame.sprite.Sprite.__init__(self, group)
        PhysicalObject.__init__(self, x, y, speed_x=speed_x, speed_y=speed_y)
        EngineObject.__init__(self, angle, begin_color=(0, 255, 250))
        OrbitMarker.__init__(self, line_life=900)

        self.name = name
        self.or_image = load_image("spaceship.png", -1)
        self.or_image = pygame.transform.scale(self.or_image, (40, 40))

        self.or_map_image = load_image("spaceship_on_map.png", -1)
        self.or_map_image = pygame.transform.scale(self.or_map_image, (20, 20))

        self.rect = self.or_image.get_rect()
        self.image = self.or_image

        self.rect.x, self.rect.y = self.blitRotate((self.x, self.y), (20, 20), self.angle, self.or_image)
        self.rotation_speed = rotation_speed
        self.collision_radius = collision_radius
        self.destroyed = None

    def update(self, surface):
        if not self.destroyed:
            a_x = 0
            a_y = 0

            keys = pygame.key.get_pressed()

            if keys[pygame.K_SPACE]:
                a_x, a_y = self.engine_on()

            if keys[pygame.K_RIGHT]:
                self.angle = (self.angle + self.rotation_speed) % 360

            if keys[pygame.K_LEFT]:
                self.angle = (self.angle - self.rotation_speed) % 360

            self.physical_move(a_x=a_x, a_y=a_y, planets=planets)

            for planet in planets:
                self.collision_with_planet(planet)

        else:
            self.x = self.destroyed[0].x + self.destroyed[1]
            self.y = self.destroyed[0].y + self.destroyed[2]

        self.make_line()

        if map_mode:
            self.render_line(surface)
            self.rect.x, self.rect.y = self.blitRotate((surface.get_width() // 2 + (self.x - map_cam_pos_x) / MAP_VIEW_SIZE,
                                                        surface.get_height() // 2 + (self.y - map_cam_pos_y) / MAP_VIEW_SIZE),
                                                       (10, 10), self.angle + 45, self.or_map_image)

        else:
            self.rect.x, self.rect.y = self.blitRotate((surface.get_width() // 2, surface.get_height() // 2), (20, 20), self.angle, self.or_image)
            self.update_and_render_engine_particles(surface)

    # ЭТУ ФУНКЦИЮ Я ЧЕСТНОГО УКРАЛ
    def blitRotate(self, pos, originPos, angle, image):

        angle = - angle - 90
        # calcaulate the axis aligned bounding box of the rotated image
        w, h = image.get_size()
        box = [pygame.math.Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
        box_rotate = [p.rotate(angle) for p in box]
        min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
        max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])

        # calculate the translation of the pivot
        pivot = pygame.math.Vector2(originPos[0], -originPos[1])
        pivot_rotate = pivot.rotate(angle)
        pivot_move = pivot_rotate - pivot

        # calculate the upper left origin of the rotated image
        origin = (pos[0] - originPos[0] + min_box[0] - pivot_move[0], pos[1] - originPos[1] - max_box[1] + pivot_move[1])

        # get a rotated image
        self.image = pygame.transform.rotate(image, angle)

        return origin

    def collision_with_planet(self, planet):
        global GAME_SPEED
        delta_x = self.x - planet.x
        delta_y = self.y - planet.y
        distanse = (delta_x ** 2 + delta_y ** 2) ** 0.5
        if distanse < self.collision_radius + planet.radius:
            self.destroyed = planet, delta_x, delta_y
            self.marker_on = False

    def pos_on_map(self):
        return map_view.get_width() // 2 + (self.x - map_cam_pos_x) / MAP_VIEW_SIZE,\
               map_view.get_height() // 2 + (self.y - map_cam_pos_y) / MAP_VIEW_SIZE


class Planet:
    def __init__(self, name, x, y, radius, mass, color='white'):
        self.name = name
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = mass
        self.color = color
        planets.append(self)

    def update(self):
        interface.add_text_to_label(self, self.name, 'x: ' + str(self.x), 'y: ' + str(self.y))

    def render_on_map(self):
        pygame.draw.circle(map_view, 'green', self.pos_on_map(), self.radius / MAP_VIEW_SIZE, 1)

    def render_on_hero_view(self):
        pygame.draw.circle(hero_view, self.color,
                           (hero_view.get_width() // 2 + (self.x - hero.x),
                            hero_view.get_height() // 2 + (self.y - hero.y)),
                           self.radius, 0)

    def pos_on_map(self):
        return map_view.get_width() // 2 + (self.x - map_cam_pos_x) / MAP_VIEW_SIZE,\
               map_view.get_height() // 2 + (self.y - map_cam_pos_y) / MAP_VIEW_SIZE


class Moon(PhysicalObject, OrbitMarker, Planet):
    def __init__(self, name, x, y, radius, mass, speed_x, speed_y, orbit_parent, color='white'):
        PhysicalObject.__init__(self, x, y, speed_x=speed_x, speed_y=speed_y, orbit_parent=orbit_parent)
        OrbitMarker.__init__(self, line_life=3600)
        Planet.__init__(self, name, x, y, radius, mass, color)

    def update(self):
        self.physical_move(planets=planets)
        interface.add_text_to_label(self, self.name, 'x: ' + str(int(self.x)), 'y: ' + str(int(self.y)), self.orbit_type)


map_mode = False
window_size = 2880 // 2, 1800 // 2
screen = pygame.display.set_mode(window_size, pygame.FULLSCREEN)
screen.fill('black')


map_view = pygame.Surface(screen.get_size())
hero_view = pygame.Surface(screen.get_size())
interface = Interface(screen)
interface.render_on_map()

map_cam_pos = map_cam_pos_x, map_cam_pos_y = 360000, 225000
focus_object = None

all_sprites = pygame.sprite.Group()
pygame.mouse.set_visible(True)

hero = Spaceship(all_sprites, '--Name--', 201100, 225000, angle=0, speed_x=0, speed_y=160)

planets = []

base_planet = Planet('Alpha', 360000, 225000, 6000, 100000)
moon = Moon('Phi', 200000, 225000, 1000, 5000, 0, 45, base_planet)
moon_2 = Moon('Tau', 250000, 226000, 1000, 5000, 0, 45, base_planet)
moon_3 = Moon('Theta', 260000, 226000, 1000, 5000, 0, 40, base_planet)


running = True
clock = pygame.time.Clock()

REDRAW_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(REDRAW_EVENT, 10)

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == REDRAW_EVENT:
            if focus_object:
                map_cam_pos = map_cam_pos_x, map_cam_pos_y = focus_object.x, focus_object.y

            map_view.fill((0, 10, 0))
            hero_view.fill('black')

            for planet in planets:
                planet.update()

            if map_mode:
                interface.render_on_map()
                map_view.blit(interface.interface_surface, (0, 0))
                pygame.mouse.set_visible(False)
                all_sprites.update(map_view)
                all_sprites.draw(map_view)

                for planet in planets:
                    planet.render_on_map()

                    # for test

                    if type(planet) == Moon:
                        planet.draw_orbit_ellipse()

                screen.blit(map_view, (0, 0))

            else:
                pygame.mouse.set_visible(True)
                all_sprites.update(hero_view)
                all_sprites.draw(hero_view)

                for planet in planets:
                    planet.render_on_hero_view()

                screen.blit(hero_view, (0, 0))

        # control

        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            map_mode = not map_mode

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHTBRACKET and GAME_SPEED < 5 ** 5:
            GAME_SPEED *= 5

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFTBRACKET and GAME_SPEED > 1:
            GAME_SPEED //= 5

        elif event.type == pygame.MOUSEWHEEL:
            MAP_VIEW_SIZE -= event.y

            if MAP_VIEW_SIZE > 500:
                MAP_VIEW_SIZE = 500

            elif MAP_VIEW_SIZE < 5:
                MAP_VIEW_SIZE = 5

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            cur_pos = interface.get_cursor_global_pos()
            for planet in planets:
                if ((planet.x - cur_pos[0]) ** 2 + (planet.y - cur_pos[1]) ** 2) ** 0.5 <= planet.radius + MAP_VIEW_SIZE * 3:
                    focus_object = planet
                    break

    pygame.display.flip()
pygame.quit()