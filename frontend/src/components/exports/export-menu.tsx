"use client"

import * as React from "react"
import { Download, FileArchive, FileSpreadsheet, Loader2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  downloadExport,
  type ExportFilter,
  type ExportFormat,
} from "@/lib/api/export"

interface Props {
  jobId: string
  jobTitle?: string
  variant?: "default" | "outline" | "secondary"
  size?: "default" | "sm"
  disabled?: boolean
}

export function ExportMenu({
  jobId,
  jobTitle,
  variant = "outline",
  size = "default",
  disabled,
}: Props) {
  const [verifiedOnly, setVerifiedOnly] = React.useState(false)
  const [highScoreOnly, setHighScoreOnly] = React.useState(false)
  const [pending, setPending] = React.useState<ExportFormat | null>(null)

  async function handleDownload(format: ExportFormat) {
    if (pending) return
    setPending(format)
    const filter: ExportFilter = {
      verifiedOnly,
      minScore: highScoreOnly ? 80 : null,
    }
    try {
      const { filename } = await downloadExport(format, jobId, filter)
      toast.success(`已开始下载 ${filename}`)
    } catch (err) {
      const e = err as { status?: number; message?: string }
      if (e.status === 404) {
        toast.error("当前筛选下没有可导出的数据")
      } else {
        toast.error(e.message ?? "导出失败")
      }
    } finally {
      setPending(null)
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={variant}
          size={size}
          disabled={disabled || pending !== null}
        >
          {pending ? (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          ) : (
            <Download className="mr-1.5 h-3.5 w-3.5" />
          )}
          导出
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="text-xs text-muted-foreground">
          {jobTitle ? `职位：${jobTitle}` : "导出选项"}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuCheckboxItem
          checked={verifiedOnly}
          onCheckedChange={(v) => setVerifiedOnly(Boolean(v))}
          onSelect={(e) => e.preventDefault()}
        >
          仅已核验
        </DropdownMenuCheckboxItem>
        <DropdownMenuCheckboxItem
          checked={highScoreOnly}
          onCheckedChange={(v) => setHighScoreOnly(Boolean(v))}
          onSelect={(e) => e.preventDefault()}
        >
          仅 80+ 高分
        </DropdownMenuCheckboxItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => handleDownload("zip")}>
          <FileArchive className="mr-2 h-4 w-4" />
          重命名附件合集 (ZIP)
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => handleDownload("csv")}>
          <FileSpreadsheet className="mr-2 h-4 w-4" />
          候选人评分表 (CSV)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
