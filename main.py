
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

def ask_ai1(profile: dict, question: str, session_id: str) -> str:
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

from openai import OpenAI
import streamlit as st

# Initialize the client (Point this to OpenAI, Groq, OpenRouter, or Local Ollama)
client = OpenAI()

#new code
def ask_ai(profile: dict, question: str, session_id: str) -> str:
    # 1. Format your user profile context dynamically
    profile_context = build_profile_context(profile)

    # 2. Establish the System instructions for the AI
    system_instruction = (
        "You are Coach AI, a personalized biometric gym and nutrition companion.\n"
        f"Here is the user's current biometric profile data:\n{profile_context}\n\n"
        "Instructions:\n"
        "- Tailor all training, workout, and meal prep advice strictly to this data.\n"
        "- Keep responses clear, actionable, motivating, and professional."
    )

    # 3. Construct the clean message history payload directly from Streamlit
    # This completely eliminates the Langflow memory double-up bug!
    api_messages = [{"role": "system", "content": system_instruction}]

    # Append the historical conversation logs
    for msg in st.session_state.chat_messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    # Append the current fresh question that the user just typed/spoke
    api_messages.append({"role": "user", "content": question})

    try:
        # 4. Make a direct, stateless call to the model
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
            temperature=0.7,
        )

        # Return the string output directly
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Error generating AI response: {e}"


from openai import OpenAI
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

client = OpenAI()

import requests
import os


def fetch_supplement_data(supplement_name: str) -> list:
    """
    Fetches real supplement/nutrition data from USDA FoodData Central API
    and returns it as a list of text chunks for RAG ingestion.
    """
    api_key = os.getenv("USDA_API_KEY")

    # Search for the supplement
    search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    search_params = {
        "query": supplement_name,
        "api_key": api_key,
        "pageSize": 3  # get top 3 results
    }

    response = requests.get(search_url, params=search_params)
    data = response.json()

    # Convert API response into text chunks for embedding
    chunks = []
    for food in data.get("foods", []):
        name = food.get("description", "")
        nutrients = food.get("foodNutrients", [])

        # Build a readable text chunk from the API data
        nutrient_text = ", ".join([
            f"{n['nutrientName']}: {n.get('value', 'N/A')} {n.get('unitName', '')}"
            for n in nutrients[:10]  # top 10 nutrients
        ])

        chunk = f"{name}: {nutrient_text}"
        chunks.append(chunk)

    return chunks if chunks else [f"No data found for {supplement_name}"]
def check_supplement_safety_rag1(profile: dict, substance_query: str) -> str:
    """
    On-the-fly RAG function that retrieves reference data for a compound
    and outputs a general educational summary detail page.
    """
    # 1. Local reference knowledge base
    safety_knowledge_base = [
        "Creatine Monohydrate: Standard dosing is 3-5g daily. Requires increased daily water intake to prevent minor cramping. Safe for muscle gain goals but can cause minor initial water retention weight fluctuations.",
        "Caffeine / Pre-workout: Maximum recommended daily ceiling is 400mg. Avoid consumption within 6 hours of sleep. Can transiently elevate blood pressure and heart rate metrics.",
        "Whey Protein / Casein: Isolated dairy derivatives. Since they are direct milk proteins, they must be completely avoided if the user notes indicate ANY milk allergies, lactose sensitivities, or vegan tracking rules.",
        "Beta-Alanine: Normal dosing causes a harmless tingling sensation on the skin (paresthesia). Used to buffer lactic acid during high-rep muscular endurance training split phases.",
        "Ashwagandha: Adaptogen herb used to modulate cortisol stress levels. Recommended cycles are 8-12 weeks on, followed by a break. May interact with thyroid balancing configurations.",
        "BCAA (Branched-Chain Amino Acids): Generally redundant if overall daily macro protein targets are met. Best utilized during extended fasted training protocols to guard muscle tissues."
    ]

    documents = [Document(page_content=text) for text in safety_knowledge_base]

    # 2. Prevent collection naming conflicts with a unique run ID
    unique_collection_name = f"safety_cache_{uuid.uuid4().hex[:8]}"

    embeddings = OpenAIEmbeddings()
    db = Chroma.from_documents(documents, embeddings, collection_name=unique_collection_name)

    try:
        # Clean query punctuation and execute semantic search
        clean_query = substance_query.replace("?", "").replace(".", "").strip()
        relevant_docs = db.similarity_search(clean_query, k=2)
        retrieved_facts = "\n".join([doc.page_content for doc in relevant_docs])
    finally:
        db.delete_collection()

    # Extract user profile details for minor personalization, keeping it friendly
    user_name = profile.get('general', {}).get('name', 'Athlete')
    user_goals = ", ".join(profile.get('goals', ['Fitness']))

    # 3. GENERAL EDUCATIONAL SYSTEM PROMPT (No more medical blocks!)
    system_instruction = (
        f"You are Coach AI, an encouraging and knowledgeable fitness expert.\n"
        f"Create a friendly, informative overview page for the supplement requested by the user.\n\n"

        f"=== USER PROFILE ===\n"
        f"User Name: {user_name}\n"
        f"Current Goals: {user_goals}\n\n"

        f"=== RETRIEVED COMPOUND FACTS ===\n"
        f"{retrieved_facts}\n"
        f"=================================\n\n"

        "Format the response using this clean, structured layout:\n\n"
        "### 🔬 What is it?\n"
        "[Provide a friendly 2-3 sentence breakdown explaining what this compound is based on the retrieved facts.]\n\n"
        "### 💡 Key Benefits & Science\n"
        "[Summarize how this compound helps performance or health using the reference metrics.]\n\n"
        "### 📋 Suggested Intake\n"
        "[Mention standard dosing protocols, timing tips, or practical insights listed in the facts.]\n\n"
        "### ⚡ Coach Notes for Your Goals\n"
        "[Give a positive closing sentence on how this relates to their interest or fitness journey.]"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Show information page for: {clean_query}"}
            ],
            temperature=0.3  # Slightly warmer for a natural, coaching tone
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Profile generation failure: {e}"


def check_supplement_safety_rag2(profile: dict, substance_query: str) -> str:
    # ✅ NEW: fetch real data from API instead of hardcoded list
    api_chunks = fetch_supplement_data(substance_query)

    # ✅ OPTIONAL: combine with your hardcoded KB as a fallback
    hardcoded_fallback = [
        "Creatine Monohydrate: Standard dosing is 3-5g daily...",
        # ... your existing entries
    ]

    # Merge both sources
    all_chunks = api_chunks + hardcoded_fallback

    # Rest of your RAG pipeline stays EXACTLY the same
    documents = [Document(page_content=text) for text in all_chunks]

    unique_collection_name = f"safety_cache_{uuid.uuid4().hex[:8]}"
    embeddings = OpenAIEmbeddings()
    db = Chroma.from_documents(documents, embeddings,
                               collection_name=unique_collection_name)

    try:
        clean_query = substance_query.replace("?", "").replace(".", "").strip()
        relevant_docs = db.similarity_search(clean_query, k=2)
        retrieved_facts = "\n".join([doc.page_content for doc in relevant_docs])
    finally:
        db.delete_collection()


    # Extract user profile details for minor personalization, keeping it friendly
    user_name = profile.get('general', {}).get('name', 'Athlete')
    user_goals = ", ".join(profile.get('goals', ['Fitness']))

    # 3. GENERAL EDUCATIONAL SYSTEM PROMPT (No more medical blocks!)
    system_instruction = (
        f"You are Coach AI, an encouraging and knowledgeable fitness expert.\n"
        f"Create a friendly, informative overview page for the supplement requested by the user.\n\n"

        f"=== USER PROFILE ===\n"
        f"User Name: {user_name}\n"
        f"Current Goals: {user_goals}\n\n"

        f"=== RETRIEVED COMPOUND FACTS ===\n"
        f"{retrieved_facts}\n"
        f"=================================\n\n"

        "Format the response using this clean, structured layout:\n\n"
        "### 🔬 What is it?\n"
        "[Provide a friendly 2-3 sentence breakdown explaining what this compound is based on the retrieved facts.]\n\n"
        "### 💡 Key Benefits & Science\n"
        "[Summarize how this compound helps performance or health using the reference metrics.]\n\n"
        "### 📋 Suggested Intake\n"
        "[Mention standard dosing protocols, timing tips, or practical insights listed in the facts.]\n\n"
        "### ⚡ Coach Notes for Your Goals\n"
        "[Give a positive closing sentence on how this relates to their interest or fitness journey.]"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Show information page for: {clean_query}"}
            ],
            temperature=0.3  # Slightly warmer for a natural, coaching tone
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Profile generation failure: {e}"


import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

PERSIST_DIR = "./supplement_vectorstore"


def build_vector_store_once():
    """
    Run this ONCE to build the persistent vector store.
    Never needs to run again unless you want to update the data.
    """
    # Only build if it doesn't already exist
    if os.path.exists(PERSIST_DIR):
        print("Vector store already exists, skipping build")
        return

    print("Building vector store for the first time...")

    # Fetch a wide range of supplements from USDA
    all_chunks = []
    supplement_queries = [
        "creatine", "vitamin d", "omega 3", "magnesium",
        "zinc", "bcaa", "whey protein", "ashwagandha",
        "beta alanine", "caffeine", "collagen", "biotin"
    ]

    for query in supplement_queries:
        chunks = fetch_supplement_data(query)  # your existing function
        all_chunks.extend(chunks)

    # Embed and save to disk permanently
    documents = [Document(page_content=c) for c in all_chunks]
    db = Chroma.from_documents(
        documents,
        OpenAIEmbeddings(),
        persist_directory=PERSIST_DIR,  # saves to disk
        collection_name="supplements_kb"
    )
    print(f"Vector store built with {len(all_chunks)} chunks")


def load_vector_store():
    """
    Load the existing vector store from disk.
    Fast — no re-embedding needed.
    """
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=OpenAIEmbeddings(),
        collection_name="supplements_kb"
    )


def check_supplement_safety_rag(profile: dict, substance_query: str) -> str:
    # ✅ Load persistent store — no rebuilding every request!
    db = load_vector_store()

    user_name = profile.get('general', {}).get('name', 'Athlete')
    user_goals = ", ".join(profile.get('goals', ['Fitness']))

    try:
        clean_query = substance_query.replace("?", "").replace(".", "").strip()
        relevant_docs = db.similarity_search(clean_query, k=2)
        retrieved_facts = "\n".join([doc.page_content for doc in relevant_docs])
    except Exception as e:
        retrieved_facts = f"General information about {substance_query}."

    # Guard against empty retrieval
    if not retrieved_facts or retrieved_facts.strip() == "":
        retrieved_facts = f"No specific data found for {substance_query}."

    system_instruction = (
        f"You are Coach AI, an encouraging and knowledgeable fitness expert.\n"
        f"Create a friendly, informative overview page for the supplement requested.\n\n"
        f"=== USER PROFILE ===\n"
        f"User Name: {user_name}\n"
        f"Current Goals: {user_goals}\n\n"
        f"=== RETRIEVED COMPOUND FACTS ===\n"
        f"{retrieved_facts}\n"
        f"=================================\n\n"
        "Format the response using this layout:\n\n"
        "### 🔬 What is it?\n"
        "[2-3 sentence breakdown of the compound]\n\n"
        "### 💡 Key Benefits & Science\n"
        "[How this compound helps performance or health]\n\n"
        "### 📋 Suggested Intake\n"
        "[Standard dosing protocols and timing tips]\n\n"
        "### ⚡ Coach Notes for Your Goals\n"
        "[Personalised closing note based on their goals]"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Show information page for: {clean_query}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Profile generation failure: {e}"
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



