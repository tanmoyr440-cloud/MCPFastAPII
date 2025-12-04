"""
Guardrails Service - Content Safety, Privacy, and Data Protection

Implements guardrails for:
- Sensitivity Detection: Identifies sensitive topics (medical, financial, legal, etc.)
- Toxicity Filtering: Detects and blocks toxic/harmful content
- Data Loss Prevention: Prevents sharing of sensitive data (keys, passwords, PII)
- Data Privacy: Redacts or blocks personally identifiable information (PII)
"""

import re
import json
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class SensitivityLevel(str, Enum):
    """Sensitivity levels for different content categories"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardrailResult:
    """Result of guardrail check"""
    passed: bool
    severity: SensitivityLevel
    issues: list[str]
    redacted_content: Optional[str] = None
    recommendation: str = "approved"


# ============== Sensitivity Detection ==============

SENSITIVE_PATTERNS = {
    "medical": {
        "patterns": [
            r"\b(diagnosis|prescription|medication|symptom|disease|treatment|patient|doctor|hospital|clinic)\b",
            r"\b(HIV|AIDS|cancer|diabetes|heart disease|mental illness)\b",
        ],
        "severity": SensitivityLevel.MEDIUM,
    },
    "financial": {
        "patterns": [
            r"\b(credit card|bank account|loan|mortgage|investment|invested|invest|portfolio|salary|payment|debt|income|expense)\b",
            r"\b(\$\d+,?\d+|€\d+|£\d+)\b",
        ],
        "severity": SensitivityLevel.MEDIUM,
    },
    "legal": {
        "patterns": [
            r"\b(lawsuit|defendant|plaintiff|court|judge|attorney|lawyer|legal|contract|agreement|sue|suing)\b",
            r"\b(guilty|innocent|verdict|sentence|parole|conviction)\b",
        ],
        "severity": SensitivityLevel.MEDIUM,
    },
}


# ============== Toxicity Patterns ==============

TOXIC_PATTERNS = [
    # Violence and threats - future tense or intent
    r"\b(will|gonna|going to|im going to|i will|time to|lets?)\s+(kill|murder|hurt|harm|attack|rape|bomb|shoot|assault)\b",
    r"\b(kill|murder|harm|assault|attack|bomb|shoot|stab|torture|rape)\s+(my|your|anyone|people|everyone|them|us|the|a)\b",
    # Standalone bombs/explosives
    r"\b(bomb|explosives?|detonate|ied)\b",
    # Hate speech
    r"\b(hate|despise|detest)\s+\w+",
    r"\b(people\s+of\s+(religion|race|ethnicity|nationality))",
    # Group harm and deportation
    r"\b(should\s+be\s+(deported|killed|eliminated|removed|destroyed))\b",
    r"\b(should\s+all\s+be\s+(deported|killed|eliminated|removed|destroyed))\b",
    # Harassment and threats - doxxing/swatting
    r"\b(doxxing|swat|blackmail|extort|haunt|stalk|found.*home.*address|found.*address|organize.*swat)\b",
    r"\b(home\s+address|criminal\s+record|everyone\s+should\s+know)\b",
    # General dehumanizing language
    r"\b(deserve\s+to\s+die|should\s+be\s+killed|human\s+trash|subhuman)\b",
    # Threats to groups
    r"\b(all\s+\w+\s+should\s+(die|be\s+killed|be\s+eliminated))\b",
]


# ============== Data Loss Prevention Patterns ==============

DLP_PATTERNS = {
    "api_key": {
        "patterns": [
            r"api[_-]?key[:\s]*['\"]?([a-zA-Z0-9\-_]{20,})['\"]?",
            r"sk[_-]?[a-zA-Z0-9\-_]{20,}",
            r"ghp[_a-zA-Z0-9]{36,}",  # GitHub tokens
        ],
        "redaction": "[API_KEY_REDACTED]",
    },
    "password": {
        "patterns": [
            r"password[:\s]*['\"]?([^\s'\"]{6,})['\"]?",
            r"passwd[:\s]*['\"]?([^\s'\"]{6,})['\"]?",
            r"pwd[:\s]*['\"]?([^\s'\"]{6,})['\"]?",
        ],
        "redaction": "[PASSWORD_REDACTED]",
    },
    "database_connection": {
        "patterns": [
            r"(mongodb|mysql|postgresql|sql)[+:\/\/]+[a-zA-Z0-9]+:[^\s]+@",
            r"(host|server)[=:]\s*\S+\s*(port|user|password)[=:]",
        ],
        "redaction": "[DATABASE_URL_REDACTED]",
    },
    "aws_key": {
        "patterns": [
            r"AKIA[0-9A-Z]{16}",  # AWS Access Key
        ],
        "redaction": "[AWS_KEY_REDACTED]",
    },
}


# ============== PII Detection Patterns ==============

PII_PATTERNS = {
    "email": {
        "patterns": [r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"],
        "redaction": "[EMAIL_REDACTED]",
        "confidence": 0.95,
    },
    "phone": {
        "patterns": [
            r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b",
            r"\b(?:\+[0-9]{1,3}[-.\s]?)?[0-9]{7,15}\b",
        ],
        "redaction": "[PHONE_REDACTED]",
        "confidence": 0.85,
    },
    "ssn": {
        "patterns": [r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b"],
        "redaction": "[SSN_REDACTED]",
        "confidence": 0.99,
    },
    "credit_card": {
        "patterns": [
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11})\b"
        ],
        "redaction": "[CREDIT_CARD_REDACTED]",
        "confidence": 0.99,
    },
    "ip_address": {
        "patterns": [
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        ],
        "redaction": "[IP_ADDRESS_REDACTED]",
        "confidence": 0.90,
    },
}


# ============== Core Guardrail Functions ==============


def check_sensitivity(content: str) -> GuardrailResult:
    """
    Check content for sensitive topics (medical, financial, legal, etc.)
    
    Args:
        content: Text to check
        
    Returns:
        GuardrailResult with sensitivity assessment
    """
    issues = []
    max_severity = SensitivityLevel.LOW

    for category, config in SENSITIVE_PATTERNS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Sensitive topic detected: {category}")
                if config["severity"].value > max_severity.value:
                    max_severity = config["severity"]

    return GuardrailResult(
        passed=len(issues) == 0,
        severity=max_severity,
        issues=issues,
        recommendation="approved" if len(issues) == 0 else "review_recommended",
    )


def check_toxicity(content: str) -> GuardrailResult:
    """
    Check content for toxic, harmful, or hateful language
    
    Args:
        content: Text to check
        
    Returns:
        GuardrailResult with toxicity assessment
    """
    issues = []

    for pattern in TOXIC_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append("Toxic or harmful language detected")
            break  # Only report once

    return GuardrailResult(
        passed=len(issues) == 0,
        severity=SensitivityLevel.CRITICAL if issues else SensitivityLevel.LOW,
        issues=issues,
        recommendation="blocked" if issues else "approved",
    )


def check_data_loss_prevention(content: str) -> tuple[GuardrailResult, str]:
    """
    Check content for sensitive data that should not be shared
    Redacts detected sensitive data
    
    Args:
        content: Text to check and redact
        
    Returns:
        Tuple of (GuardrailResult, redacted_content)
    """
    issues = []
    redacted_content = content
    detected_types = set()

    for data_type, config in DLP_PATTERNS.items():
        for pattern in config["patterns"]:
            matches = re.finditer(pattern, redacted_content, re.IGNORECASE)
            for match in matches:
                issues.append(f"Sensitive data detected: {data_type}")
                detected_types.add(data_type)
                redacted_content = re.sub(
                    pattern, config["redaction"], redacted_content, flags=re.IGNORECASE
                )

    return (
        GuardrailResult(
            passed=len(issues) == 0,
            severity=SensitivityLevel.CRITICAL if issues else SensitivityLevel.LOW,
            issues=list(set(issues)),  # Remove duplicates
            redacted_content=redacted_content if issues else None,
            recommendation="blocked_with_redaction" if issues else "approved",
        ),
        redacted_content,
    )


def check_data_privacy(content: str) -> tuple[GuardrailResult, str]:
    """
    Check content for PII (Personally Identifiable Information)
    Redacts detected PII
    
    Args:
        content: Text to check and redact
        
    Returns:
        Tuple of (GuardrailResult, redacted_content)
    """
    issues = []
    redacted_content = content
    detected_pii_types = set()

    for pii_type, config in PII_PATTERNS.items():
        for pattern in config["patterns"]:
            matches = re.finditer(pattern, redacted_content, re.IGNORECASE)
            for match in matches:
                issues.append(f"PII detected: {pii_type}")
                detected_pii_types.add(pii_type)
                redacted_content = re.sub(
                    pattern, config["redaction"], redacted_content, flags=re.IGNORECASE
                )

    return (
        GuardrailResult(
            passed=len(issues) == 0,
            severity=SensitivityLevel.CRITICAL if issues else SensitivityLevel.LOW,
            issues=list(set(issues)),  # Remove duplicates
            redacted_content=redacted_content if issues else None,
            recommendation="blocked_with_redaction" if issues else "approved",
        ),
        redacted_content,
    )


def validate_all_guardrails(content: str) -> dict:
    """
    Run all guardrail checks and consolidate results
    
    Args:
        content: Text to validate
        
    Returns:
        Dict with all guardrail results and final recommendation
    """
    # Run all checks
    sensitivity_result = check_sensitivity(content)
    toxicity_result = check_toxicity(content)
    dlp_result, dlp_redacted = check_data_loss_prevention(content)
    privacy_result, privacy_redacted = check_data_privacy(content)

    # Determine final content (apply both redactions if needed)
    final_content = content
    if dlp_result.issues:
        final_content = dlp_redacted
    if privacy_result.issues:
        final_content = privacy_redacted

    # Determine final recommendation
    all_issues = (
        sensitivity_result.issues
        + toxicity_result.issues
        + dlp_result.issues
        + privacy_result.issues
    )

    if toxicity_result.issues:
        final_recommendation = "blocked"
    elif dlp_result.issues or privacy_result.issues:
        final_recommendation = "modified"
    elif sensitivity_result.issues:
        final_recommendation = "review_required"
    else:
        final_recommendation = "approved"

    return {
        "overall_status": final_recommendation,
        "should_block": bool(toxicity_result.issues),
        "should_redact": bool(dlp_result.issues or privacy_result.issues),
        "final_content": final_content,
        "checks": {
            "sensitivity": {
                "passed": sensitivity_result.passed,
                "severity": sensitivity_result.severity.value,
                "issues": sensitivity_result.issues,
            },
            "toxicity": {
                "passed": toxicity_result.passed,
                "severity": toxicity_result.severity.value,
                "issues": toxicity_result.issues,
            },
            "data_loss_prevention": {
                "passed": dlp_result.passed,
                "severity": dlp_result.severity.value,
                "issues": dlp_result.issues,
            },
            "data_privacy": {
                "passed": privacy_result.passed,
                "severity": privacy_result.severity.value,
                "issues": privacy_result.issues,
            },
        },
    }
