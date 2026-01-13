"""
Serviço para manipulação de PDFs
Suporta extração seletiva de páginas para controle de memória
"""

from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from typing import List
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class PDFService:
    """Serviço responsável por manipulação de arquivos PDF"""
    
    def __init__(self, dpi: int = 200):
        """
        Args:
            dpi: Resolução para conversão (200 é suficiente para OCR, usa menos RAM)
        """
        self.dpi = dpi
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Retorna número total de páginas do PDF sem carregar conteúdo
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Returns:
            Número de páginas
        """
        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception as e:
            logger.error(f"Erro ao contar páginas: {e}")
            raise Exception(f"Erro ao ler PDF: {str(e)}")
    
    def extract_page_batch(
        self, 
        pdf_path: str, 
        start_page: int, 
        end_page: int
    ) -> List[Image.Image]:
        """
        Extrai um batch de páginas do PDF como imagens
        
        IMPORTANTE: Usa first_page/last_page para não carregar PDF inteiro
        
        Args:
            pdf_path: Caminho do arquivo PDF
            start_page: Página inicial (1-indexed)
            end_page: Página final (1-indexed, inclusive)
            
        Returns:
            Lista de imagens PIL (apenas o batch solicitado)
        """
        try:
            logger.info(f"Extraindo páginas {start_page}-{end_page} (DPI: {self.dpi})")
            
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=start_page,
                last_page=end_page,
                fmt='png',
                thread_count=2  # Reduzido para não competir com ProcessPool
            )
            
            return images
            
        except Exception as e:
            logger.error(f"Erro ao extrair páginas {start_page}-{end_page}: {e}")
            raise Exception(f"Erro ao processar páginas: {str(e)}")
    
    def calculate_batches(self, total_pages: int, batch_size: int = 10) -> List[tuple]:
        """
        Divide total de páginas em batches
        
        Args:
            total_pages: Total de páginas do PDF
            batch_size: Tamanho de cada batch
            
        Returns:
            Lista de tuplas (start_page, end_page) para processar
            
        Example:
            >>> calculate_batches(25, 10)
            [(1, 10), (11, 20), (21, 25)]
        """
        batches = []
        for start in range(1, total_pages + 1, batch_size):
            end = min(start + batch_size - 1, total_pages)
            batches.append((start, end))
        
        logger.info(f"PDF dividido em {len(batches)} batches de {batch_size} páginas")
        return batches
