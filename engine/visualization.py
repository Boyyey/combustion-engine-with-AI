"""
3D visualization of the engine using PyOpenGL.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *

@dataclass
class Color:
    r: float; g: float; b: float; a: float = 1.0

class EngineRenderer:
    """Handles 3D rendering of the engine."""
    
    def __init__(self, width: int = 1200, height: int = 800):
        # Initialize GLUT for OpenGL utilities
        import sys
        sys.argv = [sys.argv[0]]  # Clear any existing arguments
        from OpenGL.GLUT import glutInit
        glutInit()
        
        # Initialize display
        pygame.init()
        self.width = width
        self.height = height
        pygame.display.set_mode(
            (width, height), 
            DOUBLEBUF | OPENGL
        )
        pygame.display.set_caption("Advanced Engine Simulator")
        
        # Set up the 3D perspective
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Multiple light sources for better illumination
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (5, 5, 10, 1))  # Main light
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.9, 0.9, 1))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (1, 1, 1, 1))
        
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_POSITION, (-5, -5, 5, 1))  # Fill light
        glLightfv(GL_LIGHT1, GL_DIFFUSE, (0.5, 0.5, 0.5, 1))
        
        # Enable smooth shading
        glShadeModel(GL_SMOOTH)
        
        # Set a light gray background
        glClearColor(0.2, 0.2, 0.2, 1.0)
        
        # Camera settings
        self.camera_distance = 3.0  # Increased distance for better view
        self.camera_rot_x = 20     # Lower angle for better top-down view
        self.camera_rot_y = 35     # Slight angle for perspective
        
        # Materials with more distinct colors
        self.metal_material = {
            'ambient': (0.2, 0.2, 0.3, 1),      # Slightly blue tint
            'diffuse': (0.5, 0.5, 0.6, 1),      # Brighter for better visibility
            'specular': (0.9, 0.9, 0.9, 1),     # More reflective
            'shininess': 50.0,                  # Slightly less shiny
            'color': (0.5, 0.5, 0.6, 1)         # Base color
        }
        
        self.piston_material = {
            'ambient': (0.3, 0.1, 0.1, 1),      # Dark red
            'diffuse': (0.8, 0.2, 0.2, 1),      # Bright red
            'specular': (0.5, 0.5, 0.5, 1),
            'shininess': 30.0,
            'color': (0.8, 0.2, 0.2, 1)
        }
        
        self.valve_material = {
            'ambient': (0.1, 0.1, 0.1, 1),      # Dark gray
            'diffuse': (0.3, 0.3, 0.3, 1),
            'specular': (0.5, 0.5, 0.5, 1),
            'shininess': 10.0,
            'color': (0.3, 0.3, 0.3, 1)
        }
    
    def set_material(self, material):
        glMaterialfv(GL_FRONT, GL_AMBIENT, material['ambient'])
        glMaterialfv(GL_FRONT, GL_DIFFUSE, material['diffuse'])
        glMaterialfv(GL_FRONT, GL_SPECULAR, material['specular'])
        glMaterialf(GL_FRONT, GL_SHININESS, material['shininess'])
        glColor4fv(material.get('color', material['diffuse']))  # Set color for non-lit rendering
    
    def draw_cylinder(self, radius: float, height: float, slices: int = 32):
        """Draw a cylinder along the Z axis."""
        quad = gluNewQuadric()
        glPushMatrix()
        glRotatef(90, 1, 0, 0)
        gluCylinder(quad, radius, radius, height, slices, 1)
        glPopMatrix()
    
    def draw_piston(self, position: float, radius: float, height: float):
        """Draw a piston at the given position (0-1, 0=BDC, 1=TDC)."""
        glPushMatrix()
        # Position the piston (0=bottom, 1=top)
        z_pos = -0.8 + position * 1.6  # Adjusted range for better visibility
        glTranslatef(0, 0, z_pos)
        
        # Draw piston head (top)
        glPushMatrix()
        glScalef(radius, radius, 0.1)  # Flat top
        self.set_material(self.piston_material)
        self._draw_cube()
        glPopMatrix()
        
        # Draw piston skirt (sides)
        glPushMatrix()
        glTranslatef(0, 0, -0.2)  # Position below the head
        glScalef(radius * 0.9, radius * 0.9, 0.3)  # Slightly smaller than head
        self.set_material(self.metal_material)
        self._draw_cube()
        glPopMatrix()
        
        # Draw connecting rod
        glPushMatrix()
        glTranslatef(0, 0, -0.4)  # Position below the skirt
        glScalef(0.2, 0.2, 0.4)   # Thin rod
        self.set_material(self.valve_material)
        self._draw_cube()
        glPopMatrix()
        
        glPopMatrix()
    
    def draw_valve(self, lift: float, radius: float, is_exhaust: bool = False):
        """Draw a valve with the given lift."""
        if lift <= 0:
            return
            
        glPushMatrix()
        # Position the valve (intake on one side, exhaust on the other)
        x_pos = 0.2 if not is_exhaust else -0.2
        z_base = 0.7  # Base position at top of cylinder
        max_lift = 0.4  # Maximum valve lift
        
        # Draw valve stem
        glPushMatrix()
        glTranslatef(x_pos, 0, z_base - (lift * max_lift * 0.5))  # Move down based on lift
        glScalef(0.05, 0.05, lift * max_lift)  # Scale by lift amount
        self.set_material(self.valve_material)
        self._draw_cube()
        glPopMatrix()
        
        # Draw valve head
        glPushMatrix()
        glTranslatef(x_pos, 0, z_base - (lift * max_lift))  # At the end of the stem
        glScalef(0.15, 0.15, 0.05)  # Wider but flat head
        self.set_material(self.metal_material if not is_exhaust else self.piston_material)
        self._draw_cube()
        gluDisk(gluNewQuadric(), 0, radius, 16, 1)
        glPopMatrix()
        
        glPopMatrix()
    
    def render_engine(self, engine, throttle: float):
        """Render the entire engine."""
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Position camera
        glTranslatef(0, 0, -self.camera_distance)
        glRotatef(self.camera_rot_x, 1, 0, 0)
        glRotatef(self.camera_rot_y, 0, 1, 0)
        
        # Draw engine block (custom cube implementation)
        self.set_material(self.metal_material)
        glPushMatrix()
        glScalef(1.5, 0.8, 1.0)
        self._draw_cube()
        glPopMatrix()
        
        # Draw cylinders
        cylinder_spacing = 0.5
        for i, cyl in enumerate(engine.cylinders):
            glPushMatrix()
            x_pos = (i - (len(engine.cylinders)-1)/2) * cylinder_spacing
            glTranslatef(x_pos, 0, 0)
            
            # Draw cylinder
            glPushMatrix()
            glScalef(0.3, 0.3, 0.8)
            self.draw_cylinder(0.5, 1.0)
            glPopMatrix()
            
            # Draw piston
            piston_pos = (math.cos(math.radians(engine.angle * 2)) + 1) / 2
            self.draw_piston(piston_pos, 0.25, 0.6)
            
            # Draw valves
            self.draw_valve(cyl.intake.lift, 0.1, False)
            self.draw_valve(cyl.exhaust.lift, 0.1, True)
            
            glPopMatrix()
        
        # Draw crankshaft
        glPushMatrix()
        glRotatef(engine.angle, 0, 0, 1)
        glScalef(2.0, 0.1, 0.1)
        self._draw_cube()
        glPopMatrix()
        
        # Draw UI
        self._draw_hud(engine, throttle)
        
        pygame.display.flip()
    
    def _draw_hud(self, engine, throttle):
        """Draw the heads-up display."""
        # Switch to orthographic projection for 2D HUD
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Disable lighting for HUD
        glDisable(GL_LIGHTING)
        
        # Draw RPM gauge
        rpm_ratio = engine.rpm / 8000.0
        self._draw_gauge(100, 100, 80, rpm_ratio, (0, 1, 0, 1), f"{int(engine.rpm)} RPM")
        
        # Draw throttle indicator
        self._draw_gauge(220, 100, 60, throttle, (1, 0, 0, 1), f"Throttle: {int(throttle*100)}%")
        
        # Draw torque/power
        self._draw_text(350, 100, f"Torque: {engine.torque:.1f} Nm")
        self._draw_text(350, 130, f"Power: {engine.power:.1f} kW")
        
        # Restore 3D projection
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glEnable(GL_LIGHTING)
    
    def _draw_gauge(self, x, y, radius, value, color, label):
        """Draw a circular gauge."""
        glDisable(GL_DEPTH_TEST)
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(*color)
        glVertex2f(x, y)
        for i in range(33):
            angle = (i / 32) * np.pi * 2 * value - np.pi/2
            glVertex2f(x + np.cos(angle) * radius, y + np.sin(angle) * radius)
        glEnd()
        
        # Draw outline
        glBegin(GL_LINE_LOOP)
        glColor4f(1, 1, 1, 1)
        for i in range(33):
            angle = (i / 32) * np.pi * 2 - np.pi/2
            glVertex2f(x + np.cos(angle) * radius, y + np.sin(angle) * radius)
        glEnd()
        
        # Draw label
        self._draw_text(x - len(label)*3, y + radius + 10, label)
        glEnable(GL_DEPTH_TEST)
    
    def _draw_cube(self):
        """Draw a unit cube using immediate mode rendering."""
        # Define the 8 vertices of a cube
        vertices = [
            # Front face
            [-0.5, -0.5,  0.5], [0.5, -0.5,  0.5], [0.5,  0.5,  0.5], [-0.5,  0.5,  0.5],
            # Back face
            [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5,  0.5, -0.5], [-0.5,  0.5, -0.5]
        ]
        
        # Define the 6 faces (using 4 vertices each)
        faces = [
            [0, 1, 2, 3],  # Front
            [5, 4, 7, 6],  # Back
            [1, 5, 6, 2],  # Right
            [4, 0, 3, 7],  # Left
            [3, 2, 6, 7],  # Top
            [4, 5, 1, 0]   # Bottom
        ]
        
        # Draw the cube
        glBegin(GL_QUADS)
        for face in faces:
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        # Draw the edges in black
        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        for edge in [(0,1), (1,2), (2,3), (3,0),  # Front face
                    (4,5), (5,6), (6,7), (7,4),  # Back face
                    (0,4), (1,5), (2,6), (3,7)]:  # Connecting edges
            glVertex3fv(vertices[edge[0]])
            glVertex3fv(vertices[edge[1]])
        glEnd()
    
    def _draw_text(self, x, y, text):
        """Draw text at the given position."""
        glDisable(GL_DEPTH_TEST)
        font = pygame.font.Font(None, 24)
        text_surface = font.render(text, True, (255, 255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glRasterPos2f(x, y)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                    GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        glEnable(GL_DEPTH_TEST)
