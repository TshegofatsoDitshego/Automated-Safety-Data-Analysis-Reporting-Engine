
import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Bell, 
  Shield, 
  User, 
  Database, 
  Globe, 
  ChevronRight, 
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react';

interface SettingsPageProps {
  userName: string;
  onUpdateName: (name: string) => void;
}

const SettingsPage: React.FC<SettingsPageProps> = ({ userName, onUpdateName }) => {
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  
  // Example states for interactive settings
  const [displayName, setDisplayName] = useState(userName);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  // Keep local state in sync if userName changes externally (unlikely but good practice)
  useEffect(() => {
    setDisplayName(userName);
  }, [userName]);

  const sections = [
    { id: 'profile', title: 'Profile Settings', icon: User, desc: 'Manage your public profile and identity.' },
    { id: 'notifications', title: 'Notifications', icon: Bell, desc: 'Configure how you receive safety alerts.' },
    { id: 'security', title: 'Security', icon: Shield, desc: 'Manage two-factor auth and passwords.' },
    { id: 'data', title: 'Data Management', icon: Database, desc: 'Export or purge telemetry logs.' },
    { id: 'regional', title: 'Regional Settings', icon: Globe, desc: 'Units, timezones and localization.' },
  ];

  const handleUpdate = () => {
    setIsUpdating(true);
    setShowSuccess(false);
    
    setTimeout(() => {
      // Update the global state in App.tsx
      onUpdateName(displayName);
      setIsUpdating(false);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    }, 1200);
  };

  if (selectedSection) {
    const section = sections.find(s => s.id === selectedSection);
    return (
      <div className="space-y-8 animate-in slide-in-from-left-4 duration-300">
        <button 
          onClick={() => setSelectedSection(null)}
          className="flex items-center gap-2 text-slate-500 hover:text-blue-600 font-bold transition-colors"
        >
          <ArrowLeft size={20} />
          Back to Settings
        </button>

        <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100 max-w-2xl">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-4 bg-blue-50 text-blue-600 rounded-2xl">
              {section && <section.icon size={32} />}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900">{section?.title}</h2>
              <p className="text-slate-400">{section?.desc}</p>
            </div>
          </div>

          <div className="space-y-6">
            {showSuccess && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-3 text-green-700 animate-in fade-in zoom-in duration-300">
                <CheckCircle2 size={20} />
                <span className="text-sm font-bold">Preferences updated successfully!</span>
              </div>
            )}

            <div className="p-6 bg-slate-50 rounded-2xl border border-slate-100 flex items-start gap-4">
              <div className="p-2 bg-white rounded-full text-blue-600 shadow-sm">
                <CheckCircle2 size={20} />
              </div>
              <div>
                <h4 className="font-bold text-slate-900">Current Configuration Active</h4>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Your safety preferences are currently synchronized with the central facility node. Changes made here will take effect immediately.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1 block">Display Name</label>
                <input 
                  type="text" 
                  className="w-full bg-white border border-slate-200 rounded-xl p-3.5 outline-none focus:ring-2 focus:ring-blue-500 font-semibold text-black placeholder:text-slate-300 transition-all shadow-sm" 
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                />
              </div>
              
              <div 
                className="flex items-center justify-between p-4 bg-white border border-slate-200 rounded-xl cursor-pointer hover:bg-slate-50 transition-colors"
                onClick={() => setNotificationsEnabled(!notificationsEnabled)}
              >
                <div>
                  <p className="font-bold text-slate-900">Push Notifications</p>
                  <p className="text-xs text-slate-400">Receive critical alerts on your mobile device</p>
                </div>
                <div className={`w-12 h-6 rounded-full p-1 transition-colors ${notificationsEnabled ? 'bg-blue-600' : 'bg-slate-200'}`}>
                  <div className={`w-4 h-4 bg-white rounded-full transition-transform ${notificationsEnabled ? 'ml-auto' : 'ml-0'}`} />
                </div>
              </div>
            </div>

            <button 
              onClick={handleUpdate}
              disabled={isUpdating}
              className="w-full bg-blue-600 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition-all flex items-center justify-center gap-2 disabled:opacity-70"
            >
              {isUpdating ? <Loader2 size={20} className="animate-spin" /> : 'Save Preferences'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900">Account Settings</h1>
        <p className="text-slate-500 font-medium">Configure engine preferences and security</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          {sections.map((section) => (
            <div 
              key={section.id} 
              onClick={() => setSelectedSection(section.id)}
              className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center justify-between group hover:border-blue-200 transition-all cursor-pointer hover:shadow-md active:scale-[0.98]"
            >
              <div className="flex items-center gap-5">
                <div className="p-3 bg-slate-50 rounded-xl text-slate-400 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
                  <section.icon size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900">{section.title}</h3>
                  <p className="text-sm text-slate-400">{section.desc}</p>
                </div>
              </div>
              <ChevronRight className="text-slate-300 group-hover:text-blue-500 transition-colors" size={20} />
            </div>
          ))}
        </div>

        <div className="space-y-6">
          <div className="bg-blue-600 text-white p-8 rounded-3xl shadow-xl shadow-blue-600/20 relative overflow-hidden group">
             <div className="absolute top-[-20%] right-[-20%] w-48 h-48 rounded-full bg-white/10 group-hover:scale-110 transition-transform duration-700" />
             <SettingsIcon className="mb-4 opacity-50" size={40} />
             <h3 className="text-xl font-bold mb-2">Engine v2.4.0</h3>
             <p className="text-blue-100 text-sm mb-6 leading-relaxed">
               Your safety engine is currently up to date with the latest industrial standards.
             </p>
             <button className="w-full bg-white text-blue-600 font-bold py-3 rounded-xl hover:bg-blue-50 transition-colors shadow-lg active:scale-95">
                Check for Updates
             </button>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
             <div className="flex items-center gap-2 mb-4">
               <Database size={18} className="text-slate-400" />
               <h3 className="font-bold text-slate-900">Storage Usage</h3>
             </div>
             <div className="space-y-4">
               <div>
                  <div className="flex justify-between text-xs font-bold text-slate-400 uppercase mb-2">
                    <span>Telemetry Logs</span>
                    <span>14.2 GB</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div className="bg-blue-500 h-full w-[65%] transition-all duration-1000" />
                  </div>
               </div>
               <div>
                  <div className="flex justify-between text-xs font-bold text-slate-400 uppercase mb-2">
                    <span>Reports Archive</span>
                    <span>2.8 GB</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full w-[20%] transition-all duration-1000" />
                  </div>
               </div>
             </div>
             
             <div className="mt-6 pt-6 border-t border-slate-50 flex items-center gap-2 text-xs text-slate-400">
               <AlertCircle size={14} />
               <span>Auto-purge enabled for logs older than 30 days</span>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
