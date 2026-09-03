# SMTYX Conformance Benchmark

The benchmark tests semantic interoperability, not factual knowledge or writing style.

## Procedure
1. Give `prompts/AI_CONFORMANCE_PROMPT.md` to the target AI.
2. Feed every `input` from `conformance_cases.jsonl`.
3. Save one JSON answer per line in a file such as `claude_answers.jsonl`.
4. Run `python scripts/score_model_outputs.py claude_answers.jsonl`.

## What is scored
- intent
- object
- protocol status
- explicit permission scopes
- selected learning-stage fields where applicable

Confidence is requested so calibration can be studied later, but v0.2 does not score it against a single oracle value.
