
import requests
import os
import uuid

from dotenv import load_dotenv
load_dotenv()

import json




def ask_macros_ai(profile, goals):
    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": "You are a macro calculator. Respond ONLY with a JSON object, no extra text."
            },
            {
                "role": "user",
                "content": f"Calculate daily macros for:\nProfile: {profile}\nGoals: {goals}\n\nRespond ONLY with JSON:\n{{\"protein\": <number>, \"calories\": <number>, \"fat\": <number>, \"carbs\": <number>}}"
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    print(data)
    return data["choices"][0]["message"]["content"]


def build_profile_context(profile: dict) -> str:
    """
    Converts the raw profile dict into a clean, human-readable
    block that the LLM can actually understand and act on.
    Aligned with Streamlit UI state keys.
    """
    if not profile:
        return "No user profile available."

    # 1. Extract and normalize sub-dictionaries safely
    general = profile.get("general", {})
    fitness = profile.get("fitness", {})
    health = profile.get("health", {})

    # Handle 'goals' structure mismatch
    raw_goals = profile.get("goals", [])
    if isinstance(raw_goals, dict):
        goals = raw_goals.get("goals", [])
    else:
        goals = raw_goals
    goal_text = ", ".join(goals) if isinstance(goals, list) else str(goals)

    # Handle 'nutrition' structure mismatch and possible string types
    nutrition = profile.get("nutrition", {})
    if isinstance(nutrition, str):
        try:
            nutrition = json.loads(nutrition)
        except json.JSONDecodeError:
            nutrition = {}

    lines = [
        "=== USER PROFILE ===",
        f"Name            : {general.get('name', 'N/A')}",
        f"Age             : {general.get('age', 'N/A')} years",
        f"Gender          : {general.get('gender', 'N/A')}",
        f"Weight          : {general.get('weight', 'N/A')} kg",
        f"Height          : {general.get('height', 'N/A')} cm",
        f"Activity Level  : {general.get('activity_level', 'N/A')}",
        f"Goals           : {goal_text}",
        f"Experience Level: {fitness.get('experience_level', general.get('experience', 'N/A'))}",
        f"Workout Days/Wk : {fitness.get('days_per_week', general.get('days_per_week', 'N/A'))}",
        f"Preferred Split : {fitness.get('preferred_split', 'N/A')}",
        f"Equipment Access: {fitness.get('equipment', 'N/A')}",
        f"Calorie Target  : {nutrition.get('calories', 'N/A')} kcal",
        f"Protein Target  : {nutrition.get('protein', 'N/A')} g",
        f"Fat Target      : {nutrition.get('fat', 'N/A')} g",
        f"Carbs Target    : {nutrition.get('carbs', 'N/A')} g",
        f"Allergies       : {nutrition.get('allergies', 'None')}",
        f"Health Notes    : {health.get('notes', general.get('health_notes', 'None'))}",
        "===================",
    ]

    # Filter out lines where the value is still 'N/A' or default 0 to keep prompt clean
    cleaned = [
        l for l in lines
        if "N/A" not in l and ": 0 " not in l or l.startswith("===")
    ]
    return "\n".join(cleaned)



# =========================================================
# EXECUTION
# =========================================================
if __name__ == "__main__":
    user_profile = "name: Tim, Age: 24 weight: 75kg, height: 175cm"
    user_goals = "muscle gain"

    print("🚀 Running ask_macros_ai function...")
    output = ask_macros_ai(user_profile, user_goals)

    print("\n" + "=" * 45)
    print(output)
    print("=" * 45)


import requests

def ask_ai(profile: dict, question: str, session_id: str) -> str:
    URL = "http://localhost:7860/api/v1/run/b618b66f-9ae1-492f-8e0e-30109756d956"
    API_KEY = "sk-uewLuAmeqxMtERtgRkX-2DA3vZ4v_tC-BFYGoEvY6Y4"

    # ✅ THE FIX: use the helper to build a clean, readable profile string
    profile_context = build_profile_context(profile)

    combined_input = (
        f"{profile_context}\n\n"
        f"User Request: {question}\n\n"
        "Please give a detailed, personalised response based strictly on the profile above."
    )

    TWEAKS = {"session_id": session_id}

    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "input_value": combined_input,
        "tweaks": TWEAKS,
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
    }

    try:
        response = requests.post(URL, json=payload, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            try:
                return response_data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
            except (KeyError, IndexError):
                return response_data["outputs"][0]["outputs"][0]["results"]["text"]["data"]["text"]
        else:
            return f"Server Error ({response.status_code}): {response.text}"

    except requests.exceptions.RequestException as e:
        return f"Error connecting to Langflow: {e}"







# =========================================================
# HOW TO CALL YOUR FUNCTION DOWN BELOW:
# =========================================================
if __name__ == "__main__":
    my_profile = (
        "21-year-old student, works out twice a week, goal is muscle gain"
    )
    my_question = "Can you design a workout routine for me based on my profile?"

    print("🚀 Running ask_ai function...")
    output = ask_ai(my_profile, my_question)

    print("\n" + "=" * 45)
    print(output)
    print("=" * 45)






from openai import OpenAI

client = OpenAI()

def ask_vision_ai(base64_image_string, session_id):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image_string}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Analyze this food image. Give me: Total Calories, Protein (g), Carbs (g), Fat (g). Be specific with numbers."
                    }
                ]
            }
        ],
        max_tokens=500
    )
    return response.choices[0].message.content



