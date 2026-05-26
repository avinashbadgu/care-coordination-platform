import type { TimelineEvent } from "@/lib/types";
import { UrgencyPill } from "@/components/urgency-pill";
import { formatDateTime } from "@/lib/utils";

export function TimelineFeed({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="rounded-lg border bg-card py-12 text-center text-sm text-muted-foreground">
        No events yet. Workflows will populate this feed as the platform is used.
      </div>
    );
  }
  return (
    <ol className="relative ml-3 space-y-4 border-l">
      {events.map((ev) => (
        <li key={ev.id} className="ml-4">
          <div className="absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full bg-border" />
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{formatDateTime(ev.occurred_at)}</span>
            <UrgencyPill urgency={ev.urgency} />
            <span className="font-mono">{ev.event_type}</span>
            {ev.confidence !== null && ev.confidence !== undefined && (
              <span>· conf {ev.confidence.toFixed(2)}</span>
            )}
          </div>
          <div className="mt-1 text-sm text-foreground">{ev.summary || "—"}</div>
          {ev.payload && Object.keys(ev.payload).length > 0 && (
            <details className="mt-1">
              <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                payload
              </summary>
              <pre className="mt-1 overflow-auto rounded bg-muted p-2 text-xs">
                {JSON.stringify(ev.payload, null, 2)}
              </pre>
            </details>
          )}
        </li>
      ))}
    </ol>
  );
}
