"""
🚀 Advanced Combustion Engine Simulator with AI-Powered Features
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import time
import random
from datetime import datetime, timedelta
from engine.mechanics import Engine
from engine.thermodynamics import ThermodynamicSystem, CombustionModel

# Set page config with modern theme - must be first command
st.set_page_config(
    page_title="🚀 Advanced Engine Simulator",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Modern styling */
    .main .block-container { padding: 1rem 2rem 2rem; max-width: 95%; }
    .metric-value { color: #00f5d4; font-size: 1.8rem; font-weight: bold; }
    .metric-label { color: #8b93a7; font-size: 0.9rem; text-transform: uppercase; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; transition: all 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    .stTabs [data-baseweb="tab"] { height: 50px; padding: 0 25px; border-radius: 8px 8px 0 0; }
    .custom-card { background: rgba(30, 35, 48, 0.7); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# Custom CSS
st.markdown("""
<style>
    .metric-value { color: #00f5d4; font-size: 1.5rem; font-weight: bold; }
    .metric-label { color: #8b93a7; font-size: 0.9rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

class EngineSimulation:
    def __init__(self):
        # Initialize engine and simulation state
        self.engine = Engine(cylinders=4)
        self.thermo_system = ThermodynamicSystem()
        self.combustion_model = CombustionModel()
        
        # Simulation state
        self.running = False
        self.simulation_speed = 1.0
        self.time_step = 0.1
        self.simulation_time = 0
        self.last_update = time.time()
        
        # View settings
        self.view_mode = "normal"  # normal, exploded, cross_section
        self.camera_view = "perspective"  # perspective, top, side, front
        
        # Performance metrics
        self.performance_history = {
            'time': [],
            'rpm': [],
            'torque': [],
            'power': [],
            'efficiency': [],
            'temperature': [],
            'vibration': []
        }
        
        # Engine health
        self.engine_health = {
            'oil_life': 100.0,  # %
            'spark_plugs': 100.0,  # %
            'air_filter': 100.0,  # %
            'oil_pressure': 65.0,  # psi
            'coolant_temp': 90.0,  # °C
            'last_maintenance': datetime.now() - timedelta(days=30)
        }
        
        # AI state
        self.ai_suggestions = []
        self.last_ai_update = 0
        
    def update_simulation(self, throttle):
        """Update the engine simulation state"""
        if not self.running:
            return
            
        # Update engine state
        self.engine.update(self.time_step, throttle)
        
        # Calculate piston position for the first cylinder (for visualization)
        theta = np.radians(self.engine.angle)
        r = self.engine.cylinders[0].stroke / 2
        l = r * 1.75  # Rod ratio 1.75:1
        piston_pos = r * np.cos(theta) + np.sqrt(l**2 - (r * np.sin(theta))**2)
        
        # Calculate heat addition using combustion model
        # For a 4-cylinder engine, combustion happens every 180 degrees
        combustion_start = 10  # degrees before TDC (Top Dead Center)
        total_heat = 1000.0 * throttle  # Total heat based on throttle position
        
        # Calculate heat release for each cylinder
        heat_addition = 0
        for i in range(4):
            # Each cylinder fires every 720/4 = 180 degrees
            cylinder_angle = (self.engine.angle + i * 180) % 720
            heat_addition += self.combustion_model.heat_release_rate(
                theta=cylinder_angle,
                theta_start=combustion_start,
                total_heat=total_heat
            )
        
        # Update thermodynamic model with normalized volume (0-1 range)
        normalized_volume = (piston_pos / self.engine.cylinders[0].stroke)
        self.thermo_system.update_state(
            volume=1.0 - (normalized_volume * 0.8),  # Scale to reasonable range
            heat_addition=heat_addition,
            heat_loss=0.0,
            isentropic=False
        )
        
        # Update performance metrics
        current_time = time.time()
        time_delta = current_time - self.last_update
        self.simulation_time += time_delta
        self.last_update = current_time
        
        # Record metrics (keep last 100 data points)
        for key in ['time', 'rpm', 'torque', 'power']:
            if key in self.performance_history:
                if len(self.performance_history[key]) > 100:
                    self.performance_history[key].pop(0)
        
        self.performance_history['time'].append(self.simulation_time)
        self.performance_history['rpm'].append(self.engine.rpm)
        self.performance_history['torque'].append(self.engine.torque)
        self.performance_history['power'].append(self.engine.power)
        
        # Calculate efficiency (simplified)
        efficiency = min(0.35 * (throttle + 0.3) + np.random.uniform(-0.05, 0.05), 0.9)
        self.performance_history['efficiency'].append(efficiency)
        
        # Update AI suggestions periodically
        if self.simulation_time - self.last_ai_update > 5:  # Every 5 seconds
            self.update_ai_suggestions()
            self.last_ai_update = self.simulation_time
    
    def update_ai_suggestions(self):
        """Generate AI-powered suggestions based on engine state"""
        self.ai_suggestions = []
        
        # Check oil life
        if self.engine_health['oil_life'] < 20:
            self.ai_suggestions.append({
                'type': 'warning',
                'message': 'Oil change recommended soon',
                'priority': 1
            })
        
        # Check spark plugs
        if self.engine_health['spark_plugs'] < 30:
            self.ai_suggestions.append({
                'type': 'warning',
                'message': 'Spark plugs may need replacement',
                'priority': 2
            })
        
        # Check for optimal RPM range
        if self.engine.rpm > 6000:
            self.ai_suggestions.append({
                'type': 'info',
                'message': 'High RPM detected - consider upshifting',
                'priority': 3
            })
    
    def create_engine_3d_model(self):
        """Create a 3D model of the engine with enhanced visualization"""
        fig = go.Figure()
        
        # Calculate offsets based on view mode
        if self.view_mode == "exploded":
            offset = 0.2 * (1 + np.sin(time.time() * 0.5) * 0.2)  # Subtle pulsing effect
        else:
            offset = 0.0
        
        # Add engine block
        self._add_engine_block(fig)
        
        # Add cylinders, pistons, and valves
        for i in range(4):
            # Calculate position with explosion effect
            if self.view_mode == "exploded":
                x_pos = (i - 1.5) * (0.6 + offset)
            else:
                x_pos = (i - 1.5) * 0.5
            
            # Add cylinder
            self._add_cylinder(fig, x_pos)
            
            # Calculate piston position based on engine angle and cylinder offset
            theta = np.radians(self.engine.angle + (i * 180))  # 180° offset between cylinders
            r = self.engine.cylinders[i].stroke / 2
            l = r * 1.75  # Rod ratio 1.75:1
            piston_pos = (r * np.cos(theta) + np.sqrt(l**2 - (r * np.sin(theta))**2)) / self.engine.cylinders[i].stroke
            
            # Add piston with correct position and size
            self._add_piston(fig, x_pos, 1.0 - piston_pos, i)  # Invert Y for correct orientation
            
            # Add valves with timing
            intake_open = 0 < (self.engine.angle + i * 180) % 720 < 90
            exhaust_open = 180 < (self.engine.angle + i * 180) % 720 < 270
            
            self._add_valve(fig, x_pos + 0.2, 
                          self.engine.cylinders[i].intake.lift if intake_open else 0, 
                          "intake")
            self._add_valve(fig, x_pos - 0.2, 
                          self.engine.cylinders[i].exhaust.lift if exhaust_open else 0, 
                          "exhaust")
            
            # Add spark plug effect when firing
            if 350 < (self.engine.angle + i * 180) % 720 < 370:
                self._add_spark_effect(fig, x_pos, 0.3)
        
        # Add crankshaft
        self._add_crankshaft(fig, self.engine.angle)
        
        # Add connecting rods
        for i in range(4):
            x_pos = (i - 1.5) * 0.5
            piston_pos = (np.cos(np.radians(self.engine.angle * 2 + i * 90)) + 1) / 2
            self._add_connecting_rod(fig, x_pos, piston_pos, self.engine.angle + i * 90)
        
        # Configure camera based on view
        camera = self._get_camera_settings()
        
        # Update layout with enhanced settings
        fig.update_layout(
            scene=dict(
                xaxis=dict(visible=False, showbackground=False),
                yaxis=dict(visible=False, showbackground=False),
                zaxis=dict(visible=False, showbackground=False),
                aspectmode='data',
                camera=camera,
                bgcolor='#0a0e17',
                xaxis_showspikes=False,
                yaxis_showspikes=False,
                zaxis_showspikes=False,
                annotations=self._get_engine_annotations()
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            height=700,
            paper_bgcolor='#0a0e17',
            plot_bgcolor='#0a0e17',
            scene_camera=camera,
            uirevision='no_ui_update'  # Prevents camera reset on update
        )
        
        # Add colorbar for temperature visualization
        if self.view_mode == "temperature":
            fig.update_layout(
                coloraxis_colorbar=dict(
                    title="Temperature (°C)",
                    thicknessmode="pixels", thickness=20,
                    lenmode="pixels", len=200,
                    yanchor="top", y=1,
                    xanchor="left", x=1.05
                )
            )
            
        return fig
    
    def _get_camera_settings(self):
        """Return camera settings based on current view"""
        if self.camera_view == "top":
            return dict(eye=dict(x=0, y=0, z=2.5),
                      up=dict(x=0, y=1, z=0),
                      center=dict(x=0, y=0, z=0))
        elif self.camera_view == "side":
            return dict(eye=dict(x=3, y=0, z=0.5),
                      up=dict(x=0, y=0, z=1),
                      center=dict(x=0, y=0, z=0))
        elif self.camera_view == "front":
            return dict(eye=dict(x=0, y=3, z=0.5),
                      up=dict(x=0, y=0, z=1),
                      center=dict(x=0, y=0, z=0))
        else:  # perspective
            return dict(eye=dict(x=2, y=2, z=1.5),
                      up=dict(x=0, y=0, z=1),
                      center=dict(x=0, y=0, z=0))
    
    def _get_engine_annotations(self):
        """Return annotations for the 3D scene"""
        if self.view_mode != "annotated":
            return []
            
        return [
            dict(
                x=0, y=0, z=0.5,
                text="Engine Block",
                showarrow=True,
                arrowhead=2,
                ax=50,
                ay=-50
            )
        ]
    
    def _add_engine_block(self, fig):
        """Add the main engine block"""
        # Simple engine block representation
        x = np.linspace(-1, 1, 2)
        y = np.linspace(-0.4, 0.4, 2)
        z = np.linspace(-0.6, 0.6, 2)
        
        # Create a simple rectangular block
        fig.add_trace(go.Volume(
            x=x.repeat(4).flatten(),
            y=np.tile(y, 4).flatten(),
            z=z.repeat(4).flatten(),
            value=np.ones(8),
            isomin=0.5,
            isomax=1.5,
            surface_count=1,
            colorscale=[[0, '#2a3f5f'], [1, '#2a3f5f']],
            showscale=False,
            opacity=0.2
        ))
    
    def _add_cylinder(self, fig, x_pos):
        """Add a cylinder to the 3D model"""
        theta = np.linspace(0, 2*np.pi, 50)
        z = np.linspace(-0.4, 0.4, 2)
        theta_grid, z_grid = np.meshgrid(theta, z)
        
        x = x_pos + 0.2 * np.cos(theta_grid)
        y = 0.2 * np.sin(theta_grid)
        
        # Add cylinder walls
        fig.add_trace(go.Surface(
            x=x, y=y, z=z_grid,
            colorscale=[[0, '#4a6b8a'], [1, '#4a6b8a']],
            showscale=False,
            opacity=0.8,
            hoverinfo='none'
        ))
        
        # Add cylinder head
        fig.add_trace(go.Surface(
            x=x, y=y, z=0.4 + z_grid*0.1,
            colorscale=[[0, '#3a5a80'], [1, '#3a5a80']],
            showscale=False,
            opacity=0.9,
            hoverinfo='none'
        ))
    
    def _add_piston(self, fig, x_pos, position, cylinder_num):
        """Add a piston to the 3D model"""
        theta = np.linspace(0, 2*np.pi, 30)
        z = np.linspace(-0.1, 0.1, 2)
        theta_grid, z_grid = np.meshgrid(theta, z)
        
        # Position the piston based on engine angle
        z_pos = -0.3 + position * 0.6
        
        # Piston top
        x = x_pos + 0.15 * np.cos(theta_grid)
        y = 0.15 * np.sin(theta_grid)
        
        # Add piston crown
        fig.add_trace(go.Surface(
            x=x, y=y, z=z_grid + z_pos + 0.1,
            colorscale=[[0, '#e63946'], [1, '#e63946']],
            showscale=False,
            opacity=0.9,
            hoverinfo='none'
        ))
        
        # Add piston skirt
        fig.add_trace(go.Surface(
            x=x*0.8, y=y*0.8, z=z_grid + z_pos - 0.1,
            colorscale=[[0, '#f8ad9d'], [1, '#f8ad9d']],
            showscale=False,
            opacity=0.8,
            hoverinfo='none'
        ))
        
        # Add connecting rod cap (simplified)
        fig.add_trace(go.Cone(
            x=[x_pos], y=[0], z=[z_pos - 0.15],
            u=[0], v=[0], w=[-0.1],
            sizemode="scaled",
            sizeref=0.08,
            anchor="tip",
            colorscale=[[0, '#8d99ae'], [1, '#8d99ae']],
            showscale=False
        ))
    
    def _add_valve(self, fig, x_pos, lift, valve_type):
        """Add a valve to the 3D model"""
        if lift <= 0.01:
            return
            
        # Valve stem
        z_pos = 0.4 - (lift * 0.3)
        color = '#a8dadc' if valve_type == "intake" else '#ef476f'
        
        # Add valve stem
        fig.add_trace(go.Cylinder(
            x=[x_pos],
            y=[0],
            z=[z_pos],
            u=[0],
            v=[0],
            w=[-0.1],
            radius=0.02,
            colorscale=[[0, color], [1, color]],
            showscale=False
        ))
        
        # Add valve head
        fig.add_trace(go.Cone(
            x=[x_pos], y=[0], z=[z_pos - 0.05],
            u=[0], v=[0], w=[-0.05],
            sizemode="scaled",
            sizeref=0.12,
            anchor="tip",
            colorscale=[[0, color], [1, color]],
            showscale=False
        ))
    
    def _add_spark_effect(self, fig, x_pos, intensity):
        """Add a spark effect at the spark plug location"""
        # Simple spark effect using points
        fig.add_trace(go.Scatter3d(
            x=[x_pos + random.uniform(-0.02, 0.02)],
            y=[random.uniform(-0.02, 0.02)],
            z=[0.3 + random.uniform(-0.02, 0.02)],
            mode='markers',
            marker=dict(
                size=5 + 10 * intensity,
                color='#ffd700',
                opacity=0.8
            ),
            hoverinfo='none'
        ))
    
    def _add_crankshaft(self, fig, angle):
        """Add a crankshaft to the 3D model"""
        # Simple crankshaft representation
        t = np.linspace(-2, 2, 100)
        x = t
        y = -0.3 * np.sin(t * np.pi + np.radians(angle))
        z = -0.3 * np.cos(t * np.pi + np.radians(angle)) - 0.5
        
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            line=dict(color='#8d99ae', width=4),
            hoverinfo='none'
        ))
    
    def _add_connecting_rod(self, fig, x_pos, piston_pos, angle):
        """Add a connecting rod between piston and crankshaft"""
        # Calculate positions
        piston_z = -0.3 + piston_pos * 0.6
        crank_angle = np.radians(angle)
        crank_x = x_pos * 0.8
        crank_y = -0.3 * np.sin(crank_angle)
        crank_z = -0.3 * np.cos(crank_angle) - 0.5
        
        # Draw connecting rod
        fig.add_trace(go.Scatter3d(
            x=[x_pos, crank_x],
            y=[0, crank_y],
            z=[piston_z, crank_z],
            mode='lines',
            line=dict(color='#6c757d', width=3),
            hoverinfo='none'
        ))

def main():
    st.title("🚀 Advanced Engine Simulator")
    
    # Initialize session state
    if 'sim' not in st.session_state:
        st.session_state.sim = EngineSimulation()
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Engine Controls")
        
        # Start/Stop and Reset
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏵ Start" if not st.session_state.sim.running else "⏸ Pause", 
                        type="primary", use_container_width=True):
                st.session_state.sim.running = not st.session_state.sim.running
        with col2:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.sim = EngineSimulation()
        
        # Throttle control
        st.markdown("### Throttle Control")
        throttle = st.slider("Throttle Position", 0.0, 1.0, 0.5, 0.01, 
                           format="%.0f%%", 
                           help="Control the engine's throttle position")
        
        # View controls
        st.markdown("### View Settings")
        view_mode = st.radio(
            "View Mode",
            ["normal", "exploded", "cross_section", "temperature"],
            horizontal=True,
            format_func=lambda x: x.capitalize()
        )
        st.session_state.sim.view_mode = view_mode
        
        # Real-time metrics
        st.markdown("### 📊 Real-time Metrics")
        
        # Gauge-style metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='metric-label'>RPM</div><div class='metric-value'>{int(st.session_state.sim.engine.rpm)}</div>", 
                       unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-label'>Torque</div><div class='metric-value'>{st.session_state.sim.engine.torque:.1f}<span style='font-size:0.8rem;color:#8b93a7;'> Nm</span></div>", 
                       unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-label'>Power</div><div class='metric-value'>{st.session_state.sim.engine.power:.1f}<span style='font-size:0.8rem;color:#8b93a7;'> kW</span></div>", 
                       unsafe_allow_html=True)
        
        # AI Suggestions
        if st.session_state.sim.ai_suggestions:
            st.markdown("### 🤖 AI Assistant")
            for suggestion in st.session_state.sim.ai_suggestions[:3]:  # Show max 3 suggestions
                emoji = "⚠️" if suggestion['type'] == 'warning' else "💡"
                st.info(f"{emoji} {suggestion['message']}")
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Update simulation
        if st.session_state.sim.running:
            st.session_state.sim.update_simulation(throttle)
        
        # Create and display 3D model
        fig = st.session_state.sim.create_engine_3d_model()
        st.plotly_chart(fig, use_container_width=True, use_container_height=True)
        
        # Performance graphs
        st.markdown("### Performance Metrics")
        tab1, tab2 = st.tabs(["RPM & Power", "Efficiency"])
        
        with tab1:
            if len(st.session_state.sim.performance_history['time']) > 1:
                df = pd.DataFrame({
                    'Time (s)': st.session_state.sim.performance_history['time'],
                    'RPM': st.session_state.sim.performance_history['rpm'],
                    'Power (kW)': st.session_state.sim.performance_history['power']
                })
                st.line_chart(df.set_index('Time (s)'))
        
        with tab2:
            if len(st.session_state.sim.performance_history['time']) > 1:
                df = pd.DataFrame({
                    'Time (s)': st.session_state.sim.performance_history['time'],
                    'Efficiency (%)': [x*100 for x in st.session_state.sim.performance_history['efficiency']]
                })
                st.area_chart(df.set_index('Time (s)'))
    
    with col2:
        # Engine status panel
        with st.container():
            st.markdown("### ⚙️ Engine Status")
            
            # Engine specs
            st.markdown("#### Specifications")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Cylinders", "4")
                st.metric("Displacement", "2.0L")
            with col2:
                st.metric("Max Power", "250 HP @ 6500 RPM")
                st.metric("Max Torque", "300 Nm @ 4000 RPM")
            
            # Current readings
            st.markdown("#### Current Readings")
            st.metric("Throttle", f"{throttle*100:.0f}%")
            st.metric("Oil Temperature", f"{st.session_state.sim.engine_health['coolant_temp']:.1f}°C")
            st.metric("Oil Pressure", f"{st.session_state.sim.engine_health['oil_pressure']:.1f} psi")

if __name__ == "__main__":
    main()
