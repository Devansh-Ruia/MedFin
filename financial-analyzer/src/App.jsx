import React, { useState, useCallback } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Upload, TrendingUp, Shield, DollarSign, BarChart2, FileText, AlertTriangle, CheckCircle, Circle } from 'lucide-react';
import Papa from 'papaparse';
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

export default function FinancialAnalyzer() {
  const [data, setData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [dataType, setDataType] = useState('financial');

  const analyzeFinancialData = (rows) => {
    const numeric = {};
    const categorical = {};
    
    if (rows.length === 0) return null;
    
    const headers = Object.keys(rows[0]);
    
    headers.forEach(h => {
      const vals = rows.map(r => r[h]).filter(v => v !== null && v !== undefined && v !== '');
      const numVals = vals.map(v => parseFloat(String(v).replace(/[$,]/g, ''))).filter(n => !isNaN(n));
      
      if (numVals.length > vals.length * 0.5) {
        numeric[h] = {
          values: numVals,
          sum: numVals.reduce((a, b) => a + b, 0),
          avg: numVals.reduce((a, b) => a + b, 0) / numVals.length,
          min: Math.min(...numVals),
          max: Math.max(...numVals),
          count: numVals.length
        };
      } else {
        const counts = {};
        vals.forEach(v => { counts[v] = (counts[v] || 0) + 1; });
        categorical[h] = counts;
      }
    });

    const timeFields = headers.filter(h => /date|time|year|month|period/i.test(h));
    let timeSeries = null;
    
    if (timeFields.length > 0 && Object.keys(numeric).length > 0) {
      const timeField = timeFields[0];
      const valueField = Object.keys(numeric)[0];
      timeSeries = rows.slice(0, 20).map(r => ({
        period: r[timeField],
        value: parseFloat(String(r[valueField]).replace(/[$,]/g, '')) || 0
      })).filter(d => d.period);
    }

    return { numeric, categorical, timeSeries, totalRows: rows.length, headers };
  };

  const analyzeInsuranceData = (rows) => {
    const base = analyzeFinancialData(rows);
    if (!base) return null;

    const riskIndicators = {};
    const claimPatterns = {};
    
    const riskFields = Object.keys(rows[0]).filter(h => /risk|score|rating|class|tier/i.test(h));
    const claimFields = Object.keys(rows[0]).filter(h => /claim|loss|damage|incident/i.test(h));
    const premiumFields = Object.keys(rows[0]).filter(h => /premium|price|cost|amount/i.test(h));

    riskFields.forEach(f => {
      const counts = {};
      rows.forEach(r => {
        const v = r[f];
        if (v) counts[v] = (counts[v] || 0) + 1;
      });
      riskIndicators[f] = counts;
    });

    if (claimFields.length > 0 && premiumFields.length > 0) {
      const claimField = claimFields[0];
      const premiumField = premiumFields[0];
      let totalClaims = 0, totalPremiums = 0;
      
      rows.forEach(r => {
        const claim = parseFloat(String(r[claimField]).replace(/[$,]/g, '')) || 0;
        const premium = parseFloat(String(r[premiumField]).replace(/[$,]/g, '')) || 0;
        totalClaims += claim;
        totalPremiums += premium;
      });
      
      claimPatterns.lossRatio = totalPremiums > 0 ? (totalClaims / totalPremiums * 100).toFixed(2) : 0;
      claimPatterns.totalClaims = totalClaims;
      claimPatterns.totalPremiums = totalPremiums;
    }

    return { ...base, riskIndicators, claimPatterns, isInsurance: true };
  };

  const handleFile = useCallback((e) => {
    const file = e.target.files[0];
    if (!file) return;

    Papa.parse(file, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => {
        setData(results.data);
        const analyzed = dataType === 'insurance' 
          ? analyzeInsuranceData(results.data)
          : analyzeFinancialData(results.data);
        setAnalysis(analyzed);
      }
    });
  }, [dataType]);

  const formatCurrency = (n) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
  const formatNumber = (n) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(n);

  const renderOverview = () => {
    if (!analysis) return null;
    const numericKeys = Object.keys(analysis.numeric);
    
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 text-blue-600 mb-1">
              <FileText size={18} />
              <span className="text-sm font-medium">Records</span>
            </div>
            <p className="text-2xl font-bold text-blue-900">{formatNumber(analysis.totalRows)}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 text-green-600 mb-1">
              <BarChart2 size={18} />
              <span className="text-sm font-medium">Metrics</span>
            </div>
            <p className="text-2xl font-bold text-green-900">{numericKeys.length}</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 text-purple-600 mb-1">
              <Circle size={18} />
              <span className="text-sm font-medium">Categories</span>
            </div>
            <p className="text-2xl font-bold text-purple-900">{Object.keys(analysis.categorical).length}</p>
          </div>
          <div className="bg-amber-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 text-amber-600 mb-1">
              <TrendingUp size={18} />
              <span className="text-sm font-medium">Fields</span>
            </div>
            <p className="text-2xl font-bold text-amber-900">{analysis.headers.length}</p>
          </div>
        </div>

        {numericKeys.length > 0 && (
          <div className="bg-white border rounded-lg p-4">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <DollarSign size={18} className="text-green-600" />
              Financial Metrics Summary
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-3">Metric</th>
                    <th className="text-right py-2 px-3">Total</th>
                    <th className="text-right py-2 px-3">Average</th>
                    <th className="text-right py-2 px-3">Min</th>
                    <th className="text-right py-2 px-3">Max</th>
                  </tr>
                </thead>
                <tbody>
                  {numericKeys.slice(0, 6).map(key => (
                    <tr key={key} className="border-b hover:bg-gray-50">
                      <td className="py-2 px-3 font-medium">{key}</td>
                      <td className="text-right py-2 px-3">{formatNumber(analysis.numeric[key].sum)}</td>
                      <td className="text-right py-2 px-3">{formatNumber(analysis.numeric[key].avg)}</td>
                      <td className="text-right py-2 px-3">{formatNumber(analysis.numeric[key].min)}</td>
                      <td className="text-right py-2 px-3">{formatNumber(analysis.numeric[key].max)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {analysis.isInsurance && analysis.claimPatterns.lossRatio && (
          <div className="bg-white border rounded-lg p-4">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Shield size={18} className="text-blue-600" />
              Insurance Metrics
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Loss Ratio</p>
                <p className={`text-2xl font-bold ${parseFloat(analysis.claimPatterns.lossRatio) > 70 ? 'text-red-600' : 'text-green-600'}`}>
                  {analysis.claimPatterns.lossRatio}%
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Total Premiums</p>
                <p className="text-2xl font-bold text-blue-600">{formatCurrency(analysis.claimPatterns.totalPremiums)}</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">Total Claims</p>
                <p className="text-2xl font-bold text-amber-600">{formatCurrency(analysis.claimPatterns.totalClaims)}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderCharts = () => {
    if (!analysis) return null;
    
    const numericKeys = Object.keys(analysis.numeric);
    const catKeys = Object.keys(analysis.categorical);
    
    const barData = numericKeys.slice(0, 5).map(key => ({
      name: key.length > 12 ? key.slice(0, 12) + '...' : key,
      total: analysis.numeric[key].sum,
      average: analysis.numeric[key].avg
    }));

    const pieData = catKeys.length > 0 
      ? Object.entries(analysis.categorical[catKeys[0]]).slice(0, 8).map(([name, value]) => ({ name, value }))
      : [];

    return (
      <div className="space-y-6">
        {barData.length > 0 && (
          <div className="bg-white border rounded-lg p-4">
            <h3 className="font-semibold mb-4">Numeric Fields Comparison</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v) => formatNumber(v)} />
                <Legend />
                <Bar dataKey="total" fill="#3b82f6" name="Total" />
                <Bar dataKey="average" fill="#10b981" name="Average" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {analysis.timeSeries && analysis.timeSeries.length > 0 && (
          <div className="bg-white border rounded-lg p-4">
            <h3 className="font-semibold mb-4">Trend Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analysis.timeSeries}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v) => formatNumber(v)} />
                <Line type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {pieData.length > 0 && (
          <div className="bg-white border rounded-lg p-4">
            <h3 className="font-semibold mb-4">Distribution: {catKeys[0]}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    );
  };

  const renderRiskAnalysis = () => {
    if (!analysis || !analysis.isInsurance) {
      return (
        <div className="text-center py-12 text-gray-500">
          <Shield size={48} className="mx-auto mb-4 opacity-50" />
          <p>Risk analysis is available for insurance data.</p>
          <p className="text-sm">Select "Insurance Data" and upload a file with risk-related fields.</p>
        </div>
      );
    }

    const riskKeys = Object.keys(analysis.riskIndicators);
    
    return (
      <div className="space-y-6">
        {riskKeys.map(key => {
          const chartData = Object.entries(analysis.riskIndicators[key]).map(([name, value]) => ({ name, value }));
          return (
            <div key={key} className="bg-white border rounded-lg p-4">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <AlertTriangle size={18} className="text-amber-500" />
                Risk Distribution: {key}
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={chartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#f59e0b" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          );
        })}
        
        {riskKeys.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No risk-related fields detected in the data.</p>
            <p className="text-sm">Fields containing "risk", "score", "rating", "class", or "tier" will be analyzed.</p>
          </div>
        )}
      </div>
    );
  };

  const renderDataTable = () => {
    if (!data || data.length === 0) return null;
    const headers = Object.keys(data[0]);
    
    return (
      <div className="bg-white border rounded-lg overflow-hidden">
        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 sticky top-0">
              <tr>
                {headers.map(h => (
                  <th key={h} className="text-left py-2 px-3 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 50).map((row, i) => (
                <tr key={i} className="border-t hover:bg-gray-50">
                  {headers.map(h => (
                    <td key={h} className="py-2 px-3 whitespace-nowrap">{row[h]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.length > 50 && (
          <p className="text-center py-2 text-sm text-gray-500 bg-gray-50">Showing first 50 of {data.length} rows</p>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-100 rounded-lg">
              <TrendingUp className="text-blue-600" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Financial & Insurance Data Analyzer</h1>
              <p className="text-sm text-gray-500">Upload CSV files to analyze financial metrics and insurance data</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex gap-2">
              <button
                onClick={() => setDataType('financial')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${dataType === 'financial' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
              >
                <DollarSign size={16} className="inline mr-1" />
                Financial Data
              </button>
              <button
                onClick={() => setDataType('insurance')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${dataType === 'insurance' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
              >
                <Shield size={16} className="inline mr-1" />
                Insurance Data
              </button>
            </div>
            
            <label className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg cursor-pointer hover:bg-green-700 transition">
              <Upload size={18} />
              <span className="text-sm font-medium">Upload CSV</span>
              <input type="file" accept=".csv" onChange={handleFile} className="hidden" />
            </label>
            
            {data && (
              <span className="flex items-center gap-1 text-sm text-green-600">
                <CheckCircle size={16} />
                {data.length} records loaded
              </span>
            )}
          </div>
        </div>

        {analysis && (
          <>
            <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
              {['overview', 'charts', 'risk', 'data'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition ${activeTab === tab ? 'bg-blue-600 text-white' : 'bg-white border text-gray-700 hover:bg-gray-50'}`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {activeTab === 'overview' && renderOverview()}
            {activeTab === 'charts' && renderCharts()}
            {activeTab === 'risk' && renderRiskAnalysis()}
            {activeTab === 'data' && renderDataTable()}
          </>
        )}

        {!analysis && (
          <div className="bg-white rounded-xl border p-12 text-center">
            <Upload size={48} className="mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-700 mb-2">No Data Loaded</h3>
            <p className="text-gray-500 mb-4">Upload a CSV file to start analyzing your financial or insurance data</p>
            <div className="text-sm text-gray-400 max-w-md mx-auto">
              <p className="mb-2">Supported data includes:</p>
              <p>• Transactions, revenue, expenses, budgets</p>
              <p>• Insurance policies, claims, premiums, risk scores</p>
              <p>• Time series financial data with dates</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}