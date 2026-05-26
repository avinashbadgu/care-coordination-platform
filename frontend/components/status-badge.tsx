import { Badge } from "@/components/ui/badge";

const variantFor: Record<string, "default" | "secondary" | "muted" | "destructive" | "outline"> = {
  pending: "muted",
  sent: "secondary",
  acknowledged: "default",
  missed: "destructive",
  failed: "destructive",
  uploaded: "muted",
  ocr_running: "secondary",
  ocr_completed: "default",
  ocr_failed: "destructive",
  review_required: "outline",
  transcribing: "secondary",
  transcribed: "default",
  extracted: "default",
  open: "destructive",
  resolved: "default",
  cancelled: "muted",
  notified: "secondary",
};

export function StatusBadge({ status }: { status: string }) {
  const variant = variantFor[status] || "muted";
  return <Badge variant={variant}>{status.replace(/_/g, " ")}</Badge>;
}
