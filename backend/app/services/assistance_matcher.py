from typing import List, Dict, Any, Optional
from app.core.models import AssistanceProgram, InsuranceInfo
from app.core.config import settings


class AssistanceMatcher:
    """Matches users with financial assistance programs"""
    
    PROGRAMS = [
        {
            "program_name": "Hospital Charity Care",
            "organization": "Hospital Financial Assistance",
            "assistance_type": "financial",
            "eligibility_criteria": {
                "income_threshold": 40000,
                "household_size": None,
                "debt_threshold": None,
            },
            "estimated_benefit": None,  # Varies
            "match_score": 0.0,
        },
        {
            "program_name": "RxAssist",
            "organization": "RxAssist",
            "assistance_type": "pharmaceutical",
            "eligibility_criteria": {
                "income_threshold": 50000,
                "has_prescription": True,
            },
            "estimated_benefit": 500,
            "match_score": 0.0,
            "application_url": "https://www.rxassist.org/"
        },
        {
            "program_name": "GoodRx",
            "organization": "GoodRx",
            "assistance_type": "pharmaceutical",
            "eligibility_criteria": {},
            "estimated_benefit": 300,
            "match_score": 0.9,
            "application_url": "https://www.goodrx.com/"
        },
        {
            "program_name": "Patient Access Network Foundation",
            "organization": "PAN Foundation",
            "assistance_type": "financial",
            "eligibility_criteria": {
                "income_threshold": 60000,
                "has_diagnosis": True,
            },
            "estimated_benefit": 10000,
            "match_score": 0.0,
            "application_url": "https://www.panfoundation.org/"
        },
        {
            "program_name": "HealthWell Foundation",
            "organization": "HealthWell",
            "assistance_type": "financial",
            "eligibility_criteria": {
                "income_threshold": 72000,
                "has_diagnosis": True,
            },
            "estimated_benefit": 15000,
            "match_score": 0.0,
            "application_url": "https://www.healthwellfoundation.org/"
        },
        {
            "program_name": "Medicare Savings Programs",
            "organization": "State Medicaid",
            "assistance_type": "insurance",
            "eligibility_criteria": {
                "has_medicare": True,
                "income_threshold": 20000,
            },
            "estimated_benefit": 5000,
            "match_score": 0.0,
        },
        {
            "program_name": "Health Insurance Marketplace Subsidies",
            "organization": "Healthcare.gov",
            "assistance_type": "insurance",
            "eligibility_criteria": {
                "income_threshold": 60000,
                "no_employer_insurance": True,
            },
            "estimated_benefit": 3000,
            "match_score": 0.0,
            "application_url": "https://www.healthcare.gov/"
        },
    ]
    
    def find_matching_programs(
        self,
        annual_income: Optional[float],
        household_size: Optional[int],
        insurance_info: Optional[InsuranceInfo],
        medical_debt: float = 0.0,
        has_prescriptions: bool = False,
        has_diagnosis: bool = True
    ) -> List[AssistanceProgram]:
        """Find matching assistance programs"""
        
        matching_programs = []
        
        for program_data in self.PROGRAMS:
            match_score = self._calculate_match_score(
                program_data,
                annual_income,
                household_size,
                insurance_info,
                medical_debt,
                has_prescriptions,
                has_diagnosis
            )
            
            if match_score > 0:
                program_data_copy = program_data.copy()
                program_data_copy["match_score"] = match_score
                
                matching_programs.append(
                    AssistanceProgram(**program_data_copy)
                )
        
        # Sort by match score descending
        matching_programs.sort(key=lambda x: x.match_score, reverse=True)
        
        return matching_programs
    
    def _calculate_match_score(
        self,
        program: Dict[str, Any],
        annual_income: Optional[float],
        household_size: Optional[int],
        insurance_info: Optional[InsuranceInfo],
        medical_debt: float,
        has_prescriptions: bool,
        has_diagnosis: bool
    ) -> float:
        """Calculate match score for a program"""
        
        score = 0.0
        criteria = program.get("eligibility_criteria", {})
        
        # Income-based matching
        income_threshold = criteria.get("income_threshold")
        if income_threshold and annual_income:
            if annual_income <= income_threshold:
                score += 0.4
            elif annual_income <= income_threshold * 1.5:
                score += 0.2
        
        # Insurance-based matching
        if criteria.get("has_medicare") and insurance_info:
            if insurance_info.insurance_type.value == "medicare":
                score += 0.3
        
        if criteria.get("no_employer_insurance") and not insurance_info:
            score += 0.3
        
        # Prescription matching
        if criteria.get("has_prescription"):
            if has_prescriptions:
                score += 0.2
            else:
                return 0.0  # Required criteria not met
        
        # Diagnosis matching
        if criteria.get("has_diagnosis"):
            if has_diagnosis:
                score += 0.2
            else:
                return 0.0  # Required criteria not met
        
        # Debt-based (if no specific income threshold)
        if not income_threshold and medical_debt > 1000:
            score += 0.3
        
        # Universal programs get base score
        if not criteria:
            score = 0.9
        
        return min(score, 1.0)


# Singleton instance
assistance_matcher = AssistanceMatcher()



