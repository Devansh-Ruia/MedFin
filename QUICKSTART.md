# MedFin Quick Start Guide

Get up and running with MedFin in minutes!

## Prerequisites

- Python 3.9+ installed
- Node.js 18+ and npm installed

## Quick Setup

### 1. Backend Setup (Terminal 1)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python main.py
```

Backend will start at: `http://localhost:8000`
API Docs available at: `http://localhost:8000/docs`

### 2. Frontend Setup (Terminal 2)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the frontend server
npm run dev
```

Frontend will start at: `http://localhost:3000`

## Using the System

### Navigation Plan (Autonomous Engine)

1. Go to the "Navigation" tab
2. Add your medical bills:
   - Click "+ Add Bill"
   - Enter provider name, total amount, patient responsibility
3. Optionally enter:
   - Annual income
   - Household size
4. Click "Generate Navigation Plan"
5. Review the autonomous plan with:
   - Recommended actions with priorities
   - Projected savings
   - Risk assessment
   - Timeline for actions

### Cost Estimation

1. Go to the "Cost Estimation" tab
2. Select service type (e.g., Primary Care, Emergency)
3. Enter optional details:
   - Description
   - Location
4. Select insurance information if applicable
5. Click "Estimate Cost"
6. Review:
   - Estimated cost
   - Insurance coverage
   - Patient responsibility
   - Lower-cost alternatives

### Bill Analysis

1. Go to the "Bill Analysis" tab
2. Add medical bills
3. Click "Analyze Bills"
4. Review:
   - Potential billing errors
   - Savings opportunities
   - Recommendations

### Insurance Analysis

1. Go to the "Insurance" tab
2. Enter your insurance information:
   - Deductible and remaining amount
   - Out-of-pocket maximum and used amount
   - Coverage percentage
3. Click "Analyze Coverage"
4. Review:
   - Deductible progress
   - Out-of-pocket progress
   - Warnings and recommendations

### Financial Assistance

1. Go to the "Assistance" tab
2. Enter your information:
   - Annual income
   - Household size
   - Medical debt
   - Insurance type
3. Click "Find Matching Programs"
4. Review matching programs with:
   - Match scores
   - Estimated benefits
   - Application links

### Payment Plans

1. Go to the "Payment Plans" tab
2. Enter:
   - Total medical debt
   - Monthly income
   - Monthly expenses
3. Click "Generate Payment Plans"
4. Review payment plan options with:
   - Monthly payment amounts
   - Total costs
   - Pros and cons

## Example Usage

### Example: Generate Navigation Plan

**Input:**
- Bill 1: Provider "ABC Hospital", Amount: $5,000, Patient Responsibility: $2,000
- Bill 2: Provider "XYZ Clinic", Amount: $1,500, Patient Responsibility: $300
- Annual Income: $45,000
- Household Size: 2

**Output:**
- Total Medical Debt: $2,300
- Recommended Actions:
  1. Apply for financial assistance (Priority 1, Estimated Savings: $1,150)
  2. Negotiate with providers (Priority 2, Estimated Savings: $345)
  3. Review bills for errors (Priority 1, Estimated Savings: $230)
  4. Set up payment plan (Priority 3)
- Projected Savings: $1,725
- Risk Level: Medium
- Timeline: Immediate actions within 7 days

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Change port in backend/main.py
uvicorn.run("main:app", host="0.0.0.0", port=8001)
```

**Module not found:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Frontend Issues

**Port already in use:**
```bash
# Next.js will automatically use next available port
# Or specify port:
npm run dev -- -p 3001
```

**API connection errors:**
- Verify backend is running at `http://localhost:8000`
- Check `frontend/.env.local` if API is on different URL:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```

## Next Steps

- Explore the API documentation at `http://localhost:8000/docs`
- Customize the assistance programs in `backend/app/services/assistance_matcher.py`
- Add more service types in `backend/app/services/cost_estimator.py`
- Extend the navigation engine logic in `backend/app/services/navigation_engine.py`

## Support

For issues or questions, please refer to the main README.md file.



