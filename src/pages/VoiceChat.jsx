import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Activity, HeartPulse, Send, AlertTriangle, Volume2, VolumeX, Plus, MessageSquare, Trash2, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { analyzeMood, saveMoodLog } from '../utils/moodAnalyzer';
import { API_BASE_URL } from '../config';

// ─── Markdown stripper (for clean TTS) ──────────────────────
function stripMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/gs, '$1')      // bold **text**
    .replace(/\*(.+?)\*/gs, '$1')           // italic *text*
    .replace(/__(.+?)__/gs, '$1')           // bold __text__
    .replace(/_(.+?)_/gs, '$1')             // italic _text_
    .replace(/`{1,3}[^`]*`{1,3}/g, '')     // inline/block code
    .replace(/#{1,6}\s*/g, '')              // headings
    .replace(/>\s*/g, '')                   // blockquotes
    .replace(/\[(.+?)\]\(.*?\)/g, '$1')    // links → text only
    .replace(/!?\[.*?\]\(.*?\)/g, '')       // images
    .replace(/^[-*+]\s+/gm, '')             // list bullets
    .replace(/^\d+\.\s+/gm, '')            // numbered lists
    .replace(/\n{2,}/g, '. ')              // double newlines → pause
    .replace(/\n/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

// ─── Split text into speakable sentences ─────────────────────
function splitIntoSentences(text) {
  // Split on sentence-ending punctuation followed by space or end of string
  const raw = text.match(/[^.!?]+[.!?]+(\s|$)|[^.!?]+$/g) || [text];
  return raw.map(s => s.trim()).filter(Boolean);
}

// ─── Choose best available voice ─────────────────────────────
function selectBestVoice(savedVoiceURI) {
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;

  if (savedVoiceURI) {
    const saved = voices.find(v => v.voiceURI === savedVoiceURI);
    if (saved) return saved;
  }

  // Prefer neural / high-quality female English voices
  const preferred = [
    'Microsoft Jenny Online (Natural) - English (United States)',
    'Microsoft Aria Online (Natural) - English (United States)',
    'Google US English',
    'Samantha',
    'Karen',
    'Victoria',
  ];
  for (const name of preferred) {
    const v = voices.find(v => v.name === name);
    if (v) return v;
  }

  // Fallback: any non-male English voice
  const maleKeywords = ['david', 'mark', 'daniel', 'james', 'ryan', 'guy'];
  const enVoices = voices.filter(v => v.lang.startsWith('en'));
  return enVoices.find(v => !maleKeywords.some(m => v.name.toLowerCase().includes(m))) || enVoices[0] || null;
}

export default function VoiceChat() {
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [conversationsList, setConversationsList] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const speakQueueRef = useRef([]);
  const isSpeakingRef = useRef(false);
  const initializedRef = useRef(false);

  const fetchHistory = async () => {
    try {
      const userId = localStorage.getItem('mindmate_user_id') || 'default-user';
      const res = await fetch(`${API_BASE_URL}/api/history/?user_id=${userId}`);
      if (res.ok) {
        const data = await res.json();
        setConversationsList(data.items || []);
      }
    } catch { /* ignore */ }
  };

  const handleNewChat = () => {
    window.speechSynthesis?.cancel();
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
    setConversationId(null);
    const username = localStorage.getItem('mindmate_username') || 'guest';
    setMessages([{
      role: 'ai',
      content: `Hi${username !== 'guest' ? ` ${username}` : ''}! I'm Aura. How can I help or support you today?`,
    }]);
    fetchHistory();
  };

  const handleSelectConversation = async (id) => {
    if (id === conversationId) return;
    window.speechSynthesis?.cancel();
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/history/${id}`);
      if (res.ok) {
        const data = await res.json();
        setConversationId(id);
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages.map(m => ({
            role: m.role === 'assistant' ? 'ai' : m.role,
            content: m.content
          })));
        } else {
          setMessages([{ role: 'ai', content: 'This conversation has no messages yet.' }]);
        }
      }
    } catch (e) {
      console.error('Failed to load conversation:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (id, e) => {
    e.stopPropagation();
    try {
      const res = await fetch(`${API_BASE_URL}/api/history/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setConversationsList(prev => prev.filter(c => c.id !== id));
        if (conversationId === id) {
          handleNewChat();
        }
      }
    } catch (err) {
      console.error('Failed to delete chat:', err);
    }
  };

  // ── Initialization (runs once — component stays mounted) ─────
  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    fetchHistory();

    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/chat/health`);
        if (res.ok) setBackendAvailable(true);
      } catch { /* ignore */ }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);

    const savedVoiceToggle = localStorage.getItem('mindmate_voice_enabled');
    if (savedVoiceToggle !== null) setIsVoiceEnabled(savedVoiceToggle === 'true');

    const username = localStorage.getItem('mindmate_username') || 'guest';
    setMessages([{
      role: 'ai',
      content: `Hi${username !== 'guest' ? ` ${username}` : ''}! I'm Aura. How are you feeling today?`,
    }]);

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setTextInput(transcript);
        processMessage(transcript);
      };
      recognitionRef.current.onend = () => setIsListening(false);
      recognitionRef.current.onerror = () => setIsListening(false);
    }

    return () => clearInterval(interval);
  }, []);


  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Voice output controls ─────────────────────────────────────
  const toggleVoiceEnabled = () => {
    const newState = !isVoiceEnabled;
    setIsVoiceEnabled(newState);
    localStorage.setItem('mindmate_voice_enabled', newState);
    if (!newState) {
      window.speechSynthesis?.cancel();
      speakQueueRef.current = [];
      isSpeakingRef.current = false;
      setIsSpeaking(false);
    }
  };

  // ── Sentence-by-sentence TTS queue ───────────────────────────
  const processSpeakQueue = () => {
    if (isSpeakingRef.current || speakQueueRef.current.length === 0) return;

    const sentence = speakQueueRef.current.shift();
    if (!sentence?.trim()) {
      processSpeakQueue();
      return;
    }

    isSpeakingRef.current = true;
    setIsSpeaking(true);

    const savedVoiceURI = localStorage.getItem('mindmate_tts_voice');
    const utterance = new SpeechSynthesisUtterance(sentence);
    utterance.rate = 0.88;
    utterance.pitch = 1.05;
    utterance.volume = 1.0;

    const voice = selectBestVoice(savedVoiceURI);
    if (voice) utterance.voice = voice;

    utterance.onend = () => {
      isSpeakingRef.current = false;
      if (speakQueueRef.current.length > 0) {
        processSpeakQueue();
      } else {
        setIsSpeaking(false);
      }
    };
    utterance.onerror = () => {
      isSpeakingRef.current = false;
      processSpeakQueue();
    };

    window.speechSynthesis.speak(utterance);
  };

  const speakResponse = (text) => {
    if (!window.speechSynthesis || !isVoiceEnabled) return;
    window.speechSynthesis.cancel();
    speakQueueRef.current = [];
    isSpeakingRef.current = false;

    const clean = stripMarkdown(text);
    const sentences = splitIntoSentences(clean);
    speakQueueRef.current = sentences;

    // Small delay so voices load on first use
    setTimeout(processSpeakQueue, 100);
  };

  // ── Mic toggle ───────────────────────────────────────────────
  const toggleListen = () => {
    if (!recognitionRef.current) {
      alert('Your browser does not support Speech Recognition.');
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      window.speechSynthesis?.cancel();
      speakQueueRef.current = [];
      isSpeakingRef.current = false;
      setIsSpeaking(false);
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  // ── Backend API Call ──────────────────────────────────────────
  const getBackendResponse = async (userMessage) => {
    try {
      const userId = localStorage.getItem('mindmate_user_id') || 'default-user';
      const response = await fetch(`${API_BASE_URL}/api/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          conversation_id: conversationId,
          message: userMessage,
        }),
      });

      if (!response.ok) throw new Error(`Backend error: ${response.status}`);
      const data = await response.json();

      if (data.conversation_id) setConversationId(data.conversation_id);

      if (data.agent_output?.emotion) {
        const emotionMap = {
          joy: { label: 'Happy', score: 5 },
          content: { label: 'Happy', score: 5 },
          happy: { label: 'Happy', score: 5 },
          grateful: { label: 'Happy', score: 5 },
          excited: { label: 'Happy', score: 5 },
          sadness: { label: 'Sad', score: 1 },
          sad: { label: 'Sad', score: 1 },
          depressed: { label: 'Sad', score: 1 },
          down: { label: 'Sad', score: 1 },
          grief: { label: 'Sad', score: 1 },
          lonely: { label: 'Sad', score: 1 },
          anger: { label: 'Stressed', score: 2 },
          angry: { label: 'Stressed', score: 2 },
          frustrated: { label: 'Stressed', score: 2 },
          frustration: { label: 'Stressed', score: 2 },
          anxiety: { label: 'Anxious', score: 2 },
          anxious: { label: 'Anxious', score: 2 },
          fear: { label: 'Anxious', score: 2 },
          worry: { label: 'Anxious', score: 2 },
          panic: { label: 'Anxious', score: 2 },
          stressed: { label: 'Stressed', score: 2 },
          stress: { label: 'Stressed', score: 2 },
          overwhelmed: { label: 'Stressed', score: 2 },
          neutral: { label: 'Neutral', score: 3 },
          calm: { label: 'Neutral', score: 3 },
          surprised: { label: 'Neutral', score: 3 },
        };
        const detected = emotionMap[data.agent_output.emotion.toLowerCase()] || { label: 'Neutral', score: 3 };
        if (detected.label !== 'Neutral') {
          saveMoodLog(detected);
        }
      }

      setBackendAvailable(true);
      return data.response;
    } catch (error) {
      console.error('Backend API Error:', error);
      setBackendAvailable(false);
      return null;
    }
  };

  // ── Groq Fallback ─────────────────────────────────────────────
  const getGroqFallback = async (chatHistory) => {
    const apiKey = localStorage.getItem('groq_api_key');
    if (!apiKey) return "I'm having trouble connecting right now. Please ensure the backend server is running.";

    const voiceStyle = localStorage.getItem('mindmate_voice_style') || 'calm';
    const personaMap = {
      upbeat: 'Be highly energetic, upbeat, and extremely motivating.',
      empathetic: 'Be deeply empathetic, gentle, and emotionally attuned.',
      tough_love: 'Provide direct, no-nonsense tough love advice.',
      clinical: 'Be professional, objective, and clinical.',
      zen: 'Speak like a Zen master. Use metaphors and mindfulness.',
    };
    const personaPrompt = personaMap[voiceStyle] || 'Be gently empathetic and supportive.';

    const apiMessages = [
      { role: 'system', content: `You are MindMate, an Emotional Intelligence AI wellness companion. ${personaPrompt} Keep responses to 2-3 sentences.` },
      ...chatHistory.map(msg => ({ role: msg.role === 'ai' ? 'assistant' : 'user', content: msg.content })),
    ];

    try {
      const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
        body: JSON.stringify({ model: 'llama-3.1-8b-instant', messages: apiMessages, temperature: 0.3, max_tokens: 150 }),
      });
      if (!response.ok) throw new Error('Groq API failed');
      const data = await response.json();
      return data.choices[0].message.content;
    } catch {
      return "I'm having trouble connecting right now. Please check your connection and try again.";
    }
  };

  // ── Main message processor ────────────────────────────────────
  const processMessage = async (userMessage) => {
    if (!userMessage.trim() || isLoading) return;

    setTextInput('');
    setIsLoading(true);

    const detectedMood = analyzeMood(userMessage);
    if (detectedMood.label !== 'Neutral' || !backendAvailable) saveMoodLog(detectedMood);

    const updatedHistory = [...messages, { role: 'user', content: userMessage }];
    setMessages(updatedHistory);

    // Try backend, then Groq fallback
    let responseText = await getBackendResponse(userMessage);
    if (responseText === null) responseText = await getGroqFallback(updatedHistory);

    setIsLoading(false);

    // Start TTS on first sentence immediately — don't wait for full display
    if (isVoiceEnabled) speakResponse(responseText);

    // Word-by-word display (faster than char-by-char, less latency)
    const words = responseText.split(' ');
    setMessages(prev => [...prev, { role: 'ai', content: '' }]);

    let currentText = '';
    for (let i = 0; i < words.length; i++) {
      currentText += (i === 0 ? '' : ' ') + words[i];
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = { ...newMessages[newMessages.length - 1], content: currentText };
        return newMessages;
      });
      await new Promise(r => setTimeout(r, 18));
    }
    fetchHistory();
  };


  const handleSendText = (e) => {
    e.preventDefault();
    processMessage(textInput);
  };

  return (
    <div className="h-full flex flex-row relative bg-background overflow-hidden" style={{ minHeight: 0 }}>
      
      {/* ── Left Sidebar (History & New Chat) ───────────────── */}
      {isSidebarOpen && (
        <div className="w-72 bg-[#152228] text-[#eaefef] p-4 flex flex-col border-r border-[#2a424d] shrink-0 shadow-2xl z-20 transition-all duration-300">
          
          {/* New Chat Button */}
          <button
            onClick={handleNewChat}
            className="flex items-center space-x-3 w-full p-3.5 mb-5 bg-[#1d2f38] hover:bg-[#2a424d] text-white rounded-2xl text-sm font-medium transition-all duration-300 border border-[#2a424d] shadow-md group"
          >
            <div className="p-1.5 rounded-xl bg-primary/20 text-primary group-hover:scale-110 transition-transform">
              <Plus className="w-4 h-4" />
            </div>
            <span className="flex-1 text-left font-semibold tracking-wide">New Chat</span>
          </button>

          <div className="text-[11px] font-semibold text-[#91a8b2] uppercase tracking-wider px-2 mb-2.5 flex items-center justify-between">
            <span>Older Chats</span>
            <span className="text-[#5a737e] font-normal">{conversationsList.length}</span>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 scrollbar-thin scrollbar-thumb-[#2a424d] scrollbar-track-transparent">
            {conversationsList.length === 0 ? (
              <div className="text-center py-8 px-4 text-[#5a737e] text-xs italic">
                No older chats yet. Start talking to build your history!
              </div>
            ) : (
              conversationsList.map((convo) => {
                const isSelected = convo.id === conversationId;
                return (
                  <div
                    key={convo.id}
                    onClick={() => handleSelectConversation(convo.id)}
                    className={`group relative flex items-center justify-between p-3.5 rounded-2xl cursor-pointer text-sm transition-all duration-200 ${
                      isSelected
                        ? 'bg-[#1d2f38] text-white font-medium border-l-4 border-primary shadow-md'
                        : 'text-[#91a8b2] hover:bg-[#1d2f38]/60 hover:text-white border-l-4 border-transparent'
                    }`}
                  >
                    <div className="flex items-center space-x-3 overflow-hidden pr-6">
                      <MessageSquare className={`w-4 h-4 shrink-0 transition-colors ${isSelected ? 'text-primary' : 'text-[#5a737e] group-hover:text-[#91a8b2]'}`} />
                      <span className="truncate tracking-tight leading-snug">
                        {convo.title || 'Untitled Conversation'}
                      </span>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(convo.id, e)}
                      title="Delete chat"
                      className="absolute right-2.5 p-1.5 text-[#5a737e] hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg hover:bg-[#2a424d]"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Sidebar Footer */}
          <div className="mt-auto pt-3.5 border-t border-[#2a424d]/60 text-center">
            <span className="text-[11px] text-[#91a8b2] tracking-wider font-medium uppercase">Aura AI History</span>
          </div>
        </div>
      )}

      {/* ── Main Chat & Voice Area ──────────────────────────── */}
      <div className="flex-1 flex flex-col relative bg-background h-full overflow-hidden" style={{ minHeight: 0 }}>

        {/* Header */}
        <div className="flex items-center space-x-3 p-6 border-b border-border bg-surface/80 backdrop-blur-md shrink-0 sticky top-0 z-10">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 rounded-2xl text-muted-foreground hover:bg-muted transition-colors mr-1"
            title={isSidebarOpen ? 'Close Sidebar' : 'Open Sidebar'}
          >
            {isSidebarOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
          </button>

          <HeartPulse className="text-primary w-6 h-6" />
          <h1 className="text-lg font-semibold text-foreground flex-1 font-heading">
            {conversationsList.find(c => c.id === conversationId)?.title || 'Aura Session'}
          </h1>

          {isSpeaking && (
            <div className="flex items-center space-x-1.5 text-xs font-medium text-primary mr-2 bg-primary/10 px-3 py-1.5 rounded-full border border-primary/20">
              <Volume2 className="w-3.5 h-3.5 animate-pulse" />
              <span>Speaking…</span>
            </div>
          )}

          <button
            onClick={toggleVoiceEnabled}
            id="voice-toggle-btn"
            className={`p-2 rounded-2xl transition-all duration-300 flex items-center justify-center ${isVoiceEnabled ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-border'}`}
            title={isVoiceEnabled ? 'Disable Voice Output' : 'Enable Voice Output'}
          >
            {isVoiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>

          {!backendAvailable && (
            <div className="ml-3 bg-yellow-50 text-yellow-700 dark:bg-yellow-950/30 dark:text-yellow-400 px-3 py-1.5 rounded-2xl flex items-center space-x-2 border border-yellow-200 dark:border-yellow-900">
              <AlertTriangle className="w-4 h-4" />
              <p className="text-xs font-medium">Using Groq Fallback</p>
            </div>
          )}
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-border" style={{ minHeight: 0 }}>
          <div className="max-w-3xl mx-auto w-full space-y-6">
            {messages.map((msg, index) => (
              <div key={index} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`max-w-[85%] md:max-w-[75%] p-5 text-[15px] leading-relaxed rounded-3xl transition-all duration-300 ${
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-tr-none shadow-md font-medium'
                    : 'bg-surface text-foreground rounded-tl-none border border-border/80 shadow-sm'
                }`}>
                  {msg.content || (msg.role === 'ai' && isLoading ? (
                    <div className="flex space-x-1.5 py-2">
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
                    </div>
                  ) : '')}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center space-x-2 text-muted-foreground text-sm pl-2 py-2">
                <Activity className="w-4 h-4 animate-pulse text-primary" />
                <span>Aura is thinking…</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-6 border-t border-border/80 bg-background shrink-0">
          <div className="max-w-3xl mx-auto w-full">
            <form onSubmit={handleSendText} className="relative flex items-center space-x-3">
              <button
                type="button"
                id="mic-toggle-btn"
                onClick={toggleListen}
                className={`flex-shrink-0 p-4 rounded-2xl transition-all duration-300 ${isListening ? 'bg-red-500 text-white scale-110 shadow-lg shadow-red-500/25 animate-pulse' : 'bg-surface border border-border text-foreground hover:bg-muted shadow-sm'}`}
              >
                {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5 text-primary" />}
              </button>

              <input
                type="text"
                id="voice-text-input"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder={isListening ? 'Listening…' : 'Message Aura…'}
                disabled={isLoading || isListening}
                className="flex-1 bg-surface border border-border/80 rounded-2xl py-4 pl-6 pr-14 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all duration-300 disabled:opacity-50 shadow-sm"
              />

              <button
                type="submit"
                id="voice-send-btn"
                disabled={!textInput.trim() || isLoading || isListening}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-2.5 bg-primary text-primary-foreground rounded-xl transition-all duration-300 disabled:opacity-50 disabled:scale-95 shadow-md hover:opacity-95"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            <div className="text-center mt-3.5">
              <span className="text-[11px] text-muted-foreground font-medium tracking-wide">Aura can make mistakes. Consider verifying important information.</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}

