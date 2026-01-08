"""
Verification script to confirm BPL match detection is working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.cricinfo_scraper import get_scraper

def verify_bpl():
    print("\n" + "="*70)
    print("VERIFYING BPL MATCH DETECTION FIX")
    print("="*70 + "\n")

    scraper = get_scraper()

    # Clear cache to force fresh fetch
    scraper.cache = {}
    scraper.cache_time = {}

    print("Fetching live matches from all league sources...")
    matches = scraper.get_live_matches()

    # Filter for live matches only
    live_matches = [m for m in matches if m.get('is_live', False)]

    print(f"\nTotal live T20 matches found: {len(live_matches)}\n")

    if live_matches:
        for i, match in enumerate(live_matches, 1):
            source = match.get('source', 'unknown').upper()
            name = match.get('name', 'Unknown')
            status = match.get('status', 'N/A')
            series = match.get('series', 'N/A')

            print(f"{i}. [{source}] {name}")
            print(f"   Status: {status}")
            print(f"   Series: {series}")
            print(f"   Match ID: {match.get('match_id')}")

            # Check if it's the BPL match
            if 'rangpur' in name.lower() and 'chattogram' in name.lower():
                print(f"   ✓ BPL MATCH DETECTED!")

                teams = match.get('teams', {})
                if teams:
                    team1 = teams.get('team1', {})
                    team2 = teams.get('team2', {})
                    print(f"   Teams: {team1.get('name')} vs {team2.get('name')}")
                    print(f"   Score: {team1.get('score')} - {team2.get('score')}")

            print()

        # Check if BPL match was found
        bpl_found = any('rangpur' in m.get('name', '').lower() and 'chattogram' in m.get('name', '').lower()
                       for m in live_matches)

        if bpl_found:
            print("="*70)
            print("SUCCESS! BPL match is now being detected by the app!")
            print("="*70)
            print("\nThe Streamlit app will now show this match in the Live PI Tracker.")
            print("You can select it and view real-time Pressure Index calculations.")
        else:
            print("⚠ Warning: BPL match not found in results")
    else:
        print("No live T20 matches currently in progress.")
        print("(The BPL match may have finished)")

    print()

if __name__ == "__main__":
    verify_bpl()
