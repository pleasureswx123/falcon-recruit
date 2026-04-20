"use client"

import * as React from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import {
  useCandidates,
  useReassignFile,
} from "@/lib/hooks/use-candidates"
import { cn } from "@/lib/utils"

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  fileId: string
  jobId: string
  excludeCandidateId?: string
}

export function ReassignFileDialog({
  open,
  onOpenChange,
  fileId,
  jobId,
  excludeCandidateId,
}: Props) {
  const { data, isLoading } = useCandidates({
    job_id: jobId,
    page: 1,
    page_size: 200,
  })
  const reassignMutation = useReassignFile()
  const [targetId, setTargetId] = React.useState<string | undefined>()

  React.useEffect(() => {
    if (!open) setTargetId(undefined)
  }, [open])

  const candidates = (data?.items ?? []).filter(
    (c) => c.id !== excludeCandidateId
  )

  async function handleConfirm() {
    if (!targetId || !fileId) return
    try {
      await reassignMutation.mutateAsync({
        candidate_id: targetId,
        file_id: fileId,
      })
      toast.success("已改挂")
      onOpenChange(false)
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "改挂失败")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>将文件改挂到其他候选人</DialogTitle>
        </DialogHeader>
        <ScrollArea className="h-[360px] rounded-md border">
          {isLoading ? (
            <div className="flex flex-col gap-2 p-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : candidates.length === 0 ? (
            <div className="flex h-full items-center justify-center p-6 text-sm text-muted-foreground">
              没有可选择的目标候选人
            </div>
          ) : (
            <div className="flex flex-col">
              {candidates.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setTargetId(c.id)}
                  className={cn(
                    "flex flex-col gap-0.5 border-b px-3 py-2 text-left transition hover:bg-muted/50",
                    targetId === c.id && "bg-primary/5 hover:bg-primary/5"
                  )}
                >
                  <div className="text-sm font-medium">
                    {c.name ?? "（未识别姓名）"}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {[c.phone, c.email].filter(Boolean).join(" · ") || "—"}
                  </div>
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!targetId || reassignMutation.isPending}
          >
            确认改挂
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
