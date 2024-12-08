import sys
import math
import random
import pygame
import json

from scripts.utils import fetch_image, fetch_images, FrameAnimation
from scripts.entities import Hero, Foe
from scripts.tilemap import WorldMap
from scripts.clouds import SkyClouds
from scripts.particle import VFXParticle
from scripts.spark import Ember

class JumperGame:
    def __init__(self):
        pygame.init()
        self.game_time = 0
        pygame.display.set_caption('Block Jumper Adventure')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()
        
        self.movement = [False, False]
        
        # Load game assets
        self.assets = {
            'decor': fetch_images('tiles/decor'),
            'grass': fetch_images('tiles/grass'),
            'large_decor': fetch_images('tiles/large_decor'),
            'stone': fetch_images('tiles/stone'),
            'player': fetch_image('entities/player.png'),
            'background': fetch_image('background.webp'),
            'clouds': fetch_images('clouds'),
            'enemy/idle': FrameAnimation(fetch_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': FrameAnimation(fetch_images('entities/enemy/run'), img_dur=4),
            'player/idle': FrameAnimation(fetch_images('entities/player/idle'), img_dur=6),
            'player/run': FrameAnimation(fetch_images('entities/player/run'), img_dur=4),
            'player/jump': FrameAnimation(fetch_images('entities/player/jump')),
            'player/slide': FrameAnimation(fetch_images('entities/player/slide')),
            'player/wall_slide': FrameAnimation(fetch_images('entities/player/wall_slide')),
            'particle/leaf': FrameAnimation(fetch_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': FrameAnimation(fetch_images('particles/particle'), img_dur=6, loop=False),
            'gun': fetch_image('gun.png'),
            'projectile': fetch_image('projectile.png'),
            'doors': [pygame.transform.scale(i, (16, 20)) for i in fetch_images('tiles/door')],
            'coin': fetch_images('tiles/coin'),
            'heart': pygame.transform.scale(pygame.image.load('data/images/tiles/heart/0.png').convert_alpha(), (16,16))
        }
        
        # Sound effects
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
            'coin': pygame.mixer.Sound('data/sfx/coin.wav')
        }
        
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)
        self.sfx['coin'].set_volume(0.2)
        
        self.clouds = SkyClouds(self.assets['clouds'], count=16)
        
        self.player = Hero(self, (50, 50), (8, 15))
        self.tilemap = WorldMap(self, tile_size=16)
        
        self.level = 0
        self.score = 0
        self.lives = 3
        self.high_score = self.load_high_score()
        self.load_level(self.level)
        
        self.font = pygame.font.SysFont('Arial', 12) 
        
        self.screenshake = 0
        self.dead = 0
        self.transition = -30
        
    def load_high_score(self):
        # Load high score from file
        try:
            with open('highscore.json', 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0
        
    def save_high_score(self):
        # Save high score
        with open('highscore.json', 'w') as f:
            json.dump({'high_score': self.high_score}, f)
        
    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4+tree['pos'][0],4+tree['pos'][1],23,13))
            
        self.enemies = []
        for sp in self.tilemap.extract([('spawners', 1)]):  # enemy spawners
            self.enemies.append(Foe(self, sp['pos'], (8,15)))
            
        self.doors = self.tilemap.extract([('doors',0),('doors',1)])
        for d in self.doors:
            if d['variant'] == 0:
                self.player.pos = list(d['pos'])
                self.player.air_time = 0
                break
        
        self.coins = self.tilemap.extract([('coin',0)], keep=False)
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30

    def reset_game(self):
        self.level = 0
        self.score = 0
        self.lives = 3
        self.load_level(self.level)

    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        self.sfx['ambience'].play(-1)
        
        while True:
            self.game_time += 1
            self.display.fill((0,0,0,0))
            self.display_2.blit(self.assets['background'], (0,0))
            
            self.screenshake = max(0, self.screenshake - 1)
            
            if self.transition < 0:
                self.transition += 1
            
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.reset_game()
                    else:
                        for d in self.doors:
                            if d['variant'] == 0:
                                self.player.pos = list(d['pos'])
                                self.player.velocity = [0,0]
                                self.player.air_time = 0
                                break
                    self.dead = 0
                    self.transition = -30
            
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width()/2 - self.scroll[0])/30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height()/2 - self.scroll[1])/30
            r_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            # Leaf spawn
            for rect in self.leaf_spawners:
                if random.random()*49999 < rect.width*rect.height:
                    ps = (rect.x+random.random()*rect.width, rect.y+random.random()*rect.height)
                    self.particles.append(VFXParticle(self, 'leaf', ps, velocity=[-0.1,0.3], frame=random.randint(0,20)))
            
            self.clouds.update()
            self.clouds.render(self.display_2, offset=r_scroll)
            
            self.tilemap.render(self.display, offset=r_scroll)
            
            # Doors
            for door in self.doors:
                img = self.assets['doors'][door['variant']]
                self.display.blit(img, (door['pos'][0]-r_scroll[0], door['pos'][1]-r_scroll[1]))
            
            # Coins
            for c in self.coins.copy():
                c_rect = pygame.Rect(c['pos'][0], c['pos'][1], self.tilemap.tile_size, self.tilemap.tile_size)
                vertical_offset = math.sin(self.game_time*0.05)*2
                c_y = c['pos'][1]+vertical_offset
                img = self.assets['coin'][0]
                self.display.blit(img, (c['pos'][0]-r_scroll[0], c_y - r_scroll[1]))
                c_rect.y = c_y
                if self.player.rect().colliderect(c_rect):
                    self.coins.remove(c)
                    self.score += 50
                    self.sfx['coin'].play()

            # Enemies
            for foe in self.enemies.copy():
                kill = foe.update(self.tilemap, (0,0))
                foe.render(self.display, offset=r_scroll)
                if kill:
                    self.enemies.remove(foe)
                    self.score += 100
                    self.screenshake = max(16, self.screenshake)
                    self.sfx['hit'].play()
            
            # Player
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1]-self.movement[0],0))
                self.player.render(self.display, offset=r_scroll)
            
            # Check level transition
            for d in self.doors:
                if d['variant'] == 1:
                    d_rect = pygame.Rect(d['pos'][0], d['pos'][1], self.tilemap.tile_size, self.tilemap.tile_size)
                    if self.player.rect().colliderect(d_rect):
                        self.level += 1
                        self.load_level(self.level)
                        break

            # Projectiles
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                p_img = self.assets['projectile']
                self.display.blit(p_img, (projectile[0][0]-p_img.get_width()/2 - r_scroll[0], projectile[0][1]-p_img.get_height()/2 - r_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Ember(projectile[0], random.random()-0.5+(math.pi if projectile[1]>0 else 0), 2+random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing)<50 and self.player.rect().collidepoint(projectile[0]):
                    self.projectiles.remove(projectile)
                    self.dead += 1
                    self.sfx['hit'].play()
                    self.screenshake = max(16, self.screenshake)
                    for i in range(30):
                        angle = random.random()*math.pi*2
                        speed = random.random()*5
                        self.sparks.append(Ember(self.player.rect().center, angle, 2+random.random()))
                        self.particles.append(VFXParticle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle+math.pi)*speed*0.5, math.sin(angle+math.pi)*speed*0.5], frame=random.randint(0,7)))
            
            # Sparks
            for s in self.sparks.copy():
                remove = s.update()
                s.render(self.display, offset=r_scroll)
                if remove:
                    self.sparks.remove(s)
            
            # Silhouette
            display_mask = pygame.mask.from_surface(self.display)
            sillhouette = display_mask.to_surface(setcolor=(0,0,0,180), unsetcolor=(0,0,0,0))
            for off in [(-1,0),(1,0),(0,-1),(0,1)]:
                self.display_2.blit(sillhouette, off)
            
            # Particles
            for p in self.particles.copy():
                rem = p.update()
                p.render(self.display, offset=r_scroll)
                if p.type == 'leaf':
                    p.pos[0] += math.sin(p.animation.frame*0.035)*0.3
                if rem:
                    self.particles.remove(p)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_high_score()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        if self.player.jump():
                            self.sfx['jump'].play()
                    if event.key == pygame.K_x:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False
            
            # Transition effect
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255,255,255), (self.display.get_width()//2, self.display.get_height()//2), (30 - abs(self.transition))*8)
                transition_surf.set_colorkey((255,255,255))
                self.display.blit(transition_surf, (0,0))
                
            self.display_2.blit(self.display, (0,0))
            
            # Update high score
            if self.score > self.high_score:
                self.high_score = self.score

            # Render HUD with shadows
            score_shadow = self.font.render(f'Score: {self.score}', True, (0,0,0))
            self.display_2.blit(score_shadow, (11,11))
            score_text = self.font.render(f'Score: {self.score}', True, (255,255,255))
            self.display_2.blit(score_text, (10,10))

            high_score_shadow = self.font.render(f'High Score: {self.high_score}', True, (0,0,0))
            self.display_2.blit(high_score_shadow, (11,23))
            high_score_text = self.font.render(f'High Score: {self.high_score}', True, (255,255,255))
            self.display_2.blit(high_score_text, (10,22))

            # Lives (hearts)
            for i in range(self.lives):
                x = 10 + i*(self.assets['heart'].get_width()+2)
                y = 34
                heart_shadow = self.assets['heart'].copy()
                heart_shadow.fill((0,0,0,150), special_flags=pygame.BLEND_RGBA_MULT)
                self.display_2.blit(heart_shadow, (x+1,y+1))
                self.display_2.blit(self.assets['heart'], (x,y))
            
            shake_off = (random.random()*self.screenshake - self.screenshake/2, random.random()*self.screenshake - self.screenshake/2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), shake_off)
            pygame.display.update()
            self.clock.tick(60)
            
            self.save_high_score()

JumperGame().run()