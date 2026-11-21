#!/usr/bin/env python3
"""Score saved answers against fixed rules and print a summary.

An automated script (this one) applies the same rules to every answer, so two runs
can be compared fairly. No model grades the answers.

Rules for each answer:
  1. It contains at least one code block.
  2. Every Python code block parses.
  3. The code contains each must_include item. "a|b" means either a or b counts.
  4. The code contains none of the must_not_include items.
"""
import argparse
import ast
import csv
import json
import re
import sys
from collections import defaultdict

BLOCK_RE = re.compile(r"```(\w*)\n(.*?)```", re.S)


def split_items(cell):
    return [x.strip() for x in (cell or "").split(";") if x.strip()]


def code_blocks(text):
    return BLOCK_RE.findall(text)


def score_answer(answer, task):
    blocks = code_blocks(answer["text"])
    code = "\n".join(body for _, body in blocks)
    checks = {"has_code": bool(blocks)}

    py = [body for lang, body in blocks if lang.lower() in ("python", "py", "")]
    parses = True
    for body in py:
        try:
            ast.parse(body)
        except SyntaxError:
            parses = False
    checks["parses"] = bool(py) and parses

    missing = [item for item in split_items(task["must_include"])
               if not any(opt in code for opt in item.split("|"))]
    found_bad = [item for item in split_items(task["must_not_include"]) if item in code]
    checks["includes_required"] = not missing
    checks["avoids_forbidden"] = not found_bad
    passed = all(checks.values())
    return {**checks, "passed": passed, "missing": missing, "forbidden_found": found_bad}


def load_answers(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def pct(n, d):
    return f"{n} of {d} ({round(100 * n / d)}%)" if d else "0 of 0"


def summarize(path, tasks):
    answers = load_answers(path)
    rows, by_task = [], defaultdict(lambda: [0, 0])
    for a in answers:
        r = score_answer(a, tasks[a["task_id"]])
        rows.append({"task_id": a["task_id"], "sample": a.get("sample"), **r})
        by_task[a["task_id"]][0] += r["passed"]
        by_task[a["task_id"]][1] += 1
    return answers, rows, by_task


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("answers", nargs="+", help="one answers file, or two to compare")
    p.add_argument("--tasks", default="tasks.csv")
    p.add_argument("--csv", help="write per-answer results to this CSV file")
    args = p.parse_args(argv)

    with open(args.tasks, newline="", encoding="utf-8") as f:
        tasks = {t["task_id"]: t for t in csv.DictReader(f)}

    results = [summarize(path, tasks) for path in args.answers]
    for path, (answers, rows, by_task) in zip(args.answers, results):
        model = answers[0].get("model", "?") if answers else "?"
        passed = sum(r["passed"] for r in rows)
        print(f"\n{path}  (model: {model})")
        print(f"  Passed all rules: {pct(passed, len(rows))}")
        for rule in ("has_code", "parses", "includes_required", "avoids_forbidden"):
            print(f"    {rule:18} {pct(sum(r[rule] for r in rows), len(rows))}")
        for r in rows:
            if not r["passed"]:
                why = []
                if r["missing"]:
                    why.append("missing " + ", ".join(r["missing"]))
                if r["forbidden_found"]:
                    why.append("uses " + ", ".join(r["forbidden_found"]))
                if not r["parses"]:
                    why.append("Python doesn't parse")
                print(f"  FAIL {r['task_id']} sample {r['sample']}: {'; '.join(why) or 'no code block'}")

    if len(results) == 2:
        print("\nTask    " + "  ".join(f"{p:>18}" for p in args.answers))
        for tid in tasks:
            cells = []
            for _, _, by_task in results:
                ok, n = by_task.get(tid, [0, 0])
                cells.append(f"{ok} of {n}".rjust(18))
            print(f"{tid:8}" + "  ".join(cells))

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["file", "task_id", "sample", "has_code", "parses", "includes_required",
                        "avoids_forbidden", "passed", "missing", "forbidden_found"])
            for path, (_, rows, _) in zip(args.answers, results):
                for r in rows:
                    w.writerow([path, r["task_id"], r["sample"], r["has_code"], r["parses"],
                                r["includes_required"], r["avoids_forbidden"], r["passed"],
                                ";".join(r["missing"]), ";".join(r["forbidden_found"])])
        print(f"\nWrote per-answer results to {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
