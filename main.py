#!/usr/bin/env python3
"""
Strategist Drone Simulation - Main Entry Point

A multi-agent simulation where LLM-powered drones explore a grid map,
avoid hidden air defense systems, and destroy targets using intelligent
pathfinding and risk assessment.
"""

from config.config import API_KEY, MOCK_LLM_RESPONSE, ENABLE_VISUALIZATION
from src.core.simulation_engine import SimulationEngine

if ENABLE_VISUALIZATION:
    import pygame

def main():
    """Main entry point for the simulation."""
    if API_KEY is None and not MOCK_LLM_RESPONSE:
        print("ERROR: Please set API_KEY in your .env file!")
        print("OR set MOCK_LLM_RESPONSE = True in config.py for testing.")
        return
    
    print("🚁 Starting Strategist Drone Simulation...")
    print("=" * 50)
    
    try:
        sim = SimulationEngine()
        sim.run()
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted by user.")
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
    finally:
        if ENABLE_VISUALIZATION:
            pygame.quit()
        print("🏁 Simulation completed.")

if __name__ == '__main__':
    main() 