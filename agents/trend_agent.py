"""Trend analysis agent for fashion journal parsing and trend identification"""

from typing import Dict, Any, List
import re
from collections import Counter

from agents.base_agent import BaseAgent


class TrendAgent(BaseAgent):
    """Agent for analyzing fashion trends from journals and articles"""
    
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
    
    async def process(self, content: str) -> Dict[str, Any]:
        """
        Process trend analysis from fashion journal content
        
        Args:
            content: Fashion journal article or content text
        
        Returns:
            Dict with trends, keywords, and recommendations
        """
        try:
            self.logger.info(f"Starting trend analysis on {len(content)} characters of content...")
            
            # 1. Parse content and extract keywords
            extracted_keywords = await self._extract_keywords(content)
            
            # 2. Analyze trends from content
            trends = await self._analyze_trends(content, extracted_keywords)
            
            # 3. Generate product trend scores
            trend_scores = await self._calculate_trend_scores(trends)
            
            # 4. Identify emerging trends
            emerging_trends = await self._identify_emerging_trends(trends)
            
            # 5. Generate recommendations
            recommendations = await self._generate_recommendations(
                trends=trends,
                emerging=emerging_trends
            )
            
            # 6. Generate comprehensive report
            report = await self._generate_trend_report(
                content=content,
                extracted_keywords=extracted_keywords,
                trends=trends,
                emerging_trends=emerging_trends,
                recommendations=recommendations
            )
            
            return {
                "status": "success",
                "report": report,
                "extracted_keywords": extracted_keywords,
                "identified_trends": trends,
                "emerging_trends": emerging_trends,
                "trend_scores": trend_scores,
                "recommendations": recommendations,
                "content_length": len(content)
            }
        
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
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

