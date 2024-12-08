import os
import pygame

# Adjust base path as needed
BASE_IMG_PATH = 'data/images/'

def fetch_image(path):
    # Load a single image with transparency
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def fetch_images(path):
    # Load multiple images from a directory
    imgs = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        imgs.append(fetch_image(path + '/' + img_name))
    return imgs

class FrameAnimation:
    def __init__(self, frames, img_dur=5, loop=True):
        self.images = frames
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
    
    def copy(self):
        return FrameAnimation(self.images, self.img_duration, self.loop)
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    def img(self):
        # Return current frame's image
        return self.images[int(self.frame / self.img_duration)]