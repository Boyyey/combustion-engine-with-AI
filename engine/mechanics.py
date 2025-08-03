"""
Advanced mechanical components and dynamics of the engine.
Features:
- Realistic valve timing with temperature and wear modeling
- Advanced physics with mechanical losses
- Vibration analysis
- Temperature modeling
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum, auto
import time
from typing import Dict, List, Optional, Tuple
import random
from . import ai_engine

class ValveState(Enum):
    CLOSED = 0; OPENING = 1; OPEN = 2; CLOSING = 3

@dataclass
class Valve:
    lift: float = 0.0
    max_lift: float = 0.01
    diameter: float = 0.035
    open_angle: float = 340.0
    close_angle: float = 580.0
    state: ValveState = ValveState.CLOSED
    temperature: float = 300.0  # K
    wear: float = 0.0  # 0 (new) to 1 (failed)
    
    def update(self, angle: float, rpm: float, dt: float) -> None:
        cycle_angle = angle % 720
        
        # Update valve state and lift
        if self.open_angle <= cycle_angle < self.close_angle:
            pos = (cycle_angle - self.open_angle) / (self.close_angle - self.open_angle)
            self.lift = self.max_lift * np.sin(np.pi * pos) ** 2
            self.state = ValveState.OPENING if pos < 0.5 else ValveState.CLOSING
        else:
            self.lift = 0.0
            self.state = ValveState.CLOSED
        
        # Simulate temperature changes
        if self.state in (ValveState.OPEN, ValveState.OPENING):
            self.temperature += (1000 - self.temperature) * 0.01 * dt * (rpm / 1000)
        else:
            self.temperature -= (self.temperature - 300) * 0.005 * dt
        
        # Simulate wear (very slow degradation)
        if self.state != ValveState.CLOSED:
            self.wear += 1e-9 * rpm * dt
    
    @property
    def area(self) -> float:
        """Effective flow area considering lift and wear."""
        effective_lift = self.lift * (1.0 - self.wear * 0.5)
        return np.pi * self.diameter * effective_lift * 0.85 if effective_lift > 0 else 0.0

@dataclass
class Piston:
    position: float = 0.0  # 0 = TDC, 1 = BDC
    velocity: float = 0.0
    acceleration: float = 0.0
    temperature: float = 350.0  # K
    wear: float = 0.0
    
    def update(self, angle: float, rpm: float, dt: float) -> None:
        """Update piston position and dynamics."""
        theta = np.radians(angle)
        r = 0.5  # Crank radius / stroke ratio
        l = 1.75  # Rod length / stroke ratio
        
        # Kinematic equations for piston motion
        self.position = r * np.cos(theta) + np.sqrt(l**2 - (r * np.sin(theta))**2)
        self.velocity = -r * np.sin(theta) - (r**2 * np.sin(2*theta)) / (2 * np.sqrt(l**2 - (r * np.sin(theta))**2))
        self.acceleration = -r * np.cos(theta) - (r**2 * np.cos(2*theta) / np.sqrt(l**2 - (r * np.sin(theta))**2)) \
                          - (r**4 * np.sin(2*theta)**2) / (4 * (l**2 - (r * np.sin(theta))**2)**1.5)
        
        # Update temperature and wear
        self.temperature += (450 - self.temperature) * 0.001 * dt * (rpm / 1000)
        self.wear += 5e-10 * rpm * dt * (1.0 + self.acceleration**2)

class Cylinder:
    def __init__(self, bore: float, stroke: float, cr: float, cylinder_id: int):
        self.bore = bore
        self.stroke = stroke
        self.cr = cr
        self.cylinder_id = cylinder_id
        self.swept_vol = np.pi * (bore/2)**2 * stroke
        self.clearance_vol = self.swept_vol / (cr - 1)
        self.volume = self.clearance_vol + self.swept_vol
        
        # Valves with realistic timing
        self.intake = Valve(
            open_angle=340, 
            close_angle=580, 
            max_lift=0.01,
            diameter=0.035
        )
        self.exhaust = Valve(
            open_angle=140,  # Degrees before TDC (exhaust)
            close_angle=380,  # Degrees after TDC (intake)
            max_lift=0.01,
            diameter=0.03
        )
        
        # Piston
        self.piston = Piston()
        
        # Cylinder state
        self.pressure = 101325.0  # Pa
        self.temperature = 300.0  # K
        self.air_fuel_ratio = 14.7  # Stoichiometric
        self.combustion_efficiency = 0.95
        self.spark_timing = 15.0  # Degrees before TDC
        self.combustion_duration = 40.0  # Crank angle degrees
        self.combustion_progress = 0.0  # 0 to 1
        self.heat_loss = 0.0  # J
        self.vibration = np.zeros(100)  # Vibration spectrum
        
    def update_geometry(self, angle: float, rpm: float, dt: float) -> float:
        """Update cylinder geometry and return current volume."""
        # Update piston position
        self.piston.update(angle, rpm, dt)
        
        # Calculate current volume
        current_clearance = self.clearance_vol * (1.0 - self.piston.position)
        self.volume = self.clearance_vol + self.swept_vol * (1.0 - self.piston.position)
        
        # Update valves
        self.intake.update(angle, rpm, dt)
        self.exhaust.update(angle, rpm, dt)
        
        # Simulate vibration (simplified)
        self.vibration = np.roll(self.vibration, -1)
        vibration_magnitude = abs(self.piston.acceleration) * 0.1
        self.vibration[-1] = vibration_magnitude * (1.0 + 0.1 * np.random.normal())
        
        return self.volume
    
    def get_telemetry(self) -> dict:
        """Get current cylinder telemetry."""
        return {
            'pressure': self.pressure / 1e5,  # bar
            'temperature': self.temperature,
            'intake_valve_lift': self.intake.lift * 1000,  # mm
            'exhaust_valve_lift': self.exhaust.lift * 1000,  # mm
            'piston_position': self.piston.position * 100,  # % of stroke
            'piston_velocity': self.piston.velocity,
            'piston_acceleration': self.piston.acceleration,
            'vibration': np.max(self.vibration)
        }

class Engine:
    def __init__(self, cylinders: int = 4, bore: float = 0.086, 
                 stroke: float = 0.086, cr: float = 10.5):
        # Engine geometry
        self.bore = bore
        self.stroke = stroke
        self.cr = cr
        self.cylinders = [Cylinder(bore, stroke, cr, i) for i in range(cylinders)]
        self.firing_order = [0, 3, 1, 2]  # Typical 4-cylinder firing order
        
        # Engine state
        self.angle = 0.0  # Crank angle in degrees (0-720 for 4-stroke)
        self.rpm = 800.0  # Engine speed in RPM
        self.throttle = 0.3  # 0-1 throttle position
        self.load = 0.5  # 0-1 engine load
        self.torque = 0.0  # Nm
        self.power = 0.0  # kW
        self.efficiency = 0.3  # Thermal efficiency
        self.fuel_consumption = 0.0  # g/s
        
        # AI and telemetry
        self.ai_optimizer = ai_engine.AIPerformanceOptimizer()
        self.predictive_maintenance = ai_engine.PredictiveMaintenance()
        self.voice_control = ai_engine.VoiceControl()
        
        # Engine limits
        self.max_rpm = 8000
        self.min_rpm = 800
        
        # Timing
        self.last_update_time = time.time()
        self.running_time = 0.0  # seconds
    
    def update(self, dt: float, throttle: float = 0.5, load: float = 0.5) -> None:
        """Update engine state based on time step, throttle, and load."""
        # Update timing
        current_time = time.time()
        if self.last_update_time > 0:
            dt = current_time - self.last_update_time
        self.last_update_time = current_time
        self.running_time += dt
        
        # Update engine state
        self.throttle = max(0.0, min(1.0, throttle))
        self.load = max(0.0, min(1.0, load))
        
        # Update engine speed based on load and throttle
        self._update_rpm(dt)
        
        # Update engine angle (720° for complete 4-stroke cycle)
        angle_delta = (self.rpm / 60) * 360 * dt
        self.angle = (self.angle + angle_delta) % 720
        
        # Update each cylinder
        for i, cyl in enumerate(self.cylinders):
            # Calculate cylinder phase offset based on firing order
            firing_order_idx = self.firing_order.index(i) if i in self.firing_order else i
            offset = firing_order_idx * (720 / len(self.cylinders))
            cyl_angle = (self.angle + offset) % 720
            
            # Update cylinder geometry and physics
            cyl.update_geometry(cyl_angle, self.rpm, dt)
        
        # Calculate torque and power
        self._calculate_performance()
        
        # Update AI and telemetry
        self._update_telemetry()
    
    def _update_rpm(self, dt: float) -> None:
        """Update engine RPM based on throttle, load, and current state."""
        # Base acceleration based on throttle and load
        throttle_effect = self.throttle * 2.0 - 0.5  # -0.5 to 1.5
        load_effect = 1.0 - self.load * 0.8  # 0.2 to 1.0
        
        # Calculate RPM change
        rpm_delta = (throttle_effect * load_effect * 2000 - 
                    (self.rpm - self.min_rpm) * 0.1) * dt
        
        # Apply limits
        new_rpm = self.rpm + rpm_delta
        self.rpm = max(self.min_rpm, min(self.max_rpm, new_rpm))
    
    def _calculate_performance(self) -> None:
        """Calculate engine torque and power output."""
        # Base torque curve (simplified)
        rpm_norm = self.rpm / self.max_rpm
        torque_factor = 4 * rpm_norm * (1 - rpm_norm)  # Parabolic curve
        
        # Apply throttle and load effects
        self.torque = 200.0 * torque_factor * self.throttle * (1.0 - 0.3 * self.load)
        self.power = (self.torque * self.rpm) / 9549  # kW
        
        # Calculate fuel consumption (simplified)
        self.fuel_consumption = 0.1 * self.rpm * self.throttle / 3600  # g/s
    
    def _update_telemetry(self) -> None:
        """Update telemetry data and AI models."""
        # Create telemetry data point
        telemetry = ai_engine.EngineTelemetry(
            timestamp=time.time(),
            rpm=self.rpm,
            throttle=self.throttle,
            load=self.load,
            temperatures={
                'cylinder_head': 90.0 + 50.0 * (self.rpm / self.max_rpm),
                'oil': 80.0 + 30.0 * (self.rpm / self.max_rpm),
                'exhaust': 200.0 + 500.0 * (self.rpm / self.max_rpm)
            },
            pressures={
                'intake': 100.0 - 30.0 * (1.0 - self.throttle),
                'exhaust': 105.0 + 20.0 * (self.rpm / self.max_rpm),
                'oil': 100.0 + 400.0 * (self.rpm / self.max_rpm)
            },
            vibrations=np.random.randn(100) * (self.rpm / 1000),  # Simulated vibration data
            efficiency=0.25 + 0.15 * (self.rpm / self.max_rpm),
            fuel_consumption=self.fuel_consumption,
            emissions={'CO2': 200.0 * (self.rpm / self.max_rpm)}
        )
        
        # Update AI models
        self.ai_optimizer.update_telemetry(telemetry)
        
        # Get optimization recommendations
        recommendations = self.ai_optimizer.optimize()
        
        # Apply optimizations (simplified example)
        if 'rpm_adjustment' in recommendations:
            self.rpm += recommendations['rpm_adjustment'] * 10
            self.rpm = max(self.min_rpm, min(self.max_rpm, self.rpm))
    
    def process_voice_command(self, command: str) -> str:
        """Process a voice command and return a response."""
        return self.voice_control.process_command(command, self)
    
    def get_diagnostics(self) -> dict:
        """Get current engine diagnostics and health status."""
        return {
            'rpm': self.rpm,
            'throttle': self.throttle,
            'load': self.load,
            'torque': self.torque,
            'power': self.power,
            'efficiency': self.efficiency,
            'fuel_consumption': self.fuel_consumption,
            'running_time': self.running_time,
            'maintenance_status': self.predictive_maintenance.predict_failure(self.cylinders[0])
        }
