import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, PieChart, Pie } from 'recharts';
import { DollarSign, Activity, TrendingDown, Clock } from 'lucide-react';

const healthData = [
  { name: 'Deductible', value: 1200, total: 3000, color: '#0ea5e9' },
  { name: 'OOP Max', value: 2400, total: 6000, color: '#6366f1' },
];

const spendingData = [
  { month: 'Jan', amount: 450 },
  { month: 'Feb', amount: 120 },
  { month: 'Mar', amount: 800 },
  { month: 'Apr', amount: 320 },
  { month: 'May', amount: 150 },
];

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'YTD Spending', value: '$1,840', icon: DollarSign, color: 'text-emerald-600', bg: 'bg-emerald-50' },
          { label: 'Active Bills', value: '3', icon: FileText, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'Deductible Met', value: '40%', icon: Activity, color: 'text-indigo-600', bg: 'bg-indigo-50' },
          { label: 'Est. Savings', value: '$520', icon: TrendingDown, color: 'text-amber-600', bg: 'bg-amber-50' },
        ].map((stat, i) => (
           <div key={i} className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
             <div className="flex justify-between items-start mb-4">
                <div className={`${stat.bg} p-2.5 rounded-lg`}>
                    <stat.icon size={20} className={stat.color} />
                </div>
                <span className="text-xs font-medium px-2 py-1 bg-gray-50 text-gray-500 rounded-full">2024</span>
             </div>
             <p className="text-sm text-gray-500 font-medium">{stat.label}</p>
             <h3 className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</h3>
           </div> 
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Spending Chart */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 mb-6">Medical Spending History</h3>
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={spendingData}>
                        <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{fill: '#9ca3af'}} dy={10} />
                        <YAxis axisLine={false} tickLine={false} tick={{fill: '#9ca3af'}} prefix="$" />
                        <Tooltip 
                            cursor={{fill: '#f3f4f6'}}
                            contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                        />
                        <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={40} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>

        {/* Insurance Progress */}
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 mb-6">Coverage Status</h3>
            <div className="space-y-6">
                {healthData.map((item) => (
                    <div key={item.name}>
                        <div className="flex justify-between text-sm mb-2">
                            <span className="font-medium text-gray-700">{item.name}</span>
                            <span className="text-gray-500">${item.value} / ${item.total}</span>
                        </div>
                        <div className="h-2.5 w-full bg-gray-100 rounded-full overflow-hidden">
                            <div 
                                className="h-full rounded-full transition-all duration-1000 ease-out"
                                style={{ width: `${(item.value / item.total) * 100}%`, backgroundColor: item.color }}
                            />
                        </div>
                    </div>
                ))}
            </div>
            
            <div className="mt-8 p-4 bg-primary-50 rounded-lg flex gap-3 items-start">
                <Clock className="text-primary-600 mt-0.5" size={18} />
                <div>
                    <h4 className="text-sm font-semibold text-primary-900">Plan Reset</h4>
                    <p className="text-xs text-primary-700 mt-1">Your insurance plan year resets in 142 days. Try to schedule elective procedures soon.</p>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

// Helper for Lucide icon dynamic usage in stats array
import { FileText } from 'lucide-react';
