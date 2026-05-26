import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TimelineFeed } from "@/components/timeline-feed";

export const dynamic = "force-dynamic";

export default async function PatientTimelinePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const patientId = Number(id);
  const [page, alerts, openEscalations] = await Promise.all([
    api.listTimeline(patientId, { limit: 100 }),
    api.listAlerts(patientId, true),
    api.listEscalations(patientId),
  ]);
  const openEscalationCount = openEscalations.filter((e) => e.status !== "resolved").length;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Care timeline</h1>
        <p className="text-sm text-muted-foreground">
          Source-of-truth event log. Every meaningful action — reminders, uploads,
          extractions, alerts, escalations — lands here.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Events</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold">{page.total}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Open alerts</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold">{alerts.length}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Open escalations</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold">{openEscalationCount}</CardContent>
        </Card>
      </div>

      <TimelineFeed events={page.items} />
    </div>
  );
}
