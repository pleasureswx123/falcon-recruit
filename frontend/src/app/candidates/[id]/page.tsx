import { CandidateDetailView } from "@/components/reports/candidate-detail-view"

interface PageProps {
  params: { id: string }
}

export default function CandidateDetailPage({ params }: PageProps) {
  return <CandidateDetailView candidateId={params.id} />
}
