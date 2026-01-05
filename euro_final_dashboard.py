import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import os

# --- 1. SETTING UP THE PAGE ---
# Configuration for a wider dashboard layout
st.set_page_config(page_title="Euro 2024 Final - Tactical Lab", layout="wide")
st.title("⚽ Euro 2024 Final: Tactical Analysis Dashboard")

# --- 2. LOADING DATA ---
@st.cache_data
def load_data():
    """Load and preprocess StatsBomb event data."""
    path = r'C:\Users\sch2\Football Analysis\World Cup 2022\Performance_Analysis_Project_3\data\euro_final_events.csv'
    
    if os.path.exists(path):
        df = pd.read_csv(path)
        
        # --- StatsBomb Coordinate Extraction ---
        # Extract starting coordinates [x, y] from the 'location' string
        if 'location' in df.columns:
            coords = df['location'].str.strip('[]').str.split(', ', expand=True).astype(float)
            df['x'], df['y'] = coords[0], coords[1]
            
        # Extract pass end coordinates from 'pass_end_location'
        if 'pass_end_location' in df.columns:
            end_coords = df['pass_end_location'].str.strip('[]').str.split(', ', expand=True).astype(float)
            df['end_x'], df['end_y'] = end_coords[0], end_coords[1]
            
        # Extract ball carry end coordinates from 'carry_end_location'
        if 'carry_end_location' in df.columns:
            c_coords = df['carry_end_location'].str.strip('[]').str.split(', ', expand=True).astype(float)
            df['c_end_x'], df['c_end_y'] = c_coords[0], c_coords[1]
            
        return df
    return None

df = load_data()

if df is not None:
    # --- 3. SIDEBAR CONTROLS ---
    st.sidebar.header("Tactical Controls")
    
    # Team Selection Filter
    selected_team = st.sidebar.selectbox("Select Team:", df['team'].unique())
    
    # Player Selection Filter (Filtered by Team)
    team_df = df[df['team'] == selected_team]
    players = ["All Team"] + sorted(team_df['player'].dropna().unique().tolist())
    selected_player = st.sidebar.selectbox("Select Player:", players)

    # --- 4. DATA PROCESSING ---
    # Filter dataset based on the selected player or team
    if selected_player == "All Team":
        plot_df = team_df.copy()
    else:
        plot_df = team_df[team_df['player'] == selected_player].copy()

    # --- 5. VISUALIZATION ---
    # Create two columns for the Pitch and the Statistics
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Tactical Map: {selected_player}")
        # Radio buttons to toggle between visualization modes
        view_type = st.radio("Display Mode:", ["Pass Map", "Heatmap", "Carries & Dribbles"], horizontal=True)
        
        # Initialize the Pitch with StatsBomb dimensions and a dark theme
        pitch = Pitch(pitch_type='statsbomb', pitch_color='#1a1a1a', line_color='#7c7c7c')
        fig, ax = pitch.draw(figsize=(10, 8))

        if view_type == "Pass Map":
            # Draw pass arrows (Successful passes highlighted in Red)
            passes = plot_df[plot_df['type'] == 'Pass']
            pitch.arrows(passes.x, passes.y, passes.end_x, passes.end_y, 
                         color='#ef1010', width=1.5, headwidth=8, ax=ax, alpha=0.7)
                         
        elif view_type == "Heatmap":
            # Generate a 2D histogram (Heatmap) of player/team positions
            pitch.heatmap(pitch.bin_statistic(plot_df.x, plot_df.y, statistic='count'), 
                          ax=ax, cmap='Reds', alpha=0.5)
                          
        else:
            # Draw Ball Carries as dashed yellow lines
            carries = plot_df[plot_df['type'] == 'Carry']
            pitch.lines(carries.x, carries.y, carries.c_end_x, carries.c_end_y, 
                        ls='--', color='#f1c40f', lw=2, ax=ax, alpha=0.6)

        st.pyplot(fig)

    with col2:
        st.subheader("Performance Metrics")
        
        # --- Pass Accuracy Calculation ---
        # StatsBomb 'pass_outcome' is NaN if the pass was successful
        p_df = plot_df[plot_df['type'] == 'Pass']
        if not p_df.empty:
            acc = (len(p_df[p_df['pass_outcome'].isna()]) / len(p_df)) * 100
            st.metric("Pass Accuracy", f"{acc:.1f}%")
            st.metric("Total Passes", len(p_df))
        
        # --- Passing Networks: Top Recipients ---
        # Display who the player/team passed to most frequently
        st.write("---")
        st.write("**Top Recipients:**")
        st.write(p_df['pass_recipient'].value_counts().head(5))
        
        # --- Advanced Stats (Expected Threat) ---
        if 'xT' in plot_df.columns:
            st.metric("Expected Threat (xT)", f"{plot_df['xT'].sum():.3f}")

else:
    # Error handling if the CSV path is incorrect
    st.error("Error Loading File! Check the directory path.")