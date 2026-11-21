#!/usr/bin/env python3
"""Send each task to a Claude model and save the answers for scoring.

An automated script (this one) asks the model each task the number of times you set,
then writes one JSON line per answer. It never scores anything. score.py does that.
"""
import argparse
import csv
import json
import os
import sys
import time


def load_tasks(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ask(client, model, prompt, max_tokens, tries=3):
    for attempt in range(tries):
        try:
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as err:  # the script retries any API error twice, then gives up
            if attempt == tries - 1:
                raise
            wait = 2 ** attempt * 5
            print(f"  error: {err}. Retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--model", required=True,
                   help="model ID to test, such as claude-sonnet-5-5. Check the Models API for current IDs")
    p.add_argument("--tasks", default="tasks.csv")
    p.add_argument("--samples", type=int, default=2, help="answers per task. Models vary, so take more than one")
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--out", default="answers.jsonl")
    p.add_argument("--dry-run", action="store_true", help="list the calls without making them")
    p.add_argument("--yes", action="store_true", help="allow more than 40 API calls")
    args = p.parse_args(argv)

    tasks = load_tasks(args.tasks)
    calls = len(tasks) * args.samples
    print(f"{len(tasks)} tasks x {args.samples} samples = {calls} calls to {args.model}")
    if args.dry_run:
        for t in tasks:
            print(f"  {t['task_id']}: {t['prompt'][:70]}")
        return 0
    if calls > 40 and not args.yes:
        print("More than 40 calls. Add --yes to confirm the cost.", file=sys.stderr)
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
        return 2

    import anthropic
    client = anthropic.Anthropic()
    with open(args.out, "w", encoding="utf-8") as out:
        for t in tasks:
            for s in range(1, args.samples + 1):
                msg = ask(client, args.model, t["prompt"], args.max_tokens)
                text = "".join(b.text for b in msg.content if b.type == "text")
                out.write(json.dumps({
                    "task_id": t["task_id"], "sample": s, "model": args.model,
                    "stop_reason": msg.stop_reason, "text": text,
                    "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens,
                }) + "\n")
                print(f"  {t['task_id']} sample {s}: {msg.stop_reason}")
    print(f"Saved {calls} answers to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
