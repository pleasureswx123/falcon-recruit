"use client"

import * as React from "react"
import Link from "next/link"
import { CheckCircle2, ExternalLink, Save, UserCog } from "lucide-react"
import { toast } from "sonner"

import { ScoreBadge } from "@/components/reports/score-badge"
import { ReassignFileDialog } from "@/components/workbench/reassign-file-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import {
  useCandidate,
  useUpdateCandidate,
} from "@/lib/hooks/use-candidates"

interface Props {
  candidateId?: string
  jobId: string
}

interface FormState {
  name: string
  phone: string
  email: string
  wechat: string
}

export function CandidateDetailPanel({ candidateId, jobId }: Props) {
  const { data: candidate, isLoading } = useCandidate(candidateId)
  const updateMutation = useUpdateCandidate(candidateId ?? "")

  const [form, setForm] = React.useState<FormState>({
    name: "",
    phone: "",
    email: "",
    wechat: "",
  })
  const [reassignFileId, setReassignFileId] = React.useState<string | null>(
    null
  )

  React.useEffect(() => {
    if (!candidate) return
    setForm({
      name: candidate.name ?? "",
      phone: candidate.phone ?? "",
      email: candidate.email ?? "",
      wechat: candidate.wechat ?? "",
    })
  }, [candidate])

  if (!candidateId) {
    return (
      <Card className="h-full">
        <CardContent className="flex h-[640px] items-center justify-center text-sm text-muted-foreground">
          选择候选人以查看详情与纠偏
        </CardContent>
      </Card>
    )
  }

  async function handleSave() {
    try {
      await updateMutation.mutateAsync({
        name: form.name.trim() || null,
        phone: form.phone.trim() || null,
        email: form.email.trim() || null,
        wechat: form.wechat.trim() || null,
      })
      toast.success("已保存")
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "保存失败")
    }
  }

  async function handleVerify() {
    try {
      await updateMutation.mutateAsync({
        is_verified: !(candidate?.is_verified ?? false),
      })
      toast.success(candidate?.is_verified ? "已取消核验" : "已标记为已核验")
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "操作失败")
    }
  }

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <UserCog className="h-4 w-4 text-muted-foreground" />
            解析详情与纠偏
          </span>
          <div className="flex items-center gap-2">
            <ScoreBadge score={candidate?.score} size="sm" showLabel={false} />
            <Link
              href={`/candidates/${candidateId}`}
              className="inline-flex items-center gap-0.5 text-xs text-primary hover:underline"
              title="查看完整 AI 画像"
            >
              画像
              <ExternalLink className="h-3 w-3" />
            </Link>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {isLoading ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <>
            <FormField label="姓名">
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="未识别"
              />
            </FormField>
            <FormField label="手机号">
              <Input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="未识别"
              />
            </FormField>
            <FormField label="邮箱">
              <Input
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="未识别"
              />
            </FormField>
            <FormField label="微信">
              <Input
                value={form.wechat}
                onChange={(e) => setForm({ ...form, wechat: e.target.value })}
                placeholder="未识别"
              />
            </FormField>

            <div className="flex gap-2 pt-1">
              <Button
                size="sm"
                onClick={handleSave}
                disabled={updateMutation.isPending}
              >
                <Save className="mr-1 h-3.5 w-3.5" />
                保存修改
              </Button>
              <Button
                size="sm"
                variant={candidate?.is_verified ? "secondary" : "outline"}
                onClick={handleVerify}
                disabled={updateMutation.isPending}
              >
                <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                {candidate?.is_verified ? "取消核验" : "标记核验"}
              </Button>
            </div>

            <div className="mt-2 border-t pt-3">
              <div className="mb-2 text-xs font-medium text-muted-foreground">
                关联文件（{candidate?.files.length ?? 0} 份）
              </div>
              <div className="flex flex-col gap-1.5">
                {candidate?.files.map((f) => (
                  <div
                    key={f.id}
                    className="flex items-center justify-between gap-2 rounded-md border px-2.5 py-1.5 text-xs"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium">
                        {f.new_name ?? f.original_name}
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        {f.zip_member}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 text-xs"
                      onClick={() => setReassignFileId(f.id)}
                    >
                      改挂
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        <ReassignFileDialog
          open={Boolean(reassignFileId)}
          onOpenChange={(o) => !o && setReassignFileId(null)}
          fileId={reassignFileId ?? ""}
          jobId={jobId}
          excludeCandidateId={candidateId}
        />
      </CardContent>
    </Card>
  )
}

function FormField({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      {children}
    </div>
  )
}
