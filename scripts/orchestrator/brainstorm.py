"""Socratische Brainstorm Engine (Modus 1) voor de blogpost-onderzoeker agent."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

SOCRATIC_SYSTEM_PROMPT = """Je bent de **blogpost-onderzoeker** agent voor edwinvandillen.nl.
Je taak in Modus 1 is om via een Socratische dialoog samen met de auteur (Edwin van Dillen) het onderwerp en de uitgangspunten voor een nieuwe blogpost of artikelenreeks aan te scherpen.

Stel bij elke stap 1 tot maximaal 2 doelgerichte, verdiepende vragen over:
1. De kernhypothese of thesis (wat is het unieke inzicht?).
2. De beoogde lezers en de gewenste toon.
3. Reeks-inpassing (los artikel of deel van een bestaande/nieuwe reeks).
4. Concrete voorbeelden, denkkaders of bronnen die aangehaald moeten worden.

Wees bondig, scherp en redactioneel meedenkend. Geef direct feedback op voorstellen."""


class BrainstormSession:

    def __init__(self, session_id: str, topic: str):
        self.session_id = session_id
        self.topic = topic
        self.created_at = datetime.now().isoformat()
        self.messages: list[dict[str, str]] = []
        
        # Eerste initiële welkomstreactie van de onderzoeker
        initial_reply = (
            f"Interessant onderwerp: **'{topic}'**!\n\n"
            "Om hier een scherp artikel van te maken, heb ik 2 korte vragen voor je:\n"
            "1. Wat is de **kernboodschap of thesis** in 1-2 zinnen die de lezer moet bijblijven?\n"
            "2. Is dit een losstaand artikel, of past dit binnen een specifieke reeks (zoals *Intentie-gedreven engineering* of *Augmented Organisation*)?"
        )
        self.messages.append({"role": "assistant", "content": initial_reply})

    def add_user_message(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})
        reply = self._generate_socratic_reply(user_text)
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def _generate_socratic_reply(self, last_user_text: str) -> str:
        """Herleid een verdiepende socratische vervolgvraag of samenvatting."""
        msg_count = len([m for m in self.messages if m["role"] == "user"])

        if msg_count == 1:
            return (
                "Helder! Goede afbakening.\n\n"
                "Aanvullende vragen voor het **Uitgangspuntendocument**:\n"
                "3. Welke **concrete praktijkvoorbeelden**, frameworks of tegenargumenten moeten we in de tekst opnemen?\n"
                "4. Zijn er specifieke begrippen of stellingen die we juist moeten vermijden?"
            )
        elif msg_count == 2:
            return (
                "Uitstekend. De contouren zijn nu scherp.\n\n"
                "Ik heb voldoende informatie om het **Uitgangspuntendocument** (`briefing.md`) op te stellen.\n"
                "Klik op de knop **'📄 Genereer Briefing & Start Executie'** om deze sessie af te ronden en naar de Stepper (Modus 2) te gaan."
            )
        else:
            return (
                "Genoteerd! Ik neem deze toevoegingen op in het uitgangspuntendocument. "
                "Klik op **'📄 Genereer Briefing & Start Executie'** om de blogpost-keten op te starten."
            )

    def generate_briefing_md(self, slug: str) -> str:
        """Genereer een gestructureerd briefing.md bestand uit de dialoog."""
        user_msgs = [m["content"] for m in self.messages if m["role"] == "user"]
        
        lines = [
            f"# Uitgangspuntendocument: {self.topic}",
            "",
            f"*Aangemaakt op: {self.created_at[:10]} via Socratische Chat (Modus 1)*",
            "",
            "---",
            "",
            "## 1. Kernhypothese & Thesis",
            user_msgs[0] if len(user_msgs) > 0 else self.topic,
            "",
            "## 2. Inhoudelijke Hoofdlijnen & Voorbeelden",
            user_msgs[1] if len(user_msgs) > 1 else "Zie chat historie.",
            "",
            "## 3. Afbakening & Context",
            user_msgs[2] if len(user_msgs) > 2 else "Geen specifieke afbakeningsnotities.",
            "",
            "---",
            "",
            "## 4. Volledig Gespreksverslag",
        ]
        for m in self.messages:
            prefix = "**Edwin (Auteur)**:" if m["role"] == "user" else "**Onderzoeker (AI)**:"
            lines.append(f"{prefix}\n{m['content']}\n")

        return "\n".join(lines)


# In-memory sessieopslag
SESSIONS: dict[str, BrainstormSession] = {}


def start_brainstorm_session(session_id: str, topic: str) -> BrainstormSession:
    sess = BrainstormSession(session_id, topic)
    SESSIONS[session_id] = sess
    return sess


def get_brainstorm_session(session_id: str) -> BrainstormSession | None:
    return SESSIONS.get(session_id)
