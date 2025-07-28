import streamlit as st
from PIL import Image
import io
import speech_recognition as sr
from google import generativeai as genai
import requests
from gtts import gTTS
import tempfile

# --- Configure Gemini API ---
genai.configure(api_key="AIzaSyADAFye4AdI16sPJoxIx9KtnuZQTg3dmwI")
model = genai.GenerativeModel("gemini-2.5-flash")

# --- Configure WeatherAPI.com ---
WEATHERAPI_KEY = "2385b7a7051045f382d62111252807"  # Replace with your WeatherAPI.com key

# --- Language Options ---
st.set_page_config(page_title="🌾 AGRI-TOOL", layout="wide")
st.markdown("""
    <style>
        body {
            background-image: linear-gradient(to right, #e0ffe0, #ffffff);
            animation: fadeIn 2s ease-in;
        }
        .main {
            background: rgba(255, 255, 255, 0.92);
            padding: 2rem;
            border-radius: 10px;
            animation: slideIn 1.5s ease-in-out;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        @keyframes fadeIn {
            0% {opacity: 0;}
            100% {opacity: 1;}
        }
        @keyframes slideIn {
            0% {transform: translateY(20px); opacity: 0;}
            100% {transform: translateY(0); opacity: 1;}
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main">
""", unsafe_allow_html=True)

st.title("🌾 AGRI-TOOL – AI Assistant for Farmers")
st.markdown("Empowering Farmers with AI — Disease Detection, Weather Alerts, Farming Advice, and More!")

lang = st.sidebar.selectbox("🌐 Select Language", ["English", "Telugu", "Hindi"])
lang_map = {
    "English": "Respond in English.",
    "Telugu": "స్పష్టంగా తెలుగులో స్పందించండి.",
    "Hindi": "कृपया स्पष्ट हिंदी में उत्तर दें।"
}

def get_gtts_lang_code(selected_lang):
    return {
        "English": "en",
        "Telugu": "te",
        "Hindi": "hi"
    }.get(selected_lang, "en")

def speak(text):
    try:
        tts = gTTS(text=text, lang=get_gtts_lang_code(lang))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.warning(f"TTS failed: {e}")

def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening...")
        audio = r.listen(source, phrase_time_limit=6)
    try:
        query = r.recognize_google(audio)
        st.success(f"You said: {query}")
        return query
    except:
        st.error("Could not recognize speech.")
        return None

def gemini_text_response(user_input, system_prompt, lang_instruction):
    prompt = f"{system_prompt}\n\n{lang_instruction}\n\nUser: {user_input}"
    response = model.generate_content(prompt)
    return response.text

def gemini_image_analysis(image_bytes):
    prompt = (
        "Analyze this image and identify if there's any crop disease, pest, or soil issue. "
        "Suggest treatment including pesticides, fertilizers, or best practices. "
        f"{lang_map[lang]}"
    )
    response = model.generate_content([
        {"mime_type": "image/jpeg", "data": image_bytes},
        prompt
    ])
    return response.text

def get_weather_advisory(location):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={location}&aqi=no"
        response = requests.get(url)
        data = response.json()

        if "error" in data:
            return "❌ Location not found or weather service error."

        location_name = data["location"]["name"]
        condition = data["current"]["condition"]["text"]
        temp_c = data["current"]["temp_c"]
        humidity = data["current"]["humidity"]
        wind_kph = data["current"]["wind_kph"]
        rainfall = data["current"].get("precip_mm", 0)

        advisory = f"""
📍 **Weather in {location_name}**:
- 🌡️ Temperature: {temp_c}°C
- 🌫️ Condition: {condition}
- 💧 Humidity: {humidity}%
- 💨 Wind Speed: {wind_kph} km/h
- 🌧️ Rainfall: {rainfall} mm

📢 **Farming Advice**:
- {"Delay irrigation due to rainfall." if rainfall > 2 else "Consider light irrigation today."}
- Monitor for fungal diseases in humid conditions.
- {"Ideal" if 20 < temp_c < 30 else "Caution advised"} temperature for most crops.
"""
        return advisory

    except Exception as e:
        return f"⚠️ Error fetching weather data: {e}"

# --- Sidebar Navigation ---
option = st.sidebar.radio("📋 Choose a Service", [
    "🌿 Crop & Disease Detection",
    "🤖 AI Farming Chatbot",
    "🌦 Weather-Based Advisory",
    "🧪 Soil & Fertilizer Analysis",
    "🏛 Government Schemes",
])

# --- Main UI ---
with st.container():
    if option == "🌿 Crop & Disease Detection":
        st.header("🧫 🌿 Upload Crop Image for Disease, Pest, or Soil Diagnosis")
        uploaded = st.file_uploader("📥 Upload leaf, crop, or soil image:", type=["jpg", "png", "jpeg"])
        if uploaded is not None:
            image_bytes = uploaded.read()
            with st.spinner("🔍 Analyzing image using AI..."):
                result = gemini_image_analysis(image_bytes)
                st.success("🧬 Analysis Result:")
                st.write(result)
                speak(result)

    elif option == "🤖 AI Farming Chatbot":
        st.header("💬 🤖 Ask Your Farming Questions (Text or Voice)")
        col1, col2 = st.columns(2)
        with col1:
            user_input = st.text_input("📝 Type your question:")
        with col2:
            if st.button("🎤 Speak Now"):
                user_input = recognize_speech()
        if user_input:
            with st.spinner("🤔 Thinking..."):
                reply = gemini_text_response(
                    user_input,
                    system_prompt="You are a multilingual agricultural expert...",
                    lang_instruction=lang_map[lang]
                )
                st.success("🧠 Response:")
                st.write(reply)
                speak(reply)

    elif option == "🌦 Weather-Based Advisory":
        st.header("☁️ 🌦 Weather-Based Farming Guidance")
        st.info("🔍 Powered by WeatherAPI.com")
        location = st.text_input("📍 Enter your village/town name:")
        if location and st.button("📡 Get Advisory"):
            with st.spinner("🌐 Fetching real-time weather data..."):
                result = get_weather_advisory(location)
                st.success("🌤️ Advisory:")
                st.markdown(result)
                speak(result)

    elif option == "🧪 Soil & Fertilizer Analysis":
        st.header("🧪 🧫 Input Soil Parameters for Fertilizer Suggestion")
        ph = st.slider("🌡️ Soil pH", 3.5, 9.0, 6.5)
        nitrogen = st.number_input("🌱 Nitrogen (N) level (ppm)", value=50)
        phosphorus = st.number_input("🌾 Phosphorus (P) level (ppm)", value=30)
        potassium = st.number_input("🍠 Potassium (K) level (ppm)", value=40)
        if st.button("🧮 Get Fertilizer Plan"):
            query = (
                f"My soil has pH {ph}, Nitrogen {nitrogen} ppm, Phosphorus {phosphorus} ppm, Potassium {potassium} ppm. "
                "Suggest best fertilizer strategy and also organic options."
            )
            result = gemini_text_response(query,
                system_prompt="You are a soil expert helping farmers with personalized fertilizer suggestions.",
                lang_instruction=lang_map[lang]
            )
            st.success("🧪 Fertilizer Recommendation:")
            st.write(result)
            speak(result)

    elif option == "🏛 Government Schemes":
        st.header("🏛 📰 Government Policies & Subsidies for Farmers")
        query = st.text_input("🔍 Ask about a scheme or type (e.g., PM-KISAN, irrigation subsidy):")
        if query:
            response = gemini_text_response(
                query,
                system_prompt="You are a government assistant for Indian farmers. Give info on schemes, subsidies, and how to apply.",
                lang_instruction=lang_map[lang]
            )
            st.success("📘 Information:")
            st.write(response)
            speak(response)

st.markdown("""</div>""", unsafe_allow_html=True)
st.markdown("---")
st.caption(f"🌐 Language: {lang} | Voice + AI Enabled | Powered by Gemini AI + WeatherAPI | Built for Farmers 👨‍🌾")
