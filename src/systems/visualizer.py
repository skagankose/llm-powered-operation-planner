from config.config import *

if ENABLE_VISUALIZATION:
    import pygame

class Visualizer:
    def __init__(self, engine):
        if not ENABLE_VISUALIZATION:
            return
            
        pygame.init()
        pygame.display.set_caption("Strategist Drone Simulation")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.font = pygame.font.SysFont('Arial', 10)
        self.engine = engine

    def draw(self):
        if not ENABLE_VISUALIZATION:
            return
            
        self.screen.fill(COLOR_BG)
        self.draw_grid()
        self.draw_known_world()
        self.draw_drones()
        self.draw_info()
        pygame.display.flip()

    def draw_grid(self):
        # First draw known HSS danger zones from strategist's world model
        for zone in self.engine.central_strategist.world_model['potential_threat_zones']:
            if 'hss_location' in zone:
                # Draw precise HSS danger zone
                hss_x = zone['hss_location']['x']
                hss_y = zone['hss_location']['y']
                hss_radius = zone['radius']
                
                radius_in_pixels = hss_radius * CELL_SIZE
                center_pixel_x = hss_x * CELL_SIZE + CELL_SIZE // 2
                center_pixel_y = (GRID_HEIGHT - 1 - hss_y) * CELL_SIZE + CELL_SIZE // 2
                
                # Create a surface to draw semi-transparent circle
                s = pygame.Surface((radius_in_pixels * 2, radius_in_pixels * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, COLOR_HSS_RANGE, (radius_in_pixels, radius_in_pixels), radius_in_pixels)
                self.screen.blit(s, (center_pixel_x - radius_in_pixels, center_pixel_y - radius_in_pixels))
                
                # Draw HSS center as a red X to mark discovered location
                pygame.draw.line(self.screen, COLOR_HSS, 
                               (center_pixel_x - CELL_SIZE//3, center_pixel_y - CELL_SIZE//3),
                               (center_pixel_x + CELL_SIZE//3, center_pixel_y + CELL_SIZE//3), 3)
                pygame.draw.line(self.screen, COLOR_HSS, 
                               (center_pixel_x + CELL_SIZE//3, center_pixel_y - CELL_SIZE//3),
                               (center_pixel_x - CELL_SIZE//3, center_pixel_y + CELL_SIZE//3), 3)
            elif 'center' in zone:
                # Draw old-style estimated threat zones
                center_x = zone['center']['x']
                center_y = zone['center']['y']
                radius = zone['radius']
                
                radius_in_pixels = radius * CELL_SIZE
                center_pixel_x = center_x * CELL_SIZE + CELL_SIZE // 2
                center_pixel_y = (GRID_HEIGHT - 1 - center_y) * CELL_SIZE + CELL_SIZE // 2
                
                s = pygame.Surface((radius_in_pixels * 2, radius_in_pixels * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 200, 0, 80), (radius_in_pixels, radius_in_pixels), radius_in_pixels)
                self.screen.blit(s, (center_pixel_x - radius_in_pixels, center_pixel_y - radius_in_pixels))

        # Now draw other tiles (but NOT actual HSS positions - that would be cheating!)
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                rect = pygame.Rect(x * CELL_SIZE, (GRID_HEIGHT - 1 - y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                tile = self.engine.grid.get_tile(x, y)
                color = COLOR_EMPTY
                if tile.type == 'OBSTACLE':
                    color = COLOR_OBSTACLE
                elif tile.type == 'BASE':
                    # Draw base area separately, skip here
                    pass
                elif tile.type == 'TARGET':
                    color = COLOR_TARGET
                # Don't draw HSS tiles - they should be invisible until discovered!

                if color != COLOR_EMPTY:
                    pygame.draw.rect(self.screen, color, rect, (1 if color == COLOR_EMPTY else 0))

        # Draw base area last so it doesn't cover everything else
        for x in range(11):
            for y in range(11):
                rect = pygame.Rect(x * CELL_SIZE, (GRID_HEIGHT - 1 - y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                s.fill(COLOR_BASE)
                self.screen.blit(s, rect.topleft)

    def draw_known_world(self):
        """Visualizes areas known by the strategist."""
        s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        s.fill(COLOR_KNOWN_WORLD)
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                 tile = self.engine.grid.get_tile(x, y)
                 if tile.is_known_by_strategist:
                     rect = pygame.Rect(x * CELL_SIZE, (GRID_HEIGHT - 1 - y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                     self.screen.blit(s, rect.topleft)

    def draw_drones(self):
        for drone in self.engine.drones:
            x, y = drone.position['x'], drone.position['y']
            center = (x * CELL_SIZE + CELL_SIZE // 2, (GRID_HEIGHT - 1 - y) * CELL_SIZE + CELL_SIZE // 2)
            color = COLOR_DRONE if drone.status != 'DESTROYED' else COLOR_DRONE_DESTROYED
            pygame.draw.circle(self.screen, color, center, CELL_SIZE // 2)
            
            # Draw drone ID
            id_text = self.font.render(drone.id.split('-')[1], True, (255, 255, 255))
            self.screen.blit(id_text, (center[0] - id_text.get_width() // 2, center[1] - id_text.get_height() // 2))

    def draw_info(self):
        """Draws general information on screen."""
        known_hss_count = len([zone for zone in self.engine.central_strategist.world_model['potential_threat_zones'] 
                              if 'hss_location' in zone])
        
        info_texts = [
            f"Tick: {self.engine.current_tick}",
            f"Missiles: {self.engine.missile_system.missile_count}",
            f"Active Drones: {sum(1 for d in self.engine.drones if d.status != 'DESTROYED')}/{NUM_DRONES}",
            f"Remaining Targets: {sum(1 for row in self.engine.grid.tiles for tile in row if tile.type == 'TARGET')}",
            f"Discovered HSS: {known_hss_count}/{NUM_HSS}"
        ]
        
        for i, text in enumerate(info_texts):
            text_surf = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surf, (5, 5 + i * 15)) 