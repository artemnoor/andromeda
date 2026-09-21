"""Human-gated jev-align proposal workflow for semantic artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from andromeda.modules.semantic.contracts.review import SemanticReviewQueueItem
from andromeda.modules.semantic.contracts.review_artifacts import SemanticMappingProposal, SemanticReviewAction
from andromeda.modules.semantic.services.review_workflow import SemanticReviewWorkflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run explicit export/review/publish jev-align workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)
    export = subparsers.add_parser("export")
    export.add_argument("--queue", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--feature-id", required=True)
    export.add_argument("--tool-version", default="jev-align.v1")
    review = subparsers.add_parser("review")
    review.add_argument("--manifest", type=Path, required=True)
    review.add_argument("--proposal-id", required=True)
    review.add_argument("--action", choices=tuple(action.value for action in SemanticReviewAction), required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--source-hash")
    publish = subparsers.add_parser("publish")
    publish.add_argument("--manifest", type=Path, required=True)
    publish.add_argument("--output", type=Path, required=True)
    publish.add_argument("--artifact-id", required=True)
    publish.add_argument("--diff-report", action="store_true")
    args = parser.parse_args(argv)

    workflow = SemanticReviewWorkflow()
    if args.command == "export":
        queue = SemanticReviewQueueItem.model_validate(
            json.loads(args.queue.read_text(encoding="utf-8")), strict=False
        )
        feature = next((value for value in queue.values if value.feature_id == args.feature_id), None)
        if feature is None:
            parser.error("the requested feature must be present in the typed review queue row")
        proposal = workflow.propose(queue, feature_id=args.feature_id, feature=feature, tool_version=args.tool_version)
        _write_manifest(args.output, (proposal,))
        return 0

    proposals = _read_manifest(args.manifest)
    if args.command == "review":
        selected = next((proposal for proposal in proposals if proposal.proposal_id == args.proposal_id), None)
        if selected is None:
            parser.error("proposal was not found")
        updated = workflow.review(
            selected,
            SemanticReviewAction(args.action),
            reviewer=args.reviewer,
            current_source_hash=args.source_hash,
        )
        _write_manifest(args.manifest, tuple(updated if proposal.proposal_id == args.proposal_id else proposal for proposal in proposals))
        return 0

    artifact = workflow.publish(
        proposals,
        artifact_id=args.artifact_id,
        semantic_version=proposals[0].semantic_version if proposals else "semantic-taxonomy.v1",
        classifier_version=proposals[0].classifier_version if proposals else "semantic-classifier.v1",
        diff_report_present=args.diff_report,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(artifact.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return 0


def _write_manifest(path: Path, proposals: tuple[SemanticMappingProposal, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([proposal.model_dump(mode="json") for proposal in proposals], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _read_manifest(path: Path) -> tuple[SemanticMappingProposal, ...]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("review manifest must be a list")
    return tuple(SemanticMappingProposal.model_validate(row, strict=False) for row in rows)


if __name__ == "__main__":
    raise SystemExit(main())
