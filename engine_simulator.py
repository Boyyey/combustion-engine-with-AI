import pygame
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from sklearn.ensemble import RandomForestRegressor
import random
import math
from dataclasses import dataclass

# Constants and setup
SCREEN_SIZE = (1200, 800)
FPS = 60

class EngineSimulator:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("AI-Powered Combustion Engine Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 18)
        self.running = True
        
        # Engine parameters
        self.rpm = 800
        self.throttle = 0.5
        self.load = 0.5
        self.temperature = 90
        self.pressure = 1.0
        self.angle = 0
        
        # Initialize AI model
        self.ai_model = self._init_ai_model()
        self.ai_predictions = []
        
    def _init_ai_model(self):
        # Generate synthetic training data
        X = np.random.rand(1000, 4)
        y = np.random.rand(1000) * 100
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        return model
    
    def predict_engine_health(self):
        X = np.array([[
            self.rpm / 8000,
            self.load,
            self.temperature / 150,
            self.pressure / 5
        ]])
        health = self.ai_model.predict(X)[0]
        self.ai_predictions = (self.ai_predictions + [health])[-100:]
        return health
    
    def update(self, dt):
        # Update engine state
        rpm_change = (self.throttle * 2 - 0.5) * 1000 * dt
        self.rpm = np.clip(self.rpm + rpm_change, 800, 8000)
        self.angle = (self.angle + (self.rpm / 60) * 360 * dt) % 720
        
        # Update physics
        self.temperature = 80 + (self.rpm / 8000) * 40 + random.uniform(-2, 2)
        self.pressure = 1.0 + (self.rpm / 8000) * 4.0
        
        # Update AI predictions
        self.predict_engine_health()
    
    def draw(self):
        self.screen.fill((20, 20, 30))
        
        # Draw engine diagram
        self._draw_engine()
        
        # Draw gauges
        self._draw_gauge(200, 600, 50, self.rpm, 0, 8000, (0, 200, 255), "RPM", "")
        self._draw_gauge(400, 600, 50, self.temperature, 60, 120, (255, 100, 100), "Temp", "°C")
        self._draw_gauge(600, 600, 50, self.pressure, 0, 5, (100, 255, 100), "Pressure", " bar")
        
        # Draw AI health prediction
        health = self.predict_engine_health()
        self._draw_health_bar(800, 600, 200, 30, health / 100, (100, 255, 100))
        
        pygame.display.flip()
    
    def _draw_engine(self):
        # Simplified engine visualization
        center_x, center_y = 300, 300
        angle_rad = math.radians(self.angle)
        
        # Draw cylinder
        pygame.draw.rect(self.screen, (100, 100, 100), (200, 100, 200, 400))
        
        # Draw piston
        piston_y = 150 + math.sin(angle_rad) * 100
        pygame.draw.rect(self.screen, (200, 50, 50), (220, piston_y - 25, 160, 50))
        
        # Draw connecting rod and crankshaft
        pygame.draw.line(self.screen, (0, 100, 200), 
                        (300, piston_y), 
                        (center_x + math.cos(angle_rad) * 80, center_y + math.sin(angle_rad) * 80), 5)
        
        pygame.draw.circle(self.screen, (200, 150, 0), (center_x, center_y), 30)
        
        # Draw spark effect
        if 350 < self.angle % 720 < 370:
            pygame.draw.circle(self.screen, (255, 255, 0), (300, 150), 10)
    
    def _draw_gauge(self, x, y, radius, value, min_val, max_val, color, label, unit):
        pygame.draw.circle(self.screen, (40, 40, 40), (x, y), radius + 5)
        pygame.draw.circle(self.screen, (30, 30, 30), (x, y), radius)
        
        start_angle = math.pi * 0.75
        end_angle = math.pi * 2.25
        value_angle = start_angle + (value - min_val) / (max_val - min_val) * (end_angle - start_angle)
        
        # Draw needle
        needle_x = x + math.cos(value_angle) * (radius * 0.8)
        needle_y = y - math.sin(value_angle) * (radius * 0.8)
        pygame.draw.line(self.screen, color, (x, y), (needle_x, needle_y), 3)
        
        # Draw label and value
        text = self.font.render(f"{label}: {value:.1f}{unit}", True, (255, 255, 255))
        self.screen.blit(text, (x - text.get_width() // 2, y + radius + 10))
    
    def _draw_health_bar(self, x, y, width, height, value, color):
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, width, height))
        pygame.draw.rect(self.screen, color, (x, y, int(width * value), height))
        text = self.font.render(f"AI Health: {value*100:.1f}%", True, (255, 255, 255))
        self.screen.blit(text, (x + 10, y + height // 2 - text.get_height() // 2))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.throttle = min(1.0, self.throttle + 0.1)
                elif event.key == pygame.K_DOWN:
                    self.throttle = max(0.0, self.throttle - 0.1)
    
    def run(self):
        last_time = pygame.time.get_ticks()
        while self.running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - last_time) / 1000.0
            last_time = current_time
            
            self.handle_events()
            self.update(dt)
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    simulator = EngineSimulator()
    simulator.run()
