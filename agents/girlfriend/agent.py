"""Girlfriend agent implementation using LangGraph.

This project uses a custom `LLMProvider` interface (see `llm/base.py`) rather than
LangChain chat model objects. Therefore, tool routing is implemented via
`LLMProvider.generate_with_tools` instead of `bind_tools`.
"""

import logging
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END

from llm.base import LLMProvider
from .utils.state import GirlfriendState
from .utils.tools import get_horoscope, detect_zodiac_sign

logger = logging.getLogger(__name__)


class GirlfriendAgent:
    """Girlfriend agent for casual conversation and horoscopes.
    
    This agent provides friendly conversation support like chatting with
    a girlfriend who knows about horoscopes and various topics.
    """
    
    DEFAULT_SYSTEM_PROMPT = """Ты — тёплая, дружелюбная и поддерживающая собеседница, общаешься как близкая подруга.

Твоя манера общения:
- Эмпатично и бережно, без морализаторства
- Естественно и непринуждённо, без канцелярита
- Умеешь задавать уточняющие вопросы и запоминать детали
- Можешь говорить про отношения, повседневность, эмоции, планы, мечты
- Если пользователь просит гороскоп/астрологический совет — используй инструмент get_horoscope и не выдумывай текст
- Если пользователь пишет дату рождения или просит определить знак — используй detect_zodiac_sign

Правила:
- Отвечай кратко и по делу (обычно 2–6 предложений), но тепло
- Подстраивайся под тон пользователя
- Не используй откровенно сексуальный или токсичный стиль
- Не выдавай гороскоп «из головы» — только через инструмент
"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        language: str = "auto",
        custom_system_prompt: Optional[str] = None
    ):
        """Initialize girlfriend agent.
        
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
        
        logger.info("Girlfriend agent initialized")
    
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
        
        language_instruction = language_instructions.get(self.language, language_instructions["auto"])
        
        return f"{base_prompt}\n\nLanguage Instruction: {language_instruction}"
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow.
        
        Returns:
            Compiled state graph
        """
        # Create workflow
        workflow = StateGraph(GirlfriendState)

        workflow.add_node("girlfriend", self._girlfriend_node)
        
        # Set entry point
        workflow.set_entry_point("girlfriend")

        workflow.add_edge("girlfriend", END)
        
        # Compile graph
        graph = workflow.compile()
        
        logger.info("Girlfriend agent graph compiled")
        return graph

    async def _girlfriend_node(self, state: GirlfriendState) -> Dict[str, Any]:
        """Single node that generates reply and executes tools if requested."""

        user_text = state.get("message") or ""
        conversation_history = state.get("conversation_history") or []
        zodiac_sign = state.get("zodiac_sign")

        system = self._get_system_prompt()

        # Build a plain-text prompt that the custom provider understands
        history_lines: List[str] = []
        for msg in conversation_history:
            role = msg.get("role")
            content = msg.get("content", "")
            if not content:
                continue
            if role == "user":
                history_lines.append(f"Пользователь: {content}")
            elif role == "assistant":
                history_lines.append(f"Ассистент: {content}")

        context: Dict[str, Any] = {
            "zodiac_sign": zodiac_sign,
        }

        tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "get_horoscope",
                    "description": "Получить ежедневный гороскоп по знаку зодиака (eng token).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sign": {
                                "type": "string",
                                "description": "Знак зодиака: aries/taurus/gemini/cancer/leo/virgo/libra/scorpio/sagittarius/capricorn/aquarius/pisces",
                            },
                            "day": {
                                "type": "string",
                                "enum": ["today", "tomorrow", "yesterday"],
                                "description": "День (сейчас используем как метку; источник выдаёт ежедневный гороскоп).",
                            },
                        },
                        "required": ["sign"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_zodiac_sign",
                    "description": "Определить знак зодиака по дате рождения.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "birthdate": {
                                "type": "string",
                                "description": "Дата в формате 'MM/DD' или 'YYYY-MM-DD'",
                            }
                        },
                        "required": ["birthdate"],
                    },
                },
            },
        ]

        prompt_parts = [
            system,
            "Если нужно, вызывай инструменты (function calling).",
            "Если знак зодиака уже известен (zodiac_sign), используй его напрямую и не подменяй другим.",
        ]
        if history_lines:
            prompt_parts.append("История диалога:\n" + "\n".join(history_lines))
        if zodiac_sign:
            prompt_parts.append(f"Известный знак зодиака пользователя: {zodiac_sign}")
        prompt_parts.append(f"Пользователь: {user_text}")
        prompt = "\n\n".join(prompt_parts)

        # Loop tool calls until the model returns plain content
        accumulated_tool_results: List[str] = []
        for _ in range(3):
            result = await self.llm_provider.generate_with_tools(
                prompt=prompt,
                tools=tools_schema,
                context=context,
            )

            content = (result.get("content") or "").strip()
            tool_calls = result.get("tool_calls") or []

            if tool_calls:
                # OpenAI-style: list of tool calls; support a minimal subset
                for call in tool_calls:
                    fn = None
                    args = None
                    if isinstance(call, dict):
                        fn = call.get("function", {}).get("name") or call.get("name")
                        args = call.get("function", {}).get("arguments") or call.get("arguments")

                    # Arguments may come as dict or JSON string depending on provider
                    if isinstance(args, str):
                        import json

                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    if not isinstance(args, dict):
                        args = {}

                    if fn == "detect_zodiac_sign":
                        zodiac_sign = await detect_zodiac_sign.ainvoke(args)
                        state["zodiac_sign"] = zodiac_sign
                        accumulated_tool_results.append(f"detected_zodiac_sign: {zodiac_sign}")
                    elif fn == "get_horoscope":
                        horoscope_text = await get_horoscope.ainvoke(args)
                        accumulated_tool_results.append(f"horoscope: {horoscope_text}")
                    else:
                        accumulated_tool_results.append(f"unknown_tool: {fn}")

                # Feed tool results back into the prompt
                prompt = (
                    prompt
                    + "\n\nРезультаты инструментов:\n"
                    + "\n\n".join(accumulated_tool_results)
                    + "\n\nТеперь ответь пользователю, используя результаты, без выдумок, на русском языке."
                )
                continue

            # No tool calls => final assistant content
            if not content and accumulated_tool_results:
                content = "\n\n".join(accumulated_tool_results)

            state["response"] = content
            return state

        state["response"] = "Я не смогла корректно обработать запрос с инструментами. Попробуй переформулировать вопрос."
        return state
    
    async def process(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        zodiac_sign: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user message.
        
        Args:
            user_id: User identifier
            message: User message
            conversation_history: Optional conversation history
            zodiac_sign: Optional zodiac sign if known
        
        Returns:
            Dict with response and conversation state
        """
        try:
            self.logger.info(f"Processing message for user {user_id}: {message[:50]}...")
            
            # Initialize state (plain fields; no langchain message objects)
            initial_state: GirlfriendState = {
                "user_id": user_id,
                "message": message,
                "conversation_history": conversation_history or [],
                "zodiac_sign": zodiac_sign,
            }
            
            # Run graph
            final_state = await self.graph.ainvoke(initial_state)
            
            response_text = (final_state.get("response") or "").strip()
            
            return {
                "status": "success",
                "response": response_text,
                "user_id": user_id,
                "zodiac_sign": final_state.get("zodiac_sign"),
                "messages": None,
            }
        
        except Exception as e:
            self.logger.error(f"Error processing message for user {user_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "response": "Ой, у меня что-то пошло не так. Давай попробуем ещё раз?",
                "error": str(e),
                "user_id": user_id
            }
