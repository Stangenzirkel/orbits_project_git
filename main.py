import os
import pygame
import copy
from planetary_system import PhysicalObject, Spaceship, Planet, Moon, PlanetarySystem
from interplanetary_map import InterplanetaryMap, PhysicalObjectOnMap, HeroOnMap, StarOnMap, PlanetOnMap
from weapon import Bullet, Shell, Weapon
import sqlite3

FPS = 60
files = {1: 'omicron.txt', 2: 'phi.txt', 3: 'theta.txt', 4: 'tau.txt'}

pygame.init()
pygame.mouse.set_visible(False)


def load_system(id, new=True):
    name = files[id]
    fullname = os.path.join('systems', name)
    file = open(fullname, 'r').read().split('\n')
    system_name = file[0]
    map_start_height, map_speed, map_apsis_argument, map_radius, map_mass = tuple(file[1].split(', '))
    if new:
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
    for line in file[3:len(file)]:
        system.load_object(line)

    hero_x, hero_y, hero_angle, hero_speed_x, hero_speed_y = tuple(file[2].split(', '))
    system.hero = Spaceship(system.all_view_sprites,
                            int(hero_x),
                            int(hero_y),
                            int(hero_angle),
                            float(hero_speed_x),
                            float(hero_speed_y))

    first_weapon = copy.copy(minigun_weapon)
    first_weapon.set_group(system.bullets)
    system.hero.add_weapon(first_weapon, 1)

    second_weapon = copy.copy(cannon_weapon)
    second_weapon.set_group(system.bullets)
    system.hero.add_weapon(second_weapon, 2)
    systems[id] = system


infoObject = pygame.display.Info()
window_size = (infoObject.current_w, infoObject.current_h)
screen = pygame.display.set_mode(window_size)
font = pygame.font.Font(None, 80)
text = font.render("Now loading", False , (100, 255, 100))
text_x = infoObject.current_w // 2 - text.get_width() // 2
text_y = infoObject.current_h // 2 - text.get_height() // 2
text_w = text.get_width()
text_h = text.get_height()
screen.blit(text, (text_x, text_y))
pygame.display.update()

systems = dict()
interplanetary_map = InterplanetaryMap(window_size)
star = StarOnMap(interplanetary_map, 'HR 8799')

cannon_weapon = Weapon('cannon_sprite_2.png', 'shell.png', bullet=Shell, bullet_speed=100, life_span=600)
minigun_weapon = Weapon('minigun_sprite.png', 'shell.png', life_span=500, magazine_size=60, reload_time=24, bullet_speed=450)

for key in files.keys():
    load_system(key)

hero = HeroOnMap(interplanetary_map, interplanetary_map.objects[-1])
interplanetary_map_mode = True
current_system = systems[interplanetary_map.hero.planet.id]

running = True
clock = pygame.time.Clock()

REDRAW_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(REDRAW_EVENT, 1000 // FPS)

screen.fill('black')

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == REDRAW_EVENT:
            screen.fill('black')
            if interplanetary_map_mode:
                interplanetary_map.update()
                screen.blit(interplanetary_map.surface(), (0, 0))

            else:
                current_system.update()
                screen.blit(current_system.surface, (0, 0))

        elif event.type == pygame.KEYDOWN and (current_system.hero.destroyed or current_system.win):
            interplanetary_map_mode = True
            load_system(current_system.id, new=False)
            current_system = systems[current_system.id]

        elif event.type == pygame.KEYDOWN and not current_system.hero.destroyed and not current_system.win:
            if not interplanetary_map_mode:
                # time speed changing
                if event.key == pygame.K_RIGHTBRACKET and \
                        current_system.game_speed < 5 ** 2:
                    current_system.game_speed *= 5

                if event.key == pygame.K_LEFTBRACKET and \
                        current_system.game_speed > 1:
                    current_system.game_speed //= 5

                if event.key == pygame.K_m:
                    current_system.map_mode = not systems[
                        interplanetary_map.hero.planet.id].map_mode

            if event.key == pygame.K_n and \
                    not interplanetary_map.hero.in_travel:
                interplanetary_map_mode = not interplanetary_map_mode

            if event.key == pygame.K_s and \
                    not interplanetary_map_mode and \
                    current_system.map_mode:
                current_system.simulation()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT and interplanetary_map_mode:
            cmd = interplanetary_map.click_object(event.pos)
            if cmd == 3:
                running = False

            elif cmd == 1 and not interplanetary_map.hero.in_travel:
                load_system(current_system.id, new=False)
                current_system = systems[current_system.id]

            current_system = systems[interplanetary_map.hero.planet.id]
    pygame.display.flip()
pygame.quit()
