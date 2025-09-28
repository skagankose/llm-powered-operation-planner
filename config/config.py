import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_KEY = os.getenv("API_KEY")

# Simulation Settings (with environment variable overrides)
GRID_WIDTH = int(os.getenv("GRID_WIDTH", 100))
GRID_HEIGHT = int(os.getenv("GRID_HEIGHT", 100))
NUM_DRONES = int(os.getenv("NUM_DRONES", 10))
NUM_TARGETS = int(os.getenv("NUM_TARGETS", 3))
NUM_HSS = int(os.getenv("NUM_HSS", 4))  # Hidden Air Defense Systems
INITIAL_MISSILES = int(os.getenv("INITIAL_MISSILES", 5))

# LLM Settings (with environment variable overrides)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
# Set to True to skip API calls and use mock response for testing
MOCK_LLM_RESPONSE = os.getenv("MOCK_LLM_RESPONSE", "false").lower() == "true"

# Drone Settings (with environment variable overrides)
DRONE_BATTERY_MAX = float(os.getenv("DRONE_BATTERY_MAX", 1000.0))
DRONE_SCAN_RADIUS = int(os.getenv("DRONE_SCAN_RADIUS", 5))  # Manhattan distance
COST_MOVE = float(os.getenv("COST_MOVE", 1.0))
COST_SCAN = float(os.getenv("COST_SCAN", 5.0))
COST_REPORT = float(os.getenv("COST_REPORT", 2.0))
BASE_RECHARGE_RATE = float(os.getenv("BASE_RECHARGE_RATE", 50.0))

# Visualization Settings (with environment variable overrides)
ENABLE_VISUALIZATION = os.getenv("ENABLE_VISUALIZATION", "true").lower() == "true"
CELL_SIZE = int(os.getenv("CELL_SIZE", 8))
FPS = int(os.getenv("FPS", 10))  # Controls simulation speed

# Colors
COLOR_BG = (10, 10, 20)
COLOR_GRID = (40, 40, 50)
COLOR_EMPTY = (25, 25, 40)
COLOR_OBSTACLE = (100, 100, 100)
COLOR_BASE = (0, 150, 50, 100)
COLOR_TARGET = (255, 0, 0)
COLOR_HSS = (255, 100, 0)  # For debug only
COLOR_DRONE = (0, 200, 255)
COLOR_DRONE_DESTROYED = (150, 0, 0)
COLOR_SCAN_AREA = (255, 255, 0, 50)
COLOR_KNOWN_WORLD = (0, 0, 255, 30)  # Areas known by strategist
COLOR_HSS_RANGE = (255, 100, 0, 60)

# Calculated values
if ENABLE_VISUALIZATION:
    SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
    SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE 