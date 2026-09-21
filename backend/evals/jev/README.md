# Jev evaluation artifacts

This directory is evaluation-only. Nothing under `backend/evals` is imported by
the application composition root or by production API routes.

`decision-cases.v1.jsonl` is a synthetic, versioned corpus. It contains no
production profiles, credentials, cookies, or source snapshots. `train`, `dev`,
and `heldout` splits are kept immutable for a calibration run. The labels are
the expected bounded decisions, not factual catalog answers.

The optional System One adapter is invoked only by an explicit evaluation
command. Its report stores case IDs, typed metadata, usage and sanitized
structured output; it does not store raw state or provider debug transcripts.
