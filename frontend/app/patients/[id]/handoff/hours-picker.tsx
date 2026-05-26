"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

const PRESETS = [8, 12, 24];

export function HoursPicker({ initial }: { initial: number }) {
  const router = useRouter();
  const pathname = usePathname();
  const search = useSearchParams();

  function pick(h: number) {
    const params = new URLSearchParams(search.toString());
    params.set("hours", String(h));
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <div className="flex gap-2">
      {PRESETS.map((h) => (
        <Button
          key={h}
          variant={h === initial ? "default" : "outline"}
          size="sm"
          onClick={() => pick(h)}
        >
          Last {h}h
        </Button>
      ))}
    </div>
  );
}
