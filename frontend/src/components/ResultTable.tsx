// frontend/src/components/ResultTable.tsx

export interface ItemResultado {
  tipo: "NF-e" | "CT-e";
  chave: string;
  emitente: string;
  destinatario: string;
  numero: string;
  valor: string;
  nomePdf: string;
}

interface Props {
  itens: ItemResultado[];
}

export function ResultTable({ itens }: Props) {
  if (itens.length === 0) return null;

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <th className="px-4 py-3">Tipo</th>
            <th className="px-4 py-3">Chave de acesso</th>
            <th className="px-4 py-3">Emitente</th>
            <th className="px-4 py-3">Destinatário</th>
            <th className="px-4 py-3 text-right">Número</th>
            <th className="px-4 py-3 text-right">Valor</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {itens.map((item, i) => (
            <tr key={i} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3">
                <span
                  className={[
                    "inline-block px-2 py-0.5 rounded text-xs font-semibold",
                    item.tipo === "NF-e"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-amber-100 text-amber-700",
                  ].join(" ")}
                >
                  {item.tipo}
                </span>
              </td>
              <td className="px-4 py-3 font-mono text-xs text-gray-500 max-w-[180px] truncate">
                {item.chave || "—"}
              </td>
              <td className="px-4 py-3 text-gray-700 max-w-[160px] truncate">
                {item.emitente || "—"}
              </td>
              <td className="px-4 py-3 text-gray-700 max-w-[160px] truncate">
                {item.destinatario || "—"}
              </td>
              <td className="px-4 py-3 text-right text-gray-700">
                {item.numero || "—"}
              </td>
              <td className="px-4 py-3 text-right font-medium text-gray-900">
                {item.valor ? `R$ ${item.valor}` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
