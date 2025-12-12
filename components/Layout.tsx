import React from 'react';
import { LayoutDashboard, FileText, Map, MessageSquare, ShieldCheck, Activity } from 'lucide-react';
import { View } from '../types';

interface LayoutProps {
  currentView: View;
  setCurrentView: (view: View) => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ currentView, setCurrentView, children }) => {
  const navItems = [
    { id: View.DASHBOARD, label: 'Dashboard', icon: LayoutDashboard },
    { id: View.BILL_UPLOAD, label: 'Analyze Bills', icon: FileText },
    { id: View.NAVIGATION_PLAN, label: 'Action Plan', icon: Map },
    { id: View.ASSISTANCE, label: 'Assistance', icon: ShieldCheck },
    { id: View.CHAT, label: 'AI Advisor', icon: MessageSquare },
  ];

  return (
    <div className="flex h-screen bg-gray-50 text-slate-800">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 hidden md:flex flex-col">
        <div className="p-6 border-b border-gray-100 flex items-center gap-2">
          <Activity className="w-8 h-8 text-primary-600" />
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-primary-400">
            MedFin
          </span>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive 
                    ? 'bg-primary-50 text-primary-700 font-medium shadow-sm' 
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <Icon size={20} className={isActive ? 'text-primary-600' : 'text-gray-400'} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-4 text-white">
            <p className="text-xs text-slate-400 uppercase font-semibold mb-1">Total Savings</p>
            <p className="text-2xl font-bold text-emerald-400">$1,240.50</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {/* Mobile Header */}
        <div className="md:hidden bg-white border-b border-gray-200 p-4 flex items-center justify-between sticky top-0 z-10">
           <div className="flex items-center gap-2">
            <Activity className="w-6 h-6 text-primary-600" />
            <span className="font-bold text-lg">MedFin</span>
          </div>
          <button className="text-gray-500">
            <LayoutDashboard />
          </button>
        </div>
        
        <div className="p-6 md:p-8 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};
