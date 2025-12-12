import React, { useState, useRef } from 'react';
import { Upload, X, AlertTriangle, CheckCircle, FileText, Loader2, ArrowRight, ShieldCheck } from 'lucide-react';
import { analyzeMedicalBill } from '../services/geminiService';
import { AnalyzedBill } from '../types';

interface BillAnalyzerProps {
  onBillAnalyzed: (bill: AnalyzedBill) => void;
}

export const BillAnalyzer: React.FC<BillAnalyzerProps> = ({ onBillAnalyzed }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const processFile = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError("Please upload an image (JPG, PNG). PDF support coming soon.");
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const base64 = (reader.result as string).split(',')[1];
        const result = await analyzeMedicalBill(base64);
        onBillAnalyzed(result);
      } catch (err) {
        setError("Failed to analyze bill. Please ensure the image is clear and try again.");
      } finally {
        setIsAnalyzing(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Bill Analysis Engine</h2>
          <p className="text-gray-500 mt-1">Upload your medical bills to detect errors and find savings.</p>
        </div>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all ${
          isDragging 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-primary-400 bg-white'
        }`}
      >
        <div className="max-w-md mx-auto flex flex-col items-center">
          <div className="w-16 h-16 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center mb-4">
            {isAnalyzing ? <Loader2 className="animate-spin" size={32} /> : <Upload size={32} />}
          </div>
          
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {isAnalyzing ? "Analyzing Document..." : "Upload Medical Bill"}
          </h3>
          
          <p className="text-gray-500 mb-6">
            {isAnalyzing 
              ? "Gemini is extracting line items, CPT codes, and checking for errors." 
              : "Drag and drop your bill image here, or browse files."}
          </p>

          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileSelect} 
            className="hidden" 
            accept="image/*"
          />
          
          <button 
            disabled={isAnalyzing}
            onClick={() => fileInputRef.current?.click()}
            className="bg-primary-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {isAnalyzing ? "Processing..." : "Select File"}
          </button>
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg flex items-center gap-2">
              <AlertTriangle size={16} />
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Feature capabilities */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { icon: AlertTriangle, title: "Error Detection", desc: "Identifies upcoding, unbundling, and duplicates." },
          { icon: FileText, title: "CPT Code Analysis", desc: "Verifies procedure codes against descriptions." },
          { icon: ShieldCheck, title: "Fair Price Check", desc: "Compares charges to regional averages." }
        ].map((item, idx) => (
            <div key={idx} className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-start gap-3">
                <div className="p-2 bg-gray-100 rounded-lg text-gray-600">
                    <item.icon size={20} />
                </div>
                <div>
                    <h4 className="font-semibold text-gray-900 text-sm">{item.title}</h4>
                    <p className="text-xs text-gray-500 mt-1">{item.desc}</p>
                </div>
            </div>
        ))}
      </div>
    </div>
  );
};

export const BillResults: React.FC<{ bill: AnalyzedBill, onReset: () => void }> = ({ bill, onReset }) => {
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
             <div className="flex items-center justify-between">
                <button onClick={onReset} className="text-gray-500 hover:text-gray-800 flex items-center gap-2 text-sm font-medium">
                    <ArrowRight className="rotate-180" size={16} /> Back to Upload
                </button>
                <div className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-bold uppercase">Analyzed</span>
                </div>
             </div>

             <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Bill Info */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <div className="p-6 border-b border-gray-100 flex justify-between items-start">
                            <div>
                                <h3 className="text-xl font-bold text-gray-900">{bill.providerName}</h3>
                                <p className="text-gray-500 text-sm">Service Date: {bill.date}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm text-gray-500">Total Billed</p>
                                <p className="text-2xl font-bold text-gray-900">${bill.totalAmount.toLocaleString()}</p>
                            </div>
                        </div>
                        <div className="p-6">
                            <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">Line Items</h4>
                            <div className="space-y-4">
                                {bill.lineItems.map((item, idx) => (
                                    <div key={idx} className={`flex items-start justify-between p-3 rounded-lg ${item.flagged ? 'bg-red-50 border border-red-100' : 'bg-gray-50'}`}>
                                        <div>
                                            <p className="font-medium text-gray-900">{item.description}</p>
                                            <div className="flex items-center gap-2 mt-1">
                                                {item.cptCode && <span className="text-xs bg-gray-200 px-2 py-0.5 rounded text-gray-600 font-mono">{item.cptCode}</span>}
                                                {item.flagged && <span className="text-xs text-red-600 font-medium flex items-center gap-1"><AlertTriangle size={12}/> {item.issueDescription}</span>}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-medium">${item.charge.toLocaleString()}</p>
                                            {item.expectedCost && (
                                                <p className="text-xs text-gray-500">Avg: ${item.expectedCost.toLocaleString()}</p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Analysis Sidebar */}
                <div className="space-y-6">
                    <div className="bg-gradient-to-br from-primary-600 to-primary-800 rounded-xl p-6 text-white shadow-lg">
                        <p className="text-primary-100 font-medium mb-1">Potential Savings</p>
                        <h3 className="text-3xl font-bold mb-4">${bill.potentialSavings.toLocaleString()}</h3>
                        <p className="text-sm text-primary-100 opacity-90 leading-relaxed">
                            {bill.summary}
                        </p>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                         <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <AlertTriangle className="text-amber-500" size={18} />
                            Detected Issues
                         </h4>
                         <ul className="space-y-3">
                            {bill.issues.map((issue, i) => (
                                <li key={i} className="flex gap-3 text-sm text-gray-700">
                                    <span className="w-1.5 h-1.5 bg-red-500 rounded-full mt-1.5 shrink-0"></span>
                                    {issue}
                                </li>
                            ))}
                         </ul>
                    </div>
                </div>
             </div>
        </div>
    )
}