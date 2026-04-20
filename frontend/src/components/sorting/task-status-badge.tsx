import { CheckCircle2, Loader2, XCircle } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { STATUS_LABEL, type TaskStatus } from "@/lib/api/tasks"
import { cn } from "@/lib/utils"

interface Props {
  status: TaskStatus
  className?: string
}

const STYLE: Record<TaskStatus, string> = {
  pending: "bg-slate-100 text-slate-700 hover:bg-slate-100",
  extracting: "bg-sky-100 text-sky-700 hover:bg-sky-100",
  parsing: "bg-indigo-100 text-indigo-700 hover:bg-indigo-100",
  linking: "bg-violet-100 text-violet-700 hover:bg-violet-100",
  succeeded: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
  failed: "bg-rose-100 text-rose-700 hover:bg-rose-100",
}

export function TaskStatusBadge({ status, className }: Props) {
  const isRunning =
    status === "pending" ||
    status === "extracting" ||
    status === "parsing" ||
    status === "linking"

  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1 border-transparent font-medium",
        STYLE[status],
        className
      )}
    >
      {isRunning ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : status === "succeeded" ? (
        <CheckCircle2 className="h-3 w-3" />
      ) : (
        <XCircle className="h-3 w-3" />
      )}
      {STATUS_LABEL[status]}
    </Badge>
  )
}
