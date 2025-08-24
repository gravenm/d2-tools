Destiny 2 Live Armor Analyzer 🛡️
=================================

This is an interactive web application built with Streamlit that connects directly to the Bungie.net API to analyze and rank your in-game armor. It fetches your live vault data and applies a deeply customizable weighting system to help you find your best gear for any build, identify valuable legacy armor, and clean out your vault with confidence.

✨ Features
----------

-   **Live API Integration:** No more manual CSV exports. The app securely authenticates with your Bungie.net account to fetch your live vault inventory.

-   **Base Stat Calculation:** Automatically identifies and subtracts bonuses from mods and masterworks to calculate the true, unmodified base stats of your armor.

-   **Advanced Weighting System:** A powerful and fully customizable scoring system with sliders and toggles for:

    -   **Base Stat Total (BST):** Prioritize raw stat totals.

    -   **Artifice Armor:** Give a special bonus to armor with an extra mod slot.

    -   **Tier Bonuses:** Reward high-stat seasonal armor (Tiers 1-5).

    -   **Archetype Spikes:** Assign value to armor that fits specific playstyles (e.g., "Grenadier," "Brawler") by having high spikes in two key stats.

    -   **Illegal Combos:** A special bonus for rare "Armor 2.0" (Tier 0) pieces with high stats in normally incompatible slots.

-   **Exotic Identification:** Automatically detects Exotic armor and highlights it in the results table for easy visibility.

-   **Interactive UI:**

    -   **Dynamic Filtering:** Filter your ranked armor by class and tier.

    -   **Session Persistence:** Your custom weight settings are saved for your entire browser session.

    -   **Shard Assistant:** A slider-based tool to generate a DIM-compatible search query for your lowest-ranked items.

    -   **Data Visualization:** Summary charts showing average armor weight and piece count per class.

-   **Debug Logging:** Outputs detailed processing steps to both the console and a `d2_analyzer.log` file for troubleshooting.

🚀 Setup and Usage
------------------

### 1\. Prerequisites

-   Python 3.8+

-   A Bungie.net account with a registered application.

### 2\. Bungie.net API Setup

1.  Go to the [Bungie.net Developer Portal](https://www.bungie.net/en/Application "null") and create a new application.

2.  Set the **"Redirect URL"** for your application to your Streamlit app's URL (e.g., `http://localhost:8501`).

3.  Create a folder named `.streamlit` in your project directory.

4.  Inside that folder, create a file named `secrets.toml`.

5.  Add your API credentials to the `secrets.toml` file:

    ```
    # .streamlit/secrets.toml
    API_KEY = "YOUR_API_KEY_HERE"
    CLIENT_ID = "YOUR_CLIENT_ID_HERE"

    ```

### 3\. Installation

1.  Clone or download the project files.

2.  Create a `requirements.txt` file with the following content:

    ```
    streamlit
    requests
    pandas
    colorlog

    ```

3.  Install the dependencies:

    ```
    pip install -r requirements.txt

    ```

### 4\. Running the App

1.  Open your terminal and navigate to the project's root directory.

2.  Run the following command:

    ```
    streamlit run app.py

    ```

3.  The application will open in your web browser, where you can authorize it with your Bungie.net account.

📁 Project Structure
--------------------

The application is modularized for better organization and maintainability.

```
d2_armor_analyzer/
├── app.py                  # Main Streamlit UI and application flow
├── requirements.txt        # Project dependencies
├── .streamlit/
│   └── secrets.toml        # API credentials (not committed to git)
└── core/
    ├── __init__.py
    ├── constants.py        # All static data (URLs, hashes, weights)
    └── armor_processing.py # Data processing and weight calculation logic
└── api/
    ├── __init__.py
    └── bungie.py           # Functions for Bungie API interaction
└── utils/
    ├── __init__.py
    └── helpers.py          # Logger setup and other utilities

```