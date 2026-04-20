import { Badge } from "@/components/ui/badge"
import type { EducationLevel, JobCriteria } from "@/lib/api/jobs"
import { cn } from "@/lib/utils"

const EDUCATION_LABEL: Record<EducationLevel, string> = {
  unlimited: "学历不限",
  college: "大专",
  bachelor: "本科",
  master: "硕士",
  phd: "博士",
}

function formatYears(min: number, max: number | null): string {
  if (!max && !min) return "经验不限"
  if (!max) return `${min}+ 年`
  if (min === max) return `${min} 年`
  return `${min}-${max} 年`
}

interface JobCriteriaSummaryProps {
  criteria: JobCriteria
  maxSkills?: number
  className?: string
}

export function JobCriteriaSummary({
  criteria,
  maxSkills = 4,
  className,
}: JobCriteriaSummaryProps) {
  const topSkills = criteria.skills.slice(0, maxSkills)
  const remain = Math.max(0, criteria.skills.length - topSkills.length)

  return (
    <div className={cn("flex flex-wrap items-center gap-1.5", className)}>
      <Badge variant="outline" className="font-normal">
        {EDUCATION_LABEL[criteria.education]}
      </Badge>
      <Badge variant="outline" className="font-normal">
        {formatYears(criteria.years_min, criteria.years_max)}
      </Badge>
      {topSkills.map((skill) => (
        <Badge
          key={skill.name}
          variant={skill.level === "required" ? "default" : "secondary"}
          className="font-normal"
        >
          {skill.name}
        </Badge>
      ))}
      {remain > 0 && (
        <Badge variant="outline" className="font-normal text-muted-foreground">
          +{remain}
        </Badge>
      )}
    </div>
  )
}
