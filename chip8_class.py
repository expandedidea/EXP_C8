import pygame
import pygame.sndarray
import random

offset = 0x200


class chip8:

    def init(self):
        pygame.init()
        pygame.mixer.music.load("processed.wav")
        pygame.mixer.music.play(-1)
        pygame.mixer.music.pause()

        self.opcode = 0
        self.memory = [0] * 4096
        self.V = [0] * 16

        self.spriteColor = (255, 255, 255)  # White
        self.backgroundColor = (0, 153, 153)  # Black

        self.screen = pygame.display.set_mode((64 * 10, 32 * 10))
        self.I = 0
        self.pc = offset

        self.key_down = False
        self.key = 0

        self.gfx = [0] * (32 * 64)

        self.draw_flag = True

        self.delay_timer = 0
        self.sound_timer = 0
        self.timer_counter = 0

        self.stack = [0] * 16
        self.sp = -1

        self.key = [0] * 16

        fonts = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80  # F
        ]
        for i in range(len(fonts)):
            self.memory[i] = fonts[i]

    def updateTimers(self, clockRate):  # Relates the timing of the 60 Hz timers to the clock cycle
        self.timer_counter += 1
        if self.timer_counter == (clockRate // 60):
            if self.delay_timer > 0:
                self.delay_timer -= 1

            if self.sound_timer > 0:
                pygame.mixer.music.unpause()
                self.sound_timer -= 1
            else:
                pygame.mixer.music.pause()
            self.timer_counter = 0

    def loadGame(self, name):
        program = open(name + ".ch8", 'rb').read()
        i = offset
        for char in program:
            self.memory[i] = char
            i += 0x001

    def drawScreen(self):
        self.screen.fill(self.backgroundColor)
        for i in range(len(self.gfx)):
            if self.gfx[i] == 1:
                pygame.draw.rect(self.screen, self.spriteColor, ((i % 64) * 10, (i // 64) * 10, 10, 10))
            else:
                pygame.draw.rect(self.screen, self.backgroundColor, ((i % 64) * 10, (i // 64) * 10, 10, 10))
        pygame.display.update()

    def emulateCycle(self):

        self.draw_flag = False
        # print("PC: " + str(hex(self.pc)))
        self.opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
        # print(str(hex(self.opcode)))
        self.pc += 2
        instruct = self.opcode >> 12
        X = (self.opcode & 0x0F00) >> 8
        Y = (self.opcode & 0x00F0) >> 4
        N = (self.opcode & 0x000F)
        NN = (Y << 4) | N
        NNN = (X << 8) | (Y << 4) | N
        if instruct == 0x0:
            if NNN == 0x0E0:  # 0x00E0 Clear the screen
                self.gfx = [0] * (64 * 32)
                self.draw_flag = True
            elif NNN == 0x0EE:  # 0x00EE Return from subroutine
                self.pc = self.stack[self.sp]
                self.sp -= 1

        elif instruct == 0x1:  # 0x1NNN Jump
            self.pc = NNN

        elif instruct == 0x2:  # 0x2NNN Call addr
            self.sp += 1
            self.stack[self.sp] = self.pc
            self.pc = NNN

        elif instruct == 0x3:  # 0x3xNN If Vx == NN, increment pc
            if self.V[X] == NN:
                self.pc += 2

        elif instruct == 0x4:
            if self.V[X] != NN:
                self.pc += 2

        elif instruct == 0x5:
            if self.V[X] == self.V[Y]:
                self.pc += 2

        elif instruct == 0x6:  # 0x6XNN Set register VX
            self.V[X] = NN
            self.V[X] &= 0xFF

        elif instruct == 0x7:  # 0x7XNN Add value to register VX
            self.V[X] += NN
            self.V[X] &= 0xFF

        elif instruct == 0x8:
            if N == 0:
                self.V[X] = self.V[Y]
                self.V[X] &= 0xFF
            elif N == 1:
                self.V[X] |= self.V[Y]
                self.V[X] &= 0xFF
            elif N == 2:
                self.V[X] &= self.V[Y]
                self.V[X] &= 0xFF
            elif N == 3:
                self.V[X] ^= self.V[Y]
                self.V[X] &= 0xFF
            elif N == 4:  # Carry appears to work
                self.V[X] += self.V[Y]
                if((self.V[X] + self.V[Y]) > 255):
                    self.V[X] &= 0xFF
                    self.V[0xF] = 1
                else:
                    self.V[0xF] = 0
            elif N == 5:  # Flag implemented
                if(self.V[X] > self.V[Y]):
                    self.V[0xF] = 1
                else:
                    self.V[0xF] = 0
                self.V[X] -= self.V[Y]
                self.V[X] &= 0xFF
            elif N == 6:  # Has a different implementation depending on version
                lsb = self.V[X] & 1
                if lsb == 1:
                    self.V[0xF] = 1
                else:
                    self.V[0xF] = 0
                self.V[X] //= 2
                self.V[X] &= 0xFF
            elif N == 7:
                var = self.V[Y] - self.V[X]  # This is broken somehow
                if(self.V[X] < self.V[Y]):
                    self.V[0xF] = 1
                    self.V[X] = var
                else:
                    self.V[0xF] = 0
                    self.V[X] = abs(var)
            elif N == 0xE:
                msb = self.V[X] & 0x80
                if msb == 0x80:
                    self.V[0xF] = 1
                else:
                    self.V[0xF] = 0
                self.V[X] *= 2
                self.V[X] &= 0xFF
            else:
                print ("Unknown opcode " + str(hex(self.opcode)))

        elif instruct == 0x9:
            if self.V[X] != self.V[Y]:
                self.pc += 2

        elif instruct == 0xA:  # 0xANNN Set index register I
            self.I = NNN
        elif instruct == 0xB:
            self.pc = self.V[0] + NNN
        elif instruct == 0xC:  # Random generator, appears to be working properly
            ranGen = random.randint(0x00, 0xFF)
            self.V[X] = ranGen & NN
        elif instruct == 0xE:
            if NN == 0x9E:  # Key down events
                if ((self.V[X] == self.key)):
                    self.pc += 2
            elif NN == 0xA1:  # Key down events
                if ((self.V[X] != self.key)):
                    self.pc += 2
            else:
                print ("Unknown opcode " + str(hex(self.opcode)))
        elif instruct == 0xF:
            if NN == 0x07:  # 0xFx07 Delay timer placed into Vx
                self.V[X] = self.delay_timer
            elif NN == 0x15:  # 0xFx15 Vx placed into delay timer
                self.delay_timer = self.V[X]
            elif NN == 0x18:  # 0xFx18 Vx placed into sound timer
                self.sound_timer = self.V[X]
            elif NN == 0x1E:  # 0xFx1E I and Vx added and placed in I
                self.I += self.V[X]
                self.I &= 0xFFF
            elif NN == 0x29:
                self.I = self.V[X] * 5
            elif NN == 0x33:
                self.memory[self.I + 2] = self.V[X] % 10
                self.memory[self.I + 1] = int((self.V[X] % 100 - self.V[X] % 10) / 10)
                self.memory[self.I] = int((self.V[X] - (self.V[X] % 100)) / 100)

            elif NN == 0x55:  # This should work properly
                for store in range(X + 1):
                    self.memory[self.I + store] = self.V[store]
            elif NN == 0x65:  # This should work properly
                for store in range(X + 1):
                    self.V[store] = self.memory[self.I + store]
            elif NN == 0x0A:
                if self.key_down == True:
                    self.V[X] = self.key
                else:
                    self.pc -= 2
            else:
                print ("Unknown opcode " + str(hex(self.opcode)))

        elif instruct == 0xD:  # 0xDxyn Displaying a sprite at Vx/Vy position. Slanted for some reason, probably due to pygame
            self.screen.fill(self.backgroundColor)
            self.V[0xF] = 0
            for height in range(N):
                pixel = self.memory[height + self.I]
                for x_line in range(8):
                    if (pixel & (0x80 >> x_line)) != 0:
                        loc = ((self.V[X] + x_line) % 64 + ((self.V[Y] + height) % 32) * 64)
                        # print (loc)
                        if self.gfx[loc] is 1:
                            self.V[0xF] = 1
                        self.gfx[loc] ^= 1
            self.draw_flag = True

        else:
            print ("Unknown opcode " + str(hex(self.opcode)))
