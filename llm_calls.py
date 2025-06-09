from server.config import client, completion_model
import json

METABOLIC_RATES = {
    "sleeping": 0.7,
    "cooking": 1.8,
    "working": 1.3,
    "reclining": 0.8,
    "yoga": 2.5,
    "sitting": 1.0,
    "standing": 1.2
}

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
""",
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
        # Fix the metabolic rates if needed
        for activity in activities:
            act_name = activity["activity"].lower()
            if act_name in METABOLIC_RATES:
                activity["metabolic_rate"] = METABOLIC_RATES[act_name]
            else:
                activity["metabolic_rate"] = activity.get("metabolic_rate", 1.0)

        # 24-hour lists, default values
        hourly_metabolic_rates = [1.2] * 24
        hourly_activities = ["standing"] * 24

        # Fill hours with correct activity & rate
        for activity in activities:
            for h in activity["hours"]:
                hourly_metabolic_rates[h] = activity["metabolic_rate"]
                hourly_activities[h] = activity["activity"]

        # Return everything
        return {
            "activities_json": activities,
            "hourly_metabolic_rates": hourly_metabolic_rates,
            "hourly_activities": hourly_activities
        }
    except Exception as e:
        return {
            "error": str(e),
            "raw_output": result_json
        }

