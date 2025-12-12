export enum View {
  DASHBOARD = 'DASHBOARD',
  BILL_UPLOAD = 'BILL_UPLOAD',
  NAVIGATION_PLAN = 'NAVIGATION_PLAN',
  ASSISTANCE = 'ASSISTANCE',
  CHAT = 'CHAT'
}

export interface BillLineItem {
  description: string;
  cptCode?: string;
  charge: number;
  expectedCost?: number;
  flagged?: boolean;
  issueDescription?: string;
}

export interface AnalyzedBill {
  id: string;
  providerName: string;
  date: string;
  totalAmount: number;
  confidenceScore: number;
  lineItems: BillLineItem[];
  summary: string;
  potentialSavings: number;
  status: 'pending' | 'analyzed' | 'disputed';
  issues: string[];
}

export interface NavigationAction {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  estimatedSavings: number;
  status: 'pending' | 'completed';
  category: 'bill_review' | 'negotiate' | 'assistance';
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'model';
  text: string;
  timestamp: Date;
}
