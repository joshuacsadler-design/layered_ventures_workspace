import os, sys, datetime
from pathlib import Path

try:
    from openai import OpenAI
except Exception:
    print("ERROR: missing openai SDK. Install: py -m pip install --upgrade openai", file=sys.stderr)
    raise

def now_dates():
    dt = datetime.datetime.now()
    return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m-%d_%H-%M-%S")

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def extract_block(text: str, start: str, end: str):
    s = text.find(start)
    if s == -1:
        return None
    e = text.find(end, s + len(start))
    if e == -1:
        return None
    return text[s + len(start):e].strip()

def main():
    if len(sys.argv) < 3:
        print("usage: lv_chat_client.py <root> <project>", file=sys.stderr)
        sys.exit(2)

    root = Path(sys.argv[1]).resolve()
    project = sys.argv[2].strip()

    prompt = sys.stdin.read().strip()
    if not prompt:
        print("ERROR: empty prompt", file=sys.stderr)
        sys.exit(2)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set. Run: setx OPENAI_API_KEY \"yourkey\" and reopen PowerShell.", file=sys.stderr)
        sys.exit(2)

    ops_root = root / "lv_ops" / "ops"
    logs_dir = ops_root / "logs" / project
    events_dir = ops_root / "events" / project
    capsule_file = ops_root / "context-capsule.md"
    decision_file = ops_root / "decision-log.md"

    ensure_dir(logs_dir)
    ensure_dir(events_dir)

    today, ts = now_dates()
    log_file = logs_dir / f"{today}.md"
    events_file = events_dir / f"{today}.md"

    if not capsule_file.exists():
        capsule_file.write_text(
f"""# context-capsule
date: {today}
timezone: america/new_york

## active-objective (one sentence)

## current-workstream
project: {project}
repo_path: {root}
branch:

## what we finished last

## current blockers / errors (verbatim)

## decisions locked today

## next actions (exact)
1)

## artifacts touched
- file:
""", encoding="utf-8"
        )

    if not decision_file.exists():
        decision_file.write_text("# decision-log\n", encoding="utf-8")

    if not events_file.exists():
        events_file.write_text(f"# opslog events: {project} ({today})\n", encoding="utf-8")

    system = f"""You are the ops logger for Layered Ventures. Project={project}.
Always end your response with these EXACT blocks (even if empty):

---context-capsule---
<complete updated context-capsule.md contents (full replacement)>
---end-context-capsule---

---decision-log---
- decision: ...
  reason: ...
  scope: global | project:{project}
---end-decision-log---

---opslog-events---
- type: decision|change|milestone|risk|todo|note
  project: {project}
  detail: <one-line>
  files: [optional list]
---end-opslog-events---

Rules:
- Capsule must be a full replacement, not a diff.
- Decisions are locked-in choices only.
- Events must capture the important details needed to jog memory and trace changes.
"""

    client = OpenAI()
    resp = client.responses.create(
        model="gpt-5.2",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )

    out = (resp.output_text or "").strip()

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"\n---\n# session {ts}\n\n## user\n{prompt}\n\n## assistant\n{out}\n")

    cap = extract_block(out, "---context-capsule---", "---end-context-capsule---")
    dec = extract_block(out, "---decision-log---", "---end-decision-log---")
    ev  = extract_block(out, "---opslog-events---", "---end-opslog-events---")

    if cap:
        capsule_file.write_text(cap + "\n", encoding="utf-8")

    if dec:
        with decision_file.open("a", encoding="utf-8") as f:
            f.write(f"\n## {today}\n{dec}\n")

    if ev:
        with events_file.open("a", encoding="utf-8") as f:
            f.write(f"\n---\n{ev}\n")

    print(out)

if __name__ == "__main__":
    main()
