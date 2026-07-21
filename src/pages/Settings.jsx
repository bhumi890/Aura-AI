import React, { useState, useEffect } from 'react';
import { Volume2, Shield, User, Brain } from 'lucide-react';

export default function Settings() {
  const [voiceMode, setVoiceMode] = useState('calm');
  const [profileData, setProfileData] = useState(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  
  // TTS Voice states
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoiceURI, setSelectedVoiceURI] = useState('');

  const fetchProfile = async () => {
    setIsLoadingProfile(true);
    try {
      const userId = localStorage.getItem('mindmate_user_id') || 'default-user';
      const res = await fetch(`/api/users/${userId}/profile`);
      if (res.ok) {
        const data = await res.json();
        setProfileData(data);
      } else {
        setProfileData({
          username: localStorage.getItem('mindmate_username') || 'Demo User',
          memory_summary: 'No background profile stored yet.',
          conversation_count: 0,
          message_count: 0
        });
      }
    } catch (e) {
      setProfileData({
        username: localStorage.getItem('mindmate_username') || 'Demo User',
        memory_summary: 'No background profile stored yet.',
        conversation_count: 0,
        message_count: 0
      });
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const handleClearMemory = async () => {
    if (!window.confirm("Are you sure you want to clear your AI memory? Aura will forget personal background details across sessions.")) return;
    try {
      const userId = localStorage.getItem('mindmate_user_id') || 'default-user';
      await fetch(`/api/users/${userId}/profile/memory`, { method: 'DELETE' });
      await fetchProfile();
      alert('AI memory summary cleared successfully.');
    } catch (e) {
      alert('Failed to clear memory right now.');
    }
  };

  useEffect(() => {
    fetchProfile();
    const savedVoice = localStorage.getItem('mindmate_voice_style');

    if (savedVoice) setVoiceMode(savedVoice);
    
    const savedTTSVoice = localStorage.getItem('mindmate_tts_voice');
    if (savedTTSVoice) setSelectedVoiceURI(savedTTSVoice);

    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        const enVoices = voices.filter(v => v.lang.startsWith('en'));
        setAvailableVoices(enVoices);
        
        let currentSavedVoice = savedTTSVoice;
        if (currentSavedVoice) {
          const matchedVoice = enVoices.find(v => v.voiceURI === currentSavedVoice);
          if (matchedVoice && (matchedVoice.name.toLowerCase().includes('david') || matchedVoice.name.toLowerCase().includes('mark'))) {
            currentSavedVoice = null; // Force female selection
          }
        }
        
        if (!currentSavedVoice) {
          const femaleNames = ['zira', 'samantha', 'jenny', 'victoria', 'google us english', 'female'];
          let defaultVoice = null;
          for (const name of femaleNames) {
            defaultVoice = enVoices.find(v => v.name.toLowerCase().includes(name));
            if (defaultVoice) break;
          }
          if (!defaultVoice && enVoices.length > 0) {
            defaultVoice = enVoices.find(v => !v.name.toLowerCase().includes('david') && !v.name.toLowerCase().includes('mark') && !v.name.toLowerCase().includes('daniel'));
            if (!defaultVoice) defaultVoice = enVoices[0];
          }
          if (defaultVoice) {
            setSelectedVoiceURI(defaultVoice.voiceURI);
            localStorage.setItem('mindmate_tts_voice', defaultVoice.voiceURI);
          }
        }
      }
    };

    loadVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  const handleVoiceChange = (e) => {
    const newStyle = e.target.value;
    setVoiceMode(newStyle);
    localStorage.setItem('mindmate_voice_style', newStyle);
  };
  
  const handleTTSVoiceChange = (e) => {
    const newVoice = e.target.value;
    setSelectedVoiceURI(newVoice);
    localStorage.setItem('mindmate_tts_voice', newVoice);
  };

  const handleClearHistory = () => {
    if (window.confirm("Are you sure you want to delete all past conversations? This cannot be undone.")) {
      localStorage.removeItem('mindmate_chat_history');
      localStorage.removeItem('mindmate_mood_logs');
      alert("Conversation history cleared.");
    }
  };

  return (
    <div className="h-full p-8 md:p-10 overflow-y-auto">
      
      <div className="max-w-4xl mx-auto">
        <header className="mb-10">
          <h1 className="text-4xl font-bold tracking-tight text-foreground mb-2 font-heading">Settings</h1>
          <p className="text-muted-foreground text-base">Manage your preferences and AI integration settings.</p>
        </header>

        <div className="space-y-7">
          
          {/* My AI Profile (Background & Data Visibility) */}
          <div className="surface-panel p-8 md:p-9 border border-border/80 shadow-md">
            <div className="flex items-center justify-between mb-6 pb-6 border-b border-border/80">
              <div className="flex items-center space-x-4">
                <div className="p-3.5 bg-primary/10 rounded-2xl border border-primary/15">
                  <User className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-foreground font-heading">My AI Profile & Background</h3>
                  <p className="text-sm text-muted-foreground">What Aura remembers about you across your conversations.</p>
                </div>
              </div>
              <button 
                onClick={handleClearMemory}
                className="btn-secondary text-xs px-4 py-2 hover:bg-red-500/10 hover:text-red-600 dark:hover:text-red-400 hover:border-red-400/30 transition-all"
                title="Reset long-term AI memory summary"
              >
                Clear AI Memory
              </button>
            </div>
            
            {isLoadingProfile ? (
              <p className="text-sm text-muted-foreground animate-pulse py-4">Loading your AI profile data...</p>
            ) : profileData ? (
              <div className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-muted/50 p-5 rounded-2xl border border-border/60">
                  <div>
                    <span className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Username</span>
                    <span className="font-bold text-foreground text-base">{profileData.username || 'Guest'}</span>
                  </div>
                  <div>
                    <span className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Total Conversations</span>
                    <span className="font-bold text-foreground text-base">{profileData.conversation_count ?? 0}</span>
                  </div>
                  <div>
                    <span className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Total Messages</span>
                    <span className="font-bold text-foreground text-base">{profileData.message_count ?? 0}</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-foreground mb-2.5 flex items-center space-x-2">
                    <Brain className="w-4 h-4 text-primary" />
                    <span>Long-Term Memory Summary</span>
                  </label>
                  <div className="p-5 bg-input border border-border/80 rounded-2xl text-sm text-foreground/90 leading-relaxed max-h-48 overflow-y-auto font-sans shadow-inner">
                    {profileData.memory_summary || "No background details stored yet. As you chat, Aura builds a rolling summary of recurring themes and preferences to personalize future check-ins."}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground py-4">Could not load profile data right now.</p>
            )}
          </div>

          {/* Preferences Section */}
          <div className="surface-panel p-8 md:p-9 border border-border/80 shadow-md">
            <div className="flex items-center space-x-4 mb-6 pb-6 border-b border-border/80">
              <div className="p-3.5 bg-primary/10 rounded-2xl border border-primary/15">
                <Volume2 className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-foreground font-heading">App Preferences</h3>
                <p className="text-sm text-muted-foreground">Customize how Aura speaks and interacts with you.</p>
              </div>
            </div>
            
            <div className="space-y-6">
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="font-semibold text-foreground mb-1">Text-to-Speech Voice</h4>
                  <p className="text-sm text-muted-foreground">Choose the voice Aura uses to speak to you.</p>
                </div>
                <select 
                  value={selectedVoiceURI} 
                  onChange={handleTTSVoiceChange}
                  className="bg-input border border-border/80 rounded-2xl py-3 px-4 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 min-w-[220px] max-w-[280px] shadow-sm transition-all"
                >
                  {availableVoices.map((voice, i) => (
                    <option key={i} value={voice.voiceURI} className="bg-surface text-foreground">
                      {voice.name}
                    </option>
                  ))}
                  {availableVoices.length === 0 && <option className="bg-surface text-foreground">Loading voices...</option>}
                </select>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="font-semibold text-foreground mb-1">Aura Personality</h4>
                  <p className="text-sm text-muted-foreground">Choose the personality style the AI will use to respond.</p>
                </div>
                <select 
                  value={voiceMode} 
                  onChange={handleVoiceChange}
                  className="bg-input border border-border/80 rounded-2xl py-3 px-4 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 min-w-[220px] shadow-sm transition-all"
                >
                  <option value="calm" className="bg-surface text-foreground">Calm & Soothing</option>
                  <option value="upbeat" className="bg-surface text-foreground">Upbeat & Energizing</option>
                  <option value="empathetic" className="bg-surface text-foreground">Deeply Empathetic</option>
                  <option value="tough_love" className="bg-surface text-foreground">Direct & Tough Love</option>
                  <option value="clinical" className="bg-surface text-foreground">Clinical & Professional</option>
                  <option value="zen" className="bg-surface text-foreground">Zen & Philosophical</option>
                </select>
              </div>
            </div>
          </div>

          {/* Privacy Section */}
          <div className="surface-panel p-8 md:p-9 border border-border/80 shadow-md">
            <div className="flex items-center space-x-4 mb-6 pb-6 border-b border-border/80">
              <div className="p-3.5 bg-red-500/10 rounded-2xl border border-red-500/20">
                <Shield className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-foreground font-heading">Privacy & Security</h3>
                <p className="text-sm text-muted-foreground">Manage your local conversation data.</p>
              </div>
            </div>
            
            <div className="space-y-6">
              <div>
                <button onClick={handleClearHistory} className="text-red-600 dark:text-red-400 font-semibold hover:underline transition-colors">
                  Clear Conversation History
                </button>
                <p className="text-xs text-muted-foreground mt-1">This will permanently erase all local chat history and mood logs.</p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
