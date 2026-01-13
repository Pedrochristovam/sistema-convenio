"""
Worker de OCR que roda em processo isolado
CRÍTICO: Este código roda fora do FastAPI, em ProcessPoolExecutor
"""

import logging
from typing import List, Dict
from datetime import datetime

# Imports locais (precisam ser reimportados no processo filho)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ocr_service import OCRService
from services.pdf_service import PDFService
from services.page_filter import PageFilter
from services.extractor import DataExtractor
from jobs.models import JobResult, JobStatus

logger = logging.getLogger(__name__)


def process_ocr_job(job_id: str, pdf_path: str, callback_update=None) -> JobResult:
    """
    Função principal que executa OCR completo em processo separado
    
    ATENÇÃO: Roda em ProcessPoolExecutor, não tem acesso ao contexto FastAPI
    
    Args:
        job_id: ID do job
        pdf_path: Caminho completo do PDF
        callback_update: Função para atualizar progresso (opcional)
        
    Returns:
        JobResult com dados extraídos ou erro
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"[{job_id}] Iniciando processamento OCR")
        
        # Inicializa serviços (cada processo tem sua própria instância)
        pdf_service = PDFService(dpi=200)  # DPI reduzido para economizar RAM
        ocr_service = OCRService()
        page_filter = PageFilter()
        extractor = DataExtractor()
        
        # 1. Conta páginas sem carregar conteúdo
        total_pages = pdf_service.get_page_count(pdf_path)
        logger.info(f"[{job_id}] PDF com {total_pages} páginas")
        
        if callback_update:
            callback_update(job_id, "start", total_pages)
        
        # 2. Divide em batches (10 páginas por vez)
        batches = pdf_service.calculate_batches(total_pages, batch_size=10)
        
        all_ocr_results = []
        processed_count = 0
        
        # 3. Processa cada batch sequencialmente
        for batch_num, (start_page, end_page) in enumerate(batches, 1):
            logger.info(f"[{job_id}] Batch {batch_num}/{len(batches)}: páginas {start_page}-{end_page}")
            
            try:
                # Extrai apenas este batch de páginas
                images = pdf_service.extract_page_batch(pdf_path, start_page, end_page)
                
                # OCR em cada página do batch
                for idx, image in enumerate(images):
                    page_num = start_page + idx
                    
                    try:
                        # Pré-processa e extrai texto
                        processed_img = ocr_service.preprocess_image(image)
                        text = ocr_service.extract_text_from_image(processed_img)
                        
                        all_ocr_results.append({
                            "page": page_num,
                            "text": text,
                            "has_content": len(text.strip()) > 0
                        })
                        
                        # Atualiza progresso
                        processed_count += 1
                        if callback_update:
                            callback_update(job_id, "progress", processed_count)
                        
                    except Exception as e:
                        logger.error(f"[{job_id}] Erro na página {page_num}: {e}")
                        all_ocr_results.append({
                            "page": page_num,
                            "text": "",
                            "has_content": False,
                            "error": str(e)
                        })
                    
                    # Libera memória imediatamente
                    del image
                    if 'processed_img' in locals():
                        del processed_img
                
                # Libera batch inteiro
                del images
                
            except Exception as e:
                logger.error(f"[{job_id}] Erro no batch {batch_num}: {e}")
                # Continua para próximo batch
        
        # 4. Filtra páginas relevantes
        logger.info(f"[{job_id}] Filtrando páginas relevantes")
        relevant_pages = page_filter.filter_pages(all_ocr_results)
        
        if not relevant_pages:
            return JobResult(
                job_id=job_id,
                status=JobStatus.ERROR,
                total_pages=total_pages,
                relevant_pages=0,
                records_found=0,
                items=[],
                error_message="Nenhuma página relevante encontrada no documento"
            )
        
        # 5. Extrai dados bancários
        logger.info(f"[{job_id}] Extraindo dados bancários de {len(relevant_pages)} páginas")
        texts = [page["text"] for page in relevant_pages]
        extracted_data = extractor.extract_multiple_records(texts)
        
        if not extracted_data:
            return JobResult(
                job_id=job_id,
                status=JobStatus.ERROR,
                total_pages=total_pages,
                relevant_pages=len(relevant_pages),
                records_found=0,
                items=[],
                error_message="Nenhum dado bancário encontrado"
            )
        
        # 6. Retorna resultado
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[{job_id}] Concluído: {len(extracted_data)} registros em {elapsed:.1f}s")
        
        return JobResult(
            job_id=job_id,
            status=JobStatus.DONE,
            total_pages=total_pages,
            relevant_pages=len(relevant_pages),
            records_found=len(extracted_data),
            items=extracted_data,
            processing_time_seconds=elapsed
        )
        
    except Exception as e:
        logger.exception(f"[{job_id}] Erro fatal no processamento")
        return JobResult(
            job_id=job_id,
            status=JobStatus.ERROR,
            total_pages=0,
            relevant_pages=0,
            records_found=0,
            items=[],
            error_message=str(e)
        )


# Callback adapter para atualizar JobManager de dentro do worker
def update_job_progress(job_id: str, event: str, value: any):
    """
    Adapter para comunicação worker -> JobManager
    
    LIMITAÇÃO: Em ProcessPoolExecutor puro, não há comunicação direta
    Solução atual: logging apenas
    Solução futura: usar Queue ou Redis
    """
    if event == "start":
        logger.info(f"[{job_id}] Total de páginas: {value}")
    elif event == "progress":
        logger.info(f"[{job_id}] Progresso: {value} páginas processadas")
