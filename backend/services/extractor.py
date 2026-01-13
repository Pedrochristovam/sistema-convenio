"""
Serviço para extrair dados bancários de textos OCR
Usa regex para identificar informações estruturadas
"""

import re
from typing import List, Dict, Optional


class DataExtractor:
    """Serviço responsável por extrair dados bancários"""
    
    def __init__(self):
        """Inicializa o extrator de dados"""
        # Lista de bancos conhecidos
        self.banks = [
            "BANCO DO BRASIL", "BB", "BANCO BRASIL",
            "BRADESCO", "BRADESCO S.A.",
            "ITAU", "ITAU UNIBANCO", "ITAU S.A.",
            "SANTANDER", "BANCO SANTANDER",
            "CAIXA", "CAIXA ECONOMICA FEDERAL", "CEF",
            "NUBANK", "NU PAGAMENTOS",
            "INTER", "BANCO INTER",
            "BANRISUL", "BANCO DO ESTADO DO RIO GRANDE DO SUL",
            "SICREDI", "BANCO SICREDI",
            "SICOOB", "BANCO COOPERATIVO SICOOB"
        ]
    
    def extract_bank_name(self, text: str) -> Optional[str]:
        """
        Extrai nome do banco do texto
        
        Args:
            text: Texto para análise
            
        Returns:
            Nome do banco encontrado ou None
        """
        text_upper = text.upper()
        
        # Procura por nomes de bancos conhecidos
        for bank in self.banks:
            if bank.upper() in text_upper:
                return bank
        
        # Tenta padrões genéricos
        patterns = [
            r'BANCO\s+([A-ZÁÉÍÓÚÇ\s]+?)(?:\s|$|\.|,)',
            r'INSTITUI[ÇC][AÃ]O\s+FINANCEIRA\s+([A-ZÁÉÍÓÚÇ\s]+?)(?:\s|$|\.|,)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_upper, re.IGNORECASE)
            if match:
                bank_name = match.group(1).strip()
                if len(bank_name) > 3:  # Filtra nomes muito curtos
                    return bank_name
        
        return None
    
    def extract_agency(self, text: str) -> Optional[str]:
        """
        Extrai número da agência
        
        Args:
            text: Texto para análise
            
        Returns:
            Número da agência ou None
        """
        # Padrões para agência (geralmente 4 dígitos)
        patterns = [
            r'AG[EÊ]NCIA[:\s]+(\d{4,5})',
            r'AG[EÊ]NCIA[:\s]+(\d{1,2}\.\d{3})',
            r'AG[:\s]+(\d{4,5})',
            r'AG[:\s]+(\d{1,2}\.\d{3})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                agency = match.group(1).replace('.', '').strip()
                if len(agency) >= 4:
                    return agency
        
        return None
    
    def extract_account(self, text: str) -> Optional[str]:
        """
        Extrai número da conta
        
        Args:
            text: Texto para análise
            
        Returns:
            Número da conta ou None
        """
        # Padrões para conta (geralmente 5-10 dígitos, pode ter hífen)
        patterns = [
            r'CONTA[:\s]+(\d{5,10})',
            r'CONTA[:\s]+(\d{1,5}[-\.]?\d{1,5})',
            r'CONTA\s+CORRENTE[:\s]+(\d{5,10})',
            r'CONTA\s+POUPAN[ÇC]A[:\s]+(\d{5,10})',
            r'CC[:\s]+(\d{5,10})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                account = match.group(1).replace('.', '').replace('-', '').strip()
                if len(account) >= 5:
                    return account
        
        return None
    
    def extract_account_type(self, text: str) -> Optional[str]:
        """
        Extrai tipo de conta
        
        Args:
            text: Texto para análise
            
        Returns:
            Tipo de conta (CORRENTE, POUPANÇA, etc.) ou None
        """
        text_upper = text.upper()
        
        if 'POUPANÇA' in text_upper or 'POUPANCA' in text_upper:
            return 'POUPANÇA'
        elif 'CORRENTE' in text_upper:
            return 'CORRENTE'
        elif 'CC' in text_upper:
            return 'CORRENTE'
        elif 'CP' in text_upper:
            return 'POUPANÇA'
        
        return None
    
    def extract_cpf_cnpj(self, text: str) -> Optional[str]:
        """
        Extrai CPF ou CNPJ
        
        Args:
            text: Texto para análise
            
        Returns:
            CPF ou CNPJ formatado ou None
        """
        # Remove espaços e caracteres especiais para busca
        clean_text = re.sub(r'[^\d]', '', text)
        
        # Padrão CNPJ (14 dígitos)
        cnpj_pattern = r'(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2})'
        cnpj_match = re.search(cnpj_pattern, text)
        if cnpj_match:
            cnpj = re.sub(r'[^\d]', '', cnpj_match.group(1))
            if len(cnpj) == 14:
                return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        
        # Padrão CPF (11 dígitos)
        cpf_pattern = r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})'
        cpf_match = re.search(cpf_pattern, text)
        if cpf_match:
            cpf = re.sub(r'[^\d]', '', cpf_match.group(1))
            if len(cpf) == 11:
                return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        
        return None
    
    def extract_value(self, text: str) -> Optional[float]:
        """
        Extrai valores monetários
        
        Args:
            text: Texto para análise
            
        Returns:
            Valor numérico ou None
        """
        # Padrões para valores monetários
        patterns = [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*R\$',
            r'VALOR[:\s]+R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Pega o maior valor encontrado (geralmente é o principal)
                values = []
                for match in matches:
                    value_str = match.replace('.', '').replace(',', '.')
                    try:
                        values.append(float(value_str))
                    except:
                        pass
                if values:
                    return max(values)
        
        return None
    
    def extract_all(self, text: str) -> Dict[str, any]:
        """
        Extrai todas as informações bancárias do texto
        
        Args:
            text: Texto completo para análise
            
        Returns:
            Dicionário com todos os dados extraídos
        """
        return {
            "banco": self.extract_bank_name(text),
            "agencia": self.extract_agency(text),
            "conta": self.extract_account(text),
            "tipo_conta": self.extract_account_type(text),
            "cpf_cnpj": self.extract_cpf_cnpj(text),
            "valor": self.extract_value(text)
        }
    
    def extract_multiple_records(self, pages_text: List[str]) -> List[Dict[str, any]]:
        """
        Extrai múltiplos registros de múltiplas páginas ou seções
        
        Args:
            pages_text: Lista de textos de páginas relevantes
            
        Returns:
            Lista de dicionários com dados extraídos
        """
        all_records = []
        
        # Processa cada página/seção
        for text in pages_text:
            if not text or len(text.strip()) == 0:
                continue
            
            # Extrai dados desta seção
            record = self.extract_all(text)
            
            # Só adiciona se tiver pelo menos banco ou agência/conta
            if record.get("banco") or (record.get("agencia") and record.get("conta")):
                all_records.append(record)
        
        # Remove duplicatas baseado em agência + conta
        unique_records = []
        seen = set()
        
        for record in all_records:
            key = f"{record.get('agencia', '')}_{record.get('conta', '')}"
            if key and key not in seen:
                seen.add(key)
                unique_records.append(record)
            elif not key:  # Se não tem agência/conta, adiciona mesmo assim
                unique_records.append(record)
        
        return unique_records if unique_records else all_records
