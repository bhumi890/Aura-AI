export const analyzeMood = (text) => {
  const lowerText = text.toLowerCase();
  
  if (lowerText.includes('stress') || lowerText.includes('overwhelm') || lowerText.includes('pressure')) {
    return { label: 'Stressed', score: 2, color: 'text-wellness-danger', iconClass: 'bg-wellness-danger/20' };
  }
  if (lowerText.includes('anxious') || lowerText.includes('worry') || lowerText.includes('panic')) {
    return { label: 'Anxious', score: 2, color: 'text-wellness-danger', iconClass: 'bg-wellness-danger/20' };
  }
  if (lowerText.includes('sad') || lowerText.includes('down') || lowerText.includes('depress')) {
    return { label: 'Sad', score: 1, color: 'text-wellness-secondary', iconClass: 'bg-wellness-secondary/20' };
  }
  if (lowerText.includes('happy') || lowerText.includes('good') || lowerText.includes('great') || lowerText.includes('awesome')) {
    return { label: 'Happy', score: 5, color: 'text-wellness-success', iconClass: 'bg-wellness-success/20' };
  }
  if (lowerText.includes('okay') || lowerText.includes('fine') || lowerText.includes('alright')) {
    return { label: 'Neutral', score: 3, color: 'text-gray-400', iconClass: 'bg-white/10' };
  }
  
  // Default fallback if no keywords matched
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
