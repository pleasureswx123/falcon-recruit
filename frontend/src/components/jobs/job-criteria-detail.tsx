import {
  Briefcase,
  GraduationCap,
  HeartHandshake,
  MapPin,
  Sparkles,
  TrendingUp,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import type {
  EducationLevel,
  JobCriteria,
  SkillLevel,
  SkillRequirement,
} from "@/lib/api/jobs"

const EDUCATION_LABEL: Record<EducationLevel, string> = {
  unlimited: "学历不限",
  college: "大专",
  bachelor: "本科",
  master: "硕士",
  phd: "博士",
}

const SKILL_LEVEL_LABEL: Record<SkillLevel, string> = {
  required: "必备",
  preferred: "期望",
  bonus: "加分",
}

function formatYears(min: number, max: number | null) {
  if (!max && !min) return "经验不限"
  if (!max) return `${min}+ 年`
  if (min === max) return `${min} 年`
  return `${min}-${max} 年`
}

function formatSalary(salary: JobCriteria["salary"]) {
  if (!salary.min && !salary.max) return "面议"
  if (salary.min && salary.max) return `${salary.min}-${salary.max} K/月`
  if (salary.min) return `${salary.min}K+ /月`
  return `至多 ${salary.max}K/月`
}

interface SectionProps {
  icon: React.ComponentType<{ className?: string }>
  title: string
  children: React.ReactNode
}

function Section({ icon: Icon, title, children }: SectionProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-sm font-medium">
        <Icon className="h-4 w-4 text-muted-foreground" />
        {title}
      </div>
      <div className="pl-6">{children}</div>
    </div>
  )
}

function SkillGroup({
  level,
  items,
}: {
  level: SkillLevel
  items: SkillRequirement[]
}) {
  if (items.length === 0) return null
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs font-medium text-muted-foreground">
        {SKILL_LEVEL_LABEL[level]}（{items.length}）
      </div>
      <div className="flex flex-col gap-2">
        {items.map((s) => (
          <div key={s.name} className="flex items-center gap-3">
            <Badge
              variant={level === "required" ? "default" : "secondary"}
              className="min-w-[90px] justify-center font-normal"
            >
              {s.name}
            </Badge>
            <Progress value={s.weight * 10} className="h-1.5 flex-1" />
            <span className="w-8 text-right text-xs text-muted-foreground">
              {s.weight}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function JobCriteriaDetail({ criteria }: { criteria: JobCriteria }) {
  const required = criteria.skills.filter((s) => s.level === "required")
  const preferred = criteria.skills.filter((s) => s.level === "preferred")
  const bonus = criteria.skills.filter((s) => s.level === "bonus")

  return (
    <div className="flex flex-col gap-6">
      <Section icon={GraduationCap} title="硬性条件">
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="font-normal">
            {EDUCATION_LABEL[criteria.education]}
          </Badge>
          <Badge variant="outline" className="font-normal">
            {formatYears(criteria.years_min, criteria.years_max)}
          </Badge>
        </div>
      </Section>

      <Separator />

      <Section icon={Briefcase} title="专业背景">
        {criteria.skills.length === 0 ? (
          <div className="text-xs text-muted-foreground">未设置技能要求</div>
        ) : (
          <div className="flex flex-col gap-4">
            <SkillGroup level="required" items={required} />
            <SkillGroup level="preferred" items={preferred} />
            <SkillGroup level="bonus" items={bonus} />
            {criteria.industries.length > 0 && (
              <div className="flex flex-col gap-2">
                <div className="text-xs font-medium text-muted-foreground">
                  行业背景
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {criteria.industries.map((i) => (
                    <Badge key={i} variant="outline" className="font-normal">
                      {i}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Section>

      <Separator />

      <Section icon={TrendingUp} title="稳定性">
        <div className="text-sm">
          {criteria.min_tenure_months
            ? `期望平均在职 ≥ ${criteria.min_tenure_months} 个月`
            : "未设置"}
        </div>
      </Section>

      <Separator />

      <Section icon={HeartHandshake} title="软技能">
        {criteria.soft_skills.length === 0 ? (
          <div className="text-xs text-muted-foreground">未设置</div>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {criteria.soft_skills.map((s) => (
              <Badge key={s} variant="outline" className="font-normal">
                <Sparkles className="mr-1 h-3 w-3" />
                {s}
              </Badge>
            ))}
          </div>
        )}
      </Section>

      <Separator />

      <Section icon={MapPin} title="期望契合">
        <div className="flex flex-col gap-1 text-sm">
          <div>薪资：{formatSalary(criteria.salary)}</div>
          <div>地点：{criteria.location || "不限"}</div>
        </div>
      </Section>
    </div>
  )
}
