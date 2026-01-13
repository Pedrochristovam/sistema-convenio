"""
Gerenciador de jobs de processamento OCR
Thread-safe para uso com ProcessPoolExecutor
"""

import threading
from datetime import datetime
from typing import Dict, Optional, List
from .models import JobMetadata, JobStatus, JobProgress, JobResult
import logging

logger = logging.getLogger(__name__)


class JobManager:
    """
    Gerencia estado e lifecycle dos jobs de OCR
    Thread-safe com locks para acesso concorrente
    """
    
    def __init__(self):
        self._jobs: Dict[str, JobMetadata] = {}
        self._results: Dict[str, JobResult] = {}
        self._lock = threading.Lock()
        
    def create_job(self, job_id: str, filename: str, file_path: str) -> JobMetadata:
        """
        Cria novo job em estado PENDING
        
        Args:
            job_id: UUID único do job
            filename: Nome original do arquivo
            file_path: Caminho onde PDF foi salvo
            
        Returns:
            JobMetadata criado
        """
        with self._lock:
            if job_id in self._jobs:
                raise ValueError(f"Job {job_id} já existe")
            
            metadata = JobMetadata(
                job_id=job_id,
                filename=filename,
                file_path=file_path,
                status=JobStatus.PENDING,
                created_at=datetime.now(),
                processed_pages=0
            )
            
            self._jobs[job_id] = metadata
            logger.info(f"Job criado: {job_id} - {filename}")
            
            return metadata
    
    def start_job(self, job_id: str, total_pages: int):
        """Marca job como PROCESSING"""
        with self._lock:
            if job_id not in self._jobs:
                raise ValueError(f"Job {job_id} não encontrado")
            
            self._jobs[job_id].status = JobStatus.PROCESSING
            self._jobs[job_id].started_at = datetime.now()
            self._jobs[job_id].total_pages = total_pages
            
            logger.info(f"Job iniciado: {job_id} ({total_pages} páginas)")
    
    def update_progress(self, job_id: str, processed_pages: int):
        """Atualiza contador de páginas processadas"""
        with self._lock:
            if job_id not in self._jobs:
                return
            
            self._jobs[job_id].processed_pages = processed_pages
    
    def complete_job(self, job_id: str, result: JobResult):
        """Marca job como DONE e armazena resultado"""
        with self._lock:
            if job_id not in self._jobs:
                raise ValueError(f"Job {job_id} não encontrado")
            
            self._jobs[job_id].status = JobStatus.DONE
            self._jobs[job_id].completed_at = datetime.now()
            self._results[job_id] = result
            
            logger.info(f"Job concluído: {job_id} - {result.records_found} registros")
    
    def fail_job(self, job_id: str, error_message: str):
        """Marca job como ERROR"""
        with self._lock:
            if job_id not in self._jobs:
                return
            
            self._jobs[job_id].status = JobStatus.ERROR
            self._jobs[job_id].completed_at = datetime.now()
            self._jobs[job_id].error_message = error_message
            
            logger.error(f"Job falhou: {job_id} - {error_message}")
    
    def cancel_job(self, job_id: str):
        """Marca job como CANCELLED"""
        with self._lock:
            if job_id not in self._jobs:
                return
            
            self._jobs[job_id].status = JobStatus.CANCELLED
            self._jobs[job_id].completed_at = datetime.now()
            
            logger.info(f"Job cancelado: {job_id}")
    
    def get_job(self, job_id: str) -> Optional[JobMetadata]:
        """Retorna metadata de um job"""
        with self._lock:
            return self._jobs.get(job_id)
    
    def get_progress(self, job_id: str) -> Optional[JobProgress]:
        """
        Retorna progresso atual do job para polling
        
        Returns:
            JobProgress ou None se não encontrado
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            
            # Calcula progresso percentual
            progress_percent = 0.0
            if job.total_pages and job.total_pages > 0:
                progress_percent = (job.processed_pages / job.total_pages) * 100
            
            # Mensagem amigável por status
            message_map = {
                JobStatus.PENDING: "Aguardando processamento",
                JobStatus.PROCESSING: f"Processando página {job.processed_pages}/{job.total_pages}",
                JobStatus.DONE: "Processamento concluído",
                JobStatus.ERROR: f"Erro: {job.error_message}",
                JobStatus.CANCELLED: "Processamento cancelado"
            }
            
            return JobProgress(
                job_id=job_id,
                status=job.status,
                progress_percent=round(progress_percent, 2),
                total_pages=job.total_pages,
                processed_pages=job.processed_pages,
                message=message_map.get(job.status, "")
            )
    
    def get_result(self, job_id: str) -> Optional[JobResult]:
        """Retorna resultado final de um job DONE"""
        with self._lock:
            return self._results.get(job_id)
    
    def list_jobs(self, status: Optional[JobStatus] = None) -> List[JobMetadata]:
        """Lista todos os jobs, opcionalmente filtrados por status"""
        with self._lock:
            jobs = list(self._jobs.values())
            
            if status:
                jobs = [j for j in jobs if j.status == status]
            
            return sorted(jobs, key=lambda x: x.created_at, reverse=True)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Remove jobs antigos para evitar vazamento de memória
        
        Args:
            max_age_hours: Jobs mais antigos que isso serão removidos
        """
        with self._lock:
            now = datetime.now()
            to_remove = []
            
            for job_id, job in self._jobs.items():
                # Remove apenas jobs finalizados (DONE, ERROR, CANCELLED)
                if job.status in [JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED]:
                    age_hours = (now - job.created_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_remove.append(job_id)
            
            for job_id in to_remove:
                del self._jobs[job_id]
                if job_id in self._results:
                    del self._results[job_id]
                logger.info(f"Job removido (cleanup): {job_id}")


# Singleton global (em produção, usar injeção de dependência)
job_manager = JobManager()
