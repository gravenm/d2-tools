import streamlit as st
from utils.helpers import *
from core.constants import *
from api.bungie import *
from core.armor_processing import *
import time

# Setup
logger = setup_logger()

st.set_page_config(page_title="Destiny 2 Armor Analyzer", layout="wide")
st.title("Destiny 2 Armor Analyzer 🛡️")
initialize_session_state()

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

with st.expander("How to use?"):
    st.markdown("""
    1.  **Adjust Weights:** Use the sliders and toggles in the sidebar on the left to customize how the armor score is calculated based on what you value most.
    2.  **Analyze & Filter:** The main panel will display your armor, ranked by the calculated weight. Use the dropdown menu to filter by character class.
    3.  **Shard Assistant:** Use the slider at the bottom of the "Ranked Armor Data" tab to generate a list of your lowest-ranked items, making it easy to clean out your vault.
    """)  

# --- Authentication and Token Refresh Flow ---
query_params = st.query_params.to_dict()
auth_code = query_params.get("code")

# 1. If we get an auth code back from Bungie, get the initial token
if auth_code and 'token_data' not in st.session_state:
    with st.spinner("Requesting Access Token..."):
        token_data = get_access_token(auth_code)
        if token_data:
            st.session_state.token_data = token_data
            st.session_state.token_acquired_time = time.time()
            st.rerun()

# 2. Before showing the main app, check if the token is expired and refresh if needed
if 'token_data' in st.session_state:
    # Check if more than an hour has passed (3600 seconds)
    if time.time() - st.session_state.token_acquired_time > st.session_state.token_data['expires_in']:
        with st.spinner("Your session has expired, refreshing..."):
            refresh_token = st.session_state.token_data['refresh_token']
            new_token_data = refresh_access_token(refresh_token)
            if new_token_data:
                st.session_state.token_data = new_token_data
                st.session_state.token_acquired_time = time.time()
                st.success("Session refreshed!")
                time.sleep(1) # Give user time to see the message
                st.rerun()
            else:
                # If refresh fails, clear the session to force re-login
                del st.session_state.token_data
                st.error("Could not refresh your session. Please authorize again.")
                time.sleep(2)
                st.rerun()

if 'token_data' not in st.session_state:
    auth_url = f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code"
    html_string = f'<h2><a href="{auth_url}" target="_self">Click here to authorize with Bungie.net</a></h2>'
    st.html(html_string)
    st.info("You will be redirected back here after authorization.")       

else:
    manifest_db = get_manifest()

    if manifest_db:
        if 'armor_df' not in st.session_state:
            with st.spinner("Fetching profile and armor..."):
                profile = get_destiny_profile(st.session_state.token_data)
                if profile:
                    st.write(f"Found profile for: **{profile['displayName']}**")
                    profile_data = get_profile_with_components(profile, st.session_state.token_data)
                    if profile_data:
                        st.session_state.armor_df = process_api_data(profile_data, manifest_db)
                        st.rerun()

        if 'armor_df' in st.session_state:
            armor_df = st.session_state.armor_df

            with st.sidebar:
                st.header("⚙️ Weight Controls")
                with st.expander("General Weights"):
                    st.session_state.weights['BST'] = st.slider("Total Stat Weight", 0.0, 2.0, st.session_state.weights['BST'], 0.1)
                    st.session_state.weights['Artifice'] = st.slider("Artifice Bonus", 0.0, 2.0, st.session_state.weights['Artifice'], 0.1)
                
                with st.expander("Archetype Weights"):
                    for name in st.session_state.archetype_weights:
                        st.session_state.archetype_weights[name] = st.slider(f"{name} Weight", 0.0, 5.0, st.session_state.archetype_weights[name], 0.1, key=f"archetype_{name}")

                with st.expander("Tier Weights"):
                    for tier_name, values in st.session_state.tier_weights.items():
                        st.session_state.tier_weights[tier_name]['enabled'] = st.toggle(f"Enable {tier_name} Bonus", value=values['enabled'], key=f"toggle_{tier_name}")                        
                        with st.expander(f"{tier_name} Weights"):
                            st.session_state.tier_weights[tier_name]['low'] = st.slider(f"{tier_name} Low-end Bonus", 0.0, 2.0, values["low"], 0.05, key=f"low_{tier_name}", disabled=not values['enabled'])
                            st.session_state.tier_weights[tier_name]['high'] = st.slider(f"{tier_name} High-end Bonus", 0.0, 2.0, values["high"], 0.05, key=f"high_{tier_name}", disabled=not values['enabled'])
                
                with st.expander("Illegal Combo Weights (2.0 Only)"):
                    combo_keys = list(st.session_state.illegal_combo_weights.keys())
                    for combo in combo_keys:
                        key_str = f"illegal_{combo[0]}_{combo[1]}"
                        st.session_state.illegal_combo_weights[combo] = st.slider(f"{combo[0]} & {combo[1]}", 0.0, 10.0, st.session_state.illegal_combo_weights[combo], 0.1, key=key_str)

            armor_df["Armor_Weight"] = armor_df.apply(
                calculate_armor_weight,
                axis=1,
                weights=st.session_state.weights,
                archetype_weights=st.session_state.archetype_weights,
                tier_weights=st.session_state.tier_weights,
                illegal_combo_weights=st.session_state.illegal_combo_weights,
            )
            ranked_df = armor_df.sort_values(by="Armor_Weight", ascending=False)

            st.header("Filter Your Armor")
            all_classes = ['All'] + list(ranked_df['Equippable'].dropna().unique())
            all_tiers = ['All'] + list(ranked_df['Tier'].unique())            
            selected_class = st.selectbox("Filter by Class", all_classes)
            selected_tier = st.selectbox("Filter by Tier", all_tiers)
            selected_exotics = st.checkbox("Show Exotics", bool)
            
            if selected_class != 'All' and selected_tier != 'All':
                display_df = ranked_df[ranked_df['Equippable'] == selected_class]
                display_df = display_df[display_df['Tier'] == selected_tier]
            elif selected_class != 'All' and selected_tier == 'All':
                display_df = ranked_df[ranked_df['Equippable'] == selected_class]
            elif selected_class == 'All' and selected_tier != 'All':
                display_df = ranked_df[ranked_df['Tier'] == selected_tier]                
            else:            
                display_df = ranked_df

            if selected_exotics == False:
                display_df = display_df[display_df["Exotic"] == False]

            st.header("Armor Rankings")
            tab1, tab2, tab3 = st.tabs(["📊 Ranked Armor Data", "📈 Summary Statistics","Idk testing"])

            with tab1:
                st.dataframe(display_df[['Exotic','Name', 'Total', 'Tier', 'Equippable', 'Armor_Weight', 'Weapons', 'Health', 'Class', 'Grenade', 'Super', 'Melee','Id']].style.format({'Armor_Weight': "{:.2f}"}),hide_index=True)
                st.text(f"Showing {len(display_df)}")
                st.subheader("Shard Assistant")
                num_to_shard = st.slider("Number of items to shard", 1, 50, 20)
                bottom_df = display_df.tail(num_to_shard)
                if not bottom_df.empty:
                    ids = bottom_df['Id'].iloc[::-1].astype(str).tolist()
                    st.code(" or ".join([f"id:{_id}" for _id in ids]))

            if st.button("Did you clean your vault?"):
                st.balloons()
            
            with tab2:
                st.subheader("Average Weight by Class")
                avg_weight_by_class = ranked_df.groupby('Equippable')['Armor_Weight'].mean().reset_index()
                st.bar_chart(avg_weight_by_class, x='Equippable', y='Armor_Weight')
                
                st.subheader("Armor Piece Count by Class")
                count_by_class = ranked_df['Equippable'].value_counts().reset_index()
                count_by_class.columns = ['Equippable', 'Count']
                st.bar_chart(count_by_class, x='Equippable', y='Count')

                st.subheader("Tiers")
                count_by_tier = ranked_df['Tier'].value_counts().reset_index()
                count_by_tier.columns = ['Tier','Count']
                st.bar_chart(count_by_tier, x='Tier', y='Count',horizontal=True)

            with tab3:
                st.subheader("Armor Grouped by Slot and Top 3 Stats")
                
                # --- Checkbox Toggles for Filtering ---
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    helmet_toggle = st.checkbox("Helmets", True)
                with col2:
                    arm_toggle = st.checkbox("Gauntlets", True)
                with col3:
                    chest_toggle = st.checkbox("Chest", True)
                with col4:
                    legs_toggle = st.checkbox("Legs", True)
                with col5:
                    class_item_toggle = st.checkbox("Class Item", True)
                
                # Create a list of selected slots
                selected_slots = []
                if helmet_toggle: selected_slots.append("Helmet")
                if arm_toggle: selected_slots.append("Gauntlets")
                if chest_toggle: selected_slots.append("Chest Armor")
                if legs_toggle: selected_slots.append("Leg Armor")
                if class_item_toggle: selected_slots.append("Class Item")

                # Filter the dataframe based on selected slots
                filtered_group_df = display_df[display_df['Slot'].isin(selected_slots)]

                # --- DYNAMICALLY CREATE "Top 3 Stats" COLUMN ---
                stat_cols = list(STAT_HASH_TO_NAME.values())
                filtered_group_df['Top 3 Stats'] = filtered_group_df[stat_cols].apply(
                    lambda row: ', '.join(row.nlargest(3).index), axis=1
                )

                # Group the filtered data
                grouped = filtered_group_df.groupby(['Slot', 'Top 3 Stats'])

                for (slot, top_stats), group in grouped:
                    with st.expander(f"**{slot}** with stats: **{top_stats}** ({len(group)} pieces)"):
                        st.dataframe(
                            group[['Name', 'Total', 'Tier', 'Armor_Weight', 'Weapons', 'Health', 'Class', 'Grenade', 'Super', 'Melee']].style.format({'Armor_Weight': "{:.2f}"}),
                            hide_index=True
                        )