export type PortalRole = "owner" | "admin" | "analyst" | "viewer";

export type SubscriptionStatus =
  | "trialing"
  | "active"
  | "past_due"
  | "canceled"
  | "unpaid"
  | "incomplete"
  | "none";

export type MeResponse = {
  userId: string;
  email: string | null;
  organizationId: string;
  tenantId: string;
  tenantName: string | null;
  role: PortalRole;
  subscriptionStatus: SubscriptionStatus;
  hasActiveSubscription: boolean;
  allowedActions: string[];
};

export type TenantResponse = {
  tenantId: string;
  tenantName: string | null;
  websiteUrl: string | null;
  industry: string | null;
  supportEmail: string | null;
  domains: string[];
  settings: {
    confidenceThreshold?: number;
    autoAnswerEnabled?: boolean;
  } & Record<string, unknown>;
  brandVoice: {
    tone?: string;
    use?: string[];
    avoid?: string[];
    escalationStyle?: string;
    exampleReplies?: string[];
  } & Record<string, unknown>;
  onboarding: Record<string, unknown>;
  billing: {
    status: SubscriptionStatus;
    hasActiveSubscription: boolean;
  };
};

export type OverviewResponse = {
  tenantId: string;
  metrics: {
    deflectionRate: number;
    aiResolved: number;
    humanEscalated: number;
    activeSessions: number;
    activeKnowledgeEntries: number;
    humanHoursSaved: number;
    safetyScore: number | null;
  };
  recentActivity: GovernanceLog[];
  setupWarnings: string[];
  systemHealth: {
    status: string;
    subscription: SubscriptionStatus;
  };
};

export type MetricsResponse = {
  tenantId: string;
  decisionCounts: {
    answered: number;
    escalated: number;
    closed: number;
    total: number;
  };
  deflectionRate: number;
  humanHoursSaved: number;
};

export type SessionMessage = {
  sender?: string;
  speaker?: string;
  role?: string;
  text: string;
  timestamp?: string;
  createdAt?: string;
  at?: string;
};

export type SessionSummary = {
  id: string;
  clientId?: string | null;
  userId?: string | null;
  provider?: string | null;
  status?: string | null;
  dashboardStatus?: string | null;
  latestMessage?: string | null;
  messageCount?: number;
  question?: string | null;
  customer?: string | null;
  confidence?: number | null;
  similarity?: number | null;
  source?: string | null;
  answer?: string | null;
  escalationReason?: string | null;
  transcript?: SessionMessage[];
  messages?: SessionMessage[];
  createdAt?: string | null;
  updatedAt?: string | null;
};

export type SessionsResponse = {
  tenantId: string;
  sessions: SessionSummary[];
};

export type SessionDetailResponse = {
  tenantId: string;
  session: SessionSummary;
  governanceLogs: GovernanceLog[];
};

export type KnowledgeBaseEntry = {
  id: string;
  domainId: string;
  question: string;
  answer: string;
  tags: string[];
  active: boolean;
  createdAt?: string | null;
  updatedAt?: string | null;
};

export type KnowledgeBaseResponse = {
  tenantId: string;
  entries: KnowledgeBaseEntry[];
};

export type TestQuestionResponse = {
  tenantId: string;
  question: string;
  domainId: string | null;
  dryRun: boolean;
  decision: string;
  response: string | null;
  matchedKnowledgeBaseEntry: KnowledgeBaseEntry | null;
  confidenceScore: number | null;
  threshold: number | null;
  reason: string;
  entriesConsidered: number;
};

export type BrandVoiceResponse = {
  tenantId: string;
  brandVoice: TenantResponse["brandVoice"];
};

export type GovernanceLog = {
  id?: string;
  decision?: string | null;
  question?: string | null;
  reason?: string | null;
  source?: string | null;
  similarity?: number | null;
  groundedness?: number | null;
  safety?: number | null;
  timestamp?: string | null;
  action?: string | null;
  actorEmail?: string | null;
  actorUserId?: string | null;
  resourceType?: string | null;
  resourceId?: string | null;
  before?: unknown;
  after?: unknown;
  metadata?: Record<string, unknown> | null;
};

export type GovernanceResponse = {
  tenantId: string;
  logs: GovernanceLog[];
};

export type IntegrationStatus = {
  tenantId?: string;
  provider: string;
  status: string;
  health?: string | null;
  setupWarnings?: string[];
  metadata?: Record<string, unknown>;
  updatedAt?: string | null;
};

export type IntegrationsResponse = {
  tenantId: string;
  integrations: IntegrationStatus[];
};
