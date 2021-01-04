import pygame
import math
import os
import random

GRAVITY = 100
FPS = 60
GAME_SPEED = 1

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


class PlanetarySystem:
    def __init__(self, id, size, planet_radius, planet_mass, color='white'):
        self.id = id
        self.surface = pygame.Surface(size)
        self.all_sprites = pygame.sprite.Group()
        pygame.mouse.set_visible(False)

        self.hero = Spaceship(self.all_sprites, '--Name--', 6570, 0, angle=0, speed_x=0, speed_y=310)
        self.base_planet = Planet(self.all_sprites, 0, 0, planet_radius, planet_mass, color=color)
        self.objects = [self.base_planet]

        self.load_file(None)

    def update(self):
        self.surface.fill('black')
        self.all_sprites.update(self.surface, self.objects, self.hero)
        self.all_sprites.draw(self.surface)

    def load_file(self, filename):
        # пока вместо этого просто создаем все вручную
        self.objects.append(Moon(self.all_sprites, 6420, 0, 0, 310, 100, 0))


class PhysicalObject:
    def __init__(self, x, y, speed_x, speed_y):
        self.render_counter = 0

        self.x = x
        self.y = y

        self.speed_x = speed_x
        self.speed_y = speed_y

    def physical_move(self, a_x=0, a_y=0, planets=[]):
        for planet in planets:
            if planet.mass == 0:
                continue

            delta_x = self.x - planet.x
            delta_y = self.y - planet.y
            a = planet.mass * GRAVITY / (delta_x ** 2 + delta_y ** 2)
            a_x += delta_x * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)
            a_y += delta_y * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)

        self.speed_x += a_x * GAME_SPEED
        self.speed_y += a_y * GAME_SPEED

        self.x += self.speed_x / FPS * GAME_SPEED
        self.y += self.speed_y / FPS * GAME_SPEED


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


class Spaceship(pygame.sprite.Sprite, PhysicalObject, EngineObject):
    def __init__(self, group, name, x, y, angle=0, speed_x=0, speed_y=0, rotation_speed=1, collision_radius=0.75):
        pygame.sprite.Sprite.__init__(self, group)
        PhysicalObject.__init__(self, x, y, speed_x=speed_x, speed_y=speed_y)
        EngineObject.__init__(self, angle, begin_color=(0, 255, 250))

        self.name = name
        self.or_image = load_image("spaceship.png", -1)
        self.or_image = pygame.transform.scale(self.or_image, (40, 40))

        self.rect = self.or_image.get_rect()
        self.image = self.or_image

        self.rect.x, self.rect.y = self.blitRotate((self.x, self.y), (20, 20), self.angle, self.or_image)
        self.rotation_speed = rotation_speed
        self.collision_radius = collision_radius
        self.destroyed = None

    def update(self, surface, objects, hero):
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

            self.physical_move(a_x=a_x, a_y=a_y, planets=objects)

            for object in objects:
                if type(object) == Planet or type(object) == Moon:
                    self.collision_with_planet(object)

        else:
            self.x = self.destroyed[0].x + self.destroyed[1]
            self.y = self.destroyed[0].y + self.destroyed[2]

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


class Planet(pygame.sprite.Sprite):
    def __init__(self, group, x, y, radius, mass, color='white'):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = mass
        self.color = color
        self.image = pygame.surface.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius, 0)

        self.rect = self.image.get_rect()

    def update(self, surface, objects, hero):
        self.rect.x, self.rect.y = self.x - hero.x - self.radius + surface.get_width() // 2, \
                                   self.y - hero.y - self.radius + surface.get_height() // 2


class Moon(Planet, PhysicalObject):
    def __init__(self, group, x, y, speed_x, speed_y, radius, mass, color='white'):
        Planet.__init__(self, group, x, y, radius, mass, color=color)
        PhysicalObject.__init__(self, x, y, speed_x, speed_y)

    def update(self, surface, objects, hero):
        self.physical_move(planets=[objects[0]])
        self.rect.x, self.rect.y = self.x - hero.x - self.radius + surface.get_width() // 2, \
                                   self.y - hero.y - self.radius + surface.get_height() // 2