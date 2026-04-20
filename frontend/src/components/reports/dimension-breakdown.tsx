"use client"

import { CheckCircle2, AlertTriangle } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import type { DimensionScore } from "@/lib/api/reports"
import { DIMENSION_ORDER } from "@/lib/api/reports"
import { cn } from "@/lib/utils"

interface Props {
  dimensions: DimensionScore[]
}

function scoreColor(score: number): string {
  if (score >= 85) return "bg-emerald-500"
  if (score >= 70) return "bg-blue-500"
  if (score >= 55) return "bg-amber-500"
  return "bg-rose-500"
}

export function DimensionBreakdown({ dimensions }: Props) {
  const order = new Map(DIMENSION_ORDER.map((d, i) => [d, i]))
  const sorted = [...dimensions].sort(
    (a, b) => (order.get(a.dimension) ?? 0) - (order.get(b.dimension) ?? 0)
  )

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {sorted.map((d) => (
        <Card key={d.dimension}>
          <CardContent className="flex flex-col gap-3 p-4">
            <div className="flex items-baseline justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{d.label}</span>
                <span className="text-[11px] text-muted-foreground">
                  权重 {d.weight}
                </span>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-semibold tabular-nums">
                  {d.score}
                </span>
                <span className="text-xs text-muted-foreground">/100</span>
              </div>
            </div>

            <Progress
              value={d.score}
              className="h-1.5"
              indicatorClassName={cn(scoreColor(d.score))}
            />

            <p className="text-xs text-muted-foreground">{d.reason}</p>

            {d.highlights.length > 0 && (
              <ul className="flex flex-col gap-1">
                {d.highlights.map((h, i) => (
                  <li
                    key={`h-${i}`}
                    className="flex items-start gap-1.5 text-xs text-emerald-700"
                  >
                    <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            )}

            {d.concerns.length > 0 && (
              <ul className="flex flex-col gap-1">
                {d.concerns.map((c, i) => (
                  <li
                    key={`c-${i}`}
                    className="flex items-start gap-1.5 text-xs text-rose-700"
                  >
                    <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
