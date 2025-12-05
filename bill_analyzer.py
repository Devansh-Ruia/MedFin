"""
MedFin Analysis Engine - Bill Analyzer Module
Comprehensive bill analysis with error detection and negotiation scoring
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class BillAnalyzer:
    """Analyzes medical bills for errors, duplicates, and negotiation opportunities"""
    
    # CPT Bundling Rules (CCI Edits - simplified subset)
    # Format: parent_code -> [codes that should be bundled into parent]
    BUNDLING_RULES = {
        # E&M bundling
        "99213": ["99211", "99212"],
        "99214": ["99211", "99212", "99213"],
        "99215": ["99211", "99212", "99213", "99214"],
        
        # Surgical bundling
        "43239": ["43235"],  # EGD with biopsy includes diagnostic
        "29881": ["29880"],  # Knee arthroscopy
        "47562": ["47563"],  # Lap chole
        "27447": ["27446"],  # TKA
        
        # Injection bundling
        "96372": ["96374"],  # Injection administration
        
        # Lab bundling
        "80053": ["80048"],  # Comprehensive includes basic metabolic
        "85025": ["85027"],  # CBC with diff includes CBC
    }
    
    # Preventive care CPT codes (should have $0 cost share)
    PREVENTIVE_CODES = {
        "99381", "99382", "99383", "99384", "99385", "99386", "99387",
        "99391", "99392", "99393", "99394", "99395", "99396", "99397",
        "G0438", "G0439", "G0402",
        "77067", "G0101", "G0123", "G0124",
        "82270", "G0104", "G0105", "G0121",
        "36415",  # Venipuncture for preventive labs
    }
    
    # Typical fair price multipliers by facility type
    FAIR_PRICE_MULTIPLIERS = {
        "hospital_inpatient": 2.5,
        "hospital_outpatient": 2.0,
        "ambulatory_surgical_center": 1.5,
        "physician_office": 1.2,
        "urgent_care": 1.4,
        "emergency_room": 3.0,
        "laboratory": 1.0,
        "imaging_center": 1.3,
    }
    
    def __init__(self):
        self.analysis_results = []
    
    def analyze(self, bills: list['ParsedBill'],
                insurance: Optional['InsurancePlan'] = None,
                fpl_percentage: float = 500) -> 'BillAnalysisOutput':
        """Analyze all bills and produce comprehensive output"""
        
        bill_analyses = []
        total_errors = 0
        total_savings = Decimal("0")
        errors_by_type = defaultdict(int)
        
        for bill in bills:
            analysis = self._analyze_single_bill(bill, insurance, fpl_percentage)
            bill_analyses.append(analysis)
            
            total_errors += len(analysis.errors)
            total_savings += analysis.total_potential_recovery
            
            for error in analysis.errors:
                errors_by_type[error.error_type.value] += 1
        
        # Identify high-priority disputes
        all_errors = []
        for ba in bill_analyses:
            all_errors.extend(ba.errors)
        
        high_priority = [
            str(e.error_id) for e in all_errors
            if e.severity in [RiskTier.HIGH, RiskTier.SEVERE, RiskTier.CRITICAL]
        ]
        
        # Generate dispute sequence (by expected recovery, descending)
        dispute_sequence = [
            str(e.error_id) for e in 
            sorted(all_errors, key=lambda e: e.potential_recovery, reverse=True)
        ]
        
        # Calculate overall billing accuracy
        total_items = sum(ba.bill.total_line_items for ba in bill_analyses)
        accuracy = 1.0 - (total_errors / total_items) if total_items > 0 else 1.0
        
        # Generate immediate actions
        immediate_actions = self._generate_immediate_actions(bill_analyses)
        
        return BillAnalysisOutput(
            bill_analyses=bill_analyses,
            total_bills_analyzed=len(bills),
            total_patient_balance=sum(b.patient_balance for b in bills),
            total_errors_found=total_errors,
            total_potential_savings=total_savings,
            errors_by_type=dict(errors_by_type),
            high_priority_disputes=high_priority,
            billing_accuracy_score=max(0.0, accuracy),
            immediate_actions=immediate_actions,
            dispute_sequence=dispute_sequence
        )
    
    def _analyze_single_bill(self, bill: 'ParsedBill',
                              insurance: Optional['InsurancePlan'],
                              fpl_percentage: float) -> 'SingleBillAnalysis':
        """Analyze a single bill comprehensively"""
        
        errors = []
        duplicates = []
        bundling_issues = []
        preventive_flags = []
        
        # 1. Detect duplicate charges
        dups = self._detect_duplicates(bill)
        duplicates.extend(dups)
        for dup in dups:
            errors.append(self._duplicate_to_error(bill, dup))
        
        # 2. Detect unbundling
        bundles = self._detect_unbundling(bill)
        bundling_issues.extend(bundles)
        for bundle in bundles:
            errors.append(self._bundling_to_error(bill, bundle))
        
        # 3. Check preventive care coding
        prev_flags = self._check_preventive_care(bill)
        preventive_flags.extend(prev_flags)
        for flag in prev_flags:
            errors.append(self._preventive_to_error(bill, flag))
        
        # 4. Check for pricing errors
        pricing_errors = self._check_pricing(bill, insurance)
        errors.extend(pricing_errors)
        
        # 5. Check for modifier errors
        modifier_errors = self._check_modifiers(bill)
        errors.extend(modifier_errors)
        
        # 6. Check balance billing (if applicable)
        if insurance and bill.network_status == NetworkStatus.OUT_OF_NETWORK:
            balance_errors = self._check_balance_billing(bill, insurance)
            errors.extend(balance_errors)
        
        # 7. Calculate totals
        total_overcharge = sum(e.overcharge_amount for e in errors)
        total_recovery = sum(e.potential_recovery for e in errors)
        
        # 8. Generate negotiation opportunities
        negotiations = self._generate_negotiation_opportunities(
            bill, insurance, fpl_percentage, errors
        )
        
        # 9. Calculate urgency
        urgency = self._calculate_urgency(bill, errors)
        
        # 10. Calculate collections risk
        collections_risk = self._calculate_collections_risk(bill)
        
        return SingleBillAnalysis(
            bill_id=str(bill.id),
            provider_name=bill.provider_name,
            patient_balance=bill.patient_balance,
            errors=errors,
            duplicates=duplicates,
            bundling_issues=bundling_issues,
            preventive_care_flags=preventive_flags,
            total_overcharge_identified=total_overcharge,
            total_potential_recovery=total_recovery,
            negotiation_opportunities=negotiations,
            urgency_score=urgency,
            days_until_due=bill.days_until_due,
            collections_risk=collections_risk
        )
    
    def _detect_duplicates(self, bill: 'ParsedBill') -> list['DuplicateCharge']:
        """Detect duplicate line items"""
        duplicates = []
        seen = {}
        
        for item in bill.line_items:
            # Create key for comparison
            key = (
                item.cpt_code or item.hcpcs_code,
                item.service_date,
                str(item.billed_amount)
            )
            
            if key in seen:
                match_type = "exact"
                confidence = 0.95
                
                duplicates.append(DuplicateCharge(
                    original_line_id=str(seen[key]),
                    duplicate_line_id=str(item.id),
                    charge_amount=item.billed_amount,
                    service_date=item.service_date,
                    cpt_code=item.cpt_code,
                    match_confidence=confidence,
                    match_type=match_type
                ))
            else:
                seen[key] = item.id
        
        # Also check for similar charges (potential duplicates)
        items_by_code = defaultdict(list)
        for item in bill.line_items:
            if item.cpt_code:
                items_by_code[item.cpt_code].append(item)
        
        for code, items in items_by_code.items():
            if len(items) > 1:
                # Check if quantities seem excessive
                for i, item in enumerate(items[1:], 1):
                    # Same code, same date, similar amount
                    if (item.service_date == items[0].service_date and
                        abs(item.billed_amount - items[0].billed_amount) < items[0].billed_amount * Decimal("0.1")):
                        
                        dup_key = (item.cpt_code, item.service_date, str(item.billed_amount))
                        if dup_key not in seen:
                            duplicates.append(DuplicateCharge(
                                original_line_id=str(items[0].id),
                                duplicate_line_id=str(item.id),
                                charge_amount=item.billed_amount,
                                service_date=item.service_date,
                                cpt_code=item.cpt_code,
                                match_confidence=0.75,
                                match_type="similar"
                            ))
        
        return duplicates
    
    def _detect_unbundling(self, bill: 'ParsedBill') -> list['BundlingIssue']:
        """Detect potential unbundling issues"""
        issues = []
        codes_present = {
            item.cpt_code for item in bill.line_items 
            if item.cpt_code
        }
        
        for parent_code, child_codes in self.BUNDLING_RULES.items():
            if parent_code in codes_present:
                for child in child_codes:
                    if child in codes_present:
                        # Found unbundling
                        parent_item = next(
                            (i for i in bill.line_items if i.cpt_code == parent_code),
                            None
                        )
                        child_item = next(
                            (i for i in bill.line_items if i.cpt_code == child),
                            None
                        )
                        
                        if parent_item and child_item:
                            issues.append(BundlingIssue(
                                parent_code=parent_code,
                                child_codes=[child],
                                issue_type="unbundled",
                                overbilled_amount=child_item.billed_amount,
                                correct_billing_amount=Decimal("0"),  # Should be included
                                cci_edit_reference=f"CCI {parent_code}/{child}"
                            ))
        
        return issues
    
    def _check_preventive_care(self, bill: 'ParsedBill') -> list['PreventiveCareFlag']:
        """Check for preventive care that was charged cost-share"""
        flags = []
        
        for item in bill.line_items:
            if item.cpt_code in self.PREVENTIVE_CODES:
                if item.patient_responsibility > Decimal("0"):
                    # Check if diagnosis might be causing the issue
                    reason = "ACA preventive service should be $0"
                    if item.icd10_codes:
                        non_preventive = [c for c in item.icd10_codes if not c.startswith("Z")]
                        if non_preventive:
                            reason = f"Non-preventive diagnosis {non_preventive[0]} may be causing cost share"
                    
                    flags.append(PreventiveCareFlag(
                        bill_id=str(bill.id),
                        line_item_id=str(item.id),
                        service_description=item.description,
                        cpt_code=item.cpt_code,
                        reason_should_be_preventive=reason,
                        patient_charged=item.patient_responsibility,
                        uspstf_reference="USPSTF A/B recommendation"
                    ))
        
        return flags
    
    def _check_pricing(self, bill: 'ParsedBill',
                       insurance: Optional['InsurancePlan']) -> list['BillError']:
        """Check for pricing anomalies"""
        errors = []
        
        for item in bill.line_items:
            # Check if billed amount vastly exceeds allowed
            if item.allowed_amount and item.allowed_amount > 0:
                ratio = item.billed_amount / item.allowed_amount
                if ratio > Decimal("5.0"):
                    errors.append(BillError(
                        bill_id=str(bill.id),
                        line_item_id=str(item.id),
                        error_type=BillErrorType.PRICING_ERROR,
                        severity=RiskTier.MODERATE,
                        description=f"Billed amount {ratio:.1f}x higher than allowed",
                        evidence=[
                            f"Billed: ${item.billed_amount}",
                            f"Allowed: ${item.allowed_amount}"
                        ],
                        overcharge_amount=item.billed_amount - item.allowed_amount,
                        potential_recovery=Decimal("0"),  # Insurance handles this
                        recovery_confidence=0.3,
                        dispute_recommended=False,
                        estimated_resolution_days=0,
                        required_documents=[]
                    ))
            
            # Check quantity
            if item.quantity > 10:
                errors.append(BillError(
                    bill_id=str(bill.id),
                    line_item_id=str(item.id),
                    error_type=BillErrorType.INCORRECT_QUANTITY,
                    severity=RiskTier.MODERATE,
                    description=f"Unusually high quantity: {item.quantity}",
                    evidence=[f"Quantity billed: {item.quantity}"],
                    overcharge_amount=item.unit_price * (item.quantity - 1),
                    potential_recovery=item.patient_responsibility * Decimal("0.5"),
                    recovery_confidence=0.5,
                    dispute_recommended=True,
                    estimated_resolution_days=30,
                    required_documents=["medical_records"]
                ))
        
        return errors
    
    def _check_modifiers(self, bill: 'ParsedBill') -> list['BillError']:
        """Check for modifier issues"""
        errors = []
        
        for item in bill.line_items:
            # Check for missing bilateral modifier
            if item.quantity == 2 and "50" not in item.modifiers:
                # Might need -50 modifier instead of quantity 2
                errors.append(BillError(
                    bill_id=str(bill.id),
                    line_item_id=str(item.id),
                    error_type=BillErrorType.MODIFIER_ERROR,
                    severity=RiskTier.LOW,
                    description="Possible missing bilateral modifier (-50)",
                    evidence=["Quantity 2 without bilateral modifier"],
                    overcharge_amount=item.unit_price,
                    potential_recovery=item.patient_responsibility * Decimal("0.2"),
                    recovery_confidence=0.4,
                    dispute_recommended=False,
                    estimated_resolution_days=30,
                    required_documents=[]
                ))
        
        return errors
    
    def _check_balance_billing(self, bill: 'ParsedBill',
                                insurance: 'InsurancePlan') -> list['BillError']:
        """Check for illegal balance billing"""
        errors = []
        
        # Emergency services should be protected from balance billing
        if bill.facility_type in ["emergency_room", "ER"]:
            for item in bill.line_items:
                if item.allowed_amount:
                    excess = item.patient_responsibility - (
                        item.allowed_amount * Decimal(str(insurance.coinsurance_in_network))
                    )
                    if excess > Decimal("50"):
                        errors.append(BillError(
                            bill_id=str(bill.id),
                            line_item_id=str(item.id),
                            error_type=BillErrorType.BALANCE_BILLING,
                            severity=RiskTier.HIGH,
                            description="Potential illegal ER balance billing",
                            evidence=[
                                f"Charged: ${item.patient_responsibility}",
                                f"Should be: ${item.allowed_amount * Decimal(str(insurance.coinsurance_in_network))}"
                            ],
                            overcharge_amount=excess,
                            potential_recovery=excess,
                            recovery_confidence=0.75,
                            dispute_recommended=True,
                            estimated_resolution_days=45,
                            required_documents=["eob", "itemized_bill"]
                        ))
        
        return errors
    
    def _duplicate_to_error(self, bill: 'ParsedBill', 
                            dup: 'DuplicateCharge') -> 'BillError':
        """Convert duplicate charge to error"""
        return BillError(
            bill_id=str(bill.id),
            line_item_id=dup.duplicate_line_id,
            error_type=BillErrorType.DUPLICATE_CHARGE,
            severity=RiskTier.HIGH,
            description=f"Duplicate charge for {dup.cpt_code or 'service'}",
            evidence=[
                f"Original: {dup.original_line_id}",
                f"Duplicate: {dup.duplicate_line_id}",
                f"Amount: ${dup.charge_amount}"
            ],
            overcharge_amount=dup.charge_amount,
            potential_recovery=dup.charge_amount * Decimal(str(dup.match_confidence)),
            recovery_confidence=dup.match_confidence,
            dispute_recommended=True,
            estimated_resolution_days=14,
            required_documents=["itemized_bill"]
        )
    
    def _bundling_to_error(self, bill: 'ParsedBill',
                            bundle: 'BundlingIssue') -> 'BillError':
        """Convert bundling issue to error"""
        return BillError(
            bill_id=str(bill.id),
            line_item_id=None,
            error_type=BillErrorType.UNBUNDLING,
            severity=RiskTier.HIGH,
            description=f"Unbundling: {bundle.child_codes[0]} should be included in {bundle.parent_code}",
            evidence=[
                f"Parent code: {bundle.parent_code}",
                f"Child code: {bundle.child_codes[0]}",
                f"CCI Edit: {bundle.cci_edit_reference}"
            ],
            overcharge_amount=bundle.overbilled_amount,
            potential_recovery=bundle.overbilled_amount * Decimal("0.85"),
            recovery_confidence=0.80,
            dispute_recommended=True,
            estimated_resolution_days=30,
            required_documents=["itemized_bill", "medical_records"]
        )
    
    def _preventive_to_error(self, bill: 'ParsedBill',
                              flag: 'PreventiveCareFlag') -> 'BillError':
        """Convert preventive care flag to error"""
        return BillError(
            bill_id=str(bill.id),
            line_item_id=flag.line_item_id,
            error_type=BillErrorType.PREVENTIVE_MISCODED,
            severity=RiskTier.MODERATE,
            description=f"Preventive service charged cost-share: {flag.cpt_code}",
            evidence=[
                f"Service: {flag.service_description}",
                f"Amount charged: ${flag.patient_charged}",
                flag.reason_should_be_preventive
            ],
            overcharge_amount=flag.patient_charged,
            potential_recovery=flag.patient_charged,
            recovery_confidence=0.70,
            dispute_recommended=True,
            estimated_resolution_days=21,
            required_documents=["eob"]
        )
    
    def _generate_negotiation_opportunities(self, bill: 'ParsedBill',
                                             insurance: Optional['InsurancePlan'],
                                             fpl_percentage: float,
                                             errors: list['BillError']) -> list['NegotiationOpportunity']:
        """Generate negotiation opportunities for a bill"""
        opportunities = []
        balance = bill.patient_balance
        
        # Error-based savings already calculated
        error_savings = sum(e.potential_recovery for e in errors)
        remaining = balance - error_savings
        
        if remaining <= 0:
            return opportunities
        
        # 1. Prompt-pay discount (almost always available)
        if remaining > Decimal("200"):
            opportunities.append(NegotiationOpportunity(
                bill_id=str(bill.id),
                negotiation_type="prompt_pay",
                current_balance=remaining,
                target_amount=remaining * Decimal("0.80"),
                expected_savings=remaining * Decimal("0.20"),
                savings_confidence=0.70,
                negotiation_script_points=[
                    "I'd like to pay this bill in full today",
                    "What prompt-pay discount can you offer?",
                    "I've seen discounts of 15-25% for immediate payment"
                ],
                leverage_factors=["Immediate payment", "Reduced collection costs"],
                best_time_to_call="Tuesday-Thursday, 10am-2pm",
                decision_maker_title="Billing Supervisor"
            ))
        
        # 2. Financial hardship discount
        if fpl_percentage < 400:
            discount = 0.50 if fpl_percentage < 200 else 0.35 if fpl_percentage < 300 else 0.20
            opportunities.append(NegotiationOpportunity(
                bill_id=str(bill.id),
                negotiation_type="financial_hardship",
                current_balance=remaining,
                target_amount=remaining * Decimal(str(1 - discount)),
                expected_savings=remaining * Decimal(str(discount)),
                savings_confidence=0.60 if fpl_percentage < 250 else 0.45,
                negotiation_script_points=[
                    f"My income is at {fpl_percentage:.0f}% of federal poverty level",
                    "I'm requesting a financial hardship adjustment",
                    "I'm willing to set up a payment plan for the reduced amount"
                ],
                leverage_factors=[f"Income at {fpl_percentage:.0f}% FPL", "Documented hardship"],
                best_time_to_call="Tuesday-Thursday morning",
                decision_maker_title="Patient Financial Services Manager"
            ))
        
        # 3. Cash-pay discount (for uninsured/high-deductible)
        if not insurance or (insurance and insurance.deductible_remaining > balance):
            opportunities.append(NegotiationOpportunity(
                bill_id=str(bill.id),
                negotiation_type="cash_pay",
                current_balance=remaining,
                target_amount=remaining * Decimal("0.60"),
                expected_savings=remaining * Decimal("0.40"),
                savings_confidence=0.55,
                negotiation_script_points=[
                    "I'm paying out of pocket for this service",
                    "What is your cash-pay or self-pay rate?",
                    "I'd like to negotiate to the Medicare rate"
                ],
                leverage_factors=["Self-pay", "No insurance processing costs"],
                best_time_to_call="End of month/quarter",
                decision_maker_title="Billing Manager"
            ))
        
        return opportunities
    
    def _calculate_urgency(self, bill: 'ParsedBill',
                           errors: list['BillError']) -> int:
        """Calculate urgency score (0-100)"""
        score = 30  # Base score
        
        # Due date factors
        if bill.days_until_due is not None:
            if bill.days_until_due < 0:
                score += 35  # Past due
            elif bill.days_until_due < 7:
                score += 25
            elif bill.days_until_due < 14:
                score += 15
            elif bill.days_until_due < 30:
                score += 10
        
        # Balance factors
        if bill.patient_balance > Decimal("10000"):
            score += 15
        elif bill.patient_balance > Decimal("5000"):
            score += 10
        elif bill.patient_balance > Decimal("1000"):
            score += 5
        
        # Error factors (more errors = more urgent to dispute)
        if len(errors) > 3:
            score += 10
        elif len(errors) > 0:
            score += 5
        
        # High-severity errors
        high_sev = sum(1 for e in errors if e.severity in [RiskTier.HIGH, RiskTier.SEVERE])
        score += high_sev * 5
        
        return min(100, score)
    
    def _calculate_collections_risk(self, bill: 'ParsedBill') -> float:
        """Calculate risk of bill going to collections"""
        risk = 0.05  # Base risk
        
        if bill.days_until_due is not None:
            if bill.days_until_due < -90:
                risk = 0.90
            elif bill.days_until_due < -60:
                risk = 0.70
            elif bill.days_until_due < -30:
                risk = 0.50
            elif bill.days_until_due < 0:
                risk = 0.30
            elif bill.days_until_due < 14:
                risk = 0.15
        
        # Higher balances = higher collection likelihood
        if bill.patient_balance > Decimal("5000"):
            risk = min(1.0, risk + 0.10)
        
        return risk
    
    def _generate_immediate_actions(self, 
                                     bill_analyses: list['SingleBillAnalysis']) -> list[str]:
        """Generate immediate action recommendations"""
        actions = []
        
        # Check for past-due bills
        past_due = [ba for ba in bill_analyses if ba.days_until_due and ba.days_until_due < 0]
        if past_due:
            actions.append(f"URGENT: {len(past_due)} bill(s) are past due - contact providers immediately")
        
        # Check for high-value errors
        high_value_errors = []
        for ba in bill_analyses:
            for error in ba.errors:
                if error.potential_recovery > Decimal("500"):
                    high_value_errors.append(error)
        
        if high_value_errors:
            total = sum(e.potential_recovery for e in high_value_errors)
            actions.append(f"Dispute billing errors: ${total:,.0f} potential recovery identified")
        
        # Check for unsubmitted claims
        for ba in bill_analyses:
            # This would check claim status
            pass
        
        actions.append("Request itemized bills from all providers")
        actions.append("Do not make payments until all errors are resolved")
        
        return actions