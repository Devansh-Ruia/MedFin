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