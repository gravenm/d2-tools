import pandas as pd
from itertools import combinations
from utils.helpers import query_manifest
from core.constants import *
from app import logger


def process_api_data(profile_data, manifest_db):
    logger.info("Starting to process API data...")
    vault_items = profile_data['Response']['profileInventory']['data']['items']
    item_stats = profile_data['Response']['itemComponents']['stats']['data']
    item_sockets = profile_data['Response']['itemComponents']['sockets']['data']
    
    armor_data = []
    for item in vault_items:
        item_def = query_manifest(manifest_db, "DestinyInventoryItemDefinition", item['itemHash'])
        if item_def and any(h in ARMOR_TYPE_HASHES for h in item_def['itemCategoryHashes']):
            logger.debug(f"Processing item: {item_def['displayProperties']['name']}")
            
            # Start with the stats provided by the API (includes mods/masterwork)
            api_stats = {name: 0 for name in STAT_HASH_TO_NAME.values()}
            api_total = 0
            instance_stats = item_stats.get(item['itemInstanceId'], {}).get('stats', {})
            for stat_hash, details in instance_stats.items():
                stat_name = STAT_HASH_TO_NAME.get(int(stat_hash))
                if stat_name:
                    api_stats[stat_name] = details['value']
                    api_total += details['value']
            
            # Now, find and subtract mod and masterwork bonuses
            is_masterworked = False
            mod_bonuses = {name: 0 for name in STAT_HASH_TO_NAME.values()}
            
            sockets = item_sockets.get(item['itemInstanceId'], {}).get('sockets', [])
            for socket in sockets:
                plug_hash = socket.get('plugHash')
                if not plug_hash:
                    continue

                plug_def = query_manifest(manifest_db, "DestinyInventoryItemDefinition", plug_hash)
                if not plug_def:
                    continue

                # Check for Masterwork
                if plug_def.get('plug', {}).get('plugCategoryHash') == MASTERWORK_ENERGY_PLUG_CATEGORY_HASH:
                    is_masterworked = True

                # Check for General Stat Mods
                socket_type_def = query_manifest(manifest_db, "DestinySocketTypeDefinition", item_def['sockets']['socketEntries'][sockets.index(socket)]['socketTypeHash'])
                if socket_type_def and socket_type_def.get('socketCategoryHash') == GENERAL_ARMOR_MOD_SOCKET_CATEGORY_HASH:
                    for stat in plug_def.get('investmentStats', []):
                        stat_name = STAT_HASH_TO_NAME.get(stat['statTypeHash'])
                        if stat_name:
                            mod_bonuses[stat_name] += stat['value']

            # Calculate the true base stats
            base_stats = api_stats.copy()
            if is_masterworked:
                logger.debug(f"  - Item is Masterworked. Subtracting +2 from all stats.")
                for stat_name in base_stats:
                    base_stats[stat_name] -= 2
            
            for stat_name, bonus in mod_bonuses.items():
                if bonus > 0:
                    logger.debug(f"  - Found {stat_name} mod with +{bonus}. Subtracting.")
                    base_stats[stat_name] -= bonus

            base_total = sum(base_stats.values())

            is_artifice = False
            for socket in sockets:
                plug_def = query_manifest(manifest_db, "DestinyInventoryItemDefinition", socket.get('plugHash', 0))
                if plug_def and plug_def.get('socket', {}).get('socketTypeHash') == ARTIFICE_SOCKET_TYPE_HASH:
                    is_artifice = True
                    break

            # --- UPDATED TIER LOGIC ---
            tier = 0
            stats_series = pd.Series(base_stats)
            sorted_stats = stats_series.sort_values(ascending=False)
            top_two_stats_names = tuple(sorted(sorted_stats.index[:2]))

            # Check for illegal combo first
            if top_two_stats_names in ILLEGAL_COMBO_WEIGHTS:
                tier = 0
                logger.debug(f"  - Marked as Tier 0 due to illegal combo: {top_two_stats_names}")
            elif (stats_series > 0).all(): 
                tier = 0
                logger.debug(f"  - Marked as Tier 0 due to non zero stats")
            else:
                # If not illegal, assign tier based on total stats
                for t, (low, high) in TIERS.items():
                    if low <= base_total <= high:
                        tier = int(t.split(" ")[1])
                        break

            armor_data.append({
                "Name": item_def['displayProperties']['name'],
                "Id": item['itemInstanceId'],
                "Equippable": item_def['classType'],
                "Total": base_total, # Use the calculated base total
                "Tier": tier,
                "Artifice": is_artifice,
                **base_stats # Use the calculated base stats
            })
    
    df = pd.DataFrame(armor_data)
    df['Equippable'] = df['Equippable'].map({0: 'Titan', 1: 'Hunter', 2: 'Warlock', 3: 'Any'})
    logger.info("Finished processing API data.")
    return df

# --- Weight Calculation Logic ---
def calculate_armor_weight(armor_piece, weights, archetype_weights, tier_weights, illegal_combo_weights):
    logger.debug(f"Processing: {armor_piece['Name']} (ID: {armor_piece['Id']})")
    weight = 0
    bst = armor_piece.get("Total", 0)
    is_legacy_armor = False

    # 1. Base stat and Artifice bonus are always applied first
    bst_bonus = bst * weights.get("BST", 1.0)
    weight += bst_bonus
    logger.debug(f"  - BST Bonus: {bst_bonus:.2f} (Total: {bst})")

    if armor_piece.get("Artifice", False):
        artifice_bonus = weights.get("Artifice", 1.0)
        weight += artifice_bonus
        logger.debug(f"  - Artifice Bonus: {artifice_bonus:.2f}")

    # 2. Determine stat combos and check for illegal ones FIRST
    stats_series = pd.Series({stat: armor_piece.get(stat, 0) for stat in STAT_HASH_TO_NAME.values()})
    sorted_stats = stats_series.sort_values(ascending=False)
    top_two_stats_names = tuple(sorted(sorted_stats.index[:2]))

    # Check if the top two stats form an illegal combo
    if top_two_stats_names in illegal_combo_weights and sorted_stats.iloc[0] > 15 and sorted_stats.iloc[1] > 15:
        is_legacy_armor = True
        combo_bonus = illegal_combo_weights[top_two_stats_names]
        weight += combo_bonus
        logger.debug(f"  - Found Illegal Combo: {top_two_stats_names} with bonus {combo_bonus:.2f}")
        # This piece is now considered Tier 0 and skips the normal tiering
    
    # 3. If it's NOT a legacy piece, apply the standard tier bonus
    if not is_legacy_armor:
        tier = armor_piece.get('Tier', 0)
        if tier > 0:
            tier_name = f"Tier {tier}"
            if tier_name in tier_weights and tier_weights[tier_name].get('enabled', False):
                min_stat, max_stat = TIERS[tier_name]
                midpoint = (min_stat + max_stat) / 2
                tier_config = tier_weights[tier_name]
                tier_bonus = tier_config["high"] if bst >= midpoint else tier_config["low"]
                weight += tier_bonus
                logger.debug(f"  - Tier {tier} Bonus: {tier_bonus:.2f}")

        # 4. Finally, check for an archetype match based on the top two stats
        for archetype_name, stats in ARCHETYPES.items():
            if tuple(sorted((stats["Primary"], stats["Secondary"]))) == top_two_stats_names:
                archetype_bonus = archetype_weights.get(archetype_name, 0)
                weight += archetype_bonus
                logger.debug(f"  - Archetype Bonus for {archetype_name}: {archetype_bonus:.2f}")
                break
            
    logger.info(f"Final Weight for {armor_piece['Name']}: {weight:.2f}")
    return weight
