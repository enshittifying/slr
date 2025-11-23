"""
LLM Interface for R1 Validation
Adapted from R2 pipeline with SLRinator-specific configuration
"""
import json
import time
from openai import OpenAI
from typing import Dict, Any, Optional
import logging
import sys
from pathlib import Path

# Add SLRinator config to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.validation_settings import (
    OPENAI_API_KEY, GPT_MODEL, GPT_TEMPERATURE, GPT_MAX_TOKENS,
    VECTOR_STORE_CACHE
)

logger = logging.getLogger(__name__)

class LLMInterface:
    """LLM interface for R1 cite checking validation."""

    # Class-level cooldown management
    _last_failure_time = None
    _failure_cooldown_seconds = 5
    _stagger_until = None
    _stagger_delay = 15
    _last_staggered_call = None

    # Throttling
    _initial_post_delay = 10
    _polling_delay = 25
    _processing_call_delay = 15

    def __init__(self, api_key: str = OPENAI_API_KEY, use_vector_store: bool = True):
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.total_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0

        # Pricing
        if GPT_MODEL.startswith("gpt-4o"):
            self.input_cost_per_1k = 0.00015
            self.output_cost_per_1k = 0.0006
        elif GPT_MODEL.startswith("gpt-5"):
            self.input_cost_per_1k = 0.00005
            self.output_cost_per_1k = 0.0004
        else:
            self.input_cost_per_1k = 0.00015
            self.output_cost_per_1k = 0.0006

        # Vector store
        self.use_vector_store = use_vector_store
        self.assistant_id = None
        if use_vector_store:
            try:
                self.assistant_id = self._load_assistant_id()
                if self.assistant_id:
                    logger.info(f"Loaded Bluebook assistant: {self.assistant_id}")
                else:
                    logger.warning("No Bluebook assistant found")
            except Exception as e:
                logger.warning(f"Failed to load vector store: {e}")

    def _load_assistant_id(self) -> Optional[str]:
        """Load assistant ID from cache."""
        try:
            with open(VECTOR_STORE_CACHE, 'r') as f:
                cache = json.load(f)
                return cache.get('assistant_id')
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    @classmethod
    def _check_and_enforce_cooldown(cls):
        """Check cooldown and staggering."""
        current_time = time.time()

        if cls._last_failure_time is not None:
            elapsed = current_time - cls._last_failure_time
            if elapsed < cls._failure_cooldown_seconds:
                wait_time = cls._failure_cooldown_seconds - elapsed
                logger.info(f"API cooldown: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                current_time = time.time()

        if cls._stagger_until is not None and current_time < cls._stagger_until:
            if cls._last_staggered_call is not None:
                time_since_last = current_time - cls._last_staggered_call
                if time_since_last < cls._stagger_delay:
                    stagger_wait = cls._stagger_delay - time_since_last
                    logger.info(f"Stagger mode: waiting {stagger_wait:.1f}s")
                    time.sleep(stagger_wait)
            cls._last_staggered_call = time.time()

    @classmethod
    def _mark_api_failure(cls):
        """Mark API failure for cooldown."""
        cls._last_failure_time = time.time()
        cls._stagger_until = time.time() + 60
        logger.info("API failure marked - cooldown activated")

    def call_gpt(self,
                 system_prompt: str,
                 user_prompt: str,
                 response_format: str = "json",
                 max_retries: int = 3) -> Dict[str, Any]:
        """Make a GPT API call with retry logic."""
        self._check_and_enforce_cooldown()

        if not self.client:
            logger.error("OpenAI client not initialized")
            return {
                "success": False,
                "data": None,
                "error": "OpenAI API key not configured",
                "tokens": 0,
                "cost": 0
            }

        for attempt in range(max_retries):
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]

                kwargs = {
                    "model": GPT_MODEL,
                    "messages": messages,
                    "max_tokens": GPT_MAX_TOKENS,
                    "temperature": GPT_TEMPERATURE,
                }
                if response_format == "json":
                    kwargs["response_format"] = {"type": "json_object"}

                response = self.client.chat.completions.create(**kwargs)

                content = response.choices[0].message.content or ""
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

                cost = (input_tokens * self.input_cost_per_1k / 1000 +
                       output_tokens * self.output_cost_per_1k / 1000)

                self.total_tokens += input_tokens + output_tokens
                self.total_cost += cost
                self.call_count += 1

                # Parse JSON
                if response_format == "json":
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError:
                        if "```json" in content:
                            content = content.split("```json")[1].split("```")[0].strip()
                        elif "```" in content:
                            content = content.split("```")[1].split("```")[0].strip()
                        data = json.loads(content)
                else:
                    data = content

                logger.info(f"GPT call successful. Tokens: {input_tokens + output_tokens}, Cost: ${cost:.4f}")

                return {
                    "success": True,
                    "data": data,
                    "error": None,
                    "tokens": input_tokens + output_tokens,
                    "cost": cost
                }

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error on attempt {attempt + 1}: {e}")
                self._mark_api_failure()
                if attempt == max_retries - 1:
                    return {"success": False, "data": None, "error": f"JSON decode failed: {str(e)}", "tokens": 0, "cost": 0}
                time.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                self._mark_api_failure()
                if attempt == max_retries - 1:
                    return {"success": False, "data": None, "error": str(e), "tokens": 0, "cost": 0}
                time.sleep(2 ** attempt)

    def call_assistant_with_search(self,
                                   query: str,
                                   max_wait_time: int = 120,
                                   response_format: str = "json",
                                   max_retries: int = 8) -> Dict[str, Any]:
        """Use Bluebook assistant with File Search."""
        self._check_and_enforce_cooldown()

        if not self.client:
            return {"success": False, "data": None, "error": "API key not configured", "tokens": 0, "cost": 0}

        if not self.assistant_id:
            logger.warning("No assistant available, falling back to regular GPT")
            return self.call_gpt(
                system_prompt="You are an expert in Bluebook legal citation rules.",
                user_prompt=query,
                response_format=response_format
            )

        for attempt in range(max_retries):
            try:
                thread = self.client.beta.threads.create()
                logger.info(f"Created thread: {thread.id}")
                time.sleep(self._initial_post_delay)

                query_with_format = f"{query}\n\nIMPORTANT: Respond ONLY with valid JSON." if response_format == "json" else query

                message = self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=query_with_format
                )
                time.sleep(self._initial_post_delay)

                run = self.client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=self.assistant_id
                )
                logger.info(f"Started run: {run.id}")

                start_time = time.time()
                poll_count = 0
                while time.time() - start_time < max_wait_time:
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )

                    if run.status == 'completed':
                        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                        assistant_message = messages.data[0]
                        content = assistant_message.content[0].text.value

                        estimated_tokens = len(query.split()) * 1.3 + len(content.split()) * 1.3
                        estimated_cost = (estimated_tokens * self.input_cost_per_1k / 1000)

                        self.total_tokens += int(estimated_tokens)
                        self.total_cost += estimated_cost
                        self.call_count += 1

                        if response_format == "json":
                            content_clean = content.strip()
                            if content_clean.startswith("```json"):
                                content_clean = content_clean[7:]
                            if content_clean.startswith("```"):
                                content_clean = content_clean[3:]
                            if content_clean.endswith("```"):
                                content_clean = content_clean[:-3]
                            content_clean = content_clean.strip()
                            data = json.loads(content_clean)
                        else:
                            data = content

                        logger.info(f"Assistant call successful. Tokens: {int(estimated_tokens)}, Cost: ${estimated_cost:.4f}")

                        return {
                            "success": True,
                            "data": data,
                            "error": None,
                            "tokens": int(estimated_tokens),
                            "cost": estimated_cost
                        }

                    elif run.status in ['failed', 'cancelled', 'expired']:
                        logger.warning(f"Run {run.status} on attempt {attempt + 1}")
                        self._mark_api_failure()
                        break

                    poll_count += 1
                    time.sleep(self._polling_delay)

                if attempt < max_retries - 1:
                    time.sleep(self._processing_call_delay)
                else:
                    self._mark_api_failure()
                    return {"success": False, "data": None, "error": f"Failed after {max_retries} attempts", "tokens": 0, "cost": 0}

            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}")
                self._mark_api_failure()
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return {"success": False, "data": None, "error": str(e), "tokens": 0, "cost": 0}

    def get_stats(self) -> Dict[str, Any]:
        """Return API usage statistics."""
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "avg_tokens_per_call": self.total_tokens / max(self.call_count, 1),
            "avg_cost_per_call": self.total_cost / max(self.call_count, 1)
        }
