import pandas as pd
import logging
import colorlog
import json
import streamlit as st
from itertools import combinations

# --- Initial Setup and Configuration ---

# Configure logger for better feedback in the console
def setup_logger():
    """Sets up a colored logger."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = colorlog.ColoredFormatter(
            '%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()

# --- Default Data and Weights ---

# Default weights and configurations
DEFAULT_WEIGHTS = {
    "BST": 1.0,
    "Artifice": 1.0,
}

ARCHETYPE_WEIGHTS = {
    "Bulwark": 0.7, "Brawler": 1.6, "Gunner": 1.1,
    "Specialist": 1.6, "Grenadier": 1.8, "Paragon": 1.6,
}

TIER_WEIGHTS = {
    "Tier 1": {"low": 1.0, "high": 1.05}, "Tier 2": {"low": 1.1, "high": 1.15},
    "Tier 3": {"low": 1.2, "high": 1.25}, "Tier 4": {"low": 1.3, "high": 1.35},
    "Tier 5": {"low": 1.5, "high": 1.55},
}

ILLEGAL_COMBO_WEIGHTS = {
    ("Grenade (Base)", "Health (Base)"): 1.5, ("Health (Base)", "Super (Base)"): 1.5,
    ("Health (Base)", "Weapons (Base)"): 1.8, ("Grenade (Base)", "Melee (Base)"): 2.0,
    ("Melee (Base)", "Super (Base)"): 2.0, ("Class (Base)", "Melee (Base)"): 2.0,
    ("Class (Base)", "Grenade (Base)"): 1.5, ("Class (Base)", "Super (Base)"): 1.5,
    ("Super (Base)", "Weapons (Base)"): 1.8,
}

ARCHETYPES = {
    "Brawler": {"Primary": "Melee (Base)", "Secondary": "Health (Base)"},
    "Gunner": {"Primary": "Weapons (Base)", "Secondary": "Grenade (Base)"},
    "Specialist": {"Primary": "Class (Base)", "Secondary": "Weapons (Base)"},
    "Grenadier": {"Primary": "Grenade (Base)", "Secondary": "Super (Base)"},
    "Paragon": {"Primary": "Weapons (Base)", "Secondary": "Melee (Base)"},
    "Bulwark": {"Primary": "Health (Base)", "Secondary": "Class (Base)"},
}

TIERS = {
    "Tier 1": [52, 57], "Tier 2": [58, 63], "Tier 3": [64, 69],
    "Tier 4": [70, 75], "Tier 5": [75, 81],
}

STATS = ['Health (Base)', 'Melee (Base)', 'Grenade (Base)', 'Super (Base)', 'Class (Base)', 'Weapons (Base)']

# --- Core Logic ---

def initialize_session_state():
    """Initializes session state for all weights if they don't exist."""
    if 'weights_initialized' not in st.session_state:
        st.session_state.weights = DEFAULT_WEIGHTS.copy()
        st.session_state.archetype_weights = ARCHETYPE_WEIGHTS.copy()
        st.session_state.tier_weights = {
            tier: {**values, 'enabled': True} for tier, values in TIER_WEIGHTS.items()
        }
        st.session_state.illegal_combo_weights = ILLEGAL_COMBO_WEIGHTS.copy()
        st.session_state.weights_initialized = True

@st.cache_data
def load_data(uploaded_file):
    """Loads armor data from a user-uploaded CSV file."""
    try:
        df = pd.read_csv(uploaded_file)
        logger.info("Armor data loaded successfully!")
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        logger.error(f"An error occurred while loading data: {e}")
        return None

def calculate_armor_weight(armor_piece, weights, archetype_weights, tier_weights, illegal_combo_weights):
    """Calculates the weight of an armor piece based on defined criteria."""
    weight = 0
    logger.debug(f"Processing armor piece: {armor_piece['Name']} ({armor_piece['Id']})")

    # 1. Total Stats
    bst_weight = armor_piece.get("Total (Base)", 0) * weights.get("BST", 1.0)
    weight += bst_weight
    logger.debug(f"  - BST Weight: {bst_weight:.2f}. Current Total: {weight:.2f}")

    # 2. Artifice Slot
    if armor_piece.get("Artifice", False):
        weight += weights.get("Artifice", 1.0)
        logger.debug(f"  - Artifice Bonus: {weights.get('Artifice', 1.0)}. Current Total: {weight:.2f}")

    # 3. Tier-specific logic
    tier = armor_piece.get('Tier', 0)
    if tier == 0: # Armor 2.0
        armor_stat_combinations = list(combinations(STATS, 2))
        for combo in armor_stat_combinations:
            sorted_combo = tuple(sorted(combo))
            if sorted_combo in illegal_combo_weights and armor_piece.get(combo[0], 0) > 15 and armor_piece.get(combo[1], 0) > 15:
                combo_weight = illegal_combo_weights[sorted_combo]
                weight += combo_weight
                logger.debug(f"  - Illegal Combo Bonus: {combo_weight:.2f} for {sorted_combo}. Current Total: {weight:.2f}")
    elif tier in [1, 2, 3, 4, 5]:
        tier_name = f"Tier {tier}"
        if tier_name in tier_weights and tier_name in TIERS:
            min_stat, max_stat = TIERS[tier_name]
            midpoint = (min_stat + max_stat) / 2
            armor_total_base = armor_piece.get("Total (Base)", 0)
            tier_weight_config = tier_weights[tier_name]
            tier_weight_bonus = tier_weight_config["high"] if armor_total_base >= midpoint else tier_weight_config["low"]
            weight += tier_weight_bonus
            logger.debug(f"  - Tier Bonus: {tier_weight_bonus:.2f} for {tier_name}. Current Total: {weight:.2f}")

    # 4. Specific Stat Spikes
    if armor_piece.get("Total (Base)", 0) > 0:
        sorted_stats = armor_piece[STATS].sort_values(ascending=False)
        top_two_stats_names = tuple(sorted(sorted_stats.index[:2].tolist()))

        matching_archetype = next((name for name, pair in ARCHETYPES.items() if tuple(sorted([pair["Primary"], pair["Secondary"]])) == top_two_stats_names), None)

        other_stats_avg = sorted_stats[2:].mean()
        spike_threshold = 10

        if (sorted_stats[:2] > other_stats_avg + spike_threshold).all():
            if matching_archetype and matching_archetype in archetype_weights:
                spike_bonus = archetype_weights[matching_archetype]
                weight += spike_bonus
                logger.debug(f"  - Archetype Spike Bonus: {spike_bonus:.2f} for {matching_archetype}. Current Total: {weight:.2f}")

    logger.info(f"Final weight for {armor_piece['Name']} ({armor_piece['Id']}): {weight:.2f}")
    return weight

# --- Streamlit UI ---
def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Destiny 2 Armor Analyzer", layout="wide")
    initialize_session_state()

    st.title("Destiny 2 Armor Analyzer 🛡️")
    st.write("Upload your `destiny-armor.csv` file and adjust the weights to rank your armor pieces.")
    st.write("To get your `destiny-armor.csv` download from DIM")

    # ADDED: Explanation section
    with st.expander("How is the Armor Weight Calculated?"):
        st.markdown("""
        The final **Armor Weight** is a score calculated by combining a base value with several potential bonuses. Here’s the breakdown:

        - **1. Base Stat Total (BST):** The foundation of the score. Every point in the armor's base total contributes to the weight, scaled by the "BST Weight" slider in the sidebar.
        
        - **2. Artifice Bonus:** A flat bonus is added if the armor is an Artifice piece (assuming an 'Artifice' column exists and is marked true).
        
        - **3. Tier Bonus:** For armor in Tiers 1-5, a bonus is applied based on its total stats. This bonus is higher for pieces in the upper half of their stat range for that tier (e.g., a 68-stat roll gets a higher bonus than a 64). You can enable or disable this bonus for each tier individually.

        - **4. Archetype Spike Bonus:** If an armor piece has significant spikes in two specific stats that match a defined "Archetype" (like Brawler or Grenadier), it gets a bonus. This rewards specialized armor that's good for specific builds.

        - **5. Illegal Combo Bonus (Tier 0 Only):** Older "Armor 2.0" pieces (which are considered Tier 0) can get a bonus if they have high values (>15) in two stats that are normally in different pools (e.g., Grenade and Melee). This helps identify rare and valuable legacy armor.

        All these values are added together to create the final `Armor_Weight`, which you can use to sort and rank your gear.
        """)

    # --- Sidebar for Controls ---
    with st.sidebar:
        st.header("⚙️ Controls")
        uploaded_file = st.file_uploader("Upload Armor CSV", type="csv")

        if uploaded_file is not None:
            st.success("File uploaded successfully!")
            
            # --- Weight Adjustments using Session State ---
            st.subheader("General Weights")
            st.session_state.weights['BST'] = st.slider("Base Stat Total (BST) Weight", 0.0, 2.0, st.session_state.weights['BST'], 0.1)
            st.session_state.weights['Artifice'] = st.slider("Artifice Bonus Weight", 0.0, 2.0, st.session_state.weights['Artifice'], 0.1)

            st.subheader("Archetype Weights")
            for name in st.session_state.archetype_weights:
                st.session_state.archetype_weights[name] = st.slider(f"{name} Weight", 0.0, 2.0, st.session_state.archetype_weights[name], 0.01, key=f"archetype_{name}")

            st.subheader("Tier Weights")
            for tier_name, values in st.session_state.tier_weights.items():
                st.session_state.tier_weights[tier_name]['enabled'] = st.toggle(f"Enable {tier_name} Bonus", value=values['enabled'], key=f"toggle_{tier_name}")

                with st.expander(f"{tier_name} Weights"):
                    st.session_state.tier_weights[tier_name]['low'] = st.slider(f"{tier_name} Low-end Bonus", 0.0, 2.0, values["low"], 0.05, key=f"low_{tier_name}", disabled=not values['enabled'])
                    st.session_state.tier_weights[tier_name]['high'] = st.slider(f"{tier_name} High-end Bonus", 0.0, 2.0, values["high"], 0.05, key=f"high_{tier_name}", disabled=not values['enabled'])

            st.subheader("Illegal Combo Weights")
            # Create a temporary list of keys to avoid runtime errors during iteration
            combo_keys = list(st.session_state.illegal_combo_weights.keys())
            for combo in combo_keys:
                key_str = f"illegal_{combo[0].replace(' (Base)','')}_{combo[1].replace(' (Base)','')}"
                st.session_state.illegal_combo_weights[combo] = st.slider(f"{combo[0]} & {combo[1]}", 0.0, 10.0, st.session_state.illegal_combo_weights[combo], 0.1, key=key_str)
        else:
            st.info("Please upload a CSV file to begin.")
            st.stop()

    # --- Main Panel for Data Display ---
    armor_df = load_data(uploaded_file)

    if armor_df is not None:
        # Calculate weights using values from session state
        armor_df["Armor_Weight"] = armor_df.apply(
            calculate_armor_weight,
            axis=1,
            weights=st.session_state.weights,
            archetype_weights=st.session_state.archetype_weights,
            tier_weights=st.session_state.tier_weights,
            illegal_combo_weights=st.session_state.illegal_combo_weights,
        )

        ranked_armor_df = armor_df.sort_values(by='Armor_Weight', ascending=False)
        
        # --- Filtering Options ---
        st.header("Filter Your Armor")
        all_classes = ['All'] + list(ranked_armor_df['Equippable'].unique())
        all_tiers = ['All'] + list(ranked_armor_df['Tier'].unique())
        selected_class = st.selectbox("Filter by Class", all_classes)
        selected_tier = st.selectbox("Filter by Tier", all_tiers)

        if selected_class != 'All' and selected_tier != 'All':
            display_df = ranked_armor_df[ranked_armor_df['Equippable'] == selected_class]
            display_df = display_df[display_df['Tier'] == selected_tier]
        elif selected_class != 'All' and selected_tier == 'All':
            display_df = ranked_armor_df[ranked_armor_df['Equippable'] == selected_class]
        else:            
            display_df = ranked_armor_df

        # if selected_tier != 'All':
        #     display_df = ranked_armor_df[ranked_armor_df['Tier'] == selected_tier]
        # else:
        #     display_df = ranked_armor_df

        # --- Display Data in Tabs ---
        st.header("Armor Rankings")
        tab1, tab2 = st.tabs(["📊 Ranked Armor Data", "📈 Summary Statistics"])

        with tab1:
            st.dataframe(
                display_df[['Id', 'Name', 'Tier', 'Equippable', 'Total (Base)', 'Armor_Weight']].style.format({'Armor_Weight': "{:.2f}"}),
                height=600,
                use_container_width=True
            )

            # ADDED: Section to get bottom 20 IDs
            st.markdown("---") 
            st.subheader("Shard Assistant")
            st.write("Get a list of your lowest-ranked armor pieces to easily find and shard them in-game.")
            num_to_shard = st.slider("Number of items to shard", 1, 50, 20)

            bottom_x_df = display_df.tail(num_to_shard)
            if not bottom_x_df.empty:
                bottom_x_ids = bottom_x_df['Id'].iloc[::-1].astype(str).tolist()
                ids_to_copy = " or ".join([f"id:{_id}" for _id in bottom_x_ids])
                st.write(f"**Your {num_to_shard} lowest-ranked armor IDs:**")
                st.code(ids_to_copy, language='text')
            else:
                st.warning("Not enough armor pieces to display.")        

        with tab2:
            st.subheader("Average Weight by Class")
            avg_weight_by_class = ranked_armor_df.groupby('Equippable')['Armor_Weight'].mean().reset_index()
            st.bar_chart(avg_weight_by_class, x='Equippable', y='Armor_Weight')
            
            st.subheader("Armor Piece Count by Class")
            count_by_class = ranked_armor_df['Equippable'].value_counts().reset_index()
            count_by_class.columns = ['Equippable', 'Count']
            st.bar_chart(count_by_class, x='Equippable', y='Count')
            


if __name__ == "__main__":
    main()
