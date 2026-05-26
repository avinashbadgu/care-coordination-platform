import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { UrgencyPill } from "@/components/urgency-pill";
import { StatusBadge } from "@/components/status-badge";
import { formatDateTime } from "@/lib/utils";
import { ResolveAlertButton, ResolveEscalationButton } from "./actions";

export const dynamic = "force-dynamic";

export default async function AlertsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const patientId = Number(id);
  const [alerts, escalations] = await Promise.all([
    api.listAlerts(patientId),
    api.listEscalations(patientId),
  ]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Alerts & escalations</h1>
        <p className="text-sm text-muted-foreground">
          Operational urgency, deterministic rules, attributable resolution.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <p className="text-sm text-muted-foreground">No alerts.</p>
          ) : (
            <ul className="divide-y">
              {alerts.map((a) => (
                <li key={a.id} className="flex items-center justify-between gap-3 py-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <UrgencyPill urgency={a.urgency} />
                      <span className="font-medium">{a.title}</span>
                      <StatusBadge status={a.status} />
                    </div>
                    {a.detail && (
                      <p className="text-sm text-muted-foreground">{a.detail}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      Raised {formatDateTime(a.created_at)}
                    </p>
                  </div>
                  <div>
                    {a.status !== "resolved" && (
                      <ResolveAlertButton alertId={a.id} />
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Escalations</CardTitle>
        </CardHeader>
        <CardContent>
          {escalations.length === 0 ? (
            <p className="text-sm text-muted-foreground">No escalations.</p>
          ) : (
            <ul className="divide-y">
              {escalations.map((e) => (
                <li key={e.id} className="flex items-center justify-between gap-3 py-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{e.rule}</span>
                      <StatusBadge status={e.status} />
                    </div>
                    {e.reason && (
                      <p className="text-sm text-muted-foreground">{e.reason}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      Created {formatDateTime(e.created_at)}
                    </p>
                  </div>
                  <div>
                    {e.status !== "resolved" && (
                      <ResolveEscalationButton escalationId={e.id} />
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
