import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { Dashboard } from './components/Dashboard';
import { BillAnalyzer, BillResults } from './components/BillAnalyzer';
import { NavigationPlan } from './components/NavigationPlan';
import { ChatAssistant } from './components/ChatAssistant';
import { View, AnalyzedBill } from './types';

function App() {
  const [currentView, setCurrentView] = useState<View>(View.DASHBOARD);
  const [analyzedBills, setAnalyzedBills] = useState<AnalyzedBill[]>([]);
  const [activeBill, setActiveBill] = useState<AnalyzedBill | null>(null);

  const handleBillAnalyzed = (bill: AnalyzedBill) => {
    setAnalyzedBills(prev => [bill, ...prev]);
    setActiveBill(bill);
    // Stay on current view but render results, handled inside component logic or switch
  };

  const renderContent = () => {
    switch (currentView) {
      case View.DASHBOARD:
        return <Dashboard />;
      case View.BILL_UPLOAD:
        if (activeBill) {
            return <BillResults bill={activeBill} onReset={() => setActiveBill(null)} />;
        }
        return <BillAnalyzer onBillAnalyzed={handleBillAnalyzed} />;
      case View.NAVIGATION_PLAN:
        return <NavigationPlan analyzedBills={analyzedBills} />;
      case View.CHAT:
        return <ChatAssistant />;
      case View.ASSISTANCE:
        return (
            <div className="flex flex-col items-center justify-center h-96 text-center">
                <h2 className="text-2xl font-bold text-gray-900">Financial Assistance Matching</h2>
                <p className="text-gray-500 mt-2 max-w-md">The eligibility engine compares your profile against 50,000+ programs.</p>
                <button 
                    onClick={() => setCurrentView(View.DASHBOARD)}
                    className="mt-6 text-primary-600 font-medium hover:underline"
                >
                    Return to Dashboard
                </button>
            </div>
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout currentView={currentView} setCurrentView={setCurrentView}>
      {renderContent()}
    </Layout>
  );
}

export default App;
