import random

class SkyCloud:
    # Individual cloud with parallax
    def __init__(self, pos, img, speed, depth):
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth
    
    def update(self):
        self.pos[0] += self.speed
        
    def render(self, surf, offset=(0, 0)):
        rp = (self.pos[0]-offset[0]*self.depth, self.pos[1]-offset[1]*self.depth)
        surf.blit(self.img, (rp[0] % (surf.get_width()+self.img.get_width()) - self.img.get_width(), 
                             rp[1] % (surf.get_height()+self.img.get_height()) - self.img.get_height()))

class SkyClouds:
    # Collection of clouds
    def __init__(self, cloud_images, count=16):
        self.clouds = []
        for i in range(count):
            self.clouds.append(SkyCloud((random.random()*99999, random.random()*99999), 
                                        random.choice(cloud_images), 
                                        random.random()*0.05+0.05, 
                                        random.random()*0.6+0.2))
        self.clouds.sort(key=lambda c: c.depth)
    
    def update(self):
        for c in self.clouds:
            c.update()
    
    def render(self, surf, offset=(0, 0)):
        for c in self.clouds:
            c.render(surf, offset=offset)