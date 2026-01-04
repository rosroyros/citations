"""
Citation style configuration module.

This module is the single source of truth for all supported citation styles.
It provides type-safe style routing and a central place to add future styles.
"""
from typing import Literal, Dict, Any

SUPPORTED_STYLES: Dict[str, Dict[str, str]] = {
    "apa7": {
        "label": "APA 7th Edition",
        "prompt_file": "validator_prompt_v3_no_hallucination.txt",
        "success_message": "No APA 7 formatting errors detected"
    },
    "mla9": {
        "label": "MLA 9th Edition",
        "prompt_file": "validator_prompt_mla9_v1.1.txt",
        "success_message": "No MLA 9 formatting errors detected"
    },
    "chicago17": {
        "label": "Chicago 17th Edition",
        "prompt_file": "validator_prompt_chicago17_v1.2.txt",
        "success_message": "No Chicago 17 formatting errors detected"
    }
}

StyleType = Literal["apa7", "mla9", "chicago17"]
DEFAULT_STYLE: StyleType = "apa7"


def is_valid_style(style: str) -> bool:
    """Check if a style string is valid."""
    return style in SUPPORTED_STYLES


def get_style_config(style: StyleType) -> Dict[str, str]:
    """Get configuration for a given style."""
    return SUPPORTED_STYLES[style]
