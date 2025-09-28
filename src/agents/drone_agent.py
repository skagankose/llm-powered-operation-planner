import openai
import json
import random
from collections import deque
from config.config import *

class DroneAgent:
    """Individual unit that moves on the map and collects sensor data."""
    def __init__(self, drone_id, grid):
        self.id = drone_id
        self.grid = grid
        self.position = {'x': random.randint(1, 9), 'y': random.randint(1, 9)}
        self.battery = DRONE_BATTERY_MAX
        self.status = 'ACTIVE'  # 'ACTIVE', 'RECHARGING', 'DESTROYED'
        self.current_command = {"command_type": "STANDBY"}
        self.scan_results = []
        self.scan_mode = 'PASSIVE'  # 'ACTIVE' or 'PASSIVE'
        self.path = []  # For A* pathfinding
        self.known_tiles = {}  # Tiles known by drone (from strategist)
        self.threat_zones = []  # Threat zones (from central system)
        self.client = openai.OpenAI(api_key=API_KEY)  # Drone's own LLM client
        self.last_llm_consultation_tick = 0

    def set_command(self, command):
        self.current_command = command
        # Handle scan mode command separately
        if 'scan_mode' in command:
            self.scan_mode = command['scan_mode']
            print(f"{self.id} scan mode updated: {self.scan_mode}")
        # Known tiles update (info from strategist)
        if 'known_tiles' in command:
            self.known_tiles = command['known_tiles']
            print(f"{self.id} map info updated: {len(self.known_tiles)} tiles known")
        # Threat zones update (from central system)
        if 'threat_zones' in command:
            self.threat_zones = command['threat_zones']
            print(f"{self.id} threat zone info updated: {len(self.threat_zones)} zones known")

    def update(self, current_tick=0):
        """Main update method called every tick."""
        if self.status != 'ACTIVE':
            return
        
        self.current_tick = current_tick  # Tick info for LLM consultation
        self.execute_command()
        
        # If battery runs out
        if self.battery <= 0:
            print(f"WARNING: {self.id} battery depleted and destroyed!")
            self.status = 'DESTROYED'

    def execute_command(self):
        """Processes commands from the center."""
        cmd_type = self.current_command.get('command_type')

        if cmd_type == 'MOVE_DRONE':
            target_pos = self.current_command.get('target_position')
            if target_pos:
                self.move(target_pos)
        elif cmd_type == 'SCAN_AREA':
            self.scan()
        elif cmd_type == 'STANDBY':
            # Recharge if in base area and battery is low
            tile = self.grid.get_tile(self.position['x'], self.position['y'])
            if tile.type == 'BASE' and self.battery < DRONE_BATTERY_MAX:
                self.recharge()
            else:
                pass  # Wait

    def move(self, target_position):
        """Moves towards target using pathfinding."""
        target_x, target_y = target_position['x'], target_position['y']
        
        if self.position['x'] == target_x and self.position['y'] == target_y:  # Reached target
            self.path = []  # Clear path
            # Check scan mode after reaching target
            if self.scan_mode == 'ACTIVE':
                print(f"{self.id} reached target and auto-scanning (ACTIVE mode)")
                self.scan()
            else:
                self.current_command = {"command_type": "STANDBY"}  # Wait for new command
            return

        # Calculate new path if none exists or invalid
        if not self.path or not self._is_path_valid():
            self.path = self._find_path_to_target(target_x, target_y)
            if not self.path:
                print(f"{self.id} no path found to target ({target_x},{target_y}), waiting.")
                self.current_command = {"command_type": "STANDBY"}
                return

        # Move to next position in path
        if self.path:
            next_pos = self.path.pop(0)
            next_x, next_y = next_pos['x'], next_pos['y']
            
            # Ground truth check (real collision detection)
            tile = self.grid.get_tile(next_x, next_y)
            if tile and tile.type != 'OBSTACLE':
                self.position['x'] = next_x
                self.position['y'] = next_y
                self.battery -= COST_MOVE
                
                # ACTIVE scan mode - scan while moving
                if self.scan_mode == 'ACTIVE' and random.random() < 0.3:  # 30% chance
                    print(f"{self.id} scanned while moving (ACTIVE mode)")
                    self.scan()
            else:
                # Hit real obstacle (unknown obstacle discovered)
                print(f"{self.id} hit unknown obstacle at ({next_x},{next_y}), recalculating route.")
                # Add this obstacle to known_tiles (discovered)
                self.known_tiles[(next_x, next_y)] = {'type': 'OBSTACLE', 'position': {'x': next_x, 'y': next_y}}
                self.path = []

    def _is_path_valid(self):
        """Checks if current path is still valid."""
        for pos in self.path:
            tile = self.grid.get_tile(pos['x'], pos['y'])
            if not tile or tile.type == 'OBSTACLE':
                return False
        return True

    def _find_path_to_target(self, target_x, target_y):
        """HSS-aware pathfinding that avoids known danger zones."""
        start = (self.position['x'], self.position['y'])
        target = (target_x, target_y)
        
        if start == target:
            return []
        
        # Simple HSS avoidance pathfinding
        return self._bfs_pathfind_avoid_hss(target_x, target_y)

    def _bfs_pathfind_avoid_hss(self, target_x, target_y):
        """BFS pathfinding that avoids known HSS danger zones."""
        from collections import deque
        
        start = (self.position['x'], self.position['y'])
        target = (target_x, target_y)
        
        queue = deque([(start, [])])
        visited = {start}
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]  # 8 directions
        
        while queue:
            (current_x, current_y), path = queue.popleft()
            
            if (current_x, current_y) == target:
                # Convert path back to list of position dictionaries
                return [{'x': x, 'y': y} for x, y in path]
            
            for dx, dy in directions:
                next_x, next_y = current_x + dx, current_y + dy
                
                # Bounds check
                if not (0 <= next_x < GRID_WIDTH and 0 <= next_y < GRID_HEIGHT):
                    continue
                
                if (next_x, next_y) in visited:
                    continue
                
                # Check known obstacles
                if self._is_known_obstacle(next_x, next_y):
                    continue
                
                # Check HSS danger zones
                if self._is_in_hss_danger_zone(next_x, next_y):
                    continue
                
                visited.add((next_x, next_y))
                new_path = path + [(next_x, next_y)]
                queue.append(((next_x, next_y), new_path))
        
        return []  # No path found

    def _is_known_obstacle(self, x, y):
        """Checks known obstacles (known tiles only)."""
        # Only check obstacles in known tiles
        tile_key = (x, y)
        if tile_key in self.known_tiles:
            tile_data = self.known_tiles[tile_key]
            return tile_data.get('type') == 'OBSTACLE'
        
        # Unknown tiles are not obstacles (considered passable)
        return False

    def _is_in_hss_danger_zone(self, x, y):
        """Check if position is within any known HSS danger zone."""
        for zone in self.threat_zones:
            if 'hss_location' in zone:
                # Precise HSS location and radius
                hss_x = zone['hss_location']['x']
                hss_y = zone['hss_location']['y']
                hss_radius = zone['radius']
                
                # Calculate distance from position to HSS
                dist_sq = (x - hss_x)**2 + (y - hss_y)**2
                if dist_sq <= hss_radius**2:
                    return True
            elif 'center' in zone:
                # Fallback for old-style threat zones
                center_x = zone['center']['x']
                center_y = zone['center']['y']
                radius = zone['radius']
                
                dist_sq = (x - center_x)**2 + (y - center_y)**2
                if dist_sq <= radius**2:
                    return True
        
        return False

    def scan(self):
        self.scan_results = self.grid.get_visible_tiles(
            self.position['x'], self.position['y'], DRONE_SCAN_RADIUS
        )
        self.battery -= COST_SCAN
        print(f"{self.id} scanned area around position ({self.position['x']},{self.position['y']}). {len(self.scan_results)} tiles found.")
        # Wait for new command after scanning
        self.current_command = {"command_type": "STANDBY"}

    def recharge(self):
        self.battery = min(DRONE_BATTERY_MAX, self.battery + BASE_RECHARGE_RATE)
        print(f"{self.id} charging at base. Current Battery: {self.battery:.1f}")

    def report_to_center(self):
        """Prepares current status and scan results in JSON format."""
        if self.status == 'DESTROYED':
            return None

        report = {
            "drone_id": self.id,
            "status": self.status,
            "position": self.position,
            "battery": round(self.battery, 2),
            "scan_results": []
        }
        
        for tile in self.scan_results:
            tile_data = {
                "type": tile.type if tile.type != 'HSS' else 'EMPTY',  # HSS are invisible in scans
                "position": {"x": tile.x, "y": tile.y}
            }
            if tile.type == 'TARGET':
                tile_data["properties"] = tile.properties
            report["scan_results"].append(tile_data)
            
            # Add scan results to own known_tiles
            self.known_tiles[(tile.x, tile.y)] = tile_data

        self.battery -= COST_REPORT
        self.scan_results = []  # Clear scan results after reporting
        return report 