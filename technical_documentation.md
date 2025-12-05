# MedFin Automated Financial Navigation Plans

## System Documentation & Design Rationale

---

## 1. Architecture Overview

The system follows a **layered architecture** with clear separation of concerns:

### Data Flow
```
Input → Validation → Analysis → Decision → Planning → Output
```

### Layer Responsibilities

| Layer | Purpose | Key Components |
|-------|---------|----------------|
| **Ingestion** | Accept and normalize data | Bill, Insurance, Profile parsers |
| **Validation** | Ensure data quality | Validators, Enrichers, Normalizers |
| **Analysis** | Extract insights | Bill, Insurance, Eligibility, Risk Analyzers |
| **Decision** | Evaluate rules | Rule Engine, Priority Matrix |
| **Planning** | Generate outputs | Plan Generator, Timeline Builder |
| **API** | Serve clients | FastAPI endpoints, Response serializers |

---

## 2. Core Design Decisions

### 2.1 Rule-Based Decision Engine

**Why rules over ML?**
- **Explainability**: Every recommendation traces to specific, auditable rules
- **Regulatory compliance**: Healthcare requires transparent decision-making
- **Maintainability**: Rules can be updated without retraining models
- **Reliability**: Deterministic outputs for the same inputs

**Rule Structure**:
Each rule contains:
- Condition function (evaluates context)
- Action type (what to recommend)
- Savings calculator (estimates financial impact)
- Priority base (default urgency level)
- Document requirements
- Dynamic deadline calculator

### 2.2 Multi-Factor Priority Scoring

Actions are ranked using weighted scoring across five dimensions:

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Savings Impact | 30% | Maximize financial benefit |
| Time Sensitivity | 25% | Prevent missed deadlines |
| Approval Likelihood | 20% | Focus on achievable wins |
| Effort Efficiency | 15% | Optimize patient time |
| Risk Mitigation | 10% | Address financial exposure |

### 2.3 Conservative Savings Estimates

Savings are provided as **ranges** (min/expected/max) with confidence scores:
- Prevents over-promising
- Sets realistic expectations
- Allows UI to show optimistic vs. conservative scenarios

---

## 3. Analysis Engine Details

### 3.1 Bill Analysis

**Error Detection Algorithms**:

1. **Duplicate Detection**: Hash-based matching on (CPT code, service date, amount)
2. **Unbundling Detection**: CPT bundling rules from CMS/AMA guidelines
3. **Balance Billing**: State-specific rules for emergency services
4. **Overcharge Detection**: Comparison to allowed amounts (>3x ratio flags)

### 3.2 Insurance Analysis

Evaluates:
- Deductible progress and remaining amounts
- Out-of-pocket maximum proximity
- Coverage gaps (missing claims, out-of-network)
- Year-end optimization opportunities
- Appeal candidates (high patient share relative to total)

### 3.3 Eligibility Matching

**Federal Poverty Level Calculation**:
```python
FPL_2024 = $15,060 + ($5,380 × (household_size - 1))
Patient_FPL% = (annual_income / FPL_threshold) × 100
```

**Matching Algorithm**:
- Score starts at 1.0
- Each unmet criterion reduces score
- Threshold of 0.5 required for inclusion
- Programs ranked by estimated savings

### 3.4 Risk Assessment

**Risk Score Components** (0-100):
- Collections probability (0-30 points)
- Credit impact severity (0-20 points)
- Bankruptcy indicators (0-30 points)
- Debt-to-income ratio (0-20 points)

**Risk Levels**:
| Score | Level | Interpretation |
|-------|-------|----------------|
| 80-100 | Severe | Immediate intervention required |
| 60-79 | High | Significant financial stress |
| 40-59 | Moderate | Manageable with action plan |
| 20-39 | Low | Minimal concern |
| 0-19 | Minimal | Financially stable |

---

## 4. Extensibility Points

### 4.1 Adding New Rules

```python
self.rules.append(Rule(
    id="R011",
    name="New Action Type",
    description="Description of when this applies",
    condition=lambda ctx: ctx["some_field"] > threshold,
    action_type=ActionType.NEW_TYPE,
    priority_base=Priority.MEDIUM,
    savings_calculator=lambda ctx: SavingsEstimate(...),
    effort_minutes=30,
    required_documents=["doc1", "doc2"]
))
```

### 4.2 Adding Assistance Programs

Programs are loaded from `AssistanceProgramDB`. To add:
1. Define `EligibilityCriteria`
2. Create `AssistanceProgram` with discount rates
3. Add to database (or external API in production)

### 4.3 Integrating External Services

The service layer accepts dependency injection:
- Swap `AssistanceProgramDB` for real database
- Replace `CacheService` with Redis
- Add notification services for deadline reminders

---

## 5. Fallback Logic

### Missing Data Handling

| Missing Field | Fallback Behavior |
|--------------|-------------------|
| Due date | Default to today + 30 days |
| Line items | Treat as summary bill, recommend itemization |
| Insurance | Assume uninsured (higher negotiation potential) |
| Income sources | Use annual income / 12 for monthly |
| FPL calculation | Use conservative estimates |

### Partial Analysis

- If bill analysis fails, skip that bill but continue others
- If eligibility matching fails, proceed without assistance recommendations
- Risk assessment provides defaults when data incomplete
- Confidence score reflects data completeness

---

## 6. Performance Considerations

### Optimization Strategies

1. **Parallel Bill Analysis**: Each bill analyzed independently
2. **Caching**: Plans cached for 24 hours with patient ID key
3. **Lazy Loading**: Assistance programs loaded per-state
4. **Rule Short-Circuiting**: Rules exit early on failed conditions

### Scalability Path

- Stateless service design enables horizontal scaling
- Database-backed program catalog for multi-tenant deployment
- Event-driven architecture for async notifications
- Separate workers for long-running eligibility verification

---

## 7. Security & Compliance

### PHI Protection
- No PHI logged at INFO level
- Patient IDs used as references (not SSN/names)
- All data in transit encrypted (TLS 1.3)

### Audit Trail
- Every plan generation logged with timestamp
- Rule evaluations recorded for explainability
- Action step updates tracked with user/timestamp

### Regulatory Alignment
- HIPAA-compliant data handling patterns
- Transparent decision documentation
- No discriminatory factors in priority scoring

---

## 8. Testing Strategy

### Unit Tests
- Each analyzer tested in isolation
- Rule conditions tested with mock contexts
- Edge cases for FPL calculations

### Integration Tests
- End-to-end plan generation
- API request/response validation
- Database interactions

### Scenario Tests
- "Golden path" happy cases
- Edge cases (zero balance, no insurance, etc.)
- Error recovery scenarios

---

## 9. Future Enhancements

1. **ML-Enhanced Savings Prediction**: Train on historical outcomes
2. **Real-Time Eligibility Verification**: API integration with programs
3. **Provider Negotiation Patterns**: Learn which providers negotiate
4. **Personalized Communication Templates**: Generate dispute letters
5. **Progress Tracking**: Patient dashboard for plan execution
6. **Notification Engine**: Deadline reminders via SMS/email

# MedFin Comprehensive Analysis Engine

## Architecture & Design Documentation

---

## 1. System Overview

The MedFin Analysis Engine is a modular, rule-based system that performs deep financial analysis across four domains: **Income**, **Debt**, **Insurance**, and **Bills**. It synthesizes findings into a unified output that powers downstream features like navigation plans, cost estimators, and assistance matchers.

### Core Principles

| Principle | Implementation |
|-----------|---------------|
| **Modularity** | Each analyzer is independent and testable |
| **Explainability** | All scores trace to specific rules and evidence |
| **Defensiveness** | Graceful handling of missing/incomplete data |
| **Extensibility** | Easy to add new rules, programs, or analyses |
| **Production-Ready** | Proper error handling, logging, and performance |

---

## 2. Module Architecture

### 2.1 Income Analyzer

**Purpose**: Assess household financial capacity and hardship indicators

**Key Algorithms**:

```
FPL Calculation:
  FPL_threshold = $15,060 + ($5,380 × (household_size - 1))
  FPL_percentage = (annual_income / FPL_threshold) × 100
  
Income Stability Score (0-1):
  - Start at 1.0
  - Penalize unstable income types (gig, self-employment): -0.5 × ratio
  - Bonus for very stable (SS, pension): +0.2 × ratio
  - Penalize unverified income: ×0.9

Hardship Score (0-100):
  - Below 100% FPL: +40
  - Below 200% FPL: +25
  - Catastrophic medical debt (>50% income): +30
  - Negative cash flow: +25
  - Medical collections: +15
```

**Outputs**:
- FPL calculation with threshold markers
- Income tier classification
- Budget projection with medical payment capacity
- Hardship flags and qualification indicators

### 2.2 Debt Analyzer

**Purpose**: Analyze debt burden, risk, and strategic opportunities

**Key Algorithms**:

```
DTI Calculation:
  gross_dti = monthly_debt_payments / monthly_gross_income
  
DTI Risk Tiers:
  - <20%: Minimal
  - 20-28%: Low
  - 28-36%: Moderate
  - 36-43%: High
  - 43-50%: Severe
  - >50%: Critical

Collections Risk (0-1):
  - In collections: 0.95
  - 90+ days delinquent: 0.85
  - 60+ days: 0.60
  - 30+ days: 0.35
  - Past due: 0.30
```

**Outputs**:
- Debt breakdown by type (medical vs consumer, secured vs unsecured)
- DTI analysis with lending threshold markers
- Qualification assessments for assistance programs
- Strategy recommendations (avalanche, snowball, consolidation)

### 2.3 Insurance Analyzer

**Purpose**: Track coverage, identify gaps, and optimize utilization

**Key Functions**:

1. **Deductible/OOP Tracking**: Calculates remaining amounts, projects when thresholds will be met
2. **Gap Detection**: Identifies out-of-network charges, denials, unsubmitted claims
3. **Coding Mismatch Detection**: Finds preventive care charged incorrectly, diagnosis issues
4. **Year-End Strategy**: Recommends actions based on plan year timing
5. **Coverage Matching**: Estimates costs for upcoming procedures

**Proximity Tiers for OOP Max**:
```
- met: 100%+
- very_close: 85-99%
- close: 70-84%
- moderate: 50-69%
- far: <50%
```

### 2.4 Bill Analyzer

**Purpose**: Detect errors, calculate savings, and generate negotiation strategies

**Error Detection Rules**:

| Error Type | Detection Method | Confidence |
|------------|-----------------|------------|
| Duplicate Charge | Same CPT + date + amount | 95% |
| Unbundling | CCI edit lookup (parent + child present) | 80% |
| Preventive Miscoded | Preventive CPT + cost share > $0 | 70-85% |
| Balance Billing | OON ER + charge > allowed × coinsurance | 75% |
| Claim Not Submitted | Insurance paid = $0 + in-network | 75% |

**Negotiation Opportunity Types**:
1. **Prompt-Pay**: 15-25% discount for immediate payment
2. **Financial Hardship**: 20-50% based on FPL percentage
3. **Cash-Pay**: 30-50% for self-pay patients

---

## 3. Data Flow

```
┌─────────────────┐
│  User Profile   │
│  (Unified Input)│
└────────┬────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│                  ANALYSIS PHASE                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Income  │ │   Debt   │ │Insurance │ │   Bill   │  │
│  │ Analyzer │ │ Analyzer │ │ Analyzer │ │ Analyzer │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │          │
└───────┼────────────┼────────────┼────────────┼──────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌────────────────────────────────────────────────────────┐
│                  SYNTHESIS PHASE                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │    Risk     │ │ Opportunity │ │  Strategy   │       │
│  │  Synthesizer│ │ Synthesizer │ │ Synthesizer │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
└────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Unified Analysis   │
              │      Output         │
              └─────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Navigation  │ │    Cost      │ │  Assistance  │
│    Planner   │ │  Estimator   │ │   Matcher    │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 4. Risk Scoring Model

### Overall Risk Score (0-100)

Weighted combination of component scores:

| Component | Weight | Factors |
|-----------|--------|---------|
| Income Risk | 30% | FPL%, hardship score, cash flow |
| Debt Risk | 30% | DTI, collections, delinquencies |
| Insurance Risk | 20% | Plan adequacy, gaps, deductible status |
| Billing Risk | 20% | Error rate, collections risk, urgency |

### Risk Tier Mapping

| Score | Tier | Action Level |
|-------|------|--------------|
| 70-100 | Critical | Immediate intervention |
| 55-69 | Severe | Urgent action needed |
| 40-54 | High | Prompt attention required |
| 25-39 | Moderate | Monitor and plan |
| 10-24 | Low | Routine management |
| 0-9 | Minimal | No immediate concern |

---

## 5. Key Design Decisions

### 5.1 Why Rule-Based Over ML?

1. **Explainability**: Healthcare requires transparent, auditable decisions
2. **Regulatory Compliance**: Rules can be mapped to regulations
3. **Maintainability**: Update rules without retraining
4. **Consistency**: Same inputs always produce same outputs
5. **Edge Cases**: Explicitly handle known scenarios

### 5.2 Conservative Estimates

All savings projections use ranges (min/expected/max) with confidence scores:
- Prevents over-promising to users
- Allows UI to show realistic expectations
- Confidence informs prioritization

### 5.3 Defensive Data Handling

| Missing Data | Fallback |
|--------------|----------|
| No income sources | Use annual gross / 12 |
| No insurance | Flag as uninsured, higher negotiation potential |
| No line items | Recommend requesting itemized bill |
| Missing due date | Default to today + 30 days |
| Unknown network status | Flag for verification |

---

## 6. Extensibility Points

### Adding New Billing Rules

```python
# In BillAnalyzer.BUNDLING_RULES
"NEW_PARENT_CODE": ["CHILD_CODE_1", "CHILD_CODE_2"]

# In BillAnalyzer.PREVENTIVE_CODES
"NEW_PREVENTIVE_CPT"
```

### Adding Assistance Programs

```python
DebtAnalyzer._assess_qualifications():
    qualifications.append(QualificationAssessment(
        program_type="new_program",
        program_name="New Assistance Program",
        qualification_likelihood=0.7,
        qualifying_factors=[...],
        required_actions=[...]
    ))
```

### Adding New Risk Factors

```python
IncomeAnalyzer._detect_hardship():
    if new_condition:
        flags.append("NEW_HARDSHIP_FLAG")
        score += points
```

---

## 7. Integration Boundaries

### Downstream Consumers

| Consumer | Key Inputs Used |
|----------|-----------------|
| Navigation Planner | risk_summary, bill_analysis.errors, strategy_summary |
| Cost Estimator | insurance_analysis.coverage_matches, deductible_status |
| Assistance Matcher | fpl_percentage, hardship_flags, qualifications |
| Payment Optimizer | monthly_payment_capacity, debt_analysis.priority_debts |

### API Contract

```python
# Input
profile: UserFinancialProfile

# Output
analysis: UnifiedAnalysisOutput

# Key output flags for routing
analysis.needs_assistance_matching  # Route to assistance flow
analysis.needs_payment_plan         # Route to payment planning
analysis.has_disputable_errors      # Route to dispute flow
analysis.urgent_action_required     # Trigger alerts
```

---

## 8. Performance Considerations

- **Target**: <500ms for complete analysis
- **Parallelization**: Bill analysis can run concurrently per bill
- **Caching**: Results cached by user_id + data hash
- **Lazy Loading**: Insurance/assistance data loaded on demand

---

## 9. Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Unit Tests | Each analyzer method |
| Integration | Full analysis pipeline |
| Edge Cases | Missing data, extreme values |
| Regression | Known billing error patterns |
| Performance | Response time under load |