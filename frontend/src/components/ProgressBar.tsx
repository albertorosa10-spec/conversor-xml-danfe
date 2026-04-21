// frontend/src/components/ProgressBar.tsx

interface Props {
  processando: boolean;
  mensagem?: string;
}

export function ProgressBar({ processando, mensagem }: Props) {
  if (!processando) return null;

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-gray-600">{mensagem ?? "Processando..."}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <div className="h-full w-full origin-left animate-pulse rounded-full bg-blue-500" />
      </div>
    </div>
  );
}
