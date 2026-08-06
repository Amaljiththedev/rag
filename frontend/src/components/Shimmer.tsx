export function ShimmerBar({ className = "" }: { className?: string }) {
  return <div className={`shimmer rounded-sm ${className}`} />;
}

/** Stands in for an answer while the backend composes it. Line widths are
 *  ragged like set prose rather than uniform bars. */
export function ShimmerAnswer() {
  return (
    <div className="space-y-3" aria-hidden="true">
      <ShimmerBar className="h-4 w-[94%]" />
      <ShimmerBar className="h-4 w-[88%]" />
      <ShimmerBar className="h-4 w-[96%]" />
      <ShimmerBar className="h-4 w-[62%]" />
    </div>
  );
}
