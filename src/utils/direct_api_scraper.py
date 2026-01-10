"""
Direct API Scraper
Directly queries ESPN's internal APIs that power their website
This is more reliable than HTML scraping
"""

import requests
import json
from typing import List, Dict, Optional
import time


class DirectAPIScraper:
    """
    Scraper that uses ESPN's internal JSON APIs directly
    These are the same APIs their website uses, so they're very reliable
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 15

    def _get_cached(self, key: str) -> Optional[any]:
        """Get cached data if still valid"""
        if key in self.cache:
            if time.time() - self.cache_time.get(key, 0) < self.cache_duration:
                return self.cache[key]
        return None

    def _set_cache(self, key: str, data: any):
        """Set cache data"""
        self.cache[key] = data
        self.cache_time[key] = time.time()

    def get_all_live_matches(self) -> List[Dict]:
        """
        Get ALL live cricket matches from ESPN's comprehensive API
        This API returns ALL cricket across all formats and leagues
        """
        cached = self._get_cached('all_live')
        if cached:
            return cached

        matches = []

        # Try multiple ESPN API endpoints
        api_endpoints = [
            "https://site.web.api.espn.com/apis/site/v2/sports/cricket/scoreboard",
            "https://site.api.espn.com/apis/site/v2/sports/cricket/scoreboard",
            "https://cdn.espn.com/core/cricket/scoreboard",
        ]

        for url in api_endpoints:
            try:
                print(f"Trying ESPN API: {url}")
                response = self.session.get(url, timeout=15)

                if response.status_code == 200:
                    data = response.json()

                    # ESPN returns 404 as JSON when no matches
                    if data.get('code') == 404:
                        print("API returned 404 - no matches currently")
                        continue

                    events = data.get('events', [])

                    print(f"ESPN API returned {len(events)} total cricket events")

                    for event in events:
                        try:
                            match_info = self._parse_event(event)
                            if match_info:
                                matches.append(match_info)
                                print(f"Found: {match_info['name']} (ID: {match_info['match_id']}, Format: {match_info.get('format', 'unknown')})")
                        except Exception as e:
                            print(f"Error parsing event: {e}")
                            continue

                    if matches:
                        break  # Found matches, no need to try other endpoints

                elif response.status_code == 404:
                    print(f"API endpoint returned 404 -probably no live matches")
                    continue

            except Exception as e:
                print(f"Error with API {url}: {e}")
                continue

        self._set_cache('all_live', matches)
        return matches

    def _parse_event(self, event: Dict) -> Optional[Dict]:
        """Parse an event from ESPN API"""
        try:
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])

            if len(competitors) < 2:
                return None

            team1 = competitors[0]
            team2 = competitors[1]

            # Get status
            status = event.get('status', {})
            status_type = status.get('type', {})
            state = status_type.get('state', '')  # 'pre', 'in', 'post'

            # Get format info
            format_info = competition.get('format', {})
            if isinstance(format_info, dict):
                format_name = format_info.get('name', '')
            else:
                format_name = str(format_info)

            # Also check series/league name
            league_name = event.get('league', {}).get('name', '')
            season_name = event.get('season', {}).get('name', '')

            match_info = {
                'match_id': str(event.get('id', '')),
                'name': event.get('name', ''),
                'short_name': event.get('shortName', ''),
                'status': status_type.get('description', ''),
                'status_detail': status_type.get('detail', ''),
                'state': state,
                'is_live': state == 'in',
                'venue': competition.get('venue', {}).get('fullName', ''),
                'series': season_name,
                'league': league_name,
                'format': format_name,
                'source': 'espn_direct',
                'teams': {
                    'team1': {
                        'name': team1.get('team', {}).get('displayName', ''),
                        'short_name': team1.get('team', {}).get('abbreviation', ''),
                        'score': team1.get('score', ''),
                    },
                    'team2': {
                        'name': team2.get('team', {}).get('displayName', ''),
                        'short_name': team2.get('team', {}).get('abbreviation', ''),
                        'score': team2.get('score', ''),
                    }
                }
            }

            return match_info

        except Exception as e:
            print(f"Error parsing event: {e}")
            return None


def get_direct_api_scraper() -> DirectAPIScraper:
    """Get singleton instance"""
    if not hasattr(get_direct_api_scraper, '_instance'):
        get_direct_api_scraper._instance = DirectAPIScraper()
    return get_direct_api_scraper._instance
