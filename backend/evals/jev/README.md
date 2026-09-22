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

The calibration scripts are Andromeda-owned exporters/loaders around the
upstream jevcal APIs. Calibration, threshold selection and ECE are not
reimplemented locally. The committed
`config/jev/locks/decisions.v1.lock.json` is a raw upstream jevcal lock with a
hash/version sidecar; the current fixture artifact is intentionally not
production-calibrated and does not enable runtime Jev.

Useful offline checks from `backend/`:

```text
uv run --locked --extra evaluation --extra dev python scripts/jevcal_export.py --output .tmp/jevcal-rows.jsonl --questions-output .tmp/jevcal-questions.yaml --check
uv run --locked --extra evaluation --extra dev python scripts/jevcal_calibrate.py --source fixture --check
uv run --locked --extra evaluation --extra dev python scripts/evaluate_jev_ecosystem.py --output .tmp/jev-report.json --check
```

`jev-align` uses the pinned upstream `ClimbSession` for uncertainty
acquisition and GEPA optimization. Andromeda's semantic review workflow still
requires a human accept/reject decision before a versioned semantic artifact
can be published. System One remains benchmark-only. Production calibration
requires an external, sufficiently sized corpus; fixture sample counts are
not accuracy or ECE evidence.
