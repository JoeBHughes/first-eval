import csv
from pathlib import Path

import score

ROOT = Path(__file__).parent.parent
with open(ROOT / "tasks.csv", newline="", encoding="utf-8") as f:
    TASKS = {t["task_id"]: t for t in csv.DictReader(f)}


def answer(code, lang="python"):
    return {"text": f"```{lang}\n{code}\n```"}


def test_passes_when_all_rules_hold():
    r = score.score_answer(answer('client.messages.create(model="claude-sonnet-5-5")'), TASKS["T01"])
    assert r["passed"]


def test_forbidden_model_fails():
    r = score.score_answer(answer('client.messages.create(model="claude-sonnet-4-5")'), TASKS["T01"])
    assert not r["avoids_forbidden"]
    assert r["forbidden_found"] == ["claude-sonnet-4-5"]


def test_alternatives_count_as_one_requirement():
    code = 'with client.messages.stream(model="m") as s:\n    for t in s.text_stream:\n        print(t)'
    assert score.score_answer(answer(code), TASKS["T02"])["includes_required"]


def test_syntax_error_and_missing_code():
    assert not score.score_answer(answer("def broken(:\n    pass"), TASKS["T01"])["parses"]
    assert not score.score_answer({"text": "No code here."}, TASKS["T01"])["has_code"]


def test_sample_files_score_as_documented():
    _, rows_a, _ = score.summarize(ROOT / "sample" / "answers_a.jsonl", TASKS)
    _, rows_b, _ = score.summarize(ROOT / "sample" / "answers_b.jsonl", TASKS)
    assert sum(r["passed"] for r in rows_a) == 4
    assert sum(r["passed"] for r in rows_b) == 7
