import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { NewCarePlanForm, CompleteTaskButton } from "./forms";

export const dynamic = "force-dynamic";

export default async function CarePlanPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const patientId = Number(id);
  const plans = await api.listCarePlans(patientId);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Care plan</h1>
        <p className="text-sm text-muted-foreground">
          Doctor- or caregiver-defined operational plan with trackable tasks.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          {plans.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-sm text-muted-foreground">
                No care plans yet.
              </CardContent>
            </Card>
          ) : (
            plans.map((p) => (
              <Card key={p.id}>
                <CardHeader>
                  <CardTitle>{p.title}</CardTitle>
                  {p.description && (
                    <p className="text-sm text-muted-foreground">{p.description}</p>
                  )}
                </CardHeader>
                <CardContent>
                  {p.tasks.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No tasks.</p>
                  ) : (
                    <ul className="divide-y">
                      {p.tasks.map((t) => (
                        <li
                          key={t.id}
                          className="flex items-center justify-between py-2"
                        >
                          <div>
                            <div className="text-sm font-medium">{t.title}</div>
                            {t.cadence && (
                              <div className="text-xs text-muted-foreground">{t.cadence}</div>
                            )}
                          </div>
                          <CompleteTaskButton carePlanId={p.id} taskId={t.id} />
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>New care plan</CardTitle>
          </CardHeader>
          <CardContent>
            <NewCarePlanForm patientId={patientId} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
