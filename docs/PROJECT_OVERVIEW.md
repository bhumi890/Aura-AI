==================================================
MINDMATE AI - FRONTEND & EMOTION AGENT
==================================================

WHAT WE DID:
We built a completely functional, prototype-ready frontend for the MindMate AI emotional wellness companion. Because the backend isn't ready yet, we engineered the frontend to be fully self-sufficient using browser APIs and local storage. 

We completely overhauled the design to be a premium, minimalist application with a Dark/Light mode toggle, avoiding the generic "AI glowing orb" aesthetic for a cleaner, more grounded feel.

WHAT WE USED:
- Framework: React (built with Vite)
- Styling: Tailwind CSS (with a custom minimalist class-based dark mode theme)
- Icons: Lucide React
- AI Engine: Groq API (llama-3.1-8b-instant model)
- Browser APIs: window.webkitSpeechRecognition (STT) and window.speechSynthesis (TTS)
- Memory: Browser Local Storage

CURRENT FEATURES:
1. Voice-to-Voice AI: 
   Users can click the microphone to speak their thoughts, and the AI will transcribe, process, and speak the response out loud in a calming, American female voice.
2. Advanced Emotion Agent: 
   The AI utilizes a highly specific system prompt to act as a therapeutic companion. It actively listens, validates emotions first, avoids unsolicited advice unless asked, and uses CBT/Mindfulness techniques.
3. Mood Dashboard: 
   The app automatically analyzes the user's text to detect their underlying emotion (Happy, Sad, Anxious, Stressed, Neutral) and plots their "Wellness Trend" dynamically on the dashboard.
4. Privacy & Settings: 
   Users can customize the AI's personality (Calm, Tough Love, Zen, etc.), change the Text-to-Speech voice, input their own Groq API key, and wipe their entire chat memory locally.
5. Dark / Light Mode: 
   A sleek toggle in the sidebar switches the entire application theme seamlessly.
