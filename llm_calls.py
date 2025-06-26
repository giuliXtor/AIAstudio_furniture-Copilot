from server.config import client, completion_model
import pandas as pd
import json
from difflib import get_close_matches

# Load activity aliases from CSV
# Load activity aliases from CSV
ALIAS_CSV_PATH = "Activity_Aliases.csv"
alias_df = pd.read_csv(ALIAS_CSV_PATH)
ALIASES = alias_df.to_dict(orient="records")

# 🔍 DEBUG PRINT
print("✅ Loaded user phrases from CSV:")
for a in ALIASES:
    print("-", a["user_phrase"])


# Match with containment first, then fallback to fuzzy
def find_alias_in_text(text):
    text = text.lower().strip()

    # Step 1: Containment
    for entry in sorted(ALIASES, key=lambda x: len(x["user_phrase"]), reverse=True):
        if entry["user_phrase"].lower().strip() in text:
            return entry

    # Step 2: Fuzzy match
    user_phrases = [entry["user_phrase"].lower().strip() for entry in ALIASES]
    match = get_close_matches(text, user_phrases, n=1, cutoff=0.85)
    if match:
        for entry in ALIASES:
            if entry["user_phrase"].lower().strip() == match[0]:
                return entry

    return None  # No match

# Main function
def extract_activities(natural_text):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
You are an assistant that extracts daily activities, their time slots, and the typical metabolic rate (in METs) for each activity from a person's schedule.

From the user's text, extract a list in this JSON format:
[
  {"activity": "activity_name", "hours": [hour1, hour2, ...]},
  ...
]

Rules:
- Use only activities from this list:
sleeping, cooking, working, reclining, yoga, sitting, typing, standing, reading, eating, stretching, organizing
- Use 24-hour time (0–23)
- For hour ranges, include all full hours in between
- For vague times like 'morning' or 'evening', use morning=7-11, evening=18-21
- Output only JSON. No explanation.
"""
            },
            {
                "role": "user",
                "content": natural_text,
            },
        ],
        temperature=0.2,
    )

    result_json = response.choices[0].message.content

    try:
        activities = json.loads(result_json)

        # Output placeholders
        hourly_metabolic_rates = [""] * 24
        hourly_activities = [""] * 24
        hourly_furniture = [""] * 24

        print("----- Matched Activities From LLM -----")
        for activity in activities:
            match = find_alias_in_text(activity["activity"])
            if match:
                print(f"> {activity['activity']} → {match['base_activity']}")
                activity["activity"] = match["base_activity"]
                activity["metabolic_rate"] = float(match["metabolic_rate"])
                activity["furniture"] = match["furniture"]

                for h in activity["hours"]:
                    hourly_metabolic_rates[h] = activity["metabolic_rate"]
                    hourly_activities[h] = activity["activity"]
                    hourly_furniture[h] = activity["furniture"]
            else:
                print(f"> {activity['activity']} → ❌ skipped (no match)")

        return {
            "activities_json": activities,
            "hourly_metabolic_rates": hourly_metabolic_rates,
            "hourly_activities": hourly_activities,
            "hourly_furniture": hourly_furniture
        }

    except Exception as e:
        return {
            "error": str(e),
            "raw_output": result_json
        }
