// frontend/src/App.tsx
import { useState } from "react";
import { converterXmls, type ResultadoConversao } from "./api/converter";
import { UploadZone } from "./components/UploadZone";
import { ResultTable, type ItemResultado } from "./components/ResultTable";
import { ErrorLog } from "./components/ErrorLog";
import { ProgressBar } from "./components/ProgressBar";

// Extrai metadados básicos do XML no cliente (apenas para exibição na tabela)
// Usa DOMParser nativo do browser — sem dependências externas
function extrairMetadadosXml(file: File): Promise<Partial<ItemResultado>> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, "application/xml");

        const get = (tag: string): string =>
          doc.getElementsByTagName(tag)[0]?.textContent?.trim() ?? "";

        const chaveId =
          doc.getElementsByTagName("infNFe")[0]?.getAttribute("Id") ||
          doc.getElementsByTagName("infCte")[0]?.getAttribute("Id") ||
          "";
        const chave = chaveId.replace(/^(NFe|CTe)/, "");
        const isNFe = doc.getElementsByTagName("infNFe").length > 0;

        resolve({
          tipo: isNFe ? "NF-e" : "CT-e",
          chave,
          emitente: get("xNome") || get("xFant"),
          numero: isNFe ? get("nNF") : get("nCT"),
          valor: get("vNF") || get("vTPrest"),
          nomePdf: chave.length === 44 ? `${chave}.pdf` : file.name.replace(".xml", ".pdf"),
        });
      } catch {
        resolve({});
      }
    };
    reader.readAsText(file, "latin1");
  });
}

export default function App() {
  const [arquivos, setArquivos] = useState<File[]>([]);
  const [processando, setProcessando] = useState(false);
  const [resultado, setResultado] = useState<ResultadoConversao | null>(null);
  const [itensTabela, setItensTabela] = useState<ItemResultado[]>([]);
  const [errosExibicao, setErrosExibicao] = useState<string[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  async function handleProcessar() {
    if (arquivos.length === 0) return;
    setProcessando(true);
    setErro(null);
    setResultado(null);
    setItensTabela([]);
    setErrosExibicao([]);

    try {
      // Extrai metadados no cliente para popular a tabela
      const metadados = await Promise.all(
        arquivos.map((f) => extrairMetadadosXml(f))
      );

      const res = await converterXmls(arquivos);
      setResultado(res);

      // Monta itens da tabela com metadados extraídos
      const itens: ItemResultado[] = metadados
        .filter((m) => m.tipo)
        .map((m, i) => ({
          tipo: m.tipo ?? "NF-e",
          chave: m.chave ?? "",
          emitente: m.emitente ?? "",
          destinatario: m.destinatario ?? "",
          numero: m.numero ?? "",
          valor: m.valor ?? "",
          nomePdf: m.nomePdf ?? arquivos[i].name.replace(".xml", ".pdf"),
        }));
      setItensTabela(itens);

      // Dispara download automático do ZIP
      const url = URL.createObjectURL(res.zipBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "danfes_convertidos.zip";
      a.click();
      URL.revokeObjectURL(url);

    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro desconhecido");
    } finally {
      setProcessando(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="mx-auto max-w-4xl">

        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">DANFE Conversor</h1>
          <p className="mt-2 text-gray-500">
            Converta XMLs de NF-e e CT-e para PDF em lote
          </p>
        </div>

        {/* Upload */}
        <UploadZone onFiles={setArquivos} disabled={processando} />

        {/* Lista de arquivos selecionados */}
        {arquivos.length > 0 && (
          <div className="mt-4 flex items-center justify-between rounded-lg bg-white border border-gray-200 px-4 py-3">
            <span className="text-sm text-gray-600">
              {arquivos.length} arquivo{arquivos.length > 1 ? "s" : ""} selecionado{arquivos.length > 1 ? "s" : ""}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setArquivos([])}
                disabled={processando}
                className="text-sm text-gray-400 hover:text-gray-600"
              >
                Limpar
              </button>
              <button
                onClick={handleProcessar}
                disabled={processando}
                className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {processando ? "Processando..." : "Processar e baixar ZIP"}
              </button>
            </div>
          </div>
        )}

        {/* Progress */}
        <ProgressBar
          processando={processando}
          mensagem={`Convertendo ${arquivos.length} arquivo${arquivos.length > 1 ? "s" : ""}...`}
        />

        {/* Erro geral */}
        {erro && (
          <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {erro}
          </div>
        )}

        {/* Sumário */}
        {resultado && (
          <div className="mt-6 grid grid-cols-3 gap-4">
            {[
              { label: "Convertidos", valor: resultado.totalProcessado, cor: "text-green-600" },
              { label: "Com erro", valor: resultado.totalErros, cor: "text-red-500" },
              { label: "Tempo", valor: resultado.tempoProcessamento, cor: "text-gray-700" },
            ].map((s) => (
              <div key={s.label} className="rounded-xl bg-white border border-gray-200 p-4 text-center">
                <p className={`text-2xl font-bold ${s.cor}`}>{s.valor}</p>
                <p className="mt-1 text-xs text-gray-400">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Tabela de resultados */}
        {itensTabela.length > 0 && (
          <div className="mt-6">
            <h2 className="mb-3 text-sm font-semibold text-gray-700">
              Documentos processados
            </h2>
            <ResultTable itens={itensTabela} />
          </div>
        )}

        {/* Log de erros */}
        <ErrorLog erros={errosExibicao} />

      </div>
    </div>
  );
}
