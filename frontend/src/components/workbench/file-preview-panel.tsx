"use client"

import * as React from "react"
import { Download, FileText } from "lucide-react"

import {
  FILE_TYPE_LABEL,
  PARSE_STATUS_LABEL,
  fileDownloadUrl,
  filePreviewUrl,
} from "@/lib/api/candidates"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useCandidate } from "@/lib/hooks/use-candidates"
import { cn } from "@/lib/utils"

interface Props {
  candidateId?: string
  selectedFileId?: string
  onSelectFile: (id: string) => void
}

export function FilePreviewPanel({
  candidateId,
  selectedFileId,
  onSelectFile,
}: Props) {
  const { data, isLoading } = useCandidate(candidateId)

  const files = React.useMemo(() => data?.files ?? [], [data])
  const activeFileId = selectedFileId ?? files[0]?.id
  const activeFile = files.find((f) => f.id === activeFileId)

  React.useEffect(() => {
    if (!selectedFileId && files[0]) {
      onSelectFile(files[0].id)
    }
  }, [files, selectedFileId, onSelectFile])

  if (!candidateId) {
    return (
      <Card className="h-full">
        <CardContent className="flex h-[640px] items-center justify-center text-sm text-muted-foreground">
          从左侧选择一位候选人以查看文件
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <FileText className="h-4 w-4 text-muted-foreground" />
          文件预览
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-3 pb-3">
        {isLoading ? (
          <Skeleton className="h-10 w-full" />
        ) : files.length === 0 ? (
          <div className="rounded-md border border-dashed px-3 py-6 text-center text-xs text-muted-foreground">
            该候选人暂无文件
          </div>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {files.map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => onSelectFile(f.id)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs transition",
                  activeFileId === f.id
                    ? "border-primary bg-primary/5 text-primary"
                    : "hover:bg-muted/60"
                )}
                title={f.original_name}
              >
                <span className="rounded bg-muted px-1 text-[10px]">
                  {FILE_TYPE_LABEL[f.file_type]}
                </span>
                <span className="max-w-[140px] truncate">
                  {f.new_name ?? f.original_name}
                </span>
              </button>
            ))}
          </div>
        )}

        {activeFile && (
          <>
            <div className="flex items-center justify-between gap-2 rounded-md border bg-muted/30 px-3 py-2 text-xs">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[10px]">
                  {FILE_TYPE_LABEL[activeFile.file_type]}
                </Badge>
                <Badge
                  variant="outline"
                  className={cn(
                    "text-[10px]",
                    activeFile.parse_status === "parsed" &&
                      "border-emerald-200 bg-emerald-50 text-emerald-700",
                    activeFile.parse_status === "failed" &&
                      "border-rose-200 bg-rose-50 text-rose-700"
                  )}
                >
                  {PARSE_STATUS_LABEL[activeFile.parse_status]}
                </Badge>
                <span className="text-muted-foreground">
                  {(activeFile.size / 1024).toFixed(1)} KB
                </span>
              </div>
              <Button variant="outline" size="sm" asChild>
                <a
                  href={fileDownloadUrl(activeFile.id)}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Download className="mr-1 h-3.5 w-3.5" />
                  下载
                </a>
              </Button>
            </div>

            {activeFile.parse_status === "parsed" &&
            (activeFile.mime === "application/pdf" ||
              activeFile.original_name.toLowerCase().endsWith(".pdf")) ? (
              <iframe
                key={activeFile.id}
                src={filePreviewUrl(activeFile.id)}
                className="h-[480px] w-full rounded-md border bg-white"
                title={activeFile.original_name}
              />
            ) : (
              <div className="flex h-[480px] flex-col gap-2 overflow-auto rounded-md border bg-muted/20 p-3 text-xs leading-relaxed">
                <div className="font-medium text-muted-foreground">
                  文本摘要
                </div>
                <pre className="whitespace-pre-wrap break-words font-sans">
                  {activeFile.text_excerpt ?? "（暂无文本摘要）"}
                </pre>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
