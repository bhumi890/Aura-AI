import React, { useEffect, useState } from 'react';
import { Activity, Brain, Clock, HeartPulse, Sparkles, TrendingUp } from 'lucide-react';
import { analyzeMood, getMoodLogs } from '../utils/moodAnalyzer';
import { API_BASE_URL } from '../config';

export default function Dashboard({ activeTab }) {
  const [moodData, setMoodData] = useState({
    currentMood: "Neutral",
    trend: "Stable",
    totalLogs: 0
  });

  // Fetch the latest logs and session emotions whenever the Dashboard mounts or tab becomes active
  useEffect(() => {
    if (activeTab && activeTab !== 'dashboard') return;

    const fetchSessionMoods = async () => {
      let combinedLogs = [...getMoodLogs()];
      try {
        const userId = localStorage.getItem('mindmate_user_id') || 'default-user';
        const res = await fetch(`${API_BASE_URL}/api/history/?user_id=${userId}&page_size=10`);
        if (res.ok) {
          const data = await res.json();
          const items = data.items || [];
          for (const item of items.slice(0, 5)) {
            const detailRes = await fetch(`${API_BASE_URL}/api/history/${item.id}`);
            if (detailRes.ok) {
              const detailData = await detailRes.json();
              if (detailData.messages) {
                for (const msg of detailData.messages) {
                  let ts = msg.created_at || new Date().toISOString();
                  if (typeof ts === 'string' && !ts.endsWith('Z') && !ts.includes('+')) {
                    ts = ts.replace(' ', 'T') + 'Z';
                  }

                  // 1. Check user message content directly
                  if (msg.role && msg.role.toLowerCase() === 'user' && msg.content) {
                    const analyzed = analyzeMood(msg.content);
                    if (analyzed && analyzed.label !== 'Neutral') {
                      combinedLogs.push({ label: analyzed.label, score: analyzed.score, timestamp: ts });
                    }
                  }

                  // 2. Check assistant emotion metadata
                  if (msg.emotion && msg.emotion !== 'neutral') {
                    const em = msg.emotion.toLowerCase();
                    let label = 'Neutral';
                    let score = 3;
                    if (['happy', 'joy', 'content', 'excited', 'grateful', 'uplifted'].includes(em)) { label = 'Happy'; score = 5; }
                    else if (['sad', 'sadness', 'depressed', 'down', 'grief', 'lonely', 'distressed'].includes(em)) { label = 'Sad'; score = 1; }
                    else if (['anxious', 'anxiety', 'fear', 'worry', 'panic'].includes(em)) { label = 'Anxious'; score = 2; }
                    else if (['stressed', 'stress', 'anger', 'angry', 'frustrated'].includes(em)) { label = 'Stressed'; score = 2; }
                    
                    if (label !== 'Neutral') {
                      combinedLogs.push({ label, score, timestamp: ts });
                    }
                  }
                }
              }
            }
          }
        }
      } catch (e) {
        console.error('Failed to sync session moods:', e);
      }

      // Sort by timestamp chronologically
      combinedLogs.sort((a, b) => new Date(a.timestamp || 0) - new Date(b.timestamp || 0));

      if (combinedLogs.length > 0) {
        const nonNeutralLogs = combinedLogs.filter(l => l.label && l.label !== 'Neutral');
        const latestLog = nonNeutralLogs.length > 0 ? nonNeutralLogs[nonNeutralLogs.length - 1] : combinedLogs[combinedLogs.length - 1];
        
        let trendStr = "Stable";
        const relevantLogs = nonNeutralLogs.length > 1 ? nonNeutralLogs : combinedLogs;
        if (relevantLogs.length > 1) {
          const prevLog = relevantLogs[relevantLogs.length - 2];
          if (latestLog.score > prevLog.score) trendStr = "Improving";
          else if (latestLog.score < prevLog.score) trendStr = "Declining";
        }

        setMoodData({
          currentMood: latestLog.label || "Neutral",
          trend: trendStr,
          totalLogs: combinedLogs.length
        });
      }
    };

    fetchSessionMoods();

    const handleUpdate = () => fetchSessionMoods();
    window.addEventListener('mood_updated', handleUpdate);
    window.addEventListener('storage', handleUpdate);
    return () => {
      window.removeEventListener('mood_updated', handleUpdate);
      window.removeEventListener('storage', handleUpdate);
    };
  }, [activeTab]);


  // Helper for Aura mood colors
  const getMoodColor = (mood) => {
    const m = mood.toLowerCase();
    if (m === 'happy' || m === 'excited' || m === 'calm' || m === 'uplifted') return 'text-[#2C5364] dark:text-[#8FB5A9] font-bold';
    if (m === 'sad' || m === 'angry' || m === 'anxious' || m === 'stressed' || m === 'distressed') return 'text-[#D97757] dark:text-[#E29578] font-bold';
    return 'text-[#5A737E] dark:text-[#91A8B2] font-semibold';
  };

  return (
    <div className="h-full p-8 md:p-10 overflow-y-auto">
      <header className="mb-10">
        <h1 className="text-4xl font-bold tracking-tight text-foreground mb-2 font-heading">Dashboard</h1>
        <p className="text-muted-foreground text-base">Your personal, serene emotional wellness overview.</p>
      </header>

      {/* Main Aura Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        
        {/* Mood Card */}
        <div className="surface-panel p-7 flex flex-col justify-between relative overflow-hidden group hover:border-primary/40">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-10 -mt-10 blur-xl transition-all group-hover:bg-primary/10"></div>
          <div className="flex justify-between items-start mb-6 relative z-10">
            <h3 className="text-sm font-medium text-muted-foreground tracking-wide uppercase">Current Mood</h3>
            <div className="p-3 bg-primary/10 rounded-2xl border border-primary/15">
              <Brain className="w-5 h-5 text-primary" />
            </div>
          </div>
          <div className="relative z-10">
            <p className={`text-4xl font-heading capitalize ${getMoodColor(moodData.currentMood)}`}>
              {moodData.currentMood}
            </p>
            <p className="text-xs text-muted-foreground mt-2 font-medium">Based on your latest session</p>
          </div>
        </div>

        {/* Trend Card */}
        <div className="surface-panel p-7 flex flex-col justify-between relative overflow-hidden group hover:border-primary/40">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-10 -mt-10 blur-xl transition-all group-hover:bg-primary/10"></div>
          <div className="flex justify-between items-start mb-6 relative z-10">
            <h3 className="text-sm font-medium text-muted-foreground tracking-wide uppercase">Wellness Trend</h3>
            <div className="p-3 bg-primary/10 rounded-2xl border border-primary/15">
              <TrendingUp className="w-5 h-5 text-primary" />
            </div>
          </div>
          <div className="relative z-10">
            <p className="text-4xl font-bold font-heading text-foreground">
              {moodData.trend}
            </p>
            <p className="text-xs text-muted-foreground mt-2 font-medium">Compared to previous log</p>
          </div>
        </div>

        {/* Activity Card */}
        <div className="surface-panel p-7 flex flex-col justify-between relative overflow-hidden group hover:border-primary/40">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-10 -mt-10 blur-xl transition-all group-hover:bg-primary/10"></div>
          <div className="flex justify-between items-start mb-6 relative z-10">
            <h3 className="text-sm font-medium text-muted-foreground tracking-wide uppercase">Total Sessions</h3>
            <div className="p-3 bg-primary/10 rounded-2xl border border-primary/15">
              <Activity className="w-5 h-5 text-primary" />
            </div>
          </div>
          <div className="relative z-10">
            <p className="text-4xl font-bold font-heading text-foreground">
              {moodData.totalLogs}
            </p>
            <p className="text-xs text-muted-foreground mt-2 font-medium">Interactions analyzed</p>
          </div>
        </div>

      </div>

      {/* Aura Sage Info Section */}
      <div className="aura-sage-box flex flex-col md:flex-row items-start md:items-center space-y-4 md:space-y-0 md:space-x-6 shadow-md">
        <div className="p-4 bg-surface rounded-2xl border border-border shadow-sm">
          <Sparkles className="w-7 h-7 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-foreground mb-2 font-heading">How Aura Works</h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-3xl font-normal">
            Aura actively analyzes the nuanced emotional sentiment of your text and voice inputs during every session. 
            These interactions are processed intelligently to determine your emotional state over time, allowing your dashboard to reflect your genuine mental wellness journey with complete accuracy and care.
          </p>
        </div>
      </div>
      
    </div>
  );
}
