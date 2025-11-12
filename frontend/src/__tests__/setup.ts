/**
 * Vitest global test setup
 *
 * This file configures the test environment for all tests.
 */

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Mock next-intl globally with comprehensive translations
vi.mock('next-intl', async (importOriginal) => {
  const actual = await importOriginal<typeof import('next-intl')>()
  return {
    ...actual,
    useTranslations:
      (namespace?: string) =>
      (key: string, values?: Record<string, unknown>) => {
        // Comprehensive translation mock that covers all used translations
        const translations: Record<string, Record<string, string>> = {
          upload: {
            title: 'Upload Declaration Documents',
            subtitle:
              'Upload all 4 required document types to process a new customs declaration. Certificate of Origin supports multiple files.',
            'progress.label': 'Upload Progress',
            'progress.count': '{count} of 4 required documents uploaded',
            'progress.complete': 'All documents uploaded! Ready to process.',
            'documentTypes.AN': 'Advance Notice (AN)',
            'documentTypes.BOL': 'Bill of Lading (BOL)',
            'documentTypes.CO':
              'Certificate of Origin (C/O) - Multiple files supported',
            'documentTypes.INVOICE': 'Commercial Invoice',
            'descriptions.AN': 'Document notifying arrival of goods',
            'descriptions.BOL': 'Legal document between shipper and carrier',
            'descriptions.CO':
              'Certificate stating country of origin (multiple files allowed)',
            'descriptions.INVOICE': 'Commercial invoice for goods',
            'buttons.process': 'Process Declaration',
            'buttons.uploading': 'Uploading...',
            'buttons.retry': 'Retry Upload',
            'messages.uploadRequired':
              'Please upload all 4 required document types to continue',
            'messages.uploadFailed': 'Upload Failed',
            'messages.uploadError': 'An error occurred while uploading files.',
            'helpAndTips.title': 'Help & Tips',
            'helpAndTips.dragDrop':
              'You can drag and drop files directly onto each zone or click to browse',
            'helpAndTips.multipleFiles':
              'Certificate of Origin supports multiple files - add as many as needed',
            'helpAndTips.validation':
              'Files are validated for type and size before upload',
            'helpAndTips.maxSizes':
              'Maximum file sizes: PDFs (10 MB), Images (5 MB)',
            'helpAndTips.requiredDocs':
              'All required documents must be uploaded before processing can begin',
            'dropzone.file': 'file',
            'dropzone.files': 'files',
            'dropzone.dropMoreFiles': 'Drop more files here',
            'dropzone.clickOrDragMore': 'Click or drag to add more files',
            'dropzone.dragAndDropSingle':
              'Drag and drop file here or click to browse',
            'dropzone.dragAndDropMultiple':
              'Drag and drop files here or click to browse',
            'dropzone.dropSingle': 'Drop file here',
            'dropzone.dropMultiple': 'Drop files here',
            'dropzone.multipleSupported': 'Multiple files supported',
          },
          common: {
            'app.title': 'Siufu',
            'common.app.title': 'Siufu',
            'nav.dashboard': 'Dashboard',
            'common.nav.dashboard': 'Dashboard',
            'nav.upload': 'Upload',
            'common.nav.upload': 'Upload',
            'nav.declarations': 'Declarations',
            'common.nav.declarations': 'Declarations',
            'nav.companies': 'Companies',
            'common.nav.companies': 'Companies',
            'nav.analytics': 'Analytics',
            'common.nav.analytics': 'Analytics',
            'nav.knowledgeBase': 'Knowledge Base',
            'common.nav.knowledgeBase': 'Knowledge Base',
            'nav.settings': 'Settings',
            'common.nav.settings': 'Settings',
            'nav.profile': 'Profile',
            'common.nav.profile': 'Profile',
            'nav.help': 'Help',
            'common.nav.help': 'Help',
            'nav.logout': 'Logout',
            'common.nav.logout': 'Logout',
            'actions.save': 'Save',
            'actions.cancel': 'Cancel',
            'actions.submit': 'Submit',
            'actions.edit': 'Edit',
            'actions.delete': 'Delete',
            'actions.create': 'Create',
            'actions.search': 'Search',
            'actions.view': 'View',
            'actions.download': 'Download',
            'actions.export': 'Export',
            'actions.previous': 'Previous',
            'actions.next': 'Next',
            'actions.yes': 'Yes',
            'actions.no': 'No',
            'common.loading': 'Loading...',
            'common.error': 'Error',
            'common.success': 'Success',
            'common.confirm': 'Confirm',
            'common.close': 'Close',
            // Nested declarations under common namespace (from common.json)
            'declarations.title': 'Declaration History',
            'declarations.createNew': 'Create New Declaration',
            'declarations.table.declarationId': 'Declaration ID',
            'declarations.table.uploadDate': 'Upload Date',
            'declarations.table.status': 'Status',
            'declarations.table.productsCount': 'Products Count',
            'declarations.table.actions': 'Actions',
            'declarations.filters.search': 'Search by Declaration ID...',
            'declarations.filters.allStatuses': 'All Statuses',
            'declarations.actions.review': 'Review',
            'declarations.actions.download': 'Download',
            'declarations.actions.delete': 'Delete',
            'declarations.pagination.showing':
              'Showing {start}-{end} of {total} declarations',
            'declarations.pagination.page': 'Page',
            'declarations.messages.loading': 'Loading declarations...',
            'declarations.messages.noDeclarations':
              'No declarations found. Upload your first declaration to get started.',
            'declarations.messages.uploadDeclaration': 'Upload Declaration',
            'declarations.messages.error':
              'Error loading declarations: {message}',
            'declarations.messages.deleteSuccess':
              'Declaration deleted successfully',
            'declarations.messages.deleteError': 'Failed to delete declaration',
            'declarations.messages.exportSuccess':
              'Declaration exported successfully',
            'declarations.messages.exportError': 'Failed to export declaration',
            'declarations.messages.deleting': 'Deleting...',
            'declarations.dialog.deleteTitle': 'Delete Declaration',
            'declarations.dialog.deleteDescription':
              'Are you sure you want to delete this declaration? This action cannot be undone.',
          },
          declarations: {
            title: 'Declarations',
            'list.title': 'Customs Declarations',
            'list.empty': 'No declarations found',
            'filters.status': 'Status',
            'filters.dateRange': 'Date Range',
            'filters.search': 'Search by Declaration ID...',
            'filters.allStatuses': 'All Statuses',
            'status.pending': 'Pending',
            'status.processing': 'Processing',
            'status.completed': 'Completed',
            'status.failed': 'Failed',
            'table.declarationId': 'Declaration ID',
            'table.uploadDate': 'Upload Date',
            'table.status': 'Status',
            'table.productsCount': 'Products Count',
            'table.actions': 'Actions',
            'actions.review': 'Review',
            'actions.download': 'Download',
            'actions.delete': 'Delete',
            'pagination.showing':
              'Showing {start}-{end} of {total} declarations',
            'pagination.page': 'Page',
            'messages.loading': 'Loading declarations...',
            'messages.noDeclarations':
              'No declarations found. Upload your first declaration to get started.',
            'messages.uploadDeclaration': 'Upload Declaration',
            'messages.error': 'Error loading declarations: {message}',
            'messages.deleteSuccess': 'Declaration deleted successfully',
            'messages.deleteError': 'Failed to delete declaration',
            'messages.exportSuccess': 'Declaration exported successfully',
            'messages.exportError': 'Failed to export declaration',
            'messages.deleting': 'Deleting...',
            'dialog.deleteTitle': 'Delete Declaration',
            'dialog.deleteDescription':
              'Are you sure you want to delete this declaration? This action cannot be undone.',
          },
          companies: {
            title: 'Companies',
            subtitle: 'Manage importer and exporter master data',
            'tabs.importers': 'Importers',
            'tabs.exporters': 'Exporters',
            'search.placeholderImporters': 'Search by name or tax code...',
            'search.placeholderExporters': 'Search by name...',
            'filters.all': 'All Companies',
            'filters.verified': 'Verified Only',
            'filters.unverified': 'Unverified Only',
            'sort.name': 'Name',
            'sort.declarationCount': 'Declaration Count',
            'sort.lastSeen': 'Last Seen',
            'sortOrder.ascending': 'Ascending',
            'sortOrder.descending': 'Descending',
            'company.taxCode': 'Tax Code',
            'company.country': 'Country',
            'company.verified': 'Verified',
            'company.unverified': 'Unverified',
            'company.declarations': '{count} declarations',
            'company.lastSeen': 'Last seen: {date}',
            'actions.addCompany': 'Add Company',
            'actions.viewDetails': 'View Details',
            'actions.edit': 'Edit',
            'actions.merge': 'Merge',
            'actions.delete': 'Delete',
            'messages.loading': 'Loading companies...',
            'messages.error': 'Error loading companies: {message}',
            'messages.noCompanies':
              'No companies found. Companies will appear here after processing declarations.',
            'messages.deleteSuccess': 'Company deleted successfully',
            'messages.deleteError': 'Failed to delete company: {message}',
            'messages.deleteConfirm':
              'Are you sure you want to delete this company? This will unlink all associated declarations.',
            'pagination.page': 'Page {current} of {total} ({count} companies)',
            'pagination.previous': 'Previous',
            'pagination.next': 'Next',
          },
        }

        // Handle nested namespaces like 'common.declarations'
        let namespaceTranslations: Record<string, string> = {}

        if (namespace) {
          const namespaceParts = namespace.split('.')
          if (namespaceParts.length > 1) {
            // For nested namespaces like 'common.declarations'
            // Look for keys like 'declarations.messages.noDeclarations'
            const prefix = namespaceParts.slice(1).join('.')
            const baseNamespace = namespaceParts[0]
            namespaceTranslations = translations[baseNamespace] || {}
            // Prepend the prefix to the key
            key = prefix ? `${prefix}.${key}` : key
          } else {
            namespaceTranslations = translations[namespace] || {}
          }
        } else {
          namespaceTranslations = translations['common'] || {}
        }

        // Return the translation or fallback to the last part of the key
        let translation = namespaceTranslations[key]

        if (!translation) {
          // Fallback: return the last part of the key
          const parts = key.split('.')
          translation = parts[parts.length - 1]
        }

        // Replace placeholders with values if provided
        if (values) {
          Object.entries(values).forEach(([placeholder, value]) => {
            translation = translation.replace(
              new RegExp(`\\{${placeholder}\\}`, 'g'),
              String(value)
            )
          })
        }

        return translation
      },
    useFormatter: () => ({
      dateTime: (date: Date | string, options?: Intl.DateTimeFormatOptions) => {
        const d = typeof date === 'string' ? new Date(date) : date
        return d.toLocaleDateString('en-US', options)
      },
      number: (num: number, options?: Intl.NumberFormatOptions) => {
        return num.toLocaleString('en-US', options)
      },
      relativeTime: () => {
        return 'recently'
      },
    }),
  }
})

// Reset handlers after each test (important for test isolation)
afterEach(() => {
  cleanup()
})

// Mock Next.js router at global level
global.matchMedia =
  global.matchMedia ||
  function () {
    return {
      matches: false,
      addListener: function () {},
      removeListener: function () {},
    }
  }

// Mock URL.createObjectURL and URL.revokeObjectURL for PDF viewer tests
global.URL.createObjectURL = () => 'blob:mock-url'
global.URL.revokeObjectURL = () => {}

// Mock hasPointerCapture for Radix UI components (not supported in jsdom)
if (typeof Element !== 'undefined') {
  Element.prototype.hasPointerCapture =
    Element.prototype.hasPointerCapture ||
    function () {
      return false
    }
  Element.prototype.setPointerCapture =
    Element.prototype.setPointerCapture || function () {}
  Element.prototype.releasePointerCapture =
    Element.prototype.releasePointerCapture || function () {}
  Element.prototype.scrollIntoView =
    Element.prototype.scrollIntoView || function () {}
}
