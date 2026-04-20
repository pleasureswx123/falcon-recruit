"use client"

import * as React from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Users } from "lucide-react"

import { ExportMenu } from "@/components/exports/export-menu"
import { CandidateListPanel } from "@/components/workbench/candidate-list-panel"
import { CandidateDetailPanel } from "@/components/workbench/candidate-detail-panel"
import { FilePreviewPanel } from "@/components/workbench/file-preview-panel"
import { UnmatchedFilesPanel } from "@/components/workbench/unmatched-files-panel"
import { Card, CardContent } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useJobs } from "@/lib/hooks/use-jobs"

export function WorkbenchView() {
  const router = useRouter()
  const params = useSearchParams()

  const jobId = params.get("jobId") ?? undefined
  const taskId = params.get("taskId") ?? undefined
  const initialCandidateId = params.get("candidateId") ?? undefined

  const [selectedCandidateId, setSelectedCandidateId] = React.useState<
    string | undefined
  >(initialCandidateId)
  const [selectedFileId, setSelectedFileId] = React.useState<
    string | undefined
  >(undefined)

  const { data: jobsData, isLoading: jobsLoading } = useJobs({
    page: 1,
    page_size: 100,
  })

  function switchJob(nextJobId: string) {
    const next = new URLSearchParams(params.toString())
    next.set("jobId", nextJobId)
    next.delete("candidateId")
    router.replace(`/workbench?${next.toString()}`)
    setSelectedCandidateId(undefined)
    setSelectedFileId(undefined)
  }

  function selectCandidate(id: string) {
    setSelectedCandidateId(id)
    setSelectedFileId(undefined)
    const next = new URLSearchParams(params.toString())
    next.set("candidateId", id)
    router.replace(`/workbench?${next.toString()}`)
  }

  if (!jobId) {
    return (
      <div className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold tracking-tight">分拣工作台</h2>
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-16">
            <Users className="h-10 w-10 text-muted-foreground" />
            <div className="text-sm text-muted-foreground">
              请选择一个职位，查看其候选人分拣结果
            </div>
            <div className="w-72">
              <Select
                onValueChange={switchJob}
                disabled={jobsLoading || !jobsData?.items.length}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择职位…" />
                </SelectTrigger>
                <SelectContent>
                  {jobsData?.items.map((j) => (
                    <SelectItem key={j.id} value={j.id}>
                      {j.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const currentJob = jobsData?.items.find((j) => j.id === jobId)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold tracking-tight">分拣工作台</h2>
          {currentJob && (
            <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {currentJob.title}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="w-60">
            <Select value={jobId} onValueChange={switchJob}>
              <SelectTrigger>
                <SelectValue placeholder="切换职位…" />
              </SelectTrigger>
              <SelectContent>
                {jobsData?.items.map((j) => (
                  <SelectItem key={j.id} value={j.id}>
                    {j.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <ExportMenu jobId={jobId} jobTitle={currentJob?.title} size="sm" />
        </div>
      </div>

      {taskId && <UnmatchedFilesPanel taskId={taskId} jobId={jobId} />}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="lg:col-span-3">
          <CandidateListPanel
            jobId={jobId}
            selectedId={selectedCandidateId}
            onSelect={selectCandidate}
          />
        </div>
        <div className="lg:col-span-5">
          <FilePreviewPanel
            candidateId={selectedCandidateId}
            selectedFileId={selectedFileId}
            onSelectFile={setSelectedFileId}
          />
        </div>
        <div className="lg:col-span-4">
          <CandidateDetailPanel
            candidateId={selectedCandidateId}
            jobId={jobId}
          />
        </div>
      </div>
    </div>
  )
}
