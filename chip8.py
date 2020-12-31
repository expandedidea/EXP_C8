import chip8_class as ch8Class
import time
import pygame
import sys

Chip8 = ch8Class.chip8()
clock_speed = 540

keypad = {
    "1": 0x1, "2": 0x2, "3": 0x3, "4": 0xC,
    "q": 0x4, "w": 0x5, "e": 0x6, "r": 0xD,
    "a": 0x7, "s": 0x8, "d": 0x9, "f": 0xE,
    "z": 0xA, "x": 0x0, "c": 0xB, "v": 0xF}

Chip8.init()
args = sys.argv
Chip8.loadGame(args[1])

while True:
    t1 = time.time()
    pressed = pygame.key.get_pressed
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            try:
                Chip8.key = keypad[pygame.key.name(event.key)]
                Chip8.key_down = True
            except:
                continue
        if event.type == pygame.KEYUP:
            Chip8.key = 0
            Chip8.key_down = False

    Chip8.emulateCycle()
    Chip8.updateTimers(clock_speed)

    while((time.time() - t1) < (1 / clock_speed)):
        continue

    if Chip8.draw_flag == True:
        Chip8.drawScreen()
