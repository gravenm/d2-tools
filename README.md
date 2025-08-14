# Destiny 2 Armor Analyzer 🛡️

This is an interactive web application built with Streamlit that helps Destiny 2 players analyze and rank their armor based on a customizable weighting system. Upload your armor data exported from Destiny Item Manager (DIM), and use the interactive controls to find your best pieces for any build.

---

## ✨ Features

* **Customizable Weighting:** Use sidebar sliders to adjust the importance of Base Stat Total (BST), Artifice bonuses, Tier bonuses, and specific stat combinations.
* **Archetype Bonuses:** Reward armor with stat "spikes" that match predefined build archetypes (e.g., "Grenadier," "Brawler").
* **Legacy Armor Support:** A special weighting system for "Armor 2.0" (Tier 0) pieces that have rare "illegal" stat combinations.
* **Interactive Filtering:** Easily filter your ranked armor by class (Titan, Hunter, Warlock).
* **Session Persistence:** Your slider and toggle settings are saved for your entire browser session, so you don't lose your configuration.
* **Shard Assistant:** Quickly generate a list of your lowest-ranked armor IDs, formatted for easy use with in-game item managers.
* **Data Visualization:** View summary charts showing the average armor weight and total piece count per class.

---

## ⚙️ How It Works

The application calculates a final **Armor Weight** score for each piece of armor. This score is the sum of several weighted components:

1.  **Base Stat Total (BST):** The foundation of the score, directly scaled by the "BST Weight" slider.
2.  **Artifice Bonus:** A flat bonus if the armor is an Artifice piece.
3.  **Tier Bonus:** A bonus for armor in Tiers 1-5, with a higher bonus for pieces in the upper half of their stat range.
4.  **Archetype Spike Bonus:** A bonus for armor with significant spikes in two stats that match a defined archetype.
5.  **Illegal Combo Bonus (Tier 0 Only):** A bonus for legacy armor with high values in two stats that are normally in different pools.

By adjusting the sliders in the sidebar, you can change how much each of these components contributes to the final score, allowing you to tailor the rankings to your personal preferences.

---

## 🚀 How to Use

1.  **Prerequisites:** Make sure you have Python and the required libraries installed.
    ```bash
    pip install streamlit pandas colorlog
    ```

2.  **Export Your Armor:**
    * Go to [Destiny Item Manager (DIM)](https://app.destinyitemmanager.com/).
    * In the "Organizer" tab, select all your armor.
    * Click the three-dots menu and choose "Export as CSV."
    * Save the file as `destiny-armor.csv` or a similar name.

3.  **Run the App:**
    * Save the application code as a Python file (e.g., `app.py`).
    * Open your terminal or command prompt.
    * Navigate to the directory where you saved the file.
    * Run the following command:
        ```bash
        streamlit run app.py
        ```

4.  **Analyze Your Armor:**
    * The application will open in your web browser.
    * Use the file uploader in the sidebar to upload your armor CSV file.
    * Adjust the weights and filters to rank your armor.