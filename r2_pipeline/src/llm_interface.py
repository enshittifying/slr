"""
Interface for GPT-5-nano API calls with rate limiting and error handling.
GPT-5-nano: Ultra-fast, 3x cheaper than gpt-4o-mini, 272K token context window.
"""
import json
import time
from openai import OpenAI
from typing import Dict, Any, Optional
import logging
from config.settings import OPENAI_API_KEY, GPT_MODEL, GPT_TEMPERATURE, GPT_MAX_TOKENS, VECTOR_STORE_CACHE
from src.vector_store_manager import VectorStoreManager

logger = logging.getLogger(__name__)

class LLMInterface:
    # Class-level variables to track last API failure time (shared across all instances)
    _last_failure_time = None
    _failure_cooldown_seconds = 5  # Wait 5 seconds after any API failure
    _stagger_until = None  # Stagger requests until this timestamp
    _stagger_delay = 15  # General stagger delay between processing calls
    _last_staggered_call = None  # Track last staggered call time

    # Throttling configuration
    _initial_post_delay = 10   # Delay between initial POSTs (thread/message/run)
    _polling_delay = 25        # Fixed delay between polling status checks
    _processing_call_delay = 15  # Delay between processing retries

    def __init__(self, api_key: str = OPENAI_API_KEY, use_vector_store: bool = True):
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.total_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0

        # Pricing per 1k tokens (approx; adjust by model family)
        if GPT_MODEL.startswith("gpt-4o"):
            # GPT-4o-mini pricing
            self.input_cost_per_1k = 0.00015   # $0.15 per 1M
            self.output_cost_per_1k = 0.0006   # $0.60 per 1M
        elif GPT_MODEL.startswith("gpt-5"):
            # GPT-5-nano pricing (as of Aug 2025)
            self.input_cost_per_1k = 0.00005   # $0.05 per 1M
            self.output_cost_per_1k = 0.0004   # $0.40 per 1M
        else:
            # Sensible defaults
            self.input_cost_per_1k = 0.00015
            self.output_cost_per_1k = 0.0006

        # Initialize vector store manager if enabled
        self.use_vector_store = use_vector_store
        self.assistant_id = None
        if use_vector_store:
            try:
                manager = VectorStoreManager(api_key=api_key, cache_file=VECTOR_STORE_CACHE)
                self.assistant_id = manager.get_assistant_id()
                if self.assistant_id:
                    logger.info(f"Loaded Bluebook assistant: {self.assistant_id}")
                else:
                    logger.warning("No Bluebook assistant found. Run setup_vector_store.py first.")
            except Exception as e:
                logger.warning(f"Failed to load vector store: {e}")

    @classmethod
    def _check_and_enforce_cooldown(cls):
        """Check if we need to wait after a recent API failure. Also enforce staggering during cooldown period."""
        current_time = time.time()

        # First, check global cooldown
        if cls._last_failure_time is not None:
            elapsed = current_time - cls._last_failure_time
            if elapsed < cls._failure_cooldown_seconds:
                wait_time = cls._failure_cooldown_seconds - elapsed
                logger.info(f"API cooldown: waiting {wait_time:.1f}s after recent failure")
                time.sleep(wait_time)
                current_time = time.time()  # Update after wait

        # Second, check if we're in stagger mode
        if cls._stagger_until is not None and current_time < cls._stagger_until:
            # We're in stagger mode - enforce delay between calls
            if cls._last_staggered_call is not None:
                time_since_last = current_time - cls._last_staggered_call
                if time_since_last < cls._stagger_delay:
                    stagger_wait = cls._stagger_delay - time_since_last
                    logger.info(f"Stagger mode: waiting {stagger_wait:.1f}s between API calls")
                    time.sleep(stagger_wait)

            # Update last staggered call time
            cls._last_staggered_call = time.time()

    @classmethod
    def _mark_api_failure(cls):
        """Mark that an API call has failed, triggering cooldown and stagger mode for subsequent calls."""
        cls._last_failure_time = time.time()
        # Enable stagger mode for next 60 seconds (stagger all requests during this period)
        cls._stagger_until = time.time() + 60
        logger.info(f"API failure marked - 5s cooldown + 60s stagger mode (5s between calls) activated")

    def call_gpt(self,
                 system_prompt: str,
                 user_prompt: str,
                 response_format: str = "json",
                 max_retries: int = 3,
                 enable_caching: bool = True,
                 fallback_model: Optional[str] = "gpt-4o-mini") -> Dict[str, Any]:
        """
        Make a GPT API call with retry logic and optional prompt caching.

        Args:
            system_prompt: System instructions (cached if enable_caching=True)
            user_prompt: User query (cached if enable_caching=True and contains rules)
            response_format: "json" or "text"
            max_retries: Number of retry attempts
            enable_caching: Enable prompt caching for 90% cost reduction on repeated content

        Returns:
            Dict with 'success', 'data', 'error', 'tokens', 'cost'
        """
        # Check if we need to wait due to recent API failure
        self._check_and_enforce_cooldown()

        if not self.client:
            logger.error("OpenAI client not initialized - missing API key")
            return {
                "success": False,
                "data": None,
                "error": "OpenAI API key not configured",
                "tokens": 0,
                "cost": 0
            }

        for attempt in range(max_retries):
            try:
                # Build prompts
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]

                # Call model using the appropriate API
                if GPT_MODEL.startswith("gpt-5"):
                    # Use Responses API for GPT-5 models
                    input_text = f"{system_prompt}\n\n---\n\n{user_prompt}"
                    resp_kwargs = {
                        "model": GPT_MODEL,
                        "input": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "input_text", "text": input_text}
                                ],
                            }
                        ],
                        # Intentionally omit temperature; defaults to 1 for GPT-5
                    }
                    # Token limit for Responses API
                    resp_kwargs["max_output_tokens"] = GPT_MAX_TOKENS

                    response = self.client.responses.create(**resp_kwargs)

                    # Extract response text
                    content = getattr(response, "output_text", "") or ""

                    # Usage accounting
                    usage = getattr(response, "usage", None)
                    input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
                    output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
                    cached_tokens = 0  # Not exposed the same way via Responses usage
                    uncached_input_tokens = input_tokens
                else:
                    # Use Chat Completions for non-GPT-5
                    kwargs = {
                        "model": GPT_MODEL,
                        "messages": messages,
                        "max_tokens": GPT_MAX_TOKENS,
                        "temperature": GPT_TEMPERATURE,
                    }
                    if response_format == "json":
                        kwargs["response_format"] = {"type": "json_object"}

                    response = self.client.chat.completions.create(**kwargs)

                    # Extract response
                    content = response.choices[0].message.content or ""

                    # Usage accounting
                    input_tokens = response.usage.prompt_tokens
                    output_tokens = response.usage.completion_tokens
                    cached_tokens = 0
                    if hasattr(response.usage, 'prompt_tokens_details') and response.usage.prompt_tokens_details:
                        cached_tokens = getattr(response.usage.prompt_tokens_details, 'cached_tokens', 0)
                    uncached_input_tokens = input_tokens - cached_tokens

                # Cost calculation:
                # - Uncached input: full price ($0.05/1M)
                # - Cached input: 90% discount (effectively $0.005/1M)
                # - Output: full price ($0.40/1M)
                cached_cost_per_1k = self.input_cost_per_1k * 0.1  # 90% discount
                cost = (uncached_input_tokens * self.input_cost_per_1k / 1000 +
                       cached_tokens * cached_cost_per_1k / 1000 +
                       output_tokens * self.output_cost_per_1k / 1000)

                if cached_tokens > 0:
                    logger.info(f"Cache hit! {cached_tokens:,} tokens cached (saved ~${cached_tokens * self.input_cost_per_1k * 0.9 / 1000:.4f})")

                # Update stats
                self.total_tokens += input_tokens + output_tokens
                self.total_cost += cost
                self.call_count += 1

                # If content is empty for GPT-5, raise to trigger retry (no cross-model fallback)
                if GPT_MODEL.startswith("gpt-5") and not content.strip():
                    raise ValueError("Empty content returned by GPT-5 response")

                # Parse JSON if requested
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
                logger.error(f"Response content (first 500 chars): {content[:500]}")
                self._mark_api_failure()
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "data": None,
                        "error": f"JSON decode failed: {str(e)}",
                        "tokens": 0,
                        "cost": 0
                    }
                time.sleep(2 ** attempt)  # Exponential backoff

            except Exception as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                self._mark_api_failure()
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "data": None,
                        "error": str(e),
                        "tokens": 0,
                        "cost": 0
                    }
                time.sleep(2 ** attempt)

    def call_assistant_with_search(self,
                                   query: str,
                                   max_wait_time: int = 120,
                                   response_format: str = "json",
                                   max_retries: int = 8) -> Dict[str, Any]:
        """
        Use the Bluebook assistant with File Search to answer a query.

        Args:
            query: The question to ask the assistant
            max_wait_time: Maximum time to wait for response in seconds
            response_format: "json" or "text"
            max_retries: Number of retry attempts for failed runs (default 8)
                        Backoff delays: 1s, 2s, 4s, 8s, 16s, 32s, 64s

        Returns:
            Dict with 'success', 'data', 'error', 'tokens', 'cost'
        """
        # Check if we need to wait due to recent API failure
        self._check_and_enforce_cooldown()

        if not self.client:
            logger.error("OpenAI client not initialized - missing API key")
            return {
                "success": False,
                "data": None,
                "error": "OpenAI API key not configured",
                "tokens": 0,
                "cost": 0
            }

        if not self.assistant_id:
            logger.warning("No assistant available, falling back to regular GPT call")
            # Fallback to regular call with a generic system prompt
            return self.call_gpt(
                system_prompt="You are an expert in Bluebook legal citation rules.",
                user_prompt=query,
                response_format=response_format
            )

        # Retry loop for failed runs
        for attempt in range(max_retries):
            try:
                # Create a thread
                thread = self.client.beta.threads.create()
                logger.info(f"Created thread: {thread.id} (attempt {attempt + 1}/{max_retries})")

                # Delay between initial processing POSTs to reduce burst traffic
                time.sleep(self._initial_post_delay)

                # Add the user message to the thread with JSON instruction if needed
                if response_format == "json":
                    query_with_format = f"{query}\n\nIMPORTANT: Respond ONLY with valid JSON. Do not include any text before or after the JSON."
                else:
                    query_with_format = query

                message = self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=query_with_format
                )
                logger.info(f"Added message to thread")

                # Delay before creating the run
                time.sleep(self._initial_post_delay)

                # Run the assistant
                run = self.client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=self.assistant_id
                )
                logger.info(f"Started run: {run.id}")

                # Wait for completion with conservative polling (reduce HTTP pings)
                start_time = time.time()
                poll_count = 0
                while time.time() - start_time < max_wait_time:
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )

                    if run.status == 'completed':
                        # Get the messages
                        messages = self.client.beta.threads.messages.list(
                            thread_id=thread.id
                        )

                        # Get the assistant's response (first message)
                        assistant_message = messages.data[0]
                        content = assistant_message.content[0].text.value

                        # Estimate tokens (rough estimate since we don't have exact usage from assistants API)
                        estimated_tokens = len(query.split()) * 1.3 + len(content.split()) * 1.3
                        estimated_cost = (estimated_tokens * self.input_cost_per_1k / 1000)

                        # Update stats
                        self.total_tokens += int(estimated_tokens)
                        self.total_cost += estimated_cost
                        self.call_count += 1

                        # Parse JSON if requested
                        if response_format == "json":
                            # Try to extract JSON from the response
                            # Sometimes the response might be wrapped in markdown code blocks
                            content_clean = content.strip()
                            if content_clean.startswith("```json"):
                                content_clean = content_clean[7:]  # Remove ```json
                            if content_clean.startswith("```"):
                                content_clean = content_clean[3:]  # Remove ```
                            if content_clean.endswith("```"):
                                content_clean = content_clean[:-3]  # Remove trailing ```
                            content_clean = content_clean.strip()

                            try:
                                data = json.loads(content_clean)
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON from assistant response. Content: {content[:200]}")
                                raise
                        else:
                            data = content

                        logger.info(f"Assistant call successful after {poll_count} polls. Estimated tokens: {int(estimated_tokens)}, Cost: ${estimated_cost:.4f}")

                        return {
                            "success": True,
                            "data": data,
                            "error": None,
                            "tokens": int(estimated_tokens),
                            "cost": estimated_cost
                        }

                    elif run.status in ['failed', 'cancelled', 'expired']:
                        error_msg = run.last_error if hasattr(run, 'last_error') else 'Unknown error'
                        logger.warning(f"Run {run.status} on attempt {attempt + 1}/{max_retries}: {error_msg}")
                        self._mark_api_failure()
                        # Break out of while loop to retry
                        break

                    # Fixed polling interval to reduce ping rate
                    # Previously: adaptive (1s, 2s, 3s, 5s, then 10s)
                    # Now: constant 25s between polls to significantly lower HTTP traffic
                    poll_count += 1
                    wait = self._polling_delay
                    
                    logger.debug(f"Status: {run.status}, polling again in {wait}s (poll #{poll_count})")
                    time.sleep(wait)

                # If we're here, either timed out or run failed - retry if attempts remain
                if attempt < max_retries - 1:
                    wait_time = self._processing_call_delay
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    self._mark_api_failure()
                    logger.error(f"All {max_retries} attempts failed")
                    return {
                        "success": False,
                        "data": None,
                        "error": f"Assistant call failed after {max_retries} attempts",
                        "tokens": 0,
                        "cost": 0
                    }

            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}/{max_retries}: {e}")
                self._mark_api_failure()
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return {
                        "success": False,
                        "data": None,
                        "error": str(e),
                        "tokens": 0,
                        "cost": 0
                    }

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about API usage."""
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "avg_tokens_per_call": self.total_tokens / max(self.call_count, 1),
            "avg_cost_per_call": self.total_cost / max(self.call_count, 1)
        }
