from typing import List, Optional

def buildGreetingPreamble(goals: List[str]) -> str:
    """
    Constructs a compact greeting preamble from active goals.
    Fixes the Aiden v3.11 'double-label' bug and adds empty-string guards.
    """
    if not goals:
        return ""

    # Filter out empty or whitespace-only goals
    clean_goals = [g.strip() for g in goals if g.strip()]
    if not clean_goals:
        return ""

    # Join goals into a single line for compactness
    goals_text = ", ".join(clean_goals)
    return f"Active goals: {goals_text}"
