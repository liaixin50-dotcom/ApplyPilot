"""
Unified LLM client for ApplyPilot.

Auto-detects provider from environment:
  GEMINI_API_KEY  -> Google Gemini (default: gemini-2.0-flash)
  OPENAI_API_KEY  -> OpenAI (default: gpt-4o-mini)
  LLM_URL         -> Local llama.cpp / Ollama compatible endpoint
  (none of above) -> Claude CLI (claude -p), if `claude` is on PATH

LLM_MODEL env var overrides the model name for any provider.
CLAUDE_CLI_MODEL env var overrides the model for Claude CLI (default: sonnet).
"""

import logging
import os
import re
import shutil
import subprocess
import time

import httpx

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------

def _detect_provider() -> tuple[str, str, str]:
    """Return (base_url, model, api_key) based on environment variables.

    Reads env at call time (not module import time) so that load_env() called
    in _bootstrap() is always visible here.

    Returns ("claude_cli", model, "") when no API keys are set but the
    `claude` CLI is on PATH — enables zero-config AI scoring for users
    who only have Claude Code installed.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    local_url = os.environ.get("LLM_URL", "")
    model_override = os.environ.get("LLM_MODEL", "")

    if gemini_key and not local_url:
        return (
            "https://generativelanguage.googleapis.com/v1beta/openai",
            model_override or "gemini-2.0-flash",
            gemini_key,
        )

    if openai_key and not local_url:
        return (
            "https://api.openai.com/v1",
            model_override or "gpt-4o-mini",
            openai_key,
        )

    if local_url:
        return (
            local_url.rstrip("/"),
            model_override or "local-model",
            os.environ.get("LLM_API_KEY", ""),
        )

    # ── Zero-config fallback: Claude CLI ────────────────────────────────
    if shutil.which("claude"):
        claude_model = os.environ.get("CLAUDE_CLI_MODEL", "sonnet")
        return ("claude_cli", claude_model, "")

    raise RuntimeError(
        "No LLM provider configured. "
        "Set GEMINI_API_KEY, OPENAI_API_KEY, LLM_URL, or install Claude Code CLI."
    )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

_MAX_RETRIES = 5
_TIMEOUT = 120  # seconds

# Base wait on first 429/503 (doubles each retry, caps at 60s).
# Gemini free tier is 15 RPM = 4s minimum between requests; 10s gives headroom.
_RATE_LIMIT_BASE_WAIT = 10


_GEMINI_COMPAT_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
_GEMINI_NATIVE_BASE = "https://generativelanguage.googleapis.com/v1beta"


class LLMClient:
    """Thin LLM client supporting OpenAI-compatible and native Gemini endpoints.

    For Gemini keys, starts on the OpenAI-compat layer. On a 403 (which
    happens with preview/experimental models not exposed via compat), it
    automatically switches to the native generateContent API and stays there
    for the lifetime of the process.
    """

    def __init__(self, base_url: str, model: str, api_key: str) -> None:
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self._client = httpx.Client(timeout=_TIMEOUT)
        # True once we've confirmed the native Gemini API works for this model
        self._use_native_gemini: bool = False
        self._is_gemini: bool = base_url.startswith(_GEMINI_COMPAT_BASE)

    # -- Native Gemini API --------------------------------------------------

    def _chat_native_gemini(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the native Gemini generateContent API.

        Used automatically when the OpenAI-compat endpoint returns 403,
        which happens for preview/experimental models not exposed via compat.

        Converts OpenAI-style messages to Gemini's contents/systemInstruction
        format transparently.
        """
        contents: list[dict] = []
        system_parts: list[dict] = []

        for msg in messages:
            role = msg["role"]
            text = msg.get("content", "")
            if role == "system":
                system_parts.append({"text": text})
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": text}]})
            elif role == "assistant":
                # Gemini uses "model" instead of "assistant"
                contents.append({"role": "model", "parts": [{"text": text}]})

        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}

        url = f"{_GEMINI_NATIVE_BASE}/models/{self.model}:generateContent"
        resp = self._client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            params={"key": self.api_key},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    # -- OpenAI-compat API --------------------------------------------------

    def _chat_compat(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the OpenAI-compatible endpoint."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        resp = self._client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
        )

        # 403 on Gemini compat = model not available on compat layer.
        # Raise a specific sentinel so chat() can switch to native API.
        if resp.status_code == 403 and self._is_gemini:
            raise _GeminiCompatForbidden(resp)

        return self._handle_compat_response(resp)

    @staticmethod
    def _handle_compat_response(resp: httpx.Response) -> str:
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    # -- public API ---------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request and return the assistant message text."""
        # Qwen3 optimization: prepend /no_think to skip chain-of-thought
        # reasoning, saving tokens on structured extraction tasks.
        if "qwen" in self.model.lower() and messages:
            first = messages[0]
            if first.get("role") == "user" and not first["content"].startswith("/no_think"):
                messages = [{"role": first["role"], "content": f"/no_think\n{first['content']}"}] + messages[1:]

        for attempt in range(_MAX_RETRIES):
            try:
                # Route to native Gemini if we've already confirmed it's needed
                if self._use_native_gemini:
                    return self._chat_native_gemini(messages, temperature, max_tokens)

                return self._chat_compat(messages, temperature, max_tokens)

            except _GeminiCompatForbidden as exc:
                # Model not available on OpenAI-compat layer — switch to native.
                log.warning(
                    "Gemini compat endpoint returned 403 for model '%s'. "
                    "Switching to native generateContent API. "
                    "(Preview/experimental models are often compat-only on native.)",
                    self.model,
                )
                self._use_native_gemini = True
                # Retry immediately with native — don't count as a rate-limit wait
                try:
                    return self._chat_native_gemini(messages, temperature, max_tokens)
                except httpx.HTTPStatusError as native_exc:
                    raise RuntimeError(
                        f"Both Gemini endpoints failed. Compat: 403 Forbidden. "
                        f"Native: {native_exc.response.status_code} — "
                        f"{native_exc.response.text[:200]}"
                    ) from native_exc

            except httpx.HTTPStatusError as exc:
                resp = exc.response
                if resp.status_code in (429, 503) and attempt < _MAX_RETRIES - 1:
                    # Respect Retry-After header if provided (Gemini sends this).
                    retry_after = (
                        resp.headers.get("Retry-After")
                        or resp.headers.get("X-RateLimit-Reset-Requests")
                    )
                    if retry_after:
                        try:
                            wait = float(retry_after)
                        except (ValueError, TypeError):
                            wait = _RATE_LIMIT_BASE_WAIT * (2 ** attempt)
                    else:
                        wait = min(_RATE_LIMIT_BASE_WAIT * (2 ** attempt), 60)

                    log.warning(
                        "LLM rate limited (HTTP %s). Waiting %ds before retry %d/%d. "
                        "Tip: Gemini free tier = 15 RPM. Consider a paid account "
                        "or switching to a local model.",
                        resp.status_code, wait, attempt + 1, _MAX_RETRIES,
                    )
                    time.sleep(wait)
                    continue
                raise

            except httpx.TimeoutException:
                if attempt < _MAX_RETRIES - 1:
                    wait = min(_RATE_LIMIT_BASE_WAIT * (2 ** attempt), 60)
                    log.warning(
                        "LLM request timed out, retrying in %ds (attempt %d/%d)",
                        wait, attempt + 1, _MAX_RETRIES,
                    )
                    time.sleep(wait)
                    continue
                raise

        raise RuntimeError("LLM request failed after all retries")

    def ask(self, prompt: str, **kwargs) -> str:
        """Convenience: single user prompt -> assistant response."""
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def close(self) -> None:
        self._client.close()


class _GeminiCompatForbidden(Exception):
    """Sentinel: Gemini OpenAI-compat returned 403. Switch to native API."""
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        super().__init__(f"Gemini compat 403: {response.text[:200]}")


# ---------------------------------------------------------------------------
# Claude CLI backend — zero-config fallback when no API keys are set
# ---------------------------------------------------------------------------

# Patterns to strip from `claude -p` output: thinking blocks, markdown fences,
# and any preamble the CLI might emit.
_CLAUDE_CLEANUP_PATTERNS: list[tuple[str, str]] = [
    # Thinking blocks (Claude Code may include these)
    (r"^​.*?​\s*", ""),
    # Markdown code fences around the whole response
    (r"^```(?:text|json)?\s*\n", ""),
    (r"\n```\s*$", ""),
]


def _clean_claude_output(text: str) -> str:
    """Strip thinking blocks and markdown artifacts from Claude CLI output."""
    for pattern, replacement in _CLAUDE_CLEANUP_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.DOTALL)
    return text.strip()


class ClaudeCLIBackend:
    """LLM backend that shells out to the local `claude` CLI (Claude Code).

    Zero-config fallback when no API keys are set. Each ``chat()`` call
    spawns a ``claude -p`` subprocess — suitable for low-volume scoring
    and tailoring.  Not recommended for high-throughput use (spawns a
    fresh process per request).

    Environment variables
    ---------------------
    CLAUDE_CLI_MODEL : str
        Model to pass to ``claude --model`` (default: ``"sonnet"``).
    """

    def __init__(self, model: str = "sonnet") -> None:
        self.model = model
        self._cli_path: str = shutil.which("claude") or "claude"

    # -- public API (mirrors LLMClient interface) -------------------------

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> str:
        """Send chat messages via ``claude -p`` and return the response text."""
        prompt = self._format_messages(messages)

        cmd = [
            self._cli_path,
            "-p", prompt,
            "--print",
            "--model", self.model,
            "--effort", "low",
            "--bare",
        ]

        log.debug("Claude CLI: %s", " ".join(cmd[:3]) + f" ... ({len(prompt)} chars)")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
                # Pass through current env so Claude finds its credentials;
                # force UTF-8 to avoid Windows GBK encoding issues.
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "Claude CLI timed out after 180s. "
                "Try a simpler prompt or a faster model (--model haiku)."
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"Claude CLI not found at '{self._cli_path}'. "
                "Install from https://claude.ai/code or set the full path."
            )

        if result.returncode != 0:
            stderr = result.stderr.strip()[:500]
            raise RuntimeError(
                f"Claude CLI exited with code {result.returncode}: {stderr}"
            )

        return _clean_claude_output(result.stdout)

    def ask(self, prompt: str, **kwargs) -> str:
        """Convenience: single user prompt -> assistant response."""
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def close(self) -> None:
        """No-op: no persistent connection to close."""

    # -- internals --------------------------------------------------------

    @staticmethod
    def _format_messages(messages: list[dict]) -> str:
        """Convert OpenAI-style messages into a single prompt for ``claude -p``.

        System messages are wrapped in XML-style tags to separate instructions
        from data.  User messages become the main prompt body.
        """
        parts: list[str] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(
                    f"<system-instructions>\n{content}\n</system-instructions>"
                )
            elif role == "user":
                parts.append(content)
            # assistant / tool roles are rare in ApplyPilot's current usage;
            # include them verbatim if they appear.
            else:
                parts.append(f"[{role}]\n{content}")

        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: LLMClient | ClaudeCLIBackend | None = None


def get_client() -> LLMClient | ClaudeCLIBackend:
    """Return (or create) the module-level LLM client singleton.

    Auto-detects the best available provider:
    1. Gemini / OpenAI / local LLM (via API keys)
    2. Claude CLI (zero-config fallback)
    """
    global _instance
    if _instance is None:
        base_url, model, api_key = _detect_provider()
        if base_url == "claude_cli":
            log.info("LLM provider: Claude CLI  model: %s", model)
            _instance = ClaudeCLIBackend(model)
        else:
            log.info("LLM provider: %s  model: %s", base_url, model)
            _instance = LLMClient(base_url, model, api_key)
    return _instance
