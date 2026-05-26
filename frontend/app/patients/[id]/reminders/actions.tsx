"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function ReminderActions({ patientId }: { patientId: number }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);

  async function run(label: string, fn: () => Promise<unknown>) {
    setBusy(label);
    try {
      await fn();
      router.refresh();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => run("expand", () => api.expandReminders(patientId))}
        disabled={busy !== null}
      >
        {busy === "expand" ? "Expanding…" : "Expand today"}
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => run("dispatch", () => api.dispatchDue())}
        disabled={busy !== null}
      >
        {busy === "dispatch" ? "Dispatching…" : "Dispatch due"}
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => run("miss", () => api.detectMisses())}
        disabled={busy !== null}
      >
        {busy === "miss" ? "Detecting…" : "Detect misses"}
      </Button>
    </div>
  );
}

export function ReminderRowActions({
  reminderId,
  status,
}: {
  reminderId: number;
  status: string;
}) {
  const router = useRouter();
  const [pending, start] = useTransition();
  if (status === "acknowledged" || status === "missed") {
    return <span className="text-xs text-muted-foreground">—</span>;
  }
  return (
    <Button
      size="sm"
      variant="secondary"
      disabled={pending}
      onClick={() =>
        start(async () => {
          await api.ackReminder(reminderId);
          router.refresh();
        })
      }
    >
      {pending ? "Acking…" : "Ack"}
    </Button>
  );
}
