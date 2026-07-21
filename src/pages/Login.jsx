import React, { useState } from 'react';
import { LogIn, UserPlus, ShieldCheck, HeartPulse, Loader2 } from 'lucide-react';

export default function Login({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }

    setIsLoading(true);
    const endpoint = isRegistering ? '/api/users/register' : '/api/users/login';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Authentication failed (${res.status})`);
      }

      const data = await res.json();
      localStorage.setItem('mindmate_auth', 'true');
      localStorage.setItem('mindmate_user_id', data.user_id);
      localStorage.setItem('mindmate_username', data.username);
      localStorage.setItem('mindmate_token', data.token);

      onLogin();
    } catch (err) {
      // If backend is not available, allow offline demo fallback if login or registration is attempted
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        const demoId = `user_${username.trim().toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
        localStorage.setItem('mindmate_auth', 'true');
        localStorage.setItem('mindmate_user_id', demoId);
        localStorage.setItem('mindmate_username', username.trim());
        onLogin();
      } else {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleBypass = () => {
    localStorage.setItem('mindmate_auth', 'true');
    localStorage.setItem('mindmate_user_id', 'default-user');
    localStorage.setItem('mindmate_username', 'Demo User');
    onLogin();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground transition-colors duration-300 p-4">
      
      <div className="w-full max-w-md surface-panel p-9 border border-border/80 shadow-xl">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-primary/10 rounded-3xl flex items-center justify-center mb-4 border border-primary/20 shadow-inner">
            <HeartPulse className="w-8 h-8 text-primary animate-pulse" />
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-2 font-heading tracking-tight">
            {isRegistering ? 'Create Account' : 'Welcome to Aura'}
          </h1>
          <p className="text-sm text-muted-foreground text-center max-w-xs">
            {isRegistering
              ? 'Join Aura and begin your calm, personalized emotional wellness journey.'
              : 'Your serene, intelligent emotional wellness companion.'}
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3.5 bg-red-50 text-red-600 dark:bg-red-950/50 dark:text-red-400 text-sm rounded-2xl border border-red-200 dark:border-red-900 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Username</label>
            <input 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-input border border-border/80 rounded-2xl py-3 px-4 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all duration-300"
              placeholder="Choose a username"
              disabled={isLoading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-input border border-border/80 rounded-2xl py-3 px-4 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all duration-300"
              placeholder={isRegistering ? 'Choose a password' : 'Enter your password'}
              disabled={isLoading}
            />
          </div>

          <button 
            type="submit"
            disabled={isLoading}
            className="w-full btn-primary flex items-center justify-center space-x-2 py-3.5 mt-2"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : isRegistering ? (
              <UserPlus className="w-5 h-5" />
            ) : (
              <LogIn className="w-5 h-5" />
            )}
            <span>{isLoading ? 'Processing...' : isRegistering ? 'Create Account & Start' : 'Sign In to Aura'}</span>
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => { setIsRegistering(!isRegistering); setError(''); }}
            className="text-sm text-primary hover:underline font-medium transition-colors"
          >
            {isRegistering
              ? 'Already have an account? Sign in here.'
              : "Don't have an account? Create one right now."}
          </button>
        </div>

        <div className="mt-8 pt-6 border-t border-border/70">
          <button 
            onClick={handleBypass}
            className="w-full btn-secondary flex items-center justify-center space-x-2 py-3"
          >
            <ShieldCheck className="w-4 h-4 text-primary" />
            <span>Quick Demo Bypass</span>
          </button>
          <p className="text-xs text-muted-foreground text-center mt-3">
            Use Quick Demo Bypass to skip authentication immediately with default user.
          </p>
        </div>
      </div>
    </div>
  );
}
