"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

export function NewCarePlanForm({ patientId }: { patientId: number }) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tasksRaw, setTasksRaw] = useState("");
  const [pending, start] = useTransition();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    start(async () => {
      const tasks = tasksRaw
        .split("\n")
        .map((t) => t.trim())
        .filter(Boolean)
        .map((title) => ({ title }));
      await api.createCarePlan(patientId, {
        title: title.trim(),
        description: description.trim() || undefined,
        tasks,
      });
      setTitle("");
      setDescription("");
      setTasksRaw("");
      router.refresh();
    });
  }

  return (
    <form className="space-y-3" onSubmit={submit}>
      <div className="space-y-1.5">
        <Label htmlFor="title">Title</Label>
        <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="description">Description</Label>
        <Input
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="tasks">Tasks (one per line)</Label>
        <textarea
          id="tasks"
          rows={4}
          value={tasksRaw}
          onChange={(e) => setTasksRaw(e.target.value)}
          className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
      </div>
      <Button type="submit" disabled={pending || !title.trim()}>
        {pending ? "Creating…" : "Create plan"}
      </Button>
    </form>
  );
}

export function CompleteTaskButton({
  carePlanId,
  taskId,
}: {
  carePlanId: number;
  taskId: number;
}) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [done, setDone] = useState(false);
  return (
    <Button
      size="sm"
      variant="outline"
      disabled={pending || done}
      onClick={() =>
        start(async () => {
          await api.completeTask(carePlanId, taskId);
          setDone(true);
          router.refresh();
        })
      }
    >
      {done ? "Marked" : pending ? "…" : "Mark done"}
    </Button>
  );
}
