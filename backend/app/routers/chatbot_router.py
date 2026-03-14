"""
Chatbot router — NLP-powered chatbot using OpenAI with keyword fallback.
Understands natural language medical/company queries via GPT.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])


# ── Company Knowledge Base ────────────────────────────────

COMPANY_CONTEXT = """
You are an AI assistant for HireAI, a cutting-edge AI-powered recruitment platform.

Company Info:
- HireAI uses machine learning and NLP to streamline hiring
- We specialize in automated resume parsing, AI-driven candidate scoring, fraud detection, and intelligent candidate matching
- Culture: Innovation, collaboration, continuous learning, agile environment, flat hierarchies

Benefits:
- Competitive salary (₹6-25 LPA depending on role)
- Health insurance for employee and family
- Flexible work hours and hybrid/remote options
- Annual learning budget of ₹50,000
- Stock options for early employees
- 20 paid vacation days + public holidays
- Gym membership reimbursement

Available Roles & Salary Ranges:
- Software Engineer: ₹8-18 LPA (React, Python, FastAPI, PostgreSQL)
- Senior Software Engineer: ₹15-25 LPA (System Design, Leadership, Full Stack)
- ML Engineer: ₹12-22 LPA (Python, TensorFlow, NLP, Computer Vision)
- Product Manager: ₹14-24 LPA (Strategy, Analytics, Stakeholder Management)
- UI/UX Designer: ₹6-15 LPA (Figma, User Research, Design Systems)

Hiring Process:
1. Submit application (resume + basic details)
2. AI screening (automated assessment)
3. Technical round (coding/system design)
4. HR interview
5. Offer letter within 48 hours of final round

Tech Stack: React, Tailwind CSS, Python, FastAPI, PostgreSQL, TensorFlow, OpenAI, Docker, AWS, Git

Timeline: AI screening is instant, technical round within 3-5 days, HR interview within 2-3 days, offer within 48 hours of final round.

INSTRUCTIONS:
- Always be helpful, professional, and enthusiastic.
- Understand natural language queries — users may use slang, abbreviations, or informal language.
- If the user asks about medical/health benefits, explain the health insurance coverage.
- If you don't know something specific, give a helpful general answer based on the context above.
- Keep responses concise but informative (2-5 sentences for most questions).
- Use emojis sparingly to make responses friendly.
- Format responses with markdown-style bullets when listing items.
"""


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    source: str  # "keyword", "ai", or "nlp"


# ── NLP intent detection (understands natural language) ────

def _detect_intent(text: str) -> Optional[str]:
    """Use NLP-style pattern matching to detect user intent from natural language."""
    lower = text.lower().strip()
    words = set(lower.split())

    # Greeting detection — handles informal greetings
    greeting_words = {"hi", "hello", "hey", "hola", "sup", "yo", "hii", "hiii", "greetings", "namaste"}
    if words & greeting_words and len(words) <= 4:
        return "greeting"

    # Salary/compensation — handles informal queries like "kitna milega", "how much do you pay"
    salary_patterns = [
        "salary", "compensation", "pay", "ctc", "package", "lpa", "stipend",
        "money", "earn", "how much", "kitna", "income", "wage", "remuneration",
        "offer", "paying", "paid"
    ]
    if any(p in lower for p in salary_patterns):
        return "salary"

    # Benefits — handles "what perks", "do you have insurance", "leaves kitne"
    benefit_patterns = [
        "benefit", "perk", "insurance", "leave", "vacation", "gym", "learning",
        "stock", "health cover", "medical", "wfh", "remote work", "flexibility",
        "holiday", "pto", "sick leave", "maternity", "paternity"
    ]
    if any(p in lower for p in benefit_patterns):
        return "benefits"

    # Process — "how to apply", "kaise apply karu", "interview process"
    process_patterns = [
        "process", "hiring", "interview", "stage", "step", "round", "how to apply",
        "apply", "application", "kaise", "procedure", "what happens", "next step",
        "selection", "screening"
    ]
    if any(p in lower for p in process_patterns):
        return "process"

    # Culture — "work environment", "office kaisa hai"
    culture_patterns = [
        "culture", "team", "environment", "balance", "remote", "hybrid", "wfh",
        "office", "workplace", "atmosphere", "vibe", "work life", "work-life"
    ]
    if any(p in lower for p in culture_patterns):
        return "culture"

    # About company
    about_patterns = [
        "about", "company", "what do you do", "who are", "organization",
        "tell me about", "what is hireai", "what is hire ai"
    ]
    if any(p in lower for p in about_patterns):
        return "about"

    # Tech stack
    tech_patterns = [
        "tech", "stack", "technology", "framework", "language", "tool",
        "what do you use", "programming"
    ]
    if any(p in lower for p in tech_patterns):
        return "tech"

    # Timeline
    timeline_patterns = [
        "how long", "time", "days", "when", "hear back", "response time",
        "timeline", "duration", "fast", "quickly", "soon"
    ]
    if any(p in lower for p in timeline_patterns):
        return "timeline"

    # Status
    status_patterns = [
        "status", "where do i stand", "progress", "update", "my application",
        "track", "check"
    ]
    if any(p in lower for p in status_patterns):
        return "status"

    # Thanks
    thanks_patterns = ["thank", "thanks", "thx", "appreciate", "dhanyavaad", "shukriya"]
    if any(p in lower for p in thanks_patterns):
        return "thanks"

    # Roles
    role_patterns = [
        "role", "position", "job", "opening", "vacancy", "available",
        "hire", "recruit", "looking for"
    ]
    if any(p in lower for p in role_patterns):
        return "roles"

    return None


# ── Keyword-based responses for detected intents ──────────

INTENT_RESPONSES = {
    "greeting": "Hello! 👋 Welcome to HireAI. I can help you with company info, salary ranges, hiring process, benefits, available roles, and more. What would you like to know?",

    "salary": """💰 **Salary Ranges at HireAI:**

• **Software Engineer**: ₹8-18 LPA
• **Senior Software Engineer**: ₹15-25 LPA
• **ML Engineer**: ₹12-22 LPA
• **Product Manager**: ₹14-24 LPA
• **UI/UX Designer**: ₹6-15 LPA

Final compensation depends on experience, skills, and interview performance. We also offer stock options and annual bonuses.""",

    "benefits": """🎁 **Benefits & Perks:**

• Competitive salary (₹6-25 LPA)
• Health insurance for employee and family
• Flexible work hours and hybrid/remote options
• Annual learning budget of ₹50,000
• Stock options for early employees
• 20 paid vacation days + public holidays
• Gym membership reimbursement""",

    "process": """📋 **Hiring Process:**

1. Submit application (resume + basic details)
2. AI screening (automated assessment)
3. Technical round (coding/system design)
4. HR interview
5. Offer letter within 48 hours of final round

The entire process typically takes 5-7 business days.""",

    "culture": """🏢 **Work Culture:**

We foster innovation, collaboration, and continuous learning. Our team works in an agile environment with flat hierarchies and open communication.

• Hybrid/remote options available
• Core hours: 10 AM - 4 PM IST
• Weekly team events & learning sessions
• Flat hierarchy with open communication""",

    "about": """🏢 **About HireAI:**

HireAI is a cutting-edge AI-powered recruitment platform that leverages machine learning and natural language processing to streamline hiring. We specialize in automated resume parsing, AI-driven candidate scoring, fraud detection, and intelligent candidate matching.""",

    "tech": """🛠️ **Tech Stack:**

• Frontend: React, Tailwind CSS
• Backend: Python, FastAPI
• Database: PostgreSQL
• ML: TensorFlow, OpenAI
• Infra: Docker, AWS
• Version Control: Git, GitHub""",

    "timeline": """⏱️ **Timeline:**

• AI screening: Instant results
• Technical round: Within 3-5 days of screening
• HR interview: Within 2-3 days of technical
• Offer: Within 48 hours of final round

Total process: ~5-7 business days""",

    "status": "📊 **Application Status:**\nYour application is being processed. HR typically reviews within 3-5 business days after each stage.\n\nIf you haven't heard back, you can reach out to: hr@hireai.com",

    "thanks": "You're welcome! 😊 Good luck with your application. If you have any more questions, feel free to ask!",

    "roles": """📌 **Available Roles at HireAI:**

• **Software Engineer** — ₹8-18 LPA (React, Python, FastAPI, PostgreSQL)
• **Senior Software Engineer** — ₹15-25 LPA (System Design, Leadership)
• **ML Engineer** — ₹12-22 LPA (Python, TensorFlow, NLP)
• **Product Manager** — ₹14-24 LPA (Strategy, Analytics)
• **UI/UX Designer** — ₹6-15 LPA (Figma, User Research)

Would you like to know more about a specific role?""",
}


# ── Endpoint ────────────────────────────────────────────────


@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(body: ChatRequest):
    """Answer candidate questions using NLP intent detection + OpenAI fallback."""
    # Step 1: Try NLP intent detection
    intent = _detect_intent(body.message)
    if intent and intent in INTENT_RESPONSES:
        return ChatResponse(response=INTENT_RESPONSES[intent], source="nlp")

    # Step 2: Fallback to OpenAI for complex/unknown queries
    try:
        import httpx

        openai_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_key:
            return ChatResponse(
                response="I can help you with salary ranges, hiring process, benefits, company culture, available roles, and tech stack. Try asking about one of these topics!",
                source="keyword",
            )

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": COMPANY_CONTEXT},
                        {"role": "user", "content": body.message},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7,
                },
            )

            if resp.status_code == 200:
                data = resp.json()
                ai_text = data["choices"][0]["message"]["content"]
                return ChatResponse(response=ai_text, source="ai")
            else:
                return ChatResponse(
                    response="I can help you with salary ranges, hiring process, benefits, company culture, and tech stack. What would you like to know?",
                    source="keyword",
                )

    except Exception:
        return ChatResponse(
            response="I can help you with salary ranges, hiring process, benefits, company culture, and tech stack. What would you like to know?",
            source="keyword",
        )
