import pygame
from planetary_system import PhysicalObject, Spaceship
import os

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


class Enemy(Spaceship):
    def __init__(self, *arg, **kwargs):
        print(arg)
        print(kwargs)
        Spaceship.__init__(self, *arg, **kwargs)
        self.or_image = load_image(arg[1], -1)
        self.or_image = pygame.transform.scale(self.or_image, (60, 60))
        self.image = self.or_image

