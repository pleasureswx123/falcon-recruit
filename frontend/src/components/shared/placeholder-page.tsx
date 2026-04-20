import { Construction } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"

interface PlaceholderPageProps {
  title: string
  description: string
  phase: string
}

export function PlaceholderPage({
  title,
  description,
  phase,
}: PlaceholderPageProps) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <Card>
        <CardContent className="flex h-64 flex-col items-center justify-center gap-3 text-sm text-muted-foreground">
          <Construction className="h-10 w-10" />
          <p>此模块将在 {phase} 上线</p>
        </CardContent>
      </Card>
    </div>
  )
}
