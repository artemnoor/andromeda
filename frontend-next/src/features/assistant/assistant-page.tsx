"use client";

import { FormEvent, useState } from "react";
import { MessageCircle, Send } from "lucide-react";
import { queryAssistant } from "@/lib/api";
import type { AssistantQueryResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/shared";
import type { Route } from "@/lib/router";

type ChatMessage = { role: "user" | "assistant"; text: string };

const SUGGESTIONS = [
  "Где больше математики?",
  "Куда я прохожу с 270?",
  "Покажи программы Бауманки с сильной математикой",
];

export function AssistantPage(_props: { navigate: (route: Route) => void }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [session, setSession] = useState<{ id: string; revision: number } | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event?: FormEvent, value?: string) {
    event?.preventDefault();
    const text = (value ?? input).trim();
    if (!text || pending) return;
    setInput("");
    setMessages((current) => [...current, { role: "user", text }]);
    setPending(true);
    setError(null);
    try {
      const result = await queryAssistant({
        text,
        sessionId: session?.id,
        expectedRevision: session?.revision,
      });
      setSession({ id: result.session_id, revision: result.revision });
      setMessages((current) => [...current, { role: "assistant", text: assistantText(result) }]);
    } catch {
      setError("Не удалось получить ответ. Попробуйте ещё раз.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div data-testid="assistant-page" className="space-y-6">
      <PageHeader
        eyebrow="Andromeda · универсальный запрос"
        title="Спросите о программах и поступлении"
        description="Система уточнит недостающие данные, соберёт typed query и объяснит результат на основе учебных планов и источников."
      />
      <Card className="border-primary/20 bg-primary/[0.03]">
        <CardContent className="space-y-4 p-5">
          <div className="flex items-center gap-2 text-sm font-medium text-primary"><MessageCircle className="h-4 w-4" /> Чат с данными Andromeda</div>
          <div className="min-h-40 space-y-3 rounded-xl bg-background/80 p-4" aria-live="polite">
            {messages.length === 0 && <p className="text-sm text-muted-foreground">Например: «Сравни эти программы по математике и программированию».</p>}
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={message.role === "user" ? "ml-8 rounded-lg bg-primary/10 p-3 text-sm" : "mr-8 rounded-lg border border-border/70 p-3 text-sm"}>
                {message.text}
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((suggestion) => <Button key={suggestion} type="button" size="sm" variant="outline" disabled={pending} onClick={() => void submit(undefined, suggestion)}>{suggestion}</Button>)}
          </div>
          <form className="flex gap-2" onSubmit={(event) => void submit(event)}>
            <Input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Например: где меньше физики?" disabled={pending} aria-label="Вопрос к Andromeda" />
            <Button type="submit" disabled={pending || !input.trim()} aria-label="Отправить вопрос"><Send className="h-4 w-4" /></Button>
          </form>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
function assistantText(result: AssistantQueryResponse): string {
  if (result.state !== "complete") {
    return [result.question, ...result.options.map((option) => `• ${option}`)].filter(Boolean).join("\n") || "Уточните запрос.";
  }
  return result.response?.text || "Результат готов.";
}
