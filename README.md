# LLM Powered Mission Plannerfor UAV Operations

A sophisticated multi-agent simulation platform where LLM-powered drones explore a grid map, avoid hidden air defense systems, and destroy targets using intelligent pathfinding and risk assessment.

## Architecture

This project uses a modular architecture organized into logical subdirectories:

```
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── docker-compose.yml          # Docker Compose orchestration
├── .env.example               # Environment template
├── .env                       # API keys (create this)
├── .dockerignore              # Docker build context exclusions
├── README.md                  # This file
├── config/                    # Configuration package
│   ├── __init__.py
│   └── config.py              # All configuration settings
├── src/                       # Source code package
│   ├── __init__.py
│   ├── agents/                # AI agents
│   │   ├── __init__.py
│   │   ├── drone_agent.py     # LLM-powered drone agents
│   │   └── central_strategist.py # Central command AI
│   ├── core/                  # Core simulation components
│   │   ├── __init__.py
│   │   ├── simulation_engine.py # Main simulation loop
│   │   └── grid.py            # Map and tile management
│   └── systems/               # Specialized systems
│       ├── __init__.py
│       ├── missile_system.py  # Weapon system
│       └── visualizer.py      # Pygame visualization
├── docker/                    # Docker configuration
│   ├── Dockerfile             # Container configuration
│   └── docker-compose.yml     # Alternative compose file
└── docs/                      # Documentation (future)
```

## Key Features

### **LLM-Powered Agents**
- **Central Strategist**: GPT-4o controls overall strategy
- **Individual Drones**: Each drone has its own GPT-4o-mini for pathfinding decisions
- **Dynamic Decision Making**: Agents adapt to threats and discoveries

### **Intelligent Pathfinding**
- **3 Strategies**: DIRECT, AVOID_THREATS, CAUTIOUS
- **Threat Avoidance**: Known danger zones influence path planning
- **Fallback Mechanisms**: Safe path → risky path if needed

### **Fog of War System**
- **Progressive Discovery**: Map revealed through drone scanning
- **Hidden Threats**: HSS systems are invisible until triggered
- **Knowledge Sharing**: Central system distributes intelligence

### **Risk Management**
- **Threat Zones**: Areas where drones were destroyed
- **Battery Management**: Low battery forces return to base
- **Sacrifice Strategies**: Risk vs reward calculations

## Quick Start

### 1. **Setup Environment**
```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# API_KEY=your_openai_api_key_here
```

### 2. **Run with Docker Compose**
```bash
# Build and start the simulation
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the simulation
docker-compose down
```

### 3. **Configuration Options**
Edit your `.env` file or override in `docker-compose.yml`:
```bash
# Required
API_KEY=your_openai_api_key_here

# Optional overrides
ENABLE_VISUALIZATION=false      # Set to true for GUI (Linux X11 only)
MOCK_LLM_RESPONSE=false        # Set to true for testing without API
GRID_WIDTH=100                 # Map dimensions
NUM_DRONES=10                  # Number of drones
NUM_TARGETS=3                  # Targets to destroy
```

## Configuration

All configuration is handled through environment variables in your `.env` file:

### **Simulation Parameters**
```bash
GRID_WIDTH=100            # Map width
GRID_HEIGHT=100           # Map height
NUM_DRONES=10             # Number of drones
NUM_TARGETS=3             # Targets to destroy
NUM_HSS=4                 # Hidden air defense systems
INITIAL_MISSILES=5        # Starting missile count
```

### **LLM Settings**
```bash
LLM_MODEL=gpt-4o          # Main strategist model
MOCK_LLM_RESPONSE=false   # Use real API calls (set to true for testing)
```

### **Visualization & Performance**
```bash
ENABLE_VISUALIZATION=false # GUI display (set to true for Linux X11)
FPS=10                    # Simulation speed
DRONE_BATTERY_MAX=1000.0  # Battery capacity
DRONE_SCAN_RADIUS=5       # Scanning range
```

## Controls

- **Close Window**: End simulation
- **Watch**: Drones move autonomously
- **Console**: Strategy decisions and events logged

## Game Mechanics

### **Mission Objective**
Destroy all 3 hidden targets using 5 missiles while minimizing drone losses.

### **Threats**
- **HSS Systems**: Invisible air defense with circular kill zones (5-8 radius)
- **Obstacles**: Block movement and line-of-sight
- **Battery Depletion**: Drones must return to base to recharge

### **Intelligence Gathering**
- **Scanning**: Reveals 5x5 area around drone
- **Line-of-Sight**: Obstacles block vision
- **Reporting**: Discoveries shared with central command

### **Strategic Elements**
- **Exploration vs Safety**: Risk unknown areas for intelligence
- **Resource Management**: Battery and missile conservation
- **Adaptive Tactics**: Learn from drone losses

## Modules

### **AI Agents (`src/agents/`)**
- **`drone_agent.py`** - Individual drone with LLM-powered navigation:
  - Intelligent pathfinding with threat avoidance
  - Battery and resource management
  - Scanning and reporting capabilities
- **`central_strategist.py`** - Master AI controlling overall strategy:
  - World model maintenance
  - High-level mission planning
  - Resource allocation decisions

### **Core Components (`src/core/`)**
- **`simulation_engine.py`** - Main simulation loop:
  - Tick-based updates
  - Command distribution
  - Game state management
- **`grid.py`** - Map and environment management:
  - Procedural map generation
  - Line-of-sight calculations
  - Tile state management

### **Specialized Systems (`src/systems/`)**
- **`visualizer.py`** - Real-time visualization:
  - Pygame-based rendering
  - Fog of war display
  - Threat zone indicators
- **`missile_system.py`** - Weapon system:
  - Missile inventory management
  - Target validation and firing

### **Configuration (`config/`)**
- **`config.py`** - Centralized configuration:
  - Environment variable support
  - Simulation parameters
  - LLM and visualization settings

## Strategy Tips

1. **Early Exploration**: Spread drones to cover maximum area
2. **Active Scanning**: Use ACTIVE mode for exploration drones
3. **Threat Learning**: Mark and avoid areas where drones were lost
4. **Battery Management**: Return to base before critical levels
5. **Risk Assessment**: Balance safety vs discovery speed

## Development

### **Project Structure Benefits**
- **Modular Design**: Each package has a specific responsibility
- **Easy Testing**: Components can be tested in isolation
- **Scalable**: Add new agents, systems, or core components easily
- **Clean Imports**: Organized import structure prevents circular dependencies

### **Adding New Features**
- **New AI Agents**: Add to `src/agents/`
- **Core Simulation Logic**: Add to `src/core/`
- **Specialized Systems**: Add to `src/systems/`
- **Configuration**: Extend `config/config.py`

### **Extending Drone Behavior**
Edit `src/agents/drone_agent.py` to add new capabilities or decision-making logic.

### **Custom Strategies**
Modify prompts in `src/agents/central_strategist.py` and `src/agents/drone_agent.py` for different AI behaviors.

### **Map Variants**
Adjust `src/core/grid.py` for different map layouts or obstacle patterns.

### **Development Workflow**
```bash
# Run locally for development
python main.py

# Run in Docker for testing
docker-compose up --build

# Mount source for live development
docker-compose up -v $(pwd):/app
```

## Performance

- **API Optimization**: Drone LLMs consult every 10 ticks
- **Efficient Pathfinding**: BFS with early termination
- **Selective Reporting**: Reduce unnecessary communication

## Docker Deployment

### **Container Features**
- **Headless Operation**: Runs without GUI by default (perfect for servers)
- **Environment Isolation**: All dependencies contained
- **Easy Scaling**: Run multiple simulations with different configurations
- **Cross-Platform**: Works on Linux, macOS, and Windows

### **Docker Commands**
```bash
# Build the image manually
docker build -t drone-simulation .

# Run a single container
docker run --env-file .env drone-simulation

# Run with custom environment variables
docker run -e API_KEY=your_key -e MOCK_LLM_RESPONSE=true drone-simulation

# Run interactively (see logs in real-time)
docker run -it --env-file .env drone-simulation

# Run with volume mount for development
docker run -v $(pwd):/app --env-file .env drone-simulation
```

### **Docker Compose Advanced**
```bash
# Scale simulation (run multiple instances)
docker-compose up --scale drone-simulation=3

# Override environment variables
ENABLE_VISUALIZATION=true docker-compose up

# Use different compose file
docker-compose -f docker-compose.prod.yml up
```

## Troubleshooting

### **API Errors**
- Check `.env` file has valid `API_KEY`
- Verify OpenAI account has credits
- Use `MOCK_LLM_RESPONSE = True` for testing

### **Docker Issues**
- **Build fails**: Ensure Docker has enough memory (4GB+ recommended)
- **Container exits**: Check logs with `docker-compose logs`
- **Permission errors**: Ensure `.env` file is readable
- **GUI not working**: Use `ENABLE_VISUALIZATION=false` for headless mode

### **Performance Issues**
- Reduce `FPS` in `.env` file: `FPS=5`
- Decrease `NUM_DRONES` for simpler simulation: `NUM_DRONES=5`
- Disable visualization: `ENABLE_VISUALIZATION=false`

### **Environment Issues**
- Ensure `.env` file exists and contains `API_KEY`
- Check Docker and Docker Compose are installed
- Verify sufficient system resources (4GB+ RAM recommended)

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
