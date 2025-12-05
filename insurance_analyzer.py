"""
MedFin Analysis Engine - Insurance Analyzer Module
Comprehensive insurance coverage analysis with gap detection and optimization
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class InsuranceAnalyzer:
    """Analyzes insurance coverage, tracks deductibles, and identifies opportunities"""
    
    # Preventive care CPT codes (ACA-mandated free preventive services)
    PREVENTIVE_CPT_CODES = {
        "99381", "99382", "99383", "99384", "99385", "99386", "99387",  # Preventive visits
        "99391", "99392", "99393", "99394", "99395", "99396", "99397",  # Est. patient preventive
        "G0438", "G0439",  # AWV
        "G0402",  # IPPE
        "77067",  # Mammogram screening
        "G0101", "G0123", "G0124",  # Cervical/pelvic
        "82270",  # Occult blood
        "G0104", "G0105", "G0121",  # Colorectal screening
    }
    
    # Common coverage issues
    COMMON_EXCLUSIONS = {
        "cosmetic", "experimental", "infertility", "weight_loss",
        "dental", "vision", "hearing_aids"
    }
    
    def __init__(self):
        self.analysis_result = None
    
    def analyze(self, insurance: 'InsurancePlan',
                bills: list['ParsedBill'],
                expected_procedures: list[dict] = None,
                secondary_insurance: Optional['InsurancePlan'] = None
               ) -> 'InsuranceAnalysisOutput':
        """Perform comprehensive insurance analysis"""
        
        expected_procedures = expected_procedures or []
        
        # Step 1: Analyze deductible status
        ded_status = self._analyze_deductible(insurance, bills)
        
        # Step 2: Analyze OOP max status
        oop_status = self._analyze_oop_max(insurance, bills)
        
        # Step 3: Analyze family coverage if applicable
        family_ded = None
        family_oop = None
        if insurance.family_coverage:
            family_ded = self._analyze_family_deductible(insurance, bills)
            family_oop = self._analyze_family_oop(insurance, bills)
        
        # Step 4: Calculate year-end strategy
        days_remaining = insurance.days_until_plan_year_end
        year_end_strategy = self._generate_year_end_strategy(
            insurance, ded_status, oop_status, days_remaining
        )
        
        # Step 5: Identify coverage gaps
        coverage_gaps = self._identify_coverage_gaps(insurance, bills)
        
        # Step 6: Find coding mismatches
        coding_mismatches = self._find_coding_mismatches(insurance, bills)
        
        # Step 7: Match upcoming procedures to coverage
        coverage_matches = self._match_procedures(
            insurance, expected_procedures
        )
        
        # Step 8: Generate warnings
        coverage_warnings = self._generate_coverage_warnings(
            insurance, ded_status, oop_status, bills
        )
        network_warnings = self._generate_network_warnings(insurance, bills)
        
        # Step 9: Analyze coordination
        coord_status = None
        coord_savings = Decimal("0")
        if secondary_insurance:
            coord_status, coord_savings = self._analyze_coordination(
                insurance, secondary_insurance, bills
            )
        
        # Step 10: Calculate plan adequacy
        adequacy = self._calculate_plan_adequacy(
            insurance, coverage_gaps, coding_mismatches
        )
        
        # Step 11: Estimate uncovered exposure
        uncovered = self._estimate_uncovered_exposure(insurance, bills, coverage_gaps)
        
        return InsuranceAnalysisOutput(
            deductible_status=ded_status,
            oop_status=oop_status,
            family_deductible_status=family_ded,
            family_oop_status=family_oop,
            days_remaining_in_plan_year=days_remaining,
            deductible_reset_date=insurance.plan_year_end,
            year_end_strategy=year_end_strategy,
            coverage_gaps=coverage_gaps,
            coding_mismatches=coding_mismatches,
            coverage_matches=coverage_matches,
            coverage_warnings=coverage_warnings,
            network_warnings=network_warnings,
            coordination_status=coord_status,
            coordination_savings_estimate=coord_savings,
            plan_adequacy_score=adequacy,
            uncovered_exposure_estimate=uncovered
        )
    
    def _analyze_deductible(self, ins: 'InsurancePlan',
                            bills: list['ParsedBill']) -> 'DeductibleStatus':
        """Analyze individual deductible status"""
        cov = ins.individual_coverage
        
        # Calculate pending amounts toward deductible
        pending_toward_ded = sum(
            sum(li.applied_to_deductible for li in b.line_items)
            for b in bills if b.claim_status in [ClaimStatus.PENDING, ClaimStatus.PROCESSING]
        )
        
        total_pending = sum(b.patient_balance for b in bills)
        remaining = cov.deductible - cov.deductible_met
        
        will_meet = pending_toward_ded >= remaining or total_pending >= remaining
        
        # Estimate date to meet
        est_date = None
        if will_meet and bills:
            # Find the bill that would push us over
            sorted_bills = sorted(bills, key=lambda b: b.service_date_start)
            cumulative = cov.deductible_met
            for bill in sorted_bills:
                ded_amount = sum(li.applied_to_deductible for li in bill.line_items)
                cumulative += ded_amount
                if cumulative >= cov.deductible:
                    est_date = bill.service_date_start
                    break
        
        return DeductibleStatus(
            total_deductible=cov.deductible,
            amount_met=cov.deductible_met,
            amount_remaining=remaining,
            percentage_met=float(cov.deductible_met / cov.deductible) if cov.deductible > 0 else 1.0,
            will_meet_with_pending_bills=will_meet,
            estimated_date_to_meet=est_date,
            amount_pending_toward_deductible=pending_toward_ded
        )
    
    def _analyze_oop_max(self, ins: 'InsurancePlan',
                         bills: list['ParsedBill']) -> 'OOPStatus':
        """Analyze out-of-pocket maximum status"""
        cov = ins.individual_coverage
        
        met = cov.oop_met
        total = cov.oop_max
        remaining = total - met
        pct = float(met / total) if total > 0 else 1.0
        
        # Determine proximity tier
        if pct >= 1.0:
            proximity = "met"
        elif pct >= 0.85:
            proximity = "very_close"
        elif pct >= 0.70:
            proximity = "close"
        elif pct >= 0.50:
            proximity = "moderate"
        else:
            proximity = "far"
        
        # Calculate potential savings after max
        pending_total = sum(b.patient_balance for b in bills)
        will_meet = pending_total >= remaining
        savings_after = max(Decimal("0"), pending_total - remaining) if will_meet else Decimal("0")
        
        # Generate recommendation
        rec = None
        days_left = ins.days_until_plan_year_end
        
        if proximity == "very_close" and days_left < 60:
            rec = "Schedule any elective procedures before plan year ends"
        elif proximity == "close" and days_left < 90:
            rec = "You may reach your OOP max - consider planned care now"
        elif proximity == "met":
            rec = "OOP max reached - additional care is fully covered"
        
        return OOPStatus(
            total_oop_max=total,
            amount_met=met,
            amount_remaining=remaining,
            percentage_met=pct,
            proximity_tier=proximity,
            will_meet_with_pending_bills=will_meet,
            potential_savings_after_max=savings_after,
            elective_care_recommendation=rec
        )
    
    def _analyze_family_deductible(self, ins: 'InsurancePlan',
                                    bills: list['ParsedBill']) -> 'DeductibleStatus':
        """Analyze family deductible (if applicable)"""
        if not ins.family_coverage:
            return None
        
        cov = ins.family_coverage
        remaining = cov.deductible - cov.deductible_met
        
        return DeductibleStatus(
            total_deductible=cov.deductible,
            amount_met=cov.deductible_met,
            amount_remaining=remaining,
            percentage_met=float(cov.deductible_met / cov.deductible) if cov.deductible > 0 else 1.0,
            will_meet_with_pending_bills=False,  # Would need family-level bills
            estimated_date_to_meet=None,
            amount_pending_toward_deductible=Decimal("0")
        )
    
    def _analyze_family_oop(self, ins: 'InsurancePlan',
                            bills: list['ParsedBill']) -> 'OOPStatus':
        """Analyze family OOP max"""
        if not ins.family_coverage:
            return None
        
        cov = ins.family_coverage
        pct = float(cov.oop_met / cov.oop_max) if cov.oop_max > 0 else 1.0
        
        if pct >= 1.0:
            proximity = "met"
        elif pct >= 0.85:
            proximity = "very_close"
        else:
            proximity = "far"
        
        return OOPStatus(
            total_oop_max=cov.oop_max,
            amount_met=cov.oop_met,
            amount_remaining=cov.oop_max - cov.oop_met,
            percentage_met=pct,
            proximity_tier=proximity,
            will_meet_with_pending_bills=False,
            potential_savings_after_max=Decimal("0"),
            elective_care_recommendation=None
        )
    
    def _generate_year_end_strategy(self, ins: 'InsurancePlan',
                                     ded: 'DeductibleStatus',
                                     oop: 'OOPStatus',
                                     days_left: int) -> Optional[str]:
        """Generate year-end insurance strategy"""
        if days_left > 90:
            return None
        
        strategies = []
        
        if oop.proximity_tier in ["very_close", "close"] and days_left < 60:
            strategies.append("Schedule elective care before deductible resets")
        
        if ded.percentage_met > 0.8 and days_left < 45:
            strategies.append("Deductible nearly met - maximize covered care now")
        
        if oop.proximity_tier == "met":
            strategies.append("OOP max reached - all additional care is fully covered")
        
        if not strategies:
            if days_left < 30:
                strategies.append("Plan year ending soon - verify all claims processed")
        
        return "; ".join(strategies) if strategies else None
    
    def _identify_coverage_gaps(self, ins: 'InsurancePlan',
                                 bills: list['ParsedBill']) -> list['CoverageGap']:
        """Identify coverage gaps from bills and plan details"""
        gaps = []
        
        for bill in bills:
            # Check for out-of-network issues
            if bill.network_status == NetworkStatus.OUT_OF_NETWORK:
                # Estimate exposure
                exposure = bill.patient_balance
                if ins.out_of_network_coverage:
                    oon = ins.out_of_network_coverage
                    exposure = exposure * Decimal(str(ins.coinsurance_out_of_network))
                
                gaps.append(CoverageGap(
                    gap_type="out_of_network",
                    description=f"Out-of-network charges at {bill.provider_name}",
                    affected_service=bill.provider_type,
                    financial_exposure=exposure,
                    mitigation_options=[
                        "Request network exception",
                        "Appeal as emergency/unavoidable",
                        "Negotiate out-of-network rate"
                    ],
                    severity=RiskTier.MODERATE if exposure < Decimal("1000") else RiskTier.HIGH
                ))
            
            # Check for denied items
            denied_items = [li for li in bill.line_items if not li.is_covered]
            if denied_items:
                total_denied = sum(li.patient_responsibility for li in denied_items)
                gaps.append(CoverageGap(
                    gap_type="claim_denial",
                    description=f"Services denied coverage on {bill.provider_name} bill",
                    affected_service=denied_items[0].description,
                    financial_exposure=total_denied,
                    mitigation_options=[
                        "Request denial reason in writing",
                        "File appeal with supporting documentation",
                        "Request peer-to-peer review"
                    ],
                    severity=RiskTier.HIGH if total_denied > Decimal("500") else RiskTier.MODERATE
                ))
        
        # Check for plan exclusions
        for exclusion in ins.excluded_services:
            gaps.append(CoverageGap(
                gap_type="plan_exclusion",
                description=f"{exclusion.replace('_', ' ').title()} services excluded",
                affected_service=exclusion,
                financial_exposure=Decimal("0"),  # Unknown
                mitigation_options=["Seek alternative coverage", "Budget for out-of-pocket"],
                severity=RiskTier.LOW
            ))
        
        return gaps
    
    def _find_coding_mismatches(self, ins: 'InsurancePlan',
                                 bills: list['ParsedBill']) -> list['CodingMismatch']:
        """Find potential coding issues affecting coverage"""
        mismatches = []
        
        for bill in bills:
            for li in bill.line_items:
                # Check if preventive care was charged
                if li.cpt_code in self.PREVENTIVE_CPT_CODES:
                    if li.patient_responsibility > Decimal("0"):
                        mismatches.append(CodingMismatch(
                            bill_id=str(bill.id),
                            line_item_id=str(li.id),
                            issue_type="preventive_with_cost_share",
                            expected_code=li.cpt_code,
                            actual_code=li.cpt_code,
                            expected_coverage="100% covered (preventive)",
                            actual_coverage=f"Patient charged ${li.patient_responsibility}",
                            potential_savings=li.patient_responsibility,
                            confidence=0.85
                        ))
                
                # Check for diagnosis code that might cause preventive to be billed as diagnostic
                if li.cpt_code in self.PREVENTIVE_CPT_CODES:
                    # If ICD-10 is not Z-code (preventive), might be miscoded
                    non_preventive_dx = [
                        code for code in li.icd10_codes 
                        if not code.startswith("Z")
                    ]
                    if non_preventive_dx and li.patient_responsibility > 0:
                        mismatches.append(CodingMismatch(
                            bill_id=str(bill.id),
                            line_item_id=str(li.id),
                            issue_type="diagnosis_causing_cost_share",
                            expected_code="Z-code (preventive)",
                            actual_code=non_preventive_dx[0],
                            expected_coverage="100% covered with Z-code",
                            actual_coverage="Diagnostic coding applied",
                            potential_savings=li.patient_responsibility,
                            confidence=0.70
                        ))
        
        return mismatches
    
    def _match_procedures(self, ins: 'InsurancePlan',
                          procedures: list[dict]) -> list['CoverageMatch']:
        """Match upcoming procedures to coverage"""
        matches = []
        
        for proc in procedures:
            name = proc.get("name", "Procedure")
            cpt_codes = proc.get("cpt_codes", [])
            estimated_cost = Decimal(str(proc.get("estimated_cost", 0)))
            
            # Determine if covered
            is_covered = True
            coverage_notes = []
            
            for exclusion in ins.excluded_services:
                if exclusion.lower() in name.lower():
                    is_covered = False
                    coverage_notes.append(f"Service appears in exclusion list: {exclusion}")
            
            # Check preauth
            requires_preauth = False
            for limit in ins.coverage_limits:
                if any(code in limit.service_type for code in cpt_codes):
                    if limit.requires_preauth:
                        requires_preauth = True
                        coverage_notes.append(f"Prior authorization required")
            
            # Estimate patient cost
            if is_covered:
                # Apply deductible first
                ded_remaining = ins.deductible_remaining
                applied_to_ded = min(ded_remaining, estimated_cost)
                after_ded = estimated_cost - applied_to_ded
                
                # Apply coinsurance
                coinsurance = after_ded * Decimal(str(ins.coinsurance_in_network))
                
                # Cap at OOP remaining
                patient_cost = min(applied_to_ded + coinsurance, ins.oop_remaining)
            else:
                patient_cost = estimated_cost
            
            matches.append(CoverageMatch(
                procedure_name=name,
                cpt_codes=cpt_codes,
                is_covered=is_covered,
                requires_preauth=requires_preauth,
                preauth_status=None,
                estimated_allowed_amount=estimated_cost,
                estimated_patient_cost=patient_cost,
                network_requirement="in_network_required",
                coverage_notes=coverage_notes
            ))
        
        return matches
    
    def _generate_coverage_warnings(self, ins: 'InsurancePlan',
                                     ded: 'DeductibleStatus',
                                     oop: 'OOPStatus',
                                     bills: list['ParsedBill']) -> list[str]:
        """Generate coverage-related warnings"""
        warnings = []
        
        # Deductible warnings
        if ded.percentage_met < 0.1 and bills:
            warnings.append("Deductible barely started - most costs will be out of pocket")
        
        # Year-end warning
        if ins.days_until_plan_year_end < 30:
            warnings.append(f"Plan year ends in {ins.days_until_plan_year_end} days - deductible will reset")
        
        # High deductible warning
        if ins.individual_coverage.deductible > Decimal("5000"):
            warnings.append("High-deductible plan - significant out-of-pocket before coverage")
        
        # Claims not submitted
        unsubmitted = [b for b in bills if b.claim_status == ClaimStatus.PENDING and b.insurance_processed == False]
        if unsubmitted:
            warnings.append(f"{len(unsubmitted)} bill(s) may not have been submitted to insurance")
        
        return warnings
    
    def _generate_network_warnings(self, ins: 'InsurancePlan',
                                    bills: list['ParsedBill']) -> list[str]:
        """Generate network-related warnings"""
        warnings = []
        
        oon_bills = [b for b in bills if b.network_status == NetworkStatus.OUT_OF_NETWORK]
        if oon_bills:
            warnings.append(f"{len(oon_bills)} bill(s) are out-of-network - higher costs apply")
        
        unknown_network = [b for b in bills if b.network_status == NetworkStatus.UNKNOWN]
        if unknown_network:
            warnings.append(f"{len(unknown_network)} bill(s) have unknown network status - verify with insurer")
        
        if not ins.has_out_of_network_coverage:
            warnings.append("Plan has no out-of-network coverage - avoid non-network providers")
        
        return warnings
    
    def _analyze_coordination(self, primary: 'InsurancePlan',
                               secondary: 'InsurancePlan',
                               bills: list['ParsedBill']) -> tuple[str, Decimal]:
        """Analyze coordination of benefits"""
        status = "Coordination of benefits applicable"
        potential_savings = Decimal("0")
        
        # Estimate savings from secondary picking up primary's cost share
        for bill in bills:
            if bill.patient_balance > 0:
                # Secondary might cover copays/coinsurance
                potential_savings += bill.patient_balance * Decimal("0.5")
        
        if secondary.insurance_type == InsuranceType.MEDICAID:
            status = "Medicaid as secondary - may cover remaining costs"
            potential_savings = sum(b.patient_balance for b in bills)
        
        return status, potential_savings
    
    def _calculate_plan_adequacy(self, ins: 'InsurancePlan',
                                  gaps: list['CoverageGap'],
                                  mismatches: list['CodingMismatch']) -> float:
        """Calculate overall plan adequacy score"""
        score = 1.0
        
        # Penalize for gaps
        severe_gaps = sum(1 for g in gaps if g.severity in [RiskTier.HIGH, RiskTier.SEVERE])
        score -= severe_gaps * 0.15
        
        # Penalize for coding issues
        score -= len(mismatches) * 0.05
        
        # Penalize for high deductible
        if ins.individual_coverage.deductible > Decimal("5000"):
            score -= 0.15
        elif ins.individual_coverage.deductible > Decimal("2500"):
            score -= 0.10
        
        # Penalize for exclusions
        score -= len(ins.excluded_services) * 0.02
        
        return max(0.1, min(1.0, score))
    
    def _estimate_uncovered_exposure(self, ins: 'InsurancePlan',
                                      bills: list['ParsedBill'],
                                      gaps: list['CoverageGap']) -> Decimal:
        """Estimate total uncovered financial exposure"""
        exposure = Decimal("0")
        
        # Add gap exposures
        exposure += sum(g.financial_exposure for g in gaps)
        
        # Add denied/uncovered items from bills
        for bill in bills:
            for li in bill.line_items:
                if not li.is_covered:
                    exposure += li.patient_responsibility
        
        return exposure