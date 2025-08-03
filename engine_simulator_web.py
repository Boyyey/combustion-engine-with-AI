"""Combustion Engine Simulator Web Interface

A Streamlit-based web application for simulating and analyzing combustion engine performance.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from engine.mechanics import Engine
from engine.thermodynamics import GasState, ThermodynamicSystem, CombustionModel, HeatTransferModel
import time

# Page configuration
st.set_page_config(
    page_title="Combustion Engine Simulator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        max-width: 1200px;
        padding: 2rem;
    }
    .metric-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    .stSlider>div>div>div>div {
        background-color: #4a90e2;
    }
</style>
""", unsafe_allow_html=True)

class EngineSimulatorApp:
    def __init__(self):
        self.engine = None
        self.simulation_data = []
        self.simulation_running = False
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'engine_params' not in st.session_state:
            st.session_state.engine_params = {
                'cylinders': 4,
                'bore': 86,  # mm
                'stroke': 86,  # mm
                'compression_ratio': 10.5,
                'max_rpm': 8000
            }
        
        if 'simulation_params' not in st.session_state:
            st.session_state.simulation_params = {
                'throttle': 0.5,
                'load': 0.5,
                'duration': 10,  # seconds
                'time_step': 0.1  # seconds
            }
    
    def create_engine(self):
        """Initialize engine and thermodynamic models"""
        params = st.session_state.engine_params
        
        try:
            # Initialize engine with required parameters only
            self.engine = Engine(
                cylinders=params['cylinders'],
                bore=params['bore'] / 1000,  # Convert to meters
                stroke=params['stroke'] / 1000,  # Convert to meters
                cr=params['compression_ratio']
            )
            
            # Set max_rpm as an attribute after initialization
            self.engine.max_rpm = params['max_rpm']
            
            # Initialize thermodynamic models
            self.thermo_system = ThermodynamicSystem()
            self.combustion_model = CombustionModel()
            self.heat_transfer_model = HeatTransferModel(
                bore=params['bore'] / 1000,
                stroke=params['stroke'] / 1000,
                compression_ratio=params['compression_ratio']
            )
            return True
            
        except Exception as e:
            st.error(f"Error initializing engine: {str(e)}")
            st.exception(e)  # Show full traceback in the UI for debugging
            return False
    
    def run_simulation(self):
        """Run engine simulation with current parameters"""
        if not self.create_engine():
            return
        
        params = st.session_state.simulation_params
        self.simulation_data = []
        current_time = 0
        
        # Initialize UI elements
        progress_bar = st.progress(0)
        status_text = st.empty()
        chart_placeholder = st.empty()
        
        try:
            # Run simulation loop
            while current_time <= params['duration']:
                try:
                    # Update engine state
                    self.engine.update(
                        dt=params['time_step'],
                        throttle=params['throttle'] / 100.0,  # Convert percentage to 0-1
                        load=params['load'] / 100.0  # Convert percentage to 0-1
                    )
                    
                    # Record data
                    self.record_snapshot(current_time)
                    
                    # Update progress
                    progress = min(1.0, current_time / params['duration'])
                    progress_bar.progress(progress)
                    status_text.text(f"Simulation progress: {progress*100:.1f}%")
                    
                    # Update charts periodically for better performance
                    if len(self.simulation_data) % 5 == 0:
                        self.update_charts(chart_placeholder)
                    
                    # Increment time
                    current_time += params['time_step']
                    
                    # Small delay to prevent UI freeze
                    time.sleep(0.02)
                    
                except Exception as e:
                    st.error(f"Error during simulation: {str(e)}")
                    st.exception(e)
                    break
            
            # Final chart update
            self.update_charts(chart_placeholder)
            st.success("Simulation completed successfully!")
            
        except Exception as e:
            st.error(f"Fatal error in simulation: {str(e)}")
            st.exception(e)
        
        finally:
            # Clean up
            progress_bar.empty()
            status_text.empty()
    
    def record_snapshot(self, current_time):
        """Record current engine state with comprehensive metrics"""
        try:
            # Get basic engine metrics
            snapshot = {
                'time': current_time,
                'rpm': self.engine.rpm,
                'throttle': self.engine.throttle * 100,  # as percentage
                'load': self.engine.load * 100,  # as percentage
                'power': self.engine.power,
                'torque': self.engine.torque,
                'efficiency': self.engine.efficiency * 100,  # as percentage
            }
            
            # Add cylinder-specific metrics if available
            if hasattr(self.engine, 'cylinders') and self.engine.cylinders:
                # Use first cylinder as representative for now
                cyl = self.engine.cylinders[0]
                snapshot.update({
                    'intake_valve_lift': getattr(cyl, 'intake', None) and cyl.intake.lift or 0,
                    'exhaust_valve_lift': getattr(cyl, 'exhaust', None) and cyl.exhaust.lift or 0,
                    'piston_position': getattr(cyl, 'piston', None) and cyl.piston.position or 0,
                    'cylinder_pressure': getattr(cyl, 'pressure', 0) / 1000,  # kPa
                    'cylinder_temp': getattr(cyl, 'temperature', 0) - 273.15,  # °C
                })
            
            # Add thermodynamic metrics if available
            if hasattr(self, 'thermo_system') and self.thermo_system:
                snapshot.update({
                    'heat_added': getattr(self.thermo_system, 'heat_added', 0),
                    'work_done': getattr(self.thermo_system, 'work_done', 0),
                    'heat_loss': getattr(self.thermo_system, 'heat_loss', 0),
                })
            
            self.simulation_data.append(snapshot)
            
        except Exception as e:
            st.warning(f"Warning: Could not record all metrics: {str(e)}")
            # If we can't get all metrics, at least save the basic ones
            minimal_snapshot = {
                'time': current_time,
                'rpm': getattr(self.engine, 'rpm', 0),
                'throttle': getattr(self.engine, 'throttle', 0) * 100,
                'load': getattr(self.engine, 'load', 0) * 100,
                'power': getattr(self.engine, 'power', 0),
                'torque': getattr(self.engine, 'torque', 0),
            }
            self.simulation_data.append(minimal_snapshot)
    
    def update_charts(self, placeholder):
        """Update the main performance charts with comprehensive engine metrics"""
        if not self.simulation_data:
            return
        
        df = pd.DataFrame(self.simulation_data)
        
        # Create tabs for different chart groups
        tab1, tab2, tab3 = st.tabs(["Performance", "Engine Dynamics", "Thermodynamics"])
        
        with tab1:
            # Performance metrics
            col1, col2 = st.columns(2)
            
            with col1:
                # RPM vs Time
                fig1 = px.line(
                    df, x='time', y='rpm',
                    title='Engine RPM vs Time',
                    labels={'rpm': 'RPM', 'time': 'Time (s)'},
                    template='plotly_dark'
                )
                fig1.update_layout(showlegend=False)
                st.plotly_chart(fig1, use_container_width=True, key=f"rpm_chart_{len(self.simulation_data)}")
                
                # Power and Torque
                fig2 = px.line(
                    df, x='time', y=['power', 'torque'],
                    title='Power & Torque vs Time',
                    labels={'value': 'Value', 'variable': 'Metric', 'time': 'Time (s)'},
                    template='plotly_dark'
                )
                st.plotly_chart(fig2, use_container_width=True, key=f"power_torque_chart_{len(self.simulation_data)}")
            
            with col2:
                # Efficiency
                fig3 = px.line(
                    df, x='time', y='efficiency',
                    title='Thermal Efficiency vs Time',
                    labels={'efficiency': 'Efficiency (%)', 'time': 'Time (s)'},
                    template='plotly_dark'
                )
                fig3.update_layout(showlegend=False)
                st.plotly_chart(fig3, use_container_width=True, key=f"efficiency_chart_{len(self.simulation_data)}")
                
                # Throttle and Load
                fig4 = px.line(
                    df, x='time', y=['throttle', 'load'],
                    title='Throttle & Load vs Time',
                    labels={'value': 'Percentage (%)', 'variable': 'Control', 'time': 'Time (s)'},
                    template='plotly_dark'
                )
                st.plotly_chart(fig4, use_container_width=True, key=f"controls_chart_{len(self.simulation_data)}")
        
        with tab2:
            # Engine dynamics
            col1, col2 = st.columns(2)
            
            with col1:
                # Valve lifts
                if 'intake_valve_lift' in df.columns and 'exhaust_valve_lift' in df.columns:
                    fig5 = px.line(
                        df, x='time', y=['intake_valve_lift', 'exhaust_valve_lift'],
                        title='Valve Lifts vs Time',
                        labels={'value': 'Lift (m)', 'variable': 'Valve', 'time': 'Time (s)'},
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig5, use_container_width=True, key=f"valve_lift_chart_{len(self.simulation_data)}")
                
                # Piston position
                if 'piston_position' in df.columns:
                    fig6 = px.line(
                        df, x='time', y='piston_position',
                        title='Piston Position vs Time',
                        labels={'piston_position': 'Position (m)', 'time': 'Time (s)'},
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig6, use_container_width=True, key=f"piston_chart_{len(self.simulation_data)}")
            
            with col2:
                # Phase plot: Power vs RPM
                if not df.empty and 'power' in df.columns and 'rpm' in df.columns:
                    fig7 = px.scatter(
                        df, x='rpm', y='power',
                        title='Power vs RPM',
                        labels={'power': 'Power (kW)', 'rpm': 'RPM'},
                        template='plotly_dark',
                        trendline='lowess'
                    )
                    st.plotly_chart(fig7, use_container_width=True, key=f"power_rpm_chart_{len(self.simulation_data)}")
        
        with tab3:
            # Thermodynamics
            col1, col2 = st.columns(2)
            
            with col1:
                # Cylinder pressure and temperature
                if 'cylinder_pressure' in df.columns:
                    fig8 = px.line(
                        df, x='time', y='cylinder_pressure',
                        title='Cylinder Pressure vs Time',
                        labels={'cylinder_pressure': 'Pressure (kPa)', 'time': 'Time (s)'},
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig8, use_container_width=True, key=f"pressure_chart_{len(self.simulation_data)}")
                
                if 'cylinder_temp' in df.columns:
                    fig9 = px.line(
                        df, x='time', y='cylinder_temp',
                        title='Cylinder Temperature vs Time',
                        labels={'cylinder_temp': 'Temperature (°C)', 'time': 'Time (s)'},
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig9, use_container_width=True, key=f"temp_chart_{len(self.simulation_data)}")
            
            with col2:
                # Energy balance
                if all(k in df.columns for k in ['heat_added', 'work_done', 'heat_loss']):
                    energy_df = df[['time', 'heat_added', 'work_done', 'heat_loss']].copy()
                    energy_df = energy_df.melt(id_vars='time', var_name='Energy', value_name='Value')
                    
                    fig10 = px.area(
                        energy_df, x='time', y='Value', color='Energy',
                        title='Energy Balance Over Time',
                        labels={'Value': 'Energy (J)', 'time': 'Time (s)'},
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig10, use_container_width=True, key=f"energy_chart_{len(self.simulation_data)}")
        
        # Show data summary
        with st.expander("View Simulation Data"):
            st.dataframe(df.tail(10), use_container_width=True)
            
            # Add download button for data
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Simulation Data (CSV)",
                data=csv,
                file_name=f"engine_simulation_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv',
            )
    
    def render_sidebar(self):
        """Render the sidebar controls"""
        with st.sidebar:
            st.title("⚙️ Engine Parameters")
            
            # Engine configuration
            st.subheader("Engine Configuration")
            st.number_input(
                "Number of Cylinders",
                min_value=1, max_value=12, step=1,
                key="engine_params.cylinders"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.number_input(
                    "Bore (mm)",
                    min_value=50, max_value=120, step=1,
                    key="engine_params.bore"
                )
            with col2:
                st.number_input(
                    "Stroke (mm)",
                    min_value=50, max_value=120, step=1,
                    key="engine_params.stroke"
                )
            
            st.slider(
                "Compression Ratio",
                min_value=8.0, max_value=15.0, step=0.5,
                key="engine_params.compression_ratio"
            )
            
            st.slider(
                "Max RPM",
                min_value=3000, max_value=12000, step=100,
                key="engine_params.max_rpm"
            )
            
            # Simulation parameters
            st.subheader("Simulation Parameters")
            st.slider(
                "Throttle Position (%)",
                min_value=0, max_value=100, step=5,
                key="simulation_params.throttle"
            )
            
            st.slider(
                "Engine Load (%)",
                min_value=0, max_value=100, step=5,
                key="simulation_params.load"
            )
            
            st.number_input(
                "Simulation Duration (s)",
                min_value=1, max_value=60, step=1,
                key="simulation_params.duration"
            )
            
            st.number_input(
                "Time Step (s)",
                min_value=0.01, max_value=1.0, step=0.01,
                key="simulation_params.time_step"
            )
            
            # Action buttons
            if st.button("🚀 Run Simulation", type="primary"):
                with st.spinner("Running simulation..."):
                    self.run_simulation()
            
            if st.button("🔄 Reset"):
                self.initialize_session_state()
                # Removed the recursive call to st.rerun()
    
    def render_metrics(self):
        """Render the metrics panel"""
        if not self.simulation_data:
            return st.warning("No simulation data available")
        
        latest = self.simulation_data[-1]
        
        st.markdown("### Engine Metrics")
        st.markdown("---")
        
        # Create a container for metrics with some styling
        with st.container():
            # Basic metrics
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric("RPM", f"{latest.get('rpm', 0):.0f}")
                st.metric("Power (kW)", f"{latest.get('power', 0):.1f}")
                st.metric("Torque (Nm)", f"{latest.get('torque', 0):.1f}")
            
            with col_b:
                st.metric("Efficiency (%)", f"{latest.get('efficiency', 0):.1f}")
                st.metric("Throttle (%)", f"{latest.get('throttle', 0):.0f}")
                st.metric("Load (%)", f"{latest.get('load', 0):.0f}")
            
            # Advanced metrics in expander
            with st.expander("Advanced Metrics"):
                if 'air_fuel_ratio' in latest:
                    st.metric("Air/Fuel Ratio", f"{latest['air_fuel_ratio']:.1f}")
                if 'cylinder_pressure' in latest:
                    st.metric("Cylinder Pressure", f"{latest['cylinder_pressure']:.1f} kPa")
                if 'cylinder_temp' in latest:
                    st.metric("Cylinder Temp", f"{latest['cylinder_temp']:.1f} °C")
                if 'intake_valve_lift' in latest:
                    st.metric("Intake Valve", f"{latest['intake_valve_lift']*1000:.2f} mm")
                if 'exhaust_valve_lift' in latest:
                    st.metric("Exhaust Valve", f"{latest['exhaust_valve_lift']*1000:.2f} mm")
        
    def run(self):
        """Run the Streamlit application"""
        st.title("🔧 Combustion Engine Simulator")
        
        # Initialize engine if not already done
        if not hasattr(self, 'engine') or not self.engine:
            self.create_engine()
        
        # Main layout with sidebar
        self.render_sidebar()
        
        # Main content area
        col1, col2 = st.columns([3, 1])  # 3:1 ratio for charts:metrics
        
        with col1:
            # Charts area
            if self.simulation_data:
                self.update_charts(st)
            else:
                st.info("Run the simulation to see the charts")
        
        with col2:
            # Metrics panel
            self.render_metrics()
        
        # Controls at the bottom
        st.markdown("---")
        # Removed the recursive call to self.render_controls()
    
    # Removed the recursive call to self.render_metrics()
    
    def render_controls(self):
        # Show data table
        if st.checkbox("Show raw data"):
            st.dataframe(pd.DataFrame(self.simulation_data), use_container_width=True)
        else:
            st.info("Configure the engine parameters and click 'Run Simulation' to begin.")

# Run the application
if __name__ == "__main__":
    app = EngineSimulatorApp()
    app.run()
