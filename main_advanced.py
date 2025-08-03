"""Advanced Combustion Engine Simulator with AI Features"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from engine.mechanics import Engine
from engine.visualization import EngineRenderer

class EngineSimulator:
    def __init__(self):
        # Initialize Pygame and OpenGL
        pygame.init()
        self.width, self.height = 1280, 720
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Advanced Engine Simulator")
        
        # Setup OpenGL
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (self.width/self.height), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        
        # Initialize engine and renderer
        self.engine = Engine(cylinders=4, bore=0.086, stroke=0.086, cr=10.5)
        self.renderer = EngineRenderer()
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        
        # Initialize fonts
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 16)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    self.paused = not self.paused
                elif event.key == K_UP:
                    self.engine.throttle = min(1.0, self.engine.throttle + 0.05)
                elif event.key == K_DOWN:
                    self.engine.throttle = max(0.0, self.engine.throttle - 0.05)
    
    def update(self):
        if not self.paused:
            dt = self.clock.get_time() / 1000.0  # Convert to seconds
            self.engine.update(dt, self.engine.throttle)
    
    def render(self):
        # Clear screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Position camera
        glTranslatef(0.0, -0.5, -5.0)
        glRotatef(20, 1, 0, 0)
        glRotatef(pygame.time.get_ticks() * 0.01, 0, 1, 0)
        
        # Render engine
        self.renderer.render_engine(self.engine, self.engine.throttle)
        
        # Render UI
        self._render_ui()
        
        pygame.display.flip()
    
    def _render_ui(self):
        # Switch to orthographic projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Get surface for text rendering
        surface = pygame.display.get_surface()
        
        # Draw engine stats
        stats = [
            f"RPM: {self.engine.rpm:.0f}",
            f"Throttle: {self.engine.throttle*100:.0f}%",
            f"Power: {self.engine.power:.1f} kW",
            f"Torque: {self.engine.torque:.1f} Nm",
            "[SPACE] Pause/Resume",
            "[UP/DOWN] Adjust Throttle",
            "[ESC] Quit"
        ]
        
        for i, text in enumerate(stats):
            text_surface = self.font.render(text, True, (255, 255, 255))
            surface.blit(text_surface, (20, 20 + i * 25))
        
        # Restore 3D rendering
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    simulator = EngineSimulator()
    simulator.run()
