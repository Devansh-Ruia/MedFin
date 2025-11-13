import React, { useState, useEffect } from 'react';
import { Calculator, Shield, DollarSign, FileText, Search, AlertCircle, TrendingUp, Users, ChevronRight, Check, X, Info, Calendar, CreditCard, Building2, Phone, Mail, MapPin, LogOut, User } from 'lucide-react';

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// API Client
class HealthcareAPI {
  constructor() {
    this.token = localStorage.getItem('authToken');
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    if (this.token) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'API request failed');
    }

    return data;
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  }

  async login(email, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(response.token);
    return response;
  }

  async register(userData) {
    const response = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    this.setToken(response.token);
    return response;
  }

  logout() {
    this.setToken(null);
  }

  async searchProcedures(query) {
    return this.request(`/procedures/search?q=${encodeURIComponent(query)}`);
  }

  async calculateOutOfPocket(procedureCode, providerId, totalCost) {
    return this.request('/estimate/calculate', {
      method: 'POST',
      body: JSON.stringify({ procedureCode, providerId, totalCost }),
    });
  }

  async getBills() {
    return this.request('/bills');
  }

  async negotiateBill(billId) {
    return this.request(`/bills/${billId}/negotiate`, {
      method: 'POST',
    });
  }

  async createPaymentPlan(billId, months) {
    return this.request(`/bills/${billId}/payment-plan`, {
      method: 'POST',
      body: JSON.stringify({ months }),
    });
  }

  async findEligibleAssistance() {
    return this.request('/assistance/eligible');
  }

  async getProfile() {
    return this.request('/user/profile');
  }

  async updateInsurance(insuranceData) {
    return this.request('/user/insurance', {
      method: 'PUT',
      body: JSON.stringify(insuranceData),
    });
  }
}

const api = new HealthcareAPI();

// Main Application Component
const HealthcareFinancialNavigator = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('estimator');
  const [showLogin, setShowLogin] = useState(true);
  
  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (api.token) {
        try {
          const profile = await api.getProfile();
          setUser(profile);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Auth check failed:', error);
          api.logout();
        }
      }
    };
    checkAuth();
  }, []);

  // Login Component
  const LoginForm = () => {
    const [email, setEmail] = useState('demo@example.com');
    const [password, setPassword] = useState('password123');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async () => {
      setError('');
      setLoading(true);
      try {
        const response = await api.login(email, password);
        setUser(response.user);
        setIsAuthenticated(true);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    const handleRegister = async () => {
      setError('');
      setLoading(true);
      try {
        const response = await api.register({ email, password, firstName, lastName });
        setUser(response.user);
        setIsAuthenticated(true);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-xl p-8">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">
            Healthcare Financial Navigator
          </h2>
          
          <div className="flex mb-6">
            <button
              onClick={() => setShowLogin(true)}
              className={`flex-1 py-2 text-center font-medium rounded-l-lg ${
                showLogin ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setShowLogin(false)}
              className={`flex-1 py-2 text-center font-medium rounded-r-lg ${
                !showLogin ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
              }`}
            >
              Sign Up
            </button>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4">
              {error}
            </div>
          )}

          <div className="space-y-4">
            {!showLogin && (
              <div className="grid grid-cols-2 gap-4">
                <input
                  type="text"
                  placeholder="First Name"
                  className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
                <input
                  type="text"
                  placeholder="Last Name"
                  className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </div>
            )}
            
            <input
              type="email"
              placeholder="Email"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            
            <input
              type="password"
              placeholder="Password"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            
            <button
              onClick={showLogin ? handleLogin : handleRegister}
              disabled={loading}
              className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Loading...' : showLogin ? 'Sign In' : 'Create Account'}
            </button>
          </div>

          {showLogin && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <strong>Demo Account:</strong><br />
                Email: demo@example.com<br />
                Password: password123
              </p>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Main Dashboard
  const Dashboard = () => {
    const [procedureSearch, setProcedureSearch] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedProcedure, setSelectedProcedure] = useState(null);
    const [bills, setBills] = useState([]);
    const [assistancePrograms, setAssistancePrograms] = useState([]);
    const [estimate, setEstimate] = useState(null);
    const [loading, setLoading] = useState(false);

    // Search procedures
    useEffect(() => {
      const searchProcedures = async () => {
        if (!procedureSearch) {
          setSearchResults([]);
          return;
        }

        try {
          const results = await api.searchProcedures(procedureSearch);
          setSearchResults(results);
        } catch (error) {
          console.error('Search failed:', error);
        }
      };

      const debounce = setTimeout(searchProcedures, 300);
      return () => clearTimeout(debounce);
    }, [procedureSearch]);

    // Load bills
    useEffect(() => {
      const loadBills = async () => {
        try {
          const userBills = await api.getBills();
          setBills(userBills);
        } catch (error) {
          console.error('Failed to load bills:', error);
        }
      };
      
      if (activeTab === 'bills') {
        loadBills();
      }
    }, [activeTab]);

    // Load assistance programs
    useEffect(() => {
      const loadAssistance = async () => {
        try {
          const data = await api.findEligibleAssistance();
          setAssistancePrograms(data.programs || []);
        } catch (error) {
          console.error('Failed to load assistance programs:', error);
        }
      };
      
      if (activeTab === 'assistance') {
        loadAssistance();
      }
    }, [activeTab]);

    const calculateEstimate = async (procedure) => {
      setLoading(true);
      try {
        const estimate = await api.calculateOutOfPocket(
          procedure.cptCode,
          'provider-id',
          procedure.averageCost
        );
        setEstimate(estimate);
      } catch (error) {
        console.error('Failed to calculate estimate:', error);
      } finally {
        setLoading(false);
      }
    };

    const negotiateBill = async (billId) => {
      try {
        const updated = await api.negotiateBill(billId);
        setBills(bills.map(b => b._id === billId ? updated : b));
      } catch (error) {
        console.error('Failed to negotiate:', error);
      }
    };

    const createPaymentPlan = async (billId, months = 12) => {
      try {
        const updated = await api.createPaymentPlan(billId, months);
        setBills(bills.map(b => b._id === billId ? updated : b));
      } catch (error) {
        console.error('Failed to create payment plan:', error);
      }
    };

    const handleLogout = () => {
      api.logout();
      setIsAuthenticated(false);
      setUser(null);
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

            {searchResults.length > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 max-h-48 overflow-y-auto">
                {searchResults.map(proc => (
                  <div
                    key={proc._id}
                    className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                    onClick={() => {
                      setSelectedProcedure(proc);
                      setProcedureSearch(proc.name);
                      calculateEstimate(proc);
                    }}
                  >
                    <div className="font-medium">{proc.name}</div>
                    <div className="text-sm text-gray-500">
                      CPT: {proc.cptCode} | Avg: ${proc.averageCost?.toLocaleString() || 'N/A'}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {selectedProcedure && estimate && (
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-lg mb-4">{selectedProcedure.name}</h4>
                
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <div className="text-sm text-gray-600">Total Cost</div>
                    <div className="text-2xl font-bold">${estimate.totalCost?.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Your Cost</div>
                    <div className="text-2xl font-bold text-blue-600">
                      ${estimate.totalOutOfPocket?.toLocaleString()}
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                  <h5 className="font-semibold mb-2">Cost Breakdown</h5>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Deductible:</span>
                      <span>${estimate.deductiblePortion?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Coinsurance:</span>
                      <span>${estimate.coinsurancePortion?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between font-semibold">
                      <span>Insurance Pays:</span>
                      <span className="text-green-600">${estimate.insurancePays?.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );

    const BillManager = () => (
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-xl">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <FileText className="mr-2" /> Medical Bills
          </h3>
          
          {bills.length === 0 ? (
            <div className="bg-white p-8 rounded-lg text-center text-gray-500">
              No bills found. Bills will appear here when you add them.
            </div>
          ) : (
            <div className="space-y-4">
              {bills.map(bill => (
                <div key={bill._id} className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-semibold">{bill.provider}</h4>
                      <div className="text-sm text-gray-500 mt-1">
                        Due: {new Date(bill.dueDate).toLocaleDateString()}
                      </div>
                      <div className="mt-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                          ${bill.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                            bill.status === 'negotiating' ? 'bg-purple-100 text-purple-800' :
                            bill.status === 'payment_plan' ? 'bg-blue-100 text-blue-800' :
                            'bg-green-100 text-green-800'}`}>
                          {bill.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">
                        ${(bill.negotiatedAmount || bill.currentAmount || bill.originalAmount)?.toLocaleString()}
                      </div>
                      {bill.negotiatedAmount && (
                        <div className="text-sm text-green-600">
                          Saved ${(bill.originalAmount - bill.negotiatedAmount).toLocaleString()}
                        </div>
                      )}
                      <div className="mt-2 space-x-2">
                        <button
                          onClick={() => negotiateBill(bill._id)}
                          className="text-sm px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700"
                        >
                          Negotiate
                        </button>
                        <button 
                          onClick={() => createPaymentPlan(bill._id)}
                          className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Payment Plan
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );

    const FinancialAssistance = () => (
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-orange-50 to-red-50 p-6 rounded-xl">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <Users className="mr-2" /> Financial Assistance Programs
          </h3>
          
          {assistancePrograms.length === 0 ? (
            <div className="bg-white p-8 rounded-lg text-center text-gray-500">
              Update your profile information to see eligible assistance programs.
            </div>
          ) : (
            <div className="space-y-3">
              {assistancePrograms.map(program => (
                <div key={program._id} className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="font-semibold">{program.name}</h4>
                      <div className="text-sm text-gray-600 mt-1">
                        {program.description || 'Financial assistance program'}
                      </div>
                      <div className="text-sm text-blue-600 mt-1">
                        {program.estimatedBenefit}
                      </div>
                    </div>
                    <div className="ml-4">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
                        ${program.likelihood === 'likely' ? 'bg-green-100 text-green-800' : 
                          program.likelihood === 'possible' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'}`}>
                        {program.likelihood === 'likely' ? 'Likely Eligible' :
                         program.likelihood === 'possible' ? 'Possibly Eligible' : 'Check Eligibility'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );

    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-6">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold mb-2">Healthcare Financial Navigator</h1>
              <p className="text-blue-100">Welcome back, {user?.profile?.firstName || user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition"
            >
              <LogOut className="mr-2" size={18} />
              Logout
            </button>
          </div>
        </div>

        <div className="max-w-7xl mx-auto p-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
            <div className="flex flex-wrap border-b">
              {[
                { id: 'estimator', label: 'Cost Estimator', icon: Calculator },
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
            {activeTab === 'bills' && <BillManager />}
            {activeTab === 'assistance' && <FinancialAssistance />}
          </div>
        </div>
      </div>
    );
  };

  return isAuthenticated ? <Dashboard /> : <LoginForm />;
};

export default HealthcareFinancialNavigator;