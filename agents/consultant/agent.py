"""Consultation agent for personalized jewelry recommendations using LangGraph"""

import re
import logging
from typing import Dict, Any, Optional, List, cast
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from agents.base_agent import BaseAgent
from agents.consultant.state import ConsultantState
from database.session import async_session_factory
from database.repositories import CustomerPreferenceRepository
from rag.retrieval import RAGRetriever


logger = logging.getLogger(__name__)


def _clean_thinking_blocks(text: str) -> str:
    """Remove [THINK]...[/THINK] blocks from LLM response"""
    cleaned = re.sub(r'\[THINK\].*?\[/THINK\]', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
    return cleaned.strip()


class ConsultantAgent(BaseAgent):
    """Agent for interactive jewelry consultation and recommendations using LangGraph"""

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

    def __init__(self, llm_provider, rag_service, language: str = "auto", custom_system_prompt: Optional[str] = None):
        super().__init__(llm_provider, rag_service, language, custom_system_prompt)
        self.rag_retriever = RAGRetriever(rag_service) if rag_service else None
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow for consultation process"""
        workflow = StateGraph(ConsultantState)

        # Add nodes
        workflow.add_node("load_profile", self._load_profile_node)
        workflow.add_node("extract_preferences",
                          self._extract_preferences_node)
        workflow.add_node("search_products", self._search_products_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("update_profile", self._update_profile_node)
        workflow.add_node("log_interaction", self._log_interaction_node)

        # Define edges
        workflow.set_entry_point("load_profile")
        workflow.add_edge("load_profile", "extract_preferences")
        workflow.add_edge("extract_preferences", "search_products")
        workflow.add_edge("search_products", "generate_response")
        workflow.add_edge("generate_response", "update_profile")
        workflow.add_edge("update_profile", "log_interaction")
        workflow.add_edge("log_interaction", END)

        return workflow.compile()

    async def process(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process consultation request using LangGraph workflow

        Args:
            user_id: User identifier
            message: User message/query
            conversation_history: Optional previous conversation messages

        Returns:
            Dict with recommendations, questions, and extracted preferences
        """
        try:
            self.logger.info(
                f"Processing consultation for user {user_id}: {message[:50]}...")

            # Initialize state
            initial_state: ConsultantState = {
                "user_id": user_id,
                "message": message,
                "conversation_history": conversation_history,
                "user_profile": None,
                "extracted_preferences": {},
                "products": [],
                "response": "",
                "recommendations": [],
                "error": None,
                "step": "start"
            }

            # Run graph
            final_state = await self.graph.ainvoke(initial_state)

            # Return result
            if final_state.get("error"):
                return {
                    "response": "Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.",
                    "recommendations": [],
                    "extracted_preferences": {},
                    "error": final_state["error"]
                }

            return {
                "response": final_state["response"],
                "recommendations": final_state["products"][:5],
                "extracted_preferences": final_state["extracted_preferences"],
                "has_profile": final_state["user_profile"] is not None,
                "user_id": user_id
            }

        except Exception as e:
            self.logger.error(
                f"Error processing consultation for user {user_id}: {e}", exc_info=True)
            return {
                "response": "Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.",
                "recommendations": [],
                "extracted_preferences": {},
                "error": str(e)
            }

    async def _load_profile_node(self, state: ConsultantState) -> ConsultantState:
        """Node: Load customer profile from database"""
        try:
            profile = await self._get_customer_profile(state["user_id"])
            state["user_profile"] = profile
            state["step"] = "profile_loaded"
        except Exception as e:
            logger.error(f"Error loading profile: {e}", exc_info=True)
            state["error"] = str(e)
        return state

    async def _extract_preferences_node(self, state: ConsultantState) -> ConsultantState:
        """Node: Extract preferences from user message"""
        try:
            extracted_prefs = await self._extract_preferences_from_message(state["message"])
            state["extracted_preferences"] = extracted_prefs

            # Merge with existing profile
            if state["user_profile"]:
                merged_prefs = self._merge_preferences(
                    state["user_profile"], extracted_prefs)
                state["user_profile"] = merged_prefs
            else:
                state["user_profile"] = extracted_prefs

            state["step"] = "preferences_extracted"
        except Exception as e:
            logger.error(f"Error extracting preferences: {e}", exc_info=True)
            state["error"] = str(e)
        return state

    async def _search_products_node(self, state: ConsultantState) -> ConsultantState:
        """Node: Search products via RAG"""
        try:
            products = []
            if self.rag_retriever and state["user_profile"]:
                rag_result = await self.rag_retriever.retrieve_relevant_products(
                    query=state["message"],
                    user_preferences=state["user_profile"],
                    limit=8,
                    include_context=False
                )
                products = rag_result.get("products", [])
            state["products"] = products
            state["step"] = "products_searched"
        except Exception as e:
            logger.error(f"Error searching products: {e}", exc_info=True)
            state["error"] = str(e)
        return state

    async def _generate_response_node(self, state: ConsultantState) -> ConsultantState:
        """Node: Generate consultation response via LLM"""
        try:
            response = await self._generate_consultation_response(
                message=state["message"],
                user_profile=state["user_profile"],
                products=state["products"],
                conversation_history=state["conversation_history"]
            )
            state["response"] = response
            state["recommendations"] = self._extract_product_ids(
                state["products"][:5])
            state["step"] = "response_generated"
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            state["error"] = str(e)
        return state

    async def _update_profile_node(self, state: ConsultantState) -> ConsultantState:
        """Node: Update customer preferences in database"""
        try:
            if state["extracted_preferences"] and any(state["extracted_preferences"].values()):
                is_new = state["user_profile"] is None or not state["user_profile"]
                await self._update_customer_preferences(
                    state["user_id"],
                    state["extracted_preferences"],
                    is_new
                )
            state["step"] = "profile_updated"
        except Exception as e:
            logger.error(f"Error updating profile: {e}", exc_info=True)
            # Don't fail the whole process if profile update fails
        return state

    async def _log_interaction_node(self, state: ConsultantState) -> ConsultantState:
        """Node: Log interaction to database"""
        try:
            await self.log_interaction(
                user_id=state["user_id"],
                agent_type="consultant",
                input_msg=state["message"],
                output_msg=state["response"],
                recommendations=state["recommendations"],
                preference_updates=state["extracted_preferences"]
            )
            state["step"] = "interaction_logged"
        except Exception as e:
            logger.error(f"Error logging interaction: {e}", exc_info=True)
            # Don't fail the whole process if logging fails
        return state

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
                    "budget_min": cast(Optional[float], preference.budget_min),
                    "budget_max": cast(Optional[float], preference.budget_max),
                    "preferred_materials": preference.preferred_materials or [],
                    "skin_tone": preference.skin_tone,
                    "occasion_types": preference.occasion_types or [],
                }
        except Exception as e:
            self.logger.error(
                f"Error getting customer profile {user_id}: {e}", exc_info=True)
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
                response_clean = response_clean.split(
                    "```json")[1].split("```")[0].strip()
            elif response_clean.startswith("```"):
                response_clean = response_clean.split(
                    "```")[1].split("```")[0].strip()

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
                    new_list = set(value if isinstance(
                        value, list) else [value])
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
                    "last_updated": datetime.now()
                }

                if is_new:
                    pref_data["created_at"] = datetime.now()
                    pref_data["consultation_history"] = []
                    await repo.create(pref_data)
                else:
                    await repo.update(user_id, pref_data)

                await session.commit()
                self.logger.info(f"Updated preferences for user {user_id}")
                return True

        except Exception as e:
            self.logger.error(
                f"Error updating preferences for user {user_id}: {e}", exc_info=True)
            return False
