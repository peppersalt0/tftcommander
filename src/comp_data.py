# Extracts comp data from MetaTft API for Agent

import requests
import json
from pathlib import Path

COMP_ID = "381014"
API_URL = "https://api-hc.metatft.com/tft-comps-api/comps_data"

def download_all_comps():
    params = {'queue' : 1100} # Parameter to request Ranked TFT

    try:
        response = requests.get(API_URL, params=params)

        if response.status_code == 200:
            print("Download Successful")
            data = response.json()
            return data
        else:
            print(f"Error: HTTP {response.status_code}")
            return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# data is the full API resonse
# comp_id is the id of the TFT comp to extract
# returns dict of comp data or none if not found
def extract_comp(data, comp_id):
    try:
        cluster_details = data['results']['data']['cluster_details']
        if comp_id in cluster_details:
            comp_data = cluster_details[comp_id]
            print(f"Found Comp {comp_id}")
            return comp_data
        else:
            print(f"Comp {comp_id} not found")
            return None
    
    except KeyError as e:
        print(f"Data structure error {e}")
        return None
    
# converts raw API data into clean bot-ready format
# comp_data is a dictionary from MetaTFT API
# returns dict of cleaned data for TFT agent
def parse_comp_for_bot(comp_data):
    
    # Extract units (remove TFT16_ prefix)
    raw_units = comp_data['units_string'].split(', ')
    units = [unit.replace('TFT16_', '') for unit in raw_units]
    
    # Get overall stats
    overall = comp_data['overall']
    
    # Extract best item builds
    item_builds = {}
    for build in comp_data['builds']:
        unit_name = build['unit'].replace('TFT16_', '')
        
        # Clean item names (remove TFT_Item_ prefix)
        items = [
            item.replace('TFT_Item_', '') 
            for item in build['buildName']
        ]
        
        item_builds[unit_name] = {
            'items': items,
            'avg_placement': build['avg'],
            'place_change': build['place_change'],
            'sample_size': build['count']
        }
    
    # Build the clean config
    config = {
        'comp_id': comp_data['Cluster'],
        'comp_name': 'Piltover T-Hex',
        'units': units,
        'main_carry': 'THex',
        
        'performance': {
            'avg_placement': overall['avg'],
            'sample_size': overall['count'],
            'estimated_top4_rate': round((8 - overall['avg']) / 7 * 100, 1)
        },
        
        'item_builds': item_builds,
        
        'strategy_notes': {
            'difficulty': comp_data.get('difficulty', 'Unknown'),
            'levelling': comp_data.get('levelling', 'Standard')
        }
    }
    
    print("Parsed successfully")
    return config

# saves config to json
# config is cleaned composition dict
# comp_id is comptional comp ID for custom filename
def save_config(config, comp_id=None):
    if comp_id:
        # Create readable filename
        comp_name = config.get('comp_name', 'unknown').lower().replace(' ', '_')
        filename = f'data/{comp_name}_{comp_id}.json'
    else:
        filename = 'data/comp_config.json'
    
    Path('data').mkdir(exist_ok=True)

    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)

    print("Saved sucessfully")
    print(f"File location @ {filename}")

def main():
    # Step 1: Download all comps from API
    data = download_all_comps()
    if not data:
        print("Failed to download data")
        return
    
    # Step 2: Extract our specific comp
    comp_data = extract_comp(data, COMP_ID)
    if not comp_data:
        print("Failed to extract comp data")
        return
    
    # Step 3: Parse into clean format
    config = parse_comp_for_bot(comp_data)
    
    # Step 4: Save to file
    save_config(config, comp_id=COMP_ID)
    
    # Step 5: Print summary
    print("COMP SUMMARY")
    print(f"Comp: {config['comp_name']}")
    print(f"Units: {', '.join(config['units'])}")
    print(f"Avg Placement: {config['performance']['avg_placement']:.2f}")
    print(f"Sample Size: {config['performance']['sample_size']:,} games")
    print(f"Estimated Top 4 Rate: {config['performance']['estimated_top4_rate']}%")
    print(f"\nMain carry: {config['main_carry']}")
    
    # Show best items for main carry
    if config['main_carry'] in config['item_builds']:
        carry_items = config['item_builds'][config['main_carry']]['items']
        print(f"Best items: {', '.join(carry_items)}")
    
    print("\nData extraction complete!")

# Run the script
if __name__ == "__main__":
    main()

    
