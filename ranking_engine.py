"""
MedFin Ranking Engine
Intelligent multi-factor recommendation ranking
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RankingEngine:
    """
    Multi-factor ranking engine for recommendations.
    
    Uses weighted scoring across 5 dimensions:
    - Urgency (25%): How time-sensitive is this action?
    - Savings Impact (25%): How much money could this save?
    - Success Probability (20%): How likely is this to work?
    - Risk Reduction (15%): How much does this reduce financial risk?
    - Ease of Execution (15%): How easy is this to accomplish?
    """
    
    DEFAULT_WEIGHTS = {
        'urgency': 0.25,
        'savings': 0.25,
        'success': 0.20,
        'risk_reduction': 0.15,
        'ease': 0.15
    }
    
    # Savings thresholds for scoring
    SAVINGS_THRESHOLDS = [
        (Decimal("10000"), 100),
        (Decimal("5000"), 90),
        (Decimal("2000"), 75),
        (Decimal("1000"), 60),
        (Decimal("500"), 45),
        (Decimal("200"), 30),
        (Decimal("100"), 20),
        (Decimal("0"), 10),
    ]
    
    # Difficulty to ease score mapping
    EASE_SCORES = {
        DifficultyLevel.TRIVIAL: 100,
        DifficultyLevel.EASY: 80,
        DifficultyLevel.MODERATE: 60,
        DifficultyLevel.CHALLENGING: 40,
        DifficultyLevel.COMPLEX: 20,
    }
    
    def __init__(self, weights: Optional[dict] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
    
    def rank_recommendations(self,
                              recommendations: list[Recommendation],
                              risk_assessment: RiskAssessment) -> list[RankedRecommendation]:
        """
        Rank recommendations using multi-factor scoring.
        
        Returns recommendations sorted by priority score (descending).
        """
        ranked = []
        
        for rec in recommendations:
            factors = self._calculate_ranking_factors(rec, risk_assessment)
            
            ranked.append(RankedRecommendation(
                recommendation=rec,
                ranking_factors=factors,
                final_rank=0,  # Will be set after sorting
                rationale=self._generate_ranking_rationale(rec, factors)
            ))
        
        # Sort by composite score (descending)
        ranked.sort(key=lambda x: x.ranking_factors.composite_score, reverse=True)
        
        # Assign final ranks
        for i, r in enumerate(ranked, 1):
            r.final_rank = i
            r.recommendation.rank = i
            r.recommendation.priority_score = r.ranking_factors.composite_score
        
        return ranked
    
    def _calculate_ranking_factors(self,
                                    rec: Recommendation,
                                    risk: RiskAssessment) -> RankingFactors:
        """Calculate all ranking factors for a recommendation."""
        
        # 1. Urgency Score (0-100)
        urgency = self._calculate_urgency_score(rec)
        
        # 2. Savings Impact Score (0-100)
        savings = self._calculate_savings_score(rec)
        
        # 3. Success Probability Score (0-100)
        success = rec.success_probability * 100
        
        # 4. Risk Reduction Score (0-100)
        risk_reduction = self._calculate_risk_reduction_score(rec, risk)
        
        # 5. Ease of Execution Score (0-100)
        ease = self.EASE_SCORES.get(rec.difficulty, 50)
        
        return RankingFactors(
            urgency_score=urgency,
            savings_impact_score=savings,
            success_score=success,
            risk_reduction_score=risk_reduction,
            ease_score=ease,
            urgency_weight=self.weights['urgency'],
            savings_weight=self.weights['savings'],
            success_weight=self.weights['success'],
            risk_weight=self.weights['risk_reduction'],
            ease_weight=self.weights['ease']
        )
    
    def _calculate_urgency_score(self, rec: Recommendation) -> float:
        """
        Calculate urgency score based on deadlines and priority.
        
        Urgency Scoring:
        - Overdue: 100
        - Due today: 95
        - Due in 1-3 days: 85
        - Due in 4-7 days: 70
        - Due in 8-14 days: 55
        - Due in 15-30 days: 40
        - Due in 30+ days or no deadline: 25
        
        Also factors in action priority level.
        """
        base_score = 25  # Default for no deadline
        
        if rec.deadline:
            days_until = (rec.deadline - date.today()).days
            
            if days_until < 0:
                base_score = 100  # Overdue
            elif days_until == 0:
                base_score = 95
            elif days_until <= 3:
                base_score = 85
            elif days_until <= 7:
                base_score = 70
            elif days_until <= 14:
                base_score = 55
            elif days_until <= 30:
                base_score = 40
            else:
                base_score = 25
        
        # Adjust based on action priority
        priority_adjustments = {
            ActionPriority.CRITICAL: 20,
            ActionPriority.HIGH: 10,
            ActionPriority.MEDIUM: 0,
            ActionPriority.LOW: -10,
            ActionPriority.INFORMATIONAL: -20
        }
        
        adjustment = priority_adjustments.get(rec.priority, 0)
        
        return max(0, min(100, base_score + adjustment))
    
    def _calculate_savings_score(self, rec: Recommendation) -> float:
        """
        Calculate savings impact score.
        
        Uses expected savings with confidence adjustment.
        """
        expected = rec.savings_estimate.expected
        confidence = rec.savings_estimate.confidence
        
        # Find base score from thresholds
        base_score = 10
        for threshold, score in self.SAVINGS_THRESHOLDS:
            if expected >= threshold:
                base_score = score
                break
        
        # Adjust for confidence (low confidence = lower effective score)
        confidence_factor = 0.7 + (confidence * 0.3)  # Range: 0.7 to 1.0
        
        return base_score * confidence_factor
    
    def _calculate_risk_reduction_score(self,
                                         rec: Recommendation,
                                         risk: RiskAssessment) -> float:
        """
        Calculate how much this recommendation reduces risk.
        
        Higher-risk situations get more benefit from risk-reducing actions.
        """
        # Base score from recommendation's stated risk reduction
        base_score = rec.risk_reduction_score
        
        # Action categories that typically reduce risk more
        high_risk_reduction_categories = {
            ActionCategory.ASSISTANCE_APPLICATION: 30,
            ActionCategory.BILL_DISPUTE: 20,
            ActionCategory.INSURANCE_APPEAL: 20,
            ActionCategory.NEGOTIATION: 15,
            ActionCategory.PAYMENT_OPTIMIZATION: 10,
        }
        
        category_boost = high_risk_reduction_categories.get(rec.category, 5)
        
        # Scale by current risk level (higher risk = more value from reduction)
        risk_multiplier = 1.0 + (risk.overall_score / 200)  # 1.0 to 1.5
        
        total_score = (base_score + category_boost) * risk_multiplier
        
        return min(100, total_score)
    
    def _generate_ranking_rationale(self, 
                                     rec: Recommendation,
                                     factors: RankingFactors) -> str:
        """Generate explanation for why recommendation is ranked where it is."""
        
        # Find the dominant factor
        factor_scores = [
            ('urgency', factors.urgency_score),
            ('potential savings', factors.savings_impact_score),
            ('success likelihood', factors.success_score),
            ('risk reduction', factors.risk_reduction_score),
            ('ease of completion', factors.ease_score)
        ]
        
        dominant = max(factor_scores, key=lambda x: x[1])
        
        rationale_parts = []
        
        if factors.urgency_score >= 80:
            rationale_parts.append("time-critical")
        
        if factors.savings_impact_score >= 70:
            rationale_parts.append(f"significant savings potential (${rec.savings_estimate.expected:,.0f})")
        
        if factors.success_score >= 70:
            rationale_parts.append("high success probability")
        
        if factors.ease_score >= 70:
            rationale_parts.append("easy to complete")
        
        if not rationale_parts:
            return f"Ranked primarily by {dominant[0]} score ({dominant[1]:.0f}/100)"
        
        return f"Priority factors: {', '.join(rationale_parts)}"