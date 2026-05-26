import { cn } from "@/lib/utils";
import type { Urgency } from "@/lib/types";

const styles: Record<Urgency, string> = {
  low: "bg-muted text-muted-foreground",
  medium: "bg-[hsl(var(--urgency-medium))]/15 text-[hsl(var(--urgency-medium))]",
  high: "bg-[hsl(var(--urgency-high))]/15 text-[hsl(var(--urgency-high))]",
};

export function UrgencyPill({ urgency, className }: { urgency: Urgency; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium uppercase tracking-wide",
        styles[urgency],
        className,
      )}
    >
      {urgency}
    </span>
  );
}
