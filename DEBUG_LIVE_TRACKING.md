# Live Tracking Debug Information

## Issue Fixed: Incorrect Target and Score Display

### Problem
When tracking the BPL match Sylhet Titans vs Chattogram Royals:
- Actual situation: Sylhet chasing 199, score 82/4
- App showing: Target = 1, Runs needed = -1

### Root Cause Analysis

1. **Target Extraction Issue** (Line 398-427 in cricinfo_scraper.py)
   - The original code was grabbing the first team's first innings score
   - It didn't ensure it was getting the OPPONENT's score (bowling team)
   - When the batting team's score from an earlier match/innings was grabbed, it resulted in target=1

2. **Score Extraction Issue** (Line 720-744 in cricinfo_scraper.py)
   - Only checked `homeScore`, not `awayScore`
   - Depending on which team is home/away, the wrong score could be used

### Fixes Applied

#### Fix 1: Target Extraction (cricinfo_scraper.py:398-427)
```python
# OLD CODE (INCORRECT):
if is_second_innings:
    for comp in competitors:
        linescores = comp.get('linescores', [])
        for linescore in linescores:
            if linescore.get('period') == 1:
                target = linescore.get('runs', 0) + 1
                break

# NEW CODE (CORRECT):
if is_second_innings:
    # Target is the opponent's first innings score + 1
    # Find the team that is NOT currently batting (bowling team batted first)
    for comp in competitors:
        team_name = comp.get('team', {}).get('displayName', '')
        if team_name and team_name != batting_team:
            linescores = comp.get('linescores', [])
            for linescore in linescores:
                if linescore.get('period') == 1 or not linescore.get('isCurrent'):
                    first_innings_runs = linescore.get('runs', 0)
                    if first_innings_runs > 0:
                        target = first_innings_runs + 1
                        break
```

**Why this works:**
- Identifies which team is currently batting
- Gets the OPPONENT team's (bowling team) first innings score
- Adds 1 to get the target (standard cricket scoring)
- Has fallback logic to check all period=1 linescores if needed

#### Fix 2: Ball-by-Ball Score Extraction (cricinfo_scraper.py:720-744)
```python
# OLD CODE (INCORRECT):
score_str = item.get('homeScore', '0/0')

# NEW CODE (CORRECT):
home_score = item.get('homeScore', '')
away_score = item.get('awayScore', '')

if home_score and '/' in home_score:
    score_str = home_score
elif away_score and '/' in away_score:
    score_str = away_score
```

**Why this works:**
- Checks both homeScore and awayScore
- Uses whichever one has valid format (contains '/')
- Handles cases where batting team is home OR away
- More robust error handling with try/except

### Expected Behavior After Fix

For Sylhet Titans vs Chattogram Royals:
- ✅ Target: 199 (Chattogram's first innings + 1)
- ✅ Current Score: 82/4
- ✅ Runs Needed: 117
- ✅ Balls Remaining: calculated correctly
- ✅ Required Run Rate: calculated correctly
- ✅ Pressure Index: calculated based on actual match state

### Data Flow

```
ESPN API Response
    ↓
_get_match_from_scoreboard()
    ↓
_parse_scoreboard_match()
    ↓ (extracts)
- batting_team: "Sylhet Titans"
- bowling_team: "Chattogram Royals"
- period: 2 (second innings)
- target: Chattogram's 1st innings score + 1 = 199
- current_runs: 82
- current_wickets: 4
    ↓
get_live_score_data()
    ↓ (formats for PI calculation)
{
    'target': 199,
    'runs_scored': 82,
    'wickets_lost': 4,
    'balls_faced': calculated from overs,
    'is_second_innings': True
}
    ↓
Live Tracker Page
    ↓
PI Calculator
    ↓
Display: Correct pressure curve
```

### Testing Checklist

When testing the live tracker:

1. **Check Target Display**
   - [ ] Target matches the first innings total + 1
   - [ ] Not showing 0, 1, or nonsensical values

2. **Check Current Score**
   - [ ] Runs and wickets match the actual match
   - [ ] Updates with each ball (if auto-refresh enabled)

3. **Check Calculations**
   - [ ] Runs Needed = Target - Current Runs
   - [ ] Should be positive (unless match won)
   - [ ] Balls Remaining calculated correctly from overs

4. **Check Pressure Index**
   - [ ] PI value makes sense for match state
   - [ ] Higher when behind required rate
   - [ ] Lower when ahead of required rate

5. **Check Ball-by-Ball Curve**
   - [ ] Shows progression from ball 1 to current ball
   - [ ] Cumulative runs increase logically
   - [ ] Wickets show as markers on curve

### Common Issues and Solutions

**Issue**: Target still showing as 1
- **Solution**: Clear browser cache and refresh
- **Check**: Ensure match is actually in second innings (not first)

**Issue**: Score not updating
- **Solution**: Enable auto-refresh or manually click refresh button
- **Check**: Match must be live (not completed or not started)

**Issue**: Wrong team's score shown
- **Solution**: Fixed with homeScore/awayScore logic
- **Verification**: Check that batting_team name matches actual batting team

**Issue**: Ball-by-ball data missing
- **Solution**: Uses estimated curve if API doesn't provide ball-by-ball
- **Note**: Some leagues may not have ball-by-ball commentary available

### Files Modified

1. `/src/utils/cricinfo_scraper.py` (Lines 398-427, 720-744)
   - Enhanced target extraction logic
   - Improved score parsing for ball-by-ball data

### No Changes Needed In

- `live_tracker.py` - Already handles data correctly once it receives it
- `pressure_index.py` - Calculation logic is correct
- Display components - Already format data correctly

The issue was purely in data extraction from the ESPN API, not in the display or calculation logic.
