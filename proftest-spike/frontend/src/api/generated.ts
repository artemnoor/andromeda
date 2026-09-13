/**
 * Public aliases used by the frontend.
 *
 * The source of truth is the generated OpenAPI module. Keeping aliases here
 * gives feature code readable names without duplicating the HTTP contract.
 */

import type { components as OpenApiComponents } from "./generated.openapi";

export type { components, operations, paths } from "./generated.openapi";

type Schemas = OpenApiComponents["schemas"];

export type AreaCode = Schemas["AreaCode"];
export type ActivityCode = Schemas["ActivityCode"];
export type AnswerOption = Schemas["AnswerOptionResponse"];
export type QuestionResponse = Schemas["QuestionResponse"];
export type AnswerPayload = Schemas["AnswerPayload"];
export type AdaptiveAnswerPayload = Schemas["AdaptiveAnswerPayload"];
export type TestAnswersRequest = Schemas["TestAnswersRequest"];
export type BootstrapResponse = Schemas["BootstrapResponse"];
export type AdaptiveDimension = Schemas["AdaptiveDimensionResponse"];
export type AdaptiveOption = Schemas["AdaptiveOptionResponse"];
export type AdaptiveQuestion = Schemas["AdaptiveQuestionResponse"];
export type AdaptiveResponse = Schemas["AdaptiveResponse"];
export type ProgressResponse = Schemas["ProgressResponse"];
export type PreviewResponse = Schemas["PreviewResponse"];
export type DistinctiveSubject = Schemas["DistinctiveSubjectResponse"];
export type CatalogProgram = Schemas["CatalogProgramResponse"];
export type ScoreBreakdown = Schemas["ScoreBreakdownResponse"];
export type Reason = Schemas["ReasonResponse"];
export type Metric = Schemas["MetricResponse"];
export type Recommendation = Schemas["RecommendationResponse"];
export type ResultsResponse = Schemas["ResultsResponse"];
export type ErrorResponse = Schemas["ErrorResponse"];
