import math
import os
import pygame
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

    def update(self, surface, objects, hero, game_speed, map_mode):
        self.timer += 1
        if self.timer > self.life_span:
            self.destroy()

        else:
            self.x += self.speed_x / FPS * game_speed
            self.y += self.speed_y / FPS* game_speed

            if not map_mode:
                self.render(surface, hero)

    def render(self, surface, hero):
        x, y = self.x - hero.x + surface.get_width() // 2, \
               self.y - hero.y + surface.get_height() // 2
        self.rect.x, self.rect.y = self.blitRotate((x, y), (10, 10),
                                                   self.angle - 90, self.or_image)


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

    def update(self, surface, objects, hero, game_speed, map_mode):
        self.timer += 1
        if self.timer > self.life_span:
            self.destroy()

        else:
            self.physical_move(game_speed, planets=objects)

            if not map_mode:
                self.render(surface, hero)


class Weapon:
    def __init__(self, collision_radius=1, life_span=1200, special=False, reload=100, bullet=Bullet, bullet_speed=60):
        self.collision_radius = collision_radius
        self.life_span = life_span
        self.special = special
        self.bullet = bullet
        self.bullet_speed = bullet_speed
        self.owner = None
        self.group = None
        self.can_fire = True
        self.reload_speed = reload
        self.reload_timer = 0

    def set_owner(self, owner):
        self.owner = owner

    def set_group(self, group):
        self.group = group

    def fire(self):
        if self.owner is not None and self.group is not None:
            self.bullet(
                self.group,
                self.owner.x,
                self.owner.y,
                self.owner.angle,
                self.bullet_speed,
                speed_x=self.owner.speed_x,
                speed_y=self.owner.speed_y
            )
            self.can_fire = False
            self.reload_timer = 0
        elif self.owner is None:
            print('*Weapon* no owner')
        else:
            print('*Weapon* no sprite group')

    def update(self):
        if self.reload_timer >= self.reload_speed:
            self.can_fire = True

        if not self.can_fire:
            self.reload_timer += 1



