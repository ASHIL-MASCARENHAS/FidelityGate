"""fidelitygate/investigation/llm_adapter.py
Resilient, bounded LLM adapter supporting OpenAI-compatible chat completion APIs
with token limits, timeouts, single bounded repair attempt, quota tracking,
and truthful fallback reporting.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Type
import httpx
from pydantic import BaseModel

from ..config import settings
from .models import AgentMode

logger = logging.getLogger("fidelitygate.investigation.llm")


class LLMAdapter:
    """Manages LLM API communication with fail-safe deterministic fallback boundaries."""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        max_repair_attempts: int = 1,
    ):
        self.provider = provider or settings.LLM_PROVIDER
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.timeout_seconds = timeout_seconds or settings.LLM_TIMEOUT_SECONDS
        self.max_output_tokens = max_output_tokens or settings.LLM_MAX_OUTPUT_TOKENS
        self.max_repair_attempts = max_repair_attempts

        self.call_count = 0
        self.quota_exhausted = False
        self.last_failure_reason: Optional[str] = None

    def is_available(self) -> Tuple[bool, Optional[str]]:
        """Checks if the LLM provider is configured and available without exhausting quota."""
        if self.quota_exhausted:
            return False, "Provider quota or billing limit previously exhausted; retries disabled."
        if not self.api_key or not self.api_key.strip():
            return False, "LLM_API_KEY is not configured in environment; using deterministic fallback."
        return True, None

    def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel],
    ) -> Tuple[Optional[BaseModel], AgentMode, Optional[str]]:
        """Queries the LLM for a structured JSON response matching the given Pydantic schema.
        Returns:
            (parsed_model_or_none, agent_mode, failure_or_fallback_reason)
        """
        available, reason = self.is_available()
        if not available:
            self.last_failure_reason = reason
            return None, AgentMode.DETERMINISTIC_PLANNER, reason

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # First generation attempt
        raw_content, err = self._call_completion_api(messages)
        if err:
            self.last_failure_reason = err
            if "429" in err or "quota" in err.lower():
                self.quota_exhausted = True
            return None, AgentMode.DETERMINISTIC_BASELINE, err

        # Attempt to parse
        parsed, parse_err = self._parse_json(raw_content, schema)
        if parsed:
            return parsed, AgentMode.LIVE_LLM_AGENT, None

        # Bounded repair attempt (at most 1)
        if self.max_repair_attempts > 0:
            logger.info("Attempting bounded single repair of malformed LLM JSON output...")
            repair_messages = list(messages)
            repair_messages.append({"role": "assistant", "content": raw_content})
            repair_messages.append({
                "role": "user",
                "content": f"The previous output failed validation: {parse_err}. "
                           f"Return ONLY valid JSON strictly matching the requested schema."
            })

            repaired_content, repair_err = self._call_completion_api(repair_messages)
            if not repair_err:
                repaired_model, second_parse_err = self._parse_json(repaired_content, schema)
                if repaired_model:
                    return repaired_model, AgentMode.LIVE_LLM_AGENT, None
                parse_err = f"Repair failed: {second_parse_err}"
            else:
                parse_err = f"Repair API call failed: {repair_err}"

        self.last_failure_reason = f"Structured output schema validation failure: {parse_err}"
        return None, AgentMode.DETERMINISTIC_BASELINE, self.last_failure_reason

    def _call_completion_api(self, messages: List[Dict[str, str]]) -> Tuple[Optional[str], Optional[str]]:
        """Makes an HTTP POST request to the completions endpoint."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_output_tokens,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        try:
            self.call_count += 1
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(url, headers=headers, json=payload)

            if resp.status_code == 200:
                body = resp.json()
                content = body["choices"][0]["message"]["content"]
                return content, None

            elif resp.status_code in [401, 403]:
                return None, f"Provider authentication failed (HTTP {resp.status_code}): Invalid credentials."

            elif resp.status_code in [429]:
                self.quota_exhausted = True
                return None, "Provider rate limit or quota exceeded (HTTP 429); subsequent retries disabled."

            else:
                return None, f"Provider returned HTTP {resp.status_code}: {resp.text[:120]}"

        except httpx.TimeoutException:
            return None, f"Provider request timed out after {self.timeout_seconds}s."
        except Exception as exc:
            # Sanitize error to avoid leaking keys or internal paths
            clean_err = str(exc).replace(self.api_key or "", "[REDACTED_API_KEY]")
            return None, f"Provider communication failure: {clean_err}"

    def _parse_json(self, raw_str: str, schema: Type[BaseModel]) -> Tuple[Optional[BaseModel], Optional[str]]:
        if not raw_str or not raw_str.strip():
            return None, "Empty response from provider"
        try:
            cleaned = raw_str.strip()
            # Strip markdown fences if present
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed_data = json.loads(cleaned)
            model_instance = schema(**parsed_data)
            return model_instance, None
        except json.JSONDecodeError as jde:
            return None, f"JSON syntax error: {jde}"
        except Exception as exc:
            return None, f"Schema validation error: {exc}"
