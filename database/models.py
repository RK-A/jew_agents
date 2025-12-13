from sqlalchemy import Column, String, Integer, Float, JSON, ARRAY, DateTime, Text, Identity
from sqlalchemy.sql import func
from datetime import datetime

from database.session import Base


class JewelryProduct(Base):
    """Jewelry products inventory table"""
    __tablename__ = "jewelry_products"
    
    id = Column(Integer, Identity(start=1, cycle=False), primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)  # rings, necklaces, bracelets, earrings, pendants
    material = Column(String, nullable=False, index=True)  # gold, silver, platinum, white_gold
    weight = Column(Float, nullable=False)  # weight in grams
    price = Column(Float, nullable=False, index=True)
    design_details = Column(JSON, nullable=True)  # metal_purity, stone_type, stone_cut, etc.
    images = Column(ARRAY(String), nullable=True)  # array of image URLs
    stock_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CustomerPreference(Base):
    """Customer preferences and profiles table"""
    __tablename__ = "customer_preferences"
    
    user_id = Column(String, primary_key=True, index=True)
    style_preference = Column(String, nullable=True)  # classic, modern, vintage, minimalist, luxury
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    preferred_materials = Column(ARRAY(String), nullable=True)  # array of materials
    skin_tone = Column(String, nullable=True)  # warm, cool, neutral
    occasion_types = Column(ARRAY(String), nullable=True)  # everyday, formal, wedding, gift
    consultation_history = Column(JSON, nullable=True, default=list)  # history of interactions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())


class ConsultationRecord(Base):
    """Consultation history records table"""
    __tablename__ = "consultation_records"
    
    id = Column(Integer, Identity(start=1, cycle=False), primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    agent_type = Column(String, nullable=False)  # consultant, analysis, trend
    message = Column(Text, nullable=False)  # user message
    response = Column(Text, nullable=False)  # agent response
    recommendations = Column(JSON, nullable=True)  # array of product IDs
    preference_updates = Column(JSON, nullable=True)  # what was updated in profile
    created_at = Column(DateTime(timezone=True), server_default=func.now())

