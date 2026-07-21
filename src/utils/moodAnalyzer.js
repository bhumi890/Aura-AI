export const analyzeMood = (text) => {
  if (!text) return { label: 'Neutral', score: 3, color: 'text-gray-400', iconClass: 'bg-white/10' };
  const lowerText = text.toLowerCase();
  
  // Crisis / Deep Distress / Suicidal Ideation / Severe Sadness
  if (
    lowerText.includes('die') || lowerText.includes('suicide') || lowerText.includes('kill') ||
    lowerText.includes('hopeless') || lowerText.includes('hurt') || lowerText.includes('terrible') ||
    lowerText.includes('sad') || lowerText.includes('down') || lowerText.includes('depress') ||
    lowerText.includes('cry') || lowerText.includes('grief') || lowerText.includes('lonely') ||
    lowerText.includes('alone') || lowerText.includes('empty') || lowerText.includes('pain') ||
    lowerText.includes('miserable') || lowerText.includes('broken') || lowerText.includes('heartbroken')
  ) {
    return { label: 'Distressed', score: 1, color: 'text-red-400', iconClass: 'bg-red-500/20' };
  }

  // Anxiety / Fear / Panic
  if (
    lowerText.includes('anxious') || lowerText.includes('anxiety') || lowerText.includes('worry') ||
    lowerText.includes('panic') || lowerText.includes('fear') || lowerText.includes('scared') ||
    lowerText.includes('afraid') || lowerText.includes('nervous') || lowerText.includes('terrified')
  ) {
    return { label: 'Anxious', score: 2, color: 'text-amber-400', iconClass: 'bg-amber-500/20' };
  }

  // Stress / Anger / Frustration
  if (
    lowerText.includes('stress') || lowerText.includes('overwhelm') || lowerText.includes('pressure') ||
    lowerText.includes('angry') || lowerText.includes('anger') || lowerText.includes('frustrated') ||
    lowerText.includes('annoyed') || lowerText.includes('mad') || lowerText.includes('tired') ||
    lowerText.includes('exhausted') || lowerText.includes('burnout')
  ) {
    return { label: 'Stressed', score: 2, color: 'text-orange-400', iconClass: 'bg-orange-500/20' };
  }

  // Happy / Joyful / Positive
  if (
    lowerText.includes('happy') || lowerText.includes('good') || lowerText.includes('great') ||
    lowerText.includes('awesome') || lowerText.includes('love') || lowerText.includes('cheerful') ||
    lowerText.includes('wonderful') || lowerText.includes('excited') || lowerText.includes('grateful') ||
    lowerText.includes('glad') || lowerText.includes('blessed') || lowerText.includes('amazing')
  ) {
    return { label: 'Happy', score: 5, color: 'text-emerald-400', iconClass: 'bg-emerald-500/20' };
  }

  // Calm / Relaxed
  if (
    lowerText.includes('calm') || lowerText.includes('relax') || lowerText.includes('peace') ||
    lowerText.includes('better') || lowerText.includes('soothed') || lowerText.includes('okay') ||
    lowerText.includes('fine') || lowerText.includes('alright')
  ) {
    return { label: 'Calm', score: 4, color: 'text-teal-400', iconClass: 'bg-teal-500/20' };
  }

  // Default fallback
  return { label: 'Neutral', score: 3, color: 'text-gray-400', iconClass: 'bg-white/10' };
};

export const saveMoodLog = (moodResult) => {
  const logs = JSON.parse(localStorage.getItem('mindmate_mood_logs') || '[]');
  
  const newLog = {
    ...moodResult,
    timestamp: new Date().toISOString()
  };
  
  logs.push(newLog);
  // Keep only the last 50 logs to avoid localStorage bloat
  if (logs.length > 50) logs.shift();
  
  localStorage.setItem('mindmate_mood_logs', JSON.stringify(logs));
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event('mood_updated'));
  }
  return logs;
};

export const getMoodLogs = () => {
  const logs = localStorage.getItem('mindmate_mood_logs');
  if (!logs) return [];
  try {
    return JSON.parse(logs);
  } catch (e) {
    console.error("Failed to parse mood logs:", e);
    return [];
  }
};
