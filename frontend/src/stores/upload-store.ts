import { create } from 'zustand';
import { FileType, FileUploadState, FIELD_NAME_MAP, validateAllFilesPresent } from '@/types/upload';

interface UploadState {
  // State
  files: FileUploadState;
  isUploading: boolean;
  uploadProgress: number;

  // Computed
  allFilesUploaded: () => boolean;
  uploadedCount: () => number;

  // Actions
  setFile: (fileType: FileType, file: File) => void;
  removeFile: (fileType: FileType) => void;
  setUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  reset: () => void;
}

const initialFiles: FileUploadState = {
  arrival_notice: null,
  bill_of_lading: null,
  certificate_of_origin: null,
  invoice: null,
  good_list: null,
  exim_tariff: null,
};

export const useUploadStore = create<UploadState>((set, get) => ({
  // Initial state
  files: initialFiles,
  isUploading: false,
  uploadProgress: 0,

  // Computed getters
  allFilesUploaded: () => {
    const files = get().files;
    return validateAllFilesPresent(files);
  },

  uploadedCount: () => {
    const files = get().files;
    return Object.values(files).filter((file) => file !== null).length;
  },

  // Actions
  setFile: (fileType: FileType, file: File) => {
    const fieldName = FIELD_NAME_MAP[fileType];
    set((state) => ({
      files: {
        ...state.files,
        [fieldName]: file,
      },
    }));
  },

  removeFile: (fileType: FileType) => {
    const fieldName = FIELD_NAME_MAP[fileType];
    set((state) => ({
      files: {
        ...state.files,
        [fieldName]: null,
      },
    }));
  },

  setUploading: (uploading: boolean) => {
    set({ isUploading: uploading });
  },

  setUploadProgress: (progress: number) => {
    set({ uploadProgress: progress });
  },

  reset: () => {
    set({
      files: initialFiles,
      isUploading: false,
      uploadProgress: 0,
    });
  },
}));
