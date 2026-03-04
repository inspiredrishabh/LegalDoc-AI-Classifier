import { useState } from "react";
import { formatConfidence } from "../../utils/format";
import type { FileUploadResult } from "../../types";

interface ExtractedTextProps {
  result: FileUploadResult | null;
}

export function ExtractedText({ result }: ExtractedTextProps) {
  const [copied, setCopied] = useState(false);

  if (!result) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-sm text-gray-500">No extracted text available</p>
      </div>
    );
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.raw_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full overflow-auto bg-white rounded-lg border border-gray-200">
      <div className="p-2 bg-gray-100 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-gray-700">Extracted Text</h3>
          <div className="flex gap-2 mt-1">
            <span className="px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700">
              {result.metadata.page_count} page(s)
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-700">
              {formatConfidence(result.metadata.confidence_score)} confidence
            </span>
          </div>
        </div>
        <button
          onClick={handleCopy}
          className="px-3 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded-md"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <pre className="p-4 text-sm font-mono whitespace-pre-wrap text-gray-800 leading-relaxed">
        {result.raw_text}
      </pre>
    </div>
  );
}
