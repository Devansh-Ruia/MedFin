"""
MedFin Smart Recommendations + Risk Scoring Engine
Main Orchestrator
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)


class SmartRecommendationEngine:
    """
    Main orchestrator for the Smart Recommendations + Risk Scoring Engine.
    
    Combines risk scoring, recommendation generation, and ranking into
    a unified output for downstream consumption.
    """
    
    def __init__(self):
        self.risk_scorer = RiskScoringEngine()
        self.recommendation_generator = RecommendationGenerator()
        self.ranking_engine = RankingEngine()
    
    def analyze(self, 
                context: 'RecommendationContext',
                custom_weights: Optional[dict] = None) -> EngineOutput:
        """
        Perform complete analysis and generate recommendations.
        
        Args:
            context: Complete context with all financial data
            custom_weights: Optional custom weights for ranking
            
        Returns:
            EngineOutput with risk assessment and ranked recommendations
        """
        start_time = time.time()
        
        try:
            # ================================================================
            # PHASE 1: RISK ASSESSMENT
            # ================================================================
            logger.info(f"Starting analysis for user {context.user_id}")
            
            risk_assessment = self.risk_scorer.calculate_risk(context)
            
            logger.info(f"Risk score: {risk_assessment.overall_score} ({risk_assessment.category.value})")
            
            # ================================================================
            # PHASE 2: RECOMMENDATION GENERATION
            # ================================================================
            recommendations = self.recommendation_generator.generate_recommendations(
                context, risk_assessment
            )
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            
            # ================================================================
            # PHASE 3: RANKING
            # ================================================================
            if custom_weights:
                self.ranking_engine.weights = custom_weights
            
            ranked_recommendations = self.ranking_engine.rank_recommendations(
                recommendations, risk_assessment
            )
            
            # ================================================================
            # PHASE 4: ORGANIZE ACTION PLAN
            # ================================================================
            action_plan = self._organize_action_plan(ranked_recommendations)
            
            # ================================================================
            # PHASE 5: CALCULATE SUMMARY METRICS
            # ================================================================
            total_savings = self._calculate_total_savings(ranked_recommendations)
            total_risk_reduction = self._calculate_total_risk_reduction(ranked_recommendations)
            
            # ================================================================
            # PHASE 6: GENERATE EXECUTIVE SUMMARY
            # ================================================================
            executive_summary = self._generate_executive_summary(
                context, risk_assessment, ranked_recommendations, total_savings
            )
            
            key_takeaways = self._generate_key_takeaways(
                risk_assessment, ranked_recommendations
            )
            
            # ================================================================
            # PHASE 7: BUILD OUTPUT
            # ================================================================
            processing_time = int((time.time() - start_time) * 1000)
            
            return EngineOutput(
                user_id=context.user_id,
                risk_assessment=risk_assessment,
                recommendations=ranked_recommendations,
                total_recommendations=len(ranked_recommendations),
                action_plan=action_plan,
                total_potential_savings=total_savings,
                total_risk_reduction_possible=total_risk_reduction,
                critical_actions_count=sum(
                    1 for r in ranked_recommendations 
                    if r.recommendation.priority == ActionPriority.CRITICAL
                ),
                executive_summary=executive_summary,
                key_takeaways=key_takeaways,
                alerts=risk_assessment.alerts,
                confidence_score=risk_assessment.confidence_score,
                data_completeness_score=risk_assessment.data_completeness,
                limitations=risk_assessment.data_quality_warnings,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.exception(f"Analysis failed for user {context.user_id}")
            raise
    
    def _organize_action_plan(self, 
                               ranked: list[RankedRecommendation]) -> ActionPlan:
        """Organize recommendations into time-based action plan."""
        
        immediate = []
        this_week = []
        this_month = []
        ongoing = []
        
        today = date.today()
        
        for r in ranked:
            rec = r.recommendation
            
            if rec.priority == ActionPriority.CRITICAL:
                immediate.append(rec)
            elif rec.deadline:
                days = (rec.deadline - today).days
                if days <= 0:
                    immediate.append(rec)
                elif days <= 7:
                    this_week.append(rec)
                elif days <= 30:
                    this_month.append(rec)
                else:
                    ongoing.append(rec)
            elif rec.priority == ActionPriority.HIGH:
                this_week.append(rec)
            elif rec.priority == ActionPriority.MEDIUM:
                this_month.append(rec)
            else:
                ongoing.append(rec)
        
        return ActionPlan(
            immediate_actions=immediate,
            this_week_actions=this_week,
            this_month_actions=this_month,
            ongoing_actions=ongoing
        )
    
    def _calculate_total_savings(self, 
                                  ranked: list[RankedRecommendation]) -> SavingsEstimate:
        """Calculate total potential savings across all recommendations."""
        
        total_min = Decimal("0")
        total_exp = Decimal("0")
        total_max = Decimal("0")
        
        weighted_confidence = Decimal("0")
        total_weight = Decimal("0")
        
        for r in ranked:
            savings = r.recommendation.savings_estimate
            total_min += savings.minimum
            total_exp += savings.expected
            total_max += savings.maximum
            
            # Weight confidence by expected savings
            weight = savings.expected
            weighted_confidence += Decimal(str(savings.confidence)) * weight
            total_weight += weight
        
        avg_confidence = float(weighted_confidence / total_weight) if total_weight > 0 else 0.5
        
        return SavingsEstimate(
            minimum=total_min,
            expected=total_exp,
            maximum=total_max,
            confidence=avg_confidence,
            calculation_method="aggregated",
            assumptions=["Assumes all recommendations executed", "Individual estimates may overlap"]
        )
    
    def _calculate_total_risk_reduction(self, 
                                         ranked: list[RankedRecommendation]) -> int:
        """Estimate total risk reduction from all recommendations."""
        
        # Each action contributes to risk reduction, but with diminishing returns
        reduction = 0
        factor = 1.0
        
        for r in ranked:
            contribution = r.ranking_factors.risk_reduction_score * factor * 0.3
            reduction += contribution
            factor *= 0.9  # Diminishing returns
        
        return min(80, int(reduction))  # Cap at 80% risk reduction
    
    def _generate_executive_summary(self,
                                     ctx: 'RecommendationContext',
                                     risk: RiskAssessment,
                                     ranked: list[RankedRecommendation],
                                     total_savings: SavingsEstimate) -> str:
        """Generate executive summary of the analysis."""
        
        parts = []
        
        # Risk summary
        parts.append(f"Your healthcare financial risk is {risk.category.value.upper()} "
                    f"(score: {risk.overall_score}/100).")
        
        # Top issue
        if risk.top_risk_factors:
            top_factor = risk.top_risk_factors[0]
            parts.append(f"Primary concern: {top_factor.name.lower()}.")
        
        # Recommendations summary
        parts.append(f"We identified {len(ranked)} actions you can take.")
        
        # Savings potential
        if total_savings.expected > Decimal("100"):
            parts.append(f"Total potential savings: ${total_savings.expected:,.0f} "
                        f"(range: ${total_savings.minimum:,.0f} - ${total_savings.maximum:,.0f}).")
        
        # Critical actions
        critical_count = sum(1 for r in ranked if r.recommendation.priority == ActionPriority.CRITICAL)
        if critical_count > 0:
            parts.append(f"{critical_count} action(s) require immediate attention.")
        
        return " ".join(parts)
    
    def _generate_key_takeaways(self,
                                 risk: RiskAssessment,
                                 ranked: list[RankedRecommendation]) -> list[str]:
        """Generate key takeaways from the analysis."""
        
        takeaways = []
        
        # Risk-based takeaway
        if risk.category in [RiskCategory.CRITICAL, RiskCategory.HIGH]:
            takeaways.append("Your situation requires immediate action to prevent financial hardship")
        elif risk.category == RiskCategory.MODERATE:
            takeaways.append("Taking proactive steps now can prevent future financial stress")
        else:
            takeaways.append("Your finances are manageable, but opportunities exist to save money")
        
        # Top recommendations
        if ranked:
            top = ranked[0].recommendation
            takeaways.append(f"Highest priority: {top.title} (${top.savings_estimate.expected:,.0f} potential savings)")
        
        # Quick wins
        quick_wins = [r for r in ranked 
                      if r.recommendation.difficulty in [DifficultyLevel.TRIVIAL, DifficultyLevel.EASY]
                      and r.recommendation.savings_estimate.expected > Decimal("100")]
        if quick_wins:
            total_quick = sum(r.recommendation.savings_estimate.expected for r in quick_wins)
            takeaways.append(f"{len(quick_wins)} easy actions could save ${total_quick:,.0f}")
        
        # Critical factors
        if risk.critical_factors:
            takeaways.append(f"Address {len(risk.critical_factors)} critical issue(s) immediately")
        
        return takeaways[:5]  # Limit to 5 takeaways


# ============================================================================
# INTEGRATION WITH EXISTING SYSTEM
# ============================================================================

class MedFinRecommendationAdapter:
    """
    Adapter to integrate the Smart Recommendation Engine with
    the existing MedFin analysis system.
    """
    
    def __init__(self):
        self.engine = SmartRecommendationEngine()
    
    def from_unified_analysis(self, 
                               unified_output: 'UnifiedAnalysisOutput') -> EngineOutput:
        """
        Create engine output from existing UnifiedAnalysisOutput.
        
        This allows the recommendation engine to consume results
        from the existing analysis orchestrator.
        """
        
        # Build context from unified output
        context = RecommendationContext(
            user_id=unified_output.user_id,
            income_analysis=unified_output.income_analysis,
            debt_analysis=unified_output.debt_analysis,
            insurance_analysis=unified_output.insurance_analysis,
            bill_analysis=unified_output.bill_analysis,
            fpl_percentage=unified_output.fpl_percentage,
        )
        
        return self.engine.analyze(context)
    
    def from_user_profile(self, 
                          profile: 'UserFinancialProfile') -> EngineOutput:
        """
        Create engine output directly from UserFinancialProfile.
        
        This runs the recommendation engine on raw profile data.
        """
        
        context = RecommendationContext(
            user_id=profile.user_id,
            income_data=profile.income,
            debt_data=profile.debt,
            insurance_data=profile.insurance,
            bills=profile.bills,
            fpl_percentage=None,  # Will be calculated
            state=profile.income.state if profile.income else None,
            upcoming_procedures=profile.expected_procedures,
        )
        
        # Calculate FPL if income data available
        if profile.income:
            from income_analyzer import IncomeAnalyzer
            analyzer = IncomeAnalyzer()
            fpl_calc = analyzer._calculate_fpl(profile.income)
            context.fpl_percentage = fpl_calc.fpl_percentage
        
        return self.engine.analyze(context)