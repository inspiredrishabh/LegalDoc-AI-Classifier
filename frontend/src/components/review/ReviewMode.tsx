import { useDocumentStore } from "../../stores/document-store";
import { OriginalView } from "./OriginalView";
import { ExtractedText } from "./ExtractedText";

export function ReviewMode() {
  const { files, results, selectedFileId } = useDocumentStore();

  const selectedResult =
    results.find((r) => r.file_id === selectedFileId) || null;

  // Find the original file by index mapping (files[i] maps to results[i])
  const selectedIndex = results.findIndex((r) => r.file_id === selectedFileId);
  const selectedFile = selectedIndex >= 0 ? files[selectedIndex] || null : null;

  if (results.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">
          Upload and process documents to review results here.
        </p>
      </div>
    );
  }

  if (!selectedFileId) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">
          Select a completed file from the upload results to review.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 h-[700px]">
      <OriginalView file={selectedFile} />
      <ExtractedText result={selectedResult} />
    </div>
  );
}
