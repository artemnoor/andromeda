"use client";

import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { useRouter } from "@/lib/router";
import { getPrograms } from "@/lib/api";
import type { ProgramSummary } from "@/lib/types";
import { CatalogPage } from "@/features/catalog/catalog-page";
import { ProgramPage } from "@/features/program/program-page";
import { ComparePage } from "@/features/compare/compare-page";
import { ProftestPage } from "@/features/proftest/proftest-page";
import { RecommendationsPage } from "@/features/recommendations/recommendations-page";
import { EventsPage } from "@/features/events/events-page";
import { EventPage } from "@/features/events/event-page";
import { PersonalRoutePage } from "@/features/personal-route/personal-route-page";
import { UnifiedFlowPage } from "@/features/unified-flow/unified-flow-page";
import { AccountPage } from "@/features/account/account-page";
import { OpsPage } from "@/features/ops/ops-page";

export default function Page() {
  const { route, navigate } = useRouter();
  const [programs, setPrograms] = useState<ProgramSummary[]>([]);
  const [programsLoading, setProgramsLoading] = useState(true);
  const [programsError, setProgramsError] = useState<string | null>(null);

  const loadPrograms = useCallback(() => {
    setProgramsLoading(true);
    setProgramsError(null);
    getPrograms()
      .then((res) => setPrograms(res.items))
      .catch(() => setProgramsError("Не удалось загрузить каталог программ из API."))
      .finally(() => setProgramsLoading(false));
  }, []);

  useEffect(() => {
    void loadPrograms();
  }, [loadPrograms]);

  return (
    <AppShell route={route} navigate={navigate}>
      {route.view === "catalog" && (
        <CatalogPage programs={programs} loading={programsLoading} error={programsError} onRetry={loadPrograms} navigate={navigate} />
      )}
      {route.view === "program" && (
        <ProgramPage id={route.id ?? programs[0]?.id ?? ""} navigate={navigate} />
      )}
      {route.view === "compare" && (
        <ComparePage programs={programs} navigate={navigate} />
      )}
      {route.view === "proftest" && <ProftestPage navigate={navigate} />}
      {route.view === "recommendations" && <RecommendationsPage navigate={navigate} />}
      {route.view === "events" && <EventsPage navigate={navigate} />}
      {route.view === "event" && <EventPage id={route.id ?? ""} navigate={navigate} />}
      {route.view === "personal-route" && <PersonalRoutePage navigate={navigate} />}
      {route.view === "flow" && <UnifiedFlowPage navigate={navigate} />}
      {route.view === "account" && <AccountPage navigate={navigate} />}
      {route.view === "ops" && <OpsPage />}
    </AppShell>
  );
}
