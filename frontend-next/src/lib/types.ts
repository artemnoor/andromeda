// API types — derived from the Andromeda OpenAPI contract (API.md / openapi.json).
// Mock fixtures in src/lib/mock conform to these shapes.

import type { components } from "./generated";

export type Provenance = {
  sourceKind?: string | null;
  sourceUrl?: string | null;
  capturedAt?: string | null;
  contentSha256?: string | null;
  locator?: string | null;
  sourceName?: string | null;
};

export type ProgramSummary = {
  id: string;
  directionId: string;
  code: string;
  name: string;
  educationYear: string;
  studyPlanUrl?: string | null;
  sourceUrl?: string | null;
};

export type ProgramListResponse = { items: ProgramSummary[] };

export type ProgramResponse = { program: ProgramSummary };

export type DisciplineArea = {
  code: string;
  name: string;
  description?: string | null;
  weight: string;
};

export type Discipline = {
  id: string;
  name: string;
  normalizedName: string;
  areaWeights: DisciplineArea[];
  primaryArea: string;
};

export type CurriculumItem = {
  id: string;
  discipline: Discipline;
  sourceName: string;
  hours: number;
  semester?: number | null;
  credits?: string | null;
  assessmentTypes?: string[] | null;
  sourcePosition?: number | null;
};

export type CurriculumResponse = {
  program: ProgramSummary;
  curriculumId: string;
  educationYear: string;
  sourceUrl?: string | null;
  capturedAt: string;
  items: CurriculumItem[];
};

export type ExamRequirement = {
  subject: string;
  sourceName?: string | null;
  minimumScore?: number | null;
  isChoice?: boolean | null;
  isRequired?: boolean | null;
  provenance?: Provenance | null;
};

export type QuotaResponse = {
  quotaType: string;
  sourceName?: string | null;
  places?: number | null;
  provenance?: Provenance | null;
};

export type CompetitionType =
  | "general"
  | "special_quota"
  | "separate_quota"
  | "targeted"
  | "bvi"
  | "other";

export type PassingScore = {
  scoreType?: string | null;
  competitionType?: CompetitionType | null;
  status: string;
  score?: string | null;
  provenance?: Provenance | null;
};

export type TuitionCost = {
  amount: string;
  currency: string;
  academicYear?: string | null;
  period?: string | null;
  studyForm?: string | null;
  isDiscounted?: boolean | null;
  provenance?: Provenance | null;
};

export type AdmissionOffering = {
  id: string;
  admissionYear: number;
  studyForm: string;
  fundingType: string;
  scope: "program" | "direction";
  places?: number | null;
  exams: ExamRequirement[];
  quotas: QuotaResponse[];
  passingScores: PassingScore[];
  tuition: TuitionCost[];
  provenance: Provenance[];
};

export type ProgramAdmissionsResponse = {
  program: ProgramSummary;
  programId: string;
  offerings: AdmissionOffering[];
};

export type AdmissionFitBreakdown = {
  minimumReadiness: number | null;
  passingReadiness: number | null;
  dataCompleteness: number | null;
};

export type AdmissionFitResponse = {
  status: "realistic" | "borderline" | "unlikely" | "insufficient_data";
  score: number;
  applicantTotalScore: string | null;
  dataQuality: string;
  breakdown: AdmissionFitBreakdown;
  reasons: string[];
  antiReasons: string[];
  dataGaps: string[];
};

export type AdmissionFitRequest = {
  version?: number;
  offeringId: string;
  applicant: {
    version: number;
    scores: { subject: string; score: number }[];
  };
};

export type ComparisonScope = "all" | "semester";

export type ComparisonRow = {
  discipline: string;
  semester?: number | null;
  hoursA?: number | null;
  hoursB?: number | null;
  creditsA?: string | null;
  creditsB?: string | null;
  presentA: boolean;
  presentB: boolean;
  deltaHours?: number | null;
  deltaCredits?: string | null;
};

export type ComparisonTotals = {
  totalHours: number;
  totalCredits: string;
};

export type AreaBreakdownItem = { code: string; name: string; share: string };

export type ComparisonResponse = {
  programA: ProgramSummary;
  programB: ProgramSummary;
  scope: ComparisonScope;
  semester?: number | null;
  rows: ComparisonRow[];
  totalsA: ComparisonTotals;
  totalsB: ComparisonTotals;
  areaBreakdownA?: AreaBreakdownItem[] | null;
  areaBreakdownB?: AreaBreakdownItem[] | null;
};

export type QuestionBlock = components["schemas"]["QuestionBlock"];

export type QuestionOption = { id: string; label: string };

export type Question = {
  id: string;
  block: QuestionBlock;
  prompt: string;
  options: QuestionOption[];
  required: boolean;
  adaptive: boolean;
  multiSelect: boolean;
  maxSelected: number;
  stage?: string | null;
  componentType: components["schemas"]["QuestionComponentType"];
  order: number;
  helperText?: string | null;
  declaredDimensions: string[];
  allowUncertain: boolean;
  allowSkip: boolean;
};

export type QuestionnaireResponse = { version: number; questionSetVersion: string; questions: Question[] };

export type ProftestAnswer = {
  questionId: string;
  optionIds: string[];
  intensity?: string;
};

export type ProftestAdaptiveAnswer = {
  questionId: string;
  optionId: string;
  dimension: string;
};

export type ProftestSubmissionRequest = {
  answers: ProftestAnswer[];
  adaptiveAnswers: ProftestAdaptiveAnswer[];
};

export type ProftestSessionAnswerRequest = components["schemas"]["ProftestSessionAnswerRequest"];
export type ProftestSessionResponse = {
  sessionId: string;
  questionSetVersion: string;
  status: "draft" | "completed" | "expired" | "abandoned";
  cursor: number;
  interactionCount: number;
  revision: number;
  currentQuestion: Question | null;
  staleQuestionIds: string[];
  progress: { stage: string; stageIndex: number; stageCount: number; answerCount: number; minRemaining: number; maxRemaining: number };
  adaptive: components["schemas"]["AdaptiveSelectionResponse"] | null;
  preliminary: components["schemas"]["PreliminaryProfileResponse"] | null;
  results: ProftestResultsResponse | null;
};
export type ProftestAnalyticsEventRequest = components["schemas"]["ProftestAnalyticsEventRequest"];

export type WeightedArea = { code: string; name: string; weight: string };

export type UserProfile = {
  interests: string[];
  activityPreferences: string[];
  antiInterests: string[];
  preferredSubjectWeights: WeightedArea[];
  preferredActivityWeights: WeightedArea[];
  negativeWeights: WeightedArea[];
  confidence: string;
  adaptiveAnswers: { dimension: string; value: string }[];
};

export type UserProfileSnapshot = {
  profile: UserProfile;
  revision: string;
  createdAt: string;
  updatedAt: string;
  expiresAt?: string | null;
};

export type ProftestPreviewResponse = {
  profile: UserProfile;
  adaptiveDecision: {
    dimension: string;
    decided: boolean;
    nextQuestion?: Question | null;
  };
  candidates: { programId: string; programName: string; contentFit: number }[];
};

export type MatchScoreBreakdown = {
  subjectFit: string;
  activityFit: string;
  distinctiveFit: string;
  antiPenalty: string;
  rawContentFit: string;
};

export type MatchScore = {
  programId: string;
  programCode: string;
  programName: string;
  breakdown: MatchScoreBreakdown;
};

export type FitReason = {
  area?: string | null;
  activity?: string | null;
  text: string;
  workload?: number | null;
  share?: string | null;
  sourceNames?: string[] | null;
};

export type OptionalMetric = {
  status?: string | null;
  score?: number | null;
};

export type Recommendation = {
  programId: string;
  programCode: string;
  programName: string;
  contentFit: number;
  score: MatchScore;
  reasons: FitReason[];
  antiFitReasons: FitReason[];
  areaShare: { code: string; name: string; share: string }[];
  semesterDistribution: { semester: number; share: string }[];
  distinctiveSubjects: string[];
  workloadReadiness?: OptionalMetric | null;
  careerFit?: OptionalMetric | null;
  admissionFit?: OptionalMetric | null;
};

export type ProftestResultsResponse = {
  profile: UserProfile;
  recommendations: Recommendation[];
};

export type RecommendationsResponse = {
  profile: UserProfile;
  recommendations: Recommendation[];
};

export type AccountInfo = {
  id: string;
  email: string;
  displayName?: string | null;
  createdAt: string;
};

export type AuthSession = {
  authenticated: boolean;
  account: AccountInfo | null;
};

export type EventKind =
  | "additional_education"
  | "open_day"
  | "lecture"
  | "competition"
  | "career"
  | "other";

export type EventFormat = "offline" | "online" | "hybrid";

export type EventVenue = {
  id?: string | null;
  name?: string | null;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
};

export type EventItem = {
  id: string;
  title: string;
  kind: EventKind;
  format: EventFormat;
  startsAt: string;
  endsAt?: string | null;
  description?: string | null;
  registrationUrl?: string | null;
  universityIds: string[];
  departmentIds: string[];
  programIds: string[];
  venue?: EventVenue | null;
  provenance: Provenance[];
};

export type EventListResponse = { items: EventItem[]; total: number };
export type EventDetailResponse = { event: EventItem };

export type CampusPoint = {
  id: string;
  name: string;
  pointType: string;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  universityIds: string[];
  departmentIds: string[];
  programIds: string[];
  provenance: Provenance[];
};

export type CampusPointDetailResponse = { point: CampusPoint };
export type CampusPointEventsResponse = { pointId: string; items: EventItem[]; total: number };
export type CampusRecommendationsResponse = {
  recommendedProgramIds: string[];
  recommendations: Recommendation[];
  points: CampusPoint[];
  events: EventItem[];
  eventsWithoutPoint: EventItem[];
};

export type PersonalRouteStatus = "ready" | "no_recommendations" | "no_events";

export type PersonalRouteStep = {
  position: number;
  kind: "explore_program" | "compare_programs" | "attend_event";
  reason: string;
  programIds: string[];
  recommendation?: Recommendation | null;
  event?: EventItem | null;
  venue?: EventVenue | null;
  point?: CampusPoint | null;
  startsAt?: string | null;
};

export type PersonalRouteResponse = {
  status: PersonalRouteStatus;
  summary: string;
  recommendations: Recommendation[];
  steps: PersonalRouteStep[];
};

export type IngestionRunStatus = "running" | "completed" | "failed";

export type IngestionRunSummary = {
  id: string;
  source?: string | null;
  status: IngestionRunStatus;
  startedAt: string;
  finishedAt?: string | null;
  sourceCount: number;
  programCount: number;
  curriculumItemCount: number;
  eventCount: number;
  campusPointCount: number;
};

export type IngestionRunDetail = IngestionRunSummary & {
  insertedCount: number;
  updatedCount: number;
  unchangedCount: number;
  removedCount: number;
  errorMessage?: string | null;
  sourceHashes: string[];
  sourceKinds: string[];
};

export type IngestionRunListResponse = { items: IngestionRunSummary[]; total: number };
export type IngestionRunDetailResponse = { run: IngestionRunDetail };
export type IngestionRetryRequest = { source: string };
