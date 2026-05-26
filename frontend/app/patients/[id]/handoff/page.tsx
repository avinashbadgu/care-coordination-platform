import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime } from "@/lib/utils";
import { HoursPicker } from "./hours-picker";

export const dynamic = "force-dynamic";

export default async function HandoffPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ hours?: string }>;
}) {
  const { id } = await params;
  const sp = await searchParams;
  const patientId = Number(id);
  const hours = Math.max(1, Math.min(72, Number(sp.hours) || 12));

  const handoff = await api.getHandoff(patientId, hours);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Shift handoff</h1>
          <p className="text-sm text-muted-foreground">
            Operational summary of the last {hours} hours. For the
            night-to-morning caregiver transition.
          </p>
        </div>
        <HoursPicker initial={hours} />
      </header>

      <Card>
        <CardHeader>
          <CardTitle>{handoff.headline}</CardTitle>
          <p className="text-xs text-muted-foreground">
            {formatDateTime(handoff.window_start)} → {formatDateTime(handoff.window_end)}
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <pre className="whitespace-pre-wrap rounded-md bg-muted p-3 text-sm">
            {handoff.body}
          </pre>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="Open alerts" value={handoff.open_alerts} />
            <Stat label="Open escalations" value={handoff.open_escalations} />
            <Stat
              label="Events in window"
              value={Object.values(handoff.events).reduce((a, b) => a + b, 0)}
            />
            <Stat
              label="Adherence"
              value={
                typeof handoff.metrics.adherence_ratio === "number"
                  ? `${Math.round((handoff.metrics.adherence_ratio as number) * 100)}%`
                  : "—"
              }
            />
          </div>

          {Object.keys(handoff.events).length > 0 && (
            <details>
              <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                event breakdown
              </summary>
              <pre className="mt-1 overflow-auto rounded bg-muted p-2 text-xs">
                {JSON.stringify(handoff.events, null, 2)}
              </pre>
            </details>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md border bg-card p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}
