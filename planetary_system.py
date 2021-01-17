import pygame
import math
import os
import copy
import random

GRAVITY = 100
FPS = 60
MAP_SIZE = 100


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
    def __init__(self, id, size):
        self.font = pygame.font.SysFont(None, 20)
        self.game_speed = 1
        self.id = id
        self.surface = pygame.Surface(size)

        self.all_view_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.map_mode = False
        pygame.mouse.set_visible(False)

        self.hero = None
        self.objects = []

        self.background = self.draw_background()
        self.stars = []
        self.create_stars()
        self.simulation_points = []

        self.enemies_counter = 0
        self.win = False

        self.time_counter = 0

    def update(self):
        self.surface.fill('black')
        if self.win:
            self.surface.blit(self.background, (0, 0))
            self.surface.blit(self.font.render('all enemies destroyed', True, 'green'), (20, 20))
            self.surface.blit(self.font.render('all systems nominal', True, 'green'), (20, 45))
            self.surface.blit(self.font.render('your time: ' + str(self.time_counter), True, 'green'), (20, 70))
            self.draw_cursor()

            return None

        if self.hero.destroyed:
            self.surface.blit(self.background, (0, 0))
            self.surface.blit(self.font.render('no signal', True, 'green'), (20, 20))
            self.surface.blit(self.font.render('transmitter not responding', True, 'green'), (20, 45))
            self.surface.blit(self.font.render('reboot failed', True, 'green'), (20, 70))
            self.draw_cursor()

            return None

        if self.map_mode:
            self.surface.blit(self.background, (0, 0))

        else:
            self.draw_stars()

        self.all_view_sprites.draw(self.surface)
        self.all_view_sprites.update(self)

        self.bullets.draw(self.surface)
        self.bullets.update(self)

        self.hero.draw_interface(self)
        self.surface.blit(self.hero.interface_surface, (0, 0))

        if self.map_mode:
            self.surface.blit(self.font.render('MAP mode', True, 'green'), (20, 20))
            self.draw_cursor()
            for point in self.simulation_points:
                pygame.draw.circle(self.surface, (0, 100, 0), point, 1)

        if self.enemies_counter == 0:
            self.win = True

        self.time_counter += self.game_speed

    def load_object(self, line):
        line = line.split(', ')
        if line[0] == 'planet':
            self.objects.append(Planet(self.all_view_sprites,
                                       int(line[1]),
                                       int(line[2]),
                                       int(line[3]),
                                       int(line[4]),
                                       str(line[5]),
                                       int(line[6])))

        elif line[0] == 'moon':
            self.objects.append(Moon(self.all_view_sprites,
                                     int(line[1]),
                                     int(line[2]),
                                     float(line[5]),
                                     float(line[6]),
                                     int(line[3]),
                                     int(line[4]),
                                     str(line[7]),
                                     int(line[8])))

        elif line[0] == 'enemy':
            self.objects.append(Enemy(self,
                                      int(line[1]),
                                      int(line[2]),
                                      int(line[3]),
                                      float(line[4]),
                                      float(line[5]),
                                      orbit_parent=self.objects[int(line[6])],
                                      hp=int(line[7])))

    def draw_cursor(self, rect_size=10):
        pygame.draw.rect(self.surface, 'green', (pygame.mouse.get_pos()[0] - rect_size // 2,
                                                 pygame.mouse.get_pos()[1] - rect_size // 2,
                                                 rect_size, rect_size), 1)

        pygame.draw.line(self.surface, 'green', (0, pygame.mouse.get_pos()[1]),
                         (pygame.mouse.get_pos()[0] - rect_size // 2, pygame.mouse.get_pos()[1]))

        pygame.draw.line(self.surface, 'green', (self.surface.get_size()[0],
                                                 pygame.mouse.get_pos()[1]),
                         (pygame.mouse.get_pos()[0] + rect_size // 2, pygame.mouse.get_pos()[1]))

        pygame.draw.line(self.surface, 'green', (pygame.mouse.get_pos()[0], 0),
                         (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1] - rect_size // 2))

        pygame.draw.line(self.surface, 'green',
                         (pygame.mouse.get_pos()[0], self.surface.get_size()[1]),
                         (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1] + rect_size // 2))

    def draw_background(self):
        grid_surface = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA, 32)
        grid_surface.fill((0, 0, 0, 0))
        for i in range(1, 160):
            pygame.draw.line(grid_surface, (0, 15, 0), (i * 9, 0), (i * 9, self.surface.get_height()))

        for i in range(1, 100):
            pygame.draw.line(grid_surface, (0, 15, 0), (0, i * 9), (self.surface.get_width(), i * 9))

        for i in range(1, 16):
            pygame.draw.line(grid_surface, (0, 35, 0), (i * 90, 0), (i * 90, self.surface.get_height()))

        for i in range(1, 10):
            pygame.draw.line(grid_surface, (0, 35, 0), (0, i * 90), (self.surface.get_width(), i * 90))

        return grid_surface

    def create_stars(self):
        for i in range(100):
            x = random.randrange(0, self.surface.get_width())
            y = random.randrange(0, self.surface.get_height())
            luminosity = random.randrange(50, 255)
            size = random.randrange(1, 3)
            self.stars.append([x, y, luminosity, size])

    def draw_stars(self):
        for star in self.stars:
            star[0] -= self.hero.speed_x * star[2] / 50000 * self.game_speed
            star[1] -= self.hero.speed_y * star[2] / 50000 * self.game_speed

            if - 10 > star[0]:
                star[0] = self.surface.get_width()
                star[1] = random.randrange(0, self.surface.get_height())

            elif star[0] > self.surface.get_width() + 10:
                star[0] = 0
                star[1] = random.randrange(0, self.surface.get_height())

            if - 10 > star[1]:
                star[1] = self.surface.get_height()
                star[0] = random.randrange(0, self.surface.get_width())

            elif star[1] > self.surface.get_height() + 10:
                star[1] = 0
                star[0] = random.randrange(0, self.surface.get_width())

            pygame.draw.circle(self.surface, (star[2], star[2], star[2]), (star[0], star[1]), star[3])

    def simulation(self):
        points = []
        counter = 0
        simulation_objects = list(map(lambda x: VirtualObject(x), self.objects))
        simulation_objects.append(VirtualObject(self.hero))
        for step in range(2500):
            counter = (counter + 1) % 10
            for object in simulation_objects:
                if type(object.parent) == Spaceship or type(object.parent) == Enemy:
                    if not counter:
                        points.append((self.surface.get_width() // 2 + object.x / MAP_SIZE,
                                       self.surface.get_height() // 2 + object.y / MAP_SIZE))

                object.move(10, simulation_objects)

        self.simulation_points = points


class PhysicalObject:
    def __init__(self, x, y, speed_x, speed_y):
        self.render_counter = 0

        self.x = x
        self.y = y

        self.speed_x = speed_x
        self.speed_y = speed_y

    def calclulate_acceleration_for_obj(self, obj):
        if obj == self:
            return 0, 0
        delta_x = self.x - obj.x
        delta_y = self.y - obj.y

        a = obj.mass * GRAVITY / (delta_x ** 2 + delta_y ** 2)
        a_x = delta_x * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)
        a_y = delta_y * -a / ((delta_x ** 2 + delta_y ** 2) ** 0.5)

        return a_x, a_y

    def calculate_next_position(self, game_speed, position, speed, acceleration):
        speed[0] += acceleration[0] * game_speed
        speed[1] += acceleration[1] * game_speed

        position[0] += speed[0] / FPS * game_speed
        position[1] += speed[1] / FPS * game_speed

        return position[0], position[1], speed[0], speed[1]

    def physical_move(self, game_speed, a_x=0, a_y=0, planets=[]):
        for planet in planets:
            if type(planet) != Planet and type(planet) != Moon and type(planet) != VirtualObject:
                continue

            if planet.mass != 0:
                a = self.calclulate_acceleration_for_obj(planet)
                a_x += a[0]
                a_y += a[1]

        self.x, self.y, self.speed_x, self.speed_y = self.calculate_next_position(game_speed,
                                                                                  [self.x, self.y],
                                                                                  [self.speed_x, self.speed_y],
                                                                                  [a_x, a_y])


class EngineObject:
    def __init__(self, angle, max_thrust=0.5,
                 begin_color=(255, 0, 0), end_color=(0, 0, 0),
                 engine_particle_speed=300, engine_particle_angle=15, engine_particle_life=60, engine_position=(13, 0)):

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

    def engine_on(self, game_speed):
        if game_speed != 1:
            return 0, 0

        if self.engine_particles_counter == 0:
            self.engine_particles.append(
                [(self.x - self.engine_position[0] * math.cos(math.radians(self.angle + self.engine_position[1])),
                  self.y - self.engine_position[0] * math.sin(math.radians(self.angle + self.engine_position[1]))),
                 ((self.speed_x - self.engine_particle_speed * math.cos(math.radians(
                     self.angle + random.randrange(-self.engine_particle_angle, self.engine_particle_angle)))) / FPS,
                  (self.speed_y - self.engine_particle_speed * math.sin(math.radians(
                      self.angle + random.randrange(-self.engine_particle_angle, self.engine_particle_angle)))) / FPS),
                 self.engine_particle_life + random.randrange(-10, 10)])

        return self.max_thrust * math.cos(math.radians(self.angle)), \
               self.max_thrust * math.sin(math.radians(self.angle))

    def update_and_render_engine_particles(self, surface):
        self.engine_particles_counter = (self.engine_particles_counter + 1) % 2

        self.engine_particles = list(
            map(lambda x: [(x[0][0] + x[1][0], x[0][1] + x[1][1]), x[1], x[2] - 1], self.engine_particles))
        self.engine_particles = list(filter(lambda x: x[2] > 3, self.engine_particles))

        centre_x = surface.get_width() // 2
        centre_y = surface.get_height() // 2

        for i, particle in enumerate(self.engine_particles):
            pygame.draw.circle(surface, self.calculate_particle_color(particle),
                               (particle[0][0] - self.x + centre_x,
                                particle[0][1] - self.y + centre_y), 3, 0)
        # self.draw_speed_vector(surface)

    def draw_speed_vector(self, surface):
        import math
        rad = math.pi / 180
        thickness = 3
        centre_x = surface.get_width() // 2
        centre_y = surface.get_height() // 2
        start = (centre_x, centre_y)
        end = (start[0] + self.speed_x, start[1] + self.speed_y)
        rotation = (math.atan2(start[1] - end[1], end[0] - start[0])) + math.pi / 2
        trirad = 1
        pygame.draw.line(surface, 'green', start, end, thickness)
        pygame.draw.polygon(surface, 'green', ((end[0] + trirad * math.sin(rotation),
                                                end[1] + trirad * math.cos(rotation)),
                                               (end[0] + trirad * math.sin(rotation - 120 * rad),
                                                end[1] + trirad * math.cos(rotation - 120 * rad)),
                                               (end[0] + trirad * math.sin(rotation + 120 * rad),
                                                end[1] + trirad * math.cos(rotation + 120 * rad))))

    def calculate_particle_color(self, particle):
        new_color = []
        for i in range(3):
            new_color.append(
                (self.begin_color[i] * particle[2] + self.end_color[i] * (self.engine_particle_life - particle[2])) / (
                        self.engine_particle_life + 10))

        return tuple(new_color)


class Spaceship(pygame.sprite.Sprite, PhysicalObject, EngineObject):
    def __init__(self, group, x, y, angle, speed_x, speed_y, rotation_speed=1, collision_radius=10):
        pygame.sprite.Sprite.__init__(self, group)
        PhysicalObject.__init__(self, x, y, speed_x=speed_x, speed_y=speed_y)
        EngineObject.__init__(self, angle, begin_color=(0, 255, 250))

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
        self.weapons = dict()
        self.interface_surface = pygame.surface.Surface((0, 0))
        self.hp = 30

    def fire(self, id):
        self.weapons[id].fire()

    def add_weapon(self, weapon, id):
        self.weapons[id] = weapon
        self.weapons[id].set_owner(self)

    def update(self, system):
        if not self.destroyed and not system.win:
            dmg = pygame.sprite.spritecollideany(self, system.bullets)
            if dmg and dmg.timer > 30:
                self.hp -= dmg.damage
                dmg.destroy()

            if self.hp <= 0:
                self.destroyed = True
                return None

            a_x = 0
            a_y = 0

            keys = pygame.key.get_pressed()

            if keys[pygame.K_SPACE]:
                a_x, a_y = self.engine_on(system.game_speed)

            if keys[pygame.K_RIGHT]:
                self.angle = (self.angle + self.rotation_speed) % 360

            if keys[pygame.K_LEFT]:
                self.angle = (self.angle - self.rotation_speed) % 360

            if keys[pygame.K_f]:
                self.fire(1)

            if keys[pygame.K_g]:
                self.fire(2)

            self.physical_move(system.game_speed, a_x=a_x, a_y=a_y, planets=system.objects)

            for object in system.objects:
                if type(object) == Planet or type(object) == Moon:
                    self.collision_with_planet(object)

        elif self.destroyed:
            self.x = self.destroyed[0].x + self.destroyed[1]
            self.y = self.destroyed[0].y + self.destroyed[2]

        if not system.map_mode:
            self.render_on_view(system.surface)

        else:
            self.render_on_map(system.surface)

        for key in self.weapons.keys():
            self.weapons[key].update()

    def render_on_view(self, surface):
        self.rect.x, self.rect.y = self.blitRotate((surface.get_width() // 2, surface.get_height() // 2), (20, 20),
                                                   self.angle, self.or_image)
        self.update_and_render_engine_particles(surface)

    def render_on_map(self, surface):
        self.rect.x, self.rect.y = self.blitRotate((surface.get_width() // 2 + self.x / MAP_SIZE,
                                                    surface.get_height() // 2 + self.y / MAP_SIZE),
                                                   (10, 10), self.angle + 45, self.or_map_image)

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
        origin = (
            pos[0] - originPos[0] + min_box[0] - pivot_move[0], pos[1] - originPos[1] - max_box[1] + pivot_move[1])

        # get a rotated image
        self.image = pygame.transform.rotate(image, angle)

        return origin

    def collision_with_planet(self, planet):
        delta_x = self.x - planet.x
        delta_y = self.y - planet.y
        distanse = (delta_x ** 2 + delta_y ** 2) ** 0.5
        if distanse < self.collision_radius + planet.radius:
            self.destroyed = planet, delta_x, delta_y
            self.marker_on = False

    def draw_interface(self, system):
        self.interface_surface = pygame.surface.Surface(system.surface.get_size(), pygame.SRCALPHA, 32)
        self.interface_surface.fill((0, 0, 0, 0))

        for i, key in enumerate(self.weapons.keys()):
            weapon = self.weapons[key]
            self.interface_surface.blit(weapon.image,
                                        (self.interface_surface.get_width() - (i + 1) * 140,
                                         self.interface_surface.get_height() - 240))

            for j in range(weapon.magazine_size):
                if j < weapon.magazine_filling:
                    self.interface_surface.blit(weapon.bullet_image,
                                 (self.interface_surface.get_width() - (i + 1) * 140 + 100,
                                  self.interface_surface.get_height() - 240 + j * weapon.bullet_image.get_height()))

                else:
                    self.interface_surface.blit(weapon.bullet_image_hollow,
                                 (self.interface_surface.get_width() - (i + 1) * 140 + 100,
                                  self.interface_surface.get_height() - 240 + j * weapon.bullet_image.get_height()))

        for i in range(self.hp):
            pygame.draw.rect(self.interface_surface, 'white', (20 + i * 10, 20, 8, 20))

        for i in range(system.enemies_counter):
            pygame.draw.rect(self.interface_surface, 'white', (20 + i * 10, 42, 8, 20))


class Planet(pygame.sprite.Sprite):
    def __init__(self, group, x, y, radius, mass, filename, atmosphere_height):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = mass
        self.atmosphere_height = atmosphere_height

        self.or_map_image = pygame.surface.Surface((radius * 2 // MAP_SIZE, radius * 2 // MAP_SIZE), pygame.SRCALPHA,
                                                   32)
        self.or_map_image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.or_map_image, 'green',
                           (radius // MAP_SIZE, radius // MAP_SIZE),
                           radius // MAP_SIZE, 1)

        self.or_image = self.draw_planet(filename, atmosphere_height)
        self.image = self.or_image
        self.rect = self.image.get_rect()

    def update(self, system):
        if not system.map_mode:
            self.render_on_view(system.surface, system.hero)

        else:
            self.render_on_map(system.surface)

    def render_on_view(self, surface, hero):
        self.image = self.or_image
        self.rect.x, self.rect.y = self.x - hero.x - self.radius + surface.get_width() // 2, \
                                   self.y - hero.y - self.radius + surface.get_height() // 2

    def render_on_map(self, surface):
        self.image = self.or_map_image
        self.rect.x, self.rect.y = surface.get_width() // 2 + (self.x - self.radius) / MAP_SIZE, \
                                   surface.get_height() // 2 + (self.y - self.radius) / MAP_SIZE

    def draw_planet(self, filename, atmosphere_height):
        image = pygame.surface.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA, 32)
        image.fill((0, 0, 0, 0))
        planet = load_image(filename, -1)
        planet = pygame.transform.scale(planet, ((self.radius - atmosphere_height) * 2,
                                                 (self.radius - atmosphere_height) * 2))

        if atmosphere_height:
            for h in range(0, atmosphere_height, 5):
                pygame.draw.circle(image, (10, 50, 100, h * (255 // atmosphere_height)),
                                   (self.radius, self.radius),
                                   self.radius - h)

        image.blit(planet, (atmosphere_height, atmosphere_height))
        return image


class Moon(Planet, PhysicalObject):
    def __init__(self, group, x, y, speed_x, speed_y, radius, mass, filename, atmosphere_height):
        Planet.__init__(self, group, x, y, radius, mass, filename, atmosphere_height)
        PhysicalObject.__init__(self, x, y, speed_x, speed_y)

    def update(self, system):
        if not system.map_mode:
            self.render_on_view(system.surface, system.hero)

        else:
            self.render_on_map(system.surface)

        self.physical_move(system.game_speed, planets=[system.objects[0]])


class VirtualObject(PhysicalObject):
    def __init__(self, parent):
        self.parent = parent
        self.x = parent.x
        self.y = parent.y

        if type(parent) == Planet:
            self.speed_x, self.speed_y = 0, 0

        else:
            self.speed_x, self.speed_y = parent.speed_x, parent.speed_y

        if type(parent) == Spaceship or type(parent) == Enemy:
            self.mass = 0

        else:
            self.mass = parent.mass

        PhysicalObject.__init__(self, self.x, self.y, self.speed_x, self.speed_y)

    def move(self, simulation_step, simulation_objects):
        if type(self.parent) != Planet:
            self.physical_move(simulation_step, planets=simulation_objects)


from weapon import Bullet, Shell, Weapon


class Enemy(pygame.sprite.Sprite, PhysicalObject):
    def __init__(self, system, x, y, angle, speed_x, speed_y, rotation_speed=1, orbit_parent=None, hp=50):
        pygame.sprite.Sprite.__init__(self, system.all_view_sprites)
        PhysicalObject.__init__(self, x, y, speed_x=speed_x, speed_y=speed_y)

        self.angle = angle

        self.or_image = load_image("spaceship.png", -1)
        self.or_image = pygame.transform.scale(self.or_image, (40, 40))

        self.or_map_image = load_image("spaceship_on_map.png", -1)
        self.or_map_image = pygame.transform.scale(self.or_map_image, (20, 20))

        self.rect = self.or_image.get_rect()
        self.image = self.or_image

        self.rect.x, self.rect.y = self.blitRotate((self.x, self.y), (20, 20), self.angle, self.or_image)
        self.rotation_speed = rotation_speed
        self.orbit_parent = orbit_parent
        self.hp = hp

        self.weapon = Weapon('minigun_sprite.png', 'shell.png', life_span=500,
                             magazine_size=60,
                             reload_time=1,
                             bullet_speed=100,
                             cooldown=40)
        self.weapon.set_owner(self)
        self.weapon.set_group(system.bullets)

        self.interface_surface = pygame.surface.Surface((0, 0))
        system.enemies_counter += 1

    def fire(self):
        self.weapon.fire()

    def destroy(self, system):
        system.enemies_counter -= 1
        self.kill()
        del self

    def update(self, system):
        dmg = pygame.sprite.spritecollideany(self, system.bullets)
        if dmg and dmg.timer > dmg.spawn_no_damage:
            self.hp -= dmg.damage
            dmg.destroy()

        if self.hp <= 0:
            self.destroy(system)

        if not system.map_mode:
            self.render_on_view(system.surface, system.hero)

        else:
            self.render_on_map(system.surface)

        if self.hero_distanse(system.hero) < 1000:
            if (self.angle + self.hero_angle(system.hero)) % 360 < 180:
                self.angle = (self.angle - self.rotation_speed) % 360

            else:
                self.angle = (self.angle + self.rotation_speed) % 360

        if self.hero_distanse(system.hero) < 500 and -20 < (self.angle + self.hero_angle(system.hero)) % 360 < 20:
            self.fire()

        if self.orbit_parent:
            self.physical_move(system.game_speed, planets=[self.orbit_parent])

        else:
            self.physical_move(system.game_speed, planets=system.objects)

        if self.weapon:
            self.weapon.update()

    def render_on_view(self, surface, hero):
        self.rect.x, self.rect.y = self.blitRotate((self.x - hero.x + surface.get_width() // 2,
                                                    self.y - hero.y + surface.get_height() // 2),
                                                   (20, 20), self.angle, self.or_image)

    def render_on_map(self, surface):
        self.rect.x, self.rect.y = self.blitRotate((surface.get_width() // 2 + self.x / MAP_SIZE,
                                                    surface.get_height() // 2 + self.y / MAP_SIZE),
                                                   (10, 10), self.angle + 45, self.or_map_image)

    def hero_distanse(self, hero):
        return int((hero.x - self.x) ** 2 + (hero.y - self.y) ** 2) ** 0.5

    def hero_angle(self, hero):
        hero_pos_angle = -math.degrees(math.atan2((hero.y - self.y), (hero.x - self.x)))
        return hero_pos_angle

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
        origin = (
            pos[0] - originPos[0] + min_box[0] - pivot_move[0], pos[1] - originPos[1] - max_box[1] + pivot_move[1])

        # get a rotated image
        self.image = pygame.transform.rotate(image, angle)

        return origin

