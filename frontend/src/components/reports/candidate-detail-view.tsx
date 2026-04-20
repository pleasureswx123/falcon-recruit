"use client"

import Link from "next/link"
import { ArrowLeft, RefreshCw, Sparkles, TrendingUp } from "lucide-react"
import { toast } from "sonner"

import { CandidateInfoCard } from "@/components/reports/candidate-info-card"
import { DimensionBreakdown } from "@/components/reports/dimension-breakdown"
import { ExperienceTimeline } from "@/components/reports/experience-timeline"
import { InterviewQuestionsCard } from "@/components/reports/interview-questions-card"
import { ScoreBadge } from "@/components/reports/score-badge"
import { ScoreRadar } from "@/components/reports/score-radar"
import { SkillMatchCard } from "@/components/reports/skill-match-card"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useCandidate } from "@/lib/hooks/use-candidates"
import {
  useCandidateReport,
  useRefreshCandidateReport,
} from "@/lib/hooks/use-candidate-report"
import { useJob } from "@/lib/hooks/use-jobs"

interface Props {
  candidateId: string
}

export function CandidateDetailView({ candidateId }: Props) {
  const {
    data: candidate,
    isLoading: loadingCandidate,
    isError: candidateErr,
  } = useCandidate(candidateId)
  const { data: report, isLoading: loadingReport } =
    useCandidateReport(candidateId)
  const { data: job } = useJob(candidate?.job_id)
  const refreshMutation = useRefreshCandidateReport(candidateId)

  async function handleRefresh() {
    try {
      await refreshMutation.mutateAsync()
      toast.success("已重新计算评分")
    } catch (err) {
      toast.error((err as { message?: string })?.message ?? "重算失败")
    }
  }

  if (loadingCandidate || loadingReport) {
    return <DetailSkeleton />
  }

  if (candidateErr || !candidate) {
    return (
      <div className="flex flex-col items-start gap-3">
        <BackLink jobId={undefined} />
        <div className="rounded-md border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          候选人不存在或已被删除
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="flex flex-col gap-4">
        <BackLink jobId={candidate.job_id} />
        <div className="rounded-md border bg-muted/30 px-4 py-6 text-sm text-muted-foreground">
          尚未生成 AI 画像报告，点击&nbsp;
          <Button
            size="sm"
            variant="link"
            className="h-auto p-0"
            onClick={handleRefresh}
            disabled={refreshMutation.isPending}
          >
            立即生成
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <BackLink jobId={candidate.job_id} />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-2xl font-semibold tracking-tight">
              {candidate.name ?? "未识别候选人"}
            </h2>
            <ScoreBadge score={report.total_score} size="lg" />
            {candidate.is_verified && (
              <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">
                已核验
              </span>
            )}
          </div>
          <div className="text-xs text-muted-foreground">
            {job?.title ? `应聘职位：${job.title}` : ""}
            {report.generated_at && (
              <span className="ml-2">
                · 评估时间：
                {new Date(report.generated_at).toLocaleString("zh-CN")}
              </span>
            )}
            <span className="ml-2">· 引擎：{report.engine}</span>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshMutation.isPending}
        >
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          重新评估
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              五维评分
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <div className="mx-auto h-[320px] w-[320px] max-w-full">
              <ScoreRadar dimensions={report.dimensions} />
            </div>
            <div className="flex flex-1 flex-col gap-3">
              <HighlightBlock
                title="核心优势"
                items={report.strengths}
                tone="pos"
              />
              <HighlightBlock
                title="主要不足"
                items={report.weaknesses}
                tone="neg"
              />
            </div>
          </CardContent>
        </Card>

        <CandidateInfoCard
          candidate={candidate}
          profile={report.profile}
          verification={report.verification}
        />
      </div>

      <DimensionBreakdown dimensions={report.dimensions} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ExperienceTimeline
            experiences={report.profile.experiences}
            educations={report.profile.educations}
            gaps={report.verification.gaps}
          />
        </div>
        <SkillMatchCard
          candidateSkills={report.profile.skills}
          criteria={job?.criteria}
        />
      </div>

      <InterviewQuestionsCard questions={report.interview_questions} />
    </div>
  )
}

function BackLink({ jobId }: { jobId: string | undefined }) {
  const href = jobId ? `/workbench?jobId=${jobId}` : "/candidates"
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
    >
      <ArrowLeft className="h-4 w-4" />
      {jobId ? "返回工作台" : "返回候选人列表"}
    </Link>
  )
}

function HighlightBlock({
  title,
  items,
  tone,
}: {
  title: string
  items: string[]
  tone: "pos" | "neg"
}) {
  const color =
    tone === "pos"
      ? "border-emerald-200 bg-emerald-50/50 text-emerald-800"
      : "border-rose-200 bg-rose-50/50 text-rose-800"
  return (
    <div className={`rounded-md border px-3 py-2 ${color}`}>
      <div className="mb-1 flex items-center gap-1.5 text-xs font-medium">
        <Sparkles className="h-3 w-3" />
        {title}
      </div>
      {items.length === 0 ? (
        <div className="text-xs opacity-70">—</div>
      ) : (
        <ul className="flex flex-col gap-0.5">
          {items.map((s, i) => (
            <li key={i} className="text-xs leading-relaxed">
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function DetailSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <Skeleton className="h-6 w-40" />
      <Skeleton className="h-10 w-64" />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Skeleton className="h-[400px] lg:col-span-2" />
        <Skeleton className="h-[400px]" />
      </div>
      <Skeleton className="h-48 w-full" />
    </div>
  )
}
