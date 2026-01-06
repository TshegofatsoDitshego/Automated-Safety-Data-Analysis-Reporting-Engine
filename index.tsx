
import React, { useState, useEffect, createContext, useContext, useMemo, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Shield, 
  LayoutDashboard, 
  Activity, 
  FileText, 
  Settings, 
  User, 
  LogOut, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ChevronRight, 
  ChevronLeft,
  Plus, 
  Download, 
  Menu, 
  X,
  Eye,
  EyeOff,
  Search,
  Zap,
  HardHat,
  Bell,
  Trash2,
  ExternalLink,
  Cpu,
  Lock,
  Globe,
  Smartphone,
  Info,
  Key,
  Users,
  UserPlus,
  CreditCard,
  PanelLeftClose,
  PanelLeftOpen,
  TestTube,
  Play,
  CheckCircle,
  XCircle,
  FileSearch,
  Printer
} from 'lucide-react';
import { GoogleGenAI, Type } from "@google/genai";

// Import logic and tests from separate modules
import { validatePassword, getStrength, getReadingStatus } from './logic';
import { runTestSuite, TestResult } from './tests/suite';

// --- CONFIG & UTILS ---
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

// --- TYPES ---
type UserData = {
  id: string;
  email: string;
  fullName: string;
  createdAt: string;
  lastLogin: string;
  preferences: {
    notifications: boolean;
    refreshInterval: number;
    units: 'metric' | 'imperial';
    timezone: string;
  }
};

type Sensor = {
  id: string;
  sensor_id: string;
  type: 'CO' | 'H2S' | 'O2' | 'LEL';
  location: string;
  status: 'active' | 'maintenance' | 'offline';
  lastCalibration: string;
  nextCalibration: string;
};

type Reading = {
  id: number;
  sensor_id: string;
  timestamp: string;
  gas_type: string;
  value: number;
  unit: string;
  status: 'normal' | 'warning' | 'critical';
};

type Alert = {
  id: number;
  sensor_id: string;
  type: string;
  severity: 'low' | 'medium' | 'high';
  value: number;
  timestamp: string;
  acknowledged: boolean;
};

// --- AUTH CONTEXT ---
const AuthContext = createContext<{
  user: UserData | null;
  login: (email: string, pass: string) => Promise<void>;
  register: (name: string, email: string, pass: string) => Promise<void>;
  logout: () => void;
  updateProfile: (data: Partial<UserData>) => void;
} | null>(null);

const AuthProvider = ({ children }: { children?: React.ReactNode }) => {
  const [user, setUser] = useState<UserData | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem('safetypulse_user');
    if (saved) setUser(JSON.parse(saved));
  }, []);

  const login = async (email: string, pass: string) => {
    const users = JSON.parse(localStorage.getItem('safetypulse_users_db') || '[]');
    const found = users.find((u: any) => u.email === email);
    
    if (found) {
      const sessionUser = { ...found, lastLogin: new Date().toISOString() };
      setUser(sessionUser);
      localStorage.setItem('safetypulse_user', JSON.stringify(sessionUser));
    } else {
      throw new Error("Invalid credentials");
    }
  };

  const register = async (name: string, email: string, pass: string) => {
    const users = JSON.parse(localStorage.getItem('safetypulse_users_db') || '[]');
    if (users.some((u: any) => u.email === email)) throw new Error("Email exists");

    const newUser: UserData = {
      id: Math.random().toString(36).substr(2, 9),
      email,
      fullName: name,
      createdAt: new Date().toISOString(),
      lastLogin: new Date().toISOString(),
      preferences: { 
        notifications: true, 
        refreshInterval: 30, 
        units: 'metric',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      }
    };

    users.push({ ...newUser, pass });
    localStorage.setItem('safetypulse_users_db', JSON.stringify(users));
    setUser(newUser);
    localStorage.setItem('safetypulse_user', JSON.stringify(newUser));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('safetypulse_user');
  };

  const updateProfile = (data: Partial<UserData>) => {
    if (!user) return;
    const updated = { 
      ...user, 
      ...data, 
      preferences: { ...user.preferences, ...(data.preferences || {}) } 
    };
    setUser(updated);
    localStorage.setItem('safetypulse_user', JSON.stringify(updated));
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

// --- UI COMPONENTS ---

const Card = ({ children, title, className = "", headerAction }: any) => (
  <div className={`bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden ${className}`}>
    {title && (
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
        <div className="font-semibold text-slate-800">{title}</div>
        {headerAction}
      </div>
    )}
    <div className="p-6">{children}</div>
  </div>
);

const Button = ({ children, onClick, variant = 'primary', className = "", disabled = false, type = 'button' }: any) => {
  const base = "px-4 py-2 rounded-lg font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50";
  const variants: any = {
    primary: "bg-amber-500 hover:bg-amber-600 text-white shadow-sm",
    secondary: "bg-slate-100 hover:bg-slate-200 text-slate-700",
    danger: "bg-red-500 hover:bg-red-600 text-white",
    outline: "border-2 border-slate-200 hover:border-slate-300 text-slate-600"
  };
  return <button type={type} disabled={disabled} onClick={onClick} className={`${base} ${variants[variant]} ${className}`}>{children}</button>;
};

const Input = ({ label, type = "text", value, onChange, placeholder, icon: Icon, error, readOnly = false }: any) => (
  <div className="mb-4">
    {label && <label className="block text-sm font-medium text-slate-700 mb-1.5">{label}</label>}
    <div className="relative">
      {Icon && <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />}
      <input 
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        readOnly={readOnly}
        className={`w-full ${Icon ? 'pl-10' : 'px-4'} py-2 bg-white border rounded-lg focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 outline-none transition-all ${error ? 'border-red-500' : 'border-slate-200'} ${readOnly ? 'bg-slate-50 text-slate-500' : ''}`}
      />
    </div>
    {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
  </div>
);

// --- PAGES ---

const LandingPage = ({ onAuthClick }: { onAuthClick: (mode: 'login' | 'register') => void }) => {
  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="fixed w-full z-50 bg-white/80 backdrop-blur-md border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-amber-500 p-2 rounded-lg">
            <Shield className="text-white w-6 h-6" />
          </div>
          <span className="text-xl font-bold tracking-tight text-slate-900">Safety<span className="text-amber-500">Pulse</span></span>
        </div>
        <div className="flex gap-4">
          <button onClick={() => onAuthClick('login')} className="text-slate-600 font-medium hover:text-amber-500 transition-colors">Login</button>
          <Button onClick={() => onAuthClick('register')}>Get Started</Button>
        </div>
      </nav>

      <main className="pt-32 pb-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-20">
            <h1 className="text-5xl md:text-6xl font-extrabold text-slate-900 mb-6 leading-tight">
              Production-Grade <br />
              <span className="text-amber-500">Safety Data Intelligence</span>
            </h1>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto mb-10">
              Transform raw sensor metrics into actionable compliance reports. Real-time monitoring, automated anomaly detection, and enterprise-level reporting for modern industrial environments.
            </p>
            <div className="flex justify-center gap-4">
              <Button onClick={() => onAuthClick('register')} className="px-8 py-3 text-lg">Deploy SafetyPulse</Button>
              <Button variant="outline" className="px-8 py-3 text-lg">View Demo</Button>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-24">
            {[
              { icon: Activity, title: "Real-time Telemetry", desc: "Live ingestion of CO, H2S, O2, and LEL readings with sub-second latency." },
              { icon: Cpu, title: "AI Analytics", desc: "Powered by Gemini to detect anomalies and predict maintenance cycles." },
              { icon: FileText, title: "Automated Reports", desc: "Generate PDF compliance documents automatically based on historical data." }
            ].map((f, i) => (
              <Card key={i} className="hover:border-amber-500/50 transition-colors group">
                <div className="bg-amber-50 w-12 h-12 rounded-lg flex items-center justify-center mb-4 group-hover:bg-amber-100 transition-colors">
                  <f.icon className="text-amber-600 w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-2">{f.title}</h3>
                <p className="text-slate-500">{f.desc}</p>
              </Card>
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-12 bg-white">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <Shield className="text-amber-500 w-5 h-5" />
            <span className="font-bold text-slate-700">SafetyPulse</span>
          </div>
          <p className="text-slate-400 text-sm italic">Built with ☕ and late night debugging sessions • v0.3.2</p>
        </div>
      </footer>
    </div>
  );
};

const AuthPage = ({ mode: initialMode, onBack }: { mode: 'login' | 'register', onBack: () => void }) => {
  const [mode, setMode] = useState(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const auth = useContext(AuthContext);

  const pwdValidations = useMemo(() => validatePassword(password), [password]);
  const strength = useMemo(() => getStrength(password), [password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      if (mode === 'register') {
        if (Object.values(pwdValidations).some(v => !v)) {
          throw new Error("Password requirements not met");
        }
        await auth?.register(name, email, password);
      } else {
        await auth?.login(email, password);
      }
    } catch (err: any) {
      setError(err.message || "Operation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-md">
        <button onClick={onBack} className="flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors mb-8 font-medium">
          <ChevronRight className="rotate-180 w-4 h-4" /> Back to SafetyPulse
        </button>

        <Card className="!p-8">
          <div className="text-center mb-8">
            <div className="inline-flex p-3 bg-amber-50 rounded-xl mb-4">
              <Shield className="w-8 h-8 text-amber-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">{mode === 'login' ? 'Welcome back' : 'Create account'}</h2>
            <p className="text-slate-500 mt-1">{mode === 'login' ? 'Login to your engine dashboard' : 'Join the safety telemetry network'}</p>
          </div>

          <form onSubmit={handleSubmit}>
            {error && <div className="p-3 bg-red-50 border border-red-100 text-red-600 text-sm rounded-lg mb-6">{error}</div>}
            
            {mode === 'register' && (
              <Input label="Full Name" placeholder="John Doe" value={name} onChange={(e: any) => setName(e.target.value)} icon={User} />
            )}
            
            <Input label="Email Address" type="email" placeholder="john@company.com" value={email} onChange={(e: any) => setEmail(e.target.value)} icon={Bell} />
            
            <div className="relative">
              <Input 
                label="Password" 
                type={showPass ? "text" : "password"} 
                placeholder="••••••••" 
                value={password} 
                onChange={(e: any) => setPassword(e.target.value)} 
                icon={Shield} 
              />
              <button 
                type="button" 
                onClick={() => setShowPass(!showPass)} 
                className="absolute right-3 top-[38px] text-slate-400 hover:text-slate-600"
              >
                {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {mode === 'register' && password.length > 0 && (
              <div className="mb-6 space-y-3">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Strength: {getStrength(password).label}</span>
                </div>
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className={`h-full transition-all duration-500 ${getStrength(password).color}`} style={{ width: getStrength(password).width }}></div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { key: 'length', label: '8+ chars' },
                    { key: 'upper', label: 'Uppercase' },
                    { key: 'lower', label: 'Lowercase' },
                    { key: 'number', label: 'Number' },
                    { key: 'special', label: 'Special' }
                  ].map(v => (
                    <div key={v.key} className="flex items-center gap-1.5">
                      <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center ${pwdValidations[v.key as keyof typeof pwdValidations] ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-300'}`}>
                        <CheckCircle2 className="w-2.5 h-2.5" />
                      </div>
                      <span className={`text-[11px] font-medium ${pwdValidations[v.key as keyof typeof pwdValidations] ? 'text-slate-700' : 'text-slate-400'}`}>{v.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Button type="submit" className="w-full py-2.5 mt-2" disabled={loading}>
              {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> : (mode === 'login' ? 'Sign In' : 'Create Account')}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-slate-100 text-center">
            <p className="text-slate-500 text-sm">
              {mode === 'login' ? "Don't have an account?" : "Already have an account?"}
              <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')} className="ml-1 text-amber-600 font-bold hover:underline">
                {mode === 'login' ? 'Register here' : 'Login here'}
              </button>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};

const TestLab = () => {
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [running, setRunning] = useState(false);

  const startTests = () => {
    setRunning(true);
    setTimeout(() => {
      const results = runTestSuite();
      setTestResults(results);
      setRunning(false);
    }, 1200);
  };

  const stats = {
    total: testResults.length,
    passed: testResults.filter(r => r.passed).length,
    failed: testResults.filter(r => !r.passed).length
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-slate-800">Unit Testing Laboratory</h3>
          <p className="text-slate-500 text-sm">Verify safety critical logic through automated assertions.</p>
        </div>
        <Button onClick={startTests} disabled={running}>
          {running ? 'Running Suite...' : <><Play className="w-4 h-4" /> Execute All Tests</>}
        </Button>
      </div>

      {testResults.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-100 text-center">
            <div className="text-2xl font-black text-slate-800">{stats.total}</div>
            <div className="text-xs text-slate-400 uppercase font-bold">Total Tests</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-100 text-center">
            <div className="text-2xl font-black text-green-600">{stats.passed}</div>
            <div className="text-xs text-slate-400 uppercase font-bold">Passed</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-100 text-center">
            <div className="text-2xl font-black text-red-600">{stats.failed}</div>
            <div className="text-xs text-slate-400 uppercase font-bold">Failed</div>
          </div>
        </div>
      )}

      <Card className="!p-0">
        {testResults.length === 0 ? (
          <div className="p-12 text-center text-slate-400 italic">
            No tests executed in current session. Click 'Execute' to start.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {testResults.map((res, i) => (
              <div key={i} className="flex items-center justify-between p-4 px-6 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-4">
                  {res.passed ? (
                    <CheckCircle className="text-green-500 w-5 h-5" />
                  ) : (
                    <XCircle className="text-red-500 w-5 h-5" />
                  )}
                  <span className={`font-medium ${res.passed ? 'text-slate-700' : 'text-red-700'}`}>{res.name}</span>
                </div>
                <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${res.passed ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {res.passed ? 'Passed' : 'Failed'}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

const Dashboard = () => {
  const auth = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState('overview');
  const [settingsSubTab, setSettingsSubTab] = useState<'profile' | 'account' | 'preferences'>('profile');
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [readings, setReadings] = useState<Reading[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiReport, setAiReport] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Settings State
  const [profileName, setProfileName] = useState(auth?.user?.fullName || '');
  const [profileEmail, setProfileEmail] = useState(auth?.user?.email || '');
  const [currentPass, setCurrentPass] = useState('');
  const [newPass, setNewPass] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  const [saveLoading, setSaveLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    setTimeout(() => {
      const mockSensors: Sensor[] = [
        { id: '1', sensor_id: 'SN-4021', type: 'CO', location: 'Lower Level Dock', status: 'active', lastCalibration: '2023-11-12', nextCalibration: '2024-05-12' },
        { id: '2', sensor_id: 'SN-8820', type: 'H2S', location: 'Pumping Station A', status: 'active', lastCalibration: '2024-01-05', nextCalibration: '2024-07-05' },
        { id: '3', sensor_id: 'SN-1102', type: 'LEL', location: 'Storage Tank 4', status: 'maintenance', lastCalibration: '2023-09-20', nextCalibration: '2024-03-20' },
        { id: '4', sensor_id: 'SN-5592', type: 'O2', location: 'Confined Space B1', status: 'active', lastCalibration: '2024-02-01', nextCalibration: '2024-08-01' },
      ];
      const mockReadings: Reading[] = Array.from({ length: 15 }).map((_, i) => {
        const type = mockSensors[i % 4].type;
        const value = Math.random() * (type === 'LEL' ? 100 : 25);
        return {
          id: i,
          sensor_id: mockSensors[i % 4].sensor_id,
          timestamp: new Date(Date.now() - i * 1000 * 60 * 15).toISOString(),
          gas_type: type,
          value: value,
          unit: type === 'LEL' ? '%' : 'ppm',
          status: getReadingStatus(value, type)
        };
      });
      const mockAlerts: Alert[] = [
        { id: 101, sensor_id: 'SN-4021', type: 'CO Threshold', severity: 'medium', value: 35.4, timestamp: new Date().toISOString(), acknowledged: false }
      ];

      setSensors(mockSensors);
      setReadings(mockReadings);
      setAlerts(mockAlerts);
      setLoading(false);
    }, 1000);
  }, []);

  const generateAiInsight = async () => {
    setIsGenerating(true);
    setAiReport(null);
    try {
      const prompt = `Act as an industrial safety engineer. Analyze these sensor readings for anomalies: ${JSON.stringify(readings)}. Generate a formal safety pulse report. Use bullet points for recommendations. Keep it strictly professional. Use plain text formatting.`;
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: prompt,
      });
      setAiReport(response.text || "Report generation failed.");
    } catch (err) {
      console.error("Gemini Error:", err);
      setAiReport("UNABLE TO REACH ANALYSIS SERVER. CONNECTION ERROR 505.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleUpdateProfile = () => {
    setSaveLoading(true);
    setTimeout(() => {
      auth?.updateProfile({ fullName: profileName, email: profileEmail });
      setSaveLoading(false);
      setSuccessMsg('Profile updated successfully!');
      setTimeout(() => setSuccessMsg(''), 3000);
    }, 800);
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-slate-500 font-medium">Booting Safety Engines...</p>
      </div>
    </div>
  );

  const sidebarItems = [
    { section: 'Main', items: [
      { id: 'overview', icon: LayoutDashboard, label: 'Dashboard' },
      { id: 'sensors', icon: Activity, label: 'Sensors' },
      { id: 'analytics', icon: Zap, label: 'Analytics' },
      { id: 'reports', icon: FileText, label: 'Compliance Reports' },
    ]},
    { section: 'User & Management', items: [
      { id: 'profile', icon: User, label: 'Profile' },
      { id: 'account_mgmt', icon: CreditCard, label: 'Account Management' },
      { id: 'settings', icon: Settings, label: 'System Settings' },
    ]},
    { section: 'Development', items: [
      { id: 'tests', icon: TestTube, label: 'Test Lab' }
    ]}
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className={`${isSidebarCollapsed ? 'w-20' : 'w-64'} bg-slate-900 text-slate-400 p-4 flex flex-col hidden lg:flex transition-all duration-300 ease-in-out relative`}>
        <div className={`flex items-center ${isSidebarCollapsed ? 'justify-center' : 'gap-3 px-2'} text-white mb-10 transition-all`}>
          <Shield className="text-amber-500 w-6 h-6 shrink-0" />
          {!isSidebarCollapsed && <span className="text-xl font-bold whitespace-nowrap overflow-hidden">SafetyPulse</span>}
        </div>
        
        <div className="flex-1 overflow-y-auto no-scrollbar space-y-6">
          {sidebarItems.map((group, idx) => (
            <div key={idx} className="space-y-1">
              {!isSidebarCollapsed && <div className="px-4 text-[10px] font-black uppercase text-slate-500 tracking-widest mb-2 truncate">{group.section}</div>}
              {group.items.map(item => (
                <button 
                  key={item.id}
                  onClick={() => {
                    if (item.id === 'profile') { setActiveTab('settings'); setSettingsSubTab('profile'); }
                    else if (item.id === 'account_mgmt') { setActiveTab('settings'); setSettingsSubTab('account'); }
                    else setActiveTab(item.id);
                  }}
                  className={`w-full flex items-center ${isSidebarCollapsed ? 'justify-center px-0' : 'px-4'} py-3 rounded-lg font-medium transition-colors ${activeTab === item.id ? 'bg-amber-500 text-white' : 'hover:bg-white/5 hover:text-white'}`}
                >
                  <item.icon className="w-5 h-5 shrink-0" />
                  {!isSidebarCollapsed && <span className="ml-3 truncate">{item.label}</span>}
                </button>
              ))}
            </div>
          ))}
        </div>

        <div className="pt-6 border-t border-white/10 mt-4">
          <button onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)} className={`w-full flex items-center ${isSidebarCollapsed ? 'justify-center' : 'px-4'} py-3 mb-2 rounded-lg font-medium text-slate-400 hover:bg-white/5 hover:text-white transition-all`}>
            {isSidebarCollapsed ? <PanelLeftOpen className="w-5 h-5 shrink-0 text-amber-500" /> : <><PanelLeftClose className="w-5 h-5 shrink-0" /><span className="ml-3">Collapse Menu</span></>}
          </button>
          <button onClick={() => auth?.logout()} className={`w-full flex items-center ${isSidebarCollapsed ? 'justify-center' : 'px-4'} py-3 rounded-lg font-medium text-red-400 hover:bg-red-400/10 transition-colors`}>
            <LogOut className="w-5 h-5 shrink-0" />
            {!isSidebarCollapsed && <span className="ml-3">Logout</span>}
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-40">
          <h2 className="text-xl font-bold text-slate-800 capitalize">{activeTab === 'settings' ? `${settingsSubTab} Settings` : activeTab.replace('_', ' ')}</h2>
          <div className="flex gap-2 items-center">
            <span className="text-sm font-medium text-slate-600 hidden md:block">System Status: <span className="text-green-500">OPERATIONAL</span></span>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
        </header>

        <div className="p-8">
          {activeTab === 'overview' && (
            <div className="space-y-8 animate-fade-in">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="!p-5 border-l-4 border-amber-500"><div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Total Sensors</div><div className="text-2xl font-black text-slate-900">{sensors.length}</div></Card>
                <Card className="!p-5 border-l-4 border-green-500"><div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Active Now</div><div className="text-2xl font-black text-slate-900">{sensors.filter(s => s.status === 'active').length}</div></Card>
                <Card className="!p-5 border-l-4 border-red-500"><div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Alerts</div><div className="text-2xl font-black text-slate-900">{alerts.length}</div></Card>
                <Card className="!p-5 border-l-4 border-blue-500"><div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Uptime</div><div className="text-2xl font-black text-slate-900">99.9%</div></Card>
              </div>

              <div className="grid lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                  <Card title="Recent Telemetry History">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead>
                          <tr className="text-slate-400 border-b border-slate-100">
                            <th className="pb-3 font-medium">Sensor</th>
                            <th className="pb-3 font-medium">Value</th>
                            <th className="pb-3 font-medium">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                          {readings.slice(0, 8).map(r => (
                            <tr key={r.id} className="group">
                              <td className="py-3 font-bold text-slate-700">{r.sensor_id}</td>
                              <td className="py-3 font-mono">{r.value.toFixed(2)} {r.unit}</td>
                              <td className="py-3">
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                                  r.status === 'critical' ? 'bg-red-100 text-red-600' : 
                                  r.status === 'warning' ? 'bg-amber-100 text-amber-600' : 'bg-green-100 text-green-600'
                                }`}>{r.status}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                </div>

                <div className="space-y-6">
                  {/* Stark Black & White AI Report */}
                  <div className="bg-black text-white p-1 border-2 border-black">
                    <div className="border border-white/20 p-6 flex flex-col min-h-[400px]">
                      <div className="flex justify-between items-center border-b border-white/20 pb-4 mb-6">
                        <div className="flex items-center gap-2">
                          <FileSearch className="w-5 h-5" />
                          <span className="text-[10px] font-black uppercase tracking-[0.2em]">Safety Analytics v3.2</span>
                        </div>
                        <span className="text-[10px] opacity-50">{new Date().toLocaleDateString()}</span>
                      </div>

                      <h3 className="text-xl font-black uppercase mb-2 tracking-tighter">Automated Analysis Report</h3>
                      <p className="text-[10px] text-slate-400 mb-8 uppercase font-bold">Engine State: {isGenerating ? 'ANALYZING...' : 'IDLE'}</p>

                      {!aiReport ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center space-y-6 border border-dashed border-white/10 rounded p-8">
                          <Zap className="w-12 h-12 text-white animate-pulse" />
                          <div>
                            <p className="text-xs font-bold uppercase mb-2">TELEMETRY DATA READY</p>
                            <p className="text-[10px] text-slate-500 leading-relaxed">System is awaiting manual trigger to process current sensor buffer and generate intelligence summary.</p>
                          </div>
                          <button 
                            onClick={generateAiInsight}
                            disabled={isGenerating}
                            className="w-full bg-white text-black font-black uppercase text-xs py-3 hover:bg-slate-200 transition-colors disabled:opacity-50"
                          >
                            {isGenerating ? "Processing Ingest..." : "RUN FULL ANALYSIS"}
                          </button>
                        </div>
                      ) : (
                        <div className="flex-1 space-y-6">
                          <div className="bg-white text-black p-4 font-mono text-[11px] leading-relaxed relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-16 h-16 bg-black flex items-center justify-center rotate-45 translate-x-8 -translate-y-8">
                              <span className="text-[8px] text-white font-bold -rotate-45">SECURE</span>
                            </div>
                            <div dangerouslySetInnerHTML={{ __html: aiReport.replace(/\n/g, '<br/>') }}></div>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={generateAiInsight} className="flex-1 border border-white font-bold uppercase text-[10px] py-2 hover:bg-white hover:text-black transition-all">Regenerate</button>
                            <button className="flex-1 bg-white text-black font-bold uppercase text-[10px] py-2 hover:bg-slate-200 transition-all flex items-center justify-center gap-2"><Printer className="w-3 h-3" /> Print PDF</button>
                          </div>
                        </div>
                      )}

                      <div className="mt-auto pt-4 border-t border-white/20 flex justify-between items-center text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                        <span>SafetyPulse Internal</span>
                        <span>CONFIDENTIAL</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tests' && <TestLab />}
          {activeTab === 'sensors' && (
            <div className="animate-fade-in"><Card title="Sensor Inventory">List of all active industrial hardware components...</Card></div>
          )}
          {activeTab === 'analytics' && (
            <div className="animate-fade-in"><Card title="Trend Visualization">Deep dive into time-series data clusters...</Card></div>
          )}
          {activeTab === 'settings' && (
            <div className="animate-fade-in"><Card title="Profile Controls">User account configuration and notification nodes...</Card></div>
          )}
        </div>
      </main>
    </div>
  );
};

// --- MAIN APP ---

function App() {
  const [authMode, setAuthMode] = useState<'landing' | 'login' | 'register'>('landing');
  const auth = useContext(AuthContext);

  useEffect(() => {
    if (auth?.user) setAuthMode('landing');
  }, [auth?.user]);

  if (auth?.user) return <Dashboard />;

  if (authMode === 'landing') {
    return <LandingPage onAuthClick={setAuthMode} />;
  }

  return <AuthPage mode={authMode as 'login' | 'register'} onBack={() => setAuthMode('landing')} />;
}

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}
