"use client"

import { Check, X } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type { JobCriteria, SkillLevel } from "@/lib/api/jobs"
import { cn } from "@/lib/utils"

interface Props {
  candidateSkills: string[]
  criteria: JobCriteria | undefined
}

const LEVEL_LABEL: Record<SkillLevel, string> = {
  required: "必备",
  preferred: "期望",
  bonus: "加分",
}

export function SkillMatchCard({ candidateSkills, criteria }: Props) {
  const have = new Set(candidateSkills.map((s) => s.toLowerCase()))
  const groups: { level: SkillLevel; items: { name: string; hit: boolean }[] }[] =
    []

  if (criteria) {
    for (const lvl of ["required", "preferred", "bonus"] as SkillLevel[]) {
      const items = criteria.skills
        .filter((s) => s.level === lvl)
        .map((s) => ({ name: s.name, hit: have.has(s.name.toLowerCase()) }))
      if (items.length > 0) groups.push({ level: lvl, items })
    }
  }

  // 候选人额外掌握但职位未要求的
  const required = new Set(
    (criteria?.skills ?? []).map((s) => s.name.toLowerCase())
  )
  const extras = candidateSkills.filter(
    (s) => !required.has(s.toLowerCase())
  )

  const allNeeded =
    criteria?.skills.filter((s) => s.level !== "bonus") ?? []
  const hitCount = allNeeded.filter((s) =>
    have.has(s.name.toLowerCase())
  ).length
  const coverage =
    allNeeded.length === 0 ? 0 : Math.round((hitCount / allNeeded.length) * 100)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-baseline justify-between text-base">
          <span>技能匹配</span>
          {allNeeded.length > 0 && (
            <span className="text-xs font-normal text-muted-foreground">
              覆盖度 {coverage}% ({hitCount}/{allNeeded.length})
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {!criteria || criteria.skills.length === 0 ? (
          <div className="text-xs text-muted-foreground">
            该职位未设置技能要求
          </div>
        ) : (
          groups.map((g) => (
            <div key={g.level} className="flex flex-col gap-1.5">
              <div className="text-xs font-medium text-muted-foreground">
                {LEVEL_LABEL[g.level]}（{g.items.filter((i) => i.hit).length}/
                {g.items.length}）
              </div>
              <div className="flex flex-wrap gap-1.5">
                {g.items.map((i) => (
                  <Badge
                    key={i.name}
                    variant="outline"
                    className={cn(
                      "gap-1 font-normal",
                      i.hit
                        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                        : "border-rose-200 bg-rose-50 text-rose-700"
                    )}
                  >
                    {i.hit ? (
                      <Check className="h-3 w-3" />
                    ) : (
                      <X className="h-3 w-3" />
                    )}
                    {i.name}
                  </Badge>
                ))}
              </div>
            </div>
          ))
        )}

        {extras.length > 0 && (
          <>
            <Separator />
            <div className="flex flex-col gap-1.5">
              <div className="text-xs font-medium text-muted-foreground">
                额外技能（{extras.length}）
              </div>
              <div className="flex flex-wrap gap-1.5">
                {extras.map((s) => (
                  <Badge
                    key={s}
                    variant="outline"
                    className="font-normal text-muted-foreground"
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
