import math
import pygame

class Ember:
    # Small particle effect for sparks
    def __init__(self, pos, angle, speed):
        self.pos = list(pos)
        self.ang = angle
        self.spd = speed
        
    def update(self):
        self.pos[0] += math.cos(self.ang) * self.spd
        self.pos[1] += math.sin(self.ang) * self.spd
        self.spd = max(0, self.spd - 0.1)  # Slow down each frame
        return not self.spd
    
    def render(self, surf, offset=(0, 0)):
        # Polygon shape representing the ember
        pts = [
            (self.pos[0] + math.cos(self.ang)*self.spd*3 - offset[0], self.pos[1] + math.sin(self.ang)*self.spd*3 - offset[1]),
            (self.pos[0] + math.cos(self.ang + math.pi*0.5)*self.spd*0.5 - offset[0], self.pos[1] + math.sin(self.ang + math.pi*0.5)*self.spd*0.5 - offset[1]),
            (self.pos[0] + math.cos(self.ang + math.pi)*self.spd*3 - offset[0], self.pos[1] + math.sin(self.ang + math.pi)*self.spd*3 - offset[1]),
            (self.pos[0] + math.cos(self.ang - math.pi*0.5)*self.spd*0.5 - offset[0], self.pos[1] + math.sin(self.ang - math.pi*0.5)*self.spd*0.5 - offset[1]),
        ]
        pygame.draw.polygon(surf, (255, 255, 255), pts)