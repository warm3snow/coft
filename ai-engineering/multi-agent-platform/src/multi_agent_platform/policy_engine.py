"""Policy Engine - synchronous, blocking, fail-closed safety guard.

Key design principles (from doc 2.4 section 3):
    1. MUST be synchronous (never async)
    2. MUST be blocking (fail-closed)
    3. Runs BEFORE every agent invocation

Checks:
    - Input length validation
    - Prompt injection detection (pattern-based)
    - Tenant permission enforcement
    - Output content filtering
"""

from __future__ import annotations

import re
import time
from typing import Optional

from .config import PolicyConfig
from .types import PolicyCheckResult, PolicyVerdict
from .observability import telemetry


# Known prompt injection patterns
_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts)", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|above|prior)", re.I),
    re.compile(r"you\s+are\s+now\s+(a|an|the)\s+", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>", re.I),
    re.compile(r"pretend\s+(you('re| are)|to be)\s+", re.I),
    re.compile(r"forget\s+(everything|all|your)\s+", re.I),
    re.compile(r"jailbreak|DAN\s*mode|developer\s+mode", re.I),
    # Chinese injection patterns
    re.compile(r"忘记.{0,5}(所有|全部|之前|以上).{0,5}(设定|指令|规则|提示)"),
    re.compile(r"忽略.{0,5}(所有|全部|之前|以上).{0,5}(指令|规则|提示|要求)"),
    re.compile(r"你现在是.{0,10}(黑客|骗子|恶意)"),
]

# Dangerous tool operation patterns
_DANGEROUS_OPERATIONS: list[re.Pattern] = [
    re.compile(r"rm\s+-rf\s+/", re.I),
    re.compile(r"sudo\s+", re.I),
    re.compile(r"DROP\s+TABLE|DELETE\s+FROM|TRUNCATE", re.I),
    re.compile(r"eval\s*\(|exec\s*\(|__import__", re.I),
    re.compile(r"os\.system|subprocess\.call|subprocess\.Popen", re.I),
]


class PolicyEngine:
    """Synchronous safety guard - checks every request before agent execution.

    This engine is intentionally synchronous and fail-closed:
    - If any check fails, the request is DENIED
    - If the engine itself errors, the request is DENIED (fail-closed)
    - Latency target: < 50ms per check
    """

    def __init__(self, config: Optional[PolicyConfig] = None) -> None:
        self.config = config or PolicyConfig()
        self._tenant_permissions: dict[str, set[str]] = {}  # tenant_id -> allowed tools

    def register_tenant(self, tenant_id: str, allowed_tools: set[str]) -> None:
        """Register a tenant with their allowed tool set."""
        self._tenant_permissions[tenant_id] = allowed_tools

    def check_input(self, text: str, tenant_id: str) -> PolicyCheckResult:
        """Check user input before processing. Synchronous, fail-closed."""
        start = time.time()

        try:
            if not self.config.enabled:
                return PolicyCheckResult(verdict=PolicyVerdict.ALLOW, reason="policy disabled")

            # 1. Length check
            if len(text) > self.config.max_input_length:
                telemetry.metrics.record_policy_denial()
                return PolicyCheckResult(
                    verdict=PolicyVerdict.DENY,
                    reason=f"input exceeds max length ({len(text)} > {self.config.max_input_length})",
                )

            # 2. Normalize text for evasion detection (Layer 2)
            texts_to_check = [text] + self._decode_evasions(text)

            # 3. Prompt injection detection (check all decoded variants)
            for check_text in texts_to_check:
                for pattern in _INJECTION_PATTERNS:
                    if pattern.search(check_text):
                        telemetry.metrics.record_policy_denial()
                        return PolicyCheckResult(
                            verdict=PolicyVerdict.DENY,
                            reason=f"potential prompt injection detected: {pattern.pattern[:50]}",
                        )

            # 4. Dangerous operation detection (check all decoded variants)
            for check_text in texts_to_check:
                for pattern in _DANGEROUS_OPERATIONS:
                    if pattern.search(check_text):
                        telemetry.metrics.record_policy_denial()
                        return PolicyCheckResult(
                            verdict=PolicyVerdict.DENY,
                            reason=f"dangerous operation detected: {pattern.pattern[:50]}",
                        )

            return PolicyCheckResult(verdict=PolicyVerdict.ALLOW, reason="all checks passed")

        except Exception as e:
            # Fail-closed: any error in policy check -> DENY
            telemetry.error("policy_engine.error", error=str(e))
            telemetry.metrics.record_policy_denial()
            return PolicyCheckResult(
                verdict=PolicyVerdict.DENY,
                reason=f"policy engine error (fail-closed): {str(e)}",
            )
        finally:
            duration_ms = (time.time() - start) * 1000
            if duration_ms > 50:
                telemetry.warn("policy_engine.slow", duration_ms=round(duration_ms, 2))

    @staticmethod
    def _decode_evasions(text: str) -> list[str]:
        """Decode common evasion techniques to catch obfuscated attacks.

        Layer 2 detection:
            - Base64 encoded content
            - Unicode fullwidth character normalization
            - Character-spaced text (i g n o r e → ignore)
            - Leetspeak normalization (1gn0re → ignore)
        """
        import base64
        import unicodedata

        decoded_variants: list[str] = []

        # 1. Base64 decoding: find base64-looking strings and decode them
        b64_pattern = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
        for match in b64_pattern.finditer(text):
            try:
                decoded = base64.b64decode(match.group()).decode("utf-8", errors="ignore")
                if decoded and len(decoded) > 5:
                    decoded_variants.append(decoded)
            except Exception:
                pass

        # 2. Unicode fullwidth normalization (ｉｇｎｏｒｅ → ignore)
        normalized = unicodedata.normalize("NFKC", text)
        if normalized != text:
            decoded_variants.append(normalized)

        # 3. Character-spaced text collapse (i g n o r e → ignore)
        # Detect: mostly single chars separated by spaces
        # 3. Character-spaced text collapse (i g n o r e → ignore)
        # Strategy: collapse single-char words into continuous text,
        # then re-insert spaces at double-space boundaries
        if re.search(r"(\w\s){4,}", text):
            # First collapse all single-char spacing
            collapsed = re.sub(r"(?<=\w)\s+(?=\w)", "", text)
            if collapsed != text:
                decoded_variants.append(collapsed)
            # Also try: collapse within word groups (double space = word boundary)
            words = re.split(r"\s{2,}", text)
            reconstructed = " ".join(re.sub(r"\s+", "", w) for w in words)
            if reconstructed != text and reconstructed != collapsed:
                decoded_variants.append(reconstructed)

        # 4. Leetspeak normalization
        leet_map = {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a"}
        if any(c in text for c in leet_map):
            deleet = text
            for k, v in leet_map.items():
                deleet = deleet.replace(k, v)
            if deleet != text:
                decoded_variants.append(deleet)

        return decoded_variants

    def check_tool_access(self, tenant_id: str, tool_name: str) -> PolicyCheckResult:
        """Check if a tenant is allowed to use a specific tool."""
        if not self.config.enabled:
            return PolicyCheckResult(verdict=PolicyVerdict.ALLOW, reason="policy disabled")

        allowed = self._tenant_permissions.get(tenant_id)
        if allowed is None:
            # No explicit permissions = allow all (for dev/testing)
            return PolicyCheckResult(verdict=PolicyVerdict.ALLOW, reason="no restrictions")

        if tool_name in allowed:
            return PolicyCheckResult(verdict=PolicyVerdict.ALLOW, reason="tool permitted")

        telemetry.metrics.record_policy_denial()
        return PolicyCheckResult(
            verdict=PolicyVerdict.DENY,
            reason=f"tenant '{tenant_id}' not authorized for tool '{tool_name}'",
        )

    def check_output(self, text: str) -> PolicyCheckResult:
        """Check agent output before returning to user."""
        if not self.config.enabled:
            return PolicyCheckResult(verdict=PolicyVerdict.ALLOW, reason="policy disabled")

        # Check for PII patterns (simplified)
        pii_patterns = [
            re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
            re.compile(r"\b\d{16,19}\b"),  # Credit card
        ]
        for pattern in pii_patterns:
            if pattern.search(text):
                telemetry.metrics.record_policy_denial()
                return PolicyCheckResult(
                    verdict=PolicyVerdict.DENY,
                    reason="potential PII detected in output",
                )

        return PolicyCheckResult(verdict=PolicyVerdict.ALLOW, reason="output clean")
