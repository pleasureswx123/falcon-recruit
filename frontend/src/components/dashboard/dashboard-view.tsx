"use client"

import { BackendStatusCard } from "@/components/shared/backend-status-card"
import { RecentTasksList } from "@/components/dashboard/recent-tasks-list"
import { StatCards } from "@/components/dashboard/stat-cards"
import { TopCandidatesTable } from "@/components/dashboard/top-candidates-table"
import { useDashboardOverview } from "@/lib/hooks"

export function DashboardView() {
  const { data, isLoading } = useDashboardOverview({
    top_limit: 10,
    recent_limit: 5,
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-semibold tracking-tight">欢迎回来</h2>
        <p className="text-sm text-muted-foreground">
          AI 驱动的简历智能分拣与人岗匹配平台
        </p>
      </div>

      <StatCards stats={data?.stats} isLoading={isLoading} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TopCandidatesTable
            items={data?.top_candidates}
            isLoading={isLoading}
          />
        </div>
        <div className="flex flex-col gap-4">
          <RecentTasksList
            items={data?.recent_tasks}
            isLoading={isLoading}
          />
          <BackendStatusCard />
        </div>
      </div>
    </div>
  )
}
