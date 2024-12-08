import json
import pygame

# Define autotiling patterns
AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2, 
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}

class WorldMap:
    # Manages tile-based world structure
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        
    def extract(self, id_pairs, keep=False):
        # Extract tiles by type and variant
        matches = []
        for t in self.offgrid_tiles.copy():
            if (t['type'], t['variant']) in id_pairs:
                matches.append(t.copy())
                if not keep:
                    self.offgrid_tiles.remove(t)
        
        for loc in list(self.tilemap.keys()):
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                new_copy = tile.copy()
                new_copy['pos'] = new_copy['pos'].copy()
                new_copy['pos'][0] *= self.tile_size
                new_copy['pos'][1] *= self.tile_size
                matches.append(new_copy)
                if not keep:
                    del self.tilemap[loc]
        
        return matches

    def tiles_around(self, pos):
        found = []
        tloc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for off in NEIGHBOR_OFFSETS:
            check_loc = str(tloc[0] + off[0]) + ';' + str(tloc[1] + off[1])
            if check_loc in self.tilemap:
                found.append(self.tilemap[check_loc])
        return found
    
    def save(self, path):
        with open(path, 'w') as f:
            json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        
    def load(self, path):
        with open(path, 'r') as f:
            map_data = json.load(f)
        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']
        
    def solid_check(self, pos):
        # Check if a position collides with a solid tile
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]
    
    def physics_rects_around(self, pos):
        rects = []
        for t in self.tiles_around(pos):
            if t['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(t['pos'][0]*self.tile_size, t['pos'][1]*self.tile_size, self.tile_size, self.tile_size))
        return rects
    
    def autotile(self):
        # Autotile logic based on neighbors
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                c_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if c_loc in self.tilemap and self.tilemap[c_loc]['type'] == tile['type']:
                    neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0)):
        # Draw offgrid tiles first
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0]-offset[0], tile['pos'][1]-offset[1]))
        
        # Then draw main tilemap
        start_x = offset[0] // self.tile_size
        end_x = (offset[0] + surf.get_width()) // self.tile_size + 1
        start_y = offset[1] // self.tile_size
        end_y = (offset[1] + surf.get_height()) // self.tile_size + 1
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    t = self.tilemap[loc]
                    surf.blit(self.game.assets[t['type']][t['variant']], (t['pos'][0]*self.tile_size - offset[0], t['pos'][1]*self.tile_size - offset[1]))