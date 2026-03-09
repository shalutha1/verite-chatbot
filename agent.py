"""
agent.py — Verité Research Chatbot Agent (Groq / Llama 3.3)

Key fixes:
  - parallel_tool_calls=False to prevent malformed multi-tool calls
  - Robust handling of text-only, tool-only, and mixed responses
  - Explicit JSON tool call format enforced
"""

import json
import logging
from dataclasses import dataclass, field

from groq import Groq

import config
from memory import MemoryManager
from prompts import SYSTEM_PROMPT
from vector_store import VectorStore

logger = logging.getLogger("verite.agent")

# ── Tool definition ────────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": (
                "Search the Verite Research knowledge base. "
                "Call ONLY for questions about Verite's published research. "
                "Do NOT call for greetings, small talk, or follow-up questions "
                "that are already answered in the conversation history."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Key search terms from the user's question. Keep it short.",
                    }
                },
                "required": ["query"],
            },
        },
    }
]


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class Source:
    source:    str
    page:      int
    text:      str
    rrf_score: float = 0.0

    @property
    def display_name(self) -> str:
        return f"{self.source}, p.{self.page}"


@dataclass
class AgentResponse:
    text:          str
    sources:       list[Source] = field(default_factory=list)
    search_query:  str | None   = None
    tool_was_used: bool         = False


# ── Agent ─────────────────────────────────────────────────────────────────────

class VeriteAgent:

    def __init__(self):
        self.client       = Groq(api_key=config.GROQ_API_KEY)
        self.vector_store = VectorStore()
        self.memory       = MemoryManager()

    # ── Public API ────────────────────────────────────────────────────────────

    def start_session(self) -> tuple[str, list[dict]]:
        session_id    = self.memory.new_session()
        prior_history = self.memory.get_long_term_context(session_id)
        return session_id, prior_history

    def chat(
        self,
        user_message:         str,
        session_id:           str,
        conversation_history: list[dict],
    ) -> tuple[AgentResponse, list[dict]]:

        conversation_history = [
            *conversation_history,
            {"role": "user", "content": user_message},
        ]

        trimmed = self._trim_history(conversation_history)

        response_text, sources, search_query = self._agentic_loop(trimmed)

        conversation_history.append(
            {"role": "assistant", "content": response_text}
        )

        self.memory.save_message(session_id, "user",      user_message)
        self.memory.save_message(session_id, "assistant", response_text)

        return AgentResponse(
            text          = response_text,
            sources       = sources,
            search_query  = search_query,
            tool_was_used = bool(sources),
        ), conversation_history

    # ── Agentic loop ──────────────────────────────────────────────────────────

    def _agentic_loop(
        self,
        history: list[dict],
    ) -> tuple[str, list[Source], str | None]:

        sources:      list[Source] = []
        search_query: str | None   = None

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self._to_groq_history(history),
        ]

        # Safety limit — max 3 tool call rounds
        for _ in range(3):
            response = self.client.chat.completions.create(
                model                = config.GROQ_MODEL,
                messages             = messages,
                tools                = TOOLS,
                tool_choice          = "auto",
                parallel_tool_calls  = False,   # prevent malformed multi-calls
                max_tokens           = config.MAX_TOKENS,
            )

            msg        = response.choices[0].message
            stop_reason = response.choices[0].finish_reason

            logger.info(f"Groq finish_reason={stop_reason}")

            # ── No tool call → return text ────────────────────────────────
            if not msg.tool_calls:
                return (msg.content or "").strip(), sources, search_query

            # ── Tool call → execute and loop ──────────────────────────────
            # Append assistant message
            messages.append({
                "role":       "assistant",
                "content":    msg.content or "",
                "tool_calls": [
                    {
                        "id":       tc.id,
                        "type":     "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            # Execute each tool call
            for tc in msg.tool_calls:
                if tc.function.name == "search_documents":
                    try:
                        args  = json.loads(tc.function.arguments)
                        query = args.get("query", "")
                    except (json.JSONDecodeError, KeyError):
                        query = ""

                    if not query:
                        result_text = "No query provided."
                    else:
                        search_query = query
                        raw_results  = self.vector_store.hybrid_search(query)
                        sources      = [
                            Source(
                                source    = r["source"],
                                page      = r["page"],
                                text      = r["text"],
                                rrf_score = r.get("rrf_score", 0.0),
                            )
                            for r in raw_results
                        ]
                        result_text = self._format_search_results(sources)
                        logger.info(f"Tool: search_documents('{query}') -> {len(sources)} results")

                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tc.id,
                        "content":      result_text,
                    })

        # Fallback if loop exhausted
        return "I'm sorry, I had trouble processing that request. Please try again.", sources, search_query

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _to_groq_history(self, history: list[dict]) -> list[dict]:
        result = []
        for msg in history:
            role = "assistant" if msg["role"] == "assistant" else "user"
            result.append({"role": role, "content": msg["content"]})
        return result

    def _format_search_results(self, sources: list[Source]) -> str:
        parts = []
        for i, s in enumerate(sources, start=1):
            parts.append(
                f"[Result {i}]\n"
                f"Source: {s.source}\n"
                f"Page: {s.page}\n"
                f"Content:\n{s.text}"
            )
        return "\n\n".join(parts)

    def _trim_history(self, history: list[dict]) -> list[dict]:
        max_items = config.MAX_HISTORY_TURNS * 2
        if len(history) <= max_items:
            return history
        return history[-max_items:]

    def is_ready(self) -> bool:
        try:
            return self.vector_store.is_ready()
        except Exception:
            return False
