"""
Test script to check live match detection from multiple sources
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.cricinfo_scraper import get_scraper
from src.utils.cricbuzz_scraper import get_cricbuzz_scraper

def test_live_matches():
    print("="*70)
    print("Testing Multi-Source Live Match Detection")
    print("="*70)

    # Test main scraper (ESPN + Cricbuzz combined)
    print("\n1. Testing Combined Scraper (ESPN + Cricbuzz)...")
    print("-" * 70)
    scraper = get_scraper()
    matches = scraper.get_live_matches()

    print(f"\nFound {len(matches)} total matches:\n")

    if matches:
        espn_count = sum(1 for m in matches if m.get('source') == 'espn')
        cricbuzz_count = sum(1 for m in matches if m.get('source') == 'cricbuzz')

        print(f"  ESPN: {espn_count} matches")
        print(f"  Cricbuzz: {cricbuzz_count} matches\n")

        for i, match in enumerate(matches, 1):
            source = match.get('source', 'unknown').upper()
            print(f"{i}. [{source}] {match.get('name', 'Unknown')}")
            print(f"   ID: {match.get('match_id', 'N/A')}")
            print(f"   Status: {match.get('status', 'N/A')}")
            print(f"   Is Live: {match.get('is_live', False)}")
            print(f"   Series: {match.get('series', 'N/A')}")

            # Show teams if available
            teams = match.get('teams', {})
            if teams:
                team1 = teams.get('team1', {})
                team2 = teams.get('team2', {})
                print(f"   Teams: {team1.get('name', '')} vs {team2.get('name', '')}")
                print(f"   Scores: {team1.get('score', 'N/A')} - {team2.get('score', 'N/A')}")
            print()
    else:
        print("No live matches detected from any source!")

        # Try direct ESPN API call for debugging
        print("\n2. Testing ESPN API Directly...")
        print("-" * 70)
        import requests
        try:
            response = requests.get(
                "https://site.web.api.espn.com/apis/site/v2/sports/cricket/8676/scoreboard",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"ESPN API Response has {len(data.get('events', []))} events")
                for event in data.get('events', [])[:3]:
                    print(f"  - {event.get('name', 'Unknown')}")
                    print(f"    Status: {event.get('status', {}).get('type', {}).get('description', 'N/A')}")
                    print(f"    State: {event.get('status', {}).get('type', {}).get('state', 'N/A')}")
        except Exception as e:
            print(f"ESPN API call failed: {e}")

        # Try Cricbuzz separately
        print("\n3. Testing Cricbuzz Separately...")
        print("-" * 70)
        try:
            cricbuzz = get_cricbuzz_scraper()
            cb_matches = cricbuzz.get_live_matches()
            print(f"Cricbuzz found {len(cb_matches)} matches")

            for match in cb_matches[:3]:
                print(f"  - {match.get('name', 'Unknown')}")
                print(f"    Status: {match.get('status', 'N/A')}")
                print(f"    Series: {match.get('series', 'N/A')}")
        except Exception as e:
            print(f"Cricbuzz test failed: {e}")

    print("\n" + "="*70)
    print("Test Complete")
    print("="*70)

if __name__ == "__main__":
    test_live_matches()
