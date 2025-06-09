from server.config import *
import requests
from llm_calls import extract_activities
import json

user_text = "I wake up at 7am and make breakfast, then work from 9am to 5pm, cook at 6pm and then sit on the sofa and watch a movie for maybe two hours, then i'll do yoga at 9pm before going to bed at 10"
activities_json = extract_activities(user_text)
print("Raw LLM output:")
print(activities_json)

activities = json.loads(activities_json)
print("\nParsed activities and hours:")
for activity in activities:
    print(activity["activity"], activity["hours"])
