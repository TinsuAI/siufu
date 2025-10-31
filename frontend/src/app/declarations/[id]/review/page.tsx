export default async function DeclarationReviewPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return (
    <div className="container mx-auto px-6 py-8">
      <h1 className="text-3xl font-bold text-slate-700 mb-4">
        Review Declaration {id}
      </h1>
      <p className="text-slate-600">
        Declaration review interface will be implemented in Story 3.6
      </p>
    </div>
  )
}
