"""
AI-powered engine analysis and optimization module.
Implements machine learning models for predictive maintenance, performance optimization,
and real-time engine health monitoring.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time
from datetime import datetime
import json
import os

@dataclass
class EngineTelemetry:
    """Stores real-time telemetry data from the engine."""
    timestamp: float
    rpm: float
    throttle: float
    load: float
    temperatures: Dict[str, float]  # cylinder_head, oil, coolant, etc.
    pressures: Dict[str, float]     # intake, exhaust, oil, etc.
    vibrations: np.ndarray          # Vibration spectrum
    efficiency: float
    fuel_consumption: float
    emissions: Dict[str, float]     # CO2, NOx, HC, etc.
    
    def to_dict(self) -> dict:
        """Convert telemetry data to a dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp,
            'rpm': self.rpm,
            'throttle': self.throttle,
            'load': self.load,
            'temperatures': self.temperatures,
            'pressures': self.pressures,
            'vibrations': self.vibrations.tolist(),
            'efficiency': self.efficiency,
            'fuel_consumption': self.fuel_consumption,
            'emissions': self.emissions
        }

class AIPerformanceOptimizer:
    """Uses machine learning to optimize engine performance in real-time."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.telemetry_history: List[EngineTelemetry] = []
        self.max_history_size = 1000  # Store last 1000 data points
        self.last_optimization_time = 0
        self.optimization_interval = 5.0  # seconds
        
        # Initialize with default model or load from file
        self.model = self._initialize_model(model_path)
        
    def _initialize_model(self, model_path: Optional[str] = None):
        """Initialize the ML model for performance optimization."""
        # In a real implementation, this would load a pre-trained model
        # For now, we'll use a simple rule-based approach
        return {
            'optimal_rpm_range': (1500, 4500),
            'max_safe_temperature': 380.0,  # K
            'efficiency_lookup': self._create_efficiency_lookup()
        }
    
    def _create_efficiency_lookup(self) -> np.ndarray:
        """Create a 2D lookup table for efficiency based on RPM and load."""
        # This would be replaced with actual ML model predictions
        rpm_range = np.linspace(800, 8000, 20)
        load_range = np.linspace(0.1, 1.0, 10)
        efficiency = np.zeros((len(rpm_range), len(load_range)))
        
        # Create a simple efficiency map (peak efficiency around 3000-4000 RPM, 70-80% load)
        for i, rpm in enumerate(rpm_range):
            for j, load in enumerate(load_range):
                # Base efficiency curve (Gaussian-like)
                rpm_eff = np.exp(-((rpm - 3500) / 2000) ** 2)
                load_eff = np.exp(-((load - 0.75) / 0.3) ** 2)
                efficiency[i, j] = 0.25 + 0.5 * (rpm_eff + load_eff) / 2
                
        return efficiency
    
    def update_telemetry(self, telemetry: EngineTelemetry) -> None:
        """Update the optimizer with new telemetry data."""
        self.telemetry_history.append(telemetry)
        if len(self.telemetry_history) > self.max_history_size:
            self.telemetry_history.pop(0)
    
    def optimize(self) -> Dict[str, float]:
        """Generate optimization recommendations."""
        current_time = time.time()
        if current_time - self.last_optimization_time < self.optimization_interval:
            return {}
            
        self.last_optimization_time = current_time
        
        if not self.telemetry_history:
            return {}
            
        # Get the most recent telemetry
        current = self.telemetry_history[-1]
        
        # Simple optimization logic (would be replaced with ML model)
        recommendations = {}
        
        # Check RPM range
        if current.rpm < self.model['optimal_rpm_range'][0]:
            recommendations['rpm_adjustment'] = 1.0  # Increase throttle
        elif current.rpm > self.model['optimal_rpm_range'][1]:
            recommendations['rpm_adjustment'] = -1.0  # Decrease throttle
        
        # Check temperatures
        for sensor, temp in current.temperatures.items():
            if temp > self.model['max_safe_temperature'] * 0.9:  # 90% of max temp
                recommendations[f'cooling_required_{sensor}'] = True
        
        return recommendations

class PredictiveMaintenance:
    """Predicts maintenance needs and potential failures."""
    
    def __init__(self):
        self.vibration_baseline = None
        self.wear_rates = {}
        self.failure_modes = self._initialize_failure_modes()
        
    def _initialize_failure_modes(self) -> Dict:
        """Initialize known failure modes and their signatures."""
        return {
            'bearing_wear': {
                'vibration_freqs': [1000, 2000, 3000],  # Hz
                'temperature_sensitivity': 1.2,
                'progression_rate': 0.01
            },
            'piston_ring_wear': {
                'compression_loss': 0.05,  # % per 100 hours
                'oil_consumption_increase': 0.1  # % per 100 hours
            }
        }
    
    def analyze_vibrations(self, vibration_spectrum: np.ndarray) -> Dict[str, float]:
        """Analyze vibration spectrum for signs of mechanical issues."""
        if self.vibration_baseline is None:
            self.vibration_baseline = vibration_spectrum
            return {}
            
        # Calculate deviation from baseline
        deviation = np.abs(vibration_spectrum - self.vibration_baseline)
        
        # Check for specific frequency patterns that indicate issues
        issues = {}
        
        # Check for bearing wear (increased high-frequency vibrations)
        high_freq_energy = np.sum(deviation[100:])
        if high_freq_energy > np.mean(devision) * 3:
            issues['possible_bearing_wear'] = high_freq_energy
            
        return issues
    
    def predict_failure(self, telemetry: EngineTelemetry) -> Dict:
        """Predict potential failures based on current conditions."""
        predictions = {}
        
        # Check for overheating
        if any(temp > 380.0 for temp in telemetry.temperatures.values()):
            predictions['overheating_risk'] = 'high'
            
        # Check for oil pressure issues
        if telemetry.pressures.get('oil', 0) < 100:  # kPa
            predictions['low_oil_pressure'] = 'critical'
            
        # Analyze vibration patterns
        vibration_issues = self.analyze_vibrations(telemetry.vibrations)
        predictions.update(vibration_issues)
        
        return predictions

class VoiceControl:
    """Handles voice commands for the engine simulation."""
    
    def __init__(self):
        self.commands = {
            'increase rpm': self._increase_rpm,
            'decrease rpm': self._decrease_rpm,
            'set rpm': self._set_rpm,
            'status': self._get_status,
            'optimize': self._optimize_engine,
            'emergency stop': self._emergency_stop
        }
        
    def process_command(self, command: str, engine) -> str:
        """Process a voice command and return a response."""
        command = command.lower().strip()
        
        # Find the best matching command
        for cmd, handler in self.commands.items():
            if cmd in command:
                return handler(engine, command)
                
        return "Command not recognized. Try 'increase rpm', 'decrease rpm', or 'status'."
    
    def _increase_rpm(self, engine, command: str) -> str:
        """Handle increase RPM command."""
        try:
            # Try to extract a number from the command
            words = command.split()
            for i, word in enumerate(words):
                if word.isdigit():
                    amount = int(word)
                    engine.rpm = min(engine.max_rpm, engine.rpm + amount)
                    return f"Increased RPM by {amount} to {engine.rpm} RPM"
            
            # No number specified, use default increment
            engine.rpm = min(engine.max_rpm, engine.rpm + 100)
            return f"Increased RPM to {engine.rpm} RPM"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _decrease_rpm(self, engine, command: str) -> str:
        """Handle decrease RPM command."""
        try:
            # Try to extract a number from the command
            words = command.split()
            for i, word in enumerate(words):
                if word.isdigit():
                    amount = int(word)
                    engine.rpm = max(engine.min_rpm, engine.rpm - amount)
                    return f"Decreased RPM by {amount} to {engine.rpm} RPM"
            
            # No number specified, use default decrement
            engine.rpm = max(engine.min_rpm, engine.rpm - 100)
            return f"Decreased RPM to {engine.rpm} RPM"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _set_rpm(self, engine, command: str) -> str:
        """Handle set RPM command."""
        try:
            # Extract the target RPM
            words = command.split()
            for word in words:
                if word.isdigit():
                    target_rpm = int(word)
                    target_rpm = max(engine.min_rpm, min(engine.max_rpm, target_rpm))
                    engine.rpm = target_rpm
                    return f"Set RPM to {target_rpm}"
            
            return "Please specify a target RPM"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_status(self, engine, command: str) -> str:
        """Return engine status."""
        return (
            f"Engine status: {engine.rpm} RPM, "
            f"Throttle: {engine.throttle*100:.1f}%, "
            f"Load: {engine.load*100:.1f}%"
        )
    
    def _optimize_engine(self, engine, command: str) -> str:
        """Optimize engine performance."""
        # This would trigger the optimization routine
        return "Optimization in progress..."
    
    def _emergency_stop(self, engine, command: str) -> str:
        """Perform an emergency stop."""
        engine.rpm = 0
        engine.throttle = 0
        return "EMERGENCY STOP ACTIVATED"
