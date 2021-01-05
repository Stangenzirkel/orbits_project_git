import os
import pygame
from planetary_system import PhysicalObject, Spaceship, Planet, Moon, PlanetarySystem
from interplanetary_map import InterplanetaryMap, PhysicalObjectOnMap, HeroOnMap, StarOnMap, PlanetOnMap

FPS = 60
files = ['omicron.txt', 'phi.txt', 'theta.txt', 'tau.txt']

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


def load_system(name):
    fullname = os.path.join('systems', name)
    print(fullname)
    file = open(fullname, 'r').read().split('\n')
    id = int(file[0])
    system_name = file[1]
    map_start_height, map_speed, map_apsis_argument, map_radius, map_mass = tuple(file[2].split(', '))
    PlanetOnMap(interplanetary_map,
                system_name,
                int(id),
                float(map_start_height),
                float(map_speed),
                star,
                float(map_apsis_argument),
                radius=int(map_radius),
                mass=int(map_mass))

    system = PlanetarySystem(id, window_size)
    for line in file[4:len(file)]:
        system.load_object(line)

    # hero_x, hero_y, hero_angle, hero_speed_x, hero_speed_y = tuple(file[3].split(', '))
    system.hero = Spaceship(system.all_view_sprites, '--Name--', 6570, 0, angle=0, speed_x=0, speed_y=310)
    systems[id] = system


infoObject = pygame.display.Info()
window_size = (infoObject.current_w, infoObject.current_h)
screen = pygame.display.set_mode(window_size, pygame.FULLSCREEN)
screen.fill('black')

systems = dict()
interplanetary_map = InterplanetaryMap(window_size)
star = StarOnMap(interplanetary_map, 'HR 8799')

for name in files:
    load_system(name)

hero = HeroOnMap(interplanetary_map, interplanetary_map.objects[-1])
interplanetary_map_mode = False

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
            if interplanetary_map_mode:
                screen.fill('black')
                interplanetary_map.update()
                screen.blit(interplanetary_map.surface(), (0, 0))

            else:
                screen.fill('black')
                systems[interplanetary_map.hero.planet.id].update()
                screen.blit(systems[interplanetary_map.hero.planet.id].surface, (0, 0))

        # control
        elif event.type == pygame.KEYDOWN and\
                event.key == pygame.K_RIGHTBRACKET and\
                systems[interplanetary_map.hero.planet.id].game_speed < 5 ** 5 and\
                not interplanetary_map_mode:
            systems[interplanetary_map.hero.planet.id].game_speed *= 5

        elif event.type == pygame.KEYDOWN and\
                event.key == pygame.K_LEFTBRACKET and\
                systems[interplanetary_map.hero.planet.id].game_speed > 1 and\
                not interplanetary_map_mode:
            systems[interplanetary_map.hero.planet.id].game_speed //= 5

        elif event.type == pygame.KEYDOWN and\
                event.key == pygame.K_n and\
                not interplanetary_map.hero.in_travel\
                and not systems[interplanetary_map.hero.planet.id].map_mode:
            interplanetary_map_mode = not interplanetary_map_mode

        elif event.type == pygame.KEYDOWN and\
                event.key == pygame.K_m and\
                not interplanetary_map_mode:
            systems[interplanetary_map.hero.planet.id].map_mode = not systems[interplanetary_map.hero.planet.id].map_mode

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT and interplanetary_map_mode:
            interplanetary_map.click_object(event.pos)

    pygame.display.flip()
pygame.quit()