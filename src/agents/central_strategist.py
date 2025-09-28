import openai
import json
from config.config import *

class CentralStrategist:
    """Collects information from all drones, makes plans with GPT-4o and sends commands."""
    def __init__(self, grid):
        self.llm_api_key = API_KEY
        self.llm_model = LLM_MODEL
        self.client = openai.OpenAI(api_key=self.llm_api_key)
        self.grid = grid
        # World model: Everything the strategist knows is stored here
        self.world_model = {
            "grid_size": {"width": GRID_WIDTH, "height": GRID_HEIGHT},
            "base_location": {"x_range": [0, 10], "y_range": [0, 10]},
            "known_tiles": {},  # (x, y) -> Tile
            "known_targets": {},  # target_id -> {"position": ..., "status": ...}
            "potential_threat_zones": []  # HSS suspicions
        }

    def collect_reports(self, reports):
        """Receives drone reports and updates world model."""
        for report in reports:
            if not report: continue
            # Process scan results
            for tile_data in report['scan_results']:
                x, y = tile_data['position']['x'], tile_data['position']['y']
                
                # Add to world model
                if (x,y) not in self.world_model['known_tiles']:
                     self.world_model['known_tiles'][(x,y)] = tile_data

                self.grid.get_tile(x, y).is_known_by_strategist = True

                if tile_data['type'] == 'TARGET':
                    target_id = tile_data['properties']['target_id']
                    if target_id not in self.world_model['known_targets']:
                        print(f"STRATEGIST: New target found! {target_id} at ({x},{y})")
                        self.world_model['known_targets'][target_id] = {
                            "position": tile_data['position'],
                            "status": "CONFIRMED"
                        }
    
    def add_threat_zone(self, drone_position):
        """Enhanced HSS detection: Precisely identify HSS location and radius when drone is destroyed."""
        drone_x, drone_y = drone_position['x'], drone_position['y']
        
        # Find the actual HSS that killed the drone
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                tile = self.grid.get_tile(x, y)
                if tile and tile.type == 'HSS':
                    # Calculate distance from drone to HSS
                    dist_sq = (drone_x - x)**2 + (drone_y - y)**2
                    hss_radius = tile.properties.get('kill_zone_radius', 5)
                    
                    # If drone was within this HSS's kill zone, this is the HSS that killed it
                    if dist_sq <= hss_radius**2:
                        # Check if we already know about this HSS
                        hss_already_known = False
                        for zone in self.world_model['potential_threat_zones']:
                            if ('hss_location' in zone and 
                                zone['hss_location']['x'] == x and 
                                zone['hss_location']['y'] == y):
                                hss_already_known = True
                                break
                        
                        if not hss_already_known:
                            # Add precise HSS information to world model
                            precise_hss_zone = {
                                "hss_location": {"x": x, "y": y},
                                "radius": hss_radius,
                                "confidence": "CONFIRMED",
                                "discovered_by_drone_loss": drone_position
                            }
                            self.world_model['potential_threat_zones'].append(precise_hss_zone)
                            print(f"STRATEGIST: HSS DISCOVERED! Location: ({x},{y}), Radius: {hss_radius}, Drone lost at: ({drone_x},{drone_y})")
                        
                        return  # Found the HSS that killed the drone
        
        # If no HSS found (shouldn't happen), add general threat zone as fallback
        print(f"STRATEGIST: Warning - Drone destroyed but no HSS found at {drone_position}")
        fallback_zone = {"center": drone_position, "radius": 8, "confidence": "ESTIMATED"}
        self.world_model['potential_threat_zones'].append(fallback_zone)

    def _format_state_for_llm(self, tick, drones, missile_system):
        """Converts current world model to JSON format for sending to LLM."""
        
        # Process known obstacles and targets
        known_obstacles = []
        for (x,y), tile in self.world_model['known_tiles'].items():
            if tile['type'] == 'OBSTACLE':
                known_obstacles.append({'x': x, 'y': y})
        
        known_targets_list = [
            {"id": tid, **tdata} for tid, tdata in self.world_model['known_targets'].items()
        ]

        drones_state = []
        for d in drones:
            state = {"id": d.id, "status": d.status, "battery": round(d.battery, 2), "scan_mode": d.scan_mode}
            if d.status == 'DESTROYED':
                state["last_known_position"] = d.position
            else:
                state["position"] = d.position
            drones_state.append(state)

        state_json = {
            "tick": tick,
            "mission_objective": "Destroy all 3 targets. Minimize drone losses by avoiding unknown HSS.",
            "resources": {
                "missiles_left": missile_system.missile_count
            },
            "drones": drones_state,
            "known_world": {
                "grid_size": self.world_model['grid_size'],
                "base_location": self.world_model['base_location'],
                "known_obstacles": known_obstacles,
                "known_targets": known_targets_list,
                "potential_threat_zones": self.world_model['potential_threat_zones']
            }
        }
        return state_json

    def plan_next_moves(self, current_tick, drones, missile_system):
        """Sends request to LLM and parses returned commands."""
        world_state = self._format_state_for_llm(current_tick, drones, missile_system)
        
        system_prompt = """
# ROLE AND GOAL
You are "Stratejist", a central command AI for a swarm of 10 autonomous drones. Your mission is to explore a 100x100 grid map, identify all 3 enemy targets, and destroy them using a limited supply of 5 missiles. You must achieve this while minimizing drone losses to hidden Hostile Air Defense Systems (HSS).

# RULES
1.  **Map:** The map is a 100x100 grid. (0,0) is the bottom-left. Your base is at (0,0) to (10,10).
2.  **Drones:** Drones consume battery for every action. They can recharge at the Base. Send them to base if battery is low (e.g., < 200). Drones that reach their target position will automatically go into STANDBY. Give them a new task.
3.  **Threats (HSS):** HSSs are stationary and invisible. If a drone is destroyed, its last known position is a strong clue to a HSS location. Assume HSS kill zones are circular. Mark that area as a threat and avoid it.
4.  **Strategy:** Initially, spread your drones out to explore different quadrants of the map. Set drone scan_mode to 'ACTIVE' for exploration drones and 'PASSIVE' for strategic drones. ACTIVE drones will automatically scan when they reach destinations and occasionally while moving.
5.  **Commands:** You can issue 'MOVE_DRONE', 'SCAN_AREA', 'SET_SCAN_MODE', 'FIRE_MISSILE', or 'STANDBY'. You can also set scan_mode='ACTIVE' or 'PASSIVE' for each drone to control their scanning behavior.
6.  **CRITICAL - MISSILE TARGETING:** ONLY fire missiles at coordinates where you have CONFIRMED targets in the known_targets list. NEVER fire at coordinates you haven't scanned or where targets are uncertain. Each missile is precious - you only have 5 total!
7.  **Communication:** You receive a JSON object with the current world state. You MUST respond with a single valid JSON object containing your reasoning and a list of commands. Do not output any other text or formatting.

# INPUT FORMAT (World State JSON)
You will receive a JSON object with the structure you are about to see.

# OUTPUT FORMAT (Your Command JSON)
Your response MUST be a single JSON object in this exact format:
{
  "reasoning": "<Your brief strategic thought process for this turn>",
  "commands": [
    { "command_type": "MOVE_DRONE", "drone_id": "<drone_id>", "target_position": {"x": <int>, "y": <int>} },
    { "command_type": "SCAN_AREA", "drone_id": "<drone_id>" },
    { "command_type": "SET_SCAN_MODE", "drone_id": "<drone_id>", "scan_mode": "ACTIVE" },
    { "command_type": "SET_SCAN_MODE", "drone_id": "<drone_id>", "scan_mode": "PASSIVE" },
    { "command_type": "FIRE_MISSILE", "target_position": {"x": <int>, "y": <int>} },
    { "command_type": "STANDBY", "drone_id": "<drone_id>", "reason": "<optional reason>" }
  ]
}

Now, analyze the provided world state and generate the commands for the next tick.
        """

        if MOCK_LLM_RESPONSE:
            print("--- USING MOCK LLM ---")
            mock_response = {
                "reasoning": "This is a mock response. Sending D-1 and D-2 in ACTIVE scan mode for exploration, D-3 and D-4 for manual scanning.",
                "commands": [
                    {"command_type": "SET_SCAN_MODE", "drone_id": "D-1", "scan_mode": "ACTIVE"},
                    {"command_type": "SET_SCAN_MODE", "drone_id": "D-2", "scan_mode": "ACTIVE"},
                    {"command_type": "MOVE_DRONE", "drone_id": "D-1", "target_position": {"x": 25, "y": 75}},
                    {"command_type": "MOVE_DRONE", "drone_id": "D-2", "target_position": {"x": 75, "y": 75}},
                    {"command_type": "SCAN_AREA", "drone_id": "D-3"},
                    {"command_type": "SCAN_AREA", "drone_id": "D-4"}
                ]
            }
            return mock_response

        print("Strategist thinking... (Making LLM API call)")
        print(self.llm_api_key)
        print()
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(world_state, indent=2)}
                ],
                response_format={"type": "json_object"}
            )
            llm_output = response.choices[0].message.content
            print("Response from Strategist:", llm_output)
            return json.loads(llm_output)
        except Exception as e:
            print(f"LLM API Error: {e}")
            # Return empty command on error
            return {"reasoning": "API error occurred, all units on standby.", "commands": []} 