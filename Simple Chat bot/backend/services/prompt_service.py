"""채팅방별 시스템 프롬프트 만들기. 긴 문장은 knowledge/ 폴더의 파일에서 읽는다."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from string import Template

from schemas.room import Persona

WEEKDAY_KO = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def today_ko(now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"{now.year}년 {now.month}월 {now.day}일 {WEEKDAY_KO[now.weekday()]}"


class PromptService:
    def __init__(self, knowledge_dir: Path):
        read = lambda name: (knowledge_dir / name).read_text(encoding="utf-8")
        self.bootcamp_info = read("bootcamp_info.md").strip()
        self.matjip_notes = read("matjip_notes.md").strip()
        self.gk = Template(read("gk_system.md"))
        self.sky = Template(read("sky_system.md"))
        self.persona = Template(read("persona_system.md"))
        self.donggyu_chat = read("donggyu_chat.md")

    def manager(self, notes: str = "", food_context: str = "", now: datetime | None = None) -> str:
        food = f"\n{self.matjip_notes}\n\n{food_context}\n" if food_context else ""
        return self.gk.substitute(bootcamp_info=self.bootcamp_info, notes=notes.strip() or "(없음)",
                                  food_context=food, today=today_ko(now))

    def weather(self, weather_data: str, now: datetime | None = None) -> str:
        return self.sky.substitute(weather_data=weather_data, today=today_ko(now))

    def persona_prompt(self, p: Persona, now: datetime | None = None) -> str:
        c = p.company
        prompt = self.persona.substitute(
            name=p.name, age=p.age, sex="여성" if p.sex == "여자" else "남성", job=p.job, district=p.district,
            housing=p.housing, education=p.education, marital=p.marital, family=p.family,
            company=c.company, company_about=c.about, company_role=c.role, company_place=c.place,
            extra_company_note=f"- {c.note}\n" if c.note else "", bio=p.bio, style=p.style, today=today_ko(now))

        return prompt + ("\n" + self.donggyu_chat if p.id == "donggyu" else "")
