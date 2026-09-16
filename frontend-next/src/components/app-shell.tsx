"use client";

import { Library, GitCompare, Compass, Sparkles, CalendarDays, Route as RouteIcon, Workflow, UserRound, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_ITEMS, type View, type Route, buildHref } from "@/lib/router";
import { AuthPanel } from "@/components/auth-panel";

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Library,
  GitCompare,
  Compass,
  Sparkles,
  CalendarDays,
  Route: RouteIcon,
  Workflow,
  UserRound,
  Wrench,
};

export function AppShell({
  route,
  navigate,
  children,
}: {
  route: Route;
  navigate: (route: Route) => void;
  children: React.ReactNode;
}) {
  const primary = NAV_ITEMS.filter((i) => !["flow", "ops"].includes(i.view));
  const secondary = NAV_ITEMS.filter((i) => ["flow", "ops"].includes(i.view));

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-6xl items-center gap-4 px-4 py-3 md:px-6">
          <button
            onClick={() => navigate({ view: "catalog" })}
            className="group flex shrink-0 items-center gap-2.5 text-left"
            aria-label="Andromeda, перейти в каталог"
          >
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary font-serif text-lg font-semibold text-primary-foreground shadow-sm transition group-hover:scale-105">
              A
            </span>
            <span className="hidden leading-tight sm:block">
              <span className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-primary">
                Andromeda · BMSTU
              </span>
              <span className="block font-serif text-sm font-semibold text-foreground">
                Учебные планы как данные
              </span>
            </span>
          </button>

          <nav aria-label="Основные разделы" className="hidden flex-1 items-center gap-1 lg:flex">
            {primary.map((item) => {
              const Icon = ICONS[item.icon];
              const active = route.view === item.view || (route.view === "event" && item.view === "events");
              return (
                <button
                  key={item.view}
                  onClick={() => navigate({ view: item.view })}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition",
                    active
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                  )}
                >
                  {Icon && <Icon className="h-4 w-4" />}
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <nav aria-label="Дополнительные разделы" className="hidden items-center gap-1 md:flex">
              {secondary.map((item) => {
                const Icon = ICONS[item.icon];
                const active = route.view === item.view;
                return (
                  <button
                    key={item.view}
                    onClick={() => navigate({ view: item.view })}
                    aria-current={active ? "page" : undefined}
                    title={item.label}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-sm font-medium transition",
                      active
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    )}
                  >
                    {Icon && <Icon className="h-4 w-4" />}
                    <span className="hidden xl:inline">{item.label}</span>
                  </button>
                );
              })}
            </nav>
            <AuthPanel onNavigate={(view: View) => navigate({ view })} />
          </div>
        </div>

        {/* Mobile nav */}
        <nav aria-label="Разделы (мобильное)" className="flex gap-1 overflow-x-auto px-4 pb-2 lg:hidden warm-scroll">
          {NAV_ITEMS.map((item) => {
            const active = route.view === item.view || (route.view === "event" && item.view === "events");
            return (
              <button
                key={item.view}
                  onClick={() => navigate({ view: item.view })}
                className={cn(
                  "inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "bg-accent/60 text-muted-foreground hover:text-accent-foreground",
                )}
              >
                {item.label}
              </button>
            );
          })}
        </nav>
      </header>

      <div className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-6 md:py-10">
        <div key={`${route.view}-${route.id ?? ""}`} className="animate-float-in">
          {children}
        </div>
      </div>

      <footer className="mt-auto border-t border-border/70 bg-background/60">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-2 px-4 py-5 text-xs text-muted-foreground md:flex-row md:px-6">
          <p>
            <span className="font-semibold text-foreground">Andromeda</span> · source-backed данные МГТУ им. Н.Э. Баумана
          </p>
          <p>Обновляем только через API · {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  );
}

export function NavAnchor({ route, children }: { route: Route; children: React.ReactNode }) {
  return (
    <a href={buildHref(route)} className="text-primary hover:underline">
      {children}
    </a>
  );
}
