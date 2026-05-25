import json
import tempfile
import os
import hashlib

class SubstratoImbad0202AcademicResearchSkills:
    def canonize(self):
        report = {
            "Title": "Academic Research Skills for Claude Code",
            "Description": "A comprehensive suite of Claude Code skills for academic research, covering the full pipeline from research to publication. It implements Deep Research, Academic Paper drafting, Academic Paper Reviewer capabilities, and an Orchestrator.",
            "Features": [
                "Deep Research: 13-agent research team with Socratic guided mode, systematic review, fact-check, and literature review.",
                "Academic Paper: 12-agent paper writing pipeline with Style Calibration, Writing Quality Check, and LaTeX/docx output.",
                "Academic Paper Reviewer: 7-agent multi-perspective peer review with rubric scoring.",
                "Academic Pipeline: 10-stage pipeline orchestrator with adaptive checkpoints and integrity verification.",
                "Style Calibration: Learns the author's voice from past works to guide the writing.",
                "Anti-Hallucination Mandate: Uses WebSearch verification to prevent citation and methodology hallucinations."
            ],
            "Architecture": [
                "Plugins integration with Claude Code CLI, VS Code, JetBrains.",
                "Mode routing based on Socratic dialogue intent and standard matching.",
                "Integrations for PDF generation (Pandoc, Tectonic).",
                "Four primary skill components: deep-research, academic-paper, academic-paper-reviewer, academic-pipeline."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_Imbad0202_academic_research_skills_")
        with os.fdopen(fd, 'w', encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        print("Canonized Imbad0202/academic-research-skills. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoImbad0202AcademicResearchSkills()
    substrate.canonize()
