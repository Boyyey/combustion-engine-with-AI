"""
🚀 Advanced Engine Simulator - Simplified Version
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from engine.mechanics import Engine

# Set page config
st.set_page_config(
    page_title="🚀 Engine Simulator",
    page_icon="🚗",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-value { color: #00f5d4; font-size: 1.5rem; font-weight: bold; }
    .metric-label { color: #8b93a7; font-size: 0.9rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

class SimpleEngineViz:
    def __init__(self):
        self.engine = Engine(cylinders=4)
        self.running = False
        self.time_step = 0.1
        self.view_mode = "normal"
        
    def create_engine_3d_model(self):
        fig = go.Figure()
        
        # Add cylinders and pistons
        for i in range(4):
            x_pos = (i - 1.5) * 0.5
            
            # Add cylinder
            self._add_cylinder(fig, x_pos)
            
            # Add piston with movement
            piston_pos = (np.cos(np.radians(self.engine.angle * 2 + i * 90)) + 1) / 2
            self._add_piston(fig, x_pos, piston_pos)
            
            # Add valves (simplified)
            self._add_valve(fig, x_pos + 0.2, 0.1, "intake")
            self._add_valve(fig, x_pos - 0.2, 0.1, "exhaust")
        
        # Update layout
        fig.update_layout(
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                aspectmode='data',
                camera=dict(eye=dict(x=2, y=2, z=1.5)),
                bgcolor='#0a0e17'
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            height=600
        )
        return fig
    
    def _add_cylinder(self, fig, x_pos):
        theta = np.linspace(0, 2*np.pi, 50)
        z = np.linspace(-0.4, 0.4, 2)
        theta_grid, z_grid = np.meshgrid(theta, z)
        x = x_pos + 0.2 * np.cos(theta_grid)
        y = 0.2 * np.sin(theta_grid)
        fig.add_trace(go.Surface(x=x, y=y, z=z_grid, 
                               colorscale=[[0, '#4a6b8a'], [1, '#4a6b8a']], 
                               showscale=False))
    
    def _add_piston(self, fig, x_pos, position):
        theta = np.linspace(0, 2*np.pi, 30)
        x = x_pos + 0.15 * np.cos(theta)
        y = 0.15 * np.sin(theta)
        z = -0.3 + position * 0.6
        fig.add_trace(go.Mesh3d(x=x, y=y, z=[z]*len(x), color='#e63946', opacity=0.9))
    
    def _add_valve(self, fig, x_pos, lift, valve_type):
        if lift <= 0.01: return
        z_pos = 0.4 - (lift * 0.3)
        color = '#a8dadc' if valve_type == "intake" else '#ef476f'
        fig.add_trace(go.Cone(x=[x_pos], y=[0], z=[z_pos], 
                             u=[0], v=[0], w=[-0.1],
                             sizemode="scaled", 
                             sizeref=0.1, 
                             showscale=False,
                             colorscale=[[0, color], [1, color]]))

def main():
    st.title("🚗 Engine Simulator")
    
    # Initialize session state
    if 'viz' not in st.session_state:
        st.session_state.viz = SimpleEngineViz()
    
    # Sidebar controls
    with st.sidebar:
        st.header("Controls")
        
        # Start/Stop button
        if st.button("Start" if not st.session_state.viz.running else "Pause"):
            st.session_state.viz.running = not st.session_state.viz.running
        
        # Throttle control
        throttle = st.slider("Throttle", 0.0, 1.0, 0.5, 0.01)
        
        # View mode
        view_mode = st.radio("View", ["normal", "exploded"], horizontal=True)
        st.session_state.viz.view_mode = view_mode
        
        # Metrics
        st.markdown("### Metrics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("RPM", f"{int(st.session_state.viz.engine.rpm)}")
        with col2:
            st.metric("Torque", f"{st.session_state.viz.engine.torque:.1f} Nm")
    
    # Main content
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Update engine state
        if st.session_state.viz.running:
            st.session_state.viz.engine.update(
                st.session_state.viz.time_step,
                throttle
            )
        
        # Render 3D model
        fig = st.session_state.viz.create_engine_3d_model()
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Engine Status")
        st.metric("Cylinders", "4")
        st.metric("Displacement", "2.0L")
        st.metric("Power", f"{st.session_state.viz.engine.power:.1f} kW")
        st.metric("Throttle", f"{throttle*100:.0f}%")

if __name__ == "__main__":
    main()
