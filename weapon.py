import math
import os
import pygame
from planetary_system import PhysicalObject


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


class Bullet(pygame.sprite.Sprite, PhysicalObject):
    def __init__(self, owner, group, x, y, angle, speed_x=0, speed_y=0, collision_radius=1, life_span=1200):
        speed = 60
        a_x = speed * math.cos(math.radians(angle))
        a_y = speed * math.sin(math.radians(angle))
        speed_x += a_x
        speed_y += a_y
        pygame.sprite.Sprite.__init__(self, group)
        PhysicalObject.__init__(self, x, y, speed_x=speed_x, speed_y=speed_y)
        print(self.speed_x, self.speed_y, owner.speed_x, owner.speed_y)

        self.or_image = load_image("bullet.png", -1)
        self.or_image = pygame.transform.scale(self.or_image, (20, 20))


        self.collision_radius = collision_radius
        self.life_span = life_span
        self.timer = 0
        self.angle = angle
        self.owner = owner
        self.image = self.or_image
        self.on_map_pos = [owner.rect.x, owner.rect.y]
        self.rect = self.image.get_rect()
        self.rect.x = 940
        self.rect.y = 520

    def destroy(self):
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
            self.physical_move(game_speed, planets=objects)

            print(self.angle)

            if not map_mode:
                self.render(surface)

    def render(self, surface):
        x, y = self.x - self.owner.x + surface.get_width() // 2, \
               self.y - self.owner.y + surface.get_height() // 2
        self.rect.x, self.rect.y = self.blitRotate((x, y), (10, 10),
                                                   self.angle + 90, self.or_image)
