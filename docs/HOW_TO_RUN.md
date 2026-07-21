==================================================
HOW TO RUN MINDMATE AI LOCALLY
==================================================

TOTAL SETUP TIME: ~5 minutes (first time only)

==================================================
STEP 1: INSTALL NODE.JS (Skip if already installed)
==================================================
1. Go to: https://nodejs.org/
2. Download the "LTS" version (the green button)
3. Run the installer and follow the steps
4. Restart your computer after installing

To check if you already have it, open Command Prompt and type:
   node --version
If you see a version number like "v20.x.x", you're good to go!

==================================================
STEP 2: GET A FREE GROQ API KEY
==================================================
The AI brain of MindMate runs on Groq (it's free):
1. Go to: https://console.groq.com/
2. Sign up with your Google or GitHub account
3. Click "API Keys" in the left sidebar
4. Click "Create API Key", give it a name, and copy it
5. Save it somewhere, you'll need it in Step 5

==================================================
STEP 3: OPEN A TERMINAL IN THIS FOLDER
==================================================
- On Windows: 
  Click on the address bar at the top of this folder,
  type "cmd" and press Enter.
- On Mac: 
  Open Terminal, type "cd " (with a space), 
  drag this folder into the terminal, press Enter.

==================================================
STEP 4: INSTALL PROJECT DEPENDENCIES
==================================================
In the terminal, type this command and press Enter:

   npm install

Wait for it to finish (1-3 minutes). You'll see "added X packages".

==================================================
STEP 5: START THE APP
==================================================
Once installation is done, type:

   npm run dev

Then open your browser and go to:
   http://localhost:5173/

==================================================
STEP 6: ADD YOUR API KEY
==================================================
1. Click "Settings" in the left sidebar
2. Paste your Groq API key (from Step 2) into the "Groq API Key" field
3. Click "Save Key"
4. Go to "Voice Session" and start chatting!

==================================================
IMPORTANT NOTES
==================================================
- Use Google Chrome or Microsoft Edge for best experience.
  (The microphone and voice features don't fully work on Firefox/Safari)
- You can log in using: Username: admin | Password: password
  OR just click the "Admin Bypass" button to skip login entirely.
- The app theme defaults to your system's dark/light mode.
  You can toggle it using the button at the bottom of the sidebar.
==================================================
