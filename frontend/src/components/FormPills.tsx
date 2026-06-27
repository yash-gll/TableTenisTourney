/** Recent form as W/L pills, most-recent first. */
export function FormPills({ form }: { form: string[] }) {
  if (!form.length) return <span className="text-sm text-slate-400">No matches yet</span>;
  return (
    <div className="flex gap-1">
      {form.map((r, i) => (
        <span
          key={i}
          className={`flex h-6 w-6 items-center justify-center rounded text-xs font-bold text-white ${
            r === "W" ? "bg-emerald-500" : "bg-rose-400"
          }`}
        >
          {r}
        </span>
      ))}
    </div>
  );
}
