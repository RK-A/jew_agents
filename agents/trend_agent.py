"""Trend analysis agent for fashion journal parsing and trend identification using LangGraph"""

import logging
from typing import Dict, Any, List
import re
from collections import Counter

from langgraph.graph import StateGraph, END

from agents.base_agent import BaseAgent
from agents.graph_states import TrendState


logger = logging.getLogger(__name__)


class TrendAgent(BaseAgent):
    """Agent for analyzing fashion trends from journals and articles using LangGraph"""
    
    DEFAULT_SYSTEM_PROMPT = """You are a fashion trend analyst specializing in jewelry and accessories.
Your role is to analyze fashion journals, identify emerging trends, and provide insights for product development.

When analyzing fashion content, focus on:
1. Mentioned jewelry designers and brands
2. Popular styles, shapes, and silhouettes
3. Trending materials and finishes
4. Color palettes and gemstones
5. Cultural influences and inspirations
6. Celebrity endorsements and red carpet moments
7. Seasonal trends and forecasts

Provide actionable insights for:
- Product catalog updates
- Trend scores for existing products
- New product recommendations
- Marketing messaging
"""
    
    JEWELRY_KEYWORDS = {
        "styles": ["classic", "modern", "vintage", "minimalist", "luxury", "bohemian", "art deco", "geometric"],
        "materials": ["gold", "silver", "platinum", "white_gold", "rose_gold", "titanium", "stainless_steel"],
        "gemstones": ["diamond", "ruby", "sapphire", "emerald", "pearl", "topaz", "amethyst", "opal"],
        "categories": ["rings", "necklaces", "bracelets", "earrings", "pendants", "brooches", "anklets"],
        "colors": ["gold", "silver", "rose", "yellow", "white", "black", "blue", "red", "green"],
        "descriptors": ["elegant", "bold", "delicate", "statement", "layered", "stackable", "chunky", "dainty"]
    }
    
    def __init__(self, llm_provider, rag_service=None, language: str = "auto", custom_system_prompt: str = None):
        super().__init__(llm_provider, rag_service, language, custom_system_prompt)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow for trend analysis process"""
        workflow = StateGraph(TrendState)
        
        # Add nodes
        workflow.add_node("extract_keywords", self._extract_keywords_node)
        workflow.add_node("analyze_trends", self._analyze_trends_node)
        workflow.add_node("calculate_scores", self._calculate_scores_node)
        workflow.add_node("identify_emerging", self._identify_emerging_node)
        workflow.add_node("generate_recommendations", self._generate_recommendations_node)
        workflow.add_node("generate_report", self._generate_report_node)
        
        # Define edges
        workflow.set_entry_point("extract_keywords")
        workflow.add_edge("extract_keywords", "analyze_trends")
        workflow.add_edge("analyze_trends", "calculate_scores")
        workflow.add_edge("calculate_scores", "identify_emerging")
        workflow.add_edge("identify_emerging", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    async def process(self, content: str) -> Dict[str, Any]:
        """
        Process trend analysis from fashion journal content using LangGraph workflow
        
        Args:
            content: Fashion journal article or content text
        
        Returns:
            Dict with trends, keywords, and recommendations
        """
        try:
            self.logger.info(f"Starting trend analysis on {len(content)} characters of content...")
            
            # Initialize state
            initial_state: TrendState = {
                "content": content,
                "extracted_keywords": {},
                "identified_trends": {},
                "emerging_trends": [],
                "trend_scores": {},
                "recommendations": [],
                "report": "",
                "error": None,
                "step": "start"
            }
            
            # Run graph
            final_state = await self.graph.ainvoke(initial_state)
            
            # Return result
            if final_state.get("error"):
                return {
                    "status": "error",
                    "message": final_state["error"]
                }
            
            return {
                "status": "success",
                "report": final_state["report"],
                "extracted_keywords": final_state["extracted_keywords"],
                "identified_trends": final_state["identified_trends"],
                "emerging_trends": final_state["emerging_trends"],
                "trend_scores": final_state["trend_scores"],
                "recommendations": final_state["recommendations"],
                "content_length": len(content)
            }
        
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _extract_keywords_node(self, state: TrendState) -> TrendState:
        """Node: Extract jewelry-related keywords from content"""
        try:
            extracted_keywords = await self._extract_keywords(state["content"])
            state["extracted_keywords"] = extracted_keywords
            state["step"] = "keywords_extracted"
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}", exc_info=True)
            state["error"] = str(e)
        return state
    
    async def _analyze_trends_node(self, state: TrendState) -> TrendState:
        """Node: Analyze trends using LLM"""
        try:
            trends = await self._analyze_trends(state["content"], state["extracted_keywords"])
            state["identified_trends"] = trends
            state["step"] = "trends_analyzed"
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}", exc_info=True)
            state["error"] = str(e)
        return state
    
    async def _calculate_scores_node(self, state: TrendState) -> TrendState:
        """Node: Calculate trend scores for product categories"""
        try:
            trend_scores = await self._calculate_trend_scores(state["identified_trends"])
            state["trend_scores"] = trend_scores
            state["step"] = "scores_calculated"
        except Exception as e:
            logger.error(f"Error calculating scores: {e}", exc_info=True)
            state["error"] = str(e)
        return state
    
    async def _identify_emerging_node(self, state: TrendState) -> TrendState:
        """Node: Identify emerging trends"""
        try:
            emerging_trends = await self._identify_emerging_trends(state["identified_trends"])
            state["emerging_trends"] = emerging_trends
            state["step"] = "emerging_identified"
        except Exception as e:
            logger.error(f"Error identifying emerging trends: {e}", exc_info=True)
            state["error"] = str(e)
        return state
    
    async def _generate_recommendations_node(self, state: TrendState) -> TrendState:
        """Node: Generate product and marketing recommendations"""
        try:
            recommendations = await self._generate_recommendations(
                trends=state["identified_trends"],
                emerging=state["emerging_trends"]
            )
            state["recommendations"] = recommendations
            state["step"] = "recommendations_generated"
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            state["error"] = str(e)
        return state
    
    async def _generate_report_node(self, state: TrendState) -> TrendState:
        """Node: Generate comprehensive trend analysis report"""
        try:
            report = await self._generate_trend_report(
                content=state["content"],
                extracted_keywords=state["extracted_keywords"],
                trends=state["identified_trends"],
                emerging_trends=state["emerging_trends"],
                recommendations=state["recommendations"]
            )
            state["report"] = report
            state["step"] = "report_generated"
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            state["error"] = str(e)
        return state
    
    async def _extract_keywords(self, content: str) -> Dict[str, List[str]]:
        """Extract jewelry-related keywords from content"""
        try:
            content_lower = content.lower()
            extracted = {}
            
            for category, keywords in self.JEWELRY_KEYWORDS.items():
                found = []
                for keyword in keywords:
                    # Count occurrences
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    matches = re.findall(pattern, content_lower)
                    if matches:
                        found.append({
                            "keyword": keyword,
                            "count": len(matches)
                        })
                
                if found:
                    # Sort by count
                    found.sort(key=lambda x: x["count"], reverse=True)
                    extracted[category] = found
            
            return extracted
        
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}", exc_info=True)
            return {}
    
    async def _analyze_trends(
        self,
        content: str,
        extracted_keywords: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Analyze trends using LLM"""
        try:
            import json
            
            keywords_summary = json.dumps(extracted_keywords, indent=2, ensure_ascii=False)
            
            prompt = f"""Analyze the following fashion content and extract jewelry trends.

Extracted Keywords:
{keywords_summary}

Content excerpt:
{content[:2000]}...

Identify:
1. Top 5 trending styles
2. Popular materials and metals
3. Trending colors
4. Key designers/brands mentioned
5. Seasonal predictions

Return as JSON:
{{
    "trending_styles": ["style1", "style2", ...],
    "popular_materials": ["material1", "material2", ...],
    "trending_colors": ["color1", "color2", ...],
    "mentioned_designers": ["designer1", "designer2", ...],
    "seasonal_forecast": "spring/summer/fall/winter insights"
}}

JSON:"""
            
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.4
            )
            
            # Parse JSON
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean.split("```json")[1].split("```")[0].strip()
            elif response_clean.startswith("```"):
                response_clean = response_clean.split("```")[1].split("```")[0].strip()
            
            trends = json.loads(response_clean)
            return trends
        
        except Exception as e:
            self.logger.warning(f"Error analyzing trends with LLM: {e}")
            # Fallback to keyword-based analysis
            return {
                "trending_styles": [kw["keyword"] for kw in extracted_keywords.get("styles", [])[:5]],
                "popular_materials": [kw["keyword"] for kw in extracted_keywords.get("materials", [])[:5]],
                "trending_colors": [kw["keyword"] for kw in extracted_keywords.get("colors", [])[:3]],
                "mentioned_designers": [],
                "seasonal_forecast": "Unable to determine"
            }
    
    async def _calculate_trend_scores(self, trends: Dict[str, Any]) -> Dict[str, float]:
        """Calculate trend scores for product categories"""
        try:
            scores = {}
            
            # Base scores for categories
            categories = ["rings", "necklaces", "bracelets", "earrings", "pendants"]
            
            trending_styles = trends.get("trending_styles", [])
            popular_materials = trends.get("popular_materials", [])
            
            for category in categories:
                base_score = 0.5
                
                # Boost by trending styles
                style_boost = len(trending_styles) * 0.05
                
                # Boost by popular materials
                material_boost = len(popular_materials) * 0.05
                
                total_score = min(base_score + style_boost + material_boost, 1.0)
                scores[category] = round(total_score, 2)
            
            return scores
        
        except Exception as e:
            self.logger.error(f"Error calculating trend scores: {e}", exc_info=True)
            return {}
    
    async def _identify_emerging_trends(self, trends: Dict[str, Any]) -> List[str]:
        """Identify emerging trends that are gaining momentum"""
        try:
            emerging = []
            
            # Check for new/unique combinations
            styles = trends.get("trending_styles", [])
            materials = trends.get("popular_materials", [])
            
            # Cross-reference to find interesting combinations
            for style in styles[:3]:
                for material in materials[:2]:
                    emerging.append(f"{material} {style} jewelry")
            
            return emerging[:5]
        
        except Exception as e:
            self.logger.error(f"Error identifying emerging trends: {e}", exc_info=True)
            return []
    
    async def _generate_recommendations(
        self,
        trends: Dict[str, Any],
        emerging: List[str]
    ) -> List[Dict[str, str]]:
        """Generate product and marketing recommendations"""
        try:
            recommendations = []
            
            # Product recommendations
            trending_styles = trends.get("trending_styles", [])
            if trending_styles:
                recommendations.append({
                    "type": "product",
                    "priority": "high",
                    "action": f"Increase inventory of {', '.join(trending_styles[:3])} style products"
                })
            
            popular_materials = trends.get("popular_materials", [])
            if popular_materials:
                recommendations.append({
                    "type": "product",
                    "priority": "high",
                    "action": f"Focus on {', '.join(popular_materials[:3])} materials for new collections"
                })
            
            # Emerging trend recommendations
            if emerging:
                recommendations.append({
                    "type": "innovation",
                    "priority": "medium",
                    "action": f"Explore new designs: {', '.join(emerging[:2])}"
                })
            
            # Marketing recommendations
            designers = trends.get("mentioned_designers", [])
            if designers:
                recommendations.append({
                    "type": "marketing",
                    "priority": "medium",
                    "action": f"Highlight designer inspiration: {', '.join(designers[:2])}"
                })
            
            return recommendations
        
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return []
    
    async def _generate_trend_report(
        self,
        content: str,
        extracted_keywords: Dict[str, List[str]],
        trends: Dict[str, Any],
        emerging_trends: List[str],
        recommendations: List[Dict[str, str]]
    ) -> str:
        """Generate comprehensive trend analysis report using LLM"""
        try:
            import json
            
            context = f"""
=== Extracted Keywords ===
{json.dumps(extracted_keywords, indent=2, ensure_ascii=False)}

=== Identified Trends ===
{json.dumps(trends, indent=2, ensure_ascii=False)}

=== Emerging Trends ===
{json.dumps(emerging_trends, indent=2, ensure_ascii=False)}

=== Recommendations ===
{json.dumps(recommendations, indent=2, ensure_ascii=False)}
"""
            
            system_prompt = self.get_system_prompt(self.DEFAULT_SYSTEM_PROMPT)
            
            prompt = f"""{system_prompt}

Based on fashion journal analysis, generate a comprehensive trend report:

{context}

Content excerpt:
{content[:1000]}...

Generate a report covering:
1. Executive Summary
2. Key Trend Findings
3. Emerging Opportunities
4. Product Development Recommendations
5. Marketing Strategy Suggestions

Report:"""
            
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.6
            )
            
            return response.strip()
        
        except Exception as e:
            self.logger.error(f"Error generating trend report: {e}", exc_info=True)
            return "Error generating report. See detailed data in response."

