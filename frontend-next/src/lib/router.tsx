"use client";

import { useCallback, useEffect, useState } from "react";

export type View =
  | "catalog"
  | "program"
  | "compare"
  | "proftest"
  | "recommendations"
  | "events"
  | "event"
  | "personal-route"
  | "flow"
  | "account"
  | "ops";

export type Route = {
  view: View;
  id?: string;
};

const DEFAULT_ROUTE: Route = { view: "catalog" };

function parseSearch(search: string): Route {
  const params = new URLSearchParams(search);
  const view = (params.get("view") as View | null) ?? "catalog";
  const id = params.get("id") ?? undefined;
  const eventId = params.get("eventId") ?? undefined;
  if (view === "event") return { view, id: eventId };
  return { view, id };
}

export function buildHref(route: Route): string {
  const params = new URLSearchParams();
  params.set("view", route.view);
  if (route.view === "event" && route.id) params.set("eventId", route.id);
  else if (route.id) params.set("id", route.id);
  const qs = params.toString();
  return qs ? `/?${qs}` : "/";
}

export function useRouter(): {
  route: Route;
  navigate: (route: Route) => void;
} {
  // Start with a stable default for SSR/first render to avoid hydration mismatch,
  // then sync to the real URL on the client.
  const [route, setRoute] = useState<Route>(DEFAULT_ROUTE);

  useEffect(() => {
    setRoute(parseSearch(window.location.search));
    const onPop = () => setRoute(parseSearch(window.location.search));
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((next: Route) => {
    const href = buildHref(next);
    if (href === window.location.pathname + window.location.search) return;
    window.history.pushState({}, "", href);
    setRoute(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  return { route, navigate };
}

export const NAV_ITEMS: { view: View; label: string; icon: string }[] = [
  { view: "catalog", label: "Каталог", icon: "Library" },
  { view: "compare", label: "Сравнить", icon: "GitCompare" },
  { view: "proftest", label: "Профиль", icon: "Compass" },
  { view: "recommendations", label: "Рекомендации", icon: "Sparkles" },
  { view: "events", label: "События", icon: "CalendarDays" },
  { view: "personal-route", label: "Мой план", icon: "Route" },
  { view: "flow", label: "Путь", icon: "Workflow" },
  { view: "account", label: "Кабинет", icon: "UserRound" },
  { view: "ops", label: "Ops", icon: "Wrench" },
];
