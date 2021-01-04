import os
import pygame
from planetary_system import PhysicalObject, Spaceship, Planet, Moon, PlanetarySystem, GAME_SPEED
from interplanetary_map import InterplanetaryMap, PhysicalObjectOnMap, HeroOnMap, StarOnMap, PlanetOnMap

FPS = 60

pygame.init()
pygame.mouse.set_visible(False)


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


infoObject = pygame.display.Info()
window_size = (infoObject.current_w, infoObject.current_h)
screen = pygame.display.set_mode(window_size, pygame.FULLSCREEN)
screen.fill('black')

interplanetary_map = InterplanetaryMap(window_size)

star = StarOnMap(interplanetary_map, 'Star', 99)
planet_1 = PlanetOnMap(interplanetary_map, 'Omicron', 1, 500, 20, star, apsis_argument=45)
planet_2 = PlanetOnMap(interplanetary_map, 'Phi', 2, 500, 20, star, apsis_argument=0)
planet_3 = PlanetOnMap(interplanetary_map, 'Theta', 3, 100, 90, star, apsis_argument=0)
planet_4 = PlanetOnMap(interplanetary_map, 'Tau', 4, 700, 20, star, apsis_argument=180)

hero = HeroOnMap(interplanetary_map, star)

system_star = PlanetarySystem(99, window_size, 6000, 100000)
system_1 = PlanetarySystem(1, window_size, 6000, 100000, color='blue')
system_2 = PlanetarySystem(2, window_size, 6000, 100000, color='green')
system_3 = PlanetarySystem(3, window_size, 6000, 100000, color='red')
system_4 = PlanetarySystem(4, window_size, 6000, 100000, color='yellow')

systems = dict()
for system in [system_star, system_1, system_2, system_3, system_4]:
    systems[system.id] = system

map_mode = False

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
            if map_mode:
                screen.fill('black')
                interplanetary_map.update()
                screen.blit(interplanetary_map.surface(), (0, 0))

            else:
                screen.fill('black')
                systems[interplanetary_map.hero.planet.id].update()
                screen.blit(systems[interplanetary_map.hero.planet.id].surface, (0, 0))

        # control
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHTBRACKET and GAME_SPEED < 5 ** 5:
            GAME_SPEED *= 5

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFTBRACKET and GAME_SPEED > 1:
            GAME_SPEED //= 5

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_m and not interplanetary_map.hero.in_travel:
            map_mode = not map_mode

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT and map_mode:
            interplanetary_map.click_object(event.pos)

    pygame.display.flip()
pygame.quit()