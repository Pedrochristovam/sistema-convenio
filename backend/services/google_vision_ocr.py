"""
Serviço de OCR usando Google Vision API
MUITO MAIS PRECISO que Tesseract para documentos de baixa qualidade
"""

import os
import logging
from typing import List, Dict, Generator
from google.cloud import vision
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
import io

logger = logging.getLogger(__name__)


class GoogleVisionOCR:
    """Serviço de OCR usando Google Vision API"""
    
    def __init__(self, credentials_path: str = None, batch_size: int = 10, dpi: int = 300):
        """
        Inicializa o serviço de OCR com Google Vision
        
        Args:
            credentials_path: Caminho para o arquivo JSON de credenciais do Google Cloud
                             Se None, usa a variável de ambiente GOOGLE_APPLICATION_CREDENTIALS
            batch_size: Páginas por batch (padrão: 10)
            dpi: Resolução das imagens (300 é suficiente para Google Vision)
        """
        self.batch_size = batch_size
        self.dpi = dpi
        
        # Configura credenciais
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            logger.info(f"Google Vision: usando credenciais de {credentials_path}")
        elif 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            logger.info("Google Vision: usando credenciais da variável de ambiente")
        else:
            raise Exception(
                "Credenciais do Google Cloud não encontradas!\n"
                "Configure a variável GOOGLE_APPLICATION_CREDENTIALS ou forneça o caminho do arquivo JSON."
            )
        
        # Inicializa cliente
        try:
            self.client = vision.ImageAnnotatorClient()
            logger.info("✅ Google Vision API inicializada com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Google Vision API: {e}")
            raise Exception(f"Erro ao inicializar Google Vision: {str(e)}")
    
    def get_page_count(self, pdf_path: str) -> int:
        """Conta páginas do PDF"""
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
    ) -> List:
        """Converte batch de páginas do PDF em imagens"""
        try:
            logger.info(f"Extraindo páginas {start_page}-{end_page} (DPI: {self.dpi})")
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=start_page,
                last_page=end_page,
                fmt='png'
            )
            return images
        except Exception as e:
            logger.error(f"Erro ao converter páginas {start_page}-{end_page}: {e}")
            raise Exception(f"Erro ao converter PDF em imagens: {str(e)}")
    
    def extract_text_from_image(self, image) -> str:
        """
        Extrai texto de imagem usando Google Vision API
        
        Args:
            image: Imagem PIL
            
        Returns:
            Texto extraído
        """
        try:
            # Converte PIL Image para bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Cria objeto de imagem para Google Vision
            vision_image = vision.Image(content=img_byte_arr)
            
            # Executa OCR
            response = self.client.text_detection(image=vision_image)
            
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            # Pega texto completo
            texts = response.text_annotations
            if texts:
                # O primeiro elemento contém o texto completo
                return texts[0].description
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Erro ao executar OCR: {e}")
            raise Exception(f"Erro ao executar Google Vision OCR: {str(e)}")
    
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
                
                try:
                    logger.info(f"📄 Processando página {page_num} com Google Vision...")
                    
                    # OCR com Google Vision
                    text = self.extract_text_from_image(image)
                    
                    results.append({
                        "page": page_num,
                        "text": text,
                        "has_content": len(text.strip()) > 0,
                        "ocr_engine": "Google Vision API"
                    })
                    
                    logger.info(f"✅ Página {page_num}: {len(text)} caracteres extraídos")
                    
                except Exception as e:
                    logger.error(f"Erro na página {page_num}: {e}")
                    results.append({
                        "page": page_num,
                        "text": "",
                        "has_content": False,
                        "error": str(e),
                        "ocr_engine": "Google Vision API"
                    })
                
                finally:
                    # Libera memória
                    del image
            
            return results
            
        finally:
            # Garante limpeza do batch
            if images is not None:
                del images
    
    def process_pdf_in_batches(self, pdf_path: str) -> Generator[List[Dict], None, None]:
        """
        Generator que processa PDF em batches
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Yields:
            Lista de resultados de cada batch
        """
        try:
            # Conta páginas
            total_pages = self.get_page_count(pdf_path)
            logger.info(f"📄 PDF com {total_pages} páginas, processando com Google Vision...")
            
            # Processa em batches
            for start in range(1, total_pages + 1, self.batch_size):
                end = min(start + self.batch_size - 1, total_pages)
                
                logger.info(f"🔄 Processando batch: páginas {start}-{end}")
                batch_results = self.process_pdf_batch(pdf_path, start, end)
                
                yield batch_results
                
                # Força garbage collection entre batches
                import gc
                gc.collect()
        
        except Exception as e:
            logger.exception(f"Erro ao processar PDF em batches: {e}")
            raise Exception(f"Erro ao processar PDF: {str(e)}")
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Processa PDF completo em batches
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Returns:
            Lista completa de resultados OCR
        """
        all_results = []
        
        for batch_results in self.process_pdf_in_batches(pdf_path):
            all_results.extend(batch_results)
        
        logger.info(f"✅ Google Vision processou {len(all_results)} páginas com sucesso!")
        return all_results
