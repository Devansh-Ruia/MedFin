# MedFin - Autonomous Healthcare Financial Navigator

MedFin is a comprehensive autonomous healthcare financial navigation system that helps users navigate healthcare costs, insurance coverage, medical billing, and financial assistance options. The system uses intelligent algorithms to analyze financial situations, recommend actions, and match users with appropriate assistance programs.

## Features

### 🤖 Autonomous Navigation Engine
- Analyzes financial situation based on medical bills, insurance, and income
- Generates personalized action plans with priorities and timelines
- Assesses financial risk and provides recommendations
- Projects potential savings from recommended actions

### 💰 Cost Estimation
- Estimate healthcare service costs by type
- Calculate insurance coverage and patient responsibility
- Location-based cost adjustments
- Alternative lower-cost options

### 📋 Bill Analysis
- Analyze medical bills for errors and issues
- Identify potential duplicate charges
- Verify insurance coverage accuracy
- Generate itemized bill request templates
- Savings opportunity identification

### 🛡️ Insurance Analysis
- Track deductible and out-of-pocket progress
- Identify coverage issues and warnings
- Provide coverage optimization recommendations
- Monitor insurance benefit utilization

### 💳 Payment Plans
- Generate multiple payment plan options
- Compare plans by monthly payment, total cost, and terms
- Interest-free and interest-bearing options
- Personalized recommendations based on financial situation

### ❤️ Financial Assistance Matching
- Match users with relevant assistance programs
- Income and eligibility-based matching
- Pharmaceutical assistance programs
- Hospital charity care programs
- Government subsidy programs

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI (Python)
- **Location**: `backend/`
- **Key Components**:
  - `app/services/cost_estimator.py` - Healthcare cost estimation
  - `app/services/navigation_engine.py` - Autonomous decision-making engine
  - `app/services/assistance_matcher.py` - Financial assistance program matching
  - `app/services/payment_planner.py` - Payment plan generation
  - `app/routers/` - API endpoints

### Frontend (Next.js)
- **Framework**: Next.js 14 with React 18
- **Location**: `frontend/`
- **Styling**: Tailwind CSS
- **Key Components**:
  - Navigation Plan dashboard
  - Cost estimation interface
  - Bill analysis tools
  - Insurance coverage tracker
  - Assistance program matcher
  - Payment plan generator

## Installation

### Prerequisites
- Python 3.9+ (for backend)
- Node.js 18+ and npm (for frontend)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

API documentation is available at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file (optional, if API is not on localhost:8000):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

### Starting the System

1. Start the backend server (from `backend/` directory):
```bash
python main.py
```

2. Start the frontend server (from `frontend/` directory):
```bash
npm run dev
```

3. Open your browser to `http://localhost:3000`

### Using the Autonomous Navigation System

1. **Navigation Plan**: Enter your medical bills, insurance information, and financial details to get an autonomous navigation plan with recommended actions.

2. **Cost Estimation**: Get cost estimates for healthcare services before scheduling appointments.

3. **Bill Analysis**: Upload your medical bills to identify errors, issues, and savings opportunities.

4. **Insurance Analysis**: Track your insurance coverage, deductible progress, and get optimization recommendations.

5. **Assistance Programs**: Find financial assistance programs that match your situation.

6. **Payment Plans**: Generate payment plan options tailored to your financial situation.

## API Endpoints

### Cost Estimation
- `POST /api/v1/cost/estimate` - Estimate healthcare service cost
- `GET /api/v1/cost/services` - Get available service types

### Insurance
- `POST /api/v1/insurance/analyze` - Analyze insurance coverage
- `GET /api/v1/insurance/types` - Get insurance types

### Bills
- `POST /api/v1/bills/analyze` - Analyze medical bills
- `POST /api/v1/bills/itemize` - Request itemized bill template

### Navigation
- `POST /api/v1/navigation/plan` - Generate autonomous navigation plan
- `POST /api/v1/navigation/analyze-situation` - Quick financial situation analysis

### Assistance
- `POST /api/v1/assistance/match` - Match assistance programs
- `GET /api/v1/assistance/programs` - List available programs

### Payment Plans
- `POST /api/v1/payment-plans/generate` - Generate payment plan options
- `POST /api/v1/payment-plans/recommend` - Get recommended payment plan

## Project Structure

```
MedFin/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # Configuration settings
│   │   │   └── models.py          # Pydantic models
│   │   ├── routers/               # API route handlers
│   │   │   ├── cost_estimation.py
│   │   │   ├── insurance.py
│   │   │   ├── bills.py
│   │   │   ├── navigation.py
│   │   │   ├── assistance.py
│   │   │   └── payment_plans.py
│   │   └── services/              # Business logic
│   │       ├── cost_estimator.py
│   │       ├── navigation_engine.py
│   │       ├── assistance_matcher.py
│   │       └── payment_planner.py
│   ├── main.py                    # FastAPI application entry point
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── app/
│   │   ├── layout.tsx             # Root layout
│   │   ├── page.tsx               # Main page
│   │   └── globals.css            # Global styles
│   ├── components/                # React components
│   │   ├── NavigationPlan.tsx
│   │   ├── CostEstimation.tsx
│   │   ├── BillAnalysis.tsx
│   │   ├── InsuranceAnalysis.tsx
│   │   ├── AssistancePrograms.tsx
│   │   └── PaymentPlans.tsx
│   ├── lib/
│   │   └── api.ts                 # API client
│   ├── package.json
│   └── next.config.js
└── README.md
```

## Key Features Explained

### Autonomous Navigation Engine

The navigation engine analyzes:
- Total medical debt
- Insurance coverage status
- Financial hardship level (based on income and household size)
- Debt-to-income ratio
- Risk factors

It generates prioritized actions such as:
- Reviewing bills for errors
- Negotiating with providers
- Applying for financial assistance
- Setting up payment plans
- Optimizing insurance usage

### Cost Estimation

Uses base cost ranges by service type and applies:
- Location-based cost multipliers
- Insurance coverage calculations
- Deductible impacts
- Alternative lower-cost options

### Financial Assistance Matching

Matches users with programs based on:
- Annual income and household size
- Insurance type
- Medical debt amount
- Prescription needs
- Medical diagnoses

## Development

### Running Tests

Backend tests (to be implemented):
```bash
cd backend
pytest
```

Frontend tests (to be implemented):
```bash
cd frontend
npm test
```

### Code Formatting

Backend:
```bash
cd backend
black app/
isort app/
```

Frontend:
```bash
cd frontend
npm run lint
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This system is designed to assist with healthcare financial navigation and should not be considered as financial or medical advice. Users should consult with healthcare providers and financial advisors for professional guidance.
