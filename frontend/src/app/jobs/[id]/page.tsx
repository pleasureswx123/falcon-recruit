import { JobDetailView } from "@/components/jobs/job-detail-view"

export const metadata = {
  title: "职位详情 · 猎鹰 Falcon AI",
}

interface PageProps {
  params: { id: string }
}

export default function JobDetailPage({ params }: PageProps) {
  return <JobDetailView jobId={params.id} />
}
