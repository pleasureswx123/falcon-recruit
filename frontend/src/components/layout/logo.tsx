import { Bird } from "lucide-react"

import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  collapsed?: boolean
}

export function Logo({ className, collapsed = false }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Bird className="h-5 w-5" />
      </div>
      {!collapsed && (
        <div className="flex flex-col leading-none">
          <span className="text-sm font-semibold">猎鹰</span>
          <span className="mt-0.5 text-[10px] tracking-wider text-muted-foreground">
            FALCON AI
          </span>
        </div>
      )}
    </div>
  )
}
