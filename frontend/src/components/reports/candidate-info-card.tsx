"use client"

import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Mail,
  MapPin,
  Phone,
  Wallet,
} from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type { CandidateDetail } from "@/lib/api/candidates"
import type { VerificationReport } from "@/lib/api/reports"

interface Props {
  candidate: CandidateDetail
  profile: {
    total_years: number
    expected_salary: string | null
    expected_location: string | null
    location: string | null
  }
  verification: VerificationReport
}

export function CandidateInfoCard({
  candidate,
  profile,
  verification,
}: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">基本信息</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 text-sm">
        <InfoRow icon={Phone} label="手机号" value={candidate.phone} />
        <InfoRow icon={Mail} label="邮箱" value={candidate.email} />
        {candidate.wechat && (
          <InfoRow icon={Mail} label="微信" value={candidate.wechat} />
        )}
        <InfoRow
          icon={CalendarDays}
          label="累计经验"
          value={
            profile.total_years > 0
              ? `${profile.total_years.toFixed(1)} 年`
              : "—"
          }
        />
        <InfoRow
          icon={CalendarDays}
          label="平均在职"
          value={
            verification.average_tenure_months > 0
              ? `${verification.average_tenure_months.toFixed(1)} 个月`
              : "—"
          }
        />
        <InfoRow
          icon={Wallet}
          label="期望薪资"
          value={profile.expected_salary}
        />
        <InfoRow
          icon={MapPin}
          label="期望地点"
          value={profile.expected_location ?? profile.location}
        />

        <Separator />

        <div className="flex flex-col gap-1.5">
          <div className="text-xs font-medium text-muted-foreground">
            风险提示
          </div>
          {verification.risk_flags.length === 0 ? (
            <div className="flex items-center gap-1.5 text-xs text-emerald-700">
              <CheckCircle2 className="h-3.5 w-3.5" />
              暂无显著风险
            </div>
          ) : (
            <ul className="flex flex-col gap-1">
              {verification.risk_flags.map((f, i) => (
                <li
                  key={i}
                  className="flex items-start gap-1.5 text-xs text-rose-700"
                >
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string | null | undefined
}) {
  return (
    <div className="flex items-center gap-2.5">
      <Icon className="h-3.5 w-3.5 text-muted-foreground" />
      <span className="w-16 shrink-0 text-xs text-muted-foreground">
        {label}
      </span>
      <span className="flex-1 truncate text-sm">{value || "—"}</span>
    </div>
  )
}
