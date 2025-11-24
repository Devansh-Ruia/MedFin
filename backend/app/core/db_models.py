from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    insurance_info = relationship("UserInsurance", back_populates="user", uselist=False)
    bills = relationship("SavedBill", back_populates="user", cascade="all, delete-orphan")
    navigation_plans = relationship("SavedNavigationPlan", back_populates="user", cascade="all, delete-orphan")
    cost_estimates = relationship("SavedCostEstimate", back_populates="user", cascade="all, delete-orphan")


class UserInsurance(Base):
    __tablename__ = "user_insurance"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    insurance_type = Column(String, nullable=False)
    plan_name = Column(String, nullable=True)
    deductible = Column(Float, default=0.0)
    deductible_remaining = Column(Float, default=0.0)
    out_of_pocket_max = Column(Float, default=0.0)
    out_of_pocket_used = Column(Float, default=0.0)
    coverage_percentage = Column(Float, default=0.80)
    copay_primary = Column(Float, nullable=True)
    copay_specialist = Column(Float, nullable=True)
    copay_emergency = Column(Float, nullable=True)
    in_network = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="insurance_info")


class SavedBill(Base):
    __tablename__ = "saved_bills"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bill_id = Column(String, nullable=False)
    provider_name = Column(String, nullable=False)
    service_date = Column(String, nullable=False)
    services = Column(JSON, nullable=False)  # Store as JSON
    total_amount = Column(Float, nullable=False)
    insurance_paid = Column(Float, nullable=True)
    patient_responsibility = Column(Float, nullable=False)
    due_date = Column(String, nullable=True)
    status = Column(String, default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="bills")


class SavedNavigationPlan(Base):
    __tablename__ = "saved_navigation_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_data = Column(JSON, nullable=False)  # Store entire plan as JSON
    current_financial_situation = Column(JSON, nullable=False)
    projected_savings = Column(Float, nullable=False)
    status = Column(String, default="active")  # active, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="navigation_plans")


class SavedCostEstimate(Base):
    __tablename__ = "saved_cost_estimates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_type = Column(String, nullable=False)
    procedure_code = Column(String, nullable=True)
    description = Column(String, nullable=True)
    location = Column(String, nullable=True)
    estimated_cost = Column(Float, nullable=False)
    insurance_coverage = Column(Float, nullable=True)
    patient_responsibility = Column(Float, nullable=False)
    breakdown = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=False)
    alternatives = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="cost_estimates")
