import { FileType, MAX_FILE_SIZES, MAX_IMAGE_SIZE, ACCEPTED_FORMATS, ACCEPTED_MIME_TYPES } from '@/types/upload';

/**
 * Validation result for file validation
 */
export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Validate file type by checking file extension
 * @param file - File to validate
 * @param acceptedExtensions - Array of accepted extensions (e.g., ['.pdf', '.jpg'])
 * @returns true if file extension matches one of the accepted types
 */
export function validateFileType(file: File, acceptedExtensions: string[]): boolean {
  const fileName = file.name.toLowerCase();
  return acceptedExtensions.some((ext) => fileName.endsWith(ext.toLowerCase()));
}

/**
 * Validate file size
 * @param file - File to validate
 * @param maxSize - Maximum size in bytes
 * @returns true if file size is within limit
 */
export function validateFileSize(file: File, maxSize: number): boolean {
  return file.size <= maxSize;
}

/**
 * Convert bytes to human-readable size
 * @param bytes - Size in bytes
 * @returns Human-readable string (e.g., "5.2 MB", "1.5 KB")
 */
export function getHumanReadableSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const size = bytes / Math.pow(k, i);

  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/**
 * Get the file extension from a filename
 * @param filename - Name of the file
 * @returns Extension including the dot (e.g., ".pdf")
 */
export function getFileExtension(filename: string): string {
  const lastDotIndex = filename.lastIndexOf('.');
  if (lastDotIndex === -1) return '';
  return filename.slice(lastDotIndex).toLowerCase();
}

/**
 * Check if a file is an image based on MIME type
 * @param file - File to check
 * @returns true if file is an image
 */
export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/');
}

/**
 * Comprehensive file validation for a specific file type
 * @param file - File to validate
 * @param fileType - Type of file (e.g., 'AN', 'INVOICE')
 * @returns Validation result with error message if invalid
 */
export function validateFile(file: File, fileType: FileType): FileValidationResult {
  // Check if file is empty
  if (file.size === 0) {
    return {
      valid: false,
      error: 'File cannot be empty',
    };
  }

  // Get accepted formats for this file type
  const acceptedFormats = ACCEPTED_FORMATS[fileType];
  const extension = getFileExtension(file.name);

  // Validate file type
  if (!validateFileType(file, acceptedFormats)) {
    const expectedFormats = acceptedFormats.join(', ');
    return {
      valid: false,
      error: `Invalid file type. Expected ${expectedFormats}, got ${extension || 'unknown'}`,
    };
  }

  // Determine max size based on file type
  let maxSize = MAX_FILE_SIZES[fileType];

  // Special case for INVOICE: images have different size limit
  if (fileType === 'INVOICE' && isImageFile(file)) {
    maxSize = MAX_IMAGE_SIZE;
  }

  // Validate file size
  if (!validateFileSize(file, maxSize)) {
    const maxSizeReadable = getHumanReadableSize(maxSize);
    const fileSizeReadable = getHumanReadableSize(file.size);
    return {
      valid: false,
      error: `File too large. Maximum size is ${maxSizeReadable}, selected file is ${fileSizeReadable}`,
    };
  }

  // All validations passed
  return {
    valid: true,
  };
}

/**
 * Validate MIME type matches accepted types
 * @param file - File to validate
 * @param fileType - Type of file
 * @returns true if MIME type is accepted
 */
export function validateMimeType(file: File, fileType: FileType): boolean {
  const acceptedMimeTypes = ACCEPTED_MIME_TYPES[fileType];
  return acceptedMimeTypes.includes(file.type);
}

/**
 * Get a formatted list of accepted file formats
 * @param fileType - Type of file
 * @returns Human-readable string of accepted formats
 */
export function getAcceptedFormatsString(fileType: FileType): string {
  const formats = ACCEPTED_FORMATS[fileType];
  const maxSize = MAX_FILE_SIZES[fileType];
  const maxSizeReadable = getHumanReadableSize(maxSize);

  return `Accepted: ${formats.join(', ')}, max ${maxSizeReadable}`;
}
