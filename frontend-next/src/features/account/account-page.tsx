"use client";

import { useEffect, useState } from "react";
import { UserRound, LogOut, Sparkles, Route as RouteIcon, Mail, Calendar } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader, Loading, ProfileRequired, Stat, SectionTitle, ScoreBadge, Tag } from "@/components/shared";
import { getAuthSession, getCurrentProfile, getCurrentRecommendations, getPersonalRoute, logoutAccount } from "@/lib/api";
import { formatPercent, formatDate } from "@/lib/format";
import type { AuthSession, UserProfileSnapshot, RecommendationsResponse, PersonalRouteResponse } from "@/lib/types";
import type { Route as RouteType } from "@/lib/router";

export function AccountPage({ navigate }: { navigate: (route: RouteType) => void }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [profile, setProfile] = useState<UserProfileSnapshot | null>(null);
  const [recs, setRecs] = useState<RecommendationsResponse | null>(null);
  const [route, setRoute] = useState<PersonalRouteResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([getAuthSession(), getCurrentProfile().catch(() => null), getCurrentRecommendations(5).catch(() => null), getPersonalRoute(5).catch(() => null)])
      .then(([s, p, r, rt]) => {
        setSession(s);
        setProfile(p);
        setRecs(r);
        setRoute(rt);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  if (loading || !session) return <Loading label="Загружаем кабинет…" />;

  if (!session.authenticated) {
    return (
      <div data-testid="account-page">
        <PageHeader eyebrow="Кабинет" title="Личный кабинет" />
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-3 p-10 text-center">
            <div className="grid h-12 w-12 place-items-center rounded-full bg-accent text-accent-foreground">
              <UserRound className="h-6 w-6" />
            </div>
            <h3 className="font-serif text-lg font-semibold">Вы вошли как гость</h3>
            <p className="max-w-md text-sm text-muted-foreground">
              Гостевая сессия уже позволяет проходить тест и смотреть рекомендации. Зарегистрируйтесь, чтобы сохранить
              профиль между устройствами.
            </p>
            <div className="flex gap-2">
              <Button onClick={() => navigate({ view: "proftest" })} className="bg-primary text-primary-foreground hover:bg-primary/90">Пройти тест</Button>
              <Button variant="outline" onClick={() => navigate({ view: "recommendations" })}>Рекомендации</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const acc = session.account!;
  return (
    <div data-testid="account-page">
      <PageHeader
        eyebrow="Кабинет"
        title={`Привет, ${acc.displayName ?? acc.email}`}
        description="Сводка вашего профиля, рекомендаций и личного маршрута."
        actions={
          <Button variant="outline" size="sm" className="gap-1" onClick={async () => { await logoutAccount(); load(); }}>
            <LogOut className="h-4 w-4" /> Выйти
          </Button>
        }
      />

      <Card className="mb-6">
        <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-primary font-serif text-2xl font-semibold text-primary-foreground">
            {acc.email[0]?.toUpperCase()}
          </span>
          <div className="flex-1">
            <p className="flex items-center gap-2 font-serif text-lg font-semibold">{acc.displayName ?? acc.email}</p>
            <p className="flex items-center gap-1 text-sm text-muted-foreground"><Mail className="h-3.5 w-3.5" /> {acc.email}</p>
          </div>
          <div className="flex gap-3">
            <Stat label="С нами с" value={formatDate(acc.createdAt)} />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <SectionTitle hint={profile ? `ревизия ${profile.revision}` : ""}>Профиль</SectionTitle>
          </CardHeader>
          <CardContent>
            {profile ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <Stat label="Уверенность" value={formatPercent(profile.profile.confidence, 0)} />
                  <Stat label="Обновлён" value={formatDate(profile.updatedAt)} />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {profile.profile.interests.map((i) => <Tag key={i} tone="muted">{i}</Tag>)}
                </div>
                <Button variant="outline" size="sm" onClick={() => navigate({ view: "proftest" })} className="gap-1">
                  <Sparkles className="h-4 w-4" /> Пройти тест заново
                </Button>
              </div>
            ) : (
              <ProfileRequired onAction={() => navigate({ view: "proftest" })} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3"><SectionTitle hint={recs ? `${recs.recommendations.length}` : ""}>Рекомендации</SectionTitle></CardHeader>
          <CardContent className="space-y-2">
            {recs && recs.recommendations.length > 0 ? (
              recs.recommendations.slice(0, 3).map((r) => (
                <button key={r.programId} onClick={() => navigate({ view: "program", id: r.programId })} className="flex w-full items-center gap-3 rounded-lg border border-border/60 bg-card p-3 text-left transition hover:border-primary/40">
                  <ScoreBadge value={r.contentFit} />
                  <div className="min-w-0">
                    <p className="font-mono text-xs text-primary">{r.programCode}</p>
                    <p className="truncate text-sm font-medium">{r.programName}</p>
                  </div>
                </button>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">Нет рекомендаций. Пройдите тест.</p>
            )}
            <Button variant="outline" size="sm" onClick={() => navigate({ view: "recommendations" })}>Все рекомендации</Button>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <SectionTitle hint={route ? route.status : ""}>
              <span className="flex items-center gap-2"><RouteIcon className="h-5 w-5 text-primary" /> Личный маршрут</span>
            </SectionTitle>
          </CardHeader>
          <CardContent>
            {route && route.steps.length > 0 ? (
              <div className="grid gap-2 sm:grid-cols-3">
                {route.steps.map((s) => (
                  <div key={s.position} className="rounded-lg border border-border/60 bg-card p-3">
                    <p className="text-xs font-bold uppercase text-primary">Шаг {s.position}</p>
                    <p className="mt-1 text-sm text-muted-foreground line-clamp-3">{s.reason}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Маршрут ещё не построен.</p>
            )}
            <Button variant="outline" size="sm" className="mt-3" onClick={() => navigate({ view: "personal-route" })}>Открыть маршрут</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
