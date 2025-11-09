import React, { useState, useEffect } from 'react';
import { Calculator, Shield, DollarSign, FileText, Search, AlertCircle, TrendingUp, Users, ChevronRight, Check, X, Info, Calendar, CreditCard, Building2, Phone, Mail, MapPin } from 'lucide-react';

const HealthcareFinancialNavigator = () => {
  const [activeTab, setActiveTab] = useState('estimator');
  const [procedureSearch, setProcedureSearch] = useState('');
  const [selectedProcedure, setSelectedProcedure] = useState(null);
  const [insuranceInfo, setInsuranceInfo] = useState({
    provider: '',
    planType: '',
    deductible: 2000,
    deductibleMet: 500,
    outOfPocketMax: 8000,
    outOfPocketMet: 1000,
    coinsurance: 20
  });
  const [bills, setBills] = useState([
    { id: 1, provider: 'City Medical Center', amount: 3500, date: '2025-01-15', status: 'pending', dueDate: '2025-02-15' },
    { id: 2, provider: 'Radiology Associates', amount: 800, date: '2025-01-10', status: 'review', dueDate: '2025-02-10' },
    { id: 3, provider: 'Emergency Physicians', amount: 1200, date: '2025-01-05', status: 'negotiating', dueDate: '2025-02-05' }
  ]);
  const [assistancePrograms, setAssistancePrograms] = useState([]);
  const [paymentPlan, setPaymentPlan] = useState(null);

  // Mock procedure database
  const procedures = [
    { id: 1, name: 'MRI Scan', cptCode: '70551', avgCost: 3000, lowCost: 1500, highCost: 5000 },
    { id: 2, name: 'CT Scan', cptCode: '74160', avgCost: 2000, lowCost: 800, highCost: 3500 },
    { id: 3, name: 'Colonoscopy', cptCode: '45380', avgCost: 3500, lowCost: 2000, highCost: 5000 },
    { id: 4, name: 'Knee Replacement', cptCode: '27447', avgCost: 35000, lowCost: 25000, highCost: 50000 },
    { id: 5, name: 'Appendectomy', cptCode: '44970', avgCost: 15000, lowCost: 10000, highCost: 25000 },
    { id: 6, name: 'Cataract Surgery', cptCode: '66984', avgCost: 3500, lowCost: 2500, highCost: 5000 }
  ];

  // Mock provider database
  const providers = [
    { id: 1, name: 'City Medical Center', quality: 4.5, distance: 2.3, estimatedCost: null },
    { id: 2, name: 'Regional Hospital', quality: 4.2, distance: 5.8, estimatedCost: null },
    { id: 3, name: 'University Medical', quality: 4.8, distance: 8.1, estimatedCost: null },
    { id: 4, name: 'Community Health', quality: 4.0, distance: 1.5, estimatedCost: null }
  ];

  const calculateOutOfPocket = (totalCost) => {
    const { deductible, deductibleMet, outOfPocketMax, outOfPocketMet, coinsurance } = insuranceInfo;
    const remainingDeductible = Math.max(0, deductible - deductibleMet);
    const costAfterDeductible = Math.max(0, totalCost - remainingDeductible);
    const coinsuranceAmount = costAfterDeductible * (coinsurance / 100);
    const totalOOP = Math.min(remainingDeductible + coinsuranceAmount, outOfPocketMax - outOfPocketMet);
    return totalOOP;
  };

  const searchProcedures = () => {
    if (!procedureSearch) return [];
    return procedures.filter(p => 
      p.name.toLowerCase().includes(procedureSearch.toLowerCase()) ||
      p.cptCode.includes(procedureSearch)
    );
  };

  const findAssistancePrograms = () => {
    // Simulate finding assistance programs
    const programs = [
      { id: 1, name: 'Hospital Financial Assistance', eligibility: 'Income < 300% FPL', coverage: 'Up to 100%', status: 'likely' },
      { id: 2, name: 'Manufacturer Patient Assistance', eligibility: 'For specific medications', coverage: 'Varies', status: 'check' },
      { id: 3, name: 'State Medicaid Expansion', eligibility: 'Income < 138% FPL', coverage: 'Full coverage', status: 'possible' },
      { id: 4, name: 'Charity Care Program', eligibility: 'Financial hardship', coverage: '50-100%', status: 'likely' },
      { id: 5, name: 'Payment Plan Options', eligibility: 'All patients', coverage: '0% interest', status: 'available' }
    ];
    setAssistancePrograms(programs);
  };

  const negotiateBill = (billId) => {
    setBills(bills.map(bill => 
      bill.id === billId 
        ? { ...bill, status: 'negotiating', amount: bill.amount * 0.7 }
        : bill
    ));
  };

  const createPaymentPlan = (totalAmount, months) => {
    const monthlyPayment = totalAmount / months;
    const plan = {
      total: totalAmount,
      months: months,
      monthlyPayment: monthlyPayment,
      firstDue: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      interestRate: 0
    };
    setPaymentPlan(plan);
    return plan;
  };

  const CostEstimator = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <Calculator className="mr-2" /> Procedure Cost Estimator
        </h3>
        
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search procedure or CPT code..."
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
              value={procedureSearch}
              onChange={(e) => setProcedureSearch(e.target.value)}
            />
          </div>

          {procedureSearch && (
            <div className="bg-white rounded-lg border border-gray-200 max-h-48 overflow-y-auto">
              {searchProcedures().map(proc => (
                <div
                  key={proc.id}
                  className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                  onClick={() => {
                    setSelectedProcedure(proc);
                    setProcedureSearch(proc.name);
                  }}
                >
                  <div className="font-medium">{proc.name}</div>
                  <div className="text-sm text-gray-500">CPT: {proc.cptCode} | Avg: ${proc.avgCost.toLocaleString()}</div>
                </div>
              ))}
            </div>
          )}

          {selectedProcedure && (
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h4 className="font-semibold text-lg mb-4">{selectedProcedure.name} Cost Analysis</h4>
              
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">${selectedProcedure.lowCost.toLocaleString()}</div>
                  <div className="text-sm text-gray-500">Low Range</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">${selectedProcedure.avgCost.toLocaleString()}</div>
                  <div className="text-sm text-gray-500">Average</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">${selectedProcedure.highCost.toLocaleString()}</div>
                  <div className="text-sm text-gray-500">High Range</div>
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <h5 className="font-semibold mb-2">Your Estimated Out-of-Pocket:</h5>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Best Case:</span>
                    <div className="font-bold text-green-600">${calculateOutOfPocket(selectedProcedure.lowCost).toLocaleString()}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Likely:</span>
                    <div className="font-bold text-blue-600">${calculateOutOfPocket(selectedProcedure.avgCost).toLocaleString()}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Worst Case:</span>
                    <div className="font-bold text-red-600">${calculateOutOfPocket(selectedProcedure.highCost).toLocaleString()}</div>
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <h5 className="font-semibold mb-2">Provider Comparison:</h5>
                <div className="space-y-2">
                  {providers.map(provider => {
                    const cost = selectedProcedure.avgCost * (0.7 + Math.random() * 0.6);
                    return (
                      <div key={provider.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <div className="font-medium">{provider.name}</div>
                          <div className="text-sm text-gray-500">
                            {provider.distance} miles | ★ {provider.quality}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">${cost.toLocaleString()}</div>
                          <div className="text-sm text-blue-600">
                            OOP: ${calculateOutOfPocket(cost).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const InsuranceNavigator = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <Shield className="mr-2" /> Insurance Coverage Analyzer
        </h3>
        
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Insurance Provider</label>
            <select 
              className="w-full p-2 border rounded-lg"
              value={insuranceInfo.provider}
              onChange={(e) => setInsuranceInfo({...insuranceInfo, provider: e.target.value})}
            >
              <option value="">Select Provider</option>
              <option value="bcbs">Blue Cross Blue Shield</option>
              <option value="united">UnitedHealth</option>
              <option value="aetna">Aetna</option>
              <option value="cigna">Cigna</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plan Type</label>
            <select 
              className="w-full p-2 border rounded-lg"
              value={insuranceInfo.planType}
              onChange={(e) => setInsuranceInfo({...insuranceInfo, planType: e.target.value})}
            >
              <option value="">Select Plan</option>
              <option value="ppo">PPO</option>
              <option value="hmo">HMO</option>
              <option value="hdhp">HDHP</option>
              <option value="epo">EPO</option>
            </select>
          </div>
        </div>

        <div className="mt-6 bg-white p-4 rounded-lg border border-gray-200">
          <h4 className="font-semibold mb-4">Your Plan Details</h4>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-600">Deductible</span>
                <span className="text-sm font-medium">${insuranceInfo.deductibleMet} / ${insuranceInfo.deductible}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{width: `${(insuranceInfo.deductibleMet / insuranceInfo.deductible) * 100}%`}}
                />
              </div>
            </div>
            
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gray-600">Out-of-Pocket Maximum</span>
                <span className="text-sm font-medium">${insuranceInfo.outOfPocketMet} / ${insuranceInfo.outOfPocketMax}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-600 h-2 rounded-full transition-all"
                  style={{width: `${(insuranceInfo.outOfPocketMet / insuranceInfo.outOfPocketMax) * 100}%`}}
                />
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Coinsurance</span>
              <span className="text-sm font-medium">{insuranceInfo.coinsurance}%</span>
            </div>
          </div>
        </div>

        <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="flex items-start">
            <AlertCircle className="text-yellow-600 mt-1 mr-2" size={20} />
            <div>
              <h5 className="font-semibold text-gray-800">Coverage Tips</h5>
              <ul className="mt-2 text-sm text-gray-600 space-y-1">
                <li>• Always verify coverage before procedures</li>
                <li>• Check if providers are in-network</li>
                <li>• Get pre-authorization when required</li>
                <li>• Keep all EOB documents for appeals</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const BillManager = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-xl">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <FileText className="mr-2" /> Medical Bill Manager
        </h3>
        
        <div className="space-y-4">
          {bills.map(bill => (
            <div key={bill.id} className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold">{bill.provider}</h4>
                  <div className="text-sm text-gray-500 mt-1">
                    Date: {bill.date} | Due: {bill.dueDate}
                  </div>
                  <div className="mt-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                      ${bill.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                        bill.status === 'review' ? 'bg-blue-100 text-blue-800' :
                        bill.status === 'negotiating' ? 'bg-purple-100 text-purple-800' :
                        'bg-green-100 text-green-800'}`}>
                      {bill.status === 'negotiating' ? 'Negotiating' : bill.status.charAt(0).toUpperCase() + bill.status.slice(1)}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold">${bill.amount.toLocaleString()}</div>
                  {bill.status === 'negotiating' && (
                    <div className="text-sm text-green-600 font-medium">30% reduction applied</div>
                  )}
                  <div className="mt-2 space-x-2">
                    <button
                      onClick={() => negotiateBill(bill.id)}
                      className="text-sm px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700"
                    >
                      Negotiate
                    </button>
                    <button className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
                      Pay
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 bg-blue-50 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">Total Outstanding</h4>
          <div className="text-3xl font-bold text-blue-600">
            ${bills.reduce((sum, bill) => sum + bill.amount, 0).toLocaleString()}
          </div>
          <button 
            onClick={() => createPaymentPlan(bills.reduce((sum, bill) => sum + bill.amount, 0), 12)}
            className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create Payment Plan
          </button>
        </div>

        {paymentPlan && (
          <div className="mt-4 bg-green-50 p-4 rounded-lg border border-green-200">
            <h4 className="font-semibold mb-2">Suggested Payment Plan</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Monthly Payment:</span>
                <div className="font-bold text-lg">${paymentPlan.monthlyPayment.toFixed(2)}</div>
              </div>
              <div>
                <span className="text-gray-600">Duration:</span>
                <div className="font-bold text-lg">{paymentPlan.months} months</div>
              </div>
              <div>
                <span className="text-gray-600">Interest Rate:</span>
                <div className="font-bold text-lg">{paymentPlan.interestRate}%</div>
              </div>
              <div>
                <span className="text-gray-600">First Payment:</span>
                <div className="font-bold text-lg">{paymentPlan.firstDue}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const FinancialAssistance = () => {
    useEffect(() => {
      findAssistancePrograms();
    }, []);

    return (
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-orange-50 to-red-50 p-6 rounded-xl">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <Users className="mr-2" /> Financial Assistance Finder
          </h3>
          
          <div className="bg-white p-4 rounded-lg border border-gray-200 mb-4">
            <h4 className="font-semibold mb-3">Quick Eligibility Check</h4>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Annual Household Income</label>
                <input type="number" placeholder="$" className="w-full p-2 border rounded-lg" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Household Size</label>
                <input type="number" placeholder="Number of people" className="w-full p-2 border rounded-lg" />
              </div>
            </div>
          </div>

          <div className="space-y-3">
            {assistancePrograms.map(program => (
              <div key={program.id} className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-semibold">{program.name}</h4>
                    <div className="text-sm text-gray-600 mt-1">
                      <div>Eligibility: {program.eligibility}</div>
                      <div>Coverage: {program.coverage}</div>
                    </div>
                  </div>
                  <div className="ml-4">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
                      ${program.status === 'likely' ? 'bg-green-100 text-green-800' : 
                        program.status === 'possible' ? 'bg-yellow-100 text-yellow-800' :
                        program.status === 'available' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'}`}>
                      {program.status === 'likely' ? 'Likely Eligible' :
                       program.status === 'possible' ? 'Possibly Eligible' :
                       program.status === 'available' ? 'Available' : 'Check Eligibility'}
                    </span>
                    <button className="mt-2 w-full text-sm px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700">
                      Apply Now
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-indigo-50 rounded-lg">
            <h4 className="font-semibold mb-2 flex items-center">
              <Info className="mr-2" size={20} /> Application Tips
            </h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• Gather all income documentation before applying</li>
              <li>• Apply for multiple programs to maximize coverage</li>
              <li>• Follow up on applications within 7-10 days</li>
              <li>• Keep copies of all submitted documents</li>
              <li>• Appeal denials with additional documentation</li>
            </ul>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">Healthcare Financial Navigator</h1>
          <p className="text-blue-100">Your autonomous guide to healthcare costs and financial assistance</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="flex flex-wrap border-b">
            {[
              { id: 'estimator', label: 'Cost Estimator', icon: Calculator },
              { id: 'insurance', label: 'Insurance', icon: Shield },
              { id: 'bills', label: 'Bills', icon: FileText },
              { id: 'assistance', label: 'Financial Aid', icon: Users }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-6 py-3 font-medium transition-colors
                  ${activeTab === tab.id 
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50' 
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'}`}
              >
                <tab.icon size={18} className="mr-2" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="transition-all">
          {activeTab === 'estimator' && <CostEstimator />}
          {activeTab === 'insurance' && <InsuranceNavigator />}
          {activeTab === 'bills' && <BillManager />}
          {activeTab === 'assistance' && <FinancialAssistance />}
        </div>

        <div className="mt-8 grid md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600">Estimated Savings</div>
                <div className="text-2xl font-bold text-green-600">$4,230</div>
              </div>
              <TrendingUp className="text-green-600" size={24} />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600">Bills Under Review</div>
                <div className="text-2xl font-bold text-blue-600">3</div>
              </div>
              <FileText className="text-blue-600" size={24} />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600">Assistance Available</div>
                <div className="text-2xl font-bold text-purple-600">5 Programs</div>
              </div>
              <Users className="text-purple-600" size={24} />
            </div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">
          <h3 className="font-bold mb-2">AI-Powered Recommendations</h3>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start">
              <Check className="mr-2 mt-0.5" size={16} />
              <span>Your upcoming MRI can save $1,200 by using Regional Imaging Center</span>
            </li>
            <li className="flex items-start">
              <Check className="mr-2 mt-0.5" size={16} />
              <span>You qualify for the hospital's financial assistance program - apply today</span>
            </li>
            <li className="flex items-start">
              <Check className="mr-2 mt-0.5" size={16} />
              <span>Negotiating your emergency room bill could reduce it by 30-40%</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default HealthcareFinancialNavigator;