# Write your first eval in 30 minutes

An eval tells you how often a model gets a task right. This tutorial walks you through a small one that tests how well a Claude model writes Claude API code. You'll write tasks, collect answers, score them with fixed rules and compare two runs.

Independent project by Joe Hughes. Not affiliated with or endorsed by Anthropic.

## What you'll build

| Step | Time | What happens |
|---|---|---|
| 1. Set up | 5 minutes | Download the kit and install one package |
| 2. Score the sample answers | 5 minutes | Run the scorer with no API key, to see how it works |
| 3. Write your own tasks | 5 minutes | Edit `tasks.csv` |
| 4. Collect answers | 5 minutes | An automated script sends each task to a model |
| 5. Score and read the results | 5 minutes | The scorer applies the same rules to every answer |
| 6. Change one thing and compare | 5 minutes | Run again and see what moved |

## Why fixed rules come first

An eval needs a grader. You can use another model as the grader, but start with rules a script can check, such as "the code parses" or "the code calls `count_tokens`." Fixed rules give the same answer every time, so when a score changes, the model or your prompt changed. The grader didn't.

This approach comes from a larger audit of 240 Claude answers to 30 coding tasks. In that audit, an automated script found that 108 of 114 answers written without web search (95%) named a model the Models API no longer listed. A rule as simple as "doesn't contain an old model ID" caught it.

## 1. Set up

You need Python 3.9 or later.

```bash
git clone https://github.com/JoeBHughes/first-eval.git
cd first-eval
pip install anthropic
```

## 2. Score the sample answers

The `sample` folder holds two small answer files written for this tutorial. They aren't real model output. They exist so you can see the scorer work before you spend anything on API calls.

```bash
python score.py sample/answers_a.jsonl sample/answers_b.jsonl
```

Part of the output:

```text
sample/answers_a.jsonl  (model: sample-prompt-a)
  Passed all rules: 4 of 8 (50%)
  FAIL T01 sample 1: uses claude-sonnet-4-5
  FAIL T04 sample 1: missing tool_result
  FAIL T07 sample 1: missing cache_control
  FAIL T08 sample 1: Python doesn't parse

sample/answers_b.jsonl  (model: sample-prompt-b)
  Passed all rules: 7 of 8 (88%)
  FAIL T08 sample 1: Python doesn't parse
```

Each FAIL line says which rule broke. That's the point of an eval: a number you can trust, plus the reason behind it.

## 3. Write your own tasks

Open `tasks.csv`. Each row is one task:

| Column | What it holds | Example |
|---|---|---|
| `task_id` | A short ID | `T06` |
| `prompt` | What you ask the model | Write Python that counts the tokens in a prompt. |
| `must_include` | Text the code must contain. Separate items with `;`. Use `\|` for "either one counts." | `count_tokens` |
| `must_not_include` | Text the code must not contain | `claude-sonnet-4-5;claude-3-` |

Write rules for what a correct answer must do. Avoid rules about style, because two correct answers can look different.

## 4. Collect answers

Set your API key, then check the plan with a dry run. The dry run makes no API calls.

```bash
export ANTHROPIC_API_KEY=...        # PowerShell: $env:ANTHROPIC_API_KEY = Read-Host "Key"
python run_eval.py --model claude-sonnet-5-5 --dry-run
```

Then run it for real:

```bash
python run_eval.py --model claude-sonnet-5-5 --samples 2 --out answers_a.jsonl
```

Use a model ID that the Models API lists today. The script takes two samples per task by default, because a model can answer the same prompt differently. It refuses to make more than 40 calls unless you add `--yes`.

## 5. Score and read the results

```bash
python score.py answers_a.jsonl --csv results.csv
```

Read the output in this order:

1. The overall pass count. It's your headline number.
2. The four rule lines. They show whether failures come from broken code, missing features or forbidden text.
3. The FAIL lines. Open a few of the failing answers in `answers_a.jsonl` and read them. A human reviewer should check that each failure is real before you trust the number.

## 6. Change one thing and compare

Change one thing and run again. For example, add "Use the current model ID from the Models API" to every prompt, or test a different model.

```bash
python run_eval.py --model claude-sonnet-5-5 --out answers_b.jsonl
python score.py answers_a.jsonl answers_b.jsonl
```

The scorer prints both runs and a table of passes per task. Change one thing at a time. If you change two, you won't know which one moved the score.

## Where to go next

- Add more samples per task. With two samples, one bad answer moves a task's score by half.
- Add web search or tools to `run_eval.py`, then compare runs with and without them.
- Add a second grader for judgments rules can't make, such as "is this explanation correct?" Use a different model as that grader, and have a human reviewer check a sample of its scores.
- Run the eval on a schedule, so you see when a new model or a docs change moves the score.

## Files

| File | What it does |
|---|---|
| `tasks.csv` | Eight sample tasks about the Claude API |
| `run_eval.py` | Sends each task to a model and saves the answers |
| `score.py` | Applies fixed rules to each answer and prints a summary |
| `sample/` | Two illustrative answer files for step 2 |
| `tests/` | Tests for the scorer. Run them with `python -m pytest tests` |

## License

MIT
