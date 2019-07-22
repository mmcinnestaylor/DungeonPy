# Created by Hayden & Marlan
# Beginnings of a grand quest
# behold...
# Binal Bantasy

import os.path

import pygame
from pygame.locals import *
from pytmx.util_pygame import load_pygame

import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup

# from pallete import *

# define configuration variables here
RESOURCES_DIR = 'Data'

HERO_MOVE_SPEED = 69  # pixels per second
MAP_FILENAME = 'BinalOverworld2.tmx'


# simple wrapper to keep the screen resizeable
def init_screen(width, height):
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    return screen


# make loading maps a little easier
def get_map(filename):
    return os.path.join(RESOURCES_DIR, filename)


# make loading images a little easier
def load_image(filename):
    return pygame.image.load(os.path.join(RESOURCES_DIR, filename))

# make playing music easier
def playMusic(song):
    # does not crash if file misnamed/does not quite exist
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(song)
        pygame.mixer.music.play(-1, 0.0) # '-1' as first parameter
                                         # therefore loops
    except pygame.error: 
        print("music error:", song)


# object for multirow/column pallete of characters
class Pallete(pygame.sprite.Sprite):
    # initializes images with pallete of character sprites
    def __init__(self, filename, rows=1,cols=1, row=0, col=0):
        self.rows = rows
        self.cols = cols
        pygame.sprite.Sprite.__init__(self)
        image = load_image(filename).convert_alpha() 
        (width, height) = image.get_size()
        (self.width, self.height) = (width, height)
        (charWidth, charHeight) = (width / cols, height / rows)
        self.image= image.subsurface(
                    (col * charWidth, row * charHeight, charWidth, charHeight))
        self.image = pygame.transform.scale(self.image, (32, 40))


class Hero(Pallete):
    """ Our Hero

    The Hero has three collision rects, one for the whole sprite "rect" and
    "old_rect", and another to check collisions with walls, called "feet".

    The position list is used because pygame rects are inaccurate for
    positioning sprites; because the values they get are 'rounded down'
    as integers, the sprite would move faster moving left or up.

    Feet is 1/2 as wide as the normal rect, and 8 pixels tall.  This size size
    allows the top of the sprite to overlap walls.  The feet rect is used for
    collisions, while the 'rect' rect is used for drawing.

    There is also an old_rect that is used to reposition the sprite if it
    collides with level walls.
    """

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = load_image('hero.png').convert_alpha()
        self.velocity = [0, 0]
        self._position = [0, 0]
        self._old_position = self.position
        self.rect = self.image.get_rect()
        self.feet = pygame.Rect(0, 0, self.rect.width * .5, 8)

        Pallete.__init__(self, 'heroes.png', 8, 12, 2, 4)
        (rows, cols) = (self.rows, self.cols)
        image = load_image('heroes.png').convert_alpha() 
        (width, height) = (self.width, self.height)
        (charWidth, charHeight) = (width / cols, height / rows)

        self.ups = list()
        self.rights = list()
        self.downs = list()
        self.lefts = list()

        # the image frames are in a grid, so below deals with the cells
        for col in range(0,2):
            self.ups.append(image.subsurface(
                        ((col+3) * charWidth, 6 * charHeight, 
                            charWidth, charHeight)))
            self.ups[col]= pygame.transform.scale(self.ups[col], (32, 40))
            self.rights.append(image.subsurface(
                        ((col+3) * charWidth, 5 * charHeight, 
                            charWidth, charHeight)))
            self.rights[col] = pygame.transform.scale(self.rights[col], 
                                                            (33, 41))
            self.downs.append(image.subsurface(
                        ((col+3) * charWidth, 4 * charHeight, 
                            charWidth, charHeight)))
            self.downs[col] = pygame.transform.scale(self.downs[col], (32, 40))
            self.lefts.append( image.subsurface(
                        ((col+3) * charWidth, 7 * charHeight, 
                            charWidth, charHeight)))
            self.lefts[col] = pygame.transform.scale(self.lefts[col], (33, 41))
        # begin game looking forward idle animation
        self.currImageList = self.ups

    @property
    def position(self):
        return list(self._position)

    @position.setter
    def position(self, value):
        self._position = list(value)

    def update(self, dt):
        self._old_position = self._position[:]
        self._position[0] += self.velocity[0] * dt
        self._position[1] += self.velocity[1] * dt
        self.rect.topleft = self._position
        self.feet.midbottom = self.rect.midbottom

    def move_back(self, dt):
        """ If called after an update, the sprite can move back
        """
        self._position = self._old_position
        self.rect.topleft = self._position
        self.feet.midbottom = self.rect.midbottom

    def walkAnimation(self, ticks):
        # adds animation for hero character
        n = 0
        if self.velocity[0] == 0 and self.velocity[1] == 0:
            ticks = ticks//500*500
            if ticks%500 == 0:
                n = 0
            if ticks%1000 == 0:
                n = 1
        else:
            ticks = ticks //350*350
            if ticks%350 == 0:
                n = 0
            if ticks%700 == 0:
                n = 1
        self.image = self.currImageList[n]




class QuestGame(object):
    """ This class is a basic game.

    This class will load data, create a pyscroll group, a hero object.
    It also reads input and moves the Hero around the map.
    Finally, it uses a pyscroll group to render the map and Hero.
    """
    filename = get_map(MAP_FILENAME)

    def __init__(self):

        # true while running
        self.running = False

        # load data from pytmx
        tmx_data = load_pygame(self.filename)

        # setup level geometry with simple pygame rects, loaded from pytmx
        self.walls = list()
        for object in tmx_data.objects:
            self.walls.append(pygame.Rect(
                object.x, object.y,
                object.width, object.height))

        # create new data source for pyscroll
        map_data = pyscroll.data.TiledMapData(tmx_data)

        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(map_data, screen.get_size(), clamp_camera=False, tall_sprites=1)
        self.map_layer.zoom = 2

        # pyscroll supports layered rendering.  our map has 3 'under' layers
        # layers begin with 0, so the layers are 0, 1, and 2.
        # since we want the sprite to be on top of layer 1, we set the default
        # layer for sprites as 2
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)

        self.hero = Hero()

        # put the hero in the center of the map
        # self.hero.position = self.map_layer.map_rect.center
        # self.hero._position[0] += 200
        # self.hero._position[1] += 400

        # add our hero to the group
        self.group.add(self.hero)

        # startpoints
        self.startpoints = []
        for object in tmx_data.objects:
            if object.name == "startpoint":
                self.startpoints.append((object.x, object.y))

        self.hero.position = (self.startpoints[0][0], self.startpoints[0][1])

    def draw(self, surface):

        # center the map/screen on our Hero
        self.group.center(self.hero.rect.center)

        # draw the map and all sprites
        self.group.draw(surface)

    def handle_input(self):
        """ Handle pygame input events
        """
        poll = pygame.event.poll
        clock = pygame.time.Clock()

        event = poll()
        while event:
            ticks = pygame.time.get_ticks()

            if event.type == QUIT:
                self.running = False
                break

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                    break

                elif event.key == K_EQUALS:
                    self.map_layer.zoom += .25

                elif event.key == K_MINUS:
                    value = self.map_layer.zoom - .25
                    if value > 0:
                        self.map_layer.zoom = value

            # this will be handled if the window is resized
            elif event.type == VIDEORESIZE:
                init_screen(event.w, event.h)
                self.map_layer.set_size((event.w, event.h))

            event = poll()

        # using get_pressed is slightly less accurate than testing for events
        # but is much easier to use.
        pressed = pygame.key.get_pressed()
        # if pressed[K_UP]:
        #     self.hero.velocity[1] = -HERO_MOVE_SPEED
        # elif pressed[K_DOWN]:
        #     self.hero.velocity[1] = HERO_MOVE_SPEED
        # else:
        #     self.hero.velocity[1] = 0

        # if pressed[K_LEFT]:
        #     self.hero.velocity[0] = -HERO_MOVE_SPEED
        # elif pressed[K_RIGHT]:
        #     self.hero.velocity[0] = HERO_MOVE_SPEED
        # else:
        #     self.hero.velocity[0] = 0

        # if self.moving != False:
        ticks = pygame.time.get_ticks()
        if pressed[K_UP]: 
            self.hero.currImageList = self.hero.downs
            self.hero.walkAnimation(ticks)
            self.hero.velocity[1] = -HERO_MOVE_SPEED
            #self.steps += 1
        elif pressed[K_DOWN]:
            self.hero.currImageList = self.hero.ups
            self.hero.walkAnimation(ticks)
            self.hero.velocity[1] = HERO_MOVE_SPEED
            #self.steps += 1
        else:
            self.hero.velocity[1] = 0
        if pressed[K_LEFT]:
            self.hero.currImageList = self.hero.lefts
            self.hero.walkAnimation(ticks)
            self.hero.velocity[0] = -HERO_MOVE_SPEED
            #self.steps += 1
        elif pressed[K_RIGHT]:
            self.hero.currImageList = self.hero.rights
            self.hero.walkAnimation(ticks)
            self.hero.velocity[0] = HERO_MOVE_SPEED
            #self.steps += 1
        
        else:
            self.hero.velocity[0] = 0
        # sprint
        if pressed[K_SPACE]:
            self.hero.velocity[0] *= 1.7
            self.hero.velocity[1] *= 1.7
            # more likely to battle encounter if sprinting
            # if self.hero.velocity[0] > 0 or self.hero.velocity[1] > 0:
            #     #self.steps += 2
            # if self.hero.velocity[0] >= 1.5 * HERO_MOVE_SPEED:
            #     pass
            # if self.hero.velocity[1] >= 1.5 * HERO_MOVE_SPEED:
            #     pass

        # stops character from moving when battlescreen is initiated
        #if self.mode == "Battle":
        #    (self.hero.velocity[0], self.hero.velocity[1]) = (0, 0)

    def update(self, dt):
        """ Tasks that occur over time should be handled here
        """
        self.group.update(dt)

        # check if the sprite's feet are colliding with wall
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        for sprite in self.group.sprites():
            if sprite.feet.collidelist(self.walls) > -1:
                sprite.move_back(dt)

    # plays music based on map file keyed to dictionary
    # also covers changing map sound effect
    # def changeMusicAndInstance(self, surface, oldMusic=None):
    #     tmap = self.filename
    #     song = MusicDict[tmap]
    #     # instance change sound, from Zelda stairs sound
    #     playSound("Enter.wav", .15)

    #     if oldMusic == None:
    #         oldMusic = MusicDict[self.oldMap]
       
    #     if self.mode != "Overworld":
    #         if song == oldMusic: return None
       
    #     # loops music indefinitely for that map
    #     playMusic(song)

    def run(self):
        """ Run the game loop
        """
        clock = pygame.time.Clock()
        self.running = True

        from collections import deque
        times = deque(maxlen=30)

        #idle hero animation
        ticks = pygame.time.get_ticks()
        self.hero.walkAnimation(ticks)
        playMusic('overworld.wav')

        try:
            while self.running:
                dt = clock.tick() / 1000.
                times.append(clock.get_fps())
                # print(sum(times)/len(times))#idle hero animation
                ticks = pygame.time.get_ticks()
                self.hero.walkAnimation(ticks)
                self.handle_input()
                self.update(dt)
                self.draw(screen)
                pygame.display.flip()

        except KeyboardInterrupt:
            self.running = False


if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    screen = init_screen(800, 600)
    pygame.display.set_caption('Binal Bantasy')

    try:
        game = QuestGame()
        game.run()
    except:
        pygame.quit()
        raise