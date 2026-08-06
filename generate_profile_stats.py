import os
import requests
from datetime import datetime, timedelta

# GraphQL Query to fetch user stats
GRAPHQL_QUERY = """
query($username: String!, $start2024: DateTime!, $end2024: DateTime!, $start2025: DateTime!, $end2025: DateTime!, $start2026: DateTime!, $end2026: DateTime!) {
  user(login: $username) {
    name
    login
    repositories(first: 100, ownerAffiliations: OWNER) {
      nodes {
        stargazerCount
      }
    }
    cal2024: contributionsCollection(from: $start2024, to: $end2024) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
    cal2025: contributionsCollection(from: $start2025, to: $end2025) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
    cal2026: contributionsCollection(from: $start2026, to: $end2026) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""

def fetch_stats(username, token):
    headers = {"Authorization": f"bearer {token}"}
    
    # We query data for 2024, 2025, and 2026
    variables = {
        "username": username,
        "start2024": "2024-01-01T00:00:00Z",
        "end2024": "2024-12-31T23:59:59Z",
        "start2025": "2025-01-01T00:00:00Z",
        "end2025": "2025-12-31T23:59:59Z",
        "start2026": "2026-01-01T00:00:00Z",
        "end2026": "2026-12-31T23:59:59Z"
    }
    
    response = requests.post("https://api.github.com/graphql", json={"query": GRAPHQL_QUERY, "variables": variables}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from GitHub API: {response.text}")
        
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL Errors: {data['errors']}")
        
    return data["data"]["user"]

def calculate_streaks(weeks_list):
    # Flatten all contribution days in order of date
    all_days = []
    for week in weeks_list:
        for day in week["contributionDays"]:
            all_days.append(day)
            
    # Sort days by date string just in case
    all_days.sort(key=lambda x: x["date"])
    
    # Filter to only look up to today
    today_str = datetime.now().strftime("%Y-%m-%d")
    all_days = [d for d in all_days if d["date"] <= today_str]
    
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    # Find active streak and longest streak
    for day in all_days:
        if day["contributionCount"] > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            # Check if this is today or yesterday before resetting current streak
            temp_streak = 0
            
    # Recalculate current streak starting from today/yesterday backwards
    # because if they committed yesterday but not yet today, the streak is still active
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    active_streak = 0
    streak_active = True
    
    for day in reversed(all_days):
        if day["date"] in [today_str, yesterday_str]:
            if day["contributionCount"] > 0:
                # We start counting back
                pass
        
    # Standard logic: trace backwards from end
    temp = 0
    streak_still_alive = False
    
    # Let's check if they committed today or yesterday
    has_today = any(d["contributionCount"] > 0 for d in all_days if d["date"] == today_str)
    has_yesterday = any(d["contributionCount"] > 0 for d in all_days if d["date"] == yesterday_str)
    
    if has_today or has_yesterday:
        # Trace back to count current streak
        for day in reversed(all_days):
            if day["contributionCount"] > 0:
                current_streak += 1
            else:
                # If we hit 0 and it's not today, break the streak
                if day["date"] != today_str:
                    break
                    
    return current_streak, longest_streak

def generate_svgs(stats):
    # Extracted stats
    stars = sum(repo["stargazerCount"] for repo in stats["repositories"]["nodes"])
    
    commits = (stats["cal2024"]["totalCommitContributions"] + 
               stats["cal2025"]["totalCommitContributions"] + 
               stats["cal2026"]["totalCommitContributions"])
               
    prs = (stats["cal2024"]["totalPullRequestContributions"] + 
           stats["cal2025"]["totalPullRequestContributions"] + 
           stats["cal2026"]["totalPullRequestContributions"])
           
    issues = (stats["cal2024"]["totalIssueContributions"] + 
              stats["cal2025"]["totalIssueContributions"] + 
              stats["cal2026"]["totalIssueContributions"])
              
    contrib_2024 = stats["cal2024"]["contributionCalendar"]["totalContributions"]
    contrib_2025 = stats["cal2025"]["contributionCalendar"]["totalContributions"]
    contrib_2026 = stats["cal2026"]["contributionCalendar"]["totalContributions"]
    
    total_contribs = contrib_2024 + contrib_2025 + contrib_2026
    
    # Calculate streak from calendar days across all years
    all_weeks = []
    all_weeks.extend(stats["cal2024"]["contributionCalendar"]["weeks"])
    all_weeks.extend(stats["cal2025"]["contributionCalendar"]["weeks"])
    all_weeks.extend(stats["cal2026"]["contributionCalendar"]["weeks"])
    
    current_streak, longest_streak = calculate_streaks(all_weeks)
    
    # Render main stats card SVG
    stats_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="450" height="195" viewBox="0 0 450 195" fill="none">
  <style>
    .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #00F0FF; }}
    .stat {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
    .label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #a9b1d6; }}
    .icon {{ fill: #00F0FF; }}
    .border {{ stroke: #1a1b26; stroke-width: 1; }}
  </style>
  <rect width="448" height="193" x="1" y="1" rx="6" fill="#1a1b26" class="border" />
  
  <text x="25" y="35" class="header">{stats['name'] or stats['login']}'s GitHub Stats</text>
  
  <!-- Stars -->
  <g transform="translate(25, 55)">
    <path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z" class="icon"/>
    <text x="25" y="12" class="label">Total Stars Earned:</text>
    <text x="200" y="12" class="stat">{stars}</text>
  </g>
  
  <!-- Commits -->
  <g transform="translate(25, 80)">
    <path d="M10.47 4.47a.75.75 0 011.06 0l3 3a.75.75 0 010 1.06l-3 3a.75.75 0 11-1.06-1.06L12.44 9H1.5a.75.75 0 010-1.5h10.94l-1.97-1.97a.75.75 0 010-1.06z" class="icon"/>
    <text x="25" y="12" class="label">Total Commits:</text>
    <text x="200" y="12" class="stat">{commits}</text>
  </g>
  
  <!-- PRs -->
  <g transform="translate(25, 105)">
    <path d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.292a.25.25 0 01-.427.177L7.177 3.073z" class="icon"/>
    <text x="25" y="12" class="label">Total PRs:</text>
    <text x="200" y="12" class="stat">{prs}</text>
  </g>
  
  <!-- Issues -->
  <g transform="translate(25, 130)">
    <path d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8z" class="icon"/>
    <text x="25" y="12" class="label">Total Issues:</text>
    <text x="200" y="12" class="stat">{issues}</text>
  </g>
  
  <!-- Contributed to -->
  <g transform="translate(25, 155)">
    <path d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8z" class="icon"/>
    <text x="25" y="12" class="label">Contributed to (last year):</text>
    <text x="200" y="12" class="stat">{contrib_2025 + contrib_2026}</text>
  </g>
</svg>"""

    # Render streak card SVG
    streak_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" fill="none">
  <style>
    .border {{ stroke: #1a1b26; stroke-width: 1; }}
    .number {{ font: 600 28px 'Segoe UI', Ubuntu, Sans-Serif; fill: #00F0FF; text-anchor: middle; }}
    .label {{ font: 400 12px 'Segoe UI', Ubuntu, Sans-Serif; fill: #a9b1d6; text-anchor: middle; }}
    .range {{ font: 400 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: #565f89; text-anchor: middle; }}
  </style>
  <rect width="493" height="193" x="1" y="1" rx="6" fill="#1a1b26" class="border" />
  
  <!-- Total Contributions -->
  <g transform="translate(82.5, 97.5)">
    <text y="-10" class="number">{total_contribs}</text>
    <text y="15" class="label">Total Contributions</text>
    <text y="35" class="range">Feb 25, 2024 - Present</text>
  </g>
  
  <line x1="165" y1="40" x2="165" y2="150" stroke="#1f2335" stroke-width="1"/>
  
  <!-- Current Streak -->
  <g transform="translate(247.5, 97.5)">
    <text y="-10" class="number">{current_streak}</text>
    <text y="15" class="label">Current Streak</text>
    <text y="35" class="range">{datetime.now().strftime('%b %d, %Y')}</text>
  </g>
  
  <line x1="330" y1="40" x2="330" y2="150" stroke="#1f2335" stroke-width="1"/>
  
  <!-- Longest Streak -->
  <g transform="translate(412.5, 97.5)">
    <text y="-10" class="number">{longest_streak}</text>
    <text y="15" class="label">Longest Streak</text>
    <text y="35" class="range">Feb 25, 2024 - Present</text>
  </g>
</svg>"""

    # Save to files
    os.makedirs("generated", exist_ok=True)
    with open("generated/github-stats.svg", "w") as f:
        f.write(stats_svg)
    with open("generated/github-streak.svg", "w") as f:
        f.write(streak_svg)
    print("SVGs successfully generated and saved to generated/ folder!")

if __name__ == "__main__":
    # Get user token and username from env
    TOKEN = os.environ.get("STATS_TOKEN")
    USERNAME = "Prashantsk45"
    
    if not TOKEN:
        print("Error: STATS_TOKEN environment variable not set.")
        exit(1)
        
    try:
        user_stats = fetch_stats(USERNAME, TOKEN)
        generate_svgs(user_stats)
    except Exception as e:
        print(f"Error occurred: {e}")
        exit(1)
