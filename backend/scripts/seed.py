"""Idempotent seed script with 30 realistic Urdu-influenced-English complaints.

Usage:
    python -m scripts.seed

Running twice must NOT duplicate records (uses deterministic UUIDs).
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Complaint
from app.database import Base

# Deterministic UUIDs: uuid5 with a fixed namespace ensures idempotency.
NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _seed_id(index: int) -> uuid.UUID:
    """Generate a deterministic UUID for seed complaint #index."""
    return uuid.uuid5(NAMESPACE, f"seed-complaint-{index}")


SEED_COMPLAINTS = [
    # Water (5)
    {
        "text": "Pani ki supply subah se band hai, poora mohalla pareshan hai. Tanki bhi khaali ho gayi hai.",
        "location": "Block 14, Gulshan-e-Iqbal, Karachi",
        "category": "water",
        "priority": "high",
    },
    {
        "text": "Water pipe burst near main road, clean water is being wasted continuously for the last two days.",
        "location": "Jail Road, Lahore",
        "category": "water",
        "priority": "high",
    },
    {
        "text": "Nala overflow ho raha hai aur ganda pani ghar mein aa raha hai. Bohot mushkil situation hai.",
        "location": "Orangi Town, Sector 5, Karachi",
        "category": "water",
        "priority": "high",
    },
    {
        "text": "Boring water has become yellowish and smells bad. Please check the underground water quality.",
        "location": "Satellite Town, Rawalpindi",
        "category": "water",
        "priority": "normal",
    },
    {
        "text": "Water tanki on the roof of government building is leaking and wasting water since last week.",
        "location": "Civic Centre, Islamabad",
        "category": "water",
        "priority": "low",
    },
    # Electricity (5)
    {
        "text": "Bijli ka transformer phatt gaya hai aur poore area mein andhera hai. Fori action chahiye.",
        "location": "Model Town, Lahore",
        "category": "electricity",
        "priority": "high",
    },
    {
        "text": "Load shedding has increased to 12 hours daily. We are paying bills on time but no improvement.",
        "location": "Nazimabad, Block 3, Karachi",
        "category": "electricity",
        "priority": "high",
    },
    {
        "text": "Exposed electric wires hanging near children's playground, very khatarnak situation.",
        "location": "Defence Housing Authority, Phase 2, Lahore",
        "category": "electricity",
        "priority": "high",
    },
    {
        "text": "Electricity meter is showing wrong readings, bill has doubled without any extra usage.",
        "location": "Hayatabad, Phase 4, Peshawar",
        "category": "electricity",
        "priority": "normal",
    },
    {
        "text": "Minor voltage fluctuation in the evening hours causing appliance issues in our street.",
        "location": "Cantt Area, Multan",
        "category": "electricity",
        "priority": "low",
    },
    # Sanitation (5)
    {
        "text": "Kachra collection band hai aur garbage pile up ho raha hai corner pe. Bohot ganda smell aa raha hai.",
        "location": "Lyari, Karachi",
        "category": "sanitation",
        "priority": "high",
    },
    {
        "text": "Open drain near school is overflowing. Children are getting sick from mosquitoes breeding there.",
        "location": "Gulberg, Lahore",
        "category": "sanitation",
        "priority": "high",
    },
    {
        "text": "Sweeper has not come for one week. Whole street is full of waste and flies everywhere.",
        "location": "Saddar, Rawalpindi",
        "category": "sanitation",
        "priority": "normal",
    },
    {
        "text": "Illegal dump site created on empty plot near residential area. Smoke from burning garbage daily.",
        "location": "North Nazimabad, Block H, Karachi",
        "category": "sanitation",
        "priority": "high",
    },
    {
        "text": "Small amount of garbage collected but the bin is overflowing by evening. Need bigger bin.",
        "location": "Blue Area, Islamabad",
        "category": "sanitation",
        "priority": "low",
    },
    # Roads (5)
    {
        "text": "Bohot bada gaddha hai main road pe, kal ek accident bhi hua. Emergency repair ki zaroorat hai.",
        "location": "Shahrah-e-Faisal, Karachi",
        "category": "roads",
        "priority": "high",
    },
    {
        "text": "Road surface completely broken after rain. Cars are getting damaged and people are injured.",
        "location": "Mall Road, Lahore",
        "category": "roads",
        "priority": "high",
    },
    {
        "text": "Speed bump near hospital is too high, ambulances are having difficulty. Please reduce height.",
        "location": "Jinnah Hospital Road, Karachi",
        "category": "roads",
        "priority": "normal",
    },
    {
        "text": "Footpath tiles are broken and uneven, elderly people are tripping and falling regularly.",
        "location": "F-8 Markaz, Islamabad",
        "category": "roads",
        "priority": "normal",
    },
    {
        "text": "Thoda sa crack aa gaya hai divider pe. Not urgent but should be fixed before monsoon.",
        "location": "University Road, Peshawar",
        "category": "roads",
        "priority": "low",
    },
    # Streetlights (5)
    {
        "text": "Street lights are not working on entire main road. Area becomes very dark and dangerous at night.",
        "location": "Clifton, Block 5, Karachi",
        "category": "streetlights",
        "priority": "high",
    },
    {
        "text": "Light pole near park has fallen down after storm. Wires are exposed on the ground, very dangerous.",
        "location": "Jallo Park Road, Lahore",
        "category": "streetlights",
        "priority": "high",
    },
    {
        "text": "Halogen bulb on our street has been flickering for two weeks. Sometimes works, sometimes not.",
        "location": "G-9 Markaz, Islamabad",
        "category": "streetlights",
        "priority": "normal",
    },
    {
        "text": "New streetlights installed but they turn on during daytime wasting electricity. Timer issue.",
        "location": "Bahria Town, Phase 8, Rawalpindi",
        "category": "streetlights",
        "priority": "low",
    },
    {
        "text": "One lamp post in the parking area has a broken glass cover. Needs replacement for safety.",
        "location": "Centaurus Mall Area, Islamabad",
        "category": "streetlights",
        "priority": "low",
    },
    # Other (5)
    {
        "text": "Stray dogs have become aggressive in the neighborhood. Children are scared to walk to school.",
        "location": "PECHS, Block 6, Karachi",
        "category": "other",
        "priority": "high",
    },
    {
        "text": "Illegal construction happening on green belt area. Builder is ignoring all municipal notices.",
        "location": "Johar Town, Block J, Lahore",
        "category": "other",
        "priority": "normal",
    },
    {
        "text": "Public park benches are broken and swings are rusty. Kids got tetanus scratch last month.",
        "location": "Fatima Jinnah Park, Islamabad",
        "category": "other",
        "priority": "normal",
    },
    {
        "text": "Noise pollution from factory running illegally in residential zone. Operating at night.",
        "location": "SITE Area, Karachi",
        "category": "other",
        "priority": "normal",
    },
    {
        "text": "Chota sa issue hai: public toilet near bus stop needs cleaning, not very urgent.",
        "location": "Faisal Movers Terminal, Lahore",
        "category": "other",
        "priority": "low",
    },
]


async def seed_database() -> None:
    """Insert seed complaints idempotently."""
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        inserted = 0
        skipped = 0

        for i, data in enumerate(SEED_COMPLAINTS):
            seed_id = _seed_id(i)

            # Check if already exists (idempotency)
            existing = await session.execute(
                select(Complaint.id).where(Complaint.id == seed_id)
            )
            if existing.scalar() is not None:
                skipped += 1
                continue

            complaint = Complaint(
                id=seed_id,
                text=data["text"],
                location=data["location"],
                reporter_contact=None,
                category=data["category"],
                priority=data["priority"],
                status="open",
                ai_summary=f"[Seed] {data['text'][:100]}",
                triaged_by="seed",
                triage_latency_ms=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(complaint)
            inserted += 1

        await session.commit()
        print(f"Seed complete: {inserted} inserted, {skipped} skipped (already existed)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
