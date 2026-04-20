import { Suspense } from "react"

import { WorkbenchView } from "@/components/workbench/workbench-view"
import { Skeleton } from "@/components/ui/skeleton"

export default function WorkbenchPage() {
  return (
    <Suspense fallback={<Skeleton className="h-[600px] w-full" />}>
      <WorkbenchView />
    </Suspense>
  )
}
