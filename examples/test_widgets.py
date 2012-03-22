import pygame
from pygame.locals import *

pygame.init()

from pygu import pyramid, pygw
from pygu.common import vcenter_blit

from pgpu.compatibility import Print
from pgpu.math_utils import Vector


MAIN = 0
F_QUIT = 10

C_BLACK = (10, 10, 10)
C_DARK_GRAY = (50, 50, 50)
C_GRAY = (150, 150, 150)
C_OFF_WHITE = (230, 230, 230)
C_WHITE = (250, 250, 250)


def quitter(eman, gstate, event):
    raise eman.Message(F_QUIT)


def main():
    pygame.key.set_repeat(330, 28)
    screen = pygame.display.set_mode((280, 85))
    
    gstate = pyramid.StateManager([MAIN])
    gstate[MAIN].bind(quitter, QUIT)
    
    main = pygw.Container(gstate[MAIN], (0, 0))
    scroll = pygw.Scrollable(main, (15, 50), (250, 30))
    updates = pygame.sprite.Group()
    
    font = pygame.font.Font(None, 25)
    
    ebg = pygame.Surface((250, 30))
    ebg.fill(C_BLACK)
    
    t = 'This is a long piece of scrolling text, you may not see all of it.'
    
    s = font.render(t, True, C_OFF_WHITE)
    l1f = pygame.Surface((500, 30), SRCALPHA)
    vcenter_blit(l1f, s, dest = (5, 0))
    
    cursor = pygame.Surface((1, 20))
    cursor.fill(C_WHITE)
    
    entry = pygw.Entry(main, (15, 10), screen.get_rect(), ebg, 
            cursor, font=font, color=C_WHITE, margin=4, blink_frames=30, 
            callback=lambda w: Print(w.get()))
    
    bglab = pygw.Label(main, (15, 50), ebg)
    
    label = pygw.Label(scroll, (0, 0), l1f)
    
    clock = pygame.time.Clock()
    
    scount = -50
    inc = 1
    
    while 1:
        clock.tick(60)
        
        scount += inc
        if not -50 <= scount <= 550:
            inc = -inc
        
        flag = gstate[gstate.state].loop(pygame.event.get())
        if flag == F_QUIT:
            return entry.get()
        
        screen.fill(C_GRAY)
        
        main.update()
        scroll.scroll_x(scount, False)
        
        main.draw(screen)
        pygame.display.update()


if __name__ == '__main__':
    Print(main())
