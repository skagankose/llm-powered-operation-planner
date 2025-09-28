import time
from config.config import *
from src.core.grid import Grid
from src.agents.drone_agent import DroneAgent
from src.systems.missile_system import MissileSystem
from src.agents.central_strategist import CentralStrategist
from src.systems.visualizer import Visualizer

if ENABLE_VISUALIZATION:
    import pygame

class SimulationEngine:
    """Manages the main simulation loop and brings all components together."""
    def __init__(self):
        self.grid = Grid(GRID_WIDTH, GRID_HEIGHT)
        self.drones = [DroneAgent(f"D-{i+1}", self.grid) for i in range(NUM_DRONES)]
        self.missile_system = MissileSystem(self.grid)
        self.central_strategist = CentralStrategist(self.grid)
        self.current_tick = 0
        self.game_over = False
        self.game_over_message = ""
        self.visualizer = None
        if ENABLE_VISUALIZATION:
            self.visualizer = Visualizer(self)

    def run(self):
        """Starts the main simulation loop."""
        
        # Get initial commands
        self._distribute_commands()

        while not self.game_over:
            start_time = time.time()
            
            self.tick()
            
            if self.visualizer:
                self.visualizer.draw()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.game_over = True
                        self.game_over_message = "User closed simulation."

            self.check_game_over()
            
            # Adjust FPS
            elapsed = time.time() - start_time
            sleep_time = (1.0 / FPS) - elapsed
            if sleep_time > 0 and ENABLE_VISUALIZATION:
                time.sleep(sleep_time)

        print("\n--- SIMULATION ENDED ---")
        print(f"Result: {self.game_over_message}")
        print(f"Total Elapsed Time (Ticks): {self.current_tick}")

    def _distribute_commands(self):
        """Gets commands from strategist and distributes them to relevant units."""
        commands_json = self.central_strategist.plan_next_moves(self.current_tick, self.drones, self.missile_system)
        
        if not commands_json or 'commands' not in commands_json:
            print("Invalid command format received. Drones waiting.")
            return

        print(f"\n--- TICK {self.current_tick} | Strategist's Assessment ---\n{commands_json.get('reasoning')}\n")

        # Send current known_tiles and threat_zones info to each drone
        for drone in self.drones:
            if drone.status == 'ACTIVE':
                # Transfer all tiles and threat zones known by strategist to drone
                drone.known_tiles = self.central_strategist.world_model['known_tiles'].copy()
                drone.threat_zones = self.central_strategist.world_model['potential_threat_zones'].copy()

        for command in commands_json['commands']:
            cmd_type = command.get('command_type')
            if cmd_type in ['MOVE_DRONE', 'SCAN_AREA', 'STANDBY']:
                drone_id = command.get('drone_id')
                for drone in self.drones:
                    if drone.id == drone_id and drone.status == 'ACTIVE':
                        # Add known tiles and threat zones info to command
                        command['known_tiles'] = self.central_strategist.world_model['known_tiles'].copy()
                        command['threat_zones'] = self.central_strategist.world_model['potential_threat_zones'].copy()
                        drone.set_command(command)
                        print(f"Command given: {drone_id} -> {cmd_type}")
                        break
            elif cmd_type == 'SET_SCAN_MODE':
                drone_id = command.get('drone_id')
                scan_mode = command.get('scan_mode')
                for drone in self.drones:
                    if drone.id == drone_id and drone.status == 'ACTIVE':
                        drone.scan_mode = scan_mode
                        print(f"Scan mode changed: {drone_id} -> {scan_mode}")
                        break
            elif cmd_type == 'FIRE_MISSILE':
                self.missile_system.fire(command.get('target_position'))

    def tick(self):
        """Advances the simulation by one step."""
        self.current_tick += 1
        print(f"\n===== TICK: {self.current_tick} =====")

        # 1. Drone Actions
        for drone in self.drones:
            drone.update(self.current_tick)

        # 2. Environmental Checks (HSS)
        for drone in self.drones:
            if drone.status == 'ACTIVE':
                # Check distance to all HSS on the map
                for hss_x in range(GRID_WIDTH):
                    for hss_y in range(GRID_HEIGHT):
                        tile = self.grid.get_tile(hss_x, hss_y)
                        if tile and tile.type == 'HSS':
                            # Calculate distance using Pythagorean theorem: a^2 + b^2 = c^2
                            dist_sq = (drone.position['x'] - hss_x)**2 + (drone.position['y'] - hss_y)**2
                            radius = tile.properties.get('kill_zone_radius', 5)
                            
                            if dist_sq <= radius**2:
                                print(f"!!! {drone.id} destroyed by HSS at ({hss_x},{hss_y}) kill zone: {drone.position} !!!")
                                drone.status = 'DESTROYED'
                                self.central_strategist.add_threat_zone(drone.position)
                                # No need to check other HSS since drone is destroyed
                                break 
                    if drone.status == 'DESTROYED':
                        break

        # 3. Reporting and Planning
        # Plan every 5 ticks (to reduce API costs)
        if self.current_tick % 5 == 1:
            # Collect reports
            all_reports = []
            for drone in self.drones:
                # Instead of reporting every tick, only when scanning or
                # completing objectives is more efficient.
                # In this simulation everyone reports before each planning.
                report = drone.report_to_center()
                if report:
                    all_reports.append(report)
            
            # Strategist processes reports
            self.central_strategist.collect_reports(all_reports)

            # Get and distribute new commands
            self._distribute_commands()
        
    def check_game_over(self):
        # Success Condition
        active_targets = 0
        for row in self.grid.tiles:
            for tile in row:
                if tile.type == 'TARGET':
                    active_targets += 1
        
        if active_targets == 0:
            self.game_over = True
            self.game_over_message = "SUCCESS: All targets destroyed!"
            return

        # Failure Condition
        active_drones = sum(1 for d in self.drones if d.status != 'DESTROYED')
        if active_drones == 0:
            self.game_over = True
            self.game_over_message = "FAILURE: All drones lost."
            return
        
        if self.missile_system.missile_count == 0 and not self.central_strategist.world_model['known_targets']:
             # This condition can be made more complex.
             # For example, if missiles are finished and there are still undiscovered targets.
             pass 