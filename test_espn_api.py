#!/usr/bin/env python3
"""
Test ESPN API to see what data is actually available for BPL matches
"""

import requests
import json

# ESPN API configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
}

# BPL League ID
BPL_LEAGUE_ID = 8653

print("=" * 80)
print("ESPN API Testing for BPL")
print("=" * 80)

# Step 1: Get current BPL matches
print("\n1. Fetching current BPL matches...")
scoreboard_url = f"https://site.web.api.espn.com/apis/site/v2/sports/cricket/{BPL_LEAGUE_ID}/scoreboard"

try:
    response = requests.get(scoreboard_url, headers=HEADERS, timeout=10)
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        events = data.get('events', [])
        print(f"   Found {len(events)} events")

        # Find live matches
        for event in events:
            match_id = event.get('id')
            name = event.get('name', 'Unknown')
            status = event.get('status', {}).get('type', {})
            state = status.get('state', '')

            print(f"\n   Match: {name}")
            print(f"   ID: {match_id}")
            print(f"   State: {state}")

            if state == 'in':  # Live match
                print(f"\n   ✓ This is a LIVE match! Testing playbyplay API...")

                # Step 2: Try to get playbyplay data
                playbyplay_url = f"https://site.web.api.espn.com/apis/site/v2/sports/cricket/{BPL_LEAGUE_ID}/playbyplay?contentorigin=espn&event={match_id}"

                try:
                    pbp_response = requests.get(playbyplay_url, headers=HEADERS, timeout=10)
                    print(f"   PlayByPlay Status: {pbp_response.status_code}")

                    if pbp_response.status_code == 200:
                        pbp_data = pbp_response.json()

                        # Check different possible locations for commentary
                        commentary = pbp_data.get('commentary', {})
                        items = commentary.get('items', [])

                        print(f"\n   commentary.items: {len(items)} items")

                        # Try alternative structures
                        plays = pbp_data.get('plays', [])
                        print(f"   plays: {len(plays)} items")

                        innings = pbp_data.get('innings', [])
                        print(f"   innings: {len(innings)} innings")

                        # Show structure
                        print(f"\n   Available keys in response:")
                        for key in pbp_data.keys():
                            value = pbp_data[key]
                            if isinstance(value, list):
                                print(f"     - {key}: list with {len(value)} items")
                            elif isinstance(value, dict):
                                print(f"     - {key}: dict with keys: {list(value.keys())[:5]}")
                            else:
                                print(f"     - {key}: {type(value).__name__}")

                        # If we found items, show a sample
                        if items:
                            print(f"\n   Sample commentary item:")
                            sample = items[0]
                            print(f"     Keys: {list(sample.keys())}")
                            print(f"     Period: {sample.get('period')}")
                            print(f"     homeScore: {sample.get('homeScore')}")
                            print(f"     awayScore: {sample.get('awayScore')}")

                        # Save full response for analysis
                        filename = f"espn_playbyplay_{match_id}.json"
                        with open(filename, 'w') as f:
                            json.dump(pbp_data, f, indent=2)
                        print(f"\n   ✓ Saved full response to {filename}")

                except Exception as e:
                    print(f"   Error fetching playbyplay: {e}")

                # Only test first live match
                break

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("Test complete. Check the generated JSON file for full API response.")
print("=" * 80)
