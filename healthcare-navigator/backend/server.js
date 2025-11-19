// server.js - Working demo server without MongoDB
const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// In-memory data store
const dataStore = {
  users: [],
  bills: [],
  procedures: [
    { _id: '1', name: 'MRI Brain w/o Contrast', cptCode: '70551', category: 'Imaging', averageCost: 3000, costRange: { low: 1500, high: 5000 }},
    { _id: '2', name: 'CT Abdomen w/Contrast', cptCode: '74160', category: 'Imaging', averageCost: 2000, costRange: { low: 800, high: 3500 }},
    { _id: '3', name: 'Colonoscopy', cptCode: '45380', category: 'Procedure', averageCost: 3500, costRange: { low: 2000, high: 5000 }},
    { _id: '4', name: 'Knee Replacement', cptCode: '27447', category: 'Surgery', averageCost: 35000, costRange: { low: 25000, high: 50000 }},
    { _id: '5', name: 'Appendectomy', cptCode: '44970', category: 'Surgery', averageCost: 15000, costRange: { low: 10000, high: 25000 }},
    { _id: '6', name: 'X-Ray Chest', cptCode: '71020', category: 'Imaging', averageCost: 400, costRange: { low: 200, high: 600 }},
    { _id: '7', name: 'Physical Therapy', cptCode: '97110', category: 'Therapy', averageCost: 150, costRange: { low: 75, high: 250 }},
    { _id: '8', name: 'Blood Test Panel', cptCode: '80053', category: 'Lab', averageCost: 200, costRange: { low: 100, high: 400 }},
    { _id: '9', name: 'Ultrasound', cptCode: '76700', category: 'Imaging', averageCost: 500, costRange: { low: 300, high: 800 }},
    { _id: '10', name: 'EKG', cptCode: '93000', category: 'Cardiac', averageCost: 250, costRange: { low: 150, high: 400 }}
  ],
  assistancePrograms: [
    {
      _id: '1',
      name: 'Hospital Financial Assistance',
      type: 'hospital',
      provider: 'City Medical Center',
      description: 'Financial assistance for qualified patients',
      eligibilityCriteria: { fplPercentage: 300, maxIncome: 75000 },
      benefits: { discountPercentage: 100 },
      likelihood: 'likely',
      estimatedBenefit: '100% discount'
    },
    {
      _id: '2',
      name: 'Medicaid',
      type: 'government',
      description: 'State health insurance program',
      eligibilityCriteria: { fplPercentage: 138, maxIncome: 35000 },
      benefits: { discountPercentage: 100 },
      likelihood: 'possible',
      estimatedBenefit: 'Full coverage'
    },
    {
      _id: '3',
      name: 'Charity Care Program',
      type: 'nonprofit',
      description: 'Charity assistance for medical bills',
      eligibilityCriteria: { fplPercentage: 200, maxIncome: 50000 },
      benefits: { discountPercentage: 75 },
      likelihood: 'likely',
      estimatedBenefit: '75% discount'
    },
    {
      _id: '4',
      name: 'Payment Plan Options',
      type: 'hospital',
      description: '0% interest payment plans available',
      eligibilityCriteria: { fplPercentage: 500, maxIncome: 100000 },
      benefits: { discountPercentage: 0 },
      likelihood: 'available',
      estimatedBenefit: '0% interest payment plan'
    }
  ]
};

// Create demo user
const demoPassword = bcrypt.hashSync('password123', 10);
dataStore.users.push({
  _id: 'demo-user',
  email: 'demo@example.com',
  password: demoPassword,
  profile: {
    firstName: 'Demo',
    lastName: 'User',
    householdSize: 2,
    annualIncome: 50000
  },
  insuranceInfo: {
    provider: 'Blue Cross',
    planType: 'PPO',
    deductible: 2000,
    deductibleMet: 500,
    outOfPocketMax: 8000,
    outOfPocketMet: 1000,
    coinsurance: 20
  }
});

// Auth middleware
const authMiddleware = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    if (!token) throw new Error('No token');
    
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
    const user = dataStore.users.find(u => u._id === decoded.userId);
    
    if (!user) throw new Error('User not found');
    
    req.user = user;
    req.userId = user._id;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Please authenticate' });
  }
};

// ============= AUTH ROUTES =============

app.post('/api/auth/register', async (req, res) => {
  try {
    const { email, password, firstName, lastName } = req.body;
    
    if (dataStore.users.find(u => u.email === email)) {
      return res.status(400).json({ error: 'Email already registered' });
    }
    
    const hashedPassword = await bcrypt.hash(password, 10);
    const newUser = {
      _id: `user-${Date.now()}`,
      email,
      password: hashedPassword,
      profile: { 
        firstName: firstName || 'New', 
        lastName: lastName || 'User',
        householdSize: 1,
        annualIncome: 50000
      },
      insuranceInfo: {
        provider: 'Blue Cross',
        planType: 'PPO',
        deductible: 2000,
        deductibleMet: 0,
        outOfPocketMax: 8000,
        outOfPocketMet: 0,
        coinsurance: 20
      }
    };
    
    dataStore.users.push(newUser);
    
    const token = jwt.sign(
      { userId: newUser._id },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    );
    
    const userResponse = { ...newUser };
    delete userResponse.password;
    
    res.status(201).json({ token, user: userResponse });
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    console.log('Login attempt for:', email);
    
    const user = dataStore.users.find(u => u.email === email);
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    const token = jwt.sign(
      { userId: user._id },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    );
    
    const userResponse = { ...user };
    delete userResponse.password;
    
    res.json({ token, user: userResponse });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============= USER ROUTES =============

app.get('/api/user/profile', authMiddleware, async (req, res) => {
  const user = { ...req.user };
  delete user.password;
  res.json(user);
});

app.put('/api/user/insurance', authMiddleware, async (req, res) => {
  try {
    const userIndex = dataStore.users.findIndex(u => u._id === req.userId);
    if (userIndex !== -1) {
      dataStore.users[userIndex].insuranceInfo = {
        ...dataStore.users[userIndex].insuranceInfo,
        ...req.body
      };
      res.json(dataStore.users[userIndex].insuranceInfo);
    } else {
      res.status(404).json({ error: 'User not found' });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= PROCEDURES =============

app.get('/api/procedures/search', async (req, res) => {
  try {
    const { q } = req.query;
    
    let results = dataStore.procedures;
    
    if (q && q.trim()) {
      const query = q.toLowerCase();
      results = dataStore.procedures.filter(p => 
        p.name.toLowerCase().includes(query) ||
        p.cptCode.toLowerCase().includes(query)
      );
    }
    
    res.json(results);
  } catch (error) {
    console.error('Procedure search error:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============= COST ESTIMATION =============

app.post('/api/estimate/calculate', authMiddleware, async (req, res) => {
  try {
    const { procedureCode, providerId, totalCost } = req.body;
    const insurance = req.user.insuranceInfo || {};
    
    // Ensure we have valid numbers
    const deductible = Number(insurance.deductible) || 2000;
    const deductibleMet = Number(insurance.deductibleMet) || 0;
    const outOfPocketMax = Number(insurance.outOfPocketMax) || 8000;
    const outOfPocketMet = Number(insurance.outOfPocketMet) || 0;
    const coinsurance = Number(insurance.coinsurance) || 20;
    const cost = Number(totalCost) || 0;
    
    // Calculate remaining deductible
    const remainingDeductible = Math.max(0, deductible - deductibleMet);
    
    // Calculate cost after deductible
    const costAfterDeductible = Math.max(0, cost - remainingDeductible);
    
    // Calculate coinsurance
    const coinsuranceAmount = costAfterDeductible * (coinsurance / 100);
    
    // Calculate total out-of-pocket (capped at OOP max)
    const remainingOOP = Math.max(0, outOfPocketMax - outOfPocketMet);
    const totalOutOfPocket = Math.min(
      Math.min(remainingDeductible, cost) + coinsuranceAmount,
      remainingOOP
    );
    
    res.json({
      totalCost: cost,
      deductiblePortion: Math.min(remainingDeductible, cost),
      coinsurancePortion: coinsuranceAmount,
      totalOutOfPocket: totalOutOfPocket,
      insurancePays: Math.max(0, cost - totalOutOfPocket),
      deductibleRemaining: remainingDeductible,
      oopRemaining: Math.max(0, remainingOOP - totalOutOfPocket)
    });
  } catch (error) {
    console.error('Estimate calculation error:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============= BILLS =============

app.get('/api/bills', authMiddleware, async (req, res) => {
  try {
    const userBills = dataStore.bills.filter(b => b.userId === req.userId);
    res.json(userBills);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/bills', authMiddleware, async (req, res) => {
  try {
    const newBill = {
      _id: `bill-${Date.now()}`,
      userId: req.userId,
      ...req.body,
      currentAmount: req.body.originalAmount,
      status: 'pending',
      createdAt: new Date(),
      dueDate: req.body.dueDate || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    };
    
    dataStore.bills.push(newBill);
    res.status(201).json(newBill);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/bills/:id/negotiate', authMiddleware, async (req, res) => {
  try {
    const bill = dataStore.bills.find(b => b._id === req.params.id && b.userId === req.userId);
    
    if (!bill) {
      return res.status(404).json({ error: 'Bill not found' });
    }
    
    // Apply 30% reduction
    bill.status = 'negotiating';
    bill.negotiatedAmount = bill.originalAmount * 0.7;
    bill.currentAmount = bill.negotiatedAmount;
    
    res.json(bill);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/bills/:id/payment-plan', authMiddleware, async (req, res) => {
  try {
    const { months } = req.body;
    const bill = dataStore.bills.find(b => b._id === req.params.id && b.userId === req.userId);
    
    if (!bill) {
      return res.status(404).json({ error: 'Bill not found' });
    }
    
    const amount = bill.negotiatedAmount || bill.currentAmount || bill.originalAmount;
    const monthlyPayment = amount / (months || 12);
    
    bill.status = 'payment_plan';
    bill.paymentPlan = {
      active: true,
      monthlyAmount: monthlyPayment,
      months: months || 12,
      startDate: new Date(),
      endDate: new Date(Date.now() + (months || 12) * 30 * 24 * 60 * 60 * 1000),
      paymentsRemaining: months || 12
    };
    
    res.json(bill);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= FINANCIAL ASSISTANCE =============

app.get('/api/assistance/eligible', authMiddleware, async (req, res) => {
  try {
    // Return all assistance programs for demo
    // In real app, would filter based on user's income/household size
    res.json({
      fplPercentage: 180,
      programs: dataStore.assistancePrograms
    });
  } catch (error) {
    console.error('Assistance error:', error);
    res.status(500).json({ error: error.message });
  }
});

// ============= HEALTH CHECK =============

app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    mode: 'demo',
    message: 'Server running in DEMO MODE (no database)',
    procedures: dataStore.procedures.length,
    users: dataStore.users.length,
    timestamp: new Date()
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════════╗
║   🚀 Healthcare Navigator API Server           ║
╠════════════════════════════════════════════════╣
║   Status: RUNNING (Demo Mode)                  ║
║   Port: ${PORT}                                    ║
║   API: http://localhost:${PORT}/api                ║
║   Health: http://localhost:${PORT}/api/health      ║
╠════════════════════════════════════════════════╣
║   Demo Account:                                ║
║   Email: demo@example.com                      ║
║   Password: password123                        ║
╚════════════════════════════════════════════════╝
  `);
});

module.exports = app;