import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
import re
from PIL import Image
import numpy as np
from datetime import datetime
import io

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="ClutchBoard",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NEW YELLOW/BLACK THEME ---
# Injected CSS to create the new theme
CUSTOM_CSS = """
<style>
/* Add a fade-in animation for the main content */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="stApp"] {
    animation: fadeIn 0.5s ease-out;
}

/* Base app background */
[data-testid="stApp"] > div:first-child {
    background-color: #0a0a0a; /* Off-black main background */
    color: #FAFAFA;
}

/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: #1a1a1a; /* Dark gray sidebar */
    padding-top: 3rem; /* Add padding to top of sidebar */
}

/* Headers - The "Yellow" accent */
h1, h2, h3, h4, h5, h6 {
    color: #FFD700; /* Gold/Yellow */
}

/* Main title color fix */
[data-testid="stHeader"] {
    color: #FFD700;
}

/* Expander (scrim details) styling */
[data-testid="stExpander"] {
    background-color: #2a2a2a; /* Lighter gray for containers */
    border-radius: 10px;
    border: 1px solid #FFD700;
    transition: all 0.3s ease-in-out; /* Animation */
}
[data-testid="stExpander"]:hover {
    background-color: #333333; /* Slightly lighter on hover */
    border-color: #FFFFFF;
}
[data-testid="stExpander"] > div:first-child {
    color: #FAFAFA; /* Expander title text */
}

/* Metric cards in sidebar */
[data-testid="stSidebar"] [data-testid="stMetric"] {
    background-color: #2a2a2a; /* Darker bg for sidebar metrics */
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #FFD700;
    margin-bottom: 10px; /* Space out metrics */
    transition: all 0.3s ease-in-out; /* Animation */
}
[data-testid="stSidebar"] [data-testid="stMetric"]:hover {
    transform: scale(1.03); /* Grow slightly */
    border-color: #FFFFFF; /* Highlight with white */
}
[data-testid="stSidebar"] [data-testid="stMetric"] label {
    color: #FAFAFA; /* Metric label */
}
[data-testid="stSidebar"] [data-testid="stMetric"] data {
    color: #FFD700; /* Metric value */
}

/* Buttons */
[data-testid="stButton"] button {
    background-color: #FFD700;
    color: #0a0a0a;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    transition: all 0.3s ease-in-out; /* Animation */
}
[data-testid="stButton"] button:hover {
    background-color: #FFFFFF; /* Hover: white bg */
    color: #0a0a0a; /* black text */
    transform: translateY(-2px); /* Lift */
    box-shadow: 0 4px 10px rgba(255, 215, 0, 0.3); /* Yellow glow */
}
[data-testid="stButton"] button:active {
    background-color: #FFD700 !important;
    color: #0a0a0a !important;
}

/* Form background */
[data-testid="stForm"] {
    background-color: #1a1a1a;
    padding: 15px;
    border-radius: 8px;
}

/* Radio buttons for navigation */
[data-testid="stRadio"] > label {
    background-color: #2a2a2a;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 10px;
}
[data-testid="stRadio"] label > div[data-testid="stMarkdownContainer"] > p {
    font-size: 1.1rem;
    font-weight: bold;
}

/* Subheader for maps within a series */
.map-subheader {
    color: #FFD700;
    font-size: 1.2rem;
    font-weight: bold;
    border-bottom: 1px solid #444;
    padding-bottom: 5px;
    margin-top: 15px;
}

/* Info box styling */
[data-testid="stInfo"] {
    background-color: rgba(255, 215, 0, 0.05); /* Faint yellow bg */
    border-left: 5px solid #FFD700;
    border-radius: 5px;
}
[data-testid="stInfo"] p {
    color: #FAFAFA;
}

/* Warning box styling */
[data-testid="stWarning"] {
    background-color: rgba(255, 69, 0, 0.05); /* Faint red bg */
    border-left: 5px solid #FF4500;
    border-radius: 5px;
}
[data-testid="stWarning"] p {
    color: #FAFAFA;
}

/* Player Name under Agent Icon */
.player-name {
    font-size: 11px;
    color: #FFD700; /* Yellow */
    font-weight: bold;
    margin-top: -4px; /* Pulls it closer to agent name */
}
.agent-name {
    font-size: 12px;
    margin: 4px 0 0 0;
    word-wrap: break-word;
    color: #FAFAFA;
}

/* Login Form Container */
.login-container {
    max-width: 450px;
    margin: 5rem auto;
    padding: 2rem;
    background-color: #1a1a1a;
    border-radius: 10px;
    border: 1px solid #FFD700;
}

</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- CONSTANTS ---
# We no longer use single CSV files. Data is stored in session_state
# and would be loaded from a database in a real app.
AGENT_ICON_PATH = "agent_icons" 
ALL_MAPS = ["Ascent", "Bind", "Haven", "Split", "Lotus", "Breeze", "Icebox"]
DEFAULT_TEAM_ROSTER = ["Player1", "Player2", "Player3", "Player4", "Player5"]
DEFAULT_LOGO = "https://placehold.co/100x100/FFD700/0a0a0a?text=LOGO"

# --- DATA COLUMN DEFINITIONS ---
SCRIM_COLUMNS = [
    'Date', 'Map', 'Opponent', 
    'Our Attack', 'Our Defense', 'Opponent Attack', 'Opponent Defense', 'Result',
    'Our Agents', 'Opponent Agents', 'VOD Link',
    'P1_Agent', 'P2_Agent', 'P3_Agent', 'P4_Agent', 'P5_Agent'
]
TOURNAMENT_COLUMNS = [
    'Date', 'Tournament Name', 'Match Type', 'Map', 'Opponent', 
    'Our Attack', 'Our Defense', 'Opponent Attack', 'Opponent Defense', 'Result',
    'Our Agents', 'Opponent Agents', 'VOD Link',
    'P1_Agent', 'P2_Agent', 'P3_Agent', 'P4_Agent', 'P5_Agent'
]

# --- DEMO DATABASE (Simulating a real backend) ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "users": {
            "clutch_admin": {
                "password": "pass",
                "role": "Manager",
                "org_id": "org_clutch"
            },
            "clutch_coach": {
                "password": "pass",
                "role": "Coach",
                "org_id": "org_clutch" # Belongs to the same org
            },
            "clutch_player": {
                "password": "pass",
                "role": "Player",
                "org_id": "org_clutch" # Belongs to the same org
            },
            "envy_admin": {
                "password": "pass",
                "role": "Manager",
                "org_id": "org_envy" # A different org
            },
            "envy_player": {
                "password": "pass",
                "role": "Player",
                "org_id": "org_envy"
            }
        },
        "orgs": {
            "org_clutch": {
                "name": "Clutch Gaming",
                "logo_url": "https://placehold.co/100x100/FFD700/0a0a0a?text=CG",
                "roster": ["Player1", "Player2", "Player3", "Player4", "Player5"],
                "scrims": pd.DataFrame(columns=SCRIM_COLUMNS),
                "tournaments": pd.DataFrame(columns=TOURNAMENT_COLUMNS)
            },
            "org_envy": {
                "name": "Team Envy",
                "logo_url": "https://placehold.co/100x100/0000FF/FFFFFF?text=Envy",
                "roster": DEFAULT_TEAM_ROSTER,
                "scrims": pd.DataFrame(columns=SCRIM_COLUMNS),
                "tournaments": pd.DataFrame(columns=TOURNAMENT_COLUMNS)
            }
        }
    }
# --- END DEMO DATABASE ---

AGENTS = [
    "Astra", "Breach", "Brimstone", "Chamber", "Clove", "Cypher", "Deadlock",
    "Fade", "Gekko", "Harbor", "Iso", "Jett", "KAY/O", "Killjoy", "Neon",
    "Omen", "Phoenix", "Raze", "Reyna", "Sage", "Skye", "Sova", "Viper", "Yoru",
    "Veto", "Waylay", "Vyse"
]
AGENT_ROLE_MAP = {
    # Duelists
    "Jett": "🔫 Jett", "Neon": "🔫 Neon", "Phoenix": "🔫 Phoenix", "Raze": "🔫 Raze", "Reyna": "🔫 Reyna", "Yoru": "🔫 Yoru", "Iso": "🔫 Iso", "Waylay": "🔫 Waylay",
    # Initiators
    "Breach": "👁️ Breach", "Fade": "👁️ Fade", "Gekko": "👁️ Gekko", "KAY/O": "👁️ KAY/O", "Skye": "👁️ Skye", "Sova": "👁️ Sova",
    # Controllers
    "Astra": "🧠 Astra", "Brimstone": "🧠 Brimstone", "Clove": "🧠 Clove", "Harbor": "🧠 Harbor", "Omen": "🧠 Omen", "Viper": "🧠 Viper",
    # Sentinels
    "Chamber": "🛡️ Chamber", "Cypher": "🛡️ Cypher", "Deadlock": "🛡️ Deadlock", "Killjoy": "🛡️ Killjoy", "Sage": "🛡️ Sage", "Veto": "🛡️ Veto", "Vyse": "🛡️ Vyse",
}
AGENT_NAME_MAP = {v: k for k, v in AGENT_ROLE_MAP.items()}
AGENT_OPTIONS = [""] + list(AGENT_ROLE_MAP.values())
OPPONENT_AGENT_OPTIONS = list(AGENT_ROLE_MAP.values())


# --- AGENT IMAGE DATABASE (NOW LOCAL) ---
AGENT_IMAGE_FILES = {
    "Astra": "astra.png",
    "Breach": "breach.png",
    "Brimstone": "brimstone.png",
    "Chamber": "chamber.png",
    "Clove": "clove.png",
    "Cypher": "cypher.png",
    "Deadlock": "deadlock.png",
    "Fade": "fade.png",
    "Gekko": "gekko.png",
    "Harbor": "harbor.png",
    "Iso": "iso.png",
    "Jett": "jett.png",
    "KAY/O": "kayo.png", # Note the special name
    "Killjoy": "killjoy.png",
    "Neon": "neon.png",
    "Omen": "omen.png",
    "Phoenix": "phoenix.png",
    "Raze": "raze.png",
    "Reyna": "reyna.png",
    "Sage": "sage.png",
    "Skye": "skye.png",
    "Sova": "sova.png",
    "Viper": "viper.png",
    "Yoru": "yoru.png",
    "Veto": "veto.png",
    "Waylay": "waylay.png",
    "Vyse": "vyse.png"
}

# Base64 for a 64x64 gray placeholder
FALLBACK_IMAGE_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAPZJREFUeJzt0sEJACAMBEGv/O9oLYZgI1sBCl7g7h527wEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIADwOsJgEAGEBkAciMgjwCyDyA/A+pBABkIkB8B5RFgfADyI0BeBJBHAPkRkEcB+RGQRwD5EZBHAfkRkEcB+RGQRwD5EZBHAfkRkEcB+RGQRwD5EZBHAfkRkEcB+RGQRwD5EZBHAfkRkEcB+RGQRwD5EZBHAfkRkEcB+RGQRwD5EZBHAfkRkEcB+RGQRwD5EZBHAfkRkEcB+RGQRwD5EZBHAfkRkEcB+RGQRwD5EZBHAfkRkEcB+RHQfwDZAJAfAfUBkF8A+RGQBAB5ANIHYB8AyF8A+RkQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABg9wGfP6L8KAbpQgAAAABJRU5ErkJggg=="

# --- HELPER FUNCTION FOR LOCAL IMAGES ---
@st.cache_data
def get_image_as_base64(path):
    """Loads an image from a local path and returns it as a base64 string."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"Error loading image {path}: {e}")
        return None

# --- NEW: Function to encode uploaded logo ---
def encode_image_to_base64(uploaded_file):
    """Encodes an uploaded image file to a base64 data string."""
    try:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        # Get mime type
        mime_type = uploaded_file.type
        return f"data:{mime_type};base64,{base64_str}"
    except Exception as e:
        st.error(f"Error encoding image: {e}")
        return DEFAULT_LOGO


# --- NEW: MULTI-TENANT DATA FUNCTIONS ---
# These functions now interact with the `st.session_state.db` dictionary
# to simulate a real, org-specific database.

def get_org_data():
    """Gets the current user's organization data from the session state DB."""
    if 'org_id' in st.session_state and st.session_state.org_id in st.session_state.db['orgs']:
        return st.session_state.db['orgs'][st.session_state.org_id]
    return None

def load_data(data_type):
    """Loads scrims or tournaments DataFrame from the org's data."""
    org_data = get_org_data()
    if org_data and data_type in org_data:
        # Return a copy to prevent mutation issues
        return org_data[data_type].copy()
    # Return empty frame if not found
    if data_type == 'scrims':
        return pd.DataFrame(columns=SCRIM_COLUMNS)
    else:
        return pd.DataFrame(columns=TOURNAMENT_COLUMNS)

def save_data(df, data_type):
    """Saves the DataFrame back into the org's data in session state."""
    org_data = get_org_data()
    if org_data:
        org_data[data_type] = df
        # In a real app, this would be a database write.
        # Here we just update the dictionary in session_state.
        
def load_roster():
    """Loads the team roster from the org's data."""
    org_data = get_org_data()
    if org_data and 'roster' in org_data:
        roster = org_data['roster']
        if len(roster) == 5:
            return roster
    return DEFAULT_TEAM_ROSTER

def save_roster(roster_list):
    """Saves the 5-player roster to the org's data."""
    org_data = get_org_data()
    if org_data and len(roster_list) == 5:
        org_data['roster'] = roster_list

# --- END MULTI-TENANT DATA FUNCTIONS ---

# --- Function to get a row's index from its string representation ---
def get_index_from_string(match_string, df, page_type):
    if not match_string:
        return None
    for index, row in df.iterrows():
        row_string = ""
        if page_type == "Scrims":
            our_final = (0 if pd.isna(row['Our Attack']) else row['Our Attack']) + (0 if pd.isna(row['Our Defense']) else row['Our Defense'])
            opp_final = (0 if pd.isna(row['Opponent Attack']) else row['Opponent Attack']) + (0 if pd.isna(row['Opponent Defense']) else row['Opponent Defense'])
            row_string = f"{row['Date']} - {row['Opponent']} on {row['Map']} ({int(our_final)}-{int(opp_final)})"
        else: # Tournaments
            our_final = (0 if pd.isna(row['Our Attack']) else row['Our Attack']) + (0 if pd.isna(row['Our Defense']) else row['Our Defense'])
            opp_final = (0 if pd.isna(row['Opponent Attack']) else row['Opponent Attack']) + (0 if pd.isna(row['Opponent Defense']) else row['Opponent Defense'])
            row_string = f"Map: {row['Map']} ({row['Date']}) - {row.get('Tournament Name', 'N/A')} ({row.get('Match Type', 'N/A')}) vs {row['Opponent']} ({int(our_final)}-{int(opp_final)})"
        
        if match_string == row_string:
            return index
    return None


# --- INITIALIZE SESSION STATE ---
if 'editing_scrim_index' not in st.session_state:
    st.session_state.editing_scrim_index = None
if 'editing_tournament_index' not in st.session_state:
    st.session_state.editing_tournament_index = None

# --- AUTHENTICATION STATE ---
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'page' not in st.session_state:
    st.session_state.page = "Login" # New state to control login/signup view

# --- NEW: LOGIN/SIGNUP PAGES ---
def login_page():
    st.title("ClutchBoard Login 👑")
    
    # --- NEW: Explanation for demo persistence ---
    st.warning("**Note:** This is a demo. All accounts and data are temporary and will be **reset if you close this browser tab.** A real app would use a permanent database.")
    
    with st.form("login_form"):
        username = st.text_input("Username").lower()
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user = st.session_state.db['users'].get(username)
            if user and user['password'] == password:
                # --- SET ORG AND USER INFO ---
                st.session_state.user_role = user['role']
                st.session_state.username = username
                st.session_state.org_id = user['org_id'] # This is the key
                st.session_state.org_name = st.session_state.db['orgs'][user['org_id']]['name']
                
                # --- LOAD DATA *AFTER* LOGIN ---
                st.session_state.scrims = load_data("scrims")
                st.session_state.tournaments = load_data("tournaments")
                st.session_state.team_roster = load_roster()
                
                # --- DEFAULT TO SCRIMS PAGE ON LOGIN ---
                st.session_state.page = "Scrims"
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    if st.button("Don't have an account? Sign Up"):
        st.session_state.page = "Sign Up"
        st.rerun()

    st.info("Demo Logins (Username / Password):\n"
            "- clutch_admin / pass (Org: Clutch Gaming)\n"
            "- clutch_coach / pass (Org: Clutch Gaming)\n"
            "- clutch_player / pass (Org: Clutch Gaming)\n"
            "- envy_admin / pass (Org: Team Envy)\n"
            "- envy_player / pass (Org: Team Envy)")

def signup_page():
    st.title("Create Your Organization 👑")
    with st.form("signup_form"):
        st.info("You are registering as the 'Manager' (Owner) of a new organization.")
        org_name = st.text_input("Organization Name (e.g., Clutch Gaming)")
        
        # --- NEW: Logo Uploader ---
        logo_upload = st.file_uploader("Upload Team Logo (PNG or JPG)", type=["png", "jpg", "jpeg"])
        
        st.markdown("---")
        
        admin_username = st.text_input("Your Username (Admin)").lower()
        admin_password = st.text_input("Your Password", type="password")
        
        submitted = st.form_submit_button("Create Organization & Sign Up")

        if submitted:
            if not org_name or not admin_username or not admin_password:
                st.warning("All fields are required.")
            elif admin_username in st.session_state.db['users']:
                st.error("That username is already taken. Please choose another.")
            else:
                # --- Create the new org and user in our demo DB ---
                new_org_id = f"org_{org_name.lower().replace(' ', '')}"
                
                # --- NEW: Process logo upload ---
                logo_data = DEFAULT_LOGO
                if logo_upload is not None:
                    logo_data = encode_image_to_base64(logo_upload)
                
                # 1. Create the new Org
                st.session_state.db['orgs'][new_org_id] = {
                    "name": org_name,
                    "logo_url": logo_data, # Save the base64 string
                    "roster": DEFAULT_TEAM_ROSTER,
                    "scrims": pd.DataFrame(columns=SCRIM_COLUMNS),
                    "tournaments": pd.DataFrame(columns=TOURNAMENT_COLUMNS)
                }
                
                # 2. Create the new Admin/Manager user
                st.session_state.db['users'][admin_username] = {
                    "password": admin_password,
                    "role": "Manager",
                    "org_id": new_org_id
                }
                
                # In a real app, this data would be written to Firebase.
                # Here, we just update the session_state dict.
                
                st.success(f"Organization '{org_name}' created! Please log in.")
                st.session_state.page = "Login"
                st.rerun()

    if st.button("Back to Login"):
        st.session_state.page = "Login"
        st.rerun()

# --- END LOGIN/SIGNUP PAGES ---


# --- MAIN APP LOGIC ---
if st.session_state.user_role is None:
    # User is not logged in
    if st.session_state.page == "Sign Up":
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            signup_page()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            login_page()
            st.markdown('</div>', unsafe_allow_html=True)
else:
    # User IS logged in
    # --- SIDEBAR (STATS & NAVIGATION) ---
    with st.sidebar:
        st.title(f"ClutchBoard 👑")
        
        # Display Org Logo
        org_logo_url = st.session_state.db['orgs'][st.session_state.org_id]['logo_url']
        st.image(org_logo_url, width=100)
        
        st.write(f"Org: **{st.session_state.org_name}**")
        st.write(f"User: **{st.session_state.username}** ({st.session_state.user_role})")

        if st.button("Logout"):
            # Clear all session data on logout
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
        
        # --- PAGE NAVIGATION (Label removed) ---
        # Show "Team Roster" only to Manager/Coach
        if st.session_state.user_role in ["Manager", "Coach"]:
            pages = ["Scrims", "Tournaments", "Admin Panel"]
        else:
            pages = ["Scrims", "Tournaments"] # Player cannot see Roster page
        
        # --- NEW STATE MANAGEMENT (BUG FIX) ---
        # Get the index of the current page
        try:
            current_page_index = pages.index(st.session_state.page)
        except ValueError:
            st.session_state.page = "Scrims" # Default to scrims if page is invalid
            current_page_index = 0
            
        # Use on_change to set the page state correctly
        def update_page_state():
            st.session_state.page = st.session_state.sidebar_radio # "sidebar_radio" is the key of st.radio
        
        st.radio(
            "Navigation", 
            pages, 
            key="sidebar_radio", # Use a dedicated key
            index=current_page_index, 
            on_change=update_page_state, # Use on_change callback
            label_visibility="hidden"
        ) 
        st.markdown("---")

        # --- STATS DISPLAY (Context-aware) ---
        st.header("Team Statistics")
        
        if st.session_state.page == "Scrims":
            data_to_show = st.session_state.scrims
            data_title = "Scrim"
        elif st.session_state.page == "Tournaments":
            data_to_show = st.session_state.tournaments
            data_title = "Tournament"
        else: # On Admin page
            data_to_show = st.session_state.scrims # Show scrim stats by default
            data_title = "Scrim"

        if data_to_show.empty:
            st.warning(f"No {data_title} data entered yet. Add a result on the main page.")
        else:
            # --- TOP-LEVEL METRICS ---
            total_matches = len(data_to_show)
            
            # Calculate final scores from Attack/Defense scores, handling potential NA values
            our_final_score = data_to_show['Our Attack'].fillna(0) + data_to_show['Our Defense'].fillna(0)
            opp_final_score = data_to_show['Opponent Attack'].fillna(0) + data_to_show['Opponent Defense'].fillna(0)

            wins = (our_final_score > opp_final_score).sum()
            losses = (our_final_score < opp_final_score).sum()
            draws = (our_final_score == opp_final_score).sum()
            
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0

            # NEW: Calculate avg Attack/Defense scores
            avg_attack_score = data_to_show['Our Attack'].dropna().mean()
            avg_defense_score = data_to_show['Our Defense'].dropna().mean()

            st.metric(f"Total {data_title} Matches", total_matches)
            st.metric("Wins ✅", wins)
            st.metric("Losses ❌", losses)
            st.metric("Win Rate 📈", f"{win_rate:.2f}%")
            
            # --- NEW METRICS ---
            st.markdown("---")
            # --- BUG FIX: Use np.isnan to check for NaN floats ---
            st.metric("Avg. Attack Rounds Won", f"{avg_attack_score:.2f}" if not np.isnan(avg_attack_score) else "0.0")
            st.metric("Avg. Defense Rounds Won", f"{avg_defense_score:.2f}" if not np.isnan(avg_defense_score) else "0.0")

        st.markdown("---")


    # --- MAIN DASHBOARD AREA (DYNAMIC CONTENT) ---

    if st.session_state.page == "Scrims":
        st.title(f"{st.session_state.org_name} - Scrim Dashboard")
        
        # --- Check if we are in editing mode ---
        is_editing = st.session_state.editing_scrim_index is not None
        data_to_edit = {}
        default_agent_indices = [0] * 5
        default_opp_agents = []

        if is_editing:
            st.info("You are currently editing a match. Click 'Update Match' to save or 'Cancel Edit' to discard.")
            data_row = st.session_state.scrims.loc[st.session_state.editing_scrim_index]
            data_to_edit = data_row.to_dict()
            
            # Pre-fill player agents
            for i in range(5):
                player_agent = data_row.get(f'P{i+1}_Agent')
                if pd.notna(player_agent) and player_agent in AGENT_OPTIONS:
                    default_agent_indices[i] = AGENT_OPTIONS.index(player_agent)
            
            # Pre-fill opponent agents
            if pd.notna(data_row.get('Opponent Agents')):
                opp_agents_clean = data_row['Opponent Agents'].split(', ')
                default_opp_agents = [AGENT_ROLE_MAP.get(agent) for agent in opp_agents_clean if AGENT_ROLE_MAP.get(agent) in OPPONENT_AGENT_OPTIONS]

        # --- Scrim form (ROLE-BASED) ---
        if st.session_state.user_role in ["Manager", "Coach"]:
            form_title = "📝 Edit Scrim Result" if is_editing else "📝 Enter New Scrim Result"
            with st.expander(form_title, expanded=is_editing): # Expand form if editing
                with st.form("scrim_form"):
                    
                    scrim_date = st.date_input(
                        "Scrim Date", 
                        value=datetime.strptime(data_to_edit.get('Date'), '%Y-%m-%d') if is_editing and pd.notna(data_to_edit.get('Date')) else datetime.now()
                    )
                    map_name = st.selectbox(
                        "Map", ALL_MAPS, 
                        index=ALL_MAPS.index(data_to_edit.get('Map')) if is_editing and data_to_edit.get('Map') in ALL_MAPS else 0, 
                        help="The map that was played."
                    )
                    opponent_name = st.text_input(
                        "Opponent Name", 
                        value=data_to_edit.get('Opponent', ''), 
                        help="The name of the team you played against."
                    )
                    
                    st.markdown("**Score Breakdown**")
                    c1, c2 = st.columns(2)
                    with c1:
                        our_attack = st.number_input(
                            "Our Attack Rounds", min_value=0, max_value=12, step=1, 
                            value=int(data_to_edit.get('Our Attack', 0)), 
                            help="Your team's rounds won on Attack."
                        )
                        our_defense = st.number_input(
                            "Our Defense Rounds", min_value=0, max_value=12, step=1, 
                            value=int(data_to_edit.get('Our Defense', 0)), 
                            help="Your team's rounds won on Defense."
                        )
                    with c2:
                        opp_attack = st.number_input(
                            "Opponent Attack Rounds", min_value=0, max_value=12, step=1, 
                            value=int(data_to_edit.get('Opponent Attack', 0)), 
                            help="Opponent's rounds won on Attack."
                        )
                        opp_defense = st.number_input(
                            "Opponent Defense Rounds", min_value=0, max_value=12, step=1, 
                            value=int(data_to_edit.get('Opponent Defense', 0)), 
                            help="Opponent's rounds won on Defense."
                        )
                    
                    # --- NEW PLAYER AGENT FORM (USES DYNAMIC ROSTER) ---
                    st.markdown("**Our Composition (Player Agents)**")
                    player_cols = st.columns(5)
                    player_agent_selections = []
                    for i, player in enumerate(st.session_state.team_roster): # --- USE SESSION STATE ROSTER ---
                        with player_cols[i]:
                            selected_agent = st.selectbox(
                                f"{player}", AGENT_OPTIONS, 
                                key=f"scrim_p{i}_{player}", 
                                index=default_agent_indices[i], 
                                help=f"Agent for {player}"
                            )
                            player_agent_selections.append(selected_agent)

                    st.markdown("**Opponent Composition**")
                    opponent_agents_pretty = st.multiselect(
                        "Opponent Agents", OPPONENT_AGENT_OPTIONS, 
                        default=default_opp_agents, 
                        max_selections=5, key="scrim_opp_agents"
                    )
                    
                    vod_link = st.text_input(
                        "VOD Link (Optional)", 
                        value=str(data_to_edit.get('VOD Link', '')) if pd.notna(data_to_edit.get('VOD Link')) else '', 
                        help="Paste a standard YouTube `watch?v=` link for best results."
                    )
                    
                    # --- NEW: Edit/Submit logic ---
                    submit_col, cancel_col = st.columns([1, 5])
                    with submit_col:
                        submitted = st.form_submit_button("Update Match" if is_editing else "Add Scrim")
                    
                    with cancel_col:
                        if is_editing:
                            if st.form_submit_button("Cancel Edit"):
                                st.session_state.editing_scrim_index = None
                                st.rerun()

                    if submitted:
                        # Get clean names from the 5 player dropdowns
                        our_agents_clean = [AGENT_NAME_MAP[agent] for agent in player_agent_selections if agent != ""]
                        # Get clean names from the opponent multiselect
                        opponent_agents = [AGENT_NAME_MAP[agent] for agent in opponent_agents_pretty]

                        if not opponent_name:
                            st.warning("Please enter an opponent's name.")
                        elif len(our_agents_clean) != 5: # Check if all 5 players have an agent
                            st.warning("Please select an agent for all 5 of your players.")
                        elif len(opponent_agents) != 5:
                            st.warning("Please select exactly 5 agents for the opponent.")
                        else:
                            our_final = our_attack + our_defense
                            opp_final = opp_attack + opp_defense
                            
                            if our_final > opp_final: result = "Win"
                            elif our_final < opp_final: result = "Loss"
                            else: result = "Draw"

                            new_data_row = {
                                'Date': scrim_date.strftime('%Y-%m-%d'),
                                'Map': map_name,
                                'Opponent': opponent_name,
                                'Our Attack': our_attack,
                                'Our Defense': our_defense,
                                'Opponent Attack': opp_attack,
                                'Opponent Defense': opp_defense,
                                'Result': result,
                                'Our Agents': ", ".join(sorted(our_agents_clean)), # For analysis charts
                                'Opponent Agents': ", ".join(sorted(opponent_agents)),
                                'VOD Link': vod_link,
                                'P1_Agent': player_agent_selections[0],
                                'P2_Agent': player_agent_selections[1],
                                'P3_Agent': player_agent_selections[2],
                                'P4_Agent': player_agent_selections[3],
                                'P5_Agent': player_agent_selections[4]
                            }

                            if is_editing:
                                # Update existing row
                                for key, value in new_data_row.items():
                                    st.session_state.scrims.loc[st.session_state.editing_scrim_index, key] = value
                                save_data(st.session_state.scrims, "scrims")
                                st.session_state.editing_scrim_index = None
                                st.success("Scrim result updated successfully!")
                                st.rerun()
                            else:
                                # Add new row
                                new_scrim = pd.DataFrame([new_data_row])
                                st.session_state.scrims = pd.concat([st.session_state.scrims, new_scrim], ignore_index=True)
                                save_data(st.session_state.scrims, "scrims")
                                st.success("Scrim result added successfully!")
                                st.rerun() # Rerun to update stats in sidebar
        else:
            st.info("You are logged in as a Player. You have read-only access to match data.")

        st.markdown("---")

    # --- SCRIM VISUALIZATIONS ---
    if not st.session_state.scrims.empty:
        st.header("Scrim Visualizations")
        col1_viz, col2_viz = st.columns(2)

        with col1_viz:
            st.subheader("Map Win Rates")
            map_stats = st.session_state.scrims.groupby('Map')['Result'].value_counts(normalize=True).unstack(fill_value=0)
            if 'Win' in map_stats.columns:
                map_win_rates = map_stats[['Win']].sort_values(by='Win', ascending=False) * 100
                fig = px.bar(map_win_rates, x=map_win_rates.index, y='Win', title="Win % by Map",
                             labels={'Win': 'Win Rate (%)', 'Map': 'Map Name'}, color=map_win_rates.index,
                             color_discrete_sequence=[px.colors.qualitative.Plotly[i] for i in range(len(map_win_rates.index))])
                fig.update_layout(plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font_color='#FAFAFA',
                                  title_font=dict(color='#FFD700'), xaxis=dict(title_font=dict(color='#FFD700')),
                                  yaxis=dict(title_font=dict(color='#FFD700')))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No scrim wins recorded yet to calculate win rates.")

        with col2_viz:
            st.subheader("Match Results Over Time")
            time_df = st.session_state.scrims.copy()
            time_df['Date'] = pd.to_datetime(time_df['Date'])
            time_df['Our Score'] = time_df['Our Attack'].fillna(0) + time_df['Our Defense'].fillna(0)
            time_df['Opponent Score'] = time_df['Opponent Attack'].fillna(0) + time_df['Opponent Defense'].fillna(0)
            time_df = time_df.sort_values('Date')
            
            fig2 = px.line(time_df, x='Date', y=['Our Score', 'Opponent Score'], title="Scores Over Time",
                           labels={'value': 'Score', 'variable': 'Team'}, markers=True)
            fig2.update_layout(plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font_color='#FAFAFA',
                               title_font=dict(color='#FFD700'), xaxis=dict(title_font=dict(color='#FFD700')),
                               yaxis=dict(title_font=dict(color='#FFD700')), legend_title_font=dict(color='#FFD700'))
            st.plotly_chart(fig2, use_container_width=True)
        
        # --- NEW VISUALIZATIONS ---
        st.subheader("Agent & Composition Analysis")
        col3_viz, col4_viz = st.columns(2)
        
        with col3_viz:
            st.subheader("Agent Win Rates")
            # This logic still works because we still save to 'Our Agents'
            agent_data = st.session_state.scrims.dropna(subset=['Our Agents'])
            if not agent_data.empty:
                agent_df = agent_data.assign(Agent=agent_data['Our Agents'].str.split(', ')).explode('Agent')
                agent_stats = agent_df.groupby('Agent')['Result'].value_counts(normalize=True).unstack(fill_value=0)
                
                if 'Win' in agent_stats.columns:
                    agent_win_rates = (agent_stats[['Win']] * 100).sort_values(by='Win', ascending=False)
                    fig3 = px.bar(agent_win_rates, x=agent_win_rates.index, y='Win', title="Win % by Agent",
                                  labels={'Win': 'Win Rate (%)', 'Agent': 'Agent'}, color=agent_win_rates.index)
                    fig3.update_layout(plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font_color='#FAFAFA',
                                       title_font=dict(color='#FFD700'), xaxis=dict(title_font=dict(color='#FFD700')),
                                       yaxis=dict(title_font=dict(color='#FFD700')))
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("Play more games to see agent win rates.")
            else:
                st.info("No agent data recorded to analyze.")
        
        with col4_viz:
            st.subheader("Most Played Compositions")
            # This logic still works because we still save to 'Our Agents'
            comp_data = st.session_state.scrims.dropna(subset=['Our Agents'])
            if not comp_data.empty:
                top_comps = comp_data['Our Agents'].value_counts().head(5)
                fig4 = px.bar(top_comps, y=top_comps.index, x=top_comps.values, title="Top 5 Compositions",
                              labels={'x': 'Times Played', 'y': 'Composition'}, orientation='h')
                fig4.update_layout(plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font_color='#FAFAFA',
                                   title_font=dict(color='#FFD700'), xaxis=dict(title_font=dict(color='#FFD700')),
                                   yaxis=dict(title_font=dict(color='#FFD700'), autorange="reversed"))
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No composition data recorded to analyze.")
    
    # --- SCRIM DETAIL LIST ---
    st.header("Scrim Details & VOD Review")
    if st.session_state.scrims.empty:
        st.warning("No scrim data entered yet. Add a result using the form above.")
    else:
        for index, row in st.session_state.scrims.iloc[::-1].iterrows():
            # BUG FIX: Handle NA values from old data by checking pd.isna
            our_attack = 0 if pd.isna(row['Our Attack']) else row['Our Attack']
            our_defense = 0 if pd.isna(row['Our Defense']) else row['Our Defense']
            opp_attack = 0 if pd.isna(row['Opponent Attack']) else row['Opponent Attack']
            opp_defense = 0 if pd.isna(row['Opponent Defense']) else row['Opponent Defense']
            
            our_final = our_attack + our_defense
            opp_final = opp_attack + opp_defense
            
            result_emoji = "✅" if our_final > opp_final else "❌" if our_final < opp_final else "🤝"
            title = f"{result_emoji}  **{row['Map']} vs {row['Opponent']}** ({int(our_final)} - {int(opp_final)})  |  *{row['Date']}*"
            
            with st.expander(title):
                st.markdown(f"""
                **Score:** {int(our_final)} - {int(opp_final)}
                &nbsp;&nbsp;&nbsp;&nbsp; **Our Attack:** {int(our_attack)} | **Our Defense:** {int(our_defense)}
                &nbsp;&nbsp;&nbsp;&nbsp; **Opponent Attack:** {int(opp_attack)} | **Opponent Defense:** {int(opp_defense)}
                """)
                st.markdown("---")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Our Composition**")
                    # --- NEW DISPLAY LOGIC ---
                    # Check if new player-specific data exists (P1_Agent is not NA)
                    if pd.notna(row.get('P1_Agent')):
                        agent_html = "<div style='line-height: 1.2;'>"
                        player_agents = [
                            (st.session_state.team_roster[0], row['P1_Agent']), # --- USE SESSION STATE ROSTER ---
                            (st.session_state.team_roster[1], row['P2_Agent']),
                            (st.session_state.team_roster[2], row['P3_Agent']),
                            (st.session_state.team_roster[3], row['P4_Agent']),
                            (st.session_state.team_roster[4], row['P5_Agent']),
                        ]
                        
                        for player, agent_pretty_name in player_agents:
                            if pd.notna(agent_pretty_name) and agent_pretty_name != "":
                                # Get clean agent name (e.g., "Jett" from "🔫 Jett")
                                clean_agent_name = AGENT_NAME_MAP.get(agent_pretty_name, agent_pretty_name) 
                                
                                img_filename = AGENT_IMAGE_FILES.get(clean_agent_name)
                                img_base64 = FALLBACK_IMAGE_B64
                                if img_filename:
                                    img_path = os.path.join(AGENT_ICON_PATH, img_filename)
                                    b64_data = get_image_as_base64(img_path)
                                    if b64_data:
                                        img_base64 = f"data:image/png;base64,{b64_data}"
                                
                                agent_html += (
                                    f"<div style='display: inline-block; vertical-align: top; width: 90px; text-align: center; margin: 5px;'>"
                                    f"<img src='{img_base64}' style='width: 64px; height: 64px; border-radius: 8px;' alt='{clean_agent_name}'>"
                                    f"<p class='agent-name'>{clean_agent_name}</p>"
                                    f"<p class='player-name'>{player}</p>" # Add player name
                                    f"</div>"
                                )
                        agent_html += "</div>"
                        st.markdown(agent_html, unsafe_allow_html=True)
                    
                    # Fallback for old data (if P1_Agent is NA but 'Our Agents' exists)
                    elif pd.notna(row['Our Agents']):
                        our_agent_list = row['Our Agents'].split(', ')
                        agent_html = "<div style='line-height: 1.2;'>"
                        for agent_name in our_agent_list:
                            agent_name = agent_name.strip()
                            img_filename = AGENT_IMAGE_FILES.get(agent_name)
                            img_base64 = FALLBACK_IMAGE_B64
                            if img_filename:
                                img_path = os.path.join(AGENT_ICON_PATH, img_filename)
                                b64_data = get_image_as_base64(img_path)
                                if b64_data:
                                    img_base64 = f"data:image/png;base64,{b64_data}"
                            agent_html += (
                                f"<div style='display: inline-block; vertical-align: top; width: 90px; text-align: center; margin: 5px;'>"
                                f"<img src='{img_base64}' style='width: 64px; height: 64px; border-radius: 8px;' alt='{agent_name}'>"
                                f"<p class='agent-name'>{agent_name}</p>"
                                f"</div>"
                            )
                        agent_html += "</div>"
                        st.markdown(agent_html, unsafe_allow_html=True)
                    else:
                        st.info("No agent data recorded for this match.")
                        
                with col2:
                    st.markdown("**Opponent Composition**")
                    if pd.notna(row['Opponent Agents']):
                        opp_agent_list = row['Opponent Agents'].split(', ')
                        agent_html = "<div style='line-height: 1.2;'>"
                        for agent_name in opp_agent_list:
                            agent_name = agent_name.strip()
                            img_filename = AGENT_IMAGE_FILES.get(agent_name)
                            img_base64 = FALLBACK_IMAGE_B64
                            if img_filename:
                                img_path = os.path.join(AGENT_ICON_PATH, img_filename)
                                b64_data = get_image_as_base64(img_path)
                                if b64_data:
                                    img_base64 = f"data:image/png;base64,{b64_data}"
                            agent_html += (
                                f"<div style='display: inline-block; vertical-align: top; width: 90px; text-align: center; margin: 5px;'>"
                                f"<img src='{img_base64}' style='width: 64px; height: 64px; border-radius: 8px;' alt='{agent_name}'>"
                                f"<p class='agent-name'>{agent_name}</p>"
                                f"</div>"
                            )
                        agent_html += "</div>"
                        st.markdown(agent_html, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("**VOD Review**")
                if pd.notna(row['VOD Link']) and row['VOD Link'].strip():
                    try:
                        st.video(row['VOD Link'])
                    except Exception as e:
                        st.error(f"Could not load video. Make sure it's a valid `watch?v=` link. Error: {e}")
                else:
                    st.info("No VOD link was provided for this match.")

    # --- Delete scrim section (ROLE-BASED) ---
    if st.session_state.user_role in ["Manager", "Coach"]:
        st.markdown("---")
        st.header("Manage Scrim Data")
        if not st.session_state.scrims.empty:
            # Update delete options to show new score format
            scrim_options = []
            for index, row in st.session_state.scrims.iterrows():
                # BUG FIX: Handle NA values
                our_final = (0 if pd.isna(row['Our Attack']) else row['Our Attack']) + (0 if pd.isna(row['Our Defense']) else row['Our Defense'])
                opp_final = (0 if pd.isna(row['Opponent Attack']) else row['Opponent Attack']) + (0 if pd.isna(row['Opponent Defense']) else row['Opponent Defense'])
                scrim_options.append(f"{row['Date']} - {row['Opponent']} on {row['Map']} ({int(our_final)}-{int(opp_final)})")
                
            scrim_to_manage = st.selectbox(
                "Select scrim to manage", 
                options=[""] + scrim_options, 
                index=0, 
                placeholder="Choose a scrim..."
            )
            
            manage_cols = st.columns(2)
            with manage_cols[0]:
                if st.button("Delete Selected Scrim", type="primary", use_container_width=True):
                    if scrim_to_manage:
                        delete_index = get_index_from_string(scrim_to_manage, st.session_state.scrims, "Scrims")
                        if delete_index is not None:
                            st.session_state.scrims = st.session_state.scrims.drop(delete_index).reset_index(drop=True)
                            save_data(st.session_state.scrims, "scrims")
                            st.success(f"Deleted scrim: {scrim_to_manage}")
                            st.rerun()
                    else:
                        st.warning("Please select a scrim to delete.")

            with manage_cols[1]:
                if st.button("Edit Selected Scrim", use_container_width=True):
                    if scrim_to_manage:
                        edit_index = get_index_from_string(scrim_to_manage, st.session_state.scrims, "Scrims")
                        if edit_index is not None:
                            st.session_state.editing_scrim_index = edit_index
                            st.rerun()
                    else:
                        st.warning("Please select a scrim to edit.")
        else:
            st.write("No scrims to delete.")

    # --- ================================== ---
    # ---     TOURNAMENT PAGE CONTENT        ---
    # --- ================================== ---
    elif st.session_state.page == "Tournaments":
        st.title(f"{st.session_state.org_name} - Tournament Dashboard")
        st.info("Add official tournament match results here to track competitive performance.")
        st.markdown("---")

        # --- Check if we are in editing mode ---
        is_editing_tourney = st.session_state.editing_tournament_index is not None
        data_to_edit_tourney = {}
        default_agent_indices_tourney = [0] * 5
        default_opp_agents_tourney = []
        default_map_index = 0
        default_match_type_index = 0

        if is_editing_tourney:
            st.info("You are currently editing a match. Click 'Update Match' to save or 'Cancel Edit' to discard.")
            data_row = st.session_state.tournaments.loc[st.session_state.editing_tournament_index]
            data_to_edit_tourney = data_row.to_dict()
            
            # Pre-fill player agents
            for i in range(5):
                player_agent = data_row.get(f'P{i+1}_Agent')
                if pd.notna(player_agent) and player_agent in AGENT_OPTIONS:
                    default_agent_indices_tourney[i] = AGENT_OPTIONS.index(player_agent)
            
            # Pre-fill opponent agents
            if pd.notna(data_row.get('Opponent Agents')):
                opp_agents_clean = data_row['Opponent Agents'].split(', ')
                default_opp_agents_tourney = [AGENT_ROLE_MAP.get(agent) for agent in opp_agents_clean if AGENT_ROLE_MAP.get(agent) in OPPONENT_AGENT_OPTIONS]
            
            # Pre-fill map and match type
            if data_to_edit_tourney.get('Map') in ALL_MAPS:
                default_map_index = ALL_MAPS.index(data_to_edit_tourney['Map'])
            
            match_types = ["BO1", "BO3", "BO5"]
            if data_to_edit_tourney.get('Match Type') in match_types:
                default_match_type_index = match_types.index(data_to_edit_tourney['Match Type'])


        # --- Tournament form (ROLE-BASED) ---
        if st.session_state.user_role in ["Manager", "Coach"]:
            form_title_tourney = "🏆 Edit Tournament Result" if is_editing_tourney else "🏆 Enter New Tournament Result"
            with st.expander(form_title_tourney, expanded=is_editing_tourney):
                with st.form("tournament_form"):
                    
                    c_form_1, c_form_2 = st.columns(2)
                    with c_form_1:
                        tournament_name = st.text_input(
                            "Tournament Name", 
                            value=data_to_edit_tourney.get('Tournament Name', ''),
                            help="The name of the tournament (e.g., 'VCT Qualifiers')"
                        )
                        match_date = st.date_input(
                            "Match Date",
                            value=datetime.strptime(data_to_edit_tourney.get('Date'), '%Y-%m-%d') if is_editing_tourney and pd.notna(data_to_edit_tourney.get('Date')) else datetime.now()
                        )
                        map_name = st.selectbox(
                            "Map", ALL_MAPS, 
                            index=default_map_index, 
                            help="The map that was played."
                        )

                    with c_form_2:
                        match_type = st.selectbox(
                            "Match Type", ["BO1", "BO3", "BO5"], 
                            index=default_match_type_index, 
                            help="Best-of-series type."
                        )
                        opponent_name = st.text_input(
                            "Opponent Name", 
                            value=data_to_edit_tourney.get('Opponent', ''),
                            help="The name of the team you played against."
                        )
                    
                    st.markdown("**Score Breakdown**")
                    c1, c2 = st.columns(2)
                    with c1:
                        our_attack = st.number_input(
                            "Our Attack Rounds", min_value=0, max_value=12, step=1, 
                            value=int(data_to_edit_tourney.get('Our Attack', 0)), 
                            help="Your team's rounds won on Attack."
                        )
                        our_defense = st.number_input(
                            "Our Defense Rounds", min_value=0, max_value=12, step=1, 
                            value=int(data_to_edit_tourney.get('Our Defense', 0)), 
                            help="Your team's rounds won on Defense."
                        )
                    with c2:
                        opp_attack = st.number_input(
                            "Opponent Attack Rounds", min_value=0, max_value=12, step=1, 
                            value=int(data_to_edit_tourney.get('Opponent Attack', 0)), 
                            help="Opponent's rounds won on Attack."
                        )
                        opp_defense = st.number_input(
                            "Opponent Defense Rounds", min_value=0, max_value=12, step=1, 
                            value=int(data_to_edit_tourney.get('Opponent Defense', 0)), 
                            help="Opponent's rounds won on Defense."
                        )
                    
                    # --- NEW PLAYER AGENT FORM (USES DYNAMIC ROSTER) ---
                    st.markdown("**Our Composition (Player Agents)**")
                    player_cols = st.columns(5)
                    player_agent_selections = []
                    for i, player in enumerate(st.session_state.team_roster): # --- USE SESSION STATE ROSTER ---
                        with player_cols[i]:
                            selected_agent = st.selectbox(
                                f"{player}", AGENT_OPTIONS, 
                                key=f"tourney_p{i}_{player}", 
                                index=default_agent_indices_tourney[i], 
                                help=f"Agent for {player}"
                            )
                            player_agent_selections.append(selected_agent)

                    st.markdown("**Opponent Composition**")
                    opponent_agents_pretty = st.multiselect(
                        "Opponent Agents", OPPONENT_AGENT_OPTIONS, 
                        default=default_opp_agents_tourney, 
                        max_selections=5, key="tourney_opp_agents"
                    )
                    
                    vod_link = st.text_input(
                        "VOD Link (Optional)", 
                        value=str(data_to_edit_tourney.get('VOD Link', '')) if pd.notna(data_to_edit_tourney.get('VOD Link')) else '',
                        help="Paste a standard YouTube `watch?v=` link for best results."
                    )

                    # --- NEW: Edit/Submit logic ---
                    submit_col, cancel_col = st.columns([1, 5])
                    with submit_col:
                        submitted = st.form_submit_button("Update Match" if is_editing_tourney else "Add Tournament Match")

                    with cancel_col:
                        if is_editing_tourney:
                            if st.form_submit_button("Cancel Edit"):
                                st.session_state.editing_tournament_index = None
                                st.rerun()

                    if submitted:
                        # Get clean names from the 5 player dropdowns
                        our_agents_clean = [AGENT_NAME_MAP[agent] for agent in player_agent_selections if agent != ""]
                        # Get clean names from the opponent multiselect
                        opponent_agents = [AGENT_NAME_MAP[agent] for agent in opponent_agents_pretty]

                        if not opponent_name or not tournament_name:
                            st.warning("Please enter a tournament name and an opponent's name.")
                        elif len(our_agents_clean) != 5: # Check if all 5 players have an agent
                            st.warning("Please select an agent for all 5 of your players.")
                        elif len(opponent_agents) != 5:
                            st.warning("Please select exactly 5 agents for the opponent.")
                        else:
                            our_final = our_attack + our_defense
                            opp_final = opp_attack + opp_defense
                            
                            if our_final > opp_final: result = "Win"
                            elif our_final < opp_final: result = "Loss"
                            else: result = "Draw"

                            new_match_data = {
                                'Date': match_date.strftime('%Y-%m-%d'),
                                'Tournament Name': tournament_name,
                                'Match Type': match_type,
                                'Map': map_name,
                                'Opponent': opponent_name,
                                'Our Attack': our_attack,
                                'Our Defense': our_defense,
                                'Opponent Attack': opp_attack,
                                'Opponent Defense': opp_defense,
                                'Result': result,
                                'Our Agents': ", ".join(sorted(our_agents_clean)), # For analysis charts
                                'Opponent Agents': ", ".join(sorted(opponent_agents)),
                                'VOD Link': vod_link,
                                'P1_Agent': player_agent_selections[0],
                                'P2_Agent': player_agent_selections[1],
                                'P3_Agent': player_agent_selections[2],
                                'P4_Agent': player_agent_selections[3],
                                'P5_Agent': player_agent_selections[4]
                            }

                            if is_editing_tourney:
                                for key, value in new_match_data.items():
                                    st.session_state.tournaments.loc[st.session_state.editing_tournament_index, key] = value
                                save_data(st.session_state.tournaments, "tournaments.csv")
                                st.session_state.editing_tournament_index = None
                                st.success("Tournament match updated successfully!")
                                st.rerun()
                            else:
                                new_match = pd.DataFrame([new_match_data])
                                st.session_state.tournaments = pd.concat([st.session_state.tournaments, new_match], ignore_index=True)
                                save_data(st.session_state.tournaments, "tournaments.csv")
                                st.success("Tournament match added successfully!")
                                st.rerun() # Rerun to update stats in sidebar
        else:
            st.info("You are logged in as a Player. You have read-only access to match data.")
            
        st.markdown("---")

    # --- TOURNAMENT VISUALIZATIONS ---
    if not st.session_state.tournaments.empty:
        st.header("Tournament Visualizations")
        col1_viz, col2_viz = st.columns(2)

        with col1_viz:
            st.subheader("Map Win Rates")
            map_stats = st.session_state.tournaments.groupby('Map')['Result'].value_counts(normalize=True).unstack(fill_value=0)
            if 'Win' in map_stats.columns:
                map_win_rates = map_stats[['Win']].sort_values(by='Win', ascending=False) * 100
                fig = px.bar(map_win_rates, x=map_win_rates.index, y='Win', title="Win % by Map (Tournaments)",
                             labels={'Win': 'Win Rate (%)', 'Map': 'Map Name'}, color=map_win_rates.index,
                             color_discrete_sequence=[px.colors.qualitative.Plotly[i] for i in range(len(map_win_rates.index))])
                fig.update_layout(plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font_color='#FAFAFA',
                                  title_font=dict(color='#FFD700'), xaxis=dict(title_font=dict(color='#FFD700')),
                                  yaxis=dict(title_font=dict(color='#FFD700')))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No tournament wins recorded yet to calculate win rates.")

        with col2_viz:
            st.subheader("Match Results Over Time")
            time_df = st.session_state.tournaments.copy()
            time_df['Date'] = pd.to_datetime(time_df['Date'])
            time_df['Our Score'] = time_df['Our Attack'].fillna(0) + time_df['Our Defense'].fillna(0)
            time_df['Opponent Score'] = time_df['Opponent Attack'].fillna(0) + time_df['Opponent Defense'].fillna(0)
            time_df = time_df.sort_values('Date')
            
            fig2 = px.line(time_df, x='Date', y=['Our Score', 'Opponent Score'], title="Scores Over Time (Tournaments)",
                           labels={'value': 'Score', 'variable': 'Team'}, markers=True)
            fig2.update_layout(plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font_color='#FAFAFA',
                               title_font=dict(color='#FFD700'), xaxis=dict(title_font=dict(color='#FFD700')),
                               yaxis=dict(title_font=dict(color='#FFD700')), legend_title_font=dict(color='#FFD700'))
            st.plotly_chart(fig2, use_container_width=True)
        
        # --- NEW VISUALIZATIONS ---
        st.subheader("Agent & Composition Analysis")
        col3_viz, col4_viz = st.columns(2)
        
        with col3_viz:
            st.subheader("Agent Win Rates")
            agent_data = st.session_state.tournaments.dropna(subset=['Our Agents'])
            if not agent_data.empty:
                agent_df = agent_data.assign(Agent=agent_data['Our Agents'].str.split(', ')).explode('Agent')
                agent_stats = agent_df.groupby('Agent')['Result'].value_counts(normalize=True).unstack(fill_value=0)
                
                if 'Win' in agent_stats.columns:
                    agent_win_rates = (agent_stats[['Win']] * 100).sort_values(by='Win', ascending=False)
                    fig3 = px.bar(agent_win_rates, x=agent_win_rates.index, y='Win', title="Win % by Agent (Tournaments)",
                                  labels={'Win': 'Win Rate (%)', 'Agent': 'Agent'}, color=agent_win_rates.index)
                    fig3.update_layout(plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font_color='#FAFAFA',
                                       title_font=dict(color='#FFD700'), xaxis=dict(title_font=dict(color='#FFD700')),
                                       yaxis=dict(title_font=dict(color='#FFD700')))
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("Play more games to see agent win rates.")
            else:
                st.info("No agent data recorded to analyze.")
        
        with col4_viz:
            st.subheader("Most Played Compositions")
            comp_data = st.session_state.tournaments.dropna(subset=['Our Agents'])
            if not comp_data.empty:
                top_comps = comp_data['Our Agents'].value_counts().head(5)
                fig4 = px.bar(top_comps, y=top_comps.index, x=top_comps.values, title="Top 5 Compositions (Tournaments)",
                              labels={'x': 'Times Played', 'y': 'Composition'}, orientation='h')
                fig4.update_layout(plot_bgcolor='#1a1a1a', paper_bgcolor='#1a1a1a', font_color='#FAFAFA',
                                   title_font=dict(color='#FFD700'), xaxis=dict(title_font=dict(color='#FFD700')),
                                   yaxis=dict(title_font=dict(color='#FFD700'), autorange="reversed"))
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No composition data recorded to analyze.")

    
    # --- TOURNAMENT DETAIL LIST (NEW GROUPING LOGIC) ---
    st.header("Tournament Match Details & VOD Review")
    if st.session_state.tournaments.empty:
        st.warning("No tournament data entered yet. Add a result using the form above.")
    else:
        # Group by series (Date, Tournament, Opponent, Match Type)
        # Sort by date first to get recent series on top
        df_tournaments = st.session_state.tournaments.sort_values(by='Date', ascending=False)
        
        # Define the grouping keys
        group_keys = ['Date', 'Tournament Name', 'Opponent', 'Match Type']
        
        # Group the DataFrame
        grouped = df_tournaments.groupby(group_keys)
        
        # Iterate over each group (each series)
        for (date, t_name, opponent, m_type), group_df in grouped:
            
            # Calculate series score
            series_wins = (group_df['Result'] == 'Win').sum()
            series_losses = (group_df['Result'] == 'Loss').sum()

            # Determine overall series result
            if series_wins > series_losses:
                series_result_emoji = "✅"
            elif series_losses > series_wins:
                series_result_emoji = "❌"
            else:
                # This handles 0-0 or 1-1 draws in a series
                series_result_emoji = "🤝"

            series_title = f"{series_result_emoji} **{t_name} ({m_type}) vs {opponent}** | Series Score: {series_wins}-{series_losses} | *{date}*"
            
            with st.expander(series_title):
                # Now iterate over each map *within* this series
                for index, row in group_df.iterrows():
                    map_result_emoji = "✅" if row['Result'] == 'Win' else "❌" if row['Result'] == 'Loss' else "🤝"
                    # BUG FIX: Handle NA values
                    our_attack = 0 if pd.isna(row['Our Attack']) else row['Our Attack']
                    our_defense = 0 if pd.isna(row['Our Defense']) else row['Our Defense']
                    opp_attack = 0 if pd.isna(row['Opponent Attack']) else row['Opponent Attack']
                    opp_defense = 0 if pd.isna(row['Opponent Defense']) else row['Opponent Defense']

                    our_final_map_score = our_attack + our_defense
                    opp_final_map_score = opp_attack + opp_defense

                    st.markdown(f"<p class='map-subheader'>{map_result_emoji} Map: {row['Map']} ({int(our_final_map_score)} - {int(opp_final_map_score)})</p>", unsafe_allow_html=True)
                    st.markdown(f"""
                    &nbsp;&nbsp;&nbsp;&nbsp; **Our Attack:** {int(our_attack)} | **Our Defense:** {int(our_defense)}
                    &nbsp;&nbsp;&nbsp;&nbsp; **Opponent Attack:** {int(opp_attack)} | **Opponent Defense:** {int(opp_defense)}
                    """)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Our Composition**")
                        # --- NEW DISPLAY LOGIC ---
                        # Check if new player-specific data exists (P1_Agent is not NA)
                        if pd.notna(row.get('P1_Agent')):
                            agent_html = "<div style='line-height: 1.2;'>"
                            player_agents = [
                                (st.session_state.team_roster[0], row['P1_Agent']), # --- USE SESSION STATE ROSTER ---
                                (st.session_state.team_roster[1], row['P2_Agent']),
                                (st.session_state.team_roster[2], row['P3_Agent']),
                                (st.session_state.team_roster[3], row['P4_Agent']),
                                (st.session_state.team_roster[4], row['P5_Agent']),
                            ]
                            
                            for player, agent_pretty_name in player_agents:
                                if pd.notna(agent_pretty_name) and agent_pretty_name != "":
                                    # Get clean agent name (e.g., "Jett" from "🔫 Jett")
                                    clean_agent_name = AGENT_NAME_MAP.get(agent_pretty_name, agent_pretty_name) 
                                    
                                    img_filename = AGENT_IMAGE_FILES.get(clean_agent_name)
                                    img_base64 = FALLBACK_IMAGE_B64
                                    if img_filename:
                                        img_path = os.path.join(AGENT_ICON_PATH, img_filename)
                                        b64_data = get_image_as_base64(img_path)
                                        if b64_data:
                                            img_base64 = f"data:image/png;base64,{b64_data}"
                                    
                                    agent_html += (
                                        f"<div style='display: inline-block; vertical-align: top; width: 90px; text-align: center; margin: 5px;'>"
                                        f"<img src='{img_base64}' style='width: 64px; height: 64px; border-radius: 8px;' alt='{clean_agent_name}'>"
                                        f"<p class='agent-name'>{clean_agent_name}</p>"
                                        f"<p class='player-name'>{player}</p>" # Add player name
                                        f"</div>"
                                    )
                            agent_html += "</div>"
                            st.markdown(agent_html, unsafe_allow_html=True)
                        
                        # Fallback for old data (if P1_Agent is NA but 'Our Agents' exists)
                        elif pd.notna(row['Our Agents']):
                            our_agent_list = row['Our Agents'].split(', ')
                            agent_html = "<div style='line-height: 1.2;'>"
                            for agent_name in our_agent_list:
                                agent_name = agent_name.strip()
                                img_filename = AGENT_IMAGE_FILES.get(agent_name)
                                img_base64 = FALLBACK_IMAGE_B64
                                if img_filename:
                                    img_path = os.path.join(AGENT_ICON_PATH, img_filename)
                                    b64_data = get_image_as_base64(img_path)
                                    if b64_data:
                                        img_base64 = f"data:image/png;base64,{b64_data}"
                                agent_html += (
                                    f"<div style='display: inline-block; vertical-align: top; width: 90px; text-align: center; margin: 5px;'>"
                                    f"<img src='{img_base64}' style='width: 64px; height: 64px; border-radius: 8px;' alt='{agent_name}'>"
                                    f"<p class='agent-name'>{agent_name}</p>"
                                    f"</div>"
                                )
                            agent_html += "</div>"
                            st.markdown(agent_html, unsafe_allow_html=True)
                        else:
                            st.info("No agent data recorded for this match.")
                            
                    with col2:
                        st.markdown("**Opponent Composition**")
                        if pd.notna(row['Opponent Agents']):
                            opp_agent_list = row['Opponent Agents'].split(', ')
                            agent_html = "<div style='line-height: 1.2;'>"
                            for agent_name in opp_agent_list:
                                agent_name = agent_name.strip()
                                img_filename = AGENT_IMAGE_FILES.get(agent_name)
                                img_base64 = FALLBACK_IMAGE_B64
                                if img_filename:
                                    img_path = os.path.join(AGENT_ICON_PATH, img_filename)
                                    b64_data = get_image_as_base64(img_path)
                                    if b64_data:
                                        img_base64 = f"data:image/png;base64,{b64_data}"
                                agent_html += (
                                    f"<div style='display: inline-block; vertical-align: top; width: 90px; text-align: center; margin: 5px;'>"
                                    f"<img src='{img_base64}' style='width: 64px; height: 64px; border-radius: 8px;' alt='{agent_name}'>"
                                    f"<p class='agent-name'>{agent_name}</p>"
                                    f"</div>"
                                )
                            agent_html += "</div>"
                            st.markdown(agent_html, unsafe_allow_html=True)
                    
                    st.markdown("**VOD Review**")
                    if pd.notna(row['VOD Link']) and row['VOD Link'].strip():
                        try:
                            st.video(row['VOD Link'])
                        except Exception as e:
                            st.error(f"Could not load video. Make sure it's a valid `watch?v=` link. Error: {e}")
                    else:
                        st.info("No VOD link was provided for this map.")
                    st.markdown("---") # Separator between maps in the same series


    # --- Delete tournament match section (ROLE-BASED) ---
    if st.session_state.user_role in ["Manager", "Coach"]:
        st.markdown("---")
        st.header("Manage Tournament Data")
        if not st.session_state.tournaments.empty:
            # Deleting is still map-by-map, which is good for correcting single-map errors
            tournament_options = []
            for index, row in st.session_state.tournaments.iterrows():
                # BUG FIX: Handle NA values
                our_final = (0 if pd.isna(row['Our Attack']) else row['Our Attack']) + (0 if pd.isna(row['Our Defense']) else row['Our Defense'])
                opp_final = (0 if pd.isna(row['Opponent Attack']) else row['Opponent Attack']) + (0 if pd.isna(row['Opponent Defense']) else row['Opponent Defense'])
                tournament_options.append(f"Map: {row['Map']} ({row['Date']}) - {row.get('Tournament Name', 'N/A')} ({row.get('Match Type', 'N/A')}) vs {row['Opponent']} ({int(our_final)}-{int(opp_final)})")
            
            match_to_manage = st.selectbox(
                "Select match to manage", 
                options=[""] + tournament_options, 
                index=0, 
                placeholder="Choose a specific map to delete..."
            )
            
            manage_cols = st.columns(2)
            with manage_cols[0]:
                if st.button("Delete Selected Match", type="primary", use_container_width=True):
                    if match_to_manage:
                        delete_index = get_index_from_string(match_to_manage, st.session_state.tournaments, "Tournaments")
                        if delete_index is not None:
                            st.session_state.tournaments = st.session_state.tournaments.drop(delete_index).reset_index(drop=True)
                            save_data(st.session_state.tournaments, "tournaments.csv")
                            st.success(f"Deleted match: {match_to_manage}")
                            st.rerun()
                    else:
                        st.warning("Please select a match to delete.")

            with manage_cols[1]:
                if st.button("Edit Selected Match", use_container_width=True):
                    if match_to_manage:
                        edit_index = get_index_from_string(match_to_manage, st.session_state.tournaments, "Tournaments")
                        if edit_index is not None:
                            st.session_state.editing_tournament_index = edit_index
                            st.rerun()
                    else:
                        st.warning("Please select a match to edit.")
        else:
            st.write("No tournament matches to delete.")

    # --- ================================== ---
    # ---     NEW TEAM ROSTER PAGE           ---
    # --- ================================== ---
    elif st.session_state.page == "Admin Panel":
        st.title("Admin Panel")
        
        # This page is only for Manager/Coach, but we check again just in case
        if st.session_state.user_role in ["Manager", "Coach"]:
            
            admin_tabs = st.tabs(["Manage Roster", "Manage Team Members"])

            with admin_tabs[0]:
                st.subheader("Manage Team Roster")
                st.info(f"Edit your 5-player roster for **{st.session_state.org_name}**. This will update the names in the data entry forms.")
                
                with st.form("roster_form"):
                    current_roster = st.session_state.team_roster
                    new_roster = []
                    
                    # Create 5 text inputs
                    for i in range(5):
                        player_name = st.text_input(
                            f"Player {i+1}", 
                            value=current_roster[i] if i < len(current_roster) else f"Player{i+1}"
                        )
                        new_roster.append(player_name)
                    
                    submitted = st.form_submit_button("Save Roster")
                    if submitted:
                        # Validate non-empty names
                        if any(name.strip() == "" for name in new_roster):
                            st.warning("Player names cannot be empty.")
                        else:
                            st.session_state.team_roster = new_roster
                            save_roster(new_roster)
                            st.success("Roster updated successfully!")
                            st.rerun() # To show changes immediately

            with admin_tabs[1]:
                st.subheader("Manage Team Members")
                st.info("Create new accounts for your Coaches and Players.")
                
                with st.form("new_user_form", clear_on_submit=True):
                    new_username = st.text_input("New User's Username").lower()
                    new_password = st.text_input("New User's Password", type="password")
                    new_role = st.selectbox("Assign Role", ["Coach", "Player"])
                    
                    submitted = st.form_submit_button("Create User")
                    if submitted:
                        if not new_username or not new_password:
                            st.warning("Username and password are required.")
                        elif new_username in st.session_state.db['users']:
                            st.error(f"Username '{new_username}' already exists.")
                        else:
                            # Add new user to our demo DB
                            st.session_state.db['users'][new_username] = {
                                "password": new_password,
                                "role": new_role,
                                "org_id": st.session_state.org_id # Assign to *your* org
                            }
                            st.success(f"User '{new_username}' created as a {new_role}.")
                            
                st.markdown("---")
                st.subheader(f"Current Team Members ({st.session_state.org_name})")
                
                # Display current members of *your* org
                current_members = []
                for username, details in st.session_state.db['users'].items():
                    if details['org_id'] == st.session_state.org_id:
                        current_members.append({
                            "Username": username,
                            "Role": details['role']
                        })
                
                st.dataframe(pd.DataFrame(current_members), use_container_width=True)

        else:
            st.error("You do not have permission to view this page.")