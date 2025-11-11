# Translation Files - Naming Conventions

## Directory Structure

```
messages/
├── en/                          # English translations
│   ├── auth.json               # Authentication pages
│   ├── common.json             # Common UI elements
│   ├── declarations.json       # Declaration form fields
│   └── customs-terms.json      # Vietnamese customs terminology
└── vi/                          # Vietnamese translations
    ├── auth.json
    ├── common.json
    ├── declarations.json
    └── customs-terms.json
```

## Translation Key Naming Convention

### Pattern

**Format:** `{namespace}.{section}.{field}.{type}`

- **namespace**: File name without extension (e.g., `declarations`, `customs-terms`, `common`)
- **section**: Form section in camelCase (e.g., `header`, `importer`, `products`)
- **field**: Field name in camelCase (e.g., `declarationNumber`, `taxCode`)
- **type**: Content type (e.g., `label`, `placeholder`, `helpText`)

### Examples

```typescript
// Section titles
t('declarations.header.title')
// → EN: "Declaration Header"
// → VI: "Tiêu Đề Tờ Khai"

// Field labels
t('declarations.header.declarationNumber.label')
// → EN: "Declaration Number"
// → VI: "Số Tờ Khai"

// Field placeholders
t('declarations.header.declarationNumber.placeholder')
// → EN: "e.g., A11 2 [4]"
// → VI: "Ví dụ: A11 2 [4]"

// Help text
t('declarations.header.declarationNumber.helpText')
// → EN: "Official customs declaration number"
// → VI: "Số tờ khai hải quan chính thức"

// Validation messages
t('declarations.validation.required')
// → EN: "This field is required"
// → VI: "Trường này là bắt buộc"

// Buttons
t('declarations.products.addButton')
// → EN: "Add Product"
// → VI: "Thêm Hàng Hóa"

// Customs terminology
t('customs-terms.hsCode')
// → EN: "HS Code"
// → VI: "Mã HS"
```

## Usage in Components

### Client Components (with useTranslations hook)

```typescript
'use client'

import { useTranslations } from 'next-intl';

export function DeclarationForm() {
  const tDecl = useTranslations('declarations');
  const tCustoms = useTranslations('customs-terms');

  return (
    <>
      <Label>{tDecl('header.declarationNumber.label')}</Label>
      <Input placeholder={tDecl('header.declarationNumber.placeholder')} />
    </>
  );
}
```

### Server Components (with getTranslations)

```typescript
import { getTranslations } from 'next-intl/server';

export async function DeclarationPage() {
  const tDecl = await getTranslations('declarations');

  return <h1>{tDecl('header.title')}</h1>;
}
```

## File Organization

### declarations.json

Contains all declaration form field labels, placeholders, help text, validation messages, and button text organized by form sections.

### customs-terms.json

Contains Vietnamese customs-specific terminology that may be reused across multiple contexts (e.g., "HS Code", "Bill of Lading", "Certificate of Origin").

### common.json

Contains common UI elements shared across the application (buttons, navigation, etc.).

### auth.json

Contains authentication-related translations (login, register, password reset).

## Translation Guidelines

1. **Formal Vietnamese**: Use formal governmental/business language for customs terminology
2. **Consistency**: Same English term should always map to same Vietnamese translation
3. **Accuracy**: Customs terms must match official Vietnamese customs regulations
4. **Clarity**: Placeholders should provide helpful examples in local format
5. **Completeness**: All UI text must be translatable (no hardcoded strings)

## Expert Review Required

All Vietnamese customs terminology in `vi/declarations.json` and `vi/customs-terms.json` requires review and approval by a Vietnamese customs domain expert (licensed customs broker or customs officer) before production deployment.
