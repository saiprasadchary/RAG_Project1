from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..api.config import Settings


@dataclass
class SourceForPrompt:
    url: str
    snippet: str


def build_prompt(question: str, sources: List[SourceForPrompt]) -> str:
    numbered = []
    for i, s in enumerate(sources, start=1):
        # Keep snippets modest to avoid huge prompts; model-agnostic
        clip = (s.snippet or "").strip()
        if len(clip) > 500:
            clip = clip[:500] + "…"
        numbered.append(f"[{i}] {clip}\n({s.url})")
    numbered_block = "\n\n".join(numbered) if numbered else "[1] (no context provided)"
    return (
        "You are a careful assistant. Using only the information in the numbered sources, "
        "answer the question concisely in 2–6 sentences. Cite sources inline like [1], [2]. "
        "If the sources are insufficient, say you don't know.\n\n"
        f"Question: {question}\n\nSources:\n{numbered_block}\n"
    )


def generate_answer_dummy(question: str, sources: List[SourceForPrompt]) -> str:
    """
    Very simple, local 'dummy' backend: stitches a short answer mentioning citations.
    This is intentionally basic so the pipeline works without any external LLMs.
    """
    if not sources:
        return "I don't know based on the available sources."
    # Use at most the first 2–3 sources for the stitched answer
    used = min(3, len(sources))
    cites = " ".join(f"[{i}]" for i in range(1, used + 1))
    # Compose a trivial synthesis from the first snippet
    lead = sources[0].snippet.strip()
    if len(lead) > 240:
        lead = lead[:240] + "…"
    return f"{lead} {cites}"


class LLMAdapter:
    """
    Adapter facade for LLM backends. For now we support:
      - 'dummy' (local, no dependencies)
      - 'openai' (placeholder site—add your call if/when you enable it)
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings()
        self.backend = (self.settings.llm_backend or "dummy").lower()

    def answer(self, question: str, sources: List[SourceForPrompt]) -> str:
        if self.backend == "dummy" or self.backend == "openai":
            # For 'openai', we intentionally reuse the same dummy generation to keep local-only
            return generate_answer_dummy(question, sources)
        # default fallback
        return generate_answer_dummy(question, sources)