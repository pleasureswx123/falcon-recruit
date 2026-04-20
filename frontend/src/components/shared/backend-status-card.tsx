"use client"

import { CircleAlert, CircleCheck, CircleDashed, Server } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { API_BASE_URL } from "@/lib/api/client"
import { useHealth } from "@/lib/hooks/use-health"

export function BackendStatusCard() {
  const { data, isLoading, isError, error, dataUpdatedAt } = useHealth()

  const statusNode = (() => {
    if (isLoading) {
      return (
        <Badge variant="secondary" className="gap-1">
          <CircleDashed className="h-3 w-3 animate-spin" />
          探测中
        </Badge>
      )
    }
    if (isError) {
      return (
        <Badge variant="destructive" className="gap-1">
          <CircleAlert className="h-3 w-3" />
          未连接
        </Badge>
      )
    }
    return (
      <Badge className="gap-1 bg-emerald-500 hover:bg-emerald-500">
        <CircleCheck className="h-3 w-3" />
        已连接
      </Badge>
    )
  })()

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
        <div className="flex flex-col gap-1">
          <CardTitle className="flex items-center gap-2 text-base">
            <Server className="h-4 w-4 text-muted-foreground" />
            后端服务状态
          </CardTitle>
          <CardDescription className="text-xs">
            {API_BASE_URL}
          </CardDescription>
        </div>
        {statusNode}
      </CardHeader>
      <CardContent className="text-xs text-muted-foreground">
        {isLoading ? (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-3 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        ) : isError ? (
          <div className="text-destructive">
            {error?.message ?? "无法连接到后端服务"}
          </div>
        ) : data ? (
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <span>应用名称</span>
            <span className="text-foreground">{data.app_name}</span>
            <span>运行环境</span>
            <span className="text-foreground">{data.app_env}</span>
            <span>版本</span>
            <span className="text-foreground">{data.app_version}</span>
            <span>最近探测</span>
            <span className="text-foreground">
              {dataUpdatedAt
                ? new Date(dataUpdatedAt).toLocaleTimeString("zh-CN")
                : "—"}
            </span>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
