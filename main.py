"""
Advanced Combustion Engine Simulator
----------------------------------
A high-fidelity simulation with realistic physics and AI integration.
"""

import sys
import time
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from engine.mechanics import Engine
from engine.visualization import EngineRenderer

class EngineSimulator:
    def __init__(self):
        # Initialize engine with realistic parameters
        self.engine = Engine(cylinders=4, bore=0.086, stroke=0.086, cr=10.5)
        self.renderer = EngineRenderer()
        self.running = True
        self.throttle = 0.3
        self.load = 0.5
        self.clock = pygame.time.Clock()
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.running = False
        
        keys = pygame.key.get_pressed()
        if keys[K_UP] or keys[K_w]:
            self.throttle = min(1.0, self.throttle + 0.01)
        if keys[K_DOWN] or keys[K_s]:
            self.throttle = max(0.0, self.throttle - 0.01)
    
    def run(self):
        last_time = time.time()
        
        while self.running:
            # Calculate delta time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Handle input
            self.handle_input()
            
            # Update engine
            self.engine.update(dt, self.throttle)
            
            # Render
            self.renderer.render_engine(self.engine, self.throttle)
            
            # Cap at 60 FPS
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("Starting Advanced Engine Simulator...")
    print("Controls:")
    print("- Up/Down arrows: Control throttle")
    print("- ESC: Quit")
    
    simulator = EngineSimulator()
    simulator.run()
