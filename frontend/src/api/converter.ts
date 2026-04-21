// frontend/src/api/converter.ts

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface ResultadoConversao {
  zipBlob: Blob;
  totalProcessado: number;
  totalErros: number;
  tempoProcessamento: string;
}

export async function converterXmls(files: File[]): Promise<ResultadoConversao> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));

  const response = await fetch(`${API_BASE}/converter`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = `Erro ${response.status}`;
    try {
      const err = await response.json();
      detail = err.detail ?? detail;
    } catch {
      // resposta não é JSON — usa mensagem genérica
    }
    throw new Error(detail);
  }

  return {
    zipBlob: await response.blob(),
    totalProcessado: parseInt(response.headers.get("X-Total-Processed") ?? "0", 10),
    totalErros: parseInt(response.headers.get("X-Total-Errors") ?? "0", 10),
    tempoProcessamento: response.headers.get("X-Processing-Time") ?? "N/D",
  };
}
