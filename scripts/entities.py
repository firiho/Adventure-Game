import math
import random
import pygame

from scripts.particle import VFXParticle
from scripts.spark import Ember

class MovableEntity:
    # Entity with physics-based movement
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.kind = e_type
        self.pos = list(pos)
        self.dim = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')
        
        self.last_movement = [0, 0]
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.dim[0], self.dim[1])
    
    def set_action(self, act):
        if act != self.action:
            self.action = act
            self.animation = self.game.assets[self.kind + '/' + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        frame_move = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        # Horizontal movement check
        self.pos[0] += frame_move[0]
        ent_rect = self.rect()
        for r in tilemap.physics_rects_around(self.pos):
            if ent_rect.colliderect(r):
                if frame_move[0] > 0:
                    ent_rect.right = r.left
                    self.collisions['right'] = True
                if frame_move[0] < 0:
                    ent_rect.left = r.right
                    self.collisions['left'] = True
                self.pos[0] = ent_rect.x
        
        # Vertical movement check
        self.pos[1] += frame_move[1]
        ent_rect = self.rect()
        for r in tilemap.physics_rects_around(self.pos):
            if ent_rect.colliderect(r):
                if frame_move[1] > 0:
                    ent_rect.bottom = r.top
                    self.collisions['down'] = True
                if frame_move[1] < 0:
                    ent_rect.top = r.bottom
                    self.collisions['up'] = True
                self.pos[1] = ent_rect.y
                
        if movement[0] > 0:
            self.flip = False
        elif movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement
        
        # Gravity
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        self.animation.update()
        
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), 
                  (self.pos[0]-offset[0]+self.anim_offset[0], self.pos[1]-offset[1]+self.anim_offset[1]))

class Foe(MovableEntity):
    # Enemy entity with AI
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        self.walking = 0
        
    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            # Simple AI for wandering/shooting
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    movement = ((movement[0] - 0.5) if self.flip else (movement[0] + 0.5), movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if abs(dis[1]) < 16:
                    # Attack logic
                    if self.flip and dis[0] < 0:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Ember(self.game.projectiles[-1][0], random.random()-0.5+math.pi, 2+random.random()))
                    elif (not self.flip) and dis[0] > 0:
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Ember(self.game.projectiles[-1][0], random.random()-0.5, 2+random.random()))
                            
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        
        super().update(tilemap, movement=movement)
        
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
            
        # Check if player is dashing through enemy
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                for i in range(30):
                    angle = random.random()*math.pi*2
                    speed = random.random()*5
                    self.game.sparks.append(Ember(self.rect().center, angle, 2+random.random()))
                    self.game.particles.append(VFXParticle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle+math.pi)*speed*0.5, math.sin(angle+math.pi)*speed*0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Ember(self.rect().center, 0, 5+random.random()))
                self.game.sparks.append(Ember(self.rect().center, math.pi, 5+random.random()))
                return True
            
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        
        # Render gun
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))

class Hero(MovableEntity):
    # Player-controlled entity
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0
    
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
        
        self.air_time += 1
        
        # Die if in air too long
        if self.air_time > 120:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
        
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1
            
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            self.flip = True if self.collisions['left'] else False
            self.set_action('wall_slide')
        
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        
        # Dashing effects
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                ang = random.random()*math.pi*2
                spd = random.random()*0.5+0.5
                pv = [math.cos(ang)*spd, math.sin(ang)*spd]
                self.game.particles.append(VFXParticle(self.game, 'particle', self.rect().center, velocity=pv, frame=random.randint(0, 7)))
                
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        elif self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing)/self.dashing*8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pv = [abs(self.dashing)/self.dashing*random.random()*3, 0]
            self.game.particles.append(VFXParticle(self.game, 'particle', self.rect().center, velocity=pv, frame=random.randint(0, 7)))
                
        # Horizontal drag
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0]-0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0]+0.1, 0)
    
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
            
    def jump(self):
        # Jump logic, including wall jump
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True
    
    def dash(self):
        # Dash action
        if not self.dashing:
            self.game.sfx['dash'].play()
            self.dashing = -60 if self.flip else 60