// frontend/src/components/UploadZone.tsx
import { useRef, useState, type DragEvent, type ChangeEvent } from "react";

interface Props {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

export function UploadZone({ onFiles, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleFiles(fileList: FileList | null) {
    if (!fileList) return;
    const xmlFiles = Array.from(fileList).filter((f) =>
      f.name.toLowerCase().endsWith(".xml")
    );
    if (xmlFiles.length > 0) onFiles(xmlFiles);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  return (
    <div
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={[
        "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors",
        dragging
          ? "border-blue-500 bg-blue-50"
          : "border-gray-300 hover:border-blue-400 hover:bg-gray-50",
        disabled ? "opacity-50 cursor-not-allowed" : "",
      ].join(" ")}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xml"
        multiple
        className="hidden"
        onChange={(e: ChangeEvent<HTMLInputElement>) => handleFiles(e.target.files)}
        disabled={disabled}
      />
      <p className="text-lg font-medium text-gray-700">
        Arraste os XMLs aqui ou clique para selecionar
      </p>
      <p className="mt-1 text-sm text-gray-400">
        Aceita NF-e e CT-e · até 100 arquivos · 2MB por arquivo
      </p>
    </div>
  );
}
