import { Circle, CircleCheck } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import type { JobStatus } from "@/lib/api/jobs"
import { cn } from "@/lib/utils"

interface JobStatusBadgeProps {
  status: JobStatus
  className?: string
}

export function JobStatusBadge({ status, className }: JobStatusBadgeProps) {
  if (status === "active") {
    return (
      <Badge
        className={cn(
          "gap-1 bg-emerald-500 hover:bg-emerald-500",
          className
        )}
      >
        <CircleCheck className="h-3 w-3" />
        进行中
      </Badge>
    )
  }
  return (
    <Badge variant="secondary" className={cn("gap-1", className)}>
      <Circle className="h-3 w-3" />
      已结束
    </Badge>
  )
}
