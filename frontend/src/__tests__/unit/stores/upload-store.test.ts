import { describe, it, expect, beforeEach } from 'vitest'
import { useUploadStore } from '@/stores/upload-store'

describe('Upload Store', () => {
  beforeEach(() => {
    // Reset store before each test
    useUploadStore.getState().reset()
  })

  describe('Initial State', () => {
    it('initializes with empty file state', () => {
      const { files } = useUploadStore.getState()

      expect(files.arrival_notice).toBeNull()
      expect(files.bill_of_lading).toBeNull()
      expect(files.certificate_of_origin).toEqual([])
      expect(files.invoice).toBeNull()
    })

    it('initializes with isUploading as false', () => {
      const { isUploading } = useUploadStore.getState()
      expect(isUploading).toBe(false)
    })

    it('initializes with uploadProgress as 0', () => {
      const { uploadProgress } = useUploadStore.getState()
      expect(uploadProgress).toBe(0)
    })

    it('initializes with coFileCountWarning as false', () => {
      const { coFileCountWarning } = useUploadStore.getState()
      expect(coFileCountWarning).toBe(false)
    })

    it('allFilesUploaded returns false when no files uploaded', () => {
      const { allFilesUploaded } = useUploadStore.getState()
      expect(allFilesUploaded()).toBe(false)
    })

    it('uploadedCount returns 0 when no files uploaded', () => {
      const { uploadedCount } = useUploadStore.getState()
      expect(uploadedCount()).toBe(0)
    })
  })

  describe('setFile', () => {
    it('sets arrival notice file', () => {
      const file = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const { setFile } = useUploadStore.getState()

      setFile('AN', file)

      const { files } = useUploadStore.getState()
      expect(files.arrival_notice).toBe(file)
    })

    it('sets bill of lading file', () => {
      const file = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const { setFile } = useUploadStore.getState()

      setFile('BOL', file)

      const { files } = useUploadStore.getState()
      expect(files.bill_of_lading).toBe(file)
    })

    it('sets invoice file', () => {
      const file = new File(['test'], 'INVOICE.jpg', { type: 'image/jpeg' })
      const { setFile } = useUploadStore.getState()

      setFile('INVOICE', file)

      const { files } = useUploadStore.getState()
      expect(files.invoice).toBe(file)
    })

    it('replaces existing file when setFile is called again', () => {
      const file1 = new File(['test1'], 'AN1.pdf', { type: 'application/pdf' })
      const file2 = new File(['test2'], 'AN2.pdf', { type: 'application/pdf' })
      const { setFile } = useUploadStore.getState()

      setFile('AN', file1)
      setFile('AN', file2)

      const { files } = useUploadStore.getState()
      expect(files.arrival_notice).toBe(file2)
    })
  })

  describe('removeFile', () => {
    it('removes arrival notice file', () => {
      const file = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const { setFile, removeFile } = useUploadStore.getState()

      setFile('AN', file)
      removeFile('AN')

      const { files } = useUploadStore.getState()
      expect(files.arrival_notice).toBeNull()
    })

    it('removes bill of lading file', () => {
      const file = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const { setFile, removeFile } = useUploadStore.getState()

      setFile('BOL', file)
      removeFile('BOL')

      const { files } = useUploadStore.getState()
      expect(files.bill_of_lading).toBeNull()
    })

    it('removes invoice file', () => {
      const file = new File(['test'], 'INVOICE.jpg', { type: 'image/jpeg' })
      const { setFile, removeFile } = useUploadStore.getState()

      setFile('INVOICE', file)
      removeFile('INVOICE')

      const { files } = useUploadStore.getState()
      expect(files.invoice).toBeNull()
    })

    it('does not affect other files when removing one', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const { setFile, removeFile } = useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)
      removeFile('AN')

      const { files } = useUploadStore.getState()
      expect(files.arrival_notice).toBeNull()
      expect(files.bill_of_lading).toBe(bolFile)
    })
  })

  describe('setCOFiles - Certificate of Origin Array Management', () => {
    it('sets single CO file', () => {
      const file = new File(['test'], 'CO_1.pdf', { type: 'application/pdf' })
      const { setCOFiles } = useUploadStore.getState()

      setCOFiles([file])

      const { files } = useUploadStore.getState()
      expect(files.certificate_of_origin).toEqual([file])
    })

    it('sets multiple CO files', () => {
      const file1 = new File(['test1'], 'CO_1.pdf', { type: 'application/pdf' })
      const file2 = new File(['test2'], 'CO_2.pdf', { type: 'application/pdf' })
      const file3 = new File(['test3'], 'CO_3.pdf', { type: 'application/pdf' })
      const { setCOFiles } = useUploadStore.getState()

      setCOFiles([file1, file2, file3])

      const { files } = useUploadStore.getState()
      expect(files.certificate_of_origin).toEqual([file1, file2, file3])
      expect(files.certificate_of_origin.length).toBe(3)
    })

    it('replaces existing CO files when setCOFiles is called', () => {
      const file1 = new File(['test1'], 'CO_1.pdf', { type: 'application/pdf' })
      const file2 = new File(['test2'], 'CO_2.pdf', { type: 'application/pdf' })
      const file3 = new File(['test3'], 'CO_3.pdf', { type: 'application/pdf' })
      const { setCOFiles } = useUploadStore.getState()

      setCOFiles([file1, file2])
      setCOFiles([file3])

      const { files } = useUploadStore.getState()
      expect(files.certificate_of_origin).toEqual([file3])
    })

    it('sets coFileCountWarning to false when CO files <= 10', () => {
      const files = Array.from(
        { length: 10 },
        (_, i) =>
          new File([`test${i}`], `CO_${i + 1}.pdf`, { type: 'application/pdf' })
      )
      const { setCOFiles } = useUploadStore.getState()

      setCOFiles(files)

      const { coFileCountWarning } = useUploadStore.getState()
      expect(coFileCountWarning).toBe(false)
    })

    it('sets coFileCountWarning to true when CO files > 10', () => {
      const files = Array.from(
        { length: 11 },
        (_, i) =>
          new File([`test${i}`], `CO_${i + 1}.pdf`, { type: 'application/pdf' })
      )
      const { setCOFiles } = useUploadStore.getState()

      setCOFiles(files)

      const { coFileCountWarning } = useUploadStore.getState()
      expect(coFileCountWarning).toBe(true)
    })

    it('sets coFileCountWarning to true when CO files = 15', () => {
      const files = Array.from(
        { length: 15 },
        (_, i) =>
          new File([`test${i}`], `CO_${i + 1}.pdf`, { type: 'application/pdf' })
      )
      const { setCOFiles } = useUploadStore.getState()

      setCOFiles(files)

      const { coFileCountWarning } = useUploadStore.getState()
      expect(coFileCountWarning).toBe(true)
    })

    it('clears CO files when empty array is passed', () => {
      const file = new File(['test'], 'CO_1.pdf', { type: 'application/pdf' })
      const { setCOFiles } = useUploadStore.getState()

      setCOFiles([file])
      setCOFiles([])

      const { files } = useUploadStore.getState()
      expect(files.certificate_of_origin).toEqual([])
    })
  })

  describe('removeCOFile', () => {
    it('removes CO file at specific index', () => {
      const file1 = new File(['test1'], 'CO_1.pdf', { type: 'application/pdf' })
      const file2 = new File(['test2'], 'CO_2.pdf', { type: 'application/pdf' })
      const file3 = new File(['test3'], 'CO_3.pdf', { type: 'application/pdf' })
      const { setCOFiles, removeCOFile } = useUploadStore.getState()

      setCOFiles([file1, file2, file3])
      removeCOFile(1) // Remove second file

      const { files } = useUploadStore.getState()
      expect(files.certificate_of_origin).toEqual([file1, file3])
    })

    it('removes first CO file', () => {
      const file1 = new File(['test1'], 'CO_1.pdf', { type: 'application/pdf' })
      const file2 = new File(['test2'], 'CO_2.pdf', { type: 'application/pdf' })
      const { setCOFiles, removeCOFile } = useUploadStore.getState()

      setCOFiles([file1, file2])
      removeCOFile(0)

      const { files } = useUploadStore.getState()
      expect(files.certificate_of_origin).toEqual([file2])
    })

    it('removes last CO file', () => {
      const file1 = new File(['test1'], 'CO_1.pdf', { type: 'application/pdf' })
      const file2 = new File(['test2'], 'CO_2.pdf', { type: 'application/pdf' })
      const { setCOFiles, removeCOFile } = useUploadStore.getState()

      setCOFiles([file1, file2])
      removeCOFile(1)

      const { files } = useUploadStore.getState()
      expect(files.certificate_of_origin).toEqual([file1])
    })

    it('updates coFileCountWarning when removing CO file brings count <= 10', () => {
      // Create 11 files (triggers warning)
      const files = Array.from(
        { length: 11 },
        (_, i) =>
          new File([`test${i}`], `CO_${i + 1}.pdf`, { type: 'application/pdf' })
      )
      const { setCOFiles, removeCOFile } = useUploadStore.getState()

      setCOFiles(files)
      expect(useUploadStore.getState().coFileCountWarning).toBe(true)

      // Remove one file to bring it to 10
      removeCOFile(0)

      const { coFileCountWarning } = useUploadStore.getState()
      expect(coFileCountWarning).toBe(false)
      expect(useUploadStore.getState().files.certificate_of_origin.length).toBe(
        10
      )
    })

    it('maintains coFileCountWarning when count still > 10 after removal', () => {
      // Create 15 files
      const files = Array.from(
        { length: 15 },
        (_, i) =>
          new File([`test${i}`], `CO_${i + 1}.pdf`, { type: 'application/pdf' })
      )
      const { setCOFiles, removeCOFile } = useUploadStore.getState()

      setCOFiles(files)
      removeCOFile(0) // Now 14 files

      const { coFileCountWarning } = useUploadStore.getState()
      expect(coFileCountWarning).toBe(true)
      expect(useUploadStore.getState().files.certificate_of_origin.length).toBe(
        14
      )
    })
  })

  describe('allFilesUploaded', () => {
    it('returns false when no files uploaded', () => {
      const { allFilesUploaded } = useUploadStore.getState()
      expect(allFilesUploaded()).toBe(false)
    })

    it('returns false when only some files uploaded', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const { setFile, allFilesUploaded } = useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)

      expect(allFilesUploaded()).toBe(false)
    })

    it('returns false when all single files uploaded but no CO files', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const invoiceFile = new File(['test'], 'INVOICE.jpg', {
        type: 'image/jpeg',
      })
      const { setFile, allFilesUploaded } = useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)
      setFile('INVOICE', invoiceFile)

      expect(allFilesUploaded()).toBe(false)
    })

    it('returns true when all files uploaded including at least 1 CO file', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const coFile = new File(['test'], 'CO_1.pdf', { type: 'application/pdf' })
      const invoiceFile = new File(['test'], 'INVOICE.jpg', {
        type: 'image/jpeg',
      })
      const { setFile, setCOFiles, allFilesUploaded } =
        useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)
      setCOFiles([coFile])
      setFile('INVOICE', invoiceFile)

      expect(allFilesUploaded()).toBe(true)
    })

    it('returns true when all files uploaded including multiple CO files', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const coFile1 = new File(['test1'], 'CO_1.pdf', {
        type: 'application/pdf',
      })
      const coFile2 = new File(['test2'], 'CO_2.pdf', {
        type: 'application/pdf',
      })
      const coFile3 = new File(['test3'], 'CO_3.pdf', {
        type: 'application/pdf',
      })
      const invoiceFile = new File(['test'], 'INVOICE.jpg', {
        type: 'image/jpeg',
      })
      const { setFile, setCOFiles, allFilesUploaded } =
        useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)
      setCOFiles([coFile1, coFile2, coFile3])
      setFile('INVOICE', invoiceFile)

      expect(allFilesUploaded()).toBe(true)
    })

    it('returns false when CO array is empty', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const invoiceFile = new File(['test'], 'INVOICE.jpg', {
        type: 'image/jpeg',
      })
      const { setFile, setCOFiles, allFilesUploaded } =
        useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)
      setCOFiles([])
      setFile('INVOICE', invoiceFile)

      expect(allFilesUploaded()).toBe(false)
    })
  })

  describe('uploadedCount', () => {
    it('returns 0 when no files uploaded', () => {
      const { uploadedCount } = useUploadStore.getState()
      expect(uploadedCount()).toBe(0)
    })

    it('returns 1 when only AN uploaded', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const { setFile, uploadedCount } = useUploadStore.getState()

      setFile('AN', anFile)

      expect(uploadedCount()).toBe(1)
    })

    it('returns 2 when AN and BOL uploaded', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const { setFile, uploadedCount } = useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)

      expect(uploadedCount()).toBe(2)
    })

    it('returns 3 when AN, BOL, and at least 1 CO file uploaded', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const coFile = new File(['test'], 'CO_1.pdf', { type: 'application/pdf' })
      const { setFile, setCOFiles, uploadedCount } = useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)
      setCOFiles([coFile])

      expect(uploadedCount()).toBe(3)
    })

    it('counts CO as 1 file type regardless of array length', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const coFiles = [
        new File(['test1'], 'CO_1.pdf', { type: 'application/pdf' }),
        new File(['test2'], 'CO_2.pdf', { type: 'application/pdf' }),
        new File(['test3'], 'CO_3.pdf', { type: 'application/pdf' }),
      ]
      const { setFile, setCOFiles, uploadedCount } = useUploadStore.getState()

      setFile('AN', anFile)
      setCOFiles(coFiles)

      // AN (1) + CO (1, regardless of 3 files) = 2
      expect(uploadedCount()).toBe(2)
    })

    it('returns 4 when all file types uploaded', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const coFile = new File(['test'], 'CO_1.pdf', { type: 'application/pdf' })
      const invoiceFile = new File(['test'], 'INVOICE.jpg', {
        type: 'image/jpeg',
      })
      const { setFile, setCOFiles, uploadedCount } = useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)
      setCOFiles([coFile])
      setFile('INVOICE', invoiceFile)

      expect(uploadedCount()).toBe(4)
    })
  })

  describe('setUploading', () => {
    it('sets isUploading to true', () => {
      const { setUploading } = useUploadStore.getState()

      setUploading(true)

      const { isUploading } = useUploadStore.getState()
      expect(isUploading).toBe(true)
    })

    it('sets isUploading to false', () => {
      const { setUploading } = useUploadStore.getState()

      setUploading(true)
      setUploading(false)

      const { isUploading } = useUploadStore.getState()
      expect(isUploading).toBe(false)
    })
  })

  describe('setUploadProgress', () => {
    it('sets upload progress to 0', () => {
      const { setUploadProgress } = useUploadStore.getState()

      setUploadProgress(0)

      const { uploadProgress } = useUploadStore.getState()
      expect(uploadProgress).toBe(0)
    })

    it('sets upload progress to 50', () => {
      const { setUploadProgress } = useUploadStore.getState()

      setUploadProgress(50)

      const { uploadProgress } = useUploadStore.getState()
      expect(uploadProgress).toBe(50)
    })

    it('sets upload progress to 100', () => {
      const { setUploadProgress } = useUploadStore.getState()

      setUploadProgress(100)

      const { uploadProgress } = useUploadStore.getState()
      expect(uploadProgress).toBe(100)
    })
  })

  describe('reset', () => {
    it('resets all files to initial state', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const bolFile = new File(['test'], 'BOL.pdf', { type: 'application/pdf' })
      const coFile = new File(['test'], 'CO_1.pdf', { type: 'application/pdf' })
      const invoiceFile = new File(['test'], 'INVOICE.jpg', {
        type: 'image/jpeg',
      })
      const { setFile, setCOFiles, reset } = useUploadStore.getState()

      setFile('AN', anFile)
      setFile('BOL', bolFile)
      setCOFiles([coFile])
      setFile('INVOICE', invoiceFile)

      reset()

      const { files } = useUploadStore.getState()
      expect(files.arrival_notice).toBeNull()
      expect(files.bill_of_lading).toBeNull()
      expect(files.certificate_of_origin).toEqual([])
      expect(files.invoice).toBeNull()
    })

    it('resets isUploading to false', () => {
      const { setUploading, reset } = useUploadStore.getState()

      setUploading(true)
      reset()

      const { isUploading } = useUploadStore.getState()
      expect(isUploading).toBe(false)
    })

    it('resets uploadProgress to 0', () => {
      const { setUploadProgress, reset } = useUploadStore.getState()

      setUploadProgress(75)
      reset()

      const { uploadProgress } = useUploadStore.getState()
      expect(uploadProgress).toBe(0)
    })

    it('resets coFileCountWarning to false', () => {
      const files = Array.from(
        { length: 15 },
        (_, i) =>
          new File([`test${i}`], `CO_${i + 1}.pdf`, { type: 'application/pdf' })
      )
      const { setCOFiles, reset } = useUploadStore.getState()

      setCOFiles(files) // Triggers warning
      reset()

      const { coFileCountWarning } = useUploadStore.getState()
      expect(coFileCountWarning).toBe(false)
    })

    it('resets all state to initial values', () => {
      const anFile = new File(['test'], 'AN.pdf', { type: 'application/pdf' })
      const files = Array.from(
        { length: 15 },
        (_, i) =>
          new File([`test${i}`], `CO_${i + 1}.pdf`, { type: 'application/pdf' })
      )
      const { setFile, setCOFiles, setUploading, setUploadProgress, reset } =
        useUploadStore.getState()

      setFile('AN', anFile)
      setCOFiles(files)
      setUploading(true)
      setUploadProgress(80)

      reset()

      const state = useUploadStore.getState()
      expect(state.files.arrival_notice).toBeNull()
      expect(state.files.bill_of_lading).toBeNull()
      expect(state.files.certificate_of_origin).toEqual([])
      expect(state.files.invoice).toBeNull()
      expect(state.isUploading).toBe(false)
      expect(state.uploadProgress).toBe(0)
      expect(state.coFileCountWarning).toBe(false)
      expect(state.allFilesUploaded()).toBe(false)
      expect(state.uploadedCount()).toBe(0)
    })
  })
})
