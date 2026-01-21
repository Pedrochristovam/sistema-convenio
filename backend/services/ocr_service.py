"""
Serviço de OCR para processamento de documentos PDF
Converte PDF em imagens, aplica pré-processamento com OpenCV
e executa OCR com Tesseract

REFATORADO: Suporta processamento em batches para PDFs grandes
"""

import os
import tempfile
import logging
from typing import List, Dict, Generator
import cv2
import numpy as np
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class OCRService:
    """Serviço responsável por OCR de documentos PDF"""
    
    def __init__(self, dpi: int = 400, batch_size: int = 10):
        """
        Inicializa o serviço de OCR
        
        Args:
            dpi: Resolução (400 para documentos escaneados de baixa qualidade)
            batch_size: Páginas por batch (padrão: 10)
        """
        # Config otimizada para TABELAS e COLUNAS (PSM 4)
        # REMOVIDO whitelist que estava impedindo leitura correta
        self.tesseract_config = '--oem 3 --psm 4 -l por'
        self.dpi = dpi
        self.batch_size = batch_size
        
        logger.info(f"OCR iniciado: DPI={dpi}, PSM=4 (detecção de colunas)")
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Conta páginas sem carregar conteúdo
        
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
    
    def pdf_to_images_batch(
        self, 
        pdf_path: str, 
        start_page: int, 
        end_page: int
    ) -> List[Image.Image]:
        """
        Converte BATCH de páginas (não o PDF inteiro)
        
        CRÍTICO: Usa first_page/last_page para não carregar tudo na RAM
        
        Args:
            pdf_path: Caminho do arquivo PDF
            start_page: Página inicial (1-indexed)
            end_page: Página final (1-indexed, inclusive)
            
        Returns:
            Lista de imagens PIL apenas do batch
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
            logger.error(f"Erro ao converter páginas {start_page}-{end_page}: {e}")
            raise Exception(f"Erro ao converter PDF em imagens: {str(e)}")
    
    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Pré-processa imagem para melhorar qualidade do OCR
        OTIMIZADO para documentos escaneados de BAIXA QUALIDADE
        
        Args:
            image: Imagem PIL
            
        Returns:
            Imagem processada como array numpy
        """
        # Converte PIL Image para array numpy
        img_array = np.array(image)
        
        # Converte para escala de cinza
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # PASSO 1: Redimensiona para AUMENTAR resolução (1.5x ao invés de 2x)
        # Balanço entre qualidade e velocidade
        height, width = gray.shape
        gray = cv2.resize(gray, (int(width * 1.5), int(height * 1.5)), interpolation=cv2.INTER_CUBIC)
        
        # PASSO 2: Denoise RÁPIDO (Gaussian Blur ao invés de fastNlMeans)
        denoised = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # PASSO 3: Aumenta contraste FORTE
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # PASSO 4: Sharpen para realçar bordas dos caracteres
        kernel_sharpen = np.array([[-1,-1,-1],
                                   [-1, 9,-1],
                                   [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel_sharpen)
        
        # PASSO 5: Binarização ADAPTATIVA (melhor que Otsu para documentos não uniformes)
        binary = cv2.adaptiveThreshold(
            sharpened, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            15,  # Block size (aumentado para documentos escaneados)
            3    # C constant
        )
        
        # PASSO 6: Morfologia para limpar ruído pequeno
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # PASSO 7: Dilata LEVEMENTE para conectar caracteres quebrados
        kernel_dilate = np.ones((2, 2), np.uint8)
        final = cv2.dilate(cleaned, kernel_dilate, iterations=1)
        
        return final
    
    def extract_text_from_image(self, processed_image: np.ndarray) -> str:
        """
        Extrai texto de imagem processada usando Tesseract
        
        Args:
            processed_image: Imagem processada como array numpy
            
        Returns:
            Texto extraído
        """
        try:
            # Converte array numpy de volta para PIL Image
            pil_image = Image.fromarray(processed_image)
            
            # Executa OCR
            text = pytesseract.image_to_string(
                pil_image,
                config=self.tesseract_config
            )
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Erro ao executar OCR: {str(e)}")
    
    def process_pdf_batch(
        self,
        pdf_path: str,
        start_page: int,
        end_page: int
    ) -> List[Dict[str, any]]:
        """
        Processa UM BATCH de páginas do PDF
        
        Args:
            pdf_path: Caminho do arquivo PDF
            start_page: Página inicial (1-indexed)
            end_page: Página final (1-indexed)
            
        Returns:
            Lista de resultados apenas do batch processado
        """
        results = []
        images = None
        
        try:
            # Extrai apenas este batch
            images = self.pdf_to_images_batch(pdf_path, start_page, end_page)
            
            # Processa cada página do batch
            for idx, image in enumerate(images):
                page_num = start_page + idx
                processed = None
                
                try:
                    # Pré-processa
                    processed = self.preprocess_image(image)
                    
                    # OCR
                    text = self.extract_text_from_image(processed)
                    
                    results.append({
                        "page": page_num,
                        "text": text,
                        "has_content": len(text.strip()) > 0
                    })
                    
                except Exception as e:
                    logger.error(f"Erro na página {page_num}: {e}")
                    results.append({
                        "page": page_num,
                        "text": "",
                        "has_content": False,
                        "error": str(e)
                    })
                
                finally:
                    # Libera memória IMEDIATAMENTE
                    if processed is not None:
                        del processed
                    del image
            
            return results
            
        finally:
            # Garante limpeza do batch
            if images is not None:
                del images
    
    def process_pdf_in_batches(self, pdf_path: str) -> Generator[List[Dict], None, None]:
        """
        Generator que processa PDF em batches
        
        IMPORTANTE: Libera memória entre batches
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Yields:
            Lista de resultados de cada batch
        """
        try:
            # Conta páginas
            total_pages = self.get_page_count(pdf_path)
            logger.info(f"PDF com {total_pages} páginas, dividindo em batches de {self.batch_size}")
            
            # Processa em batches
            for start in range(1, total_pages + 1, self.batch_size):
                end = min(start + self.batch_size - 1, total_pages)
                
                logger.info(f"Processando batch: páginas {start}-{end}")
                batch_results = self.process_pdf_batch(pdf_path, start, end)
                
                yield batch_results
                
                # Força garbage collection entre batches (opcional)
                import gc
                gc.collect()
        
        except Exception as e:
            logger.exception(f"Erro ao processar PDF em batches: {e}")
            raise Exception(f"Erro ao processar PDF: {str(e)}")
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Processa PDF completo em batches (COMPATIBILIDADE)
        
        Mantido para não quebrar código existente, mas usa batches internamente
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Returns:
            Lista completa de resultados OCR
        """
        all_results = []
        
        for batch_results in self.process_pdf_in_batches(pdf_path):
            all_results.extend(batch_results)
        
        return all_results
