from typing import Dict, Any, Optional, List
from app.core.models import ServiceType, InsuranceType, CostEstimationRequest, CostEstimationResponse
from app.core.config import settings
import random


class CostEstimator:
    """Estimates healthcare costs based on service type and insurance coverage"""
    
    # Base cost ranges by service type (in USD)
    BASE_COSTS = {
        ServiceType.PRIMARY_CARE: (150, 300),
        ServiceType.SPECIALIST: (200, 500),
        ServiceType.EMERGENCY: (500, 3000),
        ServiceType.SURGERY: (5000, 50000),
        ServiceType.IMAGING: (300, 2000),
        ServiceType.LABORATORY: (100, 500),
        ServiceType.PHARMACY: (20, 500),
        ServiceType.HOSPITALIZATION: (2000, 10000),
        ServiceType.MENTAL_HEALTH: (100, 300),
        ServiceType.PREVENTIVE: (0, 200),
    }
    
    def estimate_cost(self, request: CostEstimationRequest) -> CostEstimationResponse:
        """Estimate cost for a healthcare service"""
        
        # Get base cost range
        min_cost, max_cost = self.BASE_COSTS.get(
            request.service_type,
            (100, 1000)
        )
        
        # Generate estimated cost (in real system, would use ML model or API)
        estimated_cost = (min_cost + max_cost) / 2
        
        # Apply location multiplier (example: higher costs in certain areas)
        location_multiplier = self._get_location_multiplier(request.location)
        estimated_cost *= location_multiplier
        
        # Calculate insurance coverage
        insurance_coverage = None
        patient_responsibility = estimated_cost
        
        if request.has_insurance and request.insurance_type:
            coverage = self._calculate_coverage(
                estimated_cost,
                request.insurance_type,
                request.deductible_remaining or 0.0,
                request.copay
            )
            
            insurance_coverage = coverage["insurance_pays"]
            patient_responsibility = coverage["patient_pays"]
        
        # Build breakdown
        breakdown = {
            "base_cost": estimated_cost,
            "service_type": request.service_type.value,
            "location_multiplier": location_multiplier,
            "insurance_applied": request.has_insurance,
        }
        
        if insurance_coverage is not None:
            breakdown.update({
                "insurance_coverage": insurance_coverage,
                "deductible_impact": request.deductible_remaining or 0.0,
            })
        
        # Find alternatives
        alternatives = self._find_alternatives(request.service_type, estimated_cost)
        
        return CostEstimationResponse(
            estimated_cost=estimated_cost,
            insurance_coverage=insurance_coverage,
            patient_responsibility=patient_responsibility,
            breakdown=breakdown,
            confidence_score=0.75,  # Would be calculated by ML model
            alternatives=alternatives
        )
    
    def _get_location_multiplier(self, location: Optional[str]) -> float:
        """Get cost multiplier based on location"""
        if not location:
            return 1.0
        
        # Simplified: real system would use geographic cost data
        high_cost_areas = ["CA", "NY", "MA", "CT"]
        if any(area in location.upper() for area in high_cost_areas):
            return 1.3
        
        low_cost_areas = ["TX", "FL", "GA", "TN"]
        if any(area in location.upper() for area in low_cost_areas):
            return 0.9
        
        return 1.0
    
    def _calculate_coverage(
        self,
        cost: float,
        insurance_type: InsuranceType,
        deductible_remaining: float,
        copay: Optional[float]
    ) -> Dict[str, float]:
        """Calculate insurance coverage"""
        
        # If copay applies (typically for primary care, specialist visits)
        if copay and copay > 0:
            return {
                "insurance_pays": cost - copay,
                "patient_pays": copay
            }
        
        # Check if deductible needs to be met first
        if deductible_remaining > 0:
            if cost <= deductible_remaining:
                return {
                    "insurance_pays": 0.0,
                    "patient_pays": cost
                }
            else:
                remaining_after_deductible = cost - deductible_remaining
                # Apply coverage percentage
                coverage_pct = self._get_coverage_percentage(insurance_type)
                insurance_pays = remaining_after_deductible * coverage_pct
                patient_pays = deductible_remaining + (remaining_after_deductible * (1 - coverage_pct))
                
                return {
                    "insurance_pays": insurance_pays,
                    "patient_pays": patient_pays
                }
        
        # Deductible met, apply coverage percentage
        coverage_pct = self._get_coverage_percentage(insurance_type)
        insurance_pays = cost * coverage_pct
        patient_pays = cost * (1 - coverage_pct)
        
        return {
            "insurance_pays": insurance_pays,
            "patient_pays": patient_pays
        }
    
    def _get_coverage_percentage(self, insurance_type: InsuranceType) -> float:
        """Get coverage percentage by insurance type"""
        coverage_map = {
            InsuranceType.PRIVATE: 0.80,
            InsuranceType.MEDICARE: 0.80,
            InsuranceType.MEDICAID: 0.95,
            InsuranceType.TRICARE: 0.85,
            InsuranceType.NONE: 0.0,
        }
        return coverage_map.get(insurance_type, 0.80)
    
    def _find_alternatives(
        self,
        service_type: ServiceType,
        estimated_cost: float
    ) -> List[Dict[str, Any]]:
        """Find lower-cost alternatives"""
        alternatives = []
        
        # Suggest telehealth for certain services
        if service_type in [ServiceType.PRIMARY_CARE, ServiceType.MENTAL_HEALTH]:
            alternatives.append({
                "option": "Telehealth visit",
                "estimated_cost": estimated_cost * 0.7,
                "savings": estimated_cost * 0.3,
                "description": "Virtual consultation with healthcare provider"
            })
        
        # Suggest urgent care instead of ER
        if service_type == ServiceType.EMERGENCY:
            alternatives.append({
                "option": "Urgent care center",
                "estimated_cost": estimated_cost * 0.3,
                "savings": estimated_cost * 0.7,
                "description": "For non-life-threatening emergencies"
            })
        
        # Suggest generic medications
        if service_type == ServiceType.PHARMACY:
            alternatives.append({
                "option": "Generic medication",
                "estimated_cost": estimated_cost * 0.2,
                "savings": estimated_cost * 0.8,
                "description": "Ask your doctor about generic alternatives"
            })
        
        return alternatives


# Singleton instance
cost_estimator = CostEstimator()

