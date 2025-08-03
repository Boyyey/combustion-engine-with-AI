"""Advanced Engine Visualization with PBR and Effects"""

from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math
from dataclasses import dataclass

@dataclass
class Material:
    """PBR material properties"""
    color: tuple
    metallic: float = 0.0
    roughness: float = 0.5
    
    def apply(self):
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (*self.color, 1.0))
        glMaterialfv(GL_FRONT, GL_SPECULAR, (0.5, 0.5, 0.5, 1.0))
        glMaterialf(GL_FRONT, GL_SHININESS, 100 * (1 - self.roughness))

class AdvancedEngineRenderer:
    def __init__(self):
        self.materials = {
            'aluminum': Material((0.9, 0.9, 0.92), 0.8, 0.2),
            'steel': Material((0.7, 0.7, 0.7), 0.9, 0.1),
            'piston': Material((0.8, 0.2, 0.1), 0.7, 0.3),
            'valve': Material((0.9, 0.9, 0.95), 0.9, 0.1),
            'rubber': Material((0.1, 0.1, 0.1), 0.0, 0.9)
        }
        self._init_rendering()
    
    def _init_rendering(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_NORMALIZE)
        
        # Configure lighting
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.1, 0.1, 0.1, 1.0))
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 10.0, 5.0, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.9, 0.9, 1.0))
    
    def render_engine(self, engine, throttle):
        glPushMatrix()
        
        # Draw engine block
        self.materials['aluminum'].apply()
        self._draw_engine_block()
        
        # Draw cylinders
        for i in range(engine.cylinders):
            glPushMatrix()
            glTranslatef((i - 1.5) * 0.2, 0, 0)
            self._draw_cylinder(engine, i, throttle)
            glPopMatrix()
        
        glPopMatrix()
    
    def _draw_engine_block(self):
        # Main block
        glPushMatrix()
        glScalef(1.2, 0.6, 0.6)
        self._draw_cube()
        glPopMatrix()
        
        # Cylinder head
        glPushMatrix()
        glTranslatef(0, 0.3, 0)
        glScalef(1.2, 0.2, 0.6)
        self._draw_cube()
        glPopMatrix()
    
    def _draw_cylinder(self, engine, cylinder_idx, throttle):
        cylinder = engine.get_cylinder(cylinder_idx)
        
        # Draw cylinder wall
        glPushMatrix()
        glRotatef(90, 1, 0, 0)
        self._draw_cylinder_mesh(engine.bore/2, 0.5, 32)
        glPopMatrix()
        
        # Draw piston
        self.materials['piston'].apply()
        piston_pos = math.sin(math.radians(engine.crank_angle)) * 0.1
        
        glPushMatrix()
        glTranslatef(0, 0.2 - piston_pos, 0)
        self._draw_piston(engine.bore)
        glPopMatrix()
        
        # Draw valves
        self.materials['valve'].apply()
        self._draw_valves(cylinder)
    
    def _draw_piston(self, bore):
        glPushMatrix()
        glScalef(0.9, 0.8, 0.9)
        glPushMatrix()
        glRotatef(90, 1, 0, 0)
        self._draw_cylinder_mesh(bore/2 * 0.9, 0.1, 16)
        glPopMatrix()
        glPopMatrix()
    
    def _draw_valves(self, cylinder):
        valve_angle = 20
        valve_offset = 0.1
        
        # Intake valve
        if cylinder.intake_valve.state.name != 'CLOSED':
            glPushMatrix()
            glRotatef(valve_angle, 0, 0, 1)
            glTranslatef(0, valve_offset, 0)
            glRotatef(90, 1, 0, 0)
            self._draw_cylinder_mesh(0.02, 0.15, 12)
            glPopMatrix()
        
        # Exhaust valve
        if cylinder.exhaust_valve.state.name != 'CLOSED':
            glPushMatrix()
            glRotatef(-valve_angle, 0, 0, 1)
            glTranslatef(0, valve_offset, 0)
            glRotatef(90, 1, 0, 0)
            self._draw_cylinder_mesh(0.02, 0.15, 12)
            glPopMatrix()
    
    def _draw_cylinder_mesh(self, radius, height, slices):
        quad = gluNewQuadric()
        gluCylinder(quad, radius, radius, height, slices, 1)
        gluDeleteQuadric(quad)
    
    def _draw_cube(self):
        glBegin(GL_QUADS)
        # Front
        glNormal3f(0, 0, 1)
        glVertex3f(-0.5, -0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        # Back
        glNormal3f(0, 0, -1)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        # Top
        glNormal3f(0, 1, 0)
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(0.5, 0.5, -0.5)
        # Bottom
        glNormal3f(0, -1, 0)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(-0.5, -0.5, 0.5)
        # Left
        glNormal3f(-1, 0, 0)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5, -0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, -0.5)
        # Right
        glNormal3f(1, 0, 0)
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glEnd()
