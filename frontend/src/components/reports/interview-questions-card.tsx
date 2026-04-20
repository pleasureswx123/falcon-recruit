"use client"

import { MessageSquare } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { InterviewQuestion } from "@/lib/api/reports"

interface Props {
  questions: InterviewQuestion[]
}

export function InterviewQuestionsCard({ questions }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MessageSquare className="h-4 w-4 text-muted-foreground" />
          面试建议
        </CardTitle>
      </CardHeader>
      <CardContent>
        {questions.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            暂无针对性面试问题
          </div>
        ) : (
          <ol className="flex flex-col gap-3">
            {questions.map((q, idx) => (
              <li
                key={idx}
                className="flex gap-3 rounded-md border bg-muted/30 p-3"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {idx + 1}
                </span>
                <div className="flex flex-col gap-1">
                  <Badge variant="secondary" className="w-fit text-[10px]">
                    {q.topic}
                  </Badge>
                  <p className="text-sm leading-relaxed text-foreground/90">
                    {q.question}
                  </p>
                  {q.intent ? (
                    <p className="text-xs leading-relaxed text-muted-foreground">
                      <span className="mr-1 font-medium">考察意图：</span>
                      {q.intent}
                    </p>
                  ) : null}
                </div>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}
