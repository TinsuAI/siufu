# Backend Architecture

## Repository Pattern

```python
# repositories/declaration_repository.py
class DeclarationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, declaration: DeclarationCreate, user_id: UUID) -> Declaration:
        db_declaration = Declaration(
            status='UPLOADED',
            created_by_user_id=user_id,
            # ...
        )
        self.db.add(db_declaration)
        await self.db.commit()
        return db_declaration

    async def update_draft_data(self, declaration_id: UUID, draft_data: dict) -> Declaration:
        # Merge partial updates
        declaration = await self.get_by_id(declaration_id)
        existing_data = declaration.draft_data or {}
        merged_data = {**existing_data, **draft_data}
        declaration.draft_data = merged_data
        await self.db.commit()
        return declaration
```

## Celery Task Structure

```python
# workers/declaration_processor.py
@celery_app.task(bind=True, max_retries=3)
def process_declaration_task(self, declaration_id: str):
    try:
        result = asyncio.run(_process_declaration_async(declaration_id))
        return result
    except Exception as exc:
        logger.error(f"Processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)

async def _process_declaration_async(declaration_id: str):
    # Stage 1: OCR (20-30s)
    ocr_service = OCRService()
    ocr_results = await asyncio.gather(*[
        ocr_service.process_document(file['path'])
        for file in pdf_files
    ])

    # Stage 2: LLM Extraction (25-40s)
    extraction_service = ExtractionService()
    extracted_data = await extraction_service.extract_structured_data(ocr_results)

    # Stage 3: Validation (5-10s)
    validation_service = ValidationService()
    validation_warnings = await validation_service.cross_validate(extracted_data)

    # Stage 4: Excel Generation (3-5s)
    excel_service = ExcelService()
    excel_path = await excel_service.generate_cd_file(declaration_id, extracted_data)

    # Update declaration
    await repo.update_status(declaration_id, 'READY_FOR_REVIEW', progress=1.0)

    return {'status': 'READY_FOR_REVIEW'}
```

---
