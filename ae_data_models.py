"""
MedFin Analysis Engine - Comprehensive Data Models
Complete type definitions for income, debt, insurance, and bill analysis
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, computed_field
from uuid import UUID, uuid4


# ============================================================================
# ENUMERATIONS
# ============================================================================

class IncomeType(str, Enum):
    W2_EMPLOYMENT = "w2_employment"
    SELF_EMPLOYMENT = "self_employment"
    SOCIAL_SECURITY = "social_security"
    DISABILITY = "disability"
    PENSION = "pension"
    UNEMPLOYMENT = "unemployment"
    ALIMONY = "alimony"
    CHILD_SUPPORT = "child_support"
    RENTAL = "rental"
    INVESTMENT = "investment"
    GIG_WORK = "gig_work"
    OTHER = "other"

class IncomeFrequency(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    IRREGULAR = "irregular"

class DebtType(str, Enum):
    MEDICAL = "medical"
    CREDIT_CARD = "credit_card"
    PERSONAL_LOAN = "personal_loan"
    STUDENT_LOAN = "student_loan"
    AUTO_LOAN = "auto_loan"
    MORTGAGE = "mortgage"
    COLLECTIONS = "collections"
    PAYDAY_LOAN = "payday_loan"
    OTHER = "other"

class DebtStatus(str, Enum):
    CURRENT = "current"
    DELINQUENT_30 = "delinquent_30"
    DELINQUENT_60 = "delinquent_60"
    DELINQUENT_90 = "delinquent_90"
    COLLECTIONS = "collections"
    CHARGED_OFF = "charged_off"
    SETTLED = "settled"
    PAID = "paid"

class RiskTier(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    CRITICAL = "critical"

class IncomeTier(str, Enum):
    VERY_LOW = "very_low"      # <100% FPL
    LOW = "low"                 # 100-200% FPL
    MODERATE = "moderate"       # 200-400% FPL
    MIDDLE = "middle"           # 400-600% FPL
    UPPER_MIDDLE = "upper_middle"  # 600-800% FPL
    HIGH = "high"               # >800% FPL

class InsuranceType(str, Enum):
    EMPLOYER = "employer"
    MARKETPLACE = "marketplace"
    MEDICARE = "medicare"
    MEDICARE_ADVANTAGE = "medicare_advantage"
    MEDICAID = "medicaid"
    CHIP = "chip"
    TRICARE = "tricare"
    VA = "va"
    PRIVATE = "private"
    SHORT_TERM = "short_term"
    NONE = "none"

class NetworkStatus(str, Enum):
    IN_NETWORK = "in_network"
    OUT_OF_NETWORK = "out_of_network"
    UNKNOWN = "unknown"

class ClaimStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    DENIED = "denied"
    PARTIALLY_APPROVED = "partially_approved"
    APPEALED = "appealed"
    REPROCESSING = "reprocessing"

class BillErrorType(str, Enum):
    DUPLICATE_CHARGE = "duplicate_charge"
    UNBUNDLING = "unbundling"
    UPCODING = "upcoding"
    WRONG_CODE = "wrong_code"
    MODIFIER_ERROR = "modifier_error"
    BALANCE_BILLING = "balance_billing"
    WRONG_PATIENT = "wrong_patient"
    SERVICE_NOT_RENDERED = "service_not_rendered"
    INCORRECT_QUANTITY = "incorrect_quantity"
    PRICING_ERROR = "pricing_error"
    PREVENTIVE_MISCODED = "preventive_miscoded"
    TIMELY_FILING = "timely_filing"
    COORDINATION_ERROR = "coordination_error"
    INVALID_NDC = "invalid_ndc"


# ============================================================================
# INCOME DATA MODELS
# ============================================================================

class IncomeSource(BaseModel):
    """Individual income source with verification status"""
    id: UUID = Field(default_factory=uuid4)
    income_type: IncomeType
    source_name: Optional[str] = None  # Employer name, etc.
    gross_amount: Decimal
    net_amount: Optional[Decimal] = None
    frequency: IncomeFrequency
    is_verified: bool = False
    verification_date: Optional[date] = None
    start_date: Optional[date] = None
    is_stable: bool = True  # False for gig work, seasonal, etc.
    ytd_gross: Optional[Decimal] = None
    
    @computed_field
    @property
    def monthly_gross(self) -> Decimal:
        """Convert any frequency to monthly gross"""
        multipliers = {
            IncomeFrequency.WEEKLY: Decimal("4.333"),
            IncomeFrequency.BIWEEKLY: Decimal("2.167"),
            IncomeFrequency.SEMIMONTHLY: Decimal("2"),
            IncomeFrequency.MONTHLY: Decimal("1"),
            IncomeFrequency.QUARTERLY: Decimal("0.333"),
            IncomeFrequency.ANNUAL: Decimal("0.0833"),
            IncomeFrequency.IRREGULAR: Decimal("1"),  # Assume monthly avg provided
        }
        return self.gross_amount * multipliers.get(self.frequency, Decimal("1"))
    
    @computed_field
    @property
    def annual_gross(self) -> Decimal:
        return self.monthly_gross * 12

class HouseholdMember(BaseModel):
    """Household member for FPL and tax filing purposes"""
    relationship: str  # self, spouse, child, dependent, etc.
    age: int
    is_tax_dependent: bool = True
    has_own_income: bool = False
    income_amount: Decimal = Decimal("0")

class IncomeData(BaseModel):
    """Complete household income profile"""
    id: UUID = Field(default_factory=uuid4)
    tax_filing_status: str = "single"  # single, married_joint, married_separate, head_of_household
    income_sources: list[IncomeSource] = Field(default_factory=list)
    household_members: list[HouseholdMember] = Field(default_factory=list)
    
    # Additional income adjustments
    tax_deductions: Decimal = Decimal("0")  # Pre-tax deductions (401k, HSA, etc.)
    irregular_income_12mo_avg: Optional[Decimal] = None
    
    # State-specific
    state: str
    county: Optional[str] = None
    
    @computed_field
    @property
    def household_size(self) -> int:
        return max(1, len(self.household_members))
    
    @computed_field
    @property
    def total_monthly_gross(self) -> Decimal:
        return sum(src.monthly_gross for src in self.income_sources)
    
    @computed_field
    @property
    def total_annual_gross(self) -> Decimal:
        return self.total_monthly_gross * 12
    
    @computed_field
    @property
    def total_monthly_net(self) -> Decimal:
        """Estimate net if not provided"""
        net_sources = [s for s in self.income_sources if s.net_amount]
        if net_sources:
            ratio = sum(s.net_amount for s in net_sources) / sum(s.gross_amount for s in net_sources)
            return self.total_monthly_gross * ratio
        # Estimate 75% take-home if no net provided
        return self.total_monthly_gross * Decimal("0.75")


# ============================================================================
# DEBT DATA MODELS
# ============================================================================

class DebtAccount(BaseModel):
    """Individual debt account"""
    id: UUID = Field(default_factory=uuid4)
    debt_type: DebtType
    creditor_name: str
    original_amount: Optional[Decimal] = None
    current_balance: Decimal
    credit_limit: Optional[Decimal] = None  # For revolving credit
    interest_rate: Optional[float] = None
    minimum_payment: Decimal = Decimal("0")
    actual_payment: Optional[Decimal] = None
    status: DebtStatus = DebtStatus.CURRENT
    account_age_months: Optional[int] = None
    last_payment_date: Optional[date] = None
    next_due_date: Optional[date] = None
    is_secured: bool = False
    is_medical: bool = False
    original_provider: Optional[str] = None  # For medical debt
    in_collections: bool = False
    collection_agency: Optional[str] = None

class PaymentHistory(BaseModel):
    """Payment history for trend analysis"""
    month: date
    amount_due: Decimal
    amount_paid: Decimal
    was_on_time: bool
    days_late: int = 0

class DebtData(BaseModel):
    """Complete debt profile"""
    id: UUID = Field(default_factory=uuid4)
    accounts: list[DebtAccount] = Field(default_factory=list)
    payment_history: list[PaymentHistory] = Field(default_factory=list)
    
    # Bankruptcy/judgment history
    bankruptcy_history: bool = False
    bankruptcy_date: Optional[date] = None
    bankruptcy_type: Optional[str] = None  # Chapter 7, 13
    active_judgments: bool = False
    
    @computed_field
    @property
    def total_debt(self) -> Decimal:
        return sum(a.current_balance for a in self.accounts)
    
    @computed_field
    @property
    def total_medical_debt(self) -> Decimal:
        return sum(a.current_balance for a in self.accounts if a.is_medical)
    
    @computed_field
    @property
    def total_consumer_debt(self) -> Decimal:
        return sum(a.current_balance for a in self.accounts if not a.is_medical)
    
    @computed_field
    @property
    def total_minimum_payments(self) -> Decimal:
        return sum(a.minimum_payment for a in self.accounts)
    
    @computed_field
    @property
    def medical_debt_in_collections(self) -> Decimal:
        return sum(a.current_balance for a in self.accounts 
                   if a.is_medical and a.in_collections)
    
    @computed_field
    @property
    def delinquent_account_count(self) -> int:
        delinquent = {DebtStatus.DELINQUENT_30, DebtStatus.DELINQUENT_60, 
                      DebtStatus.DELINQUENT_90, DebtStatus.COLLECTIONS}
        return sum(1 for a in self.accounts if a.status in delinquent)


# ============================================================================
# INSURANCE DATA MODELS
# ============================================================================

class CoverageTier(BaseModel):
    """Coverage tier details (individual vs family)"""
    tier_type: str  # individual, individual_plus_one, family
    deductible: Decimal
    deductible_met: Decimal = Decimal("0")
    oop_max: Decimal
    oop_met: Decimal = Decimal("0")

class CopayStructure(BaseModel):
    """Copay amounts by service type"""
    primary_care: Decimal = Decimal("0")
    specialist: Decimal = Decimal("0")
    urgent_care: Decimal = Decimal("0")
    emergency_room: Decimal = Decimal("0")
    generic_rx: Decimal = Decimal("0")
    preferred_rx: Decimal = Decimal("0")
    specialty_rx: Decimal = Decimal("0")
    mental_health: Decimal = Decimal("0")
    preventive: Decimal = Decimal("0")  # Usually $0

class CoverageLimit(BaseModel):
    """Coverage limits and exclusions"""
    service_type: str
    annual_limit: Optional[Decimal] = None
    lifetime_limit: Optional[Decimal] = None
    visit_limit: Optional[int] = None
    requires_preauth: bool = False
    waiting_period_days: int = 0

class InsurancePlan(BaseModel):
    """Comprehensive insurance plan details"""
    id: UUID = Field(default_factory=uuid4)
    plan_name: str
    insurance_type: InsuranceType
    carrier_name: str
    policy_number: str
    group_number: Optional[str] = None
    member_id: str
    
    # Plan dates
    effective_date: date
    termination_date: Optional[date] = None
    plan_year_start: date
    plan_year_end: date
    
    # Network
    network_name: Optional[str] = None
    has_out_of_network_coverage: bool = True
    
    # Coverage tiers
    individual_coverage: CoverageTier
    family_coverage: Optional[CoverageTier] = None
    out_of_network_coverage: Optional[CoverageTier] = None
    
    # Cost sharing
    coinsurance_in_network: float = 0.2  # Patient pays
    coinsurance_out_of_network: float = 0.4
    copays: CopayStructure = Field(default_factory=CopayStructure)
    
    # Special coverage
    coverage_limits: list[CoverageLimit] = Field(default_factory=list)
    excluded_services: list[str] = Field(default_factory=list)
    
    # Coordination
    is_primary: bool = True
    coordination_type: Optional[str] = None  # birthday rule, etc.
    
    @computed_field
    @property
    def deductible_remaining(self) -> Decimal:
        return max(Decimal("0"), 
                   self.individual_coverage.deductible - self.individual_coverage.deductible_met)
    
    @computed_field
    @property
    def oop_remaining(self) -> Decimal:
        return max(Decimal("0"),
                   self.individual_coverage.oop_max - self.individual_coverage.oop_met)
    
    @computed_field
    @property
    def deductible_percentage_met(self) -> float:
        if self.individual_coverage.deductible == 0:
            return 1.0
        return float(self.individual_coverage.deductible_met / self.individual_coverage.deductible)
    
    @computed_field
    @property
    def oop_percentage_met(self) -> float:
        if self.individual_coverage.oop_max == 0:
            return 1.0
        return float(self.individual_coverage.oop_met / self.individual_coverage.oop_max)
    
    @computed_field
    @property
    def days_until_plan_year_end(self) -> int:
        return (self.plan_year_end - date.today()).days


# ============================================================================
# BILL DATA MODELS
# ============================================================================

class BillLineItem(BaseModel):
    """Individual line item on a medical bill"""
    id: UUID = Field(default_factory=uuid4)
    line_number: int
    service_date: date
    
    # Coding
    cpt_code: Optional[str] = None
    hcpcs_code: Optional[str] = None
    icd10_codes: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    ndc_code: Optional[str] = None  # For drugs
    revenue_code: Optional[str] = None  # For facility bills
    
    # Description
    description: str
    place_of_service: Optional[str] = None
    
    # Quantities and amounts
    quantity: int = 1
    unit_price: Decimal
    billed_amount: Decimal
    
    # Insurance processing
    allowed_amount: Optional[Decimal] = None
    adjustment_amount: Decimal = Decimal("0")
    insurance_paid: Decimal = Decimal("0")
    patient_responsibility: Decimal
    
    # Breakdown of patient responsibility
    applied_to_deductible: Decimal = Decimal("0")
    coinsurance_amount: Decimal = Decimal("0")
    copay_amount: Decimal = Decimal("0")
    not_covered_amount: Decimal = Decimal("0")
    
    # Flags
    is_covered: bool = True
    denial_reason: Optional[str] = None
    requires_review: bool = False
    review_reason: Optional[str] = None

class ParsedBill(BaseModel):
    """Complete parsed medical bill"""
    id: UUID = Field(default_factory=uuid4)
    
    # Provider info
    provider_name: str
    provider_npi: Optional[str] = None
    provider_tax_id: Optional[str] = None
    provider_type: str  # hospital, physician, lab, DME, etc.
    facility_type: Optional[str] = None  # inpatient, outpatient, ER, ASC
    billing_address: Optional[str] = None
    billing_phone: Optional[str] = None
    
    # Patient/account info
    patient_name: str
    patient_account_number: str
    medical_record_number: Optional[str] = None
    
    # Dates
    statement_date: date
    service_date_start: date
    service_date_end: date
    admission_date: Optional[date] = None
    discharge_date: Optional[date] = None
    
    # Bill details
    line_items: list[BillLineItem] = Field(default_factory=list)
    
    # Totals
    total_charges: Decimal
    total_adjustments: Decimal = Decimal("0")
    total_insurance_paid: Decimal = Decimal("0")
    patient_balance: Decimal
    prior_balance: Decimal = Decimal("0")
    payments_received: Decimal = Decimal("0")
    
    # Insurance info from bill
    insurance_claim_number: Optional[str] = None
    insurance_processed: bool = False
    claim_status: ClaimStatus = ClaimStatus.PENDING
    eob_date: Optional[date] = None
    
    # Payment terms
    due_date: Optional[date] = None
    payment_plan_available: bool = False
    financial_assistance_notice: bool = False
    
    # Network status
    network_status: NetworkStatus = NetworkStatus.UNKNOWN
    
    @computed_field
    @property
    def days_until_due(self) -> Optional[int]:
        if self.due_date:
            return (self.due_date - date.today()).days
        return None
    
    @computed_field
    @property
    def total_line_items(self) -> int:
        return len(self.line_items)
    
    @computed_field
    @property
    def unique_cpt_codes(self) -> list[str]:
        return list(set(li.cpt_code for li in self.line_items if li.cpt_code))


# ============================================================================
# USER FINANCIAL PROFILE (UNIFIED INPUT)
# ============================================================================

class UserFinancialProfile(BaseModel):
    """Complete user financial profile - unified input model"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Core components
    income: IncomeData
    debt: DebtData
    insurance: Optional[InsurancePlan] = None
    secondary_insurance: Optional[InsurancePlan] = None
    bills: list[ParsedBill] = Field(default_factory=list)
    
    # Additional context
    zip_code: str
    has_hsa: bool = False
    hsa_balance: Decimal = Decimal("0")
    has_fsa: bool = False
    fsa_balance: Decimal = Decimal("0")
    fsa_deadline: Optional[date] = None
    
    # Upcoming known expenses
    expected_procedures: list[dict] = Field(default_factory=list)
    
    # Preferences
    preferred_payment_timeline: Optional[int] = None  # months
    can_pay_lump_sum: bool = False
    max_monthly_payment: Optional[Decimal] = None