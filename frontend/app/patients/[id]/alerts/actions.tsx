"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export function ResolveAlertButton({ alertId }: { alertId: number }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  return (
    <Button
      size="sm"
      variant="secondary"
      disabled={pending}
      onClick={() =>
        start(async () => {
          await api.resolveAlert(alertId);
          router.refresh();
        })
      }
    >
      {pending ? "Resolving…" : "Resolve"}
    </Button>
  );
}

export function ResolveEscalationButton({ escalationId }: { escalationId: number }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  return (
    <Button
      size="sm"
      variant="secondary"
      disabled={pending}
      onClick={() =>
        start(async () => {
          await api.resolveEscalation(escalationId);
          router.refresh();
        })
      }
    >
      {pending ? "Resolving…" : "Resolve"}
    </Button>
  );
}
