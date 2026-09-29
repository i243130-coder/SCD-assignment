"""Deterministic keyword-based triage. Always available, never fails."""

from app.providers.triage.base import TriageProvider, TriageResult
from app.schemas import Category, Priority

# Keyword → Category mapping
KEYWORD_MAP: dict[Category, list[str]] = {
    Category.WATER: [
        "water", "pipe", "leak", "flood", "drainage", "sewage",
        "tap", "supply", "pani", "nala", "tanki", "boring",
    ],
    Category.ELECTRICITY: [
        "electric", "power", "outage", "transformer", "wire",
        "voltage", "bijli", "load shedding", "light pole", "meter",
    ],
    Category.SANITATION: [
        "garbage", "trash", "waste", "dump", "clean", "sanitation",
        "sweeper", "kachra", "ganda", "smell", "mosquito", "drain",
    ],
    Category.ROADS: [
        "road", "pothole", "crack", "pavement", "highway", "bridge",
        "sarak", "gaddha", "footpath", "speed bump", "divider",
    ],
    Category.STREETLIGHTS: [
        "streetlight", "lamp", "dark", "street light", "pole light",
        "bulb", "halogen", "light broken",
    ],
}

# Priority keywords
PRIORITY_KEYWORDS: dict[Priority, list[str]] = {
    Priority.HIGH: [
        "urgent", "emergency", "danger", "hazard", "critical",
        "immediately", "fori", "khatarnak", "accident", "injured",
    ],
    Priority.LOW: [
        "minor", "small", "slight", "cosmetic", "chota", "thoda",
    ],
}


class RuleBasedTriage(TriageProvider):
    """Deterministic keyword-based fallback. Always available, never fails."""

    @property
    def name(self) -> str:
        return "rules"

    async def triage(self, text: str, location: str) -> TriageResult:
        combined = f"{text} {location}".lower()

        # Determine category by keyword match count
        category = Category.OTHER
        best_score = 0
        for cat, keywords in KEYWORD_MAP.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > best_score:
                best_score = score
                category = cat

        # Determine priority
        priority = Priority.NORMAL
        for pri, keywords in PRIORITY_KEYWORDS.items():
            if any(kw in combined for kw in keywords):
                priority = pri
                break

        # Generate summary
        summary = f"[Rules] {text[:100].strip()}"
        if len(summary) > 140:
            summary = summary[:137] + "..."

        return TriageResult(
            category=category,
            priority=priority,
            summary=summary,
            confidence=0.6,
        )
