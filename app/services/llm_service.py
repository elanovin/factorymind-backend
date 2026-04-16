import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class MaintenanceAnswer(BaseModel):
    root_cause: str = Field(
        description="Most plausible underlying cause, grounded in the retrieved incidents when possible."
    )
    suggested_fix: str = Field(
        description="Concrete, actionable steps an engineer can take (checks, adjustments, parts, procedures)."
    )
    confidence: Literal["High", "Medium", "Low"] = Field(
        description="How well the retrieved incidents support this assessment."
    )


def generate_answer(query: str, incidents: list) -> dict:
    context = ""

    for incident in incidents:
        context += f"""
Machine: {incident.machine_id}
Category: {incident.category}
Severity: {incident.severity}
Problem: {incident.description}
Resolution: {incident.resolution}
"""

    user_prompt = f"""You are an industrial maintenance engineer's assistant.

Use ONLY the past incidents below as supporting evidence. If they do not clearly match the question, say so briefly and still give your best engineering judgment, with lower confidence.

Past incidents:
{context}

User question:
{query}
Focus especially on the resolution steps from similar incidents.
Prioritize solutions that appear multiple times.

Respond with concise, practical content suitable for engineers on the plant floor. Avoid long prose — short sentences and bullet-style phrasing inside the strings is fine."""

    try:
        completion = client.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You produce structured maintenance assessments. "
                        "Be concise and practical. Prefer specific checks and fixes over generic advice."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            response_format=MaintenanceAnswer,
            temperature=0.2,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is not None:
            return parsed.model_dump()

    except Exception:
        pass

    if incidents:
        top = incidents[0]
        return {
            "root_cause": (
                f"Closest match in history: {top.description} "
                f"(category: {top.category}, machine: {top.machine_id})."
            ),
            "suggested_fix": str(top.resolution),
            "confidence": "Medium",
        }

    return {
        "root_cause": "No similar incidents in the database to justify a specific root cause.",
        "suggested_fix": (
            "Collect fault codes, recent changes, and operating conditions; inspect the affected subsystem "
            "per OEM guidance and escalate if safety or production risk is unclear."
        ),
        "confidence": "Low",
    }
