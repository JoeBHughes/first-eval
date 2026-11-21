# Write your first eval in 30 minutes

An eval tells you how often a model gets a task right. This tutorial walks you through a small one that tests how well a Claude model writes Claude API code. You'll write tasks, collect answers, score them with fixed rules and compare two runs.

Independent project by Joe Hughes. Anthropic has not reviewed or endorsed this project.

## What you'll build

| Step | Time | What happens |
|---|---|---|
| 1. Set up | 5 minutes | Download the kit and install two packages |
| 2. Score the practice answers | 5 minutes | Run the scorer with no API key, to see how it works |
| 3. Write your own tasks | 5 minutes | Edit `tasks.csv` |
| 4. Collect answers | 5 minutes | An automated script sends each task to a model |
| 5. Score and read the results | 5 minutes | The scorer applies the same rules to every answer |
| 6. Change one thing and compare | 5 minutes | Run again and see what moved |

## Why fixed rules come first

An eval needs a grader. You can use another model as the grader, but start with rules a script can check, such as "the code has no syntax errors" or "the code calls `count_tokens`." Fixed rules give the same answer every time. When a score changes, you know the model or your prompt changed.

This approach comes from a larger audit of 240 Claude answers to 30 coding tasks. In that audit, an automated script found that 108 of 114 answers written without web search (95%) named a model the Models API no longer listed. A rule as simple as "doesn't contain an old model ID" caught it.

## 1. Set up

You need Python 3.9 or later. On Windows, type `py` wherever this guide says `python`.

```bash
git clone https://github.com/JoeBHughes/first-eval.git
cd first-eval
pip install anthropic pytest
```

No Git? On the repository page, click **Code**, then **Download ZIP**. Unzip it and open a terminal in the `first-eval` folder.

## 2. Score the practice answers

The `sample` folder holds two practice answer files written for this tutorial. They aren't real model output. They let you see the scorer work before you spend anything on API calls.

Answer files use JSONL format: one answer per line, written in JSON.

```bash
python score.py sample/answers_a.jsonl sample/answers_b.jsonl
```

The output for the first file:

```text
sample/answers_a.jsonl  (model: sample-prompt-a)
  Passed all rules: 4 of 8 (50%)
    has_code           8 of 8 (100%)
    parses             7 of 8 (88%)
    includes_required  6 of 8 (75%)
    avoids_forbidden   7 of 8 (88%)
  FAIL T01 sample 1: uses claude-sonnet-4-5
  FAIL T04 sample 1: missing tool_result
  FAIL T07 sample 1: missing cache_control
  FAIL T08 sample 1: Python doesn't parse
```

The output has three parts:

- The pass count. An answer passes only if it meets every rule.
- One line per rule, counting the answers that met it.
- One FAIL line per failed answer, naming the rule it broke.

The second file passes 7 of 8 (88%). At the bottom, the scorer prints a table that compares the two files task by task.

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

Set your API key, then check the plan with a dry run. The dry run lists the calls without making them.

```bash
export ANTHROPIC_API_KEY=...        # PowerShell: $env:ANTHROPIC_API_KEY = Read-Host "Key"
python run_eval.py --model claude-sonnet-5-5 --dry-run
```

Then run it for real:

```bash
python run_eval.py --model claude-sonnet-5-5 --out answers_a.jsonl
```

Use a model ID that the Models API lists today. The script asks for two answers per task by default, because a model can answer the same prompt differently. Change that number with `--samples`. The script refuses to make more than 40 calls unless you add `--yes`.

## 5. Score and read the results

```bash
python score.py answers_a.jsonl --csv results.csv
```

Read the output in this order:

1. The pass count. It's your headline number.
2. The rule lines. They show where failures come from. `has_code` counts answers with at least one code block. `parses` counts code with no syntax errors. `includes_required` checks the `must_include` column, and `avoids_forbidden` checks the `must_not_include` column.
3. The FAIL lines. Open a few of the failing answers in `answers_a.jsonl` and read them. A human reviewer should confirm each failure is real before you trust the number.

The `--csv` option saves one row per answer, so you can sort and filter the results in a spreadsheet.

## 6. Change one thing and compare

Change one thing and run again. For example, add "Use the current model ID from the Models API" to every prompt, or test a different model.

```bash
python run_eval.py --model claude-sonnet-5-5 --out answers_b.jsonl
python score.py answers_a.jsonl answers_b.jsonl
```

The scorer prints both runs and a table of passes per task. Change one thing at a time. If you change two, you won't know which one moved the score.

## What fixed rules miss

Fixed rules check text. They can't check behavior. Practice answer T08 catches `RateLimitError` but never retries the call. If you fixed its syntax error, it would pass every rule and still fail the task.

When you find an answer like that, you have two choices:

- Tighten the rule. For T08, require a loop or the SDK's `max_retries` setting.
- Add a second grader for judgments rules can't make, such as "does this code retry?" Use a different model as that grader, and have a human reviewer check a sample of its scores.

## Where to go next

- Ask for more answers per task. With two answers, one bad answer moves a task's score by half.
- Add web search or tools to `run_eval.py`, then compare runs with and without them.
- Run the eval on a schedule, so you see when a new model or a docs change moves the score.

## Files

| File | What it does |
|---|---|
| `tasks.csv` | Eight sample tasks about the Claude API |
| `run_eval.py` | Sends each task to a model and saves the answers |
| `score.py` | Applies fixed rules to each answer and prints a summary |
| `sample/` | Two practice answer files for step 2 |
| `tests/` | Tests for the scorer. Run them with `python -m pytest tests` |

## License

MIT
