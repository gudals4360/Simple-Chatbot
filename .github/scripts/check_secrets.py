#!/usr/bin/env python3
"""API 키가 GitHub에 올라가는 걸 막는 검사기.

사용법
  python .github/scripts/check_secrets.py            # 저장소의 모든 파일 검사 (GitHub Actions)
  python .github/scripts/check_secrets.py --staged   # 커밋하려고 올린 파일만 검사 (pre-commit 훅)

키처럼 보이는 값이나 .env 파일을 찾으면 경고를 출력하고 실패(종료 코드 1)한다.
"""
from __future__ import annotations

import re
import subprocess
import sys

# 실제 키의 생김새
PATTERNS = [
    ("Groq API 키", re.compile(r"gsk_[A-Za-z0-9]{20,}")),
    ("Google·Gemini API 키", re.compile(r"AIza[0-9A-Za-z_\-]{30,}")),
    ("OpenAI API 키", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("Anthropic API 키", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("GitHub 토큰", re.compile(r"(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}")),
]
# KEY=값 형태로 값이 채워진 경우 (.env 내용을 다른 파일에 붙여 넣은 경우 등)
ASSIGN = re.compile(r"^\s*(?:export\s+)?([A-Z0-9_]*(?:API_KEY|SECRET|TOKEN|PASSWORD))\s*[=:]\s*['\"]?([^'\"\s#]+)", re.M)
PLACEHOLDER = re.compile(r"^(?:your|xxx|<|\$|\.\.\.|changeme|example|none|null|여기)", re.I)
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".parquet", ".db", ".woff", ".woff2")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def files_to_check(staged: bool) -> list[str]:
    if staged:
        out = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    else:
        out = git("ls-files", "-z")
    return [f for f in out.split("\0") if f]


def read(path: str, staged: bool) -> str:
    try:
        if staged:
            return subprocess.run(["git", "show", f":{path}"], capture_output=True, check=True).stdout.decode("utf-8", "ignore")
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (OSError, subprocess.CalledProcessError):
        return ""


def mask(s: str) -> str:
    return s[:6] + "…" + s[-2:] if len(s) > 10 else "…"


def main() -> int:
    staged = "--staged" in sys.argv
    problems: list[str] = []
    for path in files_to_check(staged):
        name = path.rsplit("/", 1)[-1]
        if name == ".env" or (name.startswith(".env.") and name not in (".env.example", ".env.sample")):
            problems.append(f"{path}: .env 파일은 비밀 값이 들어 있어서 올리면 안 돼요.")
            continue
        if path.lower().endswith(SKIP_EXT):
            continue
        text = read(path, staged)
        for label, rx in PATTERNS:
            for m in rx.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                problems.append(f"{path}:{line}: {label}로 보이는 값 ({mask(m.group())})")
        for m in ASSIGN.finditer(text):
            value = m.group(2)
            if len(value) >= 8 and not PLACEHOLDER.match(value):
                line = text.count("\n", 0, m.start()) + 1
                problems.append(f"{path}:{line}: {m.group(1)}에 값이 채워져 있어요 ({mask(value)})")

    if not problems:
        print("✅ API 키 검사 통과: 올라갈 파일에 키가 없어요.")
        return 0

    print("\n🚨 경고: API 키가 GitHub에 올라갈 수 있어요!\n")
    for p in dict.fromkeys(problems):
        print("  - " + p)
    print("""
어떻게 하나요?
  1. 키는 backend/.env 에만 넣어 주세요. (.env는 .gitignore에 들어 있어서 올라가지 않아요)
  2. 코드·README·설정 파일에서 키를 지우고 다시 커밋해 주세요.
  3. 이미 GitHub에 올라갔다면, 지워도 기록에 남아요.
     바로 Groq(console.groq.com/keys)나 Google AI Studio(aistudio.google.com/apikey)에서
     그 키를 삭제하고 새 키를 발급받아 주세요.
""")
    return 1


if __name__ == "__main__":
    sys.exit(main())
