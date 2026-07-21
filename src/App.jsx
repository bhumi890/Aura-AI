import React, { useState, useEffect } from 'react';
import { Settings, Home, Mic, LogOut, Sun, Moon } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import VoiceChat from './pages/VoiceChat';
import SettingsPage from './pages/Settings';
import Login from './pages/Login';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [theme, setTheme] = useState('light');

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('mindmate_theme');
    if (savedTheme) {
      setTheme(savedTheme);
      if (savedTheme === 'dark') document.documentElement.classList.add('dark');
      else document.documentElement.classList.remove('dark');
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? 'dark' : 'light');
      if (prefersDark) document.documentElement.classList.add('dark');
    }
    
    // Check if user is logged in
    const authStatus = localStorage.getItem('mindmate_auth');
    if (authStatus === 'true') {
      setIsAuthenticated(true);
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('mindmate_theme', newTheme);
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('mindmate_auth');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <Login onLogin={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="flex h-screen bg-background text-foreground transition-colors duration-300">
      
      {/* Serene Aura Sidebar */}
      <div className="w-64 border-r border-border bg-surface flex flex-col transition-colors duration-300">
        <div className="p-8 flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-primary animate-pulse"></div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground font-heading">Aura<span className="text-primary font-light">.</span></h1>
        </div>
        
        <nav className="flex-1 px-4 space-y-2.5">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`w-full flex items-center space-x-3.5 px-4 py-3.5 rounded-2xl transition-all duration-300 ${activeTab === 'dashboard' ? 'bg-primary text-primary-foreground font-medium shadow-md' : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground'}`}
          >
            <Home className="w-5 h-5" />
            <span>Dashboard</span>
          </button>
          
          <button 
            onClick={() => setActiveTab('voice')}
            className={`w-full flex items-center space-x-3.5 px-4 py-3.5 rounded-2xl transition-all duration-300 ${activeTab === 'voice' ? 'bg-primary text-primary-foreground font-medium shadow-md' : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground'}`}
          >
            <Mic className="w-5 h-5" />
            <span>Voice Session</span>
          </button>
          
          <button 
            onClick={() => setActiveTab('settings')}
            className={`w-full flex items-center space-x-3.5 px-4 py-3.5 rounded-2xl transition-all duration-300 ${activeTab === 'settings' ? 'bg-primary text-primary-foreground font-medium shadow-md' : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground'}`}
          >
            <Settings className="w-5 h-5" />
            <span>Settings</span>
          </button>
        </nav>
        
        <div className="p-4 border-t border-border/70 space-y-2">
          <button 
            onClick={toggleTheme}
            className="w-full flex items-center space-x-3.5 px-4 py-3.5 rounded-2xl text-muted-foreground hover:bg-muted/70 hover:text-foreground transition-all duration-300"
          >
            {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            <span>{theme === 'light' ? 'Dark Mode' : 'Light Mode'}</span>
          </button>

          <button 
            onClick={handleLogout}
            className="w-full flex items-center space-x-3.5 px-4 py-3.5 rounded-2xl text-muted-foreground hover:bg-red-500/10 hover:text-red-600 dark:hover:text-red-400 transition-all duration-300"
          >
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden relative bg-background transition-colors duration-300">
        <div style={{ display: activeTab === 'dashboard' ? 'flex' : 'none' }} className="h-full flex-col">
          <Dashboard activeTab={activeTab} />
        </div>
        <div style={{ display: activeTab === 'voice' ? 'flex' : 'none' }} className="h-full flex-col">
          <VoiceChat />
        </div>
        <div style={{ display: activeTab === 'settings' ? 'flex' : 'none' }} className="h-full flex-col">
          <SettingsPage />
        </div>
      </div>

    </div>
  );
}

export default App;
