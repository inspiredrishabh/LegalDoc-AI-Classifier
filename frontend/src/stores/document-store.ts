import { create } from "zustand";
import type { FileUploadResult } from "../types";

interface DocumentState {
  files: File[];
  batchId: string | null;
  results: FileUploadResult[];
  selectedFileId: string | null;
  addFiles: (files: File[]) => void;
  removeFile: (index: number) => void;
  setBatchResult: (batchId: string, results: FileUploadResult[]) => void;
  updateResults: (results: FileUploadResult[]) => void;
  selectFile: (fileId: string) => void;
  reset: () => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  files: [],
  batchId: null,
  results: [],
  selectedFileId: null,

  addFiles: (newFiles) =>
    set((state) => ({ files: [...state.files, ...newFiles] })),

  removeFile: (index) =>
    set((state) => ({
      files: state.files.filter((_, i) => i !== index),
    })),

  setBatchResult: (batchId, results) => set({ batchId, results }),

  updateResults: (results) => set({ results }),

  selectFile: (fileId) => set({ selectedFileId: fileId }),

  reset: () =>
    set({ files: [], batchId: null, results: [], selectedFileId: null }),
}));
