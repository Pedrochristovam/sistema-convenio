"""
Serviço para filtrar páginas relevantes do documento
Identifica páginas que contêm informações de convênio bancário
"""

from typing import List, Dict


class PageFilter:
    """Serviço responsável por filtrar páginas relevantes"""
    
    def __init__(self):
        """Inicializa o filtro de páginas"""
        # Palavras-chave que indicam páginas relevantes
        self.keywords = [
            "CONVÊNIO",
            "CONVENIO",
            "BANCO",
            "DADOS BANCÁRIOS",
            "DADOS BANCARIOS",
            "AGÊNCIA",
            "AGENCIA",
            "CONTA",
            "CONTA CORRENTE",
            "CONTA POUPANÇA",
            "POUPANCA",
            "CPF",
            "CNPJ",
            "INSTITUIÇÃO FINANCEIRA",
            "INSTITUICAO FINANCEIRA",
            "BANCO DO BRASIL",
            "BRADESCO",
            "ITAU",
            "ITAU",
            "SANTANDER",
            "CAIXA",
            "CAIXA ECONOMICA",
            "NUBANK",
            "INTER"
        ]
    
    def is_relevant_page(self, text: str) -> bool:
        """
        Verifica se uma página contém informações relevantes
        
        Args:
            text: Texto extraído da página
            
        Returns:
            True se a página for relevante, False caso contrário
        """
        if not text or len(text.strip()) == 0:
            return False
        
        # Converte texto para maiúsculas para comparação case-insensitive
        text_upper = text.upper()
        
        # Conta quantas palavras-chave aparecem na página
        keyword_count = sum(1 for keyword in self.keywords if keyword in text_upper)
        
        # Considera relevante se encontrar pelo menos 2 palavras-chave
        # ou se encontrar palavras-chave muito específicas
        high_priority_keywords = ["CONVÊNIO", "CONVENIO", "DADOS BANCÁRIOS", "DADOS BANCARIOS"]
        has_high_priority = any(kw in text_upper for kw in high_priority_keywords)
        
        return keyword_count >= 2 or has_high_priority
    
    def filter_pages(self, ocr_results: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Filtra apenas as páginas relevantes do documento
        
        Args:
            ocr_results: Lista de resultados do OCR por página
            [{"page": 1, "text": "...", "has_content": True}, ...]
            
        Returns:
            Lista filtrada apenas com páginas relevantes
        """
        relevant_pages = []
        
        for page_data in ocr_results:
            if not page_data.get("has_content", False):
                continue
            
            text = page_data.get("text", "")
            
            if self.is_relevant_page(text):
                relevant_pages.append({
                    "page": page_data["page"],
                    "text": text,
                    "has_content": True
                })
        
        return relevant_pages
    
    def get_relevant_text(self, ocr_results: List[Dict[str, any]]) -> str:
        """
        Retorna todo o texto das páginas relevantes concatenado
        
        Args:
            ocr_results: Lista de resultados do OCR por página
            
        Returns:
            Texto concatenado de todas as páginas relevantes
        """
        relevant_pages = self.filter_pages(ocr_results)
        
        # Concatena textos das páginas relevantes
        texts = [page["text"] for page in relevant_pages]
        
        return "\n\n".join(texts)
