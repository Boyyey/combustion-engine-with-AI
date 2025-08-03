'''
Thermodynamic calculations for realistic engine simulation.
Implements real gas laws, heat transfer, and combustion modeling.
'''

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

# Physical constants
R = 8.31446261815324  # Universal gas constant [J/(mol·K)]
GAMMA = 1.4  # Specific heat ratio (cp/cv) for air
MOLAR_MASS_AIR = 0.02897  # kg/mol
R_SPECIFIC = R / MOLAR_MASS_AIR  # Specific gas constant for air [J/(kg·K)]

@dataclass
class GasState:
    """Represents the state of gas in the cylinder."""
    pressure: float  # [Pa]
    temperature: float  # [K]
    volume: float  # [m³]
    mass: float  # [kg]
    
    @property
    def density(self) -> float:
        return self.mass / self.volume if self.volume > 0 else 0.0
    
    @property
    def specific_volume(self) -> float:
        return self.volume / self.mass if self.mass > 0 else 0.0

class ThermodynamicSystem:
    """
    Models the thermodynamic processes in an engine cylinder.
    Implements the Otto cycle with realistic gas properties and heat transfer.
    """
    
    def __init__(self, initial_pressure: float = 1e5, initial_temperature: float = 300.0):
        self.gas = GasState(
            pressure=initial_pressure,
            temperature=initial_temperature,
            volume=0.0,
            mass=0.0
        )
        self.heat_added = 0.0
        self.work_done = 0.0
        self.heat_loss = 0.0
    
    def update_state(self, volume: float, heat_addition: float = 0.0, 
                    heat_loss: float = 0.0, isentropic: bool = False) -> None:
        """
        Update the gas state based on volume change and heat transfer.
        
        Args:
            volume: New volume [m³]
            heat_addition: Heat added to the system [J]
            heat_loss: Heat lost from the system [J]
            isentropic: If True, process is adiabatic and reversible
        """
        if isentropic:
            self._isentropic_process(volume)
        else:
            self._polytropic_process(volume, heat_addition, heat_loss)
    
    def _isentropic_process(self, new_volume: float) -> None:
        """Adiabatic reversible process (isentropic)."""
        if self.gas.volume <= 0 or new_volume <= 0:
            return
            
        # PV^γ = constant
        pressure_ratio = (self.gas.volume / new_volume) ** GAMMA
        self.gas.pressure *= pressure_ratio
        
        # TV^(γ-1) = constant
        temp_ratio = (self.gas.volume / new_volume) ** (GAMMA - 1)
        self.gas.temperature *= temp_ratio
        
        # Update volume
        self.gas.volume = new_volume
    
    def _polytropic_process(self, new_volume: float, heat_addition: float, 
                           heat_loss: float) -> None:
        """Polytropic process with heat transfer."""
        if self.gas.volume <= 0 or new_volume <= 0:
            return
            
        # Calculate work done (assuming polytropic process)
        if abs(new_volume - self.gas.volume) > 1e-10:  # Avoid division by zero
            # Polytropic exponent (n) - simplified model
            n = 1.3  # Typical value for compression/expansion in engines
            
            # Work done during polytropic process
            if abs(n - 1.0) > 1e-6:  # n ≠ 1
                work = (self.gas.pressure * self.gas.volume - 
                       self.gas.pressure * self.gas.volume * 
                       (self.gas.volume / new_volume) ** (n - 1)) / (n - 1)
            else:  # n = 1 (isothermal)
                work = self.gas.pressure * self.gas.volume * np.log(new_volume / self.gas.volume)
            
            # Update internal energy (1st law of thermodynamics)
            delta_u = heat_addition - heat_loss - work
            
            # Update temperature (assuming ideal gas)
            cv = R_SPECIFIC / (GAMMA - 1)  # Specific heat at constant volume
            delta_t = delta_u / (self.gas.mass * cv) if self.gas.mass > 0 else 0
            self.gas.temperature += delta_t
            
            # Update pressure using ideal gas law
            if self.gas.volume > 0:
                pressure_ratio = (self.gas.volume / new_volume) ** n
                self.gas.pressure *= pressure_ratio
            
            # Update volume and energy terms
            self.gas.volume = new_volume
            self.work_done += work
            self.heat_added += heat_addition
            self.heat_loss += heat_loss
    
    def reset_cycle(self) -> None:
        """Reset energy tracking for a new cycle."""
        self.heat_added = 0.0
        self.work_done = 0.0
        self.heat_loss = 0.0

class CombustionModel:
    """
    Models the combustion process in the cylinder.
    Implements Wiebe function for heat release and flame propagation.
    """
    
    def __init__(self, efficiency: float = 0.9, combustion_duration: float = 40.0):
        """
        Args:
            efficiency: Combustion efficiency (0-1)
            combustion_duration: Duration of combustion in crank angle degrees
        """
        self.efficiency = efficiency
        self.combustion_duration = combustion_duration
        self.wiebe_constants = (5.0, 2.0)  # a, n Wiebe function parameters
    
    def heat_release_rate(self, theta: float, theta_start: float, 
                         total_heat: float) -> float:
        """
        Calculate heat release rate using Wiebe function.
        
        Args:
            theta: Current crank angle [deg]
            theta_start: Start of combustion [deg]
            total_heat: Total heat to be released [J]
            
        Returns:
            Heat release rate [J/deg]
        """
        if theta < theta_start or theta > theta_start + self.combustion_duration:
            return 0.0
            
        # Normalized crank angle (0 to 1)
        x = (theta - theta_start) / self.combustion_duration
        
        # Wiebe function for mass fraction burned
        a, n = self.wiebe_constants
        mfb = 1.0 - np.exp(-a * x ** n)
        
        # Heat release rate (derivative of mfb)
        if 0 < x < 1:
            dmfb_dx = a * n * (x ** (n - 1)) * np.exp(-a * x ** n)
            dq_dtheta = total_heat * dmfb_dx / self.combustion_duration
            return dq_dtheta * self.efficiency
        return 0.0

class HeatTransferModel:
    """
    Models heat transfer in the engine cylinder.
    Implements Woschni correlation for convective heat transfer.
    """
    
    def __init__(self, bore: float, stroke: float, compression_ratio: float):
        """
        Args:
            bore: Cylinder bore [m]
            stroke: Piston stroke [m]
            compression_ratio: Engine compression ratio
        """
        self.bore = bore
        self.stroke = stroke
        self.compression_ratio = compression_ratio
        self.cylinder_area = np.pi * bore * stroke / 2  # Approximate
        
        # Material properties
        self.wall_temperature = 400.0  # K (simplified constant wall temp)
        self.thermal_conductivity = 0.1  # W/(m·K) - simplified
    
    def calculate_heat_loss(self, gas: GasState, engine_speed: float, 
                           crank_angle: float) -> float:
        """
        Calculate heat loss using Woschni correlation.
        
        Args:
            gas: Current gas state
            engine_speed: Engine speed [RPM]
            crank_angle: Current crank angle [deg]
            
        Returns:
            Heat loss rate [J/deg]
        """
        # Mean piston speed [m/s]
        s_p = 2 * self.stroke * engine_speed / 60.0
        
        # Characteristic velocity [m/s]
        c1 = 2.28  # Coefficient for gas exchange
        c2 = 0.00324  # Coefficient for compression/expansion
        
        # Calculate instantaneous cylinder volume and height
        v_d = np.pi * (self.bore ** 2) * self.stroke / 4  # Displacement volume
        v_c = v_d / (self.compression_ratio - 1)  # Clearance volume
        
        # Instantaneous volume and height
        theta_rad = np.radians(crank_angle)
        v = v_c + (v_d / 2) * (1 - np.cos(theta_rad) + 
                              (1/np.sqrt(1 - 0.25)) * (1 - np.cos(2*theta_rad)))
        
        # Woschni velocity [m/s]
        w = c1 * s_p + c2 * v_d * gas.temperature / (v * 1e5)  # P_ref = 1 bar
        
        # Heat transfer coefficient [W/(m²·K)]
        h = 3.26 * (gas.pressure/1e5) ** 0.8 * w ** 0.8 * self.bore ** -0.2 * gas.temperature ** -0.55
        
        # Heat transfer rate [J/deg]
        q = h * self.cylinder_area * (gas.temperature - self.wall_temperature)
        
        # Convert to J/deg (engine cycle basis)
        return q * (np.pi/180) * (60 / engine_speed) if engine_speed > 0 else 0.0
