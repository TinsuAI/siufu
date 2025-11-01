import { create } from 'zustand'
import {
  FileType,
  FileUploadState,
  FIELD_NAME_MAP,
  validateAllFilesPresent,
  countUploadedFileTypes,
  shouldWarnAboutCoFileCount,
} from '@/types/upload'

interface UploadState {
  // State
  files: FileUploadState
  isUploading: boolean
  uploadProgress: number
  coFileCountWarning: boolean

  // Computed
  allFilesUploaded: () => boolean
  uploadedCount: () => number

  // Actions
  setFile: (fileType: FileType, file: File) => void
  removeFile: (fileType: FileType) => void
  setCOFiles: (files: File[]) => void
  removeCOFile: (index: number) => void
  setUploading: (uploading: boolean) => void
  setUploadProgress: (progress: number) => void
  reset: () => void
}

const initialFiles: FileUploadState = {
  arrival_notice: null,
  bill_of_lading: null,
  certificate_of_origin: [],
  invoice: null,
}

export const useUploadStore = create<UploadState>((set, get) => ({
  // Initial state
  files: initialFiles,
  isUploading: false,
  uploadProgress: 0,
  coFileCountWarning: false,

  // Computed getters
  allFilesUploaded: () => {
    const files = get().files
    return validateAllFilesPresent(files)
  },

  uploadedCount: () => {
    const files = get().files
    return countUploadedFileTypes(files)
  },

  // Actions
  setFile: (fileType: FileType, file: File) => {
    const fieldName = FIELD_NAME_MAP[fileType]
    set((state) => ({
      files: {
        ...state.files,
        [fieldName]: file,
      },
    }))
  },

  removeFile: (fileType: FileType) => {
    const fieldName = FIELD_NAME_MAP[fileType]
    set((state) => ({
      files: {
        ...state.files,
        [fieldName]: null,
      },
    }))
  },

  setCOFiles: (files: File[]) => {
    set((state) => ({
      files: {
        ...state.files,
        certificate_of_origin: files,
      },
      coFileCountWarning: shouldWarnAboutCoFileCount(files),
    }))
  },

  removeCOFile: (index: number) => {
    set((state) => {
      const newCOFiles = state.files.certificate_of_origin.filter(
        (_, i) => i !== index
      )
      return {
        files: {
          ...state.files,
          certificate_of_origin: newCOFiles,
        },
        coFileCountWarning: shouldWarnAboutCoFileCount(newCOFiles),
      }
    })
  },

  setUploading: (uploading: boolean) => {
    set({ isUploading: uploading })
  },

  setUploadProgress: (progress: number) => {
    set({ uploadProgress: progress })
  },

  reset: () => {
    set({
      files: initialFiles,
      isUploading: false,
      uploadProgress: 0,
      coFileCountWarning: false,
    })
  },
}))
