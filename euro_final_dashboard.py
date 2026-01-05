import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import os

# --- 1. SETTING UP THE PAGE ---
st.set_page_config(page_title="Euro 2024 Final - Tactical Lab", layout="wide")
st.title("⚽ Euro 2024 Final: Tactical Analysis Dashboard")

# --- 2. LOADING DATA ---
@st.cache_data
def load_data():
    """Load and preprocess StatsBomb event data using relative paths."""
    # This path looks inside the 'data' folder relative to this script
    path = os.path.join('data', 'euro_final_events.csv')
    
    if os.path.exists(path):
        df = pd.read_csv(path)
        
        # --- StatsBomb Coordinate Extraction ---
        if 'location' in df.columns:
            coords = df['location'].str.strip('[]').str.split(', ', expand=True).astype(float)
            df['x'], df['y'] = coords[0], coords[1]
            
        if 'pass_end_location' in df.columns:
            end_coords = df['pass_end_location'].str.strip('[]').str.split(', ', expand=True).astype(float)
            df['end_x'], df['end_y'] = end_coords[0], end_coords[1]
            
        if 'carry_end_location' in df.columns:
            c_coords = df['carry_end_location'].str.strip('[]').str.split(', ', expand=True).astype(float)
            df['c_end_x'], df['c_end_y'] = c_coords[0], c_coords[1]
            
        return df
    return None

df = load_data()

if df is not None:
    # --- 3. SIDEBAR CONTROLS ---
    st.sidebar.header("Tactical Controls")
    selected_team = st.sidebar.selectbox("Select Team:", df['team'].unique())
    
    team_df = df[df['team'] == selected_team]
    players = ["All Team"] + sorted(team_df['player'].dropna().unique().tolist())
    selected_player = st.sidebar.selectbox("Select Player:", players)

    # --- 4. DATA PROCESSING ---
    if selected_player == "All Team":
        plot_df = team_df.copy()
    else:
        plot_df = team_df[team_df['player'] == selected_player].copy()

    # --- 5. VISUALIZATION ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Tactical Map: {selected_player}")
        view_type = st.radio("Display Mode:", ["Pass Map", "Heatmap", "Carries & Dribbles"], horizontal=True)
        
        pitch = Pitch(pitch_type='statsbomb', pitch_color='#1a1a1a', line_color='#7c7c7c')
        fig, ax = pitch.draw(figsize=(10, 8))

        if view_type == "Pass Map":
            passes = plot_df[plot_df['type'] == 'Pass']
            pitch.arrows(passes.x, passes.y, passes.end_x, passes.end_y, 
                         color='#ef1010', width=1.5, headwidth=8, ax=ax, alpha=0.7)
        elif view_type == "Heatmap":
            pitch.heatmap(pitch.bin_statistic(plot_df.x, plot_df.y, statistic='count'), 
                          ax=ax, cmap='Reds', alpha=0.5)
        else:
            carries = plot_df[plot_df['type'] == 'Carry']
            pitch.lines(carries.x, carries.y, carries.c_end_x, carries.c_end_y, 
                        ls='--', color='#f1c40f', lw=2, ax=ax, alpha=0.6)

        st.pyplot(fig)

    with col2:
        st.subheader("Performance Metrics")
        
        p_df = plot_df[plot_df['type'] == 'Pass']
        if not p_df.empty:
            acc = (len(p_df[p_df['pass_outcome'].isna()]) / len(p_df)) * 100
            st.metric("Pass Accuracy", f"{acc:.1f}%")
            st.metric("Total Passes", len(p_df))
        
        st.write("---")
        st.write("**Top Recipients:**")
        st.write(p_df['pass_recipient'].value_counts().head(5))
        
        if 'xT' in plot_df.columns:
            st.metric("Expected Threat (xT)", f"{plot_df['xT'].sum():.3f}")

else:
    # Error message if the relative path fails
    st.error("Error Loading File! Please ensure 'data/euro_final_events.csv' exists in your repository.")