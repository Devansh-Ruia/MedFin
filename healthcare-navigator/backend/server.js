// server.js - Main backend server file
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/healthcare-navigator', {
  useNewUrlParser: true,
  useUnifiedTopology: true
});

// ============= SCHEMAS =============

// User Schema
const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  profile: {
    firstName: String,
    lastName: String,
    dateOfBirth: Date,
    phone: String,
    address: {
      street: String,
      city: String,
      state: String,
      zip: String
    },
    householdSize: Number,
    annualIncome: Number
  },
  insuranceInfo: {
    provider: String,
    planType: String,
    memberId: String,
    groupNumber: String,
    deductible: Number,
    deductibleMet: { type: Number, default: 0 },
    outOfPocketMax: Number,
    outOfPocketMet: { type: Number, default: 0 },
    coinsurance: Number,
    copay: {
      primary: Number,
      specialist: Number,
      emergency: Number,
      urgent: Number
    }
  },
  createdAt: { type: Date, default: Date.now }
});

// Medical Bill Schema
const billSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  provider: { type: String, required: true },
  providerContact: {
    phone: String,
    address: String,
    email: String
  },
  dateOfService: Date,
  billDate: Date,
  dueDate: Date,
  originalAmount: { type: Number, required: true },
  negotiatedAmount: Number,
  currentAmount: Number,
  status: { 
    type: String, 
    enum: ['pending', 'reviewing', 'negotiating', 'payment_plan', 'paid', 'disputed'],
    default: 'pending'
  },
  insuranceClaim: {
    claimNumber: String,
    dateSubmitted: Date,
    amountBilled: Number,
    allowedAmount: Number,
    insurancePaid: Number,
    patientResponsibility: Number
  },
  documents: [{
    name: String,
    url: String,
    uploadedAt: Date,
    type: String // 'bill', 'eob', 'receipt', 'appeal'
  }],
  notes: [{
    date: Date,
    content: String,
    action: String
  }],
  paymentPlan: {
    active: { type: Boolean, default: false },
    monthlyAmount: Number,
    startDate: Date,
    endDate: Date,
    paymentsRemaining: Number
  },
  createdAt: { type: Date, default: Date.now }
});

// Procedure Estimate Schema
const procedureSchema = new mongoose.Schema({
  name: { type: String, required: true },
  cptCode: { type: String, required: true, unique: true },
  category: String,
  description: String,
  averageCost: Number,
  costRange: {
    low: Number,
    high: Number
  },
  medicareRate: Number,
  commonDiagnoses: [String],
  requiresPreAuth: { type: Boolean, default: false },
  typicalDuration: String,
  updatedAt: { type: Date, default: Date.now }
});

// Provider Schema
const providerSchema = new mongoose.Schema({
  name: { type: String, required: true },
  type: String, // 'hospital', 'clinic', 'imaging_center', 'lab', 'specialist'
  npi: String, // National Provider Identifier
  taxId: String,
  address: {
    street: String,
    city: String,
    state: String,
    zip: String
  },
  phone: String,
  website: String,
  qualityRating: Number,
  averageCostIndex: Number, // relative to regional average (1.0 = average)
  acceptedInsurance: [String],
  services: [String],
  chargemasterUrl: String, // link to price transparency data
  negotiatedRates: [{
    insurancePlan: String,
    procedureCode: String,
    rate: Number
  }],
  location: {
    type: { type: String, default: 'Point' },
    coordinates: [Number] // [longitude, latitude]
  }
});

// Financial Assistance Program Schema
const assistanceProgramSchema = new mongoose.Schema({
  name: { type: String, required: true },
  type: String, // 'hospital', 'government', 'nonprofit', 'pharmaceutical'
  provider: String,
  description: String,
  eligibilityCriteria: {
    maxIncome: Number,
    fplPercentage: Number, // Federal Poverty Level percentage
    otherRequirements: [String]
  },
  benefits: {
    discountPercentage: Number,
    maxBenefit: Number,
    coveredServices: [String]
  },
  applicationUrl: String,
  requiredDocuments: [String],
  averageProcessingTime: String,
  contactInfo: {
    phone: String,
    email: String,
    website: String
  }
});

// Cost Estimate History Schema
const estimateHistorySchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  procedureCode: String,
  procedureName: String,
  providers: [{
    providerId: { type: mongoose.Schema.Types.ObjectId, ref: 'Provider' },
    name: String,
    estimatedCost: Number,
    outOfPocketEstimate: Number,
    inNetwork: Boolean
  }],
  insuranceUsed: {
    provider: String,
    planType: String,
    deductibleRemaining: Number,
    oopRemaining: Number
  },
  createdAt: { type: Date, default: Date.now }
});

// Models
const User = mongoose.model('User', userSchema);
const Bill = mongoose.model('Bill', billSchema);
const Procedure = mongoose.model('Procedure', procedureSchema);
const Provider = mongoose.model('Provider', providerSchema);
const AssistanceProgram = mongoose.model('AssistanceProgram', assistanceProgramSchema);
const EstimateHistory = mongoose.model('EstimateHistory', estimateHistorySchema);

// ============= MIDDLEWARE =============

// Authentication middleware
const authMiddleware = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    if (!token) throw new Error();
    
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
    const user = await User.findById(decoded.userId).select('-password');
    
    if (!user) throw new Error();
    
    req.user = user;
    req.userId = user._id;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Please authenticate' });
  }
};

// ============= AUTH ROUTES =============

// Register
app.post('/api/auth/register', async (req, res) => {
  try {
    const { email, password, firstName, lastName } = req.body;
    
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({ error: 'Email already registered' });
    }
    
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = new User({
      email,
      password: hashedPassword,
      profile: { firstName, lastName }
    });
    
    await user.save();
    
    const token = jwt.sign(
      { userId: user._id },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    );
    
    res.status(201).json({ 
      token, 
      user: { 
        id: user._id, 
        email: user.email, 
        profile: user.profile 
      } 
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Login
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    const user = await User.findOne({ email });
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
    
    res.json({ 
      token, 
      user: { 
        id: user._id, 
        email: user.email, 
        profile: user.profile,
        insuranceInfo: user.insuranceInfo
      } 
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= USER ROUTES =============

// Get user profile
app.get('/api/user/profile', authMiddleware, async (req, res) => {
  res.json(req.user);
});

// Update user profile
app.put('/api/user/profile', authMiddleware, async (req, res) => {
  try {
    const updates = req.body;
    delete updates.password; // Don't update password this way
    
    const user = await User.findByIdAndUpdate(
      req.userId,
      { $set: updates },
      { new: true }
    ).select('-password');
    
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update insurance info
app.put('/api/user/insurance', authMiddleware, async (req, res) => {
  try {
    const user = await User.findByIdAndUpdate(
      req.userId,
      { $set: { insuranceInfo: req.body } },
      { new: true }
    ).select('-password');
    
    res.json(user.insuranceInfo);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= PROCEDURE ROUTES =============

// Search procedures
app.get('/api/procedures/search', async (req, res) => {
  try {
    const { q } = req.query;
    const query = q 
      ? {
          $or: [
            { name: { $regex: q, $options: 'i' } },
            { cptCode: { $regex: q, $options: 'i' } },
            { description: { $regex: q, $options: 'i' } }
          ]
        }
      : {};
    
    const procedures = await Procedure.find(query).limit(20);
    res.json(procedures);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get procedure details
app.get('/api/procedures/:cptCode', async (req, res) => {
  try {
    const procedure = await Procedure.findOne({ cptCode: req.params.cptCode });
    if (!procedure) {
      return res.status(404).json({ error: 'Procedure not found' });
    }
    res.json(procedure);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= COST ESTIMATION ROUTES =============

// Calculate out-of-pocket cost
app.post('/api/estimate/calculate', authMiddleware, async (req, res) => {
  try {
    const { procedureCode, providerId, totalCost } = req.body;
    const user = await User.findById(req.userId);
    const insurance = user.insuranceInfo;
    
    // Calculate remaining deductible
    const remainingDeductible = Math.max(0, insurance.deductible - insurance.deductibleMet);
    
    // Calculate cost after deductible
    const costAfterDeductible = Math.max(0, totalCost - remainingDeductible);
    
    // Calculate coinsurance
    const coinsuranceAmount = costAfterDeductible * (insurance.coinsurance / 100);
    
    // Calculate total out-of-pocket (capped at OOP max)
    const remainingOOP = insurance.outOfPocketMax - insurance.outOfPocketMet;
    const totalOutOfPocket = Math.min(
      remainingDeductible + coinsuranceAmount,
      remainingOOP
    );
    
    // Save estimate to history
    const estimate = new EstimateHistory({
      userId: req.userId,
      procedureCode,
      providers: [{
        providerId,
        estimatedCost: totalCost,
        outOfPocketEstimate: totalOutOfPocket,
        inNetwork: true
      }],
      insuranceUsed: {
        provider: insurance.provider,
        planType: insurance.planType,
        deductibleRemaining: remainingDeductible,
        oopRemaining: remainingOOP
      }
    });
    
    await estimate.save();
    
    res.json({
      totalCost,
      deductiblePortion: Math.min(remainingDeductible, totalCost),
      coinsurancePortion: coinsuranceAmount,
      totalOutOfPocket,
      insurancePays: totalCost - totalOutOfPocket,
      deductibleRemaining: remainingDeductible,
      oopRemaining: remainingOOP - totalOutOfPocket
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get provider estimates for procedure
app.get('/api/estimate/providers/:procedureCode', authMiddleware, async (req, res) => {
  try {
    const { procedureCode } = req.params;
    const { lat, lon, radius = 25 } = req.query;
    
    const procedure = await Procedure.findOne({ cptCode: procedureCode });
    if (!procedure) {
      return res.status(404).json({ error: 'Procedure not found' });
    }
    
    // Find providers within radius (if location provided)
    let query = {};
    if (lat && lon) {
      query = {
        location: {
          $near: {
            $geometry: { type: 'Point', coordinates: [parseFloat(lon), parseFloat(lat)] },
            $maxDistance: radius * 1609.34 // Convert miles to meters
          }
        }
      };
    }
    
    const providers = await Provider.find(query).limit(10);
    
    // Calculate estimated costs for each provider
    const estimates = providers.map(provider => {
      const baseCost = procedure.averageCost * (provider.averageCostIndex || 1);
      const negotiatedRate = provider.negotiatedRates.find(
        rate => rate.procedureCode === procedureCode
      );
      
      return {
        provider: {
          id: provider._id,
          name: provider.name,
          address: provider.address,
          phone: provider.phone,
          qualityRating: provider.qualityRating,
          distance: 0 // Calculate actual distance if needed
        },
        estimatedCost: negotiatedRate ? negotiatedRate.rate : baseCost,
        inNetwork: provider.acceptedInsurance.includes(req.user.insuranceInfo.provider)
      };
    });
    
    res.json(estimates);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= BILL MANAGEMENT ROUTES =============

// Get user's bills
app.get('/api/bills', authMiddleware, async (req, res) => {
  try {
    const bills = await Bill.find({ userId: req.userId }).sort({ dueDate: 1 });
    res.json(bills);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create new bill
app.post('/api/bills', authMiddleware, async (req, res) => {
  try {
    const bill = new Bill({
      ...req.body,
      userId: req.userId,
      currentAmount: req.body.originalAmount
    });
    await bill.save();
    res.status(201).json(bill);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update bill
app.put('/api/bills/:id', authMiddleware, async (req, res) => {
  try {
    const bill = await Bill.findOneAndUpdate(
      { _id: req.params.id, userId: req.userId },
      { $set: req.body },
      { new: true }
    );
    
    if (!bill) {
      return res.status(404).json({ error: 'Bill not found' });
    }
    
    res.json(bill);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Request bill negotiation
app.post('/api/bills/:id/negotiate', authMiddleware, async (req, res) => {
  try {
    const bill = await Bill.findOne({ _id: req.params.id, userId: req.userId });
    if (!bill) {
      return res.status(404).json({ error: 'Bill not found' });
    }
    
    // Simulate negotiation (in real app, this would trigger actual negotiation process)
    const negotiatedAmount = bill.originalAmount * 0.7; // 30% reduction
    
    bill.status = 'negotiating';
    bill.negotiatedAmount = negotiatedAmount;
    bill.notes.push({
      date: new Date(),
      content: 'Negotiation requested - targeting 30% reduction',
      action: 'negotiation_started'
    });
    
    await bill.save();
    res.json(bill);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create payment plan
app.post('/api/bills/:id/payment-plan', authMiddleware, async (req, res) => {
  try {
    const { months } = req.body;
    const bill = await Bill.findOne({ _id: req.params.id, userId: req.userId });
    
    if (!bill) {
      return res.status(404).json({ error: 'Bill not found' });
    }
    
    const monthlyAmount = (bill.negotiatedAmount || bill.currentAmount) / months;
    
    bill.status = 'payment_plan';
    bill.paymentPlan = {
      active: true,
      monthlyAmount,
      startDate: new Date(),
      endDate: new Date(Date.now() + months * 30 * 24 * 60 * 60 * 1000),
      paymentsRemaining: months
    };
    
    await bill.save();
    res.json(bill);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= FINANCIAL ASSISTANCE ROUTES =============

// Find eligible assistance programs
app.get('/api/assistance/eligible', authMiddleware, async (req, res) => {
  try {
    const user = await User.findById(req.userId);
    const { annualIncome, householdSize } = user.profile;
    
    // Calculate FPL percentage (2024 FPL for 48 states)
    const fplBase = 14580;
    const fplPerPerson = 5140;
    const fplThreshold = fplBase + (fplPerPerson * (householdSize - 1));
    const fplPercentage = (annualIncome / fplThreshold) * 100;
    
    // Find programs user might qualify for
    const programs = await AssistanceProgram.find({
      $or: [
        { 'eligibilityCriteria.fplPercentage': { $gte: fplPercentage } },
        { 'eligibilityCriteria.maxIncome': { $gte: annualIncome } }
      ]
    });
    
    // Categorize by likelihood
    const categorized = programs.map(program => {
      let likelihood = 'check';
      
      if (program.eligibilityCriteria.fplPercentage && 
          fplPercentage <= program.eligibilityCriteria.fplPercentage) {
        likelihood = 'likely';
      } else if (program.eligibilityCriteria.maxIncome && 
                 annualIncome <= program.eligibilityCriteria.maxIncome * 0.8) {
        likelihood = 'likely';
      } else if (program.eligibilityCriteria.maxIncome && 
                 annualIncome <= program.eligibilityCriteria.maxIncome) {
        likelihood = 'possible';
      }
      
      return {
        ...program.toObject(),
        likelihood,
        estimatedBenefit: program.benefits.discountPercentage 
          ? `${program.benefits.discountPercentage}% discount`
          : `Up to $${program.benefits.maxBenefit}`
      };
    });
    
    res.json({
      fplPercentage: Math.round(fplPercentage),
      programs: categorized
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= EXTERNAL API INTEGRATIONS =============

// Get drug prices from GoodRx API (example)
app.get('/api/drugs/price', authMiddleware, async (req, res) => {
  try {
    const { drugName, dosage, quantity } = req.query;
    
    // This would integrate with GoodRx API
    // For demo, returning mock data
    const mockPrices = {
      pharmacy: [
        { name: 'CVS', price: 45.99, distance: 0.5 },
        { name: 'Walgreens', price: 42.50, distance: 1.2 },
        { name: 'Walmart', price: 38.00, distance: 2.3 }
      ],
      coupons: [
        { provider: 'GoodRx', price: 25.00, code: 'GRX2024' },
        { provider: 'SingleCare', price: 28.00, code: 'SC2024' }
      ]
    };
    
    res.json(mockPrices);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Verify insurance coverage (would integrate with Availity or similar)
app.post('/api/insurance/verify', authMiddleware, async (req, res) => {
  try {
    const { memberId, dateOfBirth, provider } = req.body;
    
    // This would call real insurance verification API
    // Mock response for demo
    const mockVerification = {
      verified: true,
      eligibility: {
        status: 'active',
        effectiveDate: '2024-01-01',
        planName: 'PPO Gold',
        deductible: {
          individual: 2000,
          individualMet: 500,
          family: 4000,
          familyMet: 750
        },
        outOfPocketMax: {
          individual: 8000,
          individualMet: 1000,
          family: 16000,
          familyMet: 1500
        }
      }
    };
    
    res.json(mockVerification);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= ANALYTICS ROUTES =============

// Get spending analytics
app.get('/api/analytics/spending', authMiddleware, async (req, res) => {
  try {
    const bills = await Bill.find({ userId: req.userId });
    
    const analytics = {
      totalSpent: bills.reduce((sum, bill) => 
        sum + (bill.negotiatedAmount || bill.currentAmount), 0),
      totalSaved: bills.reduce((sum, bill) => 
        sum + (bill.originalAmount - (bill.negotiatedAmount || bill.originalAmount)), 0),
      byMonth: {},
      byProvider: {},
      byStatus: {}
    };
    
    // Group by month
    bills.forEach(bill => {
      const month = new Date(bill.dateOfService).toISOString().slice(0, 7);
      analytics.byMonth[month] = (analytics.byMonth[month] || 0) + 
        (bill.negotiatedAmount || bill.currentAmount);
      
      // Group by provider
      analytics.byProvider[bill.provider] = (analytics.byProvider[bill.provider] || 0) + 
        (bill.negotiatedAmount || bill.currentAmount);
      
      // Group by status
      analytics.byStatus[bill.status] = (analytics.byStatus[bill.status] || 0) + 1;
    });
    
    res.json(analytics);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============= SEED DATA ROUTE (Development) =============

app.post('/api/seed', async (req, res) => {
  try {
    // Clear existing data
    await Procedure.deleteMany({});
    await Provider.deleteMany({});
    await AssistanceProgram.deleteMany({});
    
    // Seed procedures
    const procedures = [
      { name: 'MRI Brain w/o Contrast', cptCode: '70551', category: 'Imaging', averageCost: 3000, costRange: { low: 1500, high: 5000 }},
      { name: 'CT Abdomen w/Contrast', cptCode: '74160', category: 'Imaging', averageCost: 2000, costRange: { low: 800, high: 3500 }},
      { name: 'Colonoscopy', cptCode: '45380', category: 'Procedure', averageCost: 3500, costRange: { low: 2000, high: 5000 }},
      { name: 'Knee Replacement', cptCode: '27447', category: 'Surgery', averageCost: 35000, costRange: { low: 25000, high: 50000 }},
      { name: 'Appendectomy', cptCode: '44970', category: 'Surgery', averageCost: 15000, costRange: { low: 10000, high: 25000 }}
    ];
    await Procedure.insertMany(procedures);
    
    // Seed providers
    const providers = [
      { 
        name: 'City Medical Center', 
        type: 'hospital',
        address: { city: 'Oakland', state: 'CA', zip: '94612' },
        qualityRating: 4.5, 
        averageCostIndex: 1.1,
        acceptedInsurance: ['Blue Cross', 'Aetna', 'United', 'Cigna']
      },
      { 
        name: 'Regional Hospital', 
        type: 'hospital',
        address: { city: 'Berkeley', state: 'CA', zip: '94704' },
        qualityRating: 4.2, 
        averageCostIndex: 0.95,
        acceptedInsurance: ['Blue Cross', 'Kaiser', 'United']
      },
      { 
        name: 'Bay Area Imaging', 
        type: 'imaging_center',
        address: { city: 'Oakland', state: 'CA', zip: '94607' },
        qualityRating: 4.7, 
        averageCostIndex: 0.8,
        acceptedInsurance: ['Blue Cross', 'Aetna', 'United', 'Cigna', 'Medicare']
      }
    ];
    await Provider.insertMany(providers);
    
    // Seed assistance programs
    const programs = [
      {
        name: 'Hospital Financial Assistance',
        type: 'hospital',
        provider: 'City Medical Center',
        eligibilityCriteria: { fplPercentage: 300 },
        benefits: { discountPercentage: 100 }
      },
      {
        name: 'Medi-Cal',
        type: 'government',
        eligibilityCriteria: { fplPercentage: 138 },
        benefits: { discountPercentage: 100 }
      },
      {
        name: 'Covered California Subsidies',
        type: 'government',
        eligibilityCriteria: { fplPercentage: 400 },
        benefits: { maxBenefit: 500 }
      }
    ];
    await AssistanceProgram.insertMany(programs);
    
    res.json({ message: 'Database seeded successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

// Export for testing
module.exports = app;