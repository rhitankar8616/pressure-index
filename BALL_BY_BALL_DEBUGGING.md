# Ball-by-Ball Data Fetching - Debugging Guide

## Overview
This document explains how the app fetches ball-by-ball commentary data from ESPN Cricinfo to create accurate pressure curves for live matches.

## Data Fetching Strategy

The app uses a **multi-layered fallback approach** to ensure we get ball-by-ball data:

### Layer 1: ESPN PlayByPlay API (Primary)
**URL Format**: `https://site.web.api.espn.com/apis/site/v2/sports/cricket/{league_id}/playbyplay?event={match_id}`

**How it works**:
1. Tries all major league IDs (BPL=8653, IPL=8048, BBL=10388, etc.)
2. Fetches JSON response with commentary items
3. Filters for second innings only (period=2)
4. Extracts cumulative runs/wickets from each ball

**Data Structure Expected**:
```json
{
  "commentary": {
    "items": [
      {
        "period": 2,
        "homeScore": "82/4",
        "awayScore": "198/7",
        "scoreValue": 1,
        "playType": {"description": "Single"},
        "athletesInvolved": [
          {"name": "Bowler Name"},
          {"name": "Batsman Name"}
        ],
        "sequence": 450
      }
    ]
  }
}
```

**Alternative Structures Handled**:
- `plays[]` array instead of `commentary.items[]`
- `innings[].deliveries[]` for some formats
- `inningNumber` instead of `period`
- `displayName` or `name` for athlete names
- `sequenceNumber`, `sequence`, or `id` for ordering

### Layer 2: Commentary Page Scraping (Fallback)
**URL Format**: `https://www.espncricinfo.com/series/{match_id}/commentary`

**How it works**:
1. Downloads HTML page
2. Parses commentary items using BeautifulSoup
3. Extracts runs from text (looks for "FOUR", "SIX", "X runs")
4. Detects wickets (looks for "OUT", "WICKET")
5. Builds cumulative runs/wickets

**Text Parsing Patterns**:
- `"no runs"` → 0 runs
- `"FOUR"` or `"4 runs"` → 4 runs
- `"SIX"` or `"6 runs"` → 6 runs
- `"OUT"`, `"WICKET"`, `"wicket"` → wicket fallen
- Regex: `(\d+) runs?` → extracts run count

### Layer 3: Estimation (Last Resort)
If both API and scraping fail, uses realistic estimation (progress^1.2 for runs, progress^1.5 for wickets).

## Debugging Steps

### Step 1: Check Console Output

When you run the app, look for these print statements in the terminal:

```
✓ Good signs:
- "Found 93 commentary items for match 401613"
- "Parsed 93 balls from second innings"
- "Returning 93 valid balls"

⚠️ Warning signs:
- "No ball-by-ball data found in any league API"
- "Attempting to scrape commentary page as fallback..."
- "Commentary page returned 404"
- "No commentary items found in HTML"

✗ Error signs:
- "Error parsing league 8653: ..."
- "Error fetching ball-by-ball data: ..."
```

### Step 2: Check UI Messages

In the Streamlit app:

```
✓ Success:
"✓ Loaded 93 balls of actual commentary data!"
"✓ Pressure curve based on actual ball-by-ball match data from ESPN commentary."

⚠️ Fallback:
"ℹ️ Ball-by-ball commentary not available from ESPN. Using estimated progression..."
"ℹ️ Ball-by-ball data unavailable. Curve shows estimated progression based on current match state"
```

### Step 3: Manual API Testing

Test the API manually to see what data is available:

```bash
# Replace {match_id} with your actual match ID
# BPL League ID: 8653
curl "https://site.web.api.espn.com/apis/site/v2/sports/cricket/8653/playbyplay?event={match_id}" | python -m json.tool > playbyplay.json

# Check the output
cat playbyplay.json
```

**What to look for**:
- Does `commentary.items` exist?
- How many items are there?
- Do items have `period: 2`?
- Do items have `homeScore` or `awayScore`?
- What fields contain the data you need?

### Step 4: Test Commentary Page

Visit the commentary page directly:
```
https://www.espncricinfo.com/series/{match_id}/commentary
```

**Check**:
- Does the page load?
- Is there ball-by-ball commentary visible?
- What HTML structure is used for commentary items?
- Can you see over.ball numbers (e.g., "15.3")?

## Common Issues and Solutions

### Issue 1: "No ball-by-ball data found in any league API"

**Possible Causes**:
1. Match ID is incorrect
2. Match is not in second innings yet
3. League ID is not in the ESPN_LEAGUE_IDS dictionary
4. ESPN API structure changed

**Solutions**:
```python
# Add more league IDs to ESPN_LEAGUE_IDS dictionary in cricinfo_scraper.py:
ESPN_LEAGUE_IDS = {
    8676: 'International T20I',
    8653: 'Bangladesh Premier League (BPL)',
    # Add more as needed
}

# Or manually test the playbyplay endpoint for your league
```

### Issue 2: "Parsed 0 balls from second innings"

**Possible Causes**:
1. All items have `period: 1` (first innings data)
2. Score format is different (not "runs/wickets")
3. Items don't have required fields

**Solutions**:
```python
# Check what period values exist in the data
print(f"Periods in data: {set(item.get('period') for item in items)}")

# Check score format
print(f"Score samples: {[item.get('homeScore') for item in items[:5]]}")

# Adjust filtering logic based on actual structure
```

### Issue 3: Scores Not Increasing Monotonically

**Possible Causes**:
1. Sequence numbers are wrong
2. First innings mixed with second innings
3. Data is in reverse chronological order

**Solutions**:
```python
# Already handled by sorting and reversing logic
# Check if sequence numbers make sense:
print(f"First sequence: {ball_data[0]['sequence']}")
print(f"Last sequence: {ball_data[-1]['sequence']}")
```

### Issue 4: Missing Cumulative Scores

**Possible Causes**:
1. API doesn't provide cumulative scores
2. Score format is different

**Solutions**:
```python
# If API only provides runs per ball, calculate cumulative:
cumulative_runs = 0
for ball in ball_data:
    cumulative_runs += ball['runs_scored']
    ball['runs'] = cumulative_runs
```

## Verification Checklist

When ball-by-ball data is successfully fetched:

- [ ] Number of balls matches expected (should be equal to balls_faced from current state)
- [ ] First ball has runs=0 or small number, wickets=0
- [ ] Last ball has runs matching current score
- [ ] Last ball has wickets matching current wickets
- [ ] Cumulative runs increase monotonically (never decrease)
- [ ] Cumulative wickets increase monotonically (never decrease)
- [ ] Wicket markers appear on pressure curve
- [ ] Pressure curve shows realistic variation (not perfectly smooth)

## Manual Testing Script

Create this test file to debug data fetching:

```python
# test_ball_by_ball.py
import sys
sys.path.insert(0, '.')

from src.utils.cricinfo_scraper import get_scraper

# Replace with your match ID
match_id = "401613"  # Example BPL match

scraper = get_scraper()

print(f"Fetching ball-by-ball data for match {match_id}...")
ball_by_ball = scraper.get_ball_by_ball_data(match_id)

if ball_by_ball:
    print(f"\n✓ Success! Got {len(ball_by_ball)} balls")
    print(f"\nFirst 5 balls:")
    for i, ball in enumerate(ball_by_ball[:5]):
        print(f"  Ball {i+1}: {ball['runs']}/{ball['wickets']} (scored: {ball['runs_scored']})")

    print(f"\nLast 5 balls:")
    for i, ball in enumerate(ball_by_ball[-5:], len(ball_by_ball)-4):
        print(f"  Ball {i}: {ball['runs']}/{ball['wickets']} (scored: {ball['runs_scored']})")

    print(f"\nSample commentary:")
    print(f"  {ball_by_ball[0]['text'][:100]}...")
else:
    print("✗ Failed to get ball-by-ball data")

# Run with: python test_ball_by_ball.py
```

## ESPN API League IDs Reference

Currently supported leagues:

| League ID | League Name |
|-----------|-------------|
| 8676 | International T20I |
| 8653 | Bangladesh Premier League (BPL) |
| 8048 | Indian Premier League (IPL) |
| 10388 | Big Bash League (BBL) |
| 6960 | Caribbean Premier League (CPL) |
| 8679 | Pakistan Super League (PSL) |
| 11497 | SA20 (South Africa) |
| 12504 | Lanka Premier League (LPL) |
| 11701 | The Hundred |
| 6158 | T20 Blast (England) |

If your match is from a different league, you may need to find its ESPN league ID and add it to the dictionary.

## Success Metrics

For a properly functioning ball-by-ball fetch:

1. **Fetch Success Rate**: Should get actual data for 80%+ of live T20 matches
2. **Data Completeness**: Should have all balls from start of second innings to current ball
3. **Data Accuracy**: Final ball should match current live score exactly
4. **Update Speed**: Should fetch data within 2-3 seconds
5. **Curve Quality**: Pressure curve should show realistic match dynamics

## Next Steps for Improvement

If ball-by-ball data is still not working:

1. **Capture Raw API Response**: Save the actual JSON from ESPN to a file and analyze structure
2. **Try Different Endpoints**: ESPN has multiple APIs (v1, v2, v3) - try alternatives
3. **Use Cricbuzz**: Implement Cricbuzz scraper as alternative data source
4. **Cache Incrementally**: Store fetched balls and only fetch new ones on refresh
5. **WebSocket Connection**: Use real-time updates instead of polling

## Contact and Support

If you're still having issues:

1. Check GitHub issues: https://github.com/espn/ESPN-API/issues
2. Share your match ID and league for debugging
3. Capture console output and API responses for analysis
