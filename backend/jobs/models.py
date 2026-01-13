"""
Modelos de dados para controle de jobs de processamento
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class JobStatus(str, Enum):
    """Estados possíveis de um job"""
    PENDING = "pending"           # Criado, aguardando início
    PROCESSING = "processing"     # OCR em execução
    DONE = "done"                # Concluído com sucesso
    ERROR = "error"              # Falhou
    CANCELLED = "cancelled"      # Cancelado pelo usuário


class JobMetadata(BaseModel):
    """Metadados de um job"""
    job_id: str
    filename: str
    file_path: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_pages: Optional[int] = None
    processed_pages: int = 0
    error_message: Optional[str] = None
    

class JobResult(BaseModel):
    """Resultado final de um job"""
    job_id: str
    status: JobStatus
    total_pages: int
    relevant_pages: int
    records_found: int
    items: List[Dict[str, Any]]
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None


class JobProgress(BaseModel):
    """Progresso de um job (para polling)"""
    job_id: str
    status: JobStatus
    progress_percent: float  # 0-100
    total_pages: Optional[int] = None
    processed_pages: int = 0
    estimated_time_remaining: Optional[int] = None  # segundos
    message: str = ""
