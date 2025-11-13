// api/client.js - Frontend API client for connecting to backend

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

class HealthcareAPI {
  constructor() {
    this.token = localStorage.getItem('authToken');
  }

  // Helper method for API calls
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

  // Set auth token
  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  }

  // ========== AUTH ENDPOINTS ==========
  async register(userData) {
    const response = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    this.setToken(response.token);
    return response;
  }

  async login(email, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(response.token);
    return response;
  }

  logout() {
    this.setToken(null);
  }

  // ========== USER ENDPOINTS ==========
  async getProfile() {
    return this.request('/user/profile');
  }

  async updateProfile(updates) {
    return this.request('/user/profile', {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async updateInsurance(insuranceData) {
    return this.request('/user/insurance', {
      method: 'PUT',
      body: JSON.stringify(insuranceData),
    });
  }

  // ========== PROCEDURES ENDPOINTS ==========
  async searchProcedures(query) {
    return this.request(`/procedures/search?q=${encodeURIComponent(query)}`);
  }

  async getProcedureDetails(cptCode) {
    return this.request(`/procedures/${cptCode}`);
  }

  // ========== COST ESTIMATION ENDPOINTS ==========
  async calculateOutOfPocket(procedureCode, providerId, totalCost) {
    return this.request('/estimate/calculate', {
      method: 'POST',
      body: JSON.stringify({ procedureCode, providerId, totalCost }),
    });
  }

  async getProviderEstimates(procedureCode, lat, lon, radius = 25) {
    const params = new URLSearchParams({ lat, lon, radius });
    return this.request(`/estimate/providers/${procedureCode}?${params}`);
  }

  // ========== BILLS ENDPOINTS ==========
  async getBills() {
    return this.request('/bills');
  }

  async createBill(billData) {
    return this.request('/bills', {
      method: 'POST',
      body: JSON.stringify(billData),
    });
  }

  async updateBill(billId, updates) {
    return this.request(`/bills/${billId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
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

  // ========== FINANCIAL ASSISTANCE ENDPOINTS ==========
  async findEligibleAssistance() {
    return this.request('/assistance/eligible');
  }

  // ========== EXTERNAL APIS ==========
  async getDrugPrices(drugName, dosage, quantity) {
    const params = new URLSearchParams({ drugName, dosage, quantity });
    return this.request(`/drugs/price?${params}`);
  }

  async verifyInsurance(memberId, dateOfBirth, provider) {
    return this.request('/insurance/verify', {
      method: 'POST',
      body: JSON.stringify({ memberId, dateOfBirth, provider }),
    });
  }

  // ========== ANALYTICS ==========
  async getSpendingAnalytics() {
    return this.request('/analytics/spending');
  }
}

// Create singleton instance
const api = new HealthcareAPI();
export default api;

// ============================================
// React Hooks for API Integration
// ============================================

import { useState, useEffect } from 'react';

// Hook for authenticated user
export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (api.token) {
          const profile = await api.getProfile();
          setUser(profile);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        api.logout();
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const login = async (email, password) => {
    const response = await api.login(email, password);
    setUser(response.user);
    return response;
  };

  const logout = () => {
    api.logout();
    setUser(null);
  };

  return { user, loading, login, logout, isAuthenticated: !!user };
};

// Hook for procedures search
export const useProcedureSearch = (searchTerm) => {
  const [procedures, setProcedures] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const search = async () => {
      if (!searchTerm) {
        setProcedures([]);
        return;
      }

      setLoading(true);
      try {
        const results = await api.searchProcedures(searchTerm);
        setProcedures(results);
      } catch (error) {
        console.error('Procedure search failed:', error);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(search, 300);
    return () => clearTimeout(debounce);
  }, [searchTerm]);

  return { procedures, loading };
};

// Hook for bills management
export const useBills = () => {
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchBills = async () => {
    try {
      const data = await api.getBills();
      setBills(data);
    } catch (error) {
      console.error('Failed to fetch bills:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBills();
  }, []);

  const negotiateBill = async (billId) => {
    try {
      const updatedBill = await api.negotiateBill(billId);
      setBills(bills.map(b => b._id === billId ? updatedBill : b));
      return updatedBill;
    } catch (error) {
      console.error('Failed to negotiate bill:', error);
      throw error;
    }
  };

  const createPaymentPlan = async (billId, months) => {
    try {
      const updatedBill = await api.createPaymentPlan(billId, months);
      setBills(bills.map(b => b._id === billId ? updatedBill : b));
      return updatedBill;
    } catch (error) {
      console.error('Failed to create payment plan:', error);
      throw error;
    }
  };

  return { bills, loading, negotiateBill, createPaymentPlan, refetch: fetchBills };
};

// Hook for cost estimation
export const useCostEstimate = () => {
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);

  const calculateEstimate = async (procedureCode, providerId, totalCost) => {
    setLoading(true);
    try {
      const data = await api.calculateOutOfPocket(procedureCode, providerId, totalCost);
      setEstimate(data);
      return data;
    } catch (error) {
      console.error('Failed to calculate estimate:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return { estimate, loading, calculateEstimate };
};

// Hook for financial assistance
export const useFinancialAssistance = () => {
  const [programs, setPrograms] = useState([]);
  const [fplPercentage, setFplPercentage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPrograms = async () => {
      try {
        const data = await api.findEligibleAssistance();
        setPrograms(data.programs);
        setFplPercentage(data.fplPercentage);
      } catch (error) {
        console.error('Failed to fetch assistance programs:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchPrograms();
  }, []);

  return { programs, fplPercentage, loading };
};

// ============================================
// Updated React Component with API Integration
// ============================================

// Example: Updated LoginComponent
export const LoginComponent = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">Email</label>
              <input
                id="email"
                type="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">Password</label>
              <input
                id="password"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>
          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Sign in
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};