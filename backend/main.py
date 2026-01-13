"""
API FastAPI para processamento de convênios bancários
Recebe PDFs, processa com OCR e retorna dados extraídos

REFATORADO: Suporta PDFs grandes com ProcessPoolExecutor e cache
"""

import os
import tempfile
import uuid
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cachetools import TTLCache

from services.ocr_service import OCRService
from services.page_filter import PageFilter
from services.extractor import DataExtractor
from services.excel_export import ExcelExporter

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Inicializa aplicação FastAPI
app = FastAPI(
    title="API de Processamento de Convênios Bancários",
    description="API para processar PDFs de convênios bancários usando OCR",
    version="1.0.0"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ProcessPoolExecutor global (máx 2 workers para não sobrecarregar CPU)
executor = ProcessPoolExecutor(max_workers=2)

# Cache com TTL (expira em 1 hora)
processing_cache = TTLCache(maxsize=100, ttl=3600)

# Lock para acesso thread-safe ao cache
import threading
cache_lock = threading.Lock()

# Diretórios
UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Configurações
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


class ProcessingResponse(BaseModel):
    """Modelo de resposta do processamento"""
    id: str
    status: str
    total_pages: int
    relevant_pages: int
    records_found: int
    items: List[Dict]


class JobStatus(BaseModel):
    """Status de um job em processamento"""
    job_id: str
    status: str  # pending, processing, done, error
    progress: float  # 0-100
    message: str


class HealthResponse(BaseModel):
    """Modelo de resposta do health check"""
    status: str
    message: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Endpoint de health check
    
    Returns:
        Status da API
    """
    return {
        "status": "healthy",
        "message": "API está funcionando corretamente"
    }


def process_pdf_worker(job_id: str, pdf_path: str) -> Dict:
    """
    Worker que roda em ProcessPoolExecutor (processo separado)
    
    IMPORTANTE: Código roda fora do FastAPI, precisa ser importável
    
    Args:
        job_id: ID do job
        pdf_path: Caminho do PDF
        
    Returns:
        Dicionário com resultado ou erro
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[{job_id}] Worker iniciado")
        
        # Instancia serviços (cada processo tem suas próprias instâncias)
        from services.ocr_service import OCRService
        from services.page_filter import PageFilter
        from services.extractor import DataExtractor
        
        ocr_service = OCRService(dpi=200, batch_size=10)
        page_filter = PageFilter()
        data_extractor = DataExtractor()
        
        # Processa em batches
        logger.info(f"[{job_id}] Processando PDF em batches...")
        all_ocr_results = []
        
        for batch_results in ocr_service.process_pdf_in_batches(pdf_path):
            all_ocr_results.extend(batch_results)
            logger.info(f"[{job_id}] Batch processado, total: {len(all_ocr_results)} páginas")
        
        total_pages = len(all_ocr_results)
        
        # Filtra páginas relevantes
        relevant_pages = page_filter.filter_pages(all_ocr_results)
        relevant_pages_count = len(relevant_pages)
        
        if relevant_pages_count == 0:
            return {
                "status": "error",
                "error": "Nenhuma página relevante encontrada"
            }
        
        # Extrai dados
        texts = [page["text"] for page in relevant_pages]
        extracted_data = data_extractor.extract_multiple_records(texts)
        
        if not extracted_data:
            return {
                "status": "error",
                "error": "Nenhum dado bancário encontrado"
            }
        
        logger.info(f"[{job_id}] Concluído: {len(extracted_data)} registros")
        
        return {
            "status": "done",
            "id": job_id,
            "total_pages": total_pages,
            "relevant_pages": relevant_pages_count,
            "records_found": len(extracted_data),
            "items": extracted_data
        }
        
    except Exception as e:
        logger.exception(f"[{job_id}] Erro no worker")
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/upload", response_model=Dict)
async def upload_pdf(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload de PDF e início de processamento em background
    
    MUDANÇA: Agora retorna job_id e processa assincronamente
    
    Args:
        file: Arquivo PDF
        
    Returns:
        job_id para acompanhar status
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Validação 1: Extensão
        if not file.filename.endswith('.pdf'):
            raise HTTPException(400, "Apenas arquivos PDF são aceitos")
        
        # Validação 2: Magic bytes
        content_start = await file.read(4)
        if not content_start.startswith(b'%PDF'):
            raise HTTPException(400, "Arquivo não é um PDF válido")
        
        # Validação 3: Tamanho com chunks
        file.file.seek(0)
        size = 0
        chunks = []
        
        while chunk := await file.read(8192):
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                raise HTTPException(413, f"Arquivo muito grande (máx {MAX_FILE_SIZE//1024//1024}MB)")
            chunks.append(chunk)
        
        # Salva arquivo
        file_path = UPLOAD_DIR / f"{job_id}.pdf"
        with open(file_path, 'wb') as f:
            for chunk in chunks:
                f.write(chunk)
        
        # Registra job como pending
        with cache_lock:
            processing_cache[job_id] = {
                "status": "pending",
                "filename": file.filename,
                "created_at": datetime.now().isoformat()
            }
        
        # Dispara processamento em background
        if background_tasks:
            background_tasks.add_task(process_in_background, job_id, str(file_path))
        else:
            # Fallback se BackgroundTasks não disponível
            asyncio.create_task(process_in_background(job_id, str(file_path)))
        
        logger.info(f"Upload concluído: {job_id} - {file.filename} ({size} bytes)")
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Upload realizado. Use GET /status/{job_id} para acompanhar."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro no upload: {e}")
        raise HTTPException(500, f"Erro ao processar upload: {str(e)}")


async def process_in_background(job_id: str, pdf_path: str):
    """
    Executa worker em ProcessPoolExecutor de forma assíncrona
    
    CRÍTICO: Usa run_in_executor para não bloquear event loop
    """
    try:
        # Atualiza status para processing
        with cache_lock:
            if job_id in processing_cache:
                processing_cache[job_id]["status"] = "processing"
                processing_cache[job_id]["started_at"] = datetime.now().isoformat()
        
        logger.info(f"[{job_id}] Submetendo para ProcessPoolExecutor")
        
        # Executa em processo separado (NÃO BLOQUEIA)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            process_pdf_worker,
            job_id,
            pdf_path
        )
        
        # Atualiza cache com resultado
        with cache_lock:
            if job_id in processing_cache:
                processing_cache[job_id].update(result)
                processing_cache[job_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"[{job_id}] Processamento concluído")
        
    except Exception as e:
        logger.exception(f"[{job_id}] Erro no background task")
        with cache_lock:
            if job_id in processing_cache:
                processing_cache[job_id]["status"] = "error"
                processing_cache[job_id]["error"] = str(e)
    
    finally:
        # Limpa arquivo após processamento
        try:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
                logger.info(f"[{job_id}] Arquivo temporário removido")
        except Exception as e:
            logger.error(f"[{job_id}] Erro ao remover arquivo: {e}")


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """
    Retorna status atual do job (para polling)
    
    Args:
        job_id: ID do job
        
    Returns:
        Status e progresso
    """
    with cache_lock:
        job_data = processing_cache.get(job_id)
    
    if not job_data:
        raise HTTPException(404, "Job não encontrado")
    
    status = job_data.get("status", "unknown")
    
    # Calcula progresso (simplificado)
    progress_map = {
        "pending": 0.0,
        "processing": 50.0,
        "done": 100.0,
        "error": 0.0
    }
    
    message_map = {
        "pending": "Aguardando processamento",
        "processing": "Processando PDF...",
        "done": f"Concluído - {job_data.get('records_found', 0)} registros encontrados",
        "error": f"Erro: {job_data.get('error', 'Desconhecido')}"
    }
    
    return JobStatus(
        job_id=job_id,
        status=status,
        progress=progress_map.get(status, 0.0),
        message=message_map.get(status, "")
    )


@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Retorna resultado final de um job
    
    Args:
        job_id: ID do job
        
    Returns:
        Dados extraídos (apenas se status = done)
    """
    with cache_lock:
        job_data = processing_cache.get(job_id)
    
    if not job_data:
        raise HTTPException(404, "Job não encontrado")
    
    if job_data["status"] == "processing":
        raise HTTPException(425, "Processamento ainda em andamento")
    
    if job_data["status"] == "pending":
        raise HTTPException(400, "Processamento não iniciado")
    
    if job_data["status"] == "error":
        raise HTTPException(500, f"Erro: {job_data.get('error')}")
    
    # Retorna resultado
    return {
        "id": job_data.get("id", job_id),
        "status": "completed",
        "total_pages": job_data.get("total_pages", 0),
        "relevant_pages": job_data.get("relevant_pages", 0),
        "records_found": job_data.get("records_found", 0),
        "items": job_data.get("items", [])
    }


@app.get("/export/{job_id}")
async def export_to_excel(job_id: str):
    """
    Exporta resultado para Excel
    
    Args:
        job_id: ID do job
        
    Returns:
        Arquivo Excel para download
    """
    with cache_lock:
        job_data = processing_cache.get(job_id)
    
    if not job_data or job_data.get("status") != "done":
        raise HTTPException(404, "Resultado não disponível")
    
    data = job_data.get("items", [])
    
    if not data:
        raise HTTPException(404, "Nenhum dado para exportar")
    
    try:
        excel_exporter = ExcelExporter()
        excel_path = excel_exporter.export_to_file(data)
        
        return FileResponse(
            excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"convenio_{job_id}.xlsx"
        )
    except Exception as e:
        logger.exception(f"Erro ao exportar: {e}")
        raise HTTPException(500, f"Erro ao gerar Excel: {str(e)}")


@app.on_event("startup")
async def startup():
    """Inicialização da API"""
    logger.info("=== API Iniciada ===")
    logger.info(f"ProcessPoolExecutor: {executor._max_workers} workers")
    logger.info(f"Cache TTL: 3600s (1 hora)")
    logger.info(f"Upload dir: {UPLOAD_DIR}")


@app.on_event("shutdown")
async def shutdown():
    """Encerramento da API"""
    logger.info("Encerrando ProcessPoolExecutor...")
    executor.shutdown(wait=True)
    logger.info("=== API Encerrada ===")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
