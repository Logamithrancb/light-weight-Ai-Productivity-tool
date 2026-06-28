import React, { useState, useEffect, useRef } from 'react';
import { 
  Home, CheckSquare, FileText, Search, BarChart2, 
  Mic, MicOff, Plus, Trash2, Calendar, Tag, 
  AlertCircle, CheckCircle2, Database, Sparkles, Clock,
  ArrowRight, Info, Check, Filter, CalendarDays, RefreshCw,
  Settings, LogOut
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';

const API_BASE = "http://127.0.0.1:8000";

// Audio Helpers for 16kHz mono WAV encoding in browser
const writeString = (view, offset, string) => {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
};

const floatTo16BitPCM = (output, offset, input) => {
  for (let i = 0; i < input.length; i++, offset += 2) {
    let s = Math.max(-1, Math.min(1, input[i]));
    output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }
};

const encodeWAV = (samples, sampleRate) => {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, 'data');
  view.setUint32(40, samples.length * 2, true);
  
  floatTo16BitPCM(view, 44, samples);
  
  return new Blob([view], { type: 'audio/wav' });
};

// Colors for Category badges
const CATEGORY_COLORS = {
  Study: { bg: "bg-blue-950/40", text: "text-blue-400", border: "border-blue-900/40" },
  Work: { bg: "bg-purple-950/40", text: "text-purple-400", border: "border-purple-900/40" },
  Shopping: { bg: "bg-pink-950/40", text: "text-pink-400", border: "border-pink-900/40" },
  Health: { bg: "bg-emerald-950/40", text: "text-emerald-400", border: "border-emerald-900/40" },
  Personal: { bg: "bg-amber-950/40", text: "text-amber-400", border: "border-amber-900/40" },
  Finance: { bg: "bg-teal-950/40", text: "text-teal-400", border: "border-teal-900/40" }
};

// Colors for Priority badges
const PRIORITY_COLORS = {
  High: { bg: "bg-red-950/60 text-red-400", text: "text-red-400", border: "border-red-900/60" },
  Medium: { bg: "bg-amber-950/40 text-amber-400", text: "text-amber-400", border: "border-amber-900/40" },
  Low: { bg: "bg-blue-950/40 text-blue-400", text: "text-blue-400", border: "border-blue-900/40" }
};

// Chart Colors
const PIE_COLORS = ['#3b82f6', '#a855f7', '#10b981', '#f59e0b', '#ec4899', '#14b8a6'];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tasks, setTasks] = useState([]);
  const [dailySummary, setDailySummary] = useState(null);
  const [weeklyAnalytics, setWeeklyAnalytics] = useState(null);
  const [backendStatus, setBackendStatus] = useState(null);
  
  // Authentication & Profile state
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('sysai_authenticated') === 'true';
  });
  const [authMode, setAuthMode] = useState('login');
  const [emailInput, setEmailInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [nameInput, setNameInput] = useState('');
  const [userProfile, setUserProfile] = useState(() => {
    const saved = localStorage.getItem('sysai_profile');
    return saved ? JSON.parse(saved) : { name: 'Demo User', role: 'Productivity Architect', theme: 'dark' };
  });

  // Settings view parameters
  const [voiceThreshold, setVoiceThreshold] = useState('0.5');
  const [dbTypeSetting, setDbTypeSetting] = useState('SQLite');

  // Input fields
  const [taskInput, setTaskInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Audio recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const recordingTimer = useRef(null);

  // Audio Context Ref for recording
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const streamRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  // Filters for Task Board
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');

  // Fetch initial data
  useEffect(() => {
    fetchStatus();
    fetchTasks();
    fetchDailySummary();
    fetchWeeklyAnalytics();
  }, []);

  // Update voice timer
  useEffect(() => {
    if (isRecording) {
      recordingTimer.current = setInterval(() => {
        setRecordingSeconds(prev => prev + 1);
      }, 1000);
    } else {
      clearInterval(recordingTimer.current);
      setRecordingSeconds(0);
    }
    return () => clearInterval(recordingTimer.current);
  }, [isRecording]);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/`);
      const data = await res.json();
      setBackendStatus(data);
    } catch (e) {
      console.error("Backend offline", e);
    }
  };

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/tasks`);
      const data = await res.json();
      setTasks(data);
    } catch (e) {
      console.error("Error fetching tasks", e);
    }
  };

  const fetchDailySummary = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/analytics/summary`);
      const data = await res.json();
      setDailySummary(data);
    } catch (e) {
      console.error("Error fetching summary", e);
    }
  };

  const fetchWeeklyAnalytics = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/analytics/weekly`);
      const data = await res.json();
      setWeeklyAnalytics(data);
    } catch (e) {
      console.error("Error fetching weekly analytics", e);
    }
  };

  const handleCapture = async (e) => {
    e?.preventDefault();
    if (!taskInput.trim()) return;
    setLoading(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/tasks/capture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: taskInput })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setSuccessMessage(`Captured ${data.item.intent}: "${data.item.text}"`);
        setTaskInput('');
        fetchTasks();
        fetchDailySummary();
        fetchWeeklyAnalytics();
        fetchStatus(); // update loaded modules status
      } else {
        setErrorMessage(data.detail || "Capture failed.");
      }
    } catch (err) {
      setErrorMessage("Could not connect to the local server.");
    } finally {
      setLoading(false);
    }
  };

  // Browser-based WAV recording
  const startRecording = async () => {
    setErrorMessage('');
    setSuccessMessage('');
    audioChunksRef.current = [];
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioContext({ sampleRate: 16000 }); // Vosk loves 16kHz
      audioContextRef.current = audioCtx;
      
      const source = audioCtx.createMediaStreamSource(stream);
      
      // Use ScriptProcessorNode (backward compatible, zero complex worklet configurations needed)
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      
      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        // Copy floats buffer
        audioChunksRef.current.push(new Float32Array(inputData));
      };
      
      source.connect(processor);
      processor.connect(audioCtx.destination);
      
      setIsRecording(true);
    } catch (err) {
      setErrorMessage("Microphone access denied or error starting recording.");
      console.error(err);
    }
  };

  const stopRecording = () => {
    if (!isRecording) return;
    setIsRecording(false);
    
    try {
      // Disconnect audio routing
      if (processorRef.current) processorRef.current.disconnect();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    } catch (err) {
      console.error(err);
    }
    
    // Process recorded float chunks
    const chunks = audioChunksRef.current;
    if (chunks.length === 0) {
      setErrorMessage("No audio recorded.");
      return;
    }
    
    // Flatten floats
    let totalLength = 0;
    chunks.forEach(c => totalLength += c.length);
    const flatSamples = new Float32Array(totalLength);
    let offset = 0;
    chunks.forEach(c => {
      flatSamples.set(c, offset);
      offset += c.length;
    });
    
    // Encode to 16kHz Mono WAV Blob
    const wavBlob = encodeWAV(flatSamples, 16000);
    uploadVoice(wavBlob);
  };

  const uploadVoice = async (blob) => {
    setLoading(true);
    setErrorMessage('');
    setSuccessMessage('');
    
    const formData = new FormData();
    formData.append('file', blob, 'recording.wav');
    
    try {
      const res = await fetch(`${API_BASE}/api/voice/capture`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setSuccessMessage(`Transcribed: "${data.transcript}" → Captured ${data.item.intent}`);
        fetchTasks();
        fetchDailySummary();
        fetchWeeklyAnalytics();
        fetchStatus();
      } else {
        setErrorMessage(data.detail || "Voice capture failed.");
      }
    } catch (err) {
      setErrorMessage("Could not connect to the local server or voice processing failed.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleTask = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/tasks/${id}/toggle`, { method: 'POST' });
      if (res.ok) {
        fetchTasks();
        fetchDailySummary();
        fetchWeeklyAnalytics();
      }
    } catch (e) {
      console.error("Error toggling task", e);
    }
  };

  const deleteTask = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/tasks/${id}`, { method: 'DELETE' });
      if (res.ok) {
        fetchTasks();
        fetchDailySummary();
        fetchWeeklyAnalytics();
      }
    } catch (e) {
      console.error("Error deleting task", e);
    }
  };

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/tasks?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      setSearchResults(data);
    } catch (e) {
      console.error("Error running search", e);
    } finally {
      setLoading(false);
    }
  };

  // Helper date formatter
  const formatDate = (isoStr) => {
    if (!isoStr) return "";
    const d = new Date(isoStr);
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const formatSeconds = (sec) => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  // Filter tasks logic
  const filteredTasks = tasks.filter(task => {
    if (filterStatus === 'pending' && task.status !== 'pending') return false;
    if (filterStatus === 'completed' && task.status !== 'completed') return false;
    if (filterCategory !== 'all' && task.category !== filterCategory) return false;
    if (filterPriority !== 'all' && task.priority !== filterPriority) return false;
    return true;
  });  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#02040a] text-slate-100 font-sans flex items-center justify-center relative overflow-hidden">
        {/* Glowing background circles */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/5 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/5 rounded-full blur-[120px] pointer-events-none"></div>

        {/* Login Card */}
        <div className="w-[440px] glass-panel rounded-3xl p-10 border border-slate-800/80 shadow-2xl relative z-10 space-y-8">
          <div className="flex flex-col items-center text-center space-y-3">
            <img src="/sysai_logo.png" alt="SysAi Logo" className="h-16 w-16 object-cover rounded-2xl shadow-xl shadow-blue-500/10 border border-slate-800" />
            <div>
              <h2 className="text-2xl font-extrabold text-white">
                {authMode === 'login' ? 'Welcome to SysAi' : 'Create SysAi Account'}
              </h2>
              <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-semibold">Offline AI Productivity</p>
            </div>
          </div>

          <form onSubmit={(e) => {
            e.preventDefault();
            if (!emailInput || !passwordInput || (authMode === 'signup' && !nameInput)) {
              setErrorMessage("Please fill out all required fields.");
              return;
            }
            // Mock authentication
            localStorage.setItem('sysai_authenticated', 'true');
            if (authMode === 'signup') {
              const newProfile = { name: nameInput, role: 'Productivity Architect', theme: 'dark' };
              localStorage.setItem('sysai_profile', JSON.stringify(newProfile));
              setUserProfile(newProfile);
            }
            setIsAuthenticated(true);
            setSuccessMessage("Logged in successfully!");
            setErrorMessage("");
          }} className="space-y-5">
            {errorMessage && (
              <div className="p-3 bg-red-950/30 border border-red-900/50 text-red-200 rounded-xl text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
                <span>{errorMessage}</span>
              </div>
            )}

            {authMode === 'signup' && (
              <div className="space-y-1.5">
                <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Display Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Tony Stark"
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  className="w-full bg-[#0a1120] border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all"
                />
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Email Address</label>
              <input
                type="email"
                required
                placeholder="you@example.com"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                className="w-full bg-[#0a1120] border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Password</label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                className="w-full bg-[#0a1120] border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-sm transition-all duration-300 shadow-lg shadow-blue-500/10 active:scale-[0.98]"
            >
              {authMode === 'login' ? 'Sign In to Workspace' : 'Create Workspace'}
            </button>
          </form>

          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => {
                setAuthMode(authMode === 'login' ? 'signup' : 'login');
                setErrorMessage('');
              }}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium transition"
            >
              {authMode === 'login' ? "Don't have an account? Sign Up" : 'Already have an account? Sign In'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#02040a] text-slate-100 font-sans">
      {/* SIDEBAR */}
      <aside className="w-72 bg-[#05070f] border-r border-slate-900 flex flex-col justify-between shrink-0">
        <div>
          {/* Logo */}
          <div className="p-8 border-b border-slate-900">
            <div className="flex items-center gap-3.5">
              <img src="/sysai_logo.png" alt="SysAi Logo" className="h-11 w-11 object-cover rounded-xl shadow-lg shadow-blue-500/10 border border-slate-800" />
              <div>
                <h1 className="text-xl font-bold text-white leading-none">SysAi</h1>
                <span className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">productivity</span>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-6 space-y-2">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: Home },
              { id: 'tasks', label: 'Tasks Board', icon: CheckSquare },
              { id: 'notes', label: 'Notes Wall', icon: FileText },
              { id: 'search', label: 'Smart Search', icon: Search },
              { id: 'analytics', label: 'Analytics Hub', icon: BarChart2 },
              { id: 'settings', label: 'System Settings', icon: Settings }
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive 
                      ? 'bg-blue-600/15 text-blue-400 border-l-4 border-blue-500 shadow-md shadow-blue-500/5' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-900/50 border-l-4 border-transparent'
                  }`}
                >
                  <Icon className={`h-5 w-5 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User Session and Database Status Footer in Sidebar */}
        <div className="p-6 border-t border-slate-900 space-y-4">
          <div className="flex items-center justify-between gap-3 px-1.5">
            <div className="flex items-center gap-3 min-w-0">
              <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-xs text-white uppercase shadow-md shadow-blue-500/10 shrink-0">
                {userProfile.name ? userProfile.name[0] : 'U'}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-200 truncate">{userProfile.name || 'Demo User'}</p>
                <p className="text-[10px] text-slate-400 truncate">{userProfile.role || 'Productivity Architect'}</p>
              </div>
            </div>
            
            <button
              type="button"
              onClick={() => {
                localStorage.removeItem('sysai_authenticated');
                setIsAuthenticated(false);
              }}
              className="p-2 bg-[#090e1a] hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-900/50 rounded-xl transition"
              title="Sign Out Workspace"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>

          <div className="bg-[#070b13] rounded-xl p-4 border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Database className="h-4 w-4 text-blue-500" />
              <span>SYSTEM INFRASTRUCTURE</span>
            </div>
            <div className="space-y-1.5 text-[11px] text-slate-400">
              <div className="flex justify-between items-center">
                <span>Database:</span>
                <span className="font-bold text-slate-200">{backendStatus?.database || "Offline"}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>NLP Embeddings:</span>
                <span className={`font-bold ${backendStatus?.semantic_embeddings_loaded ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {backendStatus?.semantic_embeddings_loaded ? 'Ready (Local)' : 'Pending'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>ML Classifiers:</span>
                <span className={`font-bold ${backendStatus?.ml_models_loaded ? 'text-emerald-400' : 'text-amber-500'}`}>
                  {backendStatus?.ml_models_loaded ? 'Optimized' : 'Fallback'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        {/* Header */}
        <header className="h-20 bg-[#05070f] border-b border-slate-900 flex items-center justify-between px-10 shrink-0">
          <div className="flex items-center gap-2.5">
            <h2 className="text-lg font-semibold text-slate-200 capitalize">{activeTab} View</h2>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-300">
            <div className="bg-[#0c1222] px-3.5 py-2 rounded-lg border border-slate-800 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Local Dev Node</span>
            </div>
            <div className="text-slate-400">
              {new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
            </div>
          </div>
        </header>

        {/* Content body */}
        <div className="flex-grow p-10 overflow-y-auto">
          {/* Notifications */}
          {errorMessage && (
            <div className="mb-6 p-4 bg-[#0a1120] border border-red-900/40 text-red-200 rounded-xl flex items-center gap-3">
              <AlertCircle className="h-5 w-5 shrink-0 text-red-400" />
              <p className="text-sm">{errorMessage}</p>
            </div>
          )}
          {successMessage && (
            <div className="mb-6 p-4 bg-[#0a1120] border border-emerald-900/40 text-emerald-200 rounded-xl flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-400" />
              <p className="text-sm">{successMessage}</p>
            </div>
          )}

          {/* TAB CONTENTS */}
          {activeTab === 'dashboard' && (
            <div className="space-y-8">
              {/* Top Banner Row */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Algorithmic Daily Summary */}
                <div className="lg:col-span-2 glass-panel rounded-2xl p-6 border border-slate-800/80 shadow-premium relative overflow-hidden flex flex-col justify-between">
                  <div className="absolute top-0 right-0 p-8 opacity-5">
                    <Sparkles className="h-32 w-32 text-blue-500" />
                  </div>
                  <div className="space-y-4 relative">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5 text-blue-500" />
                      <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">DAILY COGNITIVE OVERVIEW</h3>
                    </div>
                    <div className="text-slate-200 leading-relaxed text-sm pr-6">
                      {dailySummary?.summary ? (
                        <p dangerouslySetInnerHTML={{ __html: dailySummary.summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}></p>
                      ) : (
                        <p>Generate summary text by capturing new tasks or todo items using speech or keyboard inputs below.</p>
                      )}
                    </div>
                  </div>
                  <div className="mt-6 pt-4 border-t border-slate-900 flex justify-between items-center text-xs text-slate-400">
                    <span>Generated Algorithmatically (Offline models)</span>
                    <span className="font-semibold text-blue-400">Score: {dailySummary?.metrics?.productivity_score || 0}%</span>
                  </div>
                </div>

                {/* Score KPI Circle */}
                <div className="glass-panel rounded-2xl p-6 border border-slate-800/80 flex flex-col justify-between items-center text-center">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">PRODUCTIVITY RATING</h3>
                  <div className="relative flex items-center justify-center h-32 w-32">
                    {/* Ring background */}
                    <div className="absolute h-full w-full rounded-full border-[8px] border-slate-800"></div>
                    {/* Dynamic colored text */}
                    <div className="absolute flex flex-col items-center justify-center">
                      <span className="text-4xl font-extrabold text-blue-400">{dailySummary?.metrics?.grade || "N/A"}</span>
                      <span className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">Grade</span>
                    </div>
                  </div>
                  <div className="mt-4 space-y-1">
                    <span className="text-xs text-slate-300">Focus Sector: <strong className="text-blue-400">{dailySummary?.metrics?.focus_category || "None"}</strong></span>
                    <div className="text-[10px] text-slate-400">Completion rate of today's targets is {dailySummary?.metrics?.completion_rate || 0}%</div>
                  </div>
                </div>
              </div>

              {/* Natural Language Capture Panel */}
              <div className="glass-panel rounded-2xl border border-slate-800/80 p-8 shadow-premium">
                <h3 className="text-base font-bold text-white mb-6 flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-blue-500" />
                  Natural Language Task Capture
                </h3>
                <form onSubmit={handleCapture} className="space-y-4">
                  <div className="relative">
                    <input
                      type="text"
                      value={taskInput}
                      onChange={(e) => setTaskInput(e.target.value)}
                      placeholder="e.g. Remember to review math physics chapter 2 tomorrow at 9 AM"
                      className="w-full bg-[#0a1120] border border-slate-850 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 rounded-xl px-5 py-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none pr-32 transition-all duration-300"
                    />
                    
                    {/* Action buttons inside input */}
                    <div className="absolute right-2 top-2.5 flex items-center gap-2">
                      {/* Audio Button */}
                      <button
                        type="button"
                        onClick={isRecording ? stopRecording : startRecording}
                        className={`p-2 rounded-lg transition-all duration-200 ${
                          isRecording 
                            ? 'bg-rose-600 text-white animate-pulse' 
                            : 'bg-[#090e1a] border border-slate-800 hover:border-blue-800 text-slate-300 hover:text-white'
                        }`}
                        title={isRecording ? "Stop recording and transcribe" : "Record voice capture (WAV)"}
                      >
                        {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
                      </button>

                      {/* Submit Text */}
                      <button
                        type="submit"
                        disabled={loading || !taskInput.trim()}
                        className="bg-blue-600 hover:bg-blue-700 disabled:bg-[#070b13] disabled:text-slate-500 text-white px-4 py-2 rounded-lg font-medium text-xs flex items-center gap-1.5 transition-all duration-200 shadow-lg shadow-blue-500/10"
                      >
                        {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <ArrowRight className="h-3.5 w-3.5" />}
                        <span>Capture</span>
                      </button>
                    </div>
                  </div>

                  {/* Voice recording indicators */}
                  {isRecording && (
                    <div className="flex items-center gap-3 text-rose-400 text-xs px-2 animate-pulse">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-600"></span>
                      <span>Recording: {formatSeconds(recordingSeconds)} - speak now, then click the mic button to process.</span>
                    </div>
                  )}

                  {/* Quick Helpers */}
                  <div className="flex flex-wrap gap-2 pt-2 items-center">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Example commands:</span>
                    {[
                      { text: "Draft weekly sales report today at 5pm", label: "Work Task" },
                      { text: "Buy green tea and spinach from grocery store", label: "Shopping" },
                      { text: "Call doctor checkup appointment next Monday", label: "Health Reminder" },
                      { text: "Pay rent bill of $1200 on June 30th", label: "Finance" }
                    ].map((example, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setTaskInput(example.text)}
                        className="text-[10px] bg-[#0c1222] hover:bg-[#111a33] text-slate-300 hover:text-white px-3 py-1.5 rounded-lg border border-slate-800 hover:border-blue-900/40 transition-colors"
                      >
                        {example.label}
                      </button>
                    ))}
                  </div>
                </form>
              </div>

              {/* Recent Tasks List */}
              <div className="glass-panel rounded-2xl border border-slate-800/80 p-8 shadow-premium">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Clock className="h-5 w-5 text-blue-500" />
                    Recently Captured Objects
                  </h3>
                  <button onClick={() => setActiveTab('tasks')} className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1">
                    <span>View all board items</span>
                    <ArrowRight className="h-3 w-3" />
                  </button>
                </div>

                <div className="space-y-3.5">
                  {tasks.slice(0, 5).map((item) => (
                    <div 
                      key={item.id}
                      className="p-4 bg-[#070b13] border border-slate-800 rounded-xl hover:border-slate-700/80 transition-all flex items-center justify-between gap-4"
                    >
                      <div className="flex items-center gap-3.5 min-w-0">
                        <button 
                          onClick={() => toggleTask(item.id)}
                          className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 transition-colors ${
                            item.status === 'completed'
                              ? 'bg-blue-600 border-blue-500 text-white'
                              : 'border-slate-600 hover:border-blue-500'
                          }`}
                        >
                          {item.status === 'completed' && <Check className="h-3 w-3" />}
                        </button>
                        
                        <div className="min-w-0">
                          <p className={`text-sm font-medium ${item.status === 'completed' ? 'line-through text-slate-500' : 'text-slate-200'}`}>{item.text}</p>
                          <div className="flex flex-wrap items-center gap-2.5 mt-1 text-[11px]">
                            {/* Intent Badge */}
                            <span className="text-slate-400 uppercase tracking-widest font-bold text-[9px]">{item.intent}</span>
                            
                            {/* Category Badge */}
                            {CATEGORY_COLORS[item.category] && (
                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${CATEGORY_COLORS[item.category].bg} ${CATEGORY_COLORS[item.category].text} ${CATEGORY_COLORS[item.category].border}`}>
                                {item.category}
                              </span>
                            )}
                            
                            {/* Priority Badge */}
                            {PRIORITY_COLORS[item.priority] && (
                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${PRIORITY_COLORS[item.priority].bg} ${PRIORITY_COLORS[item.priority].text} ${PRIORITY_COLORS[item.priority].border}`}>
                                {item.priority}
                              </span>
                            )}

                            {/* Due Date Indicator */}
                            {item.due_date && (
                              <span className="text-slate-300 flex items-center gap-1 ml-1.5">
                                <CalendarDays className="h-3 w-3 text-blue-500" />
                                {formatDate(item.due_date)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <button 
                        onClick={() => deleteTask(item.id)}
                        className="p-1.5 rounded bg-[#090e1a] border border-slate-800 hover:border-rose-900/50 text-slate-400 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}

                  {tasks.length === 0 && (
                    <div className="text-center py-10 text-slate-400 text-sm">
                      No productivity items recorded. Use the capture bar above.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tasks' && (
            <div className="space-y-8">
              {/* Filter controls */}
              <div className="glass-panel rounded-2xl border border-slate-800/80 p-6 flex flex-wrap gap-6 items-center">
                <div className="flex items-center gap-2 text-sm text-slate-300 font-bold uppercase tracking-wider">
                  <Filter className="h-4 w-4 text-blue-500" />
                  <span>Filters</span>
                </div>

                {/* Status */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Status</label>
                  <select 
                    value={filterStatus} 
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="bg-[#0a1120] border border-slate-800 text-slate-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-blue-500"
                  >
                    <option value="all">All Items</option>
                    <option value="pending">Pending</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>

                {/* Category */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Category</label>
                  <select 
                    value={filterCategory} 
                    onChange={(e) => setFilterCategory(e.target.value)}
                    className="bg-[#0a1120] border border-slate-800 text-slate-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-blue-500"
                  >
                    <option value="all">All Categories</option>
                    {Object.keys(CATEGORY_COLORS).map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>

                {/* Priority */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Priority</label>
                  <select 
                    value={filterPriority} 
                    onChange={(e) => setFilterPriority(e.target.value)}
                    className="bg-[#0a1120] border border-slate-800 text-slate-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-blue-500"
                  >
                    <option value="all">All Priorities</option>
                    {Object.keys(PRIORITY_COLORS).map(prio => (
                      <option key={prio} value={prio}>{prio}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Tasks Board List */}
              <div className="glass-panel rounded-2xl border border-slate-800/80 p-8 shadow-premium space-y-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-base font-bold text-white">
                    Task Board List ({filteredTasks.length} items shown)
                  </h3>
                </div>

                <div className="space-y-3.5">
                  {filteredTasks.map((item) => (
                    <div 
                      key={item.id}
                      className="p-4 bg-[#070b13] border border-slate-800 rounded-xl hover:border-slate-700/80 transition-all flex items-center justify-between gap-4"
                    >
                      <div className="flex items-center gap-3.5 min-w-0">
                        <button 
                          onClick={() => toggleTask(item.id)}
                          className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 transition-colors ${
                            item.status === 'completed'
                              ? 'bg-blue-600 border-blue-500 text-white'
                              : 'border-slate-600 hover:border-blue-500'
                          }`}
                        >
                          {item.status === 'completed' && <Check className="h-3 w-3" />}
                        </button>
                        
                        <div className="min-w-0">
                          <p className={`text-sm font-medium ${item.status === 'completed' ? 'line-through text-slate-500' : 'text-slate-200'}`}>{item.text}</p>
                          
                          <div className="flex flex-wrap items-center gap-2.5 mt-2 text-[10px]">
                            {/* Intent Badge */}
                            <span className="text-slate-400 uppercase tracking-widest font-bold text-[9px]">{item.intent}</span>
                            
                            {/* Category Badge */}
                            {CATEGORY_COLORS[item.category] && (
                              <span className={`px-2 py-0.5 rounded-full font-semibold border ${CATEGORY_COLORS[item.category].bg} ${CATEGORY_COLORS[item.category].text} ${CATEGORY_COLORS[item.category].border}`}>
                                {item.category}
                              </span>
                            )}
                            
                            {/* Priority Badge */}
                            {PRIORITY_COLORS[item.priority] && (
                              <span className={`px-2 py-0.5 rounded-full font-semibold border ${PRIORITY_COLORS[item.priority].bg} ${PRIORITY_COLORS[item.priority].text} ${PRIORITY_COLORS[item.priority].border}`}>
                                {item.priority}
                              </span>
                            )}

                            {/* Date Badge */}
                            {item.due_date && (
                              <span className="text-slate-300 flex items-center gap-1.5 ml-1">
                                <CalendarDays className="h-3 w-3 text-blue-500" />
                                {formatDate(item.due_date)}
                              </span>
                            )}

                            {/* Tags list */}
                            {item.tags?.length > 0 && (
                              <div className="flex items-center gap-1 ml-1 text-slate-400">
                                <Tag className="h-3 w-3" />
                                <span className="text-[10px]">{item.tags.join(', ')}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <button 
                        onClick={() => deleteTask(item.id)}
                        className="p-1.5 rounded bg-[#090e1a] border border-slate-800 hover:border-rose-900/50 text-slate-400 hover:text-rose-400 transition-colors animate-fade"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}

                  {filteredTasks.length === 0 && (
                    <div className="text-center py-16 text-slate-400 text-sm">
                      No matching tasks found. Clear your filters or capture some tasks.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notes' && (
            <div className="space-y-8 animate-fade-in">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-bold text-white">Notes Wall</h3>
                  <p className="text-xs text-slate-400">View notes generated by classifiers or capture new thoughts directly.</p>
                </div>
              </div>

              {/* Grid Layout of Notes */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {tasks.filter(item => item.intent === 'Note').map(note => (
                  <div 
                    key={note.id}
                    className="glass-panel rounded-2xl p-6 border border-slate-800 hover:border-slate-700/80 flex flex-col justify-between h-56 relative group shadow-lg shadow-blue-950/20"
                  >
                    <div className="space-y-3 overflow-hidden">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">NOTES STORAGE</span>
                        <button 
                          onClick={() => deleteTask(note.id)}
                          className="opacity-0 group-hover:opacity-100 p-1.5 bg-[#090e1a] hover:bg-rose-950/40 border border-slate-800 hover:border-rose-900/50 rounded transition-all text-slate-400 hover:text-rose-400"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <p className="text-sm text-slate-200 leading-relaxed font-medium line-clamp-4">{note.text}</p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-900 flex justify-between items-center text-[10px] text-slate-400">
                      {CATEGORY_COLORS[note.category] ? (
                        <span className={`px-2 py-0.5 rounded-full font-semibold border ${CATEGORY_COLORS[note.category].bg} ${CATEGORY_COLORS[note.category].text} ${CATEGORY_COLORS[note.category].border}`}>
                          {note.category}
                        </span>
                      ) : <span></span>}
                      <span>{new Date(note.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}

                {tasks.filter(item => item.intent === 'Note').length === 0 && (
                  <div className="col-span-full text-center py-20 text-slate-400 text-sm">
                    No notes recorded yet. Say "Write a note about..." or add text containing concept details in the dashboard.
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'search' && (
            <div className="space-y-8">
              {/* Search input card */}
              <div className="glass-panel rounded-2xl border border-slate-800/80 p-8 shadow-premium">
                <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                  <Search className="h-5 w-5 text-blue-500" />
                  Hybrid Semantic Search
                </h3>
                <p className="text-xs text-slate-400 mb-6">Runs a sentence-transformers search to match query meanings, combined with keyword matching statistics.</p>
                <form onSubmit={handleSearch} className="flex gap-4">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by keywords or semantic meanings like: study tasks for exams or billing transactions..."
                    className="flex-grow bg-[#0a1120] border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 rounded-xl px-5 py-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all"
                  />
                  <button
                    type="submit"
                    disabled={loading || !searchQuery.trim()}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-[#070b13] disabled:text-slate-500 text-white px-6 rounded-xl font-medium text-sm flex items-center gap-2 transition"
                  >
                    {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                    <span>Search</span>
                  </button>
                </form>
              </div>

              {/* Search Results */}
              <div className="space-y-4">
                <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider px-2">Matches</h4>
                <div className="space-y-3.5">
                  {searchResults.map((item) => (
                    <div 
                      key={item.id}
                      className="p-4 bg-[#070b13] border border-slate-800 rounded-xl hover:border-slate-700/80 transition-all flex items-center justify-between gap-4"
                    >
                      <div className="flex items-center gap-3.5 min-w-0">
                        {/* Similarity indicator circle */}
                        <div className="h-11 w-11 rounded-lg bg-[#090e1a] border border-slate-800 flex flex-col items-center justify-center shrink-0 text-center">
                          <span className="text-[11px] font-extrabold text-blue-400">{Math.round(item.score * 100)}%</span>
                          <span className="text-[7px] text-slate-400 font-bold uppercase tracking-wider">Match</span>
                        </div>
                        
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-200">{item.text}</p>
                          <div className="flex flex-wrap items-center gap-2 mt-1.5 text-[10px]">
                            <span className="text-slate-400 uppercase tracking-widest font-bold text-[8px]">{item.intent}</span>
                            
                            {CATEGORY_COLORS[item.category] && (
                              <span className={`px-2 py-0.5 rounded-full font-semibold border ${CATEGORY_COLORS[item.category].bg} ${CATEGORY_COLORS[item.category].text} ${CATEGORY_COLORS[item.category].border}`}>
                                {item.category}
                              </span>
                            )}
                            
                            {PRIORITY_COLORS[item.priority] && (
                              <span className={`px-2 py-0.5 rounded-full font-semibold border ${PRIORITY_COLORS[item.priority].bg} ${PRIORITY_COLORS[item.priority].text} ${PRIORITY_COLORS[item.priority].border}`}>
                                {item.priority}
                              </span>
                            )}

                            {item.due_date && (
                              <span className="text-slate-300 flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {formatDate(item.due_date)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Details button */}
                      <span className="text-xs text-blue-400 bg-blue-950/20 px-3 py-1.5 rounded-lg border border-blue-900/30">
                        {item.status}
                      </span>
                    </div>
                  ))}

                  {searchResults.length === 0 && (
                    <div className="text-center py-20 text-slate-400 text-sm">
                      {searchQuery ? "No matches found." : "Run a search using the search bar above."}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-8">
              {/* Analytics Header Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { label: "WEEKLY PRODUCTIVITY SCORE", value: `${weeklyAnalytics?.score || 0}%`, sub: "Weighted by priority", icon: Sparkles, color: "text-blue-400" },
                  { label: "TOTAL RECORDED OBJECTS", value: weeklyAnalytics?.total_tasks || 0, sub: "Last 7 days", icon: CheckSquare, color: "text-blue-400" },
                  { label: "COMPLETED TARGETS", value: weeklyAnalytics?.completed_tasks || 0, sub: "Tasks finished", icon: CheckCircle2, color: "text-emerald-400" },
                  { label: "COMPLETION RATE", value: `${weeklyAnalytics?.completion_rate || 0}%`, sub: "Efficiency rating", icon: Clock, color: "text-amber-400" }
                ].map((stat, idx) => {
                  const Icon = stat.icon;
                  return (
                    <div key={idx} className="glass-panel rounded-2xl p-6 border border-slate-800 flex justify-between items-center shadow-lg">
                      <div className="space-y-1.5">
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">{stat.label}</span>
                        <span className="text-2xl font-bold text-white block">{stat.value}</span>
                        <span className="text-[11px] text-slate-450 block">{stat.sub}</span>
                      </div>
                      <div className="p-3 bg-[#090e1a] border border-slate-850 rounded-xl">
                        <Icon className={`h-6 w-6 ${stat.color}`} />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Charts grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* 1. Daily Trends Area Chart */}
                <div className="glass-panel rounded-2xl border border-slate-800 p-6 flex flex-col justify-between shadow-premium h-96">
                  <div className="mb-4">
                    <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Productivity Volume Trends</h4>
                    <span className="text-xs text-slate-400">Compare tasks created vs tasks completed over the days of the week</span>
                  </div>
                  <div className="flex-1 min-h-0 w-full">
                    {weeklyAnalytics?.daily_trends ? (
                      <ResponsiveContainer width="100%" height="90%">
                        <AreaChart data={weeklyAnalytics.daily_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <defs>
                            <linearGradient id="colorCreated" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                            </linearGradient>
                            <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#a855f7" stopOpacity={0.2}/>
                              <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="day" stroke="#64748b" fontSize={11} />
                          <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                          <Tooltip contentStyle={{ backgroundColor: '#090d1a', borderColor: '#1e293b', borderRadius: '8px' }} />
                          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                          <Area type="monotone" dataKey="Created" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorCreated)" />
                          <Area type="monotone" dataKey="Completed" stroke="#a855f7" strokeWidth={2} fillOpacity={1} fill="url(#colorCompleted)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-slate-400 text-xs">No trend data available</div>
                    )}
                  </div>
                </div>

                {/* 2. Category Distribution Pie Chart */}
                <div className="glass-panel rounded-2xl border border-slate-800 p-6 flex flex-col justify-between shadow-premium h-96">
                  <div className="mb-4">
                    <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Sector Focus (Category Split)</h4>
                    <span className="text-xs text-slate-400">Distribution of all tasks captured in the last 7 days</span>
                  </div>
                  <div className="flex-grow flex items-center justify-center relative min-h-0 w-full">
                    {weeklyAnalytics?.category_distribution?.length > 0 ? (
                      <ResponsiveContainer width="100%" height="90%">
                        <PieChart>
                          <Pie
                            data={weeklyAnalytics.category_distribution}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={90}
                            paddingAngle={5}
                            dataKey="value"
                            label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                            labelLine={false}
                          >
                            {weeklyAnalytics.category_distribution.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip contentStyle={{ backgroundColor: '#090d1a', borderColor: '#1e293b', borderRadius: '8px' }} />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-slate-400 text-xs">No category data recorded</div>
                    )}
                  </div>
                </div>

                {/* 3. Priority Split Bar Chart */}
                <div className="glass-panel rounded-2xl border border-slate-800 p-6 flex flex-col justify-between shadow-premium h-96 lg:col-span-2">
                  <div className="mb-4">
                    <h4 className="text-sm font-bold text-slate-350 uppercase tracking-wider">Priority Task Allocation</h4>
                    <span className="text-xs text-slate-400">Number of tasks categorized by importance levels</span>
                  </div>
                  <div className="flex-1 min-h-0 w-full">
                    {weeklyAnalytics?.priority_distribution ? (
                      <ResponsiveContainer width="100%" height="90%">
                        <BarChart data={weeklyAnalytics.priority_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                          <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                          <Tooltip contentStyle={{ backgroundColor: '#090d1a', borderColor: '#1e293b', borderRadius: '8px' }} />
                          <Bar dataKey="value" fill="#3b82f6" radius={[6, 6, 0, 0]} maxBarSize={50}>
                            {weeklyAnalytics.priority_distribution.map((entry, index) => {
                              const prioColors = ["#f43f5e", "#fbbf24", "#3b82f6"]; // High, Medium, Low colors
                              return <Cell key={`cell-${index}`} fill={prioColors[index % prioColors.length]} />;
                            })}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-slate-400 text-xs">No priority data recorded</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-8 max-w-4xl">
              <div className="glass-panel rounded-2xl border border-slate-800/80 p-8 shadow-premium space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-white">User Profile Configuration</h3>
                  <p className="text-xs text-slate-400">Customize how you appear in your local workspace.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Display Name</label>
                    <input
                      type="text"
                      value={userProfile.name}
                      onChange={(e) => {
                        const updated = { ...userProfile, name: e.target.value };
                        setUserProfile(updated);
                        localStorage.setItem('sysai_profile', JSON.stringify(updated));
                      }}
                      className="w-full bg-[#0a1120] border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none transition-all"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Role Title</label>
                    <input
                      type="text"
                      value={userProfile.role}
                      onChange={(e) => {
                        const updated = { ...userProfile, role: e.target.value };
                        setUserProfile(updated);
                        localStorage.setItem('sysai_profile', JSON.stringify(updated));
                      }}
                      className="w-full bg-[#0a1120] border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none transition-all"
                    />
                  </div>
                </div>
              </div>

              <div className="glass-panel rounded-2xl border border-slate-800/80 p-8 shadow-premium space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-white">System Infrastructure Settings</h3>
                  <p className="text-xs text-slate-400">Configure offline diagnostics and data backends.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Active Database Type</label>
                    <select
                      value={dbTypeSetting}
                      onChange={(e) => setDbTypeSetting(e.target.value)}
                      className="w-full bg-[#0a1120] border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none transition-all"
                    >
                      <option value="SQLite">SQLite (productivity.db)</option>
                      <option value="MongoDB">MongoDB (Local Host)</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Offline Voice Recognition Sensitivity</label>
                    <select
                      value={voiceThreshold}
                      onChange={(e) => setVoiceThreshold(e.target.value)}
                      className="w-full bg-[#0a1120] border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none transition-all"
                    >
                      <option value="0.3">High Sensitivity (0.3)</option>
                      <option value="0.5">Balanced (0.5)</option>
                      <option value="0.8">Low Noise Filter (0.8)</option>
                    </select>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-900 flex justify-between items-center text-xs text-slate-400">
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-blue-500" />
                    <span>Diagnostics: Backend status is {backendStatus?.status || "disconnected"}</span>
                  </div>
                  <button 
                    type="button"
                    onClick={() => {
                      fetchStatus();
                      fetchTasks();
                    }}
                    className="flex items-center gap-1.5 text-blue-400 hover:text-blue-300 font-medium transition"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                    <span>Run Server Diagnostics</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
