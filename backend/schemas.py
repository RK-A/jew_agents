"""Pydantic schemas for API requests and responses"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Consultation schemas
class ConsultationRequest(BaseModel):
    """Request schema for consultation endpoint"""
    message: str = Field(..., description="User message for consultation")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Optional conversation history"
    )


class ConsultationResponse(BaseModel):
    """Response schema for consultation endpoint"""
    status: str = Field(..., description="Status: success or error")
    agent: str = Field(..., description="Agent type used")
    response: Optional[str] = Field(None, description="Agent response text")
    recommendations: Optional[List[str]] = Field(
        None,
        description="List of recommended product IDs"
    )
    extracted_preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted user preferences"
    )
    questions_for_user: Optional[List[str]] = Field(
        None,
        description="Follow-up questions for user"
    )
    error: Optional[str] = Field(None, description="Error message if status is error")


# Customer profile schemas
class CustomerProfileResponse(BaseModel):
    """Response schema for customer profile"""
    user_id: str
    style_preference: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_materials: Optional[List[str]] = None
    skin_tone: Optional[str] = None
    occasion_types: Optional[List[str]] = None
    consultation_history: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CustomerPreferenceUpdate(BaseModel):
    """Request schema for updating customer preferences"""
    style_preference: Optional[str] = Field(None, description="Style preference: classic, modern, vintage, minimalist, luxury")
    budget_min: Optional[float] = Field(None, description="Minimum budget", ge=0)
    budget_max: Optional[float] = Field(None, description="Maximum budget", ge=0)
    preferred_materials: Optional[List[str]] = Field(None, description="Preferred materials: gold, silver, platinum, white_gold")
    skin_tone: Optional[str] = Field(None, description="Skin tone: warm, cool, neutral")
    occasion_types: Optional[List[str]] = Field(None, description="Occasion types: everyday, formal, wedding, gift")


class CustomerPreferenceUpdateResponse(BaseModel):
    """Response schema for preference update"""
    status: str
    user_id: str
    updated_fields: List[str]
    message: str


# Analysis schemas
class AnalysisReportResponse(BaseModel):
    """Response schema for customer analysis"""
    status: str = Field(..., description="Status: success or error")
    agent: str = Field(..., description="Agent type used")
    report: Optional[Dict[str, Any]] = Field(None, description="Analysis report")
    popular_styles: Optional[List[str]] = Field(None, description="Popular jewelry styles")
    budget_distribution: Optional[Dict[str, int]] = Field(None, description="Budget distribution")
    demand_forecast: Optional[Dict[str, Any]] = Field(None, description="Product demand forecast")
    insights: Optional[List[str]] = Field(None, description="Key insights")
    error: Optional[str] = Field(None, description="Error message if status is error")


# Trend analysis schemas
class TrendAnalysisRequest(BaseModel):
    """Request schema for trend analysis"""
    content: str = Field(..., description="Fashion journal or article content to analyze")
    source: Optional[str] = Field(None, description="Source of the content")
    date: Optional[str] = Field(None, description="Publication date")


class TrendReportResponse(BaseModel):
    """Response schema for trend analysis"""
    status: str = Field(..., description="Status: success or error")
    agent: str = Field(..., description="Agent type used")
    trends: Optional[List[str]] = Field(None, description="Identified trends")
    keywords: Optional[List[str]] = Field(None, description="Trend keywords")
    mentioned_products: Optional[List[str]] = Field(None, description="Mentioned product types")
    trend_scores: Optional[Dict[str, float]] = Field(None, description="Category trend scores")
    recommendations: Optional[List[str]] = Field(None, description="Product recommendations")
    insights: Optional[str] = Field(None, description="Trend insights")
    error: Optional[str] = Field(None, description="Error message if status is error")


# Product search schemas
class ProductSearchRequest(BaseModel):
    """Request schema for product search"""
    query: str = Field(..., description="Search query for products")
    limit: int = Field(5, description="Number of products to return", ge=1, le=20)
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters (category, material, price_min, price_max)")


class ProductInfo(BaseModel):
    """Product information schema"""
    id: str
    name: str
    description: str
    category: str
    material: str
    weight: float
    price: float
    design_details: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None
    stock_count: int
    score: Optional[float] = Field(None, description="Relevance score")


class ProductSearchResponse(BaseModel):
    """Response schema for product search"""
    status: str = Field(..., description="Status: success or error")
    query: str = Field(..., description="Original search query")
    products: List[ProductInfo] = Field(..., description="List of found products")
    total_found: int = Field(..., description="Total number of products found")
    error: Optional[str] = Field(None, description="Error message if status is error")


# Health check schema
class HealthResponse(BaseModel):
    """Response schema for health check"""
    status: str = Field(..., description="Health status: healthy or unhealthy")
    provider: str = Field(..., description="LLM provider in use")
    model: str = Field(..., description="LLM model in use")
    database_connected: bool = Field(..., description="Database connection status")
    qdrant_connected: bool = Field(..., description="Qdrant connection status")
    agents_status: Optional[Dict[str, Any]] = Field(None, description="Status of all agents")


# Generic error response
class ErrorResponse(BaseModel):
    """Generic error response schema"""
    status: str = "error"
    error: str
    detail: Optional[str] = None

