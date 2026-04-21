// frontend/src/components/ErrorLog.tsx

interface Props {
  erros: string[];
}

export function ErrorLog({ erros }: Props) {
  if (erros.length === 0) return null;

  return (
    <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4">
      <p className="mb-2 text-sm font-semibold text-red-700">
        {erros.length} arquivo{erros.length > 1 ? "s" : ""} com erro
      </p>
      <ul className="space-y-1">
        {erros.map((e, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-red-600">
            <span className="mt-0.5 shrink-0 text-red-400">✕</span>
            <span>{e}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
