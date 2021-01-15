import math
import os
import pygame
import copy
from planetary_system import PhysicalObject, FPS


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


class Bullet(pygame.sprite.Sprite):
    def __init__(self, group, x, y, angle, speed, speed_x=0, speed_y=0, collision_radius=1, life_span=1200):
        a_x = speed * math.cos(math.radians(angle))
        a_y = speed * math.sin(math.radians(angle))
        speed_x += a_x
        speed_y += a_y

        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y

        self.or_image = load_image("bullet.png", -1)
        self.or_image = pygame.transform.scale(self.or_image, (20, 20))

        self.collision_radius = collision_radius
        self.life_span = life_span
        self.timer = 0
        self.angle = angle
        self.image = self.or_image
        self.rect = self.image.get_rect()

        self.damage = 1

        pygame.sprite.Sprite.__init__(self, group)

    def destroy(self):
        self.kill()
        del self

    def blitRotate(self, pos, originPos, angle, image):
        angle = - angle - 90
        # calcaulate the axis aligned bounding box of the rotated image
        w, h = image.get_size()
        box = [pygame.math.Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]]
        box_rotate = [p.rotate(angle) for p in box]
        min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
        max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])

        pivot = pygame.math.Vector2(originPos[0], -originPos[1])
        pivot_rotate = pivot.rotate(angle)
        pivot_move = pivot_rotate - pivot

        # calculate the upper left origin of the rotated image
        origin = (
            pos[0] - originPos[0] + min_box[0] - pivot_move[0], pos[1] - originPos[1] - max_box[1] + pivot_move[1])

        self.image = pygame.transform.rotate(image, angle)
        return origin

    def update(self, system):
        self.timer += 1
        if self.timer > self.life_span:
            self.destroy()

        else:
            self.x += self.speed_x / FPS * system.game_speed
            self.y += self.speed_y / FPS * system.game_speed

            self.render(system.surface, system.hero, system.map_mode)

    def render(self, surface, hero, map_mode):
        if not map_mode:
            x, y = self.x - hero.x + surface.get_width() // 2, \
                   self.y - hero.y + surface.get_height() // 2
            self.rect.x, self.rect.y = self.blitRotate((x, y), (10, 10),
                                                       self.angle - 90, self.or_image)

        else:
            self.rect.x, self.rect.y = -100, -1003


# high-damage bullet with physic
class Shell(PhysicalObject, Bullet):
    def __init__(self, group, x, y, angle, speed, speed_x=0, speed_y=0, collision_radius=1, life_span=1200):
        a_x = speed * math.cos(math.radians(angle))
        a_y = speed * math.sin(math.radians(angle))
        speed_x += a_x
        speed_y += a_y

        self.or_image = load_image("bullet.png", -1)
        self.or_image = pygame.transform.scale(self.or_image, (20, 20))

        self.collision_radius = collision_radius
        self.life_span = life_span
        self.timer = 0
        self.angle = angle
        self.image = self.or_image
        self.rect = self.image.get_rect()

        PhysicalObject.__init__(self, x, y, speed_x=speed_x, speed_y=speed_y)
        Bullet.__init__(self, group, x, y, angle, speed, speed_x, speed_y, collision_radius, life_span)

        self.damage = 20

    def update(self, system):
        self.timer += 1
        if self.timer > self.life_span:
            self.destroy()

        else:
            self.physical_move(system.game_speed, planets=system.objects)

        self.render(system.surface, system.hero, system.map_mode)


class Weapon:
    def __init__(self,
                 image,
                 bullet_image,
                 collision_radius=1,
                 life_span=1200,
                 special=False,
                 magazine_size=1,
                 reload_time=100,
                 cooldown=4,
                 bullet=Bullet,
                 bullet_speed=60):
        self.collision_radius = collision_radius
        self.life_span = life_span
        self.special = special
        self.bullet = bullet
        self.bullet_speed = bullet_speed

        self.owner = None
        self.group = None

        self.magazine_size = magazine_size
        self.magazine_filling = magazine_size
        self.reload_time = reload_time
        self.reload_timer = 0
        self.cooldown = cooldown
        self.cooldown_timer = cooldown

        if image:
            self.image = load_image(image, -1)
            self.image = pygame.transform.scale(self.image, (120, 180))

        self.bullet_image = load_image(bullet_image, -1)
        self.bullet_image = pygame.transform.scale(self.bullet_image, (20, 180 // magazine_size))
        self.bullet_image_hollow = copy.copy(self.bullet_image).convert_alpha()
        self.bullet_image_hollow.set_alpha(100)

    def set_owner(self, owner):
        self.owner = owner

    def set_group(self, group):
        self.group = group

    def fire(self):
        if self.owner is not None and \
                self.group is not None and \
                self.magazine_filling > 0 and \
                self.cooldown_timer == self.cooldown:
            self.bullet(
                self.group,
                self.owner.x,
                self.owner.y,
                self.owner.angle,
                self.bullet_speed,
                speed_x=self.owner.speed_x,
                speed_y=self.owner.speed_y,
                life_span=self.life_span
            )

            self.magazine_filling -= 1
            self.cooldown_timer = 0

        elif self.owner is None:
            print(self, '*Weapon* no owner')

        elif self.group is None:
            print(self, '*Weapon* no sprite group')

    def update(self):
        if self.cooldown_timer < self.cooldown:
            self.cooldown_timer += 1

        if self.magazine_filling < self.magazine_size and self.cooldown_timer == self.cooldown:
            self.reload_timer = (self.reload_timer + 1) % self.reload_time
            if not self.reload_timer:
                self.magazine_filling += 1



