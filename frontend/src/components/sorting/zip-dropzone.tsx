"use client"

import * as React from "react"
import { Loader2, UploadCloud } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

interface Props {
  disabled?: boolean
  isUploading: boolean
  uploadProgress: number
  onFileSelected: (file: File) => void
  maxMb?: number
}

const ACCEPT_MIME =
  "application/zip,application/x-zip-compressed,application/octet-stream"

export function ZipDropzone({
  disabled,
  isUploading,
  uploadProgress,
  onFileSelected,
  maxMb = 200,
}: Props) {
  const inputRef = React.useRef<HTMLInputElement | null>(null)
  const [dragOver, setDragOver] = React.useState(false)

  function validateAndSubmit(file: File | null | undefined) {
    if (!file) return
    if (!file.name.toLowerCase().endsWith(".zip")) {
      toast.error("仅支持 .zip 压缩包")
      return
    }
    const mb = file.size / 1024 / 1024
    if (mb > maxMb) {
      toast.error(`文件过大（${mb.toFixed(1)} MB），上限 ${maxMb} MB`)
      return
    }
    onFileSelected(file)
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragOver(false)
    if (disabled || isUploading) return
    validateAndSubmit(e.dataTransfer.files?.[0])
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => !disabled && !isUploading && inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          if (!disabled && !isUploading) inputRef.current?.click()
        }
      }}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled && !isUploading) setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
      className={cn(
        "flex min-h-[140px] cursor-pointer flex-col items-center justify-center gap-2",
        "rounded-lg border-2 border-dashed px-4 py-6 text-center transition",
        dragOver
          ? "border-primary bg-primary/5"
          : "border-muted-foreground/30 hover:border-primary/50 hover:bg-muted/40",
        (disabled || isUploading) && "pointer-events-none opacity-60"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT_MIME + ",.zip"}
        className="hidden"
        onChange={(e) => {
          validateAndSubmit(e.target.files?.[0])
          e.target.value = ""
        }}
      />
      {isUploading ? (
        <div className="flex w-full max-w-sm flex-col items-center gap-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            正在上传 {uploadProgress}%
          </div>
          <Progress value={uploadProgress} className="h-1.5 w-full" />
        </div>
      ) : (
        <>
          <UploadCloud className="h-8 w-8 text-muted-foreground" />
          <div className="text-sm font-medium">
            拖拽 ZIP 到这里，或
            <Button
              type="button"
              variant="link"
              size="sm"
              className="h-auto px-1"
              onClick={(e) => {
                e.stopPropagation()
                inputRef.current?.click()
              }}
            >
              点击选择文件
            </Button>
          </div>
          <div className="text-xs text-muted-foreground">
            支持 PDF / DOCX / TXT 混合压缩包，单包 ≤ {maxMb} MB
          </div>
        </>
      )}
    </div>
  )
}
