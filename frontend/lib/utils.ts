import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

export function relativeTime(iso: string): string {
  const d = new Date(iso).getTime();
  if (Number.isNaN(d)) return iso;
  const diff = (Date.now() - d) / 1000;
  const abs = Math.abs(diff);
  if (abs < 60) return diff >= 0 ? "just now" : "in a moment";
  if (abs < 3600) {
    const m = Math.round(abs / 60);
    return diff >= 0 ? `${m}m ago` : `in ${m}m`;
  }
  if (abs < 86400) {
    const h = Math.round(abs / 3600);
    return diff >= 0 ? `${h}h ago` : `in ${h}h`;
  }
  const d2 = Math.round(abs / 86400);
  return diff >= 0 ? `${d2}d ago` : `in ${d2}d`;
}
