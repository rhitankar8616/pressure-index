"""
Cricbuzz Scraper Module
Fallback scraper to fetch live T20 match data from Cricbuzz
Used when ESPN Cricinfo doesn't detect smaller league matches
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Optional
import time

# Cricbuzz endpoints
CRICBUZZ_BASE_URL = "https://www.cricbuzz.com"
CRICBUZZ_MATCHES_URL = "https://www.cricbuzz.com/cricket-match/live-scores"
CRICBUZZ_API_RECENT = "https://www.cricbuzz.com/api/matches/recent"

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.cricbuzz.com/',
}


class CricbuzzScraper:
    """Class to scrape live T20 match data from Cricbuzz"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 15  # seconds

    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get cached data if still valid"""
        if key in self.cache:
            if time.time() - self.cache_time.get(key, 0) < self.cache_duration:
                return self.cache[key]
        return None

    def _set_cache(self, key: str, data: Dict):
        """Set cache data"""
        self.cache[key] = data
        self.cache_time[key] = time.time()

    def get_live_matches(self) -> List[Dict]:
        """
        Fetch all live T20 matches from Cricbuzz

        Returns:
            List of match dictionaries with basic info
        """
        cached = self._get_cached('cricbuzz_live_matches')
        if cached:
            return cached

        matches = []

        try:
            # Try scraping the live scores page
            response = self.session.get(CRICBUZZ_MATCHES_URL, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all match cards
                # Cricbuzz uses various class patterns, try to find common ones
                match_cards = soup.find_all('div', class_=re.compile(r'cb-mtch-lst|cb-col-100|cb-lv-scrs-col'))

                for card in match_cards:
                    match_info = self._parse_match_card(card)
                    if match_info and self._is_t20_match(match_info):
                        # Only include live or in-progress matches
                        if match_info.get('is_live', False):
                            matches.append(match_info)

                # Also try to find embedded JSON data
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'matchScheduleMap' in str(script.string):
                        # Try to extract JSON data
                        try:
                            json_match = re.search(r'var\s+matchScheduleMap\s*=\s*({.*?});',
                                                  script.string, re.DOTALL)
                            if json_match:
                                data = json.loads(json_match.group(1))
                                json_matches = self._parse_schedule_json(data)
                                for jm in json_matches:
                                    if not any(m['match_id'] == jm['match_id'] for m in matches):
                                        matches.append(jm)
                        except Exception:
                            continue

        except Exception as e:
            print(f"Cricbuzz scraping error: {e}")

        self._set_cache('cricbuzz_live_matches', matches)
        return matches

    def _parse_match_card(self, card) -> Optional[Dict]:
        """Parse Cricbuzz match card HTML element"""
        try:
            # Try to find match link with ID
            links = card.find_all('a', href=True)
            match_id = None
            match_link = None

            for link in links:
                href = link['href']
                # Cricbuzz match URLs: /live-cricket-scores/{match-id}/{match-name}
                id_match = re.search(r'/live-cricket-scores/(\d+)/', href)
                if id_match:
                    match_id = id_match.group(1)
                    match_link = href
                    break

            if not match_id:
                return None

            # Extract match type/series info
            series_elem = card.find('a', class_=re.compile(r'text-hvr-underline'))
            series = series_elem.get_text(strip=True) if series_elem else ''

            # Extract team names and scores
            team_divs = card.find_all('div', class_=re.compile(r'cb-hmscg-tm|cb-col-50'))
            teams = []

            for team_div in team_divs[:2]:
                # Find team name
                name_elem = team_div.find('div', class_=re.compile(r'cb-hmscg-tm-nm'))
                if not name_elem:
                    name_elem = team_div.find('span', class_=re.compile(r'team'))

                # Find score
                score_elem = team_div.find('div', class_=re.compile(r'cb-hmscg-tm-bat-scr'))
                if not score_elem:
                    score_elem = team_div.find('span', class_=re.compile(r'score'))

                if name_elem:
                    teams.append({
                        'name': name_elem.get_text(strip=True),
                        'score': score_elem.get_text(strip=True) if score_elem else ''
                    })

            if len(teams) < 2:
                return None

            # Extract status
            status_elem = card.find('div', class_=re.compile(r'cb-text-live|cb-text-complete|cb-schdl'))
            status = ''
            is_live = False

            if status_elem:
                status = status_elem.get_text(strip=True)
                is_live = 'live' in status.lower() or any(cls for cls in status_elem.get('class', []) if 'live' in cls.lower())

            match_name = f"{teams[0]['name']} vs {teams[1]['name']}"

            return {
                'match_id': f"cb_{match_id}",  # Prefix to distinguish from Cricinfo IDs
                'source': 'cricbuzz',
                'name': match_name,
                'short_name': match_name,
                'status': status,
                'is_live': is_live,
                'series': series,
                'format': 'T20',  # Will be validated by _is_t20_match
                'teams': {
                    'team1': {
                        'name': teams[0]['name'],
                        'score': teams[0].get('score', '')
                    },
                    'team2': {
                        'name': teams[1]['name'],
                        'score': teams[1].get('score', '')
                    }
                },
                'match_url': f"{CRICBUZZ_BASE_URL}{match_link}" if match_link else None
            }

        except Exception as e:
            print(f"Error parsing Cricbuzz match card: {e}")
            return None

    def _parse_schedule_json(self, data: Dict) -> List[Dict]:
        """Parse Cricbuzz schedule JSON data"""
        matches = []

        try:
            # The structure may vary, but typically matches are nested
            for key, value in data.items():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and 'matchId' in item:
                            match_info = self._parse_json_match(item)
                            if match_info and self._is_t20_match(match_info):
                                matches.append(match_info)

        except Exception as e:
            print(f"Error parsing Cricbuzz JSON: {e}")

        return matches

    def _parse_json_match(self, match_data: Dict) -> Optional[Dict]:
        """Parse individual match from JSON"""
        try:
            teams = match_data.get('teams', [])
            if len(teams) < 2:
                return None

            status = match_data.get('matchStatus', '')
            is_live = 'live' in status.lower() or match_data.get('state', '') == 'In Progress'

            return {
                'match_id': f"cb_{match_data.get('matchId', '')}",
                'source': 'cricbuzz',
                'name': match_data.get('matchDesc', ''),
                'status': status,
                'is_live': is_live,
                'series': match_data.get('series', {}).get('name', ''),
                'format': match_data.get('matchFormat', ''),
                'teams': {
                    'team1': {
                        'name': teams[0].get('name', ''),
                        'score': teams[0].get('score', '')
                    },
                    'team2': {
                        'name': teams[1].get('name', ''),
                        'score': teams[1].get('score', '')
                    }
                }
            }

        except Exception:
            return None

    def _is_t20_match(self, match_info: Dict) -> bool:
        """Check if match is a T20 format"""
        name = match_info.get('name', '').lower()
        series = match_info.get('series', '').lower()
        format_str = match_info.get('format', '').lower()

        # Comprehensive T20 indicators
        t20_indicators = [
            't20', 'twenty20', 'twenty-20', 'twenty 20',
            # International
            't20i', 't20 international',
            # Major leagues
            'ipl', 'indian premier league',
            'bbl', 'big bash',
            'cpl', 'caribbean premier league',
            'psl', 'pakistan super league',
            'bpl', 'bangladesh premier league',
            'sa20', 'sa 20',
            'lpl', 'lanka premier league',
            # Other leagues
            'hundred', 'the hundred',
            'blast', 't20 blast', 'vitality blast',
            'super smash',
            'premier league t20',
            'global t20',
            'max60',
            # Team name patterns (franchise teams)
            'riders', 'royals', 'challengers', 'capitals', 'knights', 'warriors',
            'kings', 'titans', 'strikers', 'chargers', 'gladiators', 'trailblazers',
            'rangpur', 'dhaka', 'chattogram', 'sylhet', 'khulna', 'comilla', 'rajshahi',
        ]

        for indicator in t20_indicators:
            if indicator in name or indicator in series or indicator in format_str:
                return True

        # Explicitly exclude non-T20 formats
        non_t20 = ['test', 'odi', 'one day', 'one-day', '50 over', '50-over', 'first class']
        for indicator in non_t20:
            if indicator in name or indicator in series or indicator in format_str:
                return False

        return False


def get_cricbuzz_scraper() -> CricbuzzScraper:
    """Get a singleton Cricbuzz scraper instance"""
    if not hasattr(get_cricbuzz_scraper, '_instance'):
        get_cricbuzz_scraper._instance = CricbuzzScraper()
    return get_cricbuzz_scraper._instance
