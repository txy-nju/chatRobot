import re
from pathlib import Path

from app.database import get_db


class SkillManager:
    """Manages skill CRUD operations, Markdown parsing and serialization."""

    @staticmethod
    def parse_markdown(content: str) -> dict:
        """Parse a skill Markdown file into structured fields.

        Returns a dict with keys: name, role, tone, rules (list), faq (list of {q, a}).
        """
        result = {
            "name": "",
            "role": "",
            "tone": "",
            "rules": [],
            "faq": [],
            "raw": content,
        }

        # Extract skill name from H1 heading
        h1_match = re.match(r"^#\s+Skill:\s*(.+)$", content.strip(), re.MULTILINE)
        if h1_match:
            result["name"] = h1_match.group(1).strip()

        # Extract sections by ## headings
        sections = re.split(r"\n##\s+", "\n" + content)
        for section in sections:
            section = section.strip()
            if section.startswith("角色"):
                result["role"] = section.split("\n", 1)[1].strip() if "\n" in section else ""
            elif section.startswith("口吻"):
                result["tone"] = section.split("\n", 1)[1].strip() if "\n" in section else ""
            elif section.startswith("回复规则"):
                body = section.split("\n", 1)[1] if "\n" in section else ""
                result["rules"] = [r.strip().lstrip("0123456789. ") for r in body.strip().split("\n") if r.strip()]
            elif section.startswith("知识库"):
                body = section.split("\n", 1)[1] if "\n" in section else ""
                faq = []
                current_q = ""
                current_a = ""
                for line in body.strip().split("\n"):
                    line = line.strip()
                    if line.startswith("- Q:") or line.startswith("Q:"):
                        if current_q:
                            faq.append({"q": current_q, "a": current_a.strip()})
                        current_q = line.split(":", 1)[1].strip() if ":" in line else line
                        current_a = ""
                    elif line.startswith("- A:") or line.startswith("A:"):
                        current_a = line.split(":", 1)[1].strip() if ":" in line else line
                    elif current_a:
                        current_a += "\n" + line
                if current_q:
                    faq.append({"q": current_q, "a": current_a.strip()})
                result["faq"] = faq

        return result

    @staticmethod
    def serialize_to_markdown(data: dict) -> str:
        """Serialize structured skill data back to Markdown format."""
        lines = [f"# Skill: {data.get('name', 'Untitled')}", ""]

        if data.get("role"):
            lines.append("## 角色")
            lines.append(data["role"])
            lines.append("")

        if data.get("tone"):
            lines.append("## 口吻")
            lines.append(data["tone"])
            lines.append("")

        rules = data.get("rules", [])
        if rules:
            lines.append("## 回复规则")
            for i, rule in enumerate(rules, 1):
                lines.append(f"{i}. {rule}")
            lines.append("")

        faq = data.get("faq", [])
        if faq:
            lines.append("## 知识库")
            for entry in faq:
                q = entry.get("q", entry.get("Q", ""))
                a = entry.get("a", entry.get("A", ""))
                lines.append(f"- Q: {q}")
                lines.append(f"- A: {a}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    async def create(name: str, content: str = "", is_active: bool = False) -> int:
        db = await get_db()
        try:
            # If this is the first skill or requested as active, deactivate others
            if is_active:
                await db.execute("UPDATE skills SET is_active = 0")

            cursor = await db.execute(
                "INSERT INTO skills (name, content, is_active) VALUES (?, ?, ?)",
                (name, content, 1 if is_active else 0),
            )
            await db.commit()
            return cursor.lastrowid
        finally:
            await db.close()

    @staticmethod
    async def get_all() -> list[dict]:
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT id, name, content, is_active, created_at, updated_at FROM skills ORDER BY updated_at DESC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()

    @staticmethod
    async def get_by_id(skill_id: int) -> dict | None:
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT id, name, content, is_active, created_at, updated_at FROM skills WHERE id = ?",
                (skill_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await db.close()

    @staticmethod
    async def get_active() -> dict | None:
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT id, name, content, is_active, created_at, updated_at FROM skills WHERE is_active = 1 LIMIT 1"
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await db.close()

    @staticmethod
    async def update(skill_id: int, name: str | None = None, content: str | None = None, is_active: bool | None = None) -> bool:
        db = await get_db()
        try:
            if is_active:
                await db.execute("UPDATE skills SET is_active = 0")

            updates = []
            params = []
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if content is not None:
                updates.append("content = ?")
                params.append(content)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)

            if not updates:
                return False

            updates.append("updated_at = datetime('now')")
            params.append(skill_id)

            await db.execute(
                f"UPDATE skills SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            await db.commit()
            return True
        finally:
            await db.close()

    @staticmethod
    async def delete(skill_id: int) -> bool:
        db = await get_db()
        try:
            # Check if it's the only active skill
            skill = await db.execute("SELECT is_active FROM skills WHERE id = ?", (skill_id,))
            row = await skill.fetchone()
            if row and row["is_active"]:
                count = await db.execute("SELECT COUNT(*) as cnt FROM skills")
                total = (await count.fetchone())["cnt"]
                if total <= 1:
                    return False  # Cannot delete the only active skill

            await db.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
            await db.commit()
            return True
        finally:
            await db.close()
