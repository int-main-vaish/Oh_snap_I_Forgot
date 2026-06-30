from datetime import datetime


def build_prioritization_prompt(task_input: str, user_context: str = "") -> str:
    """
    Builds a prompt for Gemini to parse tasks, assign urgency scores,
    and generate a realistic schedule based on user context.
    """

    current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    current_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    context_section = (
        f"\nUser's personal context/constraints: {user_context}\n"
        if user_context.strip()
        else "\nNo additional context provided by the user.\n"
    )

    prompt = f"""You are an expert productivity assistant helping a user who is overwhelmed with deadlines and tasks.

Today's date and time is: {current_datetime} (ISO: {current_iso})

The user has dumped their tasks/deadlines below in free, unstructured text. Your job is to:

1. Carefully parse out EACH individual task or deadline mentioned in the text below.
2. For each task, assign an urgency score from 0 to 10 (10 = extremely urgent, must act immediately; 0 = not urgent at all). Base urgency on how soon the deadline is and the likely consequences of missing it.
3. Write a short, one-line, honest explanation of why missing this task matters (be direct, not generic).
4. Suggest a realistic time slot or day to work on each task, taking into account today's date and the user's personal context/constraints (if provided).
5. Write a brief overall schedule_summary (2-3 sentences) giving the user a clear, encouraging action plan for the days ahead.

User's raw task dump:
\"\"\"
{task_input}
\"\"\"
{context_section}
IMPORTANT OUTPUT RULES:
- Return ONLY valid JSON. Do NOT include markdown code fences (no ```json or ```).
- Do NOT include any explanation, preamble, or text outside the JSON object.
- The JSON must strictly follow this exact structure:

{{
  "tasks": [
    {{
      "task": "string - short task name",
      "deadline": "string - the deadline as mentioned or inferred",
      "deadline_iso": "string - ISO 8601 datetime of the deadline, e.g. 2026-07-01T09:00:00. Infer from context and today's date/time.",
      "urgency": integer between 0 and 10,
      "why_it_matters": "string - one line, direct explanation",
      "suggested_time_slot": "string - specific day/time suggestion"
    }}
  ],
  "schedule_summary": "string - 2-3 sentence overall plan summary",
  "procrastination_score": "integer 0-100 — how badly the user is procrastinating, based on how close deadlines are relative to when they are asking. 0 = very organized, 100 = absolute maximum panic"
}}

Return ONLY the JSON object now."""

    return prompt


def build_what_if_prompt(task_input: str) -> str:
    """
    Builds a humorous prompt for the 'What If I Just Don't?' feature.
    Asks Gemini what happens if the user skips all their tasks.
    """
    prompt = f"""You are a brutally honest but hilarious life advisor. The user listed these tasks and deadlines:

\"\"\"
{task_input}
\"\"\"

They're now asking: "What if I just... don't do any of this?"

Write a short, funny, but REALISTIC breakdown of what would happen if they skipped EVERY single task. Be specific to THEIR actual tasks — don't be generic. Mix dark humor with real consequences.

Rules:
- 4-6 bullet points, each starting with an emoji
- Be savage but not mean
- Reference their specific tasks/deadlines
- End with one encouraging line to actually get them moving
- Keep it under 200 words
- Return ONLY the text, no JSON, no markdown code fences"""

    return prompt