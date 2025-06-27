from server.config import client, completion_model
import pandas as pd
import json
from difflib import get_close_matches

# Default metabolic rates (fallbacks)
METABOLIC_RATES = {
    "sleeping": 0.7,
    "cooking": 1.8,
    "working": 1.3,
    "reclining": 0.8,
    "yoga": 2.5,
    "sitting": 1.0,
    "standing": 1.2
}

# Load activity aliases from CSV
ALIAS_CSV_PATH = "Activity_Aliases.csv"
alias_df = pd.read_csv(ALIAS_CSV_PATH)
ALIASES = alias_df.to_dict(orient="records")

# Improved alias match: containment first, then fuzzy
def find_alias_in_text(text):
    text = text.lower().strip()

    # Step 1: Check if any user_phrase is contained inside the activity
    for entry in sorted(ALIASES, key=lambda x: len(x["user_phrase"]), reverse=True):
        if entry["user_phrase"].lower().strip() in text:
            return entry

    # Step 2: Fuzzy match fallback
    user_phrases = [a["user_phrase"].lower().strip() for a in ALIASES]
    match = get_close_matches(text, user_phrases, n=1, cutoff=0.6)
    if match:
        for entry in ALIASES:
            if entry["user_phrase"].lower().strip() == match[0]:
                return entry
    return None

# Main LLM-driven extraction
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
  {"activity": "activity_name", "hours": [hour1, hour2, ...], "metabolic_rate": value},
  ...
]

Rules:
- Use 24-hour time (0–23)
- For hour ranges, include all full hours in between
- For vague times like 'morning' or 'evening', use typical hours (morning=7-11, evening=18-21)
- Use typical MET values for each activity: sleeping=0.7, cooking=1.8, working=1.3, reclining=0.8, yoga=2.5, sitting=1.0, typing=1.1, standing=1.2.
- Do not explain. Only output valid JSON.
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

        # Initialize output lists
        hourly_metabolic_rates = [1.2] * 24
        hourly_activities = ["standing"] * 24
        hourly_furniture = ["bookcase-storage"] * 24

        print("----- Matched Activities From LLM -----")
        for activity in activities:
            matched = find_alias_in_text(activity["activity"])
            if matched:
                print(f"> {activity['activity']} → {matched['base_activity']}")
                activity["activity"] = matched["base_activity"]
                activity["metabolic_rate"] = matched["metabolic_rate"]
                activity["furniture"] = matched["furniture"]
            else:
                act_name = activity["activity"].lower()
                print(f"> {activity['activity']} → fallback")
                activity["metabolic_rate"] = METABOLIC_RATES.get(act_name, activity.get("metabolic_rate", 1.0))
                activity["furniture"] = "sofa"

            for h in activity["hours"]:
                hourly_metabolic_rates[h] = activity["metabolic_rate"]
                hourly_activities[h] = activity["activity"]
                hourly_furniture[h] = activity["furniture"]

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
