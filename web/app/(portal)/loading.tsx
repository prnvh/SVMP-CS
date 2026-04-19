export default function PortalLoading() {
  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <div className="h-4 w-28 rounded bg-mist" />
        <div className="h-12 w-full max-w-3xl rounded bg-mist" />
        <div className="h-5 w-full max-w-2xl rounded bg-mist" />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="rounded-[8px] border border-line bg-white p-5">
            <div className="h-4 w-24 rounded bg-mist" />
            <div className="mt-5 h-10 w-20 rounded bg-mist" />
            <div className="mt-4 h-4 w-full rounded bg-mist" />
          </div>
        ))}
      </div>
    </div>
  );
}
