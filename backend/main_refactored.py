"""
API FastAPI REFATORADA para suportar PDFs de até 900 páginas
Separação: Upload → Processamento Background → Polling
"""

import os
import tempfile
import uuid
import asyncio
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jobs.job_manager import job_manager
from jobs.models import JobStatus, JobProgress, JobResult
from services.excel_export import ExcelExporter
from workers.ocr_worker import process_ocr_job

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializa aplicação FastAPI
app = FastAPI(
    title="API de Processamento de Convênios Bancários",
    description="API assíncrona para OCR de PDFs com até 900 páginas",
    version="2.0.0"
)

# CORS (configurar para domínios específicos em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ProcessPoolExecutor global (máx 2 processos para não sobrecarregar)
executor = ProcessPoolExecutor(max_workers=2)

# Diretórios de armazenamento
UPLOAD_DIR = Path("storage/uploads")
RESULTS_DIR = Path("storage/results")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Configurações
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_PAGES = 900


# === MODELS ===

class UploadResponse(BaseModel):
    """Resposta do endpoint de upload"""
    job_id: str
    filename: str
    message: str


class ProcessResponse(BaseModel):
    """Resposta do endpoint de processamento"""
    job_id: str
    status: str
    message: str


# === ENDPOINTS ===

@app.get("/health")
async def health_check():
    """Health check básico"""
    return {
        "status": "healthy",
        "message": "API rodando",
        "workers": executor._max_workers
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    ETAPA 1: Upload e validação de PDF
    
    - Valida tipo e tamanho
    - Salva em disco
    - Retorna job_id
    - NÃO inicia processamento
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Validação 1: Extensão
        if not file.filename.endswith('.pdf'):
            raise HTTPException(400, "Apenas arquivos PDF são aceitos")
        
        # Validação 2: Magic bytes (primeiros 4 bytes devem ser %PDF)
        content_start = await file.read(4)
        if not content_start.startswith(b'%PDF'):
            raise HTTPException(400, "Arquivo não é um PDF válido")
        
        # Validação 3: Tamanho (lê em chunks para não estourar RAM)
        file.file.seek(0)  # Volta ao início
        size = 0
        chunks = []
        
        while chunk := await file.read(8192):  # 8KB por chunk
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                raise HTTPException(413, f"Arquivo muito grande (máx {MAX_FILE_SIZE//1024//1024}MB)")
            chunks.append(chunk)
        
        # Salva arquivo
        file_path = UPLOAD_DIR / f"{job_id}.pdf"
        with open(file_path, 'wb') as f:
            for chunk in chunks:
                f.write(chunk)
        
        # Cria job em estado PENDING
        job_manager.create_job(
            job_id=job_id,
            filename=file.filename,
            file_path=str(file_path)
        )
        
        logger.info(f"Upload concluído: {job_id} - {file.filename} ({size} bytes)")
        
        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            message="Upload realizado com sucesso. Use POST /process/{job_id} para iniciar OCR."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro no upload: {e}")
        raise HTTPException(500, f"Erro ao processar upload: {str(e)}")


@app.post("/process/{job_id}", response_model=ProcessResponse)
async def process_pdf(job_id: str, background_tasks: BackgroundTasks):
    """
    ETAPA 2: Dispara processamento OCR em background
    
    - Verifica se job existe
    - Submete para ProcessPoolExecutor
    - Retorna imediatamente
    """
    # Valida job
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    
    if job.status != JobStatus.PENDING:
        raise HTTPException(400, f"Job já está em estado: {job.status}")
    
    # Valida arquivo existe
    if not os.path.exists(job.file_path):
        raise HTTPException(404, "Arquivo PDF não encontrado no servidor")
    
    # Submete para background (ProcessPoolExecutor)
    background_tasks.add_task(run_ocr_in_background, job_id, job.file_path)
    
    logger.info(f"Processamento iniciado: {job_id}")
    
    return ProcessResponse(
        job_id=job_id,
        status="processing",
        message="Processamento OCR iniciado. Use GET /status/{job_id} para acompanhar."
    )


@app.get("/status/{job_id}", response_model=JobProgress)
async def get_status(job_id: str):
    """
    ETAPA 3: Polling de status
    
    Cliente deve chamar a cada 2-5 segundos
    """
    progress = job_manager.get_progress(job_id)
    
    if not progress:
        raise HTTPException(404, "Job não encontrado")
    
    return progress


@app.get("/result/{job_id}", response_model=JobResult)
async def get_result(job_id: str):
    """
    ETAPA 4: Resultado final
    
    Só retorna dados se status = DONE
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    
    if job.status == JobStatus.PROCESSING:
        raise HTTPException(425, "Processamento ainda em andamento")
    
    if job.status == JobStatus.PENDING:
        raise HTTPException(400, "Job não foi iniciado. Use POST /process/{job_id}")
    
    if job.status == JobStatus.ERROR:
        raise HTTPException(500, f"Processamento falhou: {job.error_message}")
    
    if job.status == JobStatus.CANCELLED:
        raise HTTPException(410, "Job foi cancelado")
    
    # Status = DONE
    result = job_manager.get_result(job_id)
    if not result:
        raise HTTPException(404, "Resultado não encontrado")
    
    return result


@app.get("/export/{job_id}")
async def export_excel(job_id: str):
    """
    BONUS: Exportar resultado para Excel
    """
    result = job_manager.get_result(job_id)
    if not result or result.status != JobStatus.DONE:
        raise HTTPException(404, "Resultado não disponível")
    
    try:
        exporter = ExcelExporter()
        excel_path = exporter.export_to_file(
            result.items,
            output_path=str(RESULTS_DIR / f"{job_id}.xlsx")
        )
        
        return FileResponse(
            excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"convenio_{job_id}.xlsx"
        )
    except Exception as e:
        logger.exception(f"Erro ao exportar: {e}")
        raise HTTPException(500, f"Erro ao gerar Excel: {str(e)}")


@app.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """
    BONUS: Cancelar job (marca como CANCELLED, mas não interrompe processo)
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job não encontrado")
    
    if job.status in [JobStatus.DONE, JobStatus.ERROR]:
        raise HTTPException(400, "Job já finalizado")
    
    job_manager.cancel_job(job_id)
    
    return {"message": "Job cancelado"}


# === BACKGROUND TASK ===

async def run_ocr_in_background(job_id: str, pdf_path: str):
    """
    Executa OCR em ProcessPoolExecutor de forma assíncrona
    
    CRÍTICO: Usa run_in_executor para não bloquear event loop
    """
    try:
        logger.info(f"[{job_id}] Submetendo para ProcessPoolExecutor")
        
        # Executa em processo separado (não bloqueia FastAPI)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            process_ocr_job,
            job_id,
            pdf_path,
            None  # callback (limitação: não funciona entre processos)
        )
        
        # Atualiza resultado
        if result.status == JobStatus.DONE:
            job_manager.complete_job(job_id, result)
        else:
            job_manager.fail_job(job_id, result.error_message or "Erro desconhecido")
        
    except Exception as e:
        logger.exception(f"[{job_id}] Erro fatal no background task")
        job_manager.fail_job(job_id, str(e))


# === LIFECYCLE ===

@app.on_event("startup")
async def startup():
    """Inicialização"""
    logger.info("API iniciada")
    logger.info(f"ProcessPoolExecutor: {executor._max_workers} workers")


@app.on_event("shutdown")
async def shutdown():
    """Limpeza ao desligar"""
    logger.info("Encerrando ProcessPoolExecutor...")
    executor.shutdown(wait=True)
    logger.info("API encerrada")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
