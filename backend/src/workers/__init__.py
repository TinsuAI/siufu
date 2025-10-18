"""
Workers module - Celery tasks for async processing
"""
from src.workers.declaration_processor import process_declaration_task

__all__ = ['process_declaration_task']
