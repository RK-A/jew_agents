"""Customer analysis agent for market insights and demand forecasting"""

from typing import Dict, Any, List
from collections import Counter
from datetime import datetime

from agents.base_agent import BaseAgent
from database.session import async_session_factory
from database.repositories import CustomerPreferenceRepository, ConsultationRecordRepository


class AnalysisAgent(BaseAgent):
    """Agent for analyzing customer preferences and forecasting demand"""
    
    SYSTEM_PROMPT = """You are a market analyst specializing in jewelry retail and customer behavior.
Your role is to analyze customer preferences, identify trends, and provide actionable insights for business decisions.

When analyzing customer data, focus on:
1. Most popular styles, materials, and price ranges
2. Emerging customer segments and their characteristics
3. Underserved market segments with growth potential
4. Seasonal patterns and occasion-based demand
5. Price sensitivity and budget distributions
6. Material preferences and their correlation with demographics

Provide clear, data-driven insights with specific recommendations for:
- Inventory optimization
- Marketing strategies
- Product development priorities
- Pricing strategies
"""
    
    async def process(self) -> Dict[str, Any]:
        """
        Process customer analysis
        
        Returns:
            Dict with analysis results, trends, and recommendations
        """
        try:
            self.logger.info("Starting customer analysis...")
            
            # 1. Get all customer preferences
            all_preferences = await self._get_all_customer_preferences()
            
            if not all_preferences:
                return {
                    "status": "no_data",
                    "message": "No customer data available for analysis"
                }
            
            # 2. Analyze preference patterns
            patterns = await self._analyze_patterns(all_preferences)
            
            # 3. Get consultation history
            consultation_stats = await self._analyze_consultation_history()
            
            # 4. Generate demand forecast
            demand_forecast = await self._forecast_demand(patterns)
            
            # 5. Identify customer segments
            segments = await self._identify_segments(all_preferences)
            
            # 6. Generate insights via LLM
            report = await self._generate_analysis_report(
                patterns=patterns,
                consultation_stats=consultation_stats,
                demand_forecast=demand_forecast,
                segments=segments
            )
            
            return {
                "status": "success",
                "report": report,
                "patterns": patterns,
                "consultation_stats": consultation_stats,
                "demand_forecast": demand_forecast,
                "customer_segments": segments,
                "total_customers": len(all_preferences),
                "generated_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error in customer analysis: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _get_all_customer_preferences(self) -> List[Dict[str, Any]]:
        """Fetch all customer preferences from database"""
        try:
            async with async_session_factory() as session:
                repo = CustomerPreferenceRepository(session)
                preferences = await repo.get_all()
                
                return [
                    {
                        "user_id": p.user_id,
                        "style_preference": p.style_preference,
                        "budget_min": float(p.budget_min) if p.budget_min else None,
                        "budget_max": float(p.budget_max) if p.budget_max else None,
                        "preferred_materials": p.preferred_materials or [],
                        "skin_tone": p.skin_tone,
                        "occasion_types": p.occasion_types or [],
                    }
                    for p in preferences
                ]
        except Exception as e:
            self.logger.error(f"Error fetching customer preferences: {e}", exc_info=True)
            return []
    
    async def _analyze_patterns(self, preferences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in customer preferences"""
        try:
            # Style preferences
            styles = [p["style_preference"] for p in preferences if p.get("style_preference")]
            style_counts = Counter(styles)
            
            # Material preferences
            all_materials = []
            for p in preferences:
                all_materials.extend(p.get("preferred_materials", []))
            material_counts = Counter(all_materials)
            
            # Budget analysis
            budgets = []
            for p in preferences:
                if p.get("budget_max"):
                    budgets.append(p["budget_max"])
            
            avg_budget = sum(budgets) / len(budgets) if budgets else 0
            budget_ranges = {
                "under_20k": sum(1 for b in budgets if b < 20000),
                "20k_50k": sum(1 for b in budgets if 20000 <= b < 50000),
                "50k_100k": sum(1 for b in budgets if 50000 <= b < 100000),
                "over_100k": sum(1 for b in budgets if b >= 100000),
            }
            
            # Skin tone preferences
            skin_tones = [p["skin_tone"] for p in preferences if p.get("skin_tone")]
            skin_tone_counts = Counter(skin_tones)
            
            # Occasion types
            all_occasions = []
            for p in preferences:
                all_occasions.extend(p.get("occasion_types", []))
            occasion_counts = Counter(all_occasions)
            
            return {
                "popular_styles": dict(style_counts.most_common()),
                "popular_materials": dict(material_counts.most_common()),
                "average_budget": round(avg_budget, 2),
                "budget_distribution": budget_ranges,
                "skin_tone_distribution": dict(skin_tone_counts),
                "popular_occasions": dict(occasion_counts.most_common()),
                "total_analyzed": len(preferences)
            }
        
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {e}", exc_info=True)
            return {}
    
    async def _analyze_consultation_history(self) -> Dict[str, Any]:
        """Analyze consultation records"""
        try:
            async with async_session_factory() as session:
                repo = ConsultationRecordRepository(session)
                records = await repo.get_all(limit=500)
                
                # Agent type distribution
                agent_types = [r.agent_type for r in records]
                agent_counts = Counter(agent_types)
                
                # Recommendations analysis
                total_recommendations = 0
                for r in records:
                    if r.recommendations:
                        total_recommendations += len(r.recommendations)
                
                avg_recommendations = (
                    total_recommendations / len(records) if records else 0
                )
                
                return {
                    "total_consultations": len(records),
                    "agent_type_distribution": dict(agent_counts),
                    "average_recommendations_per_consultation": round(avg_recommendations, 2),
                    "recent_consultations_count": len([r for r in records if r.created_at]),
                }
        
        except Exception as e:
            self.logger.error(f"Error analyzing consultation history: {e}", exc_info=True)
            return {}
    
    async def _forecast_demand(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast product demand based on patterns"""
        try:
            popular_styles = patterns.get("popular_styles", {})
            popular_materials = patterns.get("popular_materials", {})
            
            # Calculate demand scores
            demand_forecast = {}
            
            # Combine style and material for categories
            categories = ["rings", "necklaces", "bracelets", "earrings", "pendants"]
            
            for category in categories:
                # Simple demand score based on patterns
                base_score = 50
                
                # Boost by popular occasions
                occasion_boost = sum(patterns.get("popular_occasions", {}).values()) / 10
                
                demand_forecast[category] = {
                    "demand_score": round(base_score + occasion_boost, 2),
                    "recommended_stock": "high" if base_score + occasion_boost > 60 else "medium",
                    "top_style": max(popular_styles.items(), key=lambda x: x[1])[0] if popular_styles else "classic",
                    "top_material": max(popular_materials.items(), key=lambda x: x[1])[0] if popular_materials else "gold"
                }
            
            return demand_forecast
        
        except Exception as e:
            self.logger.error(f"Error forecasting demand: {e}", exc_info=True)
            return {}
    
    async def _identify_segments(self, preferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify customer segments"""
        try:
            segments = []
            
            # Budget-based segments
            luxury_customers = [
                p for p in preferences
                if p.get("budget_max") and p["budget_max"] >= 100000
            ]
            if luxury_customers:
                segments.append({
                    "name": "Luxury Buyers",
                    "size": len(luxury_customers),
                    "characteristics": {
                        "avg_budget": sum(p["budget_max"] for p in luxury_customers) / len(luxury_customers),
                        "common_styles": Counter(p["style_preference"] for p in luxury_customers if p.get("style_preference")).most_common(2)
                    }
                })
            
            # Mid-range segment
            mid_range = [
                p for p in preferences
                if p.get("budget_max") and 20000 <= p["budget_max"] < 100000
            ]
            if mid_range:
                segments.append({
                    "name": "Mid-Range Buyers",
                    "size": len(mid_range),
                    "characteristics": {
                        "avg_budget": sum(p["budget_max"] for p in mid_range) / len(mid_range),
                        "common_styles": Counter(p["style_preference"] for p in mid_range if p.get("style_preference")).most_common(2)
                    }
                })
            
            # Budget-conscious segment
            budget_conscious = [
                p for p in preferences
                if p.get("budget_max") and p["budget_max"] < 20000
            ]
            if budget_conscious:
                segments.append({
                    "name": "Budget-Conscious Buyers",
                    "size": len(budget_conscious),
                    "characteristics": {
                        "avg_budget": sum(p["budget_max"] for p in budget_conscious) / len(budget_conscious),
                        "common_styles": Counter(p["style_preference"] for p in budget_conscious if p.get("style_preference")).most_common(2)
                    }
                })
            
            return segments
        
        except Exception as e:
            self.logger.error(f"Error identifying segments: {e}", exc_info=True)
            return []
    
    async def _generate_analysis_report(
        self,
        patterns: Dict[str, Any],
        consultation_stats: Dict[str, Any],
        demand_forecast: Dict[str, Any],
        segments: List[Dict[str, Any]]
    ) -> str:
        """Generate comprehensive analysis report using LLM"""
        try:
            import json
            
            context = f"""
=== Customer Preference Patterns ===
{json.dumps(patterns, indent=2, ensure_ascii=False)}

=== Consultation Statistics ===
{json.dumps(consultation_stats, indent=2, ensure_ascii=False)}

=== Demand Forecast ===
{json.dumps(demand_forecast, indent=2, ensure_ascii=False)}

=== Customer Segments ===
{json.dumps(segments, indent=2, ensure_ascii=False)}
"""
            
            prompt = f"""{self.SYSTEM_PROMPT}

Based on the following data analysis, provide a comprehensive market insights report:

{context}

Generate a report covering:
1. Executive Summary (key findings)
2. Customer Preference Analysis
3. Market Demand Forecast
4. Customer Segmentation Insights
5. Strategic Recommendations (top 5 actionable items)

Report:"""
            
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.5
            )
            
            return response.strip()
        
        except Exception as e:
            self.logger.error(f"Error generating analysis report: {e}", exc_info=True)
            return "Error generating report. See detailed data in response."

