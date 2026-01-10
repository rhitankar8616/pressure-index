"""
ESPN Cricinfo Scraper Module
Fetches live T20 match data from ESPN Cricinfo
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import time

# ESPN Cricinfo API endpoints
CRICINFO_BASE_URL = "https://www.espncricinfo.com"
CRICINFO_LIVE_SCORES_URL = "https://www.espncricinfo.com/live-cricket-score"
CRICINFO_MATCH_API = "https://www.espncricinfo.com/matches/engine/match/{match_id}.json"
CRICINFO_LIVE_API = "https://site.web.api.espn.com/apis/site/v2/sports/cricket/{league}/scoreboard"

# ESPN Cricket League IDs for comprehensive T20 coverage
# These IDs are used to fetch matches from different leagues
# UPDATED 2025 - All major T20 leagues worldwide
ESPN_LEAGUE_IDS = {
    # International Cricket
    8676: 'International T20I',
    11571: 'T20I Series',

    # Major Franchise Leagues - 2025 UPDATED IDS
    8048: 'Indian Premier League (IPL)',
    10388: 'Big Bash League (BBL)',
    15103: 'SA20 2024-25',  # Updated SA20 league ID
    11497: 'SA20 (Legacy)',  # Keep legacy ID as fallback
    8653: 'Bangladesh Premier League (BPL)',
    15104: 'BPL 2024-25',  # Updated BPL ID
    6960: 'Caribbean Premier League (CPL)',
    8679: 'Pakistan Super League (PSL)',
    12504: 'Lanka Premier League (LPL)',
    14636: 'ILT20 (UAE)',

    # England Domestic
    11701: 'The Hundred',
    6158: 'T20 Blast (England)',
    6119: 'Vitality Blast',

    # Other Major Leagues
    14335: 'Nepal Premier League',
    13423: 'Major League Cricket (USA)',
    14012: 'Bangladesh T20',

    # Additional Leagues
    12741: 'Super Smash (New Zealand)',
    11338: 'CSA T20 Challenge (South Africa)',
    12177: 'T20 World Cup',
    8044: 'T20 World Cup Qualifier',

    # Women's Leagues
    11476: 'Women\'s Big Bash League',
    12633: 'Women\'s Premier League (WPL)',

    # Additional fallback IDs - trying broader ranges
    **{i: f'League {i}' for i in range(15100, 15120)},  # Recent league IDs
}

# Headers to mimic browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.espncricinfo.com/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
}


class CricinfoScraper:
    """Class to scrape live T20 match data from ESPN Cricinfo"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 10  # seconds - reduced for more frequent checks
    
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

    def _discover_live_match_ids(self) -> List[str]:
        """
        Scrape ESPN Cricinfo main pages to discover live match IDs
        This is the most reliable method as it gets matches directly from the website
        """
        match_ids = []

        try:
            # Try multiple ESPN pages INCLUDING league-specific pages
            pages_to_check = [
                "https://www.espncricinfo.com/live-cricket-score",
                "https://www.espncricinfo.com/",
                "https://www.espncricinfo.com/live-cricket-match-schedule-fixtures",
                "https://www.espncricinfo.com/series/sa20-2024-25-1441053",  # SA20 current season
                "https://www.espncricinfo.com/series/bpl-2024-25-1432217",   # BPL current season
                "https://www.espncricinfo.com/series/big-bash-league-2024-25-1437600",  # BBL
            ]

            for page_url in pages_to_check:
                try:
                    response = self.session.get(page_url, timeout=15)
                    if response.status_code != 200:
                        continue

                    html_content = response.text
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Method 1: Look for match IDs in ALL links and text
                    # ESPN Cricinfo uses URLs like: /series/{series_id}/{match_id}/live-cricket-score

                    # Search in links
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        # Pattern 1: /series/{series}/{match_id}/live-cricket-score
                        match = re.search(r'/series/[^/]+/(\d+)/live-cricket-score', href)
                        if match:
                            match_id = match.group(1)
                            if match_id not in match_ids and len(match_id) >= 6:
                                match_ids.append(match_id)
                                print(f"Found match ID in link: {match_id}")

                        # Pattern 2: /live-cricket-scores/{match_id}/
                        match = re.search(r'/live-cricket-scores/(\d+)/', href)
                        if match:
                            match_id = match.group(1)
                            if match_id not in match_ids and len(match_id) >= 6:
                                match_ids.append(match_id)
                                print(f"Found match ID in live scores: {match_id}")

                        # Pattern 3: event={match_id}
                        match = re.search(r'event=(\d+)', href)
                        if match:
                            match_id = match.group(1)
                            if match_id not in match_ids and len(match_id) >= 6:
                                match_ids.append(match_id)
                                print(f"Found match ID in event: {match_id}")

                    # Method 2: Search raw HTML for match ID patterns
                    # Sometimes IDs are in data attributes or JavaScript
                    all_match_ids = re.findall(r'(?:match[_-]?id|event[_-]?id)["\s:]+(\d{6,8})', html_content, re.IGNORECASE)
                    for match_id in all_match_ids:
                        if match_id not in match_ids:
                            match_ids.append(match_id)
                            print(f"Found match ID in HTML: {match_id}")

                    # Method 3: Look for embedded JSON data
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string:
                            # Look for JSON with match/event IDs
                            try:
                                # Try to extract JSON objects
                                json_matches = re.findall(r'\{[^{}]{50,2000}?\}', script.string)
                                for json_str in json_matches[:20]:  # Limit to avoid processing too much
                                    try:
                                        data = json.loads(json_str)
                                        self._extract_match_ids_from_json(data, match_ids)
                                    except:
                                        continue
                            except:
                                continue

                except Exception as e:
                    print(f"Error checking page {page_url}: {e}")
                    continue

        except Exception as e:
            print(f"Error discovering match IDs: {e}")

        print(f"Total discovered match IDs: {len(match_ids)}")
        return match_ids

    def _extract_match_ids_from_json(self, data, match_ids: List[str]):
        """Recursively extract match IDs from JSON data"""
        if isinstance(data, dict):
            # Check for id field
            if 'id' in data and isinstance(data['id'], (str, int)):
                match_id = str(data['id'])
                if match_id.isdigit() and len(match_id) >= 6:  # ESPN match IDs are typically 6-7 digits
                    if match_id not in match_ids:
                        match_ids.append(match_id)

            # Check for eventId or matchId fields
            for key in ['eventId', 'matchId', 'event_id', 'match_id']:
                if key in data:
                    match_id = str(data[key])
                    if match_id.isdigit() and match_id not in match_ids:
                        match_ids.append(match_id)

            # Recurse into nested dicts
            for value in data.values():
                self._extract_match_ids_from_json(value, match_ids)

        elif isinstance(data, list):
            for item in data:
                self._extract_match_ids_from_json(item, match_ids)

    def get_live_matches(self) -> List[Dict]:
        """
        Fetch all live T20 matches from multiple sources

        Returns:
            List of match dictionaries with basic info
        """
        cached = self._get_cached('live_matches')
        if cached:
            return cached

        matches = []

        try:
            # Method 0: Use Direct API (MOST RELIABLE - ESPN's internal API)
            print("Fetching from ESPN's comprehensive internal API...")
            try:
                from src.utils.direct_api_scraper import get_direct_api_scraper
                direct_scraper = get_direct_api_scraper()
                all_matches = direct_scraper.get_all_live_matches()

                print(f"Direct API found {len(all_matches)} total matches")

                for match in all_matches:
                    # Check if it's T20 and filter appropriately
                    if self._is_t20_match(match):
                        # Check if live or about to start
                        if match.get('state') in ['in', 'pre']:
                            matches.append(match)
                            print(f"Added from Direct API: {match['name']}")

            except Exception as e:
                print(f"Error with Direct API: {e}")
                import traceback
                traceback.print_exc()

            # Method 0b: Scrape ESPN Cricinfo main page for live match links
            print("Scraping ESPN Cricinfo main page for live matches...")
            try:
                discovered_ids = self._discover_live_match_ids()
                if discovered_ids:
                    print(f"Discovered {len(discovered_ids)} live match IDs from ESPN main page")
                    for match_id in discovered_ids:
                        # Avoid duplicates
                        if any(m['match_id'] == str(match_id) for m in matches):
                            continue

                        # Get match details directly
                        match_details = self.get_match_details(str(match_id))
                        if match_details:
                            # Create match_info structure
                            match_info = {
                                'match_id': str(match_id),
                                'name': f"{match_details['team1']} vs {match_details['team2']}",
                                'short_name': f"{match_details['team1']} v {match_details['team2']}",
                                'status': match_details['status'],
                                'venue': match_details['venue'],
                                'series': match_details['series'],
                                'is_live': True,
                                'source': 'espn',
                                'teams': {
                                    'team1': {'name': match_details['team1']},
                                    'team2': {'name': match_details['team2']}
                                }
                            }
                            if self._is_t20_match(match_info):
                                matches.append(match_info)
                                print(f"Added from discovery: {match_info['name']}")
            except Exception as e:
                print(f"Error discovering live matches from main page: {e}")

            # Method 1: Try the main ESPN cricket scoreboard (catches ALL cricket)
            print("Fetching from main ESPN cricket scoreboard API...")
            try:
                main_url = "https://site.web.api.espn.com/apis/site/v2/sports/cricket/scoreboard"
                response = self.session.get(main_url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])

                    for event in events:
                        match_info = self._parse_espn_event(event)
                        if match_info:
                            status_state = event.get('status', {}).get('type', {}).get('state', '')
                            if status_state in ['in', 'pre']:
                                if self._is_t20_match(match_info):
                                    match_info['source'] = 'espn'
                                    if not any(m['match_id'] == match_info['match_id'] for m in matches):
                                        matches.append(match_info)
                                        print(f"Found from API: {match_info['name']} (ID: {match_info['match_id']})")
            except Exception as e:
                print(f"Error with main ESPN scoreboard API: {e}")

            # Method 2: Try ESPN API endpoints for specific leagues
            print(f"Fetching from {len(ESPN_LEAGUE_IDS)} specific league APIs...")
            league_ids = list(ESPN_LEAGUE_IDS.keys())

            for league_id in league_ids:
                api_url = f"https://site.web.api.espn.com/apis/site/v2/sports/cricket/{league_id}/scoreboard"

                try:
                    response = self.session.get(api_url, timeout=10)

                    if response.status_code == 200:
                        data = response.json()
                        events = data.get('events', [])

                        for event in events:
                            match_info = self._parse_espn_event(event)
                            if match_info:
                                # Check if the match is actually live or in progress
                                status_state = event.get('status', {}).get('type', {}).get('state', '')
                                if status_state in ['in', 'pre']:  # 'in' = in progress, 'pre' = scheduled
                                    if self._is_t20_match(match_info):
                                        match_info['source'] = 'espn'
                                        match_info['league'] = ESPN_LEAGUE_IDS.get(league_id, 'Unknown')
                                        # Avoid duplicates
                                        if not any(m['match_id'] == match_info['match_id'] for m in matches):
                                            matches.append(match_info)
                                            print(f"Found from {ESPN_LEAGUE_IDS[league_id]}: {match_info['name']}")
                except Exception as e:
                    # Silent fail for individual leagues
                    pass

            # Try ESPN fallback scraping
            fallback_matches = self._scrape_live_matches_fallback()
            for fm in fallback_matches:
                if not any(m['match_id'] == fm['match_id'] for m in matches):
                    fm['source'] = 'espn'
                    matches.append(fm)

            # Try Cricbuzz as additional fallback for smaller leagues
            try:
                from src.utils.cricbuzz_scraper import get_cricbuzz_scraper
                cricbuzz = get_cricbuzz_scraper()
                cricbuzz_matches = cricbuzz.get_live_matches()

                for cm in cricbuzz_matches:
                    # Avoid duplicates by checking team names
                    is_duplicate = False
                    for m in matches:
                        m_teams = {m.get('teams', {}).get('team1', {}).get('name', '').lower(),
                                  m.get('teams', {}).get('team2', {}).get('name', '').lower()}
                        c_teams = {cm.get('teams', {}).get('team1', {}).get('name', '').lower(),
                                  cm.get('teams', {}).get('team2', {}).get('name', '').lower()}

                        # If both teams match, it's likely the same match
                        if m_teams == c_teams and '' not in m_teams:
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        matches.append(cm)

            except Exception as e:
                print(f"Cricbuzz fallback error: {e}")

        except Exception as e:
            print(f"Error fetching live matches: {e}")
            # Try fallback scraping method
            matches = self._scrape_live_matches_fallback()

        self._set_cache('live_matches', matches)
        return matches
    
    def _scrape_live_matches_fallback(self) -> List[Dict]:
        """Fallback method to scrape live matches from HTML"""
        matches = []

        try:
            # Try main live scores page
            response = self.session.get(CRICINFO_LIVE_SCORES_URL, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for embedded JSON data
                scripts = soup.find_all('script', type='application/json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        # Try to extract matches from JSON
                        if 'props' in data and 'pageProps' in data['props']:
                            page_data = data['props']['pageProps']
                            if 'data' in page_data:
                                events = page_data['data'].get('content', {}).get('matches', [])
                                for event in events:
                                    match_info = self._parse_espn_event(event)
                                    if match_info and self._is_t20_match(match_info):
                                        if not any(m['match_id'] == match_info['match_id'] for m in matches):
                                            matches.append(match_info)
                    except:
                        continue

                # Also try traditional HTML scraping
                match_cards = soup.find_all('div', class_=re.compile(r'match'))
                for card in match_cards:
                    match_info = self._parse_match_card(card)
                    if match_info and self._is_t20_match(match_info):
                        if not any(m['match_id'] == match_info['match_id'] for m in matches):
                            matches.append(match_info)

        except Exception as e:
            print(f"Fallback scraping error: {e}")

        return matches
    
    def _parse_espn_event(self, event: Dict) -> Optional[Dict]:
        """Parse ESPN API event data"""
        try:
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) < 2:
                return None
            
            team1 = competitors[0]
            team2 = competitors[1]
            
            match_info = {
                'match_id': event.get('id', ''),
                'name': event.get('name', ''),
                'short_name': event.get('shortName', ''),
                'status': event.get('status', {}).get('type', {}).get('description', ''),
                'status_detail': event.get('status', {}).get('type', {}).get('detail', ''),
                'venue': competition.get('venue', {}).get('fullName', ''),
                'series': event.get('season', {}).get('name', ''),
                'format': event.get('format', ''),
                'is_live': event.get('status', {}).get('type', {}).get('state', '') == 'in',
                'teams': {
                    'team1': {
                        'name': team1.get('team', {}).get('displayName', ''),
                        'short_name': team1.get('team', {}).get('abbreviation', ''),
                        'score': team1.get('score', ''),
                        'is_batting': team1.get('order', 1) == competition.get('order', 1)
                    },
                    'team2': {
                        'name': team2.get('team', {}).get('displayName', ''),
                        'short_name': team2.get('team', {}).get('abbreviation', ''),
                        'score': team2.get('score', ''),
                        'is_batting': team2.get('order', 2) == competition.get('order', 1)
                    }
                }
            }
            
            return match_info
        
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None
    
    def _parse_match_card(self, card) -> Optional[Dict]:
        """Parse match card HTML element"""
        try:
            # Extract match ID from link
            link = card.find('a', href=True)
            if not link:
                return None
            
            href = link['href']
            match_id = re.search(r'/(\d+)/', href)
            if match_id:
                match_id = match_id.group(1)
            else:
                return None
            
            # Extract team names and scores
            team_elements = card.find_all('div', class_=re.compile(r'team'))
            teams = []
            
            for team_el in team_elements[:2]:
                name_el = team_el.find('span', class_=re.compile(r'name'))
                score_el = team_el.find('span', class_=re.compile(r'score'))
                
                teams.append({
                    'name': name_el.get_text(strip=True) if name_el else '',
                    'score': score_el.get_text(strip=True) if score_el else ''
                })
            
            if len(teams) < 2:
                return None
            
            # Extract status
            status_el = card.find('span', class_=re.compile(r'status'))
            status = status_el.get_text(strip=True) if status_el else ''
            
            return {
                'match_id': match_id,
                'name': f"{teams[0]['name']} vs {teams[1]['name']}",
                'status': status,
                'is_live': 'live' in status.lower(),
                'teams': {
                    'team1': teams[0],
                    'team2': teams[1]
                }
            }
        
        except Exception:
            return None
    
    def _is_t20_match(self, match_info: Dict) -> bool:
        """Check if match is a T20 format"""
        name = match_info.get('name', '').lower()
        series = match_info.get('series', '').lower()
        format_str = match_info.get('format', '').lower()

        t20_indicators = [
            # Generic T20 formats
            't20', 'twenty20', 'twenty-20', 't-20',

            # International
            't20i', 't20 international', 'international t20',

            # Major Franchise Leagues
            'ipl', 'indian premier league',
            'bbl', 'big bash league', 'big bash',
            'sa20', 'sa 20', 'super giants', 'pretoria capitals', 'mi cape town', 'paarl royals', 'joburg super kings', 'sunrisers eastern cape', 'durban',
            'cpl', 'caribbean premier league', 'st kitts', 'guyana', 'jamaica', 'barbados', 'trinbago', 'antigua',
            'psl', 'pakistan super league', 'karachi kings', 'lahore qalandars', 'multan sultans', 'islamabad united', 'peshawar zalmi', 'quetta gladiators',
            'bpl', 'bangladesh premier league', 'dhaka', 'chattogram', 'sylhet', 'rangpur', 'khulna', 'comilla',
            'lpl', 'lanka premier league', 'colombo', 'kandy', 'galle', 'jaffna',
            'ilt20', 'emirates league', 'dubai capitals', 'abu dhabi', 'sharjah warriors', 'gulf giants', 'desert vipers',

            # England Domestic
            'hundred', 'the hundred', 'brave', 'invincibles', 'fire', 'originals', 'phoenix', 'rockets', 'spirit', 'superchargers',
            'blast', 't20 blast', 'vitality blast',

            # Other Major Leagues
            'major league cricket', 'mlc', 'usa cricket',
            'nepal premier league', 'npl', 'nepal t20',
            'super smash', 'new zealand t20',
            'csa t20', 'mzansi super league',

            # Tournament Identifiers
            't20 world cup', 'world t20', 'wt20',
            'asia cup t20',
            'champions league',

            # Women's Leagues
            'wbbl', 'women\'s big bash',
            'wpl', 'women\'s premier league',

            # Team Name Keywords (helps catch franchise teams)
            'super kings', 'knight riders', 'sunrisers', 'royal challengers',
            'riders', 'royals', 'challengers', 'capitals', 'knights', 'warriors', 'titans', 'giants',
        ]

        for indicator in t20_indicators:
            if indicator in name or indicator in series or indicator in format_str:
                return True

        # Check if it's specifically NOT a test or ODI
        non_t20 = ['test', 'odi', 'one day', 'one-day', '50 over', '50-over']
        for indicator in non_t20:
            if indicator in name.lower() or indicator in series.lower():
                return False

        return False

    def _get_match_from_scoreboard(self, match_id: str) -> Optional[Dict]:
        """
        Extract match details from scoreboard API
        This works for all leagues including BPL, IPL, etc.
        """
        try:
            # Try all league IDs to find the match
            for league_id in ESPN_LEAGUE_IDS.keys():
                api_url = f"https://site.web.api.espn.com/apis/site/v2/sports/cricket/{league_id}/scoreboard"

                try:
                    response = self.session.get(api_url, timeout=10)
                    if response.status_code != 200:
                        continue

                    data = response.json()
                    events = data.get('events', [])

                    # Find our match
                    for event in events:
                        if str(event.get('id')) == str(match_id):
                            # Found the match, extract details
                            return self._parse_scoreboard_match(event, match_id)

                except Exception:
                    continue

            return None

        except Exception as e:
            print(f"Error getting match from scoreboard: {e}")
            return None

    def _parse_scoreboard_match(self, event: Dict, match_id: str) -> Optional[Dict]:
        """Parse match data from scoreboard API event"""
        try:
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])

            if len(competitors) < 2:
                return None

            # Get teams
            team1 = competitors[0]
            team2 = competitors[1]

            # Get status
            status = competition.get('status', {})
            period = status.get('period', 1)  # 1 = first innings, 2 = second innings

            # Find which team is batting (has isBatting=true in current innings)
            batting_team = None
            bowling_team = None
            current_innings_data = None

            for comp in competitors:
                linescores = comp.get('linescores', [])
                for linescore in linescores:
                    if linescore.get('isCurrent') == 1:  # Current innings
                        if linescore.get('isBatting'):
                            batting_team = comp.get('team', {}).get('displayName', '')
                            current_innings_data = linescore
                        else:
                            bowling_team = comp.get('team', {}).get('displayName', '')

            # Get target if second innings
            target = None
            is_second_innings = period == 2

            if is_second_innings:
                # Target is the opponent's first innings score + 1
                # Find the team that is NOT currently batting (bowling team batted first)
                for comp in competitors:
                    team_name = comp.get('team', {}).get('displayName', '')
                    # This is the bowling team (batted in first innings)
                    if team_name and team_name != batting_team:
                        linescores = comp.get('linescores', [])
                        for linescore in linescores:
                            # Get their first innings score (period 1 or the completed innings)
                            if linescore.get('period') == 1 or not linescore.get('isCurrent'):
                                first_innings_runs = linescore.get('runs', 0)
                                if first_innings_runs > 0:
                                    target = first_innings_runs + 1
                                    break
                        if target:
                            break

                # Fallback: check all linescores with period=1
                if not target:
                    for comp in competitors:
                        linescores = comp.get('linescores', [])
                        for linescore in linescores:
                            if linescore.get('period') == 1:
                                first_innings_runs = linescore.get('runs', 0)
                                if first_innings_runs > 0:
                                    target = first_innings_runs + 1
                                    break
                        if target:
                            break

            # Extract current innings details
            runs = 0
            wickets = 0
            overs = 0.0

            if current_innings_data:
                runs = current_innings_data.get('runs', 0)
                wickets = current_innings_data.get('wickets', 0)
                overs = current_innings_data.get('overs', 0.0)

            match_details = {
                'match_id': match_id,
                'team1': team1.get('team', {}).get('displayName', ''),
                'team2': team2.get('team', {}).get('displayName', ''),
                'venue': competition.get('venue', {}).get('fullName', ''),
                'series': event.get('season', {}).get('name', ''),
                'status': status.get('type', {}).get('description', ''),
                'current_innings': {
                    'innings_number': period,
                    'batting_team': batting_team or '',
                    'bowling_team': bowling_team or '',
                    'runs': runs,
                    'wickets': wickets,
                    'overs': overs,
                    'target': target,
                    'is_second_innings': is_second_innings
                },
                'batsmen': [],  # Not available in scoreboard API
                'bowlers': [],  # Not available in scoreboard API
                'ball_by_ball': []  # Not available in scoreboard API
            }

            return match_details

        except Exception as e:
            print(f"Error parsing scoreboard match: {e}")
            return None

    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """
        Fetch detailed match data including ball-by-ball info

        Args:
            match_id: ESPN match ID

        Returns:
            Detailed match data dictionary
        """
        cache_key = f'match_{match_id}'
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            # First, try to get from scoreboard API (works for all leagues)
            match_details = self._get_match_from_scoreboard(match_id)
            if match_details:
                self._set_cache(cache_key, match_details)
                return match_details

            # Try old JSON endpoint (may not work for all leagues)
            json_url = f"https://www.espncricinfo.com/matches/engine/match/{match_id}.json"
            response = self.session.get(json_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                match_details = self._parse_match_json(data, match_id)
                if match_details:
                    self._set_cache(cache_key, match_details)
                    return match_details

            # Fallback to HTML scraping
            match_url = f"https://www.espncricinfo.com/series/{match_id}/live-cricket-score"
            response = self.session.get(match_url, timeout=10)

            if response.status_code == 200:
                match_details = self._parse_match_html(response.text, match_id)
                if match_details:
                    self._set_cache(cache_key, match_details)
                    return match_details

        except Exception as e:
            print(f"Error fetching match details: {e}")

        return None
    
    def _parse_match_json(self, data: Dict, match_id: str) -> Optional[Dict]:
        """Parse match JSON data"""
        try:
            match = data.get('match', {})
            innings = data.get('innings', [])
            
            # Determine current innings
            current_innings = None
            for inn in innings:
                if inn.get('live_current', False) or inn.get('live', False):
                    current_innings = inn
                    break
            
            if not current_innings and innings:
                current_innings = innings[-1]
            
            # Parse batting team info
            batting_team = current_innings.get('batting_team_name', '') if current_innings else ''
            bowling_team = current_innings.get('bowling_team_name', '') if current_innings else ''
            
            # Get scores
            runs = current_innings.get('runs', 0) if current_innings else 0
            wickets = current_innings.get('wickets', 0) if current_innings else 0
            overs = current_innings.get('overs', 0) if current_innings else 0
            
            # Parse target (if second innings)
            target = None
            is_second_innings = False
            
            if len(innings) >= 2:
                first_innings = innings[0]
                target = first_innings.get('runs', 0) + 1
                is_second_innings = True
            
            # Get batsmen and bowlers
            batsmen = data.get('batsmen', [])
            bowlers = data.get('bowlers', [])
            
            match_details = {
                'match_id': match_id,
                'team1': match.get('team1_name', ''),
                'team2': match.get('team2_name', ''),
                'venue': match.get('ground_name', ''),
                'series': match.get('series_name', ''),
                'status': match.get('match_status', ''),
                'current_innings': {
                    'innings_number': len(innings),
                    'batting_team': batting_team,
                    'bowling_team': bowling_team,
                    'runs': runs,
                    'wickets': wickets,
                    'overs': overs,
                    'target': target,
                    'is_second_innings': is_second_innings
                },
                'batsmen': [
                    {
                        'name': b.get('batsman_name', ''),
                        'runs': b.get('runs', 0),
                        'balls': b.get('balls_faced', 0),
                        'on_strike': b.get('on_strike', False)
                    }
                    for b in batsmen[:2]
                ],
                'bowlers': [
                    {
                        'name': b.get('bowler_name', ''),
                        'overs': b.get('overs', 0),
                        'runs': b.get('conceded', 0),
                        'wickets': b.get('wickets', 0)
                    }
                    for b in bowlers[:1]
                ],
                'ball_by_ball': self._get_ball_by_ball(data)
            }
            
            return match_details
        
        except Exception as e:
            print(f"Error parsing match JSON: {e}")
            return None
    
    def _get_ball_by_ball(self, data: Dict) -> List[Dict]:
        """Extract ball-by-ball data from match JSON"""
        ball_data = []
        
        try:
            comms = data.get('comms', [])
            
            for over_data in comms:
                balls = over_data.get('ball', [])
                for ball in balls:
                    ball_info = {
                        'over': ball.get('overs_unique', ''),
                        'runs': ball.get('runs', 0),
                        'batsman': ball.get('batsman', ''),
                        'bowler': ball.get('bowler', ''),
                        'is_wicket': ball.get('wicket', False) or 'wicket' in ball.get('event', '').lower(),
                        'commentary': ball.get('commentary', '')
                    }
                    ball_data.append(ball_info)
        
        except Exception as e:
            print(f"Error extracting ball-by-ball: {e}")
        
        return ball_data
    
    def _parse_match_html(self, html: str, match_id: str) -> Optional[Dict]:
        """Parse match HTML page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for embedded JSON data
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'window.__INITIAL_STATE__' in script.string:
                    json_str = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', 
                                        script.string, re.DOTALL)
                    if json_str:
                        data = json.loads(json_str.group(1))
                        return self._parse_embedded_json(data, match_id)
            
            # Manual HTML parsing
            return self._parse_match_html_manual(soup, match_id)
        
        except Exception as e:
            print(f"Error parsing match HTML: {e}")
            return None
    
    def _parse_embedded_json(self, data: Dict, match_id: str) -> Optional[Dict]:
        """Parse embedded JSON from HTML page"""
        try:
            match_data = data.get('match', {}).get('detail', {})
            
            return {
                'match_id': match_id,
                'team1': match_data.get('team1', {}).get('name', ''),
                'team2': match_data.get('team2', {}).get('name', ''),
                'venue': match_data.get('ground', {}).get('name', ''),
                'status': match_data.get('status', ''),
                # Add more fields as available
            }
        
        except Exception:
            return None
    
    def _parse_match_html_manual(self, soup, match_id: str) -> Optional[Dict]:
        """Manual HTML parsing fallback"""
        try:
            # Extract team names
            team_elements = soup.find_all('span', class_=re.compile(r'team-name'))
            teams = [el.get_text(strip=True) for el in team_elements[:2]]
            
            # Extract score
            score_elements = soup.find_all('span', class_=re.compile(r'score'))
            scores = [el.get_text(strip=True) for el in score_elements[:2]]
            
            return {
                'match_id': match_id,
                'team1': teams[0] if teams else '',
                'team2': teams[1] if len(teams) > 1 else '',
                'scores': scores,
            }
        
        except Exception:
            return None
    
    def get_ball_by_ball_data(self, match_id: str) -> List[Dict]:
        """
        Fetch ball-by-ball data for a match using playbyplay endpoint

        Args:
            match_id: ESPN match ID

        Returns:
            List of ball-by-ball data dictionaries with cumulative runs/wickets
        """
        try:
            # Try all league IDs to find the match
            for league_id in ESPN_LEAGUE_IDS.keys():
                url = f"https://site.web.api.espn.com/apis/site/v2/sports/cricket/{league_id}/playbyplay?contentorigin=espn&event={match_id}"

                try:
                    # ESPN API uses pagination - need to fetch all pages
                    all_items = []
                    page_index = 1
                    max_pages = 20  # Safeguard against infinite loops

                    while page_index <= max_pages:
                        paginated_url = f"{url}&page={page_index}"
                        response = self.session.get(paginated_url, timeout=10)

                        if response.status_code != 200:
                            if page_index == 1:
                                # First page failed, try next league
                                break
                            else:
                                # Subsequent page failed, use what we have
                                break

                        data = response.json()

                        # Try to get commentary items - ESPN API has multiple possible structures
                        commentary = data.get('commentary', {})
                        page_items = commentary.get('items', [])

                        # Alternative: Try plays array (only on first page)
                        if not page_items and page_index == 1:
                            plays = data.get('plays', [])
                            if plays:
                                all_items = plays
                                break

                        # Alternative: Try innings data (only on first page)
                        if not page_items and page_index == 1:
                            innings = data.get('innings', [])
                            for inning in innings:
                                if inning.get('number') == 2:  # Second innings
                                    all_items = inning.get('deliveries', [])
                                    break
                            if all_items:
                                break

                        if not page_items:
                            break  # No more items

                        all_items.extend(page_items)

                        # Check pagination info
                        page_count = commentary.get('pageCount', 1)
                        total_count = commentary.get('count', 0)

                        print(f"Fetched page {page_index}/{page_count} ({len(page_items)} items, {len(all_items)}/{total_count} total)")

                        if page_index >= page_count:
                            break  # Reached last page

                        page_index += 1

                    items = all_items

                    if not items:
                        continue

                    print(f"Found {len(items)} total commentary items for match {match_id}")

                    # Parse and return ball-by-ball data
                    ball_data = []

                    # Process each commentary item
                    for item in items:
                        period = item.get('period', 1)

                        # Also check inningNumber for alternative formats
                        inning_num = item.get('inningNumber', period)

                        # Only process second innings (period/inning 2)
                        if period != 2 and inning_num != 2:
                            continue

                        # Extract score - try both homeScore and awayScore
                        score_str = None
                        home_score = item.get('homeScore', '')
                        away_score = item.get('awayScore', '')

                        # Check which score is for the batting team in second innings
                        if home_score and '/' in str(home_score):
                            score_str = str(home_score)
                        elif away_score and '/' in str(away_score):
                            score_str = str(away_score)

                        # Parse cumulative runs and wickets
                        runs = 0
                        wickets = 0

                        if score_str and '/' in score_str:
                            try:
                                runs_str, wickets_str = score_str.split('/')
                                runs = int(runs_str.strip())
                                wickets = int(wickets_str.strip())
                            except (ValueError, AttributeError, TypeError):
                                pass

                        # Skip if no valid score (might be first innings or non-delivery)
                        if runs == 0 and wickets == 0 and len(ball_data) > 0:
                            # Check if this is actually a delivery with runs
                            score_value = item.get('scoreValue', 0)
                            if score_value == 0:
                                continue  # Skip non-scoring deliveries without score info

                        # Determine if it's a wicket
                        play_type = item.get('playType', {})
                        if isinstance(play_type, dict):
                            play_desc = play_type.get('description', '').lower()
                        else:
                            play_desc = str(play_type).lower()

                        is_wicket = 'wicket' in play_desc or 'out' in play_desc or 'dismissal' in play_desc

                        # Get batsman and bowler names
                        athletes = item.get('athletesInvolved', [])
                        batsman = ''
                        bowler = ''

                        if len(athletes) > 0:
                            # Usually bowler is first, batsman is second
                            bowler = athletes[0].get('displayName', '') or athletes[0].get('name', '')
                            if len(athletes) > 1:
                                batsman = athletes[1].get('displayName', '') or athletes[1].get('name', '')

                        # Get runs scored on this delivery
                        runs_scored = item.get('scoreValue', 0)

                        # Get ball sequence/ID for ordering
                        sequence = item.get('sequenceNumber', item.get('sequence', item.get('id', 0)))

                        ball_data.append({
                            'runs': runs,                    # Cumulative runs
                            'wickets': wickets,              # Cumulative wickets
                            'is_wicket': is_wicket,          # Was dismissal on this ball
                            'runs_scored': runs_scored,      # Runs scored on this ball
                            'batsman': batsman,
                            'bowler': bowler,
                            'text': item.get('shortText', item.get('text', '')),
                            'sequence': sequence
                        })

                    if not ball_data:
                        continue

                    print(f"Parsed {len(ball_data)} balls from second innings")

                    # Sort by sequence to get chronological order
                    ball_data.sort(key=lambda x: x['sequence'])

                    # Check if we need to reverse (some APIs use descending sequence)
                    if len(ball_data) >= 2:
                        # If first ball has higher sequence than last, reverse
                        if ball_data[0]['sequence'] > ball_data[-1]['sequence']:
                            ball_data.reverse()
                            print("Reversed ball order (descending sequence)")

                    # Filter out invalid entries (both runs and wickets are 0 after first ball)
                    if len(ball_data) > 1:
                        filtered_data = [ball_data[0]]  # Keep first ball
                        for i in range(1, len(ball_data)):
                            ball = ball_data[i]
                            # Keep if has valid score or is first ball
                            if ball['runs'] > 0 or ball['wickets'] > 0 or ball['runs_scored'] > 0:
                                filtered_data.append(ball)
                        ball_data = filtered_data

                    print(f"Returning {len(ball_data)} valid balls")
                    return ball_data

                except Exception as e:
                    print(f"Error parsing league {league_id}: {e}")
                    continue

            print("No ball-by-ball data found in any league API")

            # Final fallback: Try scraping commentary page directly
            print("Attempting to scrape commentary page as fallback...")
            return self._scrape_commentary_page(match_id)

        except Exception as e:
            print(f"Error fetching ball-by-ball data: {e}")
            return []

    def _scrape_commentary_page(self, match_id: str) -> List[Dict]:
        """
        Fallback: Scrape ball-by-ball commentary directly from ESPN Cricinfo page

        Args:
            match_id: ESPN match ID

        Returns:
            List of ball-by-ball data
        """
        try:
            # Try commentary page URL
            url = f"https://www.espncricinfo.com/series/{match_id}/commentary"

            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Commentary page returned {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for commentary items in the HTML
            # ESPN uses various class names, try multiple patterns
            commentary_items = soup.find_all(['div', 'article'], class_=re.compile(r'(commentary|Collapsible|ds-p-4)'))

            if not commentary_items:
                print("No commentary items found in HTML")
                return []

            ball_data = []
            cumulative_runs = 0
            cumulative_wickets = 0

            for item in commentary_items:
                # Extract over and ball number
                over_text = item.find(string=re.compile(r'\d+\.\d+'))
                if not over_text:
                    continue

                # Extract commentary text
                text_elem = item.find(['p', 'span'], class_=re.compile(r'(commentary|text)'))
                if not text_elem:
                    continue

                text = text_elem.get_text(strip=True)

                # Try to extract runs from text
                runs_on_ball = 0
                if 'no runs' in text.lower() or 'no run' in text.lower():
                    runs_on_ball = 0
                elif 'FOUR' in text or '4 runs' in text:
                    runs_on_ball = 4
                elif 'SIX' in text or '6 runs' in text:
                    runs_on_ball = 6
                else:
                    # Try to extract number
                    runs_match = re.search(r'(\d+) runs?', text)
                    if runs_match:
                        runs_on_ball = int(runs_match.group(1))

                cumulative_runs += runs_on_ball

                # Check for wicket
                is_wicket = 'OUT' in text or 'WICKET' in text or 'W' in text or 'wicket' in text.lower()
                if is_wicket:
                    cumulative_wickets += 1

                ball_data.append({
                    'runs': cumulative_runs,
                    'wickets': cumulative_wickets,
                    'is_wicket': is_wicket,
                    'runs_scored': runs_on_ball,
                    'text': text,
                    'batsman': '',
                    'bowler': '',
                    'sequence': len(ball_data)
                })

            if ball_data:
                # Reverse because commentary is usually newest first
                ball_data.reverse()
                print(f"Scraped {len(ball_data)} balls from commentary page")

            return ball_data

        except Exception as e:
            print(f"Error scraping commentary page: {e}")
            return []

    def get_live_score_data(self, match_id: str) -> Optional[Dict]:
        """
        Get current live score data formatted for PI calculation
        
        Returns dict with:
        - target: Target score (if 2nd innings)
        - runs_scored: Current runs
        - wickets_lost: Wickets fallen
        - balls_faced: Balls bowled
        - is_second_innings: Boolean
        """
        match_details = self.get_match_details(match_id)
        
        if not match_details:
            return None
        
        current = match_details.get('current_innings', {})
        
        # Parse overs to balls
        overs_str = str(current.get('overs', 0))
        if '.' in overs_str:
            parts = overs_str.split('.')
            completed_overs = int(parts[0])
            balls_in_over = int(parts[1])
            balls_faced = (completed_overs * 6) + balls_in_over
        else:
            balls_faced = int(float(overs_str) * 6)
        
        return {
            'match_id': match_id,
            'batting_team': current.get('batting_team', ''),
            'bowling_team': current.get('bowling_team', ''),
            'target': current.get('target'),
            'runs_scored': current.get('runs', 0),
            'wickets_lost': current.get('wickets', 0),
            'balls_faced': balls_faced,
            'overs': current.get('overs', 0),
            'is_second_innings': current.get('is_second_innings', False),
            'batsmen': match_details.get('batsmen', []),
            'bowlers': match_details.get('bowlers', []),
            'venue': match_details.get('venue', ''),
            'series': match_details.get('series', ''),
            'status': match_details.get('status', '')
        }


def get_scraper() -> CricinfoScraper:
    """Get a singleton scraper instance"""
    if not hasattr(get_scraper, '_instance'):
        get_scraper._instance = CricinfoScraper()
    return get_scraper._instance
