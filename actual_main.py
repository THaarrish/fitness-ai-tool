import uuid
import base64
from main import ask_vision_ai
import streamlit as st
from profiles import create_profile, get_profile, get_notes
from form_submit import update_personal_info, add_note, delete_note
from openai import OpenAI
# adding this import delete if no work
from st_audiorec import st_audiorec
if "chat_session_id" not in st.session_state:
    st.session_state.chat_session_id=str(uuid.uuid4())

from main import ask_macros_ai, ask_ai
import json
import sys
import os
st.title ("Your Personal AI Fitness Tool")
@st.fragment()
def personal_data_form():
    with st.form("personal_data"):
        st.header("Personal Data")
        profile= st.session_state.profile
# added code

        name = st.text_input("Name", value=profile["general"]["name"])
        age = st.number_input("Age", min_value=1, max_value=120, step=1, value=profile["general"]["age"])
        weight = st.number_input("Weight (kg)", min_value=0.0,max_value=300.0, step=0.1, value=float(profile["general"]["weight"]))
        height = st.number_input("Height (cm)", min_value=0.0, max_value=250.0, step=0.1,value=float(profile["general"]["height"]))
        genders=["Male", "Female", "Other"]
        gender= st.radio('Gender', genders, genders.index(profile["general"].get("gender", "Male")))
        activities = (
            "Beginner",
            "Lightly Active",
            "Moderately Active",
            "Very Active",
            "Super Active",
        )
        activity_level = st.selectbox("Activity Level", activities, index=activities.index(profile["general"].get("activity_level", "Beginner")))
        personal_data_submit= st.form_submit_button("Save")
        if personal_data_submit:
            if all([name,age,weight,height,gender,activity_level]):
                with st.spinner():
                    st.session_state.profile=update_personal_info(profile, "general", name=name, weight=weight, height=height, gender=gender, age=age, activity_level=activity_level)
                    st.success("Information Saved.")
            else:
                st.warning("Please fill in all of the data")

@st.fragment()
def goals_form():
    profile= st.session_state.profile
    with st.form("goals_form"):
        st.header("Goals")
        goals= st.multiselect("Select your Goals", ["Muscle Gain", "Fat Lose", "Stay active"],
                    default=profile.get("goals", ["Muscle Gain"]))
        goals_submit= st.form_submit_button("Save")
        if goals_submit:
            if goals:
                with st.spinner():
                    st.session_state.profile= update_personal_info(profile, "goals", goals=goals)
                    st.success("Goals Updated")
            else:
                st.warning("Please select at least one goal.")

def food_vision_analyzer():

    st.markdown("---")

    st.header("📸 AI Food Calorie Scanner")

    st.caption("Upload a picture of your meal to instantly estimate calories and macro-nutrients.")



    # 1. Accept any file format initially so Streamlit never throws a hard error state

    uploaded_image = st.file_uploader(

        "Snap or upload a photo of your food...",

        type=None,  # Allows the file to upload completely so we can control the error message

        accept_multiple_files=False  # Enforces that the user can only upload one photo at a time

    )



    if uploaded_image is not None:

        # Extract file extension and convert to lowercase

        file_extension = uploaded_image.name.split(".")[-1].lower()

        supported_formats = ["jpg", "jpeg", "png", "webp"]



        # 🚨 ERROR GUARD: If the user uploads an unsupported file format

        if file_extension not in supported_formats:

            st.error(f"❌ File type '.{file_extension}' is not supported!")

            st.warning("Please upload an image file ending in: .jpg, .jpeg, .png, or .webp")



            # This clear button resets the state so they can click the '+' button again smoothly

            if st.button("🔄 Clear and Try Again", use_container_width=True):

                st.rerun()



        # ✅ SUCCESS GATE: If the file is valid, proceed with the UI and API scanner pipeline

        else:

            st.image(uploaded_image, caption="Valid Meal Image Ready for Scanning", use_container_width=True)



            if st.button("🔍 Analyze Meal Calories", use_container_width=True):

                with st.spinner("Processing meal image properties via Langflow..."):

                    try:

                        # Convert uploaded image into base64 bytes for safe API transmission

                        image_bytes = uploaded_image.getvalue()

                        base64_image = base64.b64encode(image_bytes).decode("utf-8")



                        # Call your Langflow backend hook

                        analysis_result = ask_vision_ai(base64_image, st.session_state.chat_session_id)



                        st.success("Analysis Complete!")

                        st.markdown(analysis_result)



                    except Exception as e:

                        st.error(f"Vision Analysis Failed: {e}")

@st.fragment()
def macros():
    # ---- 🏷️ BRANDING HEADER SECTION ----
    # Create two columns: a small one for the logo and a wide one for the name
    logo_col, title_col = st.columns([1, 5])

    with logo_col:
        # Make sure "logo.png" is saved in your project folder!
        st.image("logo.png", use_container_width=True)

    with title_col:
        # Sets your custom chatbot name cleanly at the top
        st.markdown("<h1 style='margin-top: 0px;'>NEURO_KINETIX</h1>", unsafe_allow_html=True)
        st.caption("Your Personalized Biometric Gym & Nutrition Companion")

    st.markdown("---")
    import json
    profile= st.session_state.profile
    # added code
    if isinstance(profile.get("nutrition"), str):
        profile["nutrition"] = json.loads(profile["nutrition"])
        st.session_state.profile = profile
    nutrition= st.container (border=True)
    nutrition.header("Macros")
    if nutrition.button("Generate with AI"):
        result= ask_macros_ai(profile.get("general"),profile.get("goals"))
        profile["nutrition"]= result
        nutrition.success("AI has generated the results")


    with nutrition.form("nutrition_form", border=False):
        col1, col2, col3, col4 = st.columns (4)
        # added code

        nutrition = profile["nutrition"]
        if isinstance(nutrition, str):
            nutrition = json.loads(nutrition)
        with col1:
            calories= st.number_input("Calories",min_value=0, step=1, value=nutrition.get("calories",0 ))
        with col2:
            protein= st.number_input("Protein", min_value=0, step=1, value=nutrition.get("protein", 0))
        with col3:
            fat= st.number_input("Fat", min_value=0, step=1, value=nutrition.get("fat", 0))
        with col4:
            carbs= st.number_input("Carbs", min_value=0, step=1, value=nutrition.get("carbs", 0))
        if st.form_submit_button("Save"):
            with st.spinner():
                st.session_state.profile= update_personal_info(profile, "nutrition", protein=protein, calories=calories, fat=fat, carbs=carbs )
                st.success("Information Saved")

@st.fragment()
def notes():
    st.subheader("Notes: ")
    for i, note in enumerate(st.session_state.notes):
        cols=st.columns([5,1])
        with cols[0]:
            st.text(note.get("text"))
        with cols[1]:
            if st.button("Delete", key=i):
                delete_note(note.get("_id"))
                st.session_state.notes.pop(i)
                st.rerun()
    new_note=st.text_input("Add a new note: ")
    if st.button("Add note"):
        if new_note:
            note=add_note(new_note, st.session_state.profile_id)
            st.session_state.notes.append(note)
            st.rerun()
#@st.fragment()

# added codes for STT and TTS
client = OpenAI()


def transcribe_voice(audio_bytes):
    temp_filename = "temp_audio.wav"
    with open(temp_filename, "wb") as f:
        f.write(audio_bytes)

    with open(temp_filename, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file, language="en", prompt="A fitness, gym, and nutrition conversation about tracking macros, workout, and calories"
        )

    os.remove(temp_filename)
    return transcript.text


def speak_text(text_to_speak):
    """Converts AI text response into audio bytes, splitting long text safely to avoid OpenAI's 4096-character limit."""
    MAX_CHARS = 4000  # Set slightly below 4096 to be safe
    combined_audio = b""  # Store the final concatenated audio bytes

    # 1. Check if text is short enough to process normally
    if len(text_to_speak) <= MAX_CHARS:
        response = client.audio.speech.create(
            model="tts-1", voice="alloy", input=text_to_speak
        )
        return response.content

    # 2. If it's too long, split it up safely by paragraphs so it doesn't cut off mid-sentence
    paragraphs = text_to_speak.split("\n")
    current_chunk = ""

    for paragraph in paragraphs:
        # If adding this paragraph exceeds the limit, process the current chunk first
        if len(current_chunk) + len(paragraph) + 1 > MAX_CHARS:
            if current_chunk.strip():
                response = client.audio.speech.create(
                    model="tts-1", voice="alloy", input=current_chunk.strip()
                )
                combined_audio += response.content
            current_chunk = paragraph  # Reset chunk to start with the new paragraph
        else:
            current_chunk += "\n" + paragraph

    # Process any leftover text in the final chunk
    if current_chunk.strip():
        response = client.audio.speech.create(
            model="tts-1", voice="alloy", input=current_chunk.strip()
        )
        combined_audio += response.content

    return combined_audio


def render_pulsing_voice_circle():
    """Injects a high-tech glowing CSS pulsing circle animation while the AI talks back."""
    st.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; margin: 30px 0;">
            <div class="voice-glow-circle"></div>
        </div>

        <style>
        .voice-glow-circle {
            width: 80px;
            height: 80px;
            background: radial-gradient(circle, #00FFCC 0%, #0B0E14 100%);
            border: 2px solid #00FFCC;
            border-radius: 50%;
            box-shadow: 0 0 15px #00FFCC;
            animation: pulse-wave 1.5s infinite ease-in-out;
        }

        @keyframes pulse-wave {
            0% {
                transform: scale(0.8);
                box-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
            }
            50% {
                transform: scale(1.1);
                box-shadow: 0 0 30px rgba(0, 255, 204, 0.9), 0 0 50px rgba(0, 255, 204, 0.4);
            }
            100% {
                transform: scale(0.8);
                box-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def process_and_respond(user_question, voice_response=False):
    """Orchestrates pipeline processing: updates user UI instantly, then handles AI execution."""

    # 1. STEP ONE: Immediately save and display the user's question
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    st.session_state.chat_messages.append({"role": "user", "content": user_question})

    # Force Streamlit to quickly redraw the page so the user sees their typed text instantly
    st.rerun()

    # ---- NOTE: The code below will execute on the refresh pass if user_question is carried over ----
    # To prevent double executions across reruns, it's actually much cleaner to process the AI
    # directly inline inside the ask_ai_function itself right after st.chat_input!


@st.fragment()
def ask_ai_function():
    # ---- 🏷️ BRANDING HEADER SECTION ----
    # Create two columns: a small one for the logo and a wide one for the name
    logo_col, title_col = st.columns([1, 5])

    with logo_col:
        # Make sure "logo.png" is saved in your project folder!
        st.image("logo.png", use_container_width=True)

    with title_col:
        # Sets your custom chatbot name cleanly at the top
        st.markdown("<h1 style='margin-top: 0px;'>NEURO_KINETIX</h1>", unsafe_allow_html=True)
        st.caption("Your Personalized Biometric Gym & Nutrition Companion")

    st.markdown("---")
    st.subheader("Coach AI Chatroom")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    chat_mode = st.radio(
        "Select Interaction Mode:",
        ["💬 Text-Only Mode", "🎙️ Hands-Free Voice Mode"],
        horizontal=True,
    )
    st.markdown("---")

    # ══════════════════════════════════════════
    #  MODE A — TEXT-ONLY
    # ══════════════════════════════════════════
    if chat_mode == "💬 Text-Only Mode":

        # Welcome banner (only on fresh start)
        if not st.session_state.chat_messages:
            st.info(
                "### 💪 Welcome to Coach AI!\n"
                "I am your personal AI fitness, gym, and nutrition coach. I can help you:\n"
                "* Discover customised workout training splits\n"
                "* Calculate target macros and plan perfect clean meal preps\n"
                "* Get instant metabolic adjustments and tracking metrics guidance"
            )

        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # ── Suggestion cards (only on fresh start) ──
        card_clicked_prompt = None
        if not st.session_state.chat_messages:
            st.markdown("### 💡 Recommended for You")

            user_profile = st.session_state.get("profile", {})
            general_info = user_profile.get("general", {})
            user_goals = user_profile.get("goals", ["Muscle Gain"])

            goal_text = ", ".join(user_goals) if isinstance(user_goals, list) else user_goals
            user_weight = general_info.get("weight", "95.0")

            # ✅ Card prompts are explicit — the profile injection happens inside ask_ai
            card_1_prompt = "Please design a fully customised workout routine for me based on my profile."
            card_2_prompt = "Please calculate an optimal weekly grocery meal prep list for me based on my profile."
            card_3_prompt = "Based on my current stats and goals, what specific metabolic or diet adjustments should I make right now?"

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**🏋️ Training Plan**")
                st.caption(f"Targeting {goal_text}")
                if st.button("Generate Routine", key="card_btn_1", use_container_width=True):
                    card_clicked_prompt = card_1_prompt

            with col2:
                st.markdown("**🍎 Meal Strategy**")
                st.caption("Optimised nutrition split")
                if st.button("Get Grocery List", key="card_btn_2", use_container_width=True):
                    card_clicked_prompt = card_2_prompt

            with col3:
                st.markdown("**⚖️ Weight Advice**")
                st.caption(f"Tracking {user_weight} kg metrics")
                if st.button("Check Adjustments", key="card_btn_3", use_container_width=True):
                    card_clicked_prompt = card_3_prompt

            st.markdown("---")

        typed_input = st.chat_input("Ask me anything about your fitness goals...")

        if card_clicked_prompt:
            typed_input = card_clicked_prompt

        # ── Processing pipeline ──
        if typed_input:
            st.session_state.chat_messages.append({"role": "user", "content": typed_input})

            with chat_container:
                with st.chat_message("user"):
                    st.markdown(typed_input)

            with chat_container:
                with st.spinner("Thinking..."):
                    result = ask_ai(
                        st.session_state.profile,
                        typed_input,
                        st.session_state.chat_session_id,
                    )

                with st.chat_message("assistant"):
                    st.markdown(result)

            st.session_state.chat_messages.append({"role": "assistant", "content": result})
            st.rerun()

    # ══════════════════════════════════════════
    #  MODE B — VOICE
    # ══════════════════════════════════════════
    else:
        st.info("✨ Voice Mode Active! Talk with your Coach using the panel below.")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<h4 style='text-align: center;'>🎙️ Tap to Speak</h4>", unsafe_allow_html=True)
            wav_audio_bytes = st_audiorec()

        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if "audio" in msg and msg["audio"] is not None:
                        st.audio(msg["audio"], format="audio/mp3")

        if wav_audio_bytes is not None:
            audio_hash = hash(wav_audio_bytes)
            if (
                    "last_processed_audio" not in st.session_state
                    or st.session_state.last_processed_audio != audio_hash
            ):
                st.session_state.last_processed_audio = audio_hash

                with st.spinner("Listening to voice..."):
                    user_question = transcribe_voice(wav_audio_bytes)

                if "last_voice_reply" in st.session_state:
                    del st.session_state["last_voice_reply"]

                st.session_state.chat_messages.append({"role": "user", "content": user_question})
                render_pulsing_voice_circle()

                with st.spinner("Coach AI is generating voice response..."):
                    result = ask_ai(
                        st.session_state.profile,
                        user_question,
                        st.session_state.chat_session_id,
                    )
                    audio_bytes = speak_text(result)

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": result,
                    "audio": audio_bytes,
                })
                st.rerun()



















#def forms():
 #   if "profile" not in st.session_state:
  #      profile_id =1
   #     profile = get_profile(profile_id)
    #    if not profile :
     #       profile_id, profile=create_profile(profile_id)


      #  st.session_state.profile= profile
       # st.session_state.profile_id= profile_id
        ## added code


    #if "notes" not in st.session_state:
     #   st.session_state.notes= get_notes(st.session_state.profile_id)
    #personal_data_form()
    #goals_form()
    #macros()
    #notes()
    #ask_ai_function()

def apply_futuristic_css():
    st.markdown(
        """
        <style>
        /* 1. FORCE CORE APP BACKGROUNDS */
        .stApp, 
        [data-testid="stAppViewContainer"], 
        [data-testid="stHeader"],
        .main {
            background-color: #0B0E14 !important;
        }

        /* 2. FORCE SIDEBAR BACKGROUND */
        [data-testid="stSidebar"], 
        [data-testid="stSidebarUserContent"] {
            background-color: #161B25 !important;
            border-right: 1px solid #242F41 !important;
        }

        /* 3. TABS HEADER ROW CONFIGURATION */
        button[data-baseweb="tab"] {
            font-size: 18px !important;
            font-weight: 600 !important;
            color: #8A99AD !important;
            background-color: transparent !important;
            border-radius: 8px 8px 0px 0px;
            padding: 10px 20px !important;
            transition: all 0.3s ease-in-out;
        }

        /* Active Selected Tab Highlight */
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #00FFCC !important; 
            border-bottom: 3px solid #00FFCC !important;
        }

        /* 4. UPGRADE STANDARD CONTAINERS AND FORMS TO GLASS PANELS */
        div[data-testid="stForm"], 
        div[data-testid="stVerticalBlockBorderWrapper"] > div,
        div[data-testid="element-container"]:has(div.stButton) {
            background-color: #161B25 !important;
            border: 1px solid #242F41 !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0px 4px 15 rgba(0, 0, 0, 0.4) !important;
            margin-bottom: 15px !important;
        }

        /* 5. INTERACTIVE COMPONENT BUTTONS */
        .stButton>button, div[data-testid="stForm"] button {
            background-color: #1F2633 !important;
            color: #00FFCC !important;
            border: 1px solid #00FFCC !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            transition: all 0.2s ease-in-out !important;
        }

        .stButton>button:hover, div[data-testid="stForm"] button:hover {
            background-color: #00FFCC !important;
            color: #0B0E14 !important;
            box-shadow: 0px 0px 12px #00FFCC !important;
            border: 1px solid #00FFCC !important;
        }

        /* 6. STYLE CHAT MESSAGES */
        [data-testid="stChatMessage"] {
            background-color: #1A2332 !important;
            border: 1px solid #2C3A52 !important;
            border-radius: 10px !important;
            margin-bottom: 12px !important;
            padding: 15px !important;
        }

        /* 7. TEXT FIELD AND INPUT FIELD POLISHING */
        p, label, h1, h2, h3, h4, h5, h6, span {
            color: #FAFAFA !important;
        }

        /* Center text and pull number input boxes closer together */
        div[data-testid="stNumberInput"] {
            width: 100% !important;
            max-width: 160px !important;
            margin: 0 auto !important;
        }

        /* Brighten the inner input field container & border */
        div[data-testid="stNumberInput"] > div {
            background-color: #1F2633 !important;
            border: 1px solid #2C3A52 !important;
            border-radius: 8px !important;
        }

        /* Style the actual numbers inside the box */
        div[data-testid="stNumberInput"] input {
            text-align: center !important;
            padding-left: 10px !important;
            color: #00FFCC !important; /* Make numbers pop with the neon teal */
            font-weight: bold !important;
        }

        /* Brighten the step increment/decrement control symbols (+ / -) */
        div[data-testid="stNumberInput"] button {
            color: #FAFAFA !important;
            background-color: transparent !important;
            border: none !important;
        }

        div[data-testid="stNumberInput"] button:hover {
            color: #00FFCC !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def forms():
    if "profile" not in st.session_state:
        profile_id = 1
        profile = get_profile(profile_id)
        if not profile:
            profile_id, profile = create_profile(profile_id)

        st.session_state.profile = profile
        st.session_state.profile_id = profile_id

    if "notes" not in st.session_state:
        st.session_state.notes = get_notes(st.session_state.profile_id)

    # 1. Inject our custom ultra-cool dark CSS styles
    apply_futuristic_css()

    # 2. Move your forms completely out of the way into a sleek left sidebar!
    with st.sidebar:
        st.title("⚙️ Profile Settings")
        personal_data_form()
        goals_form()
        st.markdown("---")
        st.caption("AI Fitness Tool v2.0")

    # 3. Use Tabs in the main screen area to separate your features cleanly
    tab1, tab2 = st.tabs(["📊 Macro Dashboard", "💬 Chat with Coach AI"])

    with tab1:
        macros()
        st.markdown("---")
        notes()  # Keep notes right under macros in the dashboard area
        food_vision_analyzer()

    with tab2:
        ask_ai_function()  # This isolates the chat so it takes up the full clean window!

# Get the absolute path of the directory containing actual_main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now try importing directly from the directory path
try:
    from main import ask_macros_ai, ask_ai
except ModuleNotFoundError:
    # Backup for package-style directory structure on Linux servers
    try:
        from main import ask_macros_ai, ask_ai
    except ModuleNotFoundError:
        # Final backup to catch all bases
        import main

        ask_macros_ai = main.ask_macros_ai
        ask_ai = main.ask_ai
if __name__ == "__main__":
    forms()


