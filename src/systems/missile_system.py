from config.config import INITIAL_MISSILES

class MissileSystem:
    """Manages missile inventory and firing commands."""
    def __init__(self, grid):
        self.missile_count = INITIAL_MISSILES
        self.grid = grid

    def fire(self, target_coord):
        if self.missile_count <= 0:
            print("NO MISSILES LEFT!")
            return False
            
        x, y = target_coord['x'], target_coord['y']
        tile = self.grid.get_tile(x, y)
        
        # SAFETY CHECK: Only fire if there's actually a target there
        if tile and tile.type == 'TARGET':
            print(f"MISSILE FIRED: {tile.properties['target_id']} at ({x}, {y}) destroyed!")
            tile.type = 'EMPTY'
            tile.properties = {}
            self.missile_count -= 1
            return True
        else:
            # NO MISSILE WASTED: Just report the error
            print(f"MISSILE ABORT: No target found at ({x}, {y}) - missile saved!")
            return False 