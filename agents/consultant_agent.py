"""Consultation agent for personalized jewelry recommendations"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.base_agent import BaseAgent
from database.session import async_session_factory
from database.repositories import CustomerPreferenceRepository
from rag.retrieval import RAGRetriever


def _clean_thinking_blocks(text: str) -> str:
    """Remove [THINK]...[/THINK] blocks from LLM response"""
    cleaned = re.sub(r'\[THINK\].*?\[/THINK\]', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
    return cleaned.strip()


class ConsultantAgent(BaseAgent):
    """Agent for interactive jewelry consultation and recommendations"""
    
    DEFAULT_SYSTEM_PROMPT = """You are an expert jewelry consultant with deep knowledge of precious metals, gemstones, and fashion trends.
Your role is to help customers find the perfect jewelry by understanding their preferences, style, budget, and occasion.

IMPORTANT: Respond ONLY with your customer-facing message. Do NOT include internal thoughts, reasoning, or [THINK] blocks in your response.

Guidelines:
1. Be warm, friendly, and professional
2. Ask clarifying questions when preferences are unclear
3. Provide 3-5 specific product recommendations with explanations
4. Explain WHY each recommendation fits their needs
5. Consider budget constraints carefully
6. Suggest complementary pieces when appropriate
7. Educate customers about materials, styles, and care

If the customer hasn't shared their preferences yet, gently ask about:
- What type of jewelry they're looking for (ring, necklace, bracelet, etc.)
- The occasion (everyday wear, formal event, gift, wedding, etc.)
- Their style preference (classic, modern, vintage, minimalist, luxury)
- Budget range
- Preferred materials (gold, silver, platinum, etc.)
- Skin tone (to recommend complementary metals)
"""
    
    def __init__(self, llm_provider, rag_service, language: str = "auto", custom_system_prompt: str = None):
        super().__init__(llm_provider, rag_service, language, custom_system_prompt)
        self.rag_retriever = RAGRetriever(rag_service) if rag_service else None
    
    async def process(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process consultation request
        
        Args:
            user_id: User identifier
            message: User message/query
            conversation_history: Optional previous conversation messages
        
        Returns:
            Dict with recommendations, questions, and extracted preferences
        """
        try:
            self.logger.info(f"Processing consultation for user {user_id}: {message[:50]}...")
            
            # 1. Get customer profile
            profile = await self._get_customer_profile(user_id)
            
            # 2. Extract preferences from message
            extracted_prefs = await self._extract_preferences_from_message(message)
            
            # 3. Merge with existing profile
            if profile:
                merged_prefs = self._merge_preferences(profile, extracted_prefs)
            else:
                merged_prefs = extracted_prefs
            
            # 4. Search products via RAG
            products = []
            if self.rag_retriever and merged_prefs:
                rag_result = await self.rag_retriever.retrieve_relevant_products(
                    query=message,
                    user_preferences=merged_prefs,
                    limit=8,
                    include_context=False
                )
                products = rag_result.get("products", [])
            
            # 5. Generate recommendations via LLM
            response = await self._generate_consultation_response(
                message=message,
                user_profile=merged_prefs,
                products=products,
                conversation_history=conversation_history
            )
            
            # 6. Update customer preferences if changed
            if extracted_prefs and any(extracted_prefs.values()):
                await self._update_customer_preferences(user_id, extracted_prefs, profile is None)
            
            # 7. Log interaction
            product_ids = self._extract_product_ids(products[:5])
            await self.log_interaction(
                user_id=user_id,
                agent_type="consultant",
                input_msg=message,
                output_msg=response,
                recommendations=product_ids,
                preference_updates=extracted_prefs
            )
            
            return {
                "response": response,
                "recommendations": products[:5],
                "extracted_preferences": extracted_prefs,
                "has_profile": profile is not None,
                "user_id": user_id
            }
        
        except Exception as e:
            self.logger.error(f"Error processing consultation for user {user_id}: {e}", exc_info=True)
            return {
                "response": "Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.",
                "recommendations": [],
                "extracted_preferences": {},
                "error": str(e)
            }
    
    async def _get_customer_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get customer profile from database"""
        try:
            async with async_session_factory() as session:
                repo = CustomerPreferenceRepository(session)
                preference = await repo.get_by_user_id(user_id)
                
                if not preference:
                    return None
                
                return {
                    "user_id": preference.user_id,
                    "style_preference": preference.style_preference,
                    "budget_min": float(preference.budget_min) if preference.budget_min else None,
                    "budget_max": float(preference.budget_max) if preference.budget_max else None,
                    "preferred_materials": preference.preferred_materials or [],
                    "skin_tone": preference.skin_tone,
                    "occasion_types": preference.occasion_types or [],
                }
        except Exception as e:
            self.logger.error(f"Error getting customer profile {user_id}: {e}", exc_info=True)
            return None
    
    async def _extract_preferences_from_message(self, message: str) -> Dict[str, Any]:
        """Extract preferences from user message using LLM"""
        try:
            extraction_prompt = f"""Extract jewelry preferences from the following customer message.
Return ONLY valid JSON with these fields (use null for missing info):
{{
    "style_preference": "classic|modern|vintage|minimalist|luxury|null",
    "budget_min": number or null,
    "budget_max": number or null,
    "preferred_materials": ["gold", "silver", "platinum", "white_gold"] or [],
    "skin_tone": "warm|cool|neutral|null",
    "occasion_types": ["everyday", "formal", "wedding", "gift"] or [],
    "category": "rings|necklaces|bracelets|earrings|pendants|null"
}}

Customer message: "{message}"

JSON:"""
            
            response = await self.llm.generate(
                prompt=extraction_prompt,
                temperature=0.3
            )
            
            # Parse JSON response
            import json
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean.split("```json")[1].split("```")[0].strip()
            elif response_clean.startswith("```"):
                response_clean = response_clean.split("```")[1].split("```")[0].strip()
            
            extracted = json.loads(response_clean)
            
            # Filter out null values
            return {k: v for k, v in extracted.items() if v not in (None, "null", "")}
        
        except Exception as e:
            self.logger.warning(f"Error extracting preferences: {e}")
            return {}
    
    def _merge_preferences(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge new preferences with existing ones"""
        merged = existing.copy()
        
        for key, value in new.items():
            if value is not None:
                if key in ["preferred_materials", "occasion_types"]:
                    # Merge lists
                    existing_list = set(merged.get(key, []))
                    new_list = set(value if isinstance(value, list) else [value])
                    merged[key] = list(existing_list | new_list)
                else:
                    # Override with new value
                    merged[key] = value
        
        return merged
    
    async def _generate_consultation_response(
        self,
        message: str,
        user_profile: Dict[str, Any],
        products: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate consultation response using LLM"""
        try:
            # Build context
            context = await self._build_context_string(
                user_profile=user_profile,
                products=products
            )
            
            # Build conversation history
            history_text = ""
            if conversation_history:
                history_parts = []
                for msg in conversation_history[-5:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    history_parts.append(f"{role.capitalize()}: {content}")
                history_text = "\n".join(history_parts)
            
            # Prepare history section for prompt
            history_section = f"Previous conversation:\n{history_text}" if history_text else ""
            
            system_prompt = self.get_system_prompt(self.DEFAULT_SYSTEM_PROMPT)
            
            prompt = f"""{system_prompt}

{context}

{history_section}

Customer: {message}

Consultant:"""
            
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.7
            )
            
            return _clean_thinking_blocks(response)
        
        except Exception as e:
            self.logger.error(f"Error generating response: {e}", exc_info=True)
            return "Извините, не могу сформировать ответ. Попробуйте переформулировать вопрос."
    
    async def _update_customer_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
        is_new: bool = False
    ) -> bool:
        """Update or create customer preferences in database"""
        try:
            async with async_session_factory() as session:
                repo = CustomerPreferenceRepository(session)
                
                # Prepare data
                pref_data = {
                    "user_id": user_id,
                    "style_preference": preferences.get("style_preference"),
                    "budget_min": preferences.get("budget_min"),
                    "budget_max": preferences.get("budget_max"),
                    "preferred_materials": preferences.get("preferred_materials", []),
                    "skin_tone": preferences.get("skin_tone"),
                    "occasion_types": preferences.get("occasion_types", []),
                    "last_updated": datetime.utcnow()
                }
                
                if is_new:
                    pref_data["created_at"] = datetime.utcnow()
                    pref_data["consultation_history"] = []
                    await repo.create(pref_data)
                else:
                    await repo.update(user_id, pref_data)
                
                await session.commit()
                self.logger.info(f"Updated preferences for user {user_id}")
                return True
        
        except Exception as e:
            self.logger.error(f"Error updating preferences for user {user_id}: {e}", exc_info=True)
            return False

