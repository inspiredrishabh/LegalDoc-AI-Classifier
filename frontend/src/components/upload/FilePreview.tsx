import { formatFileSize } from "../../utils/format";

interface FilePreviewProps {
  file: File;
  index: number;
  onRemove: (index: number) => void;
}

export function FilePreview({ file, index, onRemove }: FilePreviewProps) {
  const isImage = file.type.startsWith("image/");
  const previewUrl = isImage ? URL.createObjectURL(file) : null;

  return (
    <div className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg">
      {previewUrl ? (
        <img
          src={previewUrl}
          alt={file.name}
          className="h-12 w-12 object-cover rounded"
          onLoad={() => URL.revokeObjectURL(previewUrl)}
        />
      ) : (
        <div className="h-12 w-12 bg-red-100 rounded flex items-center justify-center">
          <span className="text-xs font-medium text-red-600">PDF</span>
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {file.name}
        </p>
        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
      </div>
      <button
        onClick={() => onRemove(index)}
        className="p-1 text-gray-400 hover:text-red-500"
        aria-label="Remove file"
      >
        <svg
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}
