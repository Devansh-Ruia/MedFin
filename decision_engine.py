"""
MedFin Financial Navigation System - Decision Engine & Plan Generator
Rule-based decision making and action plan generation
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional, Callable
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# RULE ENGINE
# ============================================================================

@dataclass
class Rule:
    """Single decision rule"""
    id: str
    name: str
    description: str
    condition: Callable[..., bool]
    action_type: 'ActionType'
    priority_base: 'Priority'
    savings_calculator: Callable[..., 'SavingsEstimate']
    effort_minutes: int
    required_documents: list[str] = field(default_factory=list)
    deadline_calculator: Optional[Callable[..., date]] = None
    warnings_generator: Optional[Callable[..., list[str]]] = None

class RuleEngine:
    """Evaluates rules against patient data to generate actions"""
    
    def __init__(self):
        self.rules: list[Rule] = []
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register all built-in rules"""
        
        # Rule 1: Dispute duplicate charges
        self.rules.append(Rule(
            id="R001",
            name="Dispute Duplicate Charges",
            description="Challenge duplicate charges found on bills",
            condition=lambda ctx: len(ctx.get("duplicates", [])) > 0,
            action_type=ActionType.DISPUTE_BILL,
            priority_base=Priority.HIGH,
            savings_calculator=lambda ctx: SavingsEstimate(
                minimum=ctx["duplicate_amount"] * Decimal("0.8"),
                expected=ctx["duplicate_amount"] * Decimal("0.95"),
                maximum=ctx["duplicate_amount"],
                confidence=0.9
            ),
            effort_minutes=30,
            required_documents=["itemized_bill", "eob"],
            deadline_calculator=lambda ctx: ctx["bill"].due_date if ctx["bill"].due_date else date.today() + timedelta(days=30),
            warnings_generator=lambda ctx: ["Dispute before payment to preserve rights"] if ctx["bill"].status == BillStatus.PENDING else []
        ))
        
        # Rule 2: Request itemized bill
        self.rules.append(Rule(
            id="R002",
            name="Request Itemized Bill",
            description="Get detailed breakdown before paying large bills",
            condition=lambda ctx: (
                ctx["bill"].patient_balance > Decimal("500") and
                len(ctx["bill"].line_items) < 5  # Likely summary bill
            ),
            action_type=ActionType.REQUEST_ITEMIZATION,
            priority_base=Priority.HIGH,
            savings_calculator=lambda ctx: SavingsEstimate(
                minimum=Decimal("0"),
                expected=ctx["bill"].patient_balance * Decimal("0.15"),
                maximum=ctx["bill"].patient_balance * Decimal("0.35"),
                confidence=0.7
            ),
            effort_minutes=15,
            required_documents=[]
        ))
        
        # Rule 3: Apply for charity care
        self.rules.append(Rule(
            id="R003",
            name="Apply for Hospital Charity Care",
            description="Apply for financial assistance from hospital",
            condition=lambda ctx: (
                ctx["profile"].federal_poverty_level_percentage < 400 and
                ctx["bill"].provider_type in ["hospital", "health_system"] and
                ctx["bill"].patient_balance > Decimal("1000")
            ),
            action_type=ActionType.REQUEST_CHARITY_CARE,
            priority_base=Priority.HIGH,
            savings_calculator=lambda ctx: self._charity_care_savings(ctx),
            effort_minutes=60,
            required_documents=[
                "proof_of_income", "tax_return", "bank_statements",
                "id_document", "bills"
            ],
            warnings_generator=lambda ctx: [
                "Apply before making any payments",
                "Some programs have retroactive limits"
            ]
        ))
        
        # Rule 4: Negotiate bill reduction
        self.rules.append(Rule(
            id="R004", 
            name="Negotiate Bill Reduction",
            description="Request discount for prompt or lump sum payment",
            condition=lambda ctx: ctx["bill"].patient_balance > Decimal("300"),
            action_type=ActionType.NEGOTIATE_BILL,
            priority_base=Priority.MEDIUM,
            savings_calculator=lambda ctx: SavingsEstimate(
                minimum=ctx["bill"].patient_balance * Decimal("0.10"),
                expected=ctx["bill"].patient_balance * Decimal("0.25"),
                maximum=ctx["bill"].patient_balance * Decimal("0.40"),
                confidence=0.6
            ),
            effort_minutes=20,
            required_documents=[]
        ))
        
        # Rule 5: File insurance appeal
        self.rules.append(Rule(
            id="R005",
            name="File Insurance Appeal",
            description="Appeal denied or underpaid claim",
            condition=lambda ctx: (
                ctx.get("appeal_opportunity") and
                ctx["appeal_opportunity"]["estimated_recovery"] > Decimal("200")
            ),
            action_type=ActionType.FILE_INSURANCE_APPEAL,
            priority_base=Priority.HIGH,
            savings_calculator=lambda ctx: SavingsEstimate(
                minimum=Decimal("0"),
                expected=ctx["appeal_opportunity"]["estimated_recovery"],
                maximum=ctx["appeal_opportunity"]["estimated_recovery"] * Decimal("1.5"),
                confidence=ctx["appeal_opportunity"]["success_likelihood"]
            ),
            effort_minutes=45,
            required_documents=["eob", "medical_records", "doctor_letter"],
            deadline_calculator=lambda ctx: date.today() + timedelta(days=180)  # Typical appeal window
        ))
        
        # Rule 6: Setup payment plan
        self.rules.append(Rule(
            id="R006",
            name="Setup Interest-Free Payment Plan",
            description="Establish manageable monthly payments",
            condition=lambda ctx: (
                ctx["bill"].patient_balance > ctx["profile"].available_monthly_budget * 2
            ),
            action_type=ActionType.SETUP_PAYMENT_PLAN,
            priority_base=Priority.MEDIUM,
            savings_calculator=lambda ctx: SavingsEstimate(
                minimum=Decimal("0"),
                expected=Decimal("0"),  # Payment plans don't reduce total
                maximum=Decimal("0"),
                confidence=0.95
            ),
            effort_minutes=20,
            required_documents=[],
            warnings_generator=lambda ctx: self._payment_plan_warnings(ctx)
        ))
        
        # Rule 7: Apply for assistance programs
        self.rules.append(Rule(
            id="R007",
            name="Apply for Assistance Program",
            description="Submit application to matched assistance program",
            condition=lambda ctx: (
                ctx.get("eligibility_match") and 
                ctx["eligibility_match"].match_score > 0.5
            ),
            action_type=ActionType.APPLY_ASSISTANCE,
            priority_base=Priority.HIGH,
            savings_calculator=lambda ctx: SavingsEstimate(
                minimum=ctx["eligibility_match"].estimated_savings * Decimal("0.5"),
                expected=ctx["eligibility_match"].estimated_savings,
                maximum=ctx["eligibility_match"].estimated_savings * Decimal("1.2"),
                confidence=ctx["eligibility_match"].approval_likelihood
            ),
            effort_minutes=lambda ctx: {"low": 30, "medium": 60, "high": 120}[
                ctx["eligibility_match"].application_effort
            ],
            required_documents=lambda ctx: ctx["eligibility_match"].required_documents
        ))
        
        # Rule 8: Dispute billing errors
        self.rules.append(Rule(
            id="R008",
            name="Dispute Billing Errors",
            description="Challenge identified billing errors",
            condition=lambda ctx: len(ctx.get("errors", [])) > 0,
            action_type=ActionType.DISPUTE_BILL,
            priority_base=Priority.HIGH,
            savings_calculator=lambda ctx: SavingsEstimate(
                minimum=ctx["error_amount"] * Decimal("0.6"),
                expected=ctx["error_amount"] * Decimal("0.85"),
                maximum=ctx["error_amount"],
                confidence=0.75
            ),
            effort_minutes=45,
            required_documents=["itemized_bill", "eob", "medical_records"]
        ))
        
        # Rule 9: Check balance billing violations
        self.rules.append(Rule(
            id="R009",
            name="Challenge Balance Billing",
            description="Dispute potentially illegal balance billing",
            condition=lambda ctx: ctx.get("balance_billing_violation", False),
            action_type=ActionType.DISPUTE_BILL,
            priority_base=Priority.CRITICAL,
            savings_calculator=lambda ctx: SavingsEstimate(
                minimum=ctx["balance_billing_amount"] * Decimal("0.7"),
                expected=ctx["balance_billing_amount"],
                maximum=ctx["balance_billing_amount"],
                confidence=0.8
            ),
            effort_minutes=30,
            required_documents=["eob", "itemized_bill"],
            warnings_generator=lambda ctx: [
                "Balance billing is prohibited in many states for emergency services",
                "Contact state insurance commissioner if provider refuses"
            ]
        ))
        
        # Rule 10: Verify insurance claim submission
        self.rules.append(Rule(
            id="R010",
            name="Verify Insurance Claim",
            description="Ensure bill was properly submitted to insurance",
            condition=lambda ctx: (
                ctx["bill"].insurance_paid == 0 and
                ctx.get("has_insurance", False) and
                ctx["bill"].total_billed > Decimal("200")
            ),
            action_type=ActionType.VERIFY_INSURANCE_CLAIM,
            priority_base=Priority.HIGH,
            savings_calculator=lambda ctx: SavingsEstimate(
                minimum=Decimal("0"),
                expected=ctx["bill"].patient_balance * Decimal("0.6"),
                maximum=ctx["bill"].patient_balance * Decimal("0.9"),
                confidence=0.5
            ),
            effort_minutes=20,
            required_documents=["insurance_card"]
        ))
    
    def _charity_care_savings(self, ctx) -> 'SavingsEstimate':
        """Calculate charity care savings based on FPL"""
        fpl = ctx["profile"].federal_poverty_level_percentage
        balance = ctx["bill"].patient_balance
        
        if fpl < 200:
            discount = Decimal("1.0")  # 100% discount likely
        elif fpl < 300:
            discount = Decimal("0.75")
        elif fpl < 400:
            discount = Decimal("0.50")
        else:
            discount = Decimal("0.25")
        
        return SavingsEstimate(
            minimum=balance * discount * Decimal("0.5"),
            expected=balance * discount,
            maximum=balance,
            confidence=0.7 if fpl < 300 else 0.5
        )
    
    def _payment_plan_warnings(self, ctx) -> list[str]:
        """Generate payment plan warnings"""
        warnings = []
        
        if ctx["bill"].patient_balance > ctx["profile"].total_monthly_net:
            warnings.append("Payment plan term may exceed 12 months")
        
        return warnings
    
    def evaluate(self, context: dict) -> list[dict]:
        """Evaluate all rules against context, return triggered actions"""
        triggered = []
        
        for rule in self.rules:
            try:
                if rule.condition(context):
                    # Calculate dynamic values
                    effort = rule.effort_minutes
                    if callable(effort):
                        effort = effort(context)
                    
                    docs = rule.required_documents
                    if callable(docs):
                        docs = docs(context)
                    
                    deadline = None
                    if rule.deadline_calculator:
                        deadline = rule.deadline_calculator(context)
                    
                    warnings = []
                    if rule.warnings_generator:
                        warnings = rule.warnings_generator(context)
                    
                    triggered.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "description": rule.description,
                        "action_type": rule.action_type,
                        "priority": rule.priority_base,
                        "savings": rule.savings_calculator(context),
                        "effort_minutes": effort,
                        "required_documents": docs,
                        "deadline": deadline,
                        "warnings": warnings
                    })
            except Exception as e:
                logger.warning(f"Rule {rule.id} evaluation failed: {e}")
                continue
        
        return triggered


# ============================================================================
# PRIORITY MATRIX
# ============================================================================

class PriorityMatrix:
    """Calculates final priority scores for actions"""
    
    # Weight factors for priority calculation
    WEIGHTS = {
        "savings_impact": 0.30,
        "time_sensitivity": 0.25,
        "approval_likelihood": 0.20,
        "effort_efficiency": 0.15,
        "risk_mitigation": 0.10
    }
    
    def calculate_priority_score(self, action: dict, 
                                  risk_score: int,
                                  days_until_deadline: Optional[int]) -> float:
        """Calculate composite priority score 0-100"""
        scores = {}
        
        # Savings impact (normalized)
        savings = action["savings"]
        expected_savings = float(savings.expected)
        if expected_savings > 5000:
            scores["savings_impact"] = 100
        elif expected_savings > 2000:
            scores["savings_impact"] = 80
        elif expected_savings > 500:
            scores["savings_impact"] = 60
        elif expected_savings > 100:
            scores["savings_impact"] = 40
        else:
            scores["savings_impact"] = 20
        
        # Time sensitivity
        if days_until_deadline is not None:
            if days_until_deadline < 0:
                scores["time_sensitivity"] = 100
            elif days_until_deadline < 7:
                scores["time_sensitivity"] = 90
            elif days_until_deadline < 14:
                scores["time_sensitivity"] = 75
            elif days_until_deadline < 30:
                scores["time_sensitivity"] = 60
            else:
                scores["time_sensitivity"] = 40
        else:
            scores["time_sensitivity"] = 50  # Default
        
        # Approval likelihood
        scores["approval_likelihood"] = savings.confidence * 100
        
        # Effort efficiency (savings per minute of effort)
        effort = action["effort_minutes"]
        if effort > 0:
            efficiency = expected_savings / effort
            if efficiency > 100:
                scores["effort_efficiency"] = 100
            elif efficiency > 50:
                scores["effort_efficiency"] = 80
            elif efficiency > 20:
                scores["effort_efficiency"] = 60
            else:
                scores["effort_efficiency"] = 40
        else:
            scores["effort_efficiency"] = 100
        
        # Risk mitigation (higher risk = more important to act)
        scores["risk_mitigation"] = min(100, risk_score * 1.2)
        
        # Calculate weighted score
        total = sum(
            scores[factor] * weight 
            for factor, weight in self.WEIGHTS.items()
        )
        
        # Apply base priority multiplier
        priority_multipliers = {
            Priority.CRITICAL: 1.5,
            Priority.HIGH: 1.2,
            Priority.MEDIUM: 1.0,
            Priority.LOW: 0.8,
            Priority.INFORMATIONAL: 0.5
        }
        multiplier = priority_multipliers.get(action["priority"], 1.0)
        
        return min(100, total * multiplier)
    
    def rank_actions(self, actions: list[dict], 
                     risk_score: int) -> list[dict]:
        """Rank actions by priority score"""
        for action in actions:
            days = None
            if action.get("deadline"):
                days = (action["deadline"] - date.today()).days
            
            action["priority_score"] = self.calculate_priority_score(
                action, risk_score, days
            )
        
        # Sort by priority score descending
        return sorted(actions, key=lambda x: x["priority_score"], reverse=True)


# ============================================================================
# PLAN GENERATOR
# ============================================================================

class PlanGenerator:
    """Generates complete navigation plans from analysis results"""
    
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.priority_matrix = PriorityMatrix()
    
    def generate(self,
                 bills: list['MedicalBill'],
                 insurance: Optional['InsurancePlan'],
                 profile: 'PatientFinancialProfile',
                 bill_analyses: list['BillAnalysisResult'],
                 insurance_analysis: Optional['InsuranceAnalysisResult'],
                 eligibility_matches: list['EligibilityMatch'],
                 risk_assessment: 'RiskAssessment') -> 'NavigationPlan':
        """Generate complete navigation plan"""
        
        all_actions = []
        
        # Process each bill
        for bill, analysis in zip(bills, bill_analyses):
            context = self._build_bill_context(
                bill, analysis, insurance, profile, eligibility_matches
            )
            actions = self.rule_engine.evaluate(context)
            
            # Tag actions with bill reference
            for action in actions:
                action["target_bill_id"] = bill.id
                action["target_provider"] = bill.provider_name
            
            all_actions.extend(actions)
        
        # Add insurance-level actions
        if insurance_analysis:
            ins_actions = self._generate_insurance_actions(
                insurance, insurance_analysis, profile
            )
            all_actions.extend(ins_actions)
        
        # Add assistance program actions
        for match in eligibility_matches:
            if match.match_score > 0.5:
                context = {"eligibility_match": match, "profile": profile}
                actions = self.rule_engine.evaluate(context)
                for action in actions:
                    action["target_program_id"] = match.program_id
                all_actions.extend(actions)
        
        # Deduplicate similar actions
        all_actions = self._deduplicate_actions(all_actions)
        
        # Rank by priority
        ranked_actions = self.priority_matrix.rank_actions(
            all_actions, risk_assessment.risk_score
        )
        
        # Convert to ActionStep objects
        action_steps = self._create_action_steps(ranked_actions)
        
        # Calculate totals
        total_owed = sum(b.patient_balance for b in bills)
        total_savings = self._calculate_total_savings(action_steps)
        
        # Build budget impact
        budget_impact = self._calculate_budget_impact(
            profile, total_owed, total_savings
        )
        
        # Generate timeline and deadlines
        key_deadlines = self._extract_key_deadlines(action_steps)
        plan_duration = self._calculate_plan_duration(action_steps)
        
        # Generate explanations
        summary = self._generate_executive_summary(
            bills, action_steps, total_savings, risk_assessment
        )
        
        return NavigationPlan(
            patient_id=profile.patient_id,
            valid_until=date.today() + timedelta(days=30),
            total_bills_analyzed=len(bills),
            total_amount_owed=total_owed,
            potential_total_savings=total_savings,
            action_steps=action_steps,
            critical_actions_count=sum(
                1 for a in action_steps if a.priority == Priority.CRITICAL
            ),
            risk_assessment=risk_assessment,
            budget_impact=budget_impact,
            plan_duration_days=plan_duration,
            key_deadlines=key_deadlines,
            executive_summary=summary,
            methodology_notes=[
                "Savings estimates based on historical success rates",
                "Priority calculated using multi-factor weighting",
                "Eligibility assessment uses current program criteria"
            ],
            assumptions=[
                "All provided financial information is accurate",
                "Patient has capacity to complete recommended actions",
                "Insurance benefits remain unchanged during plan period"
            ],
            confidence_score=self._calculate_plan_confidence(action_steps),
            data_completeness_score=self._assess_data_completeness(
                bills, insurance, profile
            )
        )
    
    def _build_bill_context(self, bill, analysis, insurance, profile, matches) -> dict:
        """Build context dictionary for rule evaluation"""
        context = {
            "bill": bill,
            "profile": profile,
            "duplicates": analysis.duplicate_charges,
            "duplicate_amount": sum(
                Decimal(str(d["amount"])) for d in analysis.duplicate_charges
            ),
            "errors": analysis.errors_found,
            "error_amount": analysis.overcharge_amount,
            "has_insurance": insurance is not None,
            "eligibility_matches": matches
        }
        
        # Check for balance billing
        for err in analysis.errors_found:
            if err.get("type") == BillErrorType.BALANCE_BILLING:
                context["balance_billing_violation"] = True
                context["balance_billing_amount"] = err["amount"]
        
        return context
    
    def _generate_insurance_actions(self, insurance, analysis, profile) -> list[dict]:
        """Generate insurance-specific actions"""
        actions = []
        
        # Year-end strategy
        if analysis.year_end_strategy:
            for rec in analysis.year_end_strategy.get("recommendations", []):
                actions.append({
                    "rule_id": "INS001",
                    "rule_name": "Year-End Insurance Strategy",
                    "description": rec,
                    "action_type": ActionType.VERIFY_INSURANCE_CLAIM,
                    "priority": Priority.MEDIUM,
                    "savings": SavingsEstimate(
                        minimum=Decimal("0"),
                        expected=insurance.oop_remaining * Decimal("0.3"),
                        maximum=insurance.oop_remaining,
                        confidence=0.4
                    ),
                    "effort_minutes": 15,
                    "required_documents": [],
                    "deadline": insurance.plan_year_end,
                    "warnings": []
                })
        
        # Appeal opportunities
        for appeal in analysis.appeal_opportunities:
            actions.append({
                "rule_id": "INS002",
                "rule_name": "Insurance Appeal",
                "description": f"Appeal underpaid claim",
                "action_type": ActionType.FILE_INSURANCE_APPEAL,
                "priority": Priority.HIGH,
                "savings": SavingsEstimate(
                    minimum=Decimal("0"),
                    expected=appeal["estimated_recovery"],
                    maximum=appeal["estimated_recovery"] * Decimal("1.2"),
                    confidence=appeal["success_likelihood"]
                ),
                "effort_minutes": 45,
                "required_documents": ["eob", "medical_records"],
                "deadline": date.today() + timedelta(days=180),
                "warnings": ["Appeals have strict deadlines"],
                "target_bill_id": appeal["bill_id"]
            })
        
        return actions
    
    def _deduplicate_actions(self, actions: list[dict]) -> list[dict]:
        """Remove duplicate or redundant actions"""
        seen = set()
        unique = []
        
        for action in actions:
            # Create dedup key
            key = (
                action["action_type"],
                action.get("target_bill_id"),
                action.get("target_program_id")
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(action)
        
        return unique
    
    def _create_action_steps(self, ranked_actions: list[dict]) -> list['ActionStep']:
        """Convert ranked actions to ActionStep objects"""
        steps = []
        
        for i, action in enumerate(ranked_actions, 1):
            # Generate detailed instructions
            instructions = self._generate_instructions(action)
            
            step = ActionStep(
                step_number=i,
                action_type=action["action_type"],
                priority=self._adjust_priority(action),
                title=action["rule_name"],
                description=action["description"],
                target_bill_id=action.get("target_bill_id"),
                target_provider=action.get("target_provider"),
                target_program_id=action.get("target_program_id"),
                estimated_effort_minutes=action["effort_minutes"],
                deadline=action.get("deadline"),
                recommended_start=date.today(),
                savings_estimate=action["savings"],
                approval_likelihood=action["savings"].confidence,
                detailed_steps=instructions,
                required_documents=action["required_documents"],
                warnings=action.get("warnings", [])
            )
            steps.append(step)
        
        return steps
    
    def _adjust_priority(self, action: dict) -> 'Priority':
        """Adjust priority based on score"""
        score = action.get("priority_score", 50)
        if score >= 85:
            return Priority.CRITICAL
        elif score >= 70:
            return Priority.HIGH
        elif score >= 50:
            return Priority.MEDIUM
        elif score >= 30:
            return Priority.LOW
        return Priority.INFORMATIONAL
    
    def _generate_instructions(self, action: dict) -> list[str]:
        """Generate step-by-step instructions"""
        action_type = action["action_type"]
        
        instructions = {
            ActionType.REQUEST_ITEMIZATION: [
                "Call the billing department at the number on your statement",
                "Request a detailed itemized bill with all CPT/HCPCS codes",
                "Ask for the bill to be sent in writing",
                "Review each line item for accuracy when received"
            ],
            ActionType.DISPUTE_BILL: [
                "Write a formal dispute letter citing specific errors",
                "Include copies of supporting documentation",
                "Send via certified mail with return receipt",
                "Follow up within 30 days if no response"
            ],
            ActionType.NEGOTIATE_BILL: [
                "Research fair prices for your procedures",
                "Call billing and ask for financial hardship discount",
                "Mention ability to pay lump sum for larger discount",
                "Get any agreed reduction in writing before paying"
            ],
            ActionType.REQUEST_CHARITY_CARE: [
                "Request financial assistance application from hospital",
                "Gather all required income documentation",
                "Complete application thoroughly and honestly",
                "Submit before making any payments",
                "Follow up weekly on application status"
            ],
            ActionType.FILE_INSURANCE_APPEAL: [
                "Request denial reason in writing (EOB)",
                "Obtain supporting medical records",
                "Write appeal letter citing medical necessity",
                "Include any relevant clinical guidelines",
                "Submit within appeal deadline"
            ],
            ActionType.SETUP_PAYMENT_PLAN: [
                "Calculate affordable monthly payment",
                "Call billing to request payment plan",
                "Ask about interest-free options",
                "Get terms in writing before first payment",
                "Set up automatic payments to avoid late fees"
            ]
        }
        
        return instructions.get(action_type, [
            "Contact the relevant party",
            "Explain your situation",
            "Request the specific action",
            "Document all communications"
        ])
    
    def _calculate_total_savings(self, steps: list['ActionStep']) -> 'SavingsEstimate':
        """Calculate total potential savings"""
        min_total = sum(s.savings_estimate.minimum for s in steps)
        exp_total = sum(s.savings_estimate.expected for s in steps)
        max_total = sum(s.savings_estimate.maximum for s in steps)
        
        # Weighted average confidence
        total_expected = sum(s.savings_estimate.expected for s in steps)
        if total_expected > 0:
            avg_confidence = sum(
                s.savings_estimate.expected * s.savings_estimate.confidence 
                for s in steps
            ) / total_expected
        else:
            avg_confidence = 0.5
        
        return SavingsEstimate(
            minimum=min_total,
            expected=exp_total,
            maximum=max_total,
            confidence=avg_confidence
        )
    
    def _calculate_budget_impact(self, profile, total_owed, 
                                  savings: 'SavingsEstimate') -> 'BudgetImpact':
        """Calculate impact on patient's budget"""
        monthly_income = profile.total_monthly_net
        available = profile.available_monthly_budget
        
        # Current burden (assuming 12-month payoff)
        current_monthly = total_owed / 12
        projected_monthly = (total_owed - savings.expected) / 12
        
        # Sustainable payment (max 10% of available budget)
        max_sustainable = available * Decimal("0.10")
        recommended = min(projected_monthly, max_sustainable)
        
        return BudgetImpact(
            current_medical_payment_burden=current_monthly,
            projected_after_plan=projected_monthly,
            monthly_savings=current_monthly - projected_monthly,
            percent_of_income_current=float(current_monthly / monthly_income * 100) if monthly_income > 0 else 0,
            percent_of_income_projected=float(projected_monthly / monthly_income * 100) if monthly_income > 0 else 0,
            recommended_monthly_payment=recommended,
            maximum_sustainable_payment=max_sustainable
        )
    
    def _extract_key_deadlines(self, steps: list['ActionStep']) -> list[tuple]:
        """Extract key deadlines from action steps"""
        deadlines = []
        for step in steps:
            if step.deadline:
                deadlines.append((step.deadline, step.title))
        return sorted(deadlines, key=lambda x: x[0])
    
    def _calculate_plan_duration(self, steps: list['ActionStep']) -> int:
        """Calculate total plan duration"""
        if not steps:
            return 30
        
        deadlines = [s.deadline for s in steps if s.deadline]
        if deadlines:
            latest = max(deadlines)
            return (latest - date.today()).days
        return 60  # Default
    
    def _generate_executive_summary(self, bills, steps, savings, risk) -> str:
        """Generate executive summary"""
        total_owed = sum(b.patient_balance for b in bills)
        critical = sum(1 for s in steps if s.priority == Priority.CRITICAL)
        
        summary = f"Analysis of {len(bills)} medical bill(s) totaling ${total_owed:,.2f}. "
        summary += f"Identified {len(steps)} potential actions with expected savings of ${savings.expected:,.2f}. "
        
        if critical > 0:
            summary += f"There are {critical} critical action(s) requiring immediate attention. "
        
        if risk.overall_risk_level in [RiskLevel.SEVERE, RiskLevel.HIGH]:
            summary += f"Financial risk is {risk.overall_risk_level.value} - prompt action recommended."
        
        return summary
    
    def _calculate_plan_confidence(self, steps: list['ActionStep']) -> float:
        """Calculate overall plan confidence"""
        if not steps:
            return 0.5
        return sum(s.approval_likelihood for s in steps) / len(steps)
    
    def _assess_data_completeness(self, bills, insurance, profile) -> float:
        """Assess completeness of input data"""
        score = 0.6  # Base
        
        # Check bill completeness
        for bill in bills:
            if all(li.cpt_code for li in bill.line_items):
                score += 0.1
                break
        
        # Check insurance
        if insurance:
            score += 0.15
        
        # Check profile completeness
        if profile.income_sources:
            score += 0.1
        if profile.zip_code:
            score += 0.05
        
        return min(1.0, score)