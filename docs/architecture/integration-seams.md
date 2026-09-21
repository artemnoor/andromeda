# Integration seams

## Jev

Implement adapters for:

- `DecisionPolicyPort` → `JevDecisionPolicy`;
- `SemanticClassifierPort` → `JevSemanticClassifier`, if model-assisted
  enrichment is later approved;
- `ResponsePolicyPort` → `JevResponsePolicy`.

These adapters belong at the composition/integration boundary. Domain,
analytics, admissions and presentation contracts must not import a Jev SDK.
The deterministic implementations remain the testable default.

## MAX

MAX should send an update to `POST /assistant/query`, preserve the returned
`session_id`/`revision`, and map `ResponseEnvelope` to text, image, PDF,
buttons or a Mini App. It should not implement NLP, entity resolution,
analytics, admission fit or response selection.

## Telegram

Telegram is the reference transport. Free-form messages now use the same
assistant endpoint. Existing commands and signed OG routes remain compatibility
adapters until parity is proven. Its local store contains only an encrypted
opaque cookie and query-session metadata; it does not become a business-state
source of truth.

## Web and OG

The Web `queryAssistant` client and `AssistantPage` use the same endpoint.
Existing OG routes retain HMAC/timestamp validation and server-side cookie
forwarding. New generic renderers must consume envelope data and evidence; they
must not query canonical repositories or recalculate metrics.
