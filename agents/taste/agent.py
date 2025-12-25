"""Jewelry preference detection agent using LangGraph."""

import logging
import json
from typing import Dict, Any, Optional, List

from langgraph.graph import StateGraph, END
from llm.base import LLMProvider

from .utils.state import JewelryState
from .utils.tools import get_next_jewelry_question, analyze_jewelry_profile, JEWELRY_QUESTIONS

logger = logging.getLogger(__name__)


class TasteAgent:
    """Agent for detecting user jewelry preferences through conversation.

    Asks structured questions about metal, stones, style, occasions, and budget,
    then analyzes responses to create a jewelry preference profile with recommendations.
    """

    DEFAULT_SYSTEM_PROMPT = """Ты — консультант по ювелирным украшениям и специалист по определению вкуса.

Твоя манера общения:
- Дружелюбна и открыта
- Задаёшь чёткие вопросы о предпочтениях в украшениях
- Слушаешь ответы внимательно и запоминаешь их
- После всех вопросов анализируешь ответы и составляешь профиль предпочтений
- Объясняешь результаты с учётом модных тенденций и индивидуальности

Правила:
- Задавай вопросы по одному
- После каждого ответа благодари пользователя и переходи к следующему вопросу
- Когда все вопросы заданы, анализируй ответы и дай рекомендации по украшениям
- Будь гибкой в интерпретации ответов (не требуй точных формулировок)
- Если ответ неполный, переформулируй вопрос или попроси уточнение
- Используй знания о тенденциях в ювелирной индустрии
"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        language: str = "auto",
        custom_system_prompt: Optional[str] = None
    ):
        """Initialize jewelry preference detection agent.

        Args:
            llm_provider: LLM provider for text generation
            language: Communication language (en, ru, auto)
            custom_system_prompt: Optional custom system prompt
        """
        self.llm_provider = llm_provider
        self.language = language
        self.custom_system_prompt = custom_system_prompt
        self.logger = logging.getLogger(self.__class__.__name__)

        # Build the graph
        self.graph = self._build_graph()
        logger.info("Jewelry preference detection agent initialized")

    def _get_system_prompt(self) -> str:
        """Get system prompt with language instruction.

        Returns:
            Complete system prompt
        """
        base_prompt = self.custom_system_prompt or self.DEFAULT_SYSTEM_PROMPT

        language_instructions = {
            "en": "Respond in English.",
            "ru": "Отвечай на русском языке.",
            "auto": "Respond in the same language as the user's message."
        }

        language_instruction = language_instructions.get(
            self.language, language_instructions["auto"])
        return f"{base_prompt}\
\
Language Instruction: {language_instruction}"

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow.

        Returns:
            Compiled state graph
        """
        workflow = StateGraph(JewelryState)
        workflow.add_node("detect_jewelry", self._jewelry_node)

        # Set entry point
        workflow.set_entry_point("detect_jewelry")
        workflow.add_edge("detect_jewelry", END)

        # Compile graph
        graph = workflow.compile()
        logger.info("Jewelry preference detection agent graph compiled")

        return graph

    async def _jewelry_node(self, state: JewelryState) -> Dict[str, Any]:
        """Main node for jewelry preference detection conversation."""

        user_text = state.get("message") or ""
        conversation_history = state.get("conversation_history") or []
        current_index = state.get("current_question_index") or 0
        answers = state.get("answers") or {}

        system = self._get_system_prompt()

        # Build conversation context
        history_lines: List[str] = []
        for msg in conversation_history:
            role = msg.get("role")
            content = msg.get("content", "")
            if not content:
                continue

            if role == "user":
                history_lines.append(f"Пользователь: {content}")
            elif role == "assistant":
                history_lines.append(f"Консультант: {content}")

        # Build context for LLM
        context: Dict[str, Any] = {
            "current_question_index": current_index,
            "answers_count": len(answers),
            "total_questions": len(JEWELRY_QUESTIONS),
        }

        # Tool schemas
        tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "get_next_jewelry_question",
                    "description": "Получить следующий вопрос о предпочтениях в ювелирных украшениях",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "current_index": {
                                "type": "integer",
                                "description": "Индекс текущего вопроса (начиная с 0)",
                            },
                        },
                        "required": ["current_index"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_jewelry_profile",
                    "description": "Проанализировать все ответы пользователя и составить профиль его предпочтений в украшениях",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "answers": {
                                "type": "object",
                                "description": "Словарь с ответами (question_id -> answer_text)",
                            },
                        },
                        "required": ["answers"],
                    },
                },
            },
        ]

        # Build prompt
        prompt_parts = [system]

        if history_lines:
            prompt_parts.append("История беседы:\
" + "\
".join(history_lines))

        prompt_parts.append(
            f"Текущий прогресс: {current_index}/{len(JEWELRY_QUESTIONS)} вопросов задано"
        )

        if answers:
            answers_text = "\
".join([f"  {qid}: {answer}" for qid, answer in answers.items()])
            prompt_parts.append(f"Полученные ответы:\
{answers_text}")

        prompt_parts.append(f"Пользователь: {user_text}")

        # Instruction for when to ask next vs analyze
        if current_index < len(JEWELRY_QUESTIONS):
            prompt_parts.append(
                f"Следующий вопрос (#{current_index + 1}): {JEWELRY_QUESTIONS[current_index]['text']}\
"
                "Если пользователь уже ответил на этот вопрос, используй get_next_jewelry_question чтобы перейти к следующему."
            )
        else:
            prompt_parts.append(
                "Все вопросы заданы! Используй analyze_jewelry_profile чтобы проанализировать ответы и дать результат с рекомендациями."
            )

        prompt = "\
\
".join(prompt_parts)

        # Tool execution loop
        accumulated_tool_results: List[str] = []

        for iteration in range(5):  # Max 5 tool iterations
            result = await self.llm_provider.generate_with_tools(
                prompt=prompt,
                tools=tools_schema,
                context=context,
            )

            content = (result.get("content") or "").strip()
            tool_calls = result.get("tool_calls") or []

            if tool_calls:
                # Process tool calls
                for call in tool_calls:
                    fn = None
                    args = None

                    if isinstance(call, dict):
                        fn = call.get("function", {}).get(
                            "name") or call.get("name")
                        args = call.get("function", {}).get(
                            "arguments") or call.get("arguments")

                    # Parse arguments if string
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}

                    if not isinstance(args, dict):
                        args = {}

                    # Execute tool
                    if fn == "get_next_jewelry_question":
                        question_result = get_next_jewelry_question.invoke(
                            args)

                        if question_result.get("status") == "next_question":
                            q_id = question_result.get("question_id")
                            q_text = question_result.get("question_text")
                            q_index = question_result.get("index")

                            # Store the question info in state for next turn
                            state["current_question_index"] = q_index + 1

                            accumulated_tool_results.append(
                                f"next_question[{q_id}]: {q_text}"
                            )
                        else:
                            accumulated_tool_results.append(
                                "all_questions_complete")

                    elif fn == "analyze_jewelry_profile":
                        # Call analyze
                        jewelry_profile = await analyze_jewelry_profile.ainvoke(args)

                        state["jewelry_profile"] = jewelry_profile

                        # Format results for accumulation
                        profile_str = json.dumps(
                            jewelry_profile, ensure_ascii=False, indent=2)
                        accumulated_tool_results.append(f"jewelry_profile_analyzed:\
{profile_str}")

                    else:
                        accumulated_tool_results.append(f"unknown_tool: {fn}")

                # Prepare next prompt iteration with tool results
                prompt = (
                    prompt
                    + "\
\
Результаты инструментов:\
"
                    + "\
".join(accumulated_tool_results)
                    + "\
\
Теперь продолжи консультацию с пользователем на основе результатов."
                )

                continue

            # No tool calls => final assistant content
            if not content and accumulated_tool_results:
                content = "\
".join(accumulated_tool_results)

            # Store the current user answer if we're answering a question
            if current_index < len(JEWELRY_QUESTIONS) and user_text.strip():
                q_id = JEWELRY_QUESTIONS[current_index]["id"]
                state["answers"][q_id] = user_text

            return {
                "response": content,
                "current_question_index": state.get("current_question_index", current_index),
                "answers": state.get("answers", answers),
                "jewelry_profile": state.get("jewelry_profile"),
            }

        # Fallback if too many iterations
        return {
            "response": "Произошла ошибка при обработке. Пожалуйста, повтори ответ.",
            "current_question_index": current_index,
            "answers": answers,
            "jewelry_profile": state.get("jewelry_profile"),
        }

    async def process(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        current_question_index: Optional[int] = None,
        answers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Process user message.

        Args:
            user_id: User identifier
            message: User message
            conversation_history: Optional conversation history
            current_question_index: Current question index
            answers: Dictionary of answers so far

        Returns:
            Dict with response and conversation state
        """
        try:
            self.logger.info(
                f"Processing message for user {user_id}: {message[:50]}...")

            # Initialize state
            initial_state: JewelryState = {
                "user_id": user_id,
                "message": message,
                "conversation_history": conversation_history or [],
                "current_question_index": current_question_index or 0,
                "answers": answers or {},
            }

            # Run graph
            final_state = await self.graph.ainvoke(initial_state)

            response_text = (final_state.get("response") or "").strip()

            return {
                "status": "success",
                "response": response_text,
                "user_id": user_id,
                "current_question_index": final_state.get("current_question_index", 0),
                "answers": final_state.get("answers", {}),
                "jewelry_profile": final_state.get("jewelry_profile"),
            }

        except Exception as e:
            self.logger.error(
                f"Error processing message for user {user_id}: {e}", exc_info=True)

            return {
                "status": "error",
                "response": "Ой, что-то пошло не так. Давай попробуем ещё раз?",
                "error": str(e),
                "user_id": user_id,
            }
