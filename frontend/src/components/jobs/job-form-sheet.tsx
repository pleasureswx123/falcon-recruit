"use client"

import * as React from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { ChevronDown, ChevronUp, Loader2, Sparkles, Wand2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { JobCriteriaSummary } from "@/components/jobs/job-criteria-summary"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Textarea } from "@/components/ui/textarea"
import type { Job, JobCriteria } from "@/lib/api/jobs"
import {
  useCreateJob,
  useGenerateJd,
  useParseJd,
  useUpdateJob,
} from "@/lib/hooks/use-jobs"

const schema = z.object({
  title: z.string().min(1, "请输入职位名称").max(120),
  raw_jd: z.string().min(10, "JD 至少 10 个字符"),
})
type FormValues = z.infer<typeof schema>

interface JobFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  mode: "create" | "edit"
  job?: Job
}

export function JobFormSheet({
  open,
  onOpenChange,
  mode,
  job,
}: JobFormSheetProps) {
  const [preview, setPreview] = React.useState<JobCriteria | null>(null)
  // AI 写 JD 区域状态
  const [genOpen, setGenOpen] = React.useState(false)
  const [genHint, setGenHint] = React.useState("")

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: "", raw_jd: "" },
  })

  React.useEffect(() => {
    if (open) {
      form.reset({
        title: job?.title ?? "",
        raw_jd: job?.raw_jd ?? "",
      })
      setPreview(job?.criteria ?? null)
      setGenOpen(false)
      setGenHint("")
    }
  }, [open, job, form])

  const parse = useParseJd()
  const generate = useGenerateJd()
  const create = useCreateJob()
  const update = useUpdateJob(job?.id ?? "")

  const submitting = create.isPending || update.isPending
  const parsing = parse.isPending
  const generating = generate.isPending

  async function handleGenerate() {
    const title = form.getValues("title")
    if (!title || !title.trim()) {
      form.setError("title", { message: "请先填写职位名称" })
      return
    }
    if (!genHint.trim()) return
    try {
      const jdText = await generate.mutateAsync({
        title: title.trim(),
        description: genHint.trim(),
      })
      form.setValue("raw_jd", jdText, { shouldDirty: true })
      setGenOpen(false)
      toast.success("JD 已生成，请检查并按需修改后保存")
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "生成失败，请稍后重试")
    }
  }

  async function handlePreview() {
    const raw = form.getValues("raw_jd")
    if (!raw || raw.trim().length < 10) {
      form.setError("raw_jd", { message: "JD 至少 10 个字符" })
      return
    }
    try {
      const criteria = await parse.mutateAsync(raw)
      setPreview(criteria)
      toast.success("AI 基准预览已生成")
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "解析失败")
    }
  }

  async function onSubmit(values: FormValues) {
    try {
      if (mode === "create") {
        await create.mutateAsync({
          ...values,
          criteria: preview ?? null,
        })
        toast.success("职位已创建")
      } else if (job) {
        await update.mutateAsync({
          title: values.title,
          raw_jd: values.raw_jd,
          criteria: preview ?? undefined,
        })
        toast.success("职位已更新")
      }
      onOpenChange(false)
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "保存失败")
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full overflow-y-auto sm:max-w-[640px]"
      >
        <SheetHeader>
          <SheetTitle>{mode === "create" ? "创建职位" : "编辑职位"}</SheetTitle>
          <SheetDescription>
            填写 JD 后点击「AI 解析」生成结构化匹配基准，保存即入库
          </SheetDescription>
        </SheetHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="mt-6 flex flex-col gap-5"
          >
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>职位名称</FormLabel>
                  <FormControl>
                    <Input placeholder="高级前端工程师" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* AI 帮我写 JD 区域 */}
            <div className="rounded-md border border-dashed bg-muted/30">
              <button
                type="button"
                onClick={() => setGenOpen((v) => !v)}
                className="flex w-full items-center justify-between px-3 py-2 text-left"
              >
                <div className="flex items-center gap-2">
                  <Wand2 className="h-3.5 w-3.5 text-indigo-500" />
                  <span className="text-xs font-medium">AI 帮我写 JD</span>
                  <span className="text-xs text-muted-foreground">
                    不知道怎么写？输入基本要求，AI 自动生成
                  </span>
                </div>
                {genOpen ? (
                  <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                )}
              </button>

              {genOpen && (
                <div className="flex flex-col gap-2 border-t px-3 pb-3 pt-2">
                  <p className="text-xs text-muted-foreground">
                    用一句话描述招聘需求，例如：招 Java 后端 3 年经验，熟悉 Spring Boot 和 MySQL，上海，15~25K
                  </p>
                  <Textarea
                    rows={3}
                    placeholder="在这里输入岗位的基本要求……"
                    className="resize-none text-xs"
                    value={genHint}
                    onChange={(e) => setGenHint(e.target.value)}
                    disabled={generating}
                  />
                  <div className="flex items-center justify-between">
                    <p className="text-[11px] text-muted-foreground">
                      生成结果仅供参考，请在 JD 文本框内按需修改后再保存
                    </p>
                    <Button
                      type="button"
                      size="sm"
                      onClick={handleGenerate}
                      disabled={generating || !genHint.trim()}
                    >
                      {generating ? (
                        <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Wand2 className="mr-1.5 h-3.5 w-3.5" />
                      )}
                      {generating ? "生成中…" : "AI 生成 JD"}
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <FormField
              control={form.control}
              name="raw_jd"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>JD 文本</FormLabel>
                  <FormControl>
                    <Textarea
                      rows={14}
                      placeholder="粘贴或输入岗位 JD 文本（学历、年限、技术栈、软技能、薪资范围、工作地点等）"
                      className="resize-y font-mono text-xs leading-relaxed"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex items-center justify-between rounded-md border border-dashed bg-muted/40 p-3">
              <div className="flex flex-col gap-2">
                <div className="text-xs font-medium">AI 结构化匹配基准</div>
                {preview ? (
                  <JobCriteriaSummary criteria={preview} maxSkills={8} />
                ) : (
                  <div className="text-xs text-muted-foreground">
                    尚未解析
                  </div>
                )}
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handlePreview}
                disabled={parsing}
              >
                {parsing ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Sparkles className="h-3.5 w-3.5" />
                )}
                AI 解析
              </Button>
            </div>

            <SheetFooter className="mt-4 flex flex-row justify-end gap-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => onOpenChange(false)}
                disabled={submitting}
              >
                取消
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting && (
                  <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                )}
                {mode === "create" ? "创建职位" : "保存修改"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  )
}
