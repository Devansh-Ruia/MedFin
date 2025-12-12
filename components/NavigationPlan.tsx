import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, ArrowRight, Shield, DollarSign, FileText } from 'lucide-react';
import { generateActionPlan } from '../services/geminiService';
import { AnalyzedBill, NavigationAction } from '../types';

interface NavigationPlanProps {
  analyzedBills: AnalyzedBill[];
}

export const NavigationPlan: React.FC<NavigationPlanProps> = ({ analyzedBills }) => {
  const [actions, setActions] = useState<NavigationAction[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchPlan = async () => {
        // If we have bills but no plan, generate one
        if (analyzedBills.length > 0 && actions.length === 0) {
            setLoading(true);
            try {
                const newActions = await generateActionPlan(analyzedBills);
                setActions(newActions);
            } finally {
                setLoading(false);
            }
        }
    };
    fetchPlan();
  }, [analyzedBills, actions.length]);

  const toggleAction = (id: string) => {
    setActions(prev => prev.map(a => 
        a.id === id ? { ...a, status: a.status === 'completed' ? 'pending' : 'completed' } : a
    ));
  };

  const EmptyState = () => (
    <div className="text-center py-16 bg-white rounded-xl border border-gray-200 border-dashed">
        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-400">
            <FileText size={24} />
        </div>
        <h3 className="text-lg font-semibold text-gray-900">No Action Plan Yet</h3>
        <p className="text-gray-500 max-w-sm mx-auto mt-2">
            Upload and analyze a medical bill to let the Autonomous Navigation Engine generate a personalized savings strategy for you.
        </p>
    </div>
  );

  if (analyzedBills.length === 0) return <EmptyState />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
            <h2 className="text-2xl font-bold text-gray-900">Financial Navigation Plan</h2>
            <p className="text-gray-500 mt-1">
                Your personalized step-by-step guide to resolving medical debt.
            </p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
            {[1, 2, 3].map(i => (
                <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
            ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
                {actions.map((action) => (
                    <div 
                        key={action.id} 
                        className={`group bg-white p-5 rounded-xl border transition-all ${
                            action.status === 'completed' 
                            ? 'border-gray-100 opacity-60' 
                            : 'border-gray-200 shadow-sm hover:shadow-md hover:border-primary-200'
                        }`}
                    >
                        <div className="flex items-start gap-4">
                            <button 
                                onClick={() => toggleAction(action.id)}
                                className={`mt-1 transition-colors ${
                                    action.status === 'completed' ? 'text-green-500' : 'text-gray-300 group-hover:text-primary-500'
                                }`}
                            >
                                {action.status === 'completed' ? <CheckCircle2 size={24} /> : <Circle size={24} />}
                            </button>
                            
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                                        action.priority === 'high' ? 'bg-red-100 text-red-700' : 
                                        action.priority === 'medium' ? 'bg-amber-100 text-amber-700' : 
                                        'bg-blue-100 text-blue-700'
                                    }`}>
                                        {action.priority} Priority
                                    </span>
                                    {action.estimatedSavings > 0 && (
                                        <span className="text-xs font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded flex items-center gap-1">
                                            <DollarSign size={10} /> Save ${action.estimatedSavings}
                                        </span>
                                    )}
                                </div>
                                <h3 className={`font-semibold text-lg ${action.status === 'completed' ? 'text-gray-500 line-through' : 'text-gray-900'}`}>
                                    {action.title}
                                </h3>
                                <p className="text-gray-600 mt-1 text-sm leading-relaxed">
                                    {action.description}
                                </p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="space-y-6">
                <div className="bg-primary-50 p-6 rounded-xl border border-primary-100">
                    <h4 className="font-semibold text-primary-900 mb-2 flex items-center gap-2">
                        <Shield size={18} />
                        Assistance Eligible
                    </h4>
                    <p className="text-sm text-primary-800 mb-4">
                        Based on your profile, you may qualify for <strong>Hospital Charity Care</strong>.
                    </p>
                    <button className="w-full bg-white text-primary-600 py-2 rounded-lg font-medium text-sm shadow-sm hover:bg-primary-50 border border-primary-200 transition-colors">
                        Check Eligibility
                    </button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
};
