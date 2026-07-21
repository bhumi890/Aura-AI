"""
ai_core/agents/safety/resources.py

Structured helpline and mental health resource registry.
Keeps emergency and crisis resources deterministically managed in code rather
than relying on probabilistic RAG retrieval.
"""
from typing import TypedDict, Optional


class HelplineResource(TypedDict):
    name: str
    number: str
    description: str
    available_24_7: bool
    category: str


# Primary crisis and self-harm resources
CRISIS_HELPLINES: dict[str, list[HelplineResource]] = {
    "default": [
        {
            "name": "Kiran Mental Health & Suicide Helpline (24x7 Support)",
            "number": "9152987821",
            "description": "Free, confidential 24/7 mental health, self-harm, and crisis support helpline.",
            "available_24_7": True,
            "category": "suicide_and_self_harm",
        },
        {
            "name": "Vandrevala Foundation Helpline",
            "number": "+91 9999 666 555",
            "description": "24/7 free emotional support and crisis counseling.",
            "available_24_7": True,
            "category": "suicide_and_self_harm",
        },
    ],
    "suicide_and_self_harm": [
        {
            "name": "Kiran Mental Health & Suicide Helpline (24x7 Support)",
            "number": "9152987821",
            "description": "Free, confidential 24/7 mental health, self-harm, and crisis support helpline.",
            "available_24_7": True,
            "category": "suicide_and_self_harm",
        },
    ],
    "at_risk": [
        {
            "name": "Kiran Mental Health Helpline",
            "number": "9152987821",
            "description": "Confidential counseling and psychological support.",
            "available_24_7": True,
            "category": "general_support",
        },
    ],
}


def get_crisis_resources(category: Optional[str] = None) -> list[HelplineResource]:
    """
    Retrieve deterministic helpline resources for a given safety category.
    Defaults to the primary crisis resources (including 9152987821).
    """
    if category and category in CRISIS_HELPLINES:
        return CRISIS_HELPLINES[category]
    return CRISIS_HELPLINES["default"]


def format_crisis_message(category: Optional[str] = None) -> str:
    """
    Format the standardized crisis response message highlighting primary helplines.
    """
    resources = get_crisis_resources(category)
    
    lines = [
        "It sounds like you're going through something really difficult right now, and I want to make sure you get immediate, caring support.",
        "",
        "Please reach out to a trusted professional or a 24/7 crisis helpline right away:",
        ""
    ]
    
    for res in resources:
        lines.append(f"📞 **{res['name']}**")
        lines.append(f"**Call: {res['number']}**")
        if res.get("description"):
            lines.append(f"*{res['description']}*")
        lines.append("")
        
    lines.append("You are not alone, and there are trained counselors ready to listen and support you through this right now. Please call or reach out immediately.")
    return "\n".join(lines).strip()
