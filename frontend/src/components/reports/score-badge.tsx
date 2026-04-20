import { cn } from "@/lib/utils"
import { scoreBadgeColor } from "@/lib/api/reports"

interface Props {
  score: number | null | undefined
  size?: "sm" | "md" | "lg"
  showLabel?: boolean
  className?: string
}

/**
 * 分数徽章：根据分数段返回「优秀/良好/一般/偏弱」及对应颜色。
 * 用于候选人列表/卡片/详情页通用展示。
 */
export function ScoreBadge({
  score,
  size = "md",
  showLabel = true,
  className,
}: Props) {
  if (score === null || score === undefined) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground",
          className
        )}
      >
        未评分
      </span>
    )
  }

  const { bg, fg, label } = scoreBadgeColor(score)

  const sizeCls =
    size === "lg"
      ? "px-3 py-1 text-base font-semibold"
      : size === "sm"
      ? "px-1.5 py-0.5 text-[11px]"
      : "px-2 py-0.5 text-xs font-medium"

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md",
        bg,
        fg,
        sizeCls,
        className
      )}
    >
      <span className="tabular-nums">{score}</span>
      {showLabel && <span className="opacity-80">· {label}</span>}
    </span>
  )
}
