"""
Extrator de Convênio SEGURO com validação baseada em rótulos

GARANTE:
- Apenas valores com rótulos válidos
- Validação de sanidade
- Bloqueio de valores absurdos
- Rastreabilidade por página
"""

import logging
from typing import Dict, List, Optional
from services.financial_label_extractor import FinancialLabelExtractor

logger = logging.getLogger(__name__)


class SafeConvenioExtractor:
    """
    Extrator de convênio que usa validação baseada em rótulos
    
    DIFERENÇA DO ANTIGO:
    - Não extrai números soltos
    - Valida TODOS os valores
    - Bloqueia totais absurdos
    """
    
    def __init__(self):
        """Inicializa com extrator baseado em rótulos"""
        self.label_extractor = FinancialLabelExtractor()
    
    def extract_from_page(
        self,
        ocr_result: Dict,
        documento_id: str
    ) -> Dict:
        """
        Extrai dados de UMA página com validação
        
        Args:
            ocr_result: Resultado do OCR {"page": 1, "text": "..."}
            documento_id: ID do documento
            
        Returns:
            Dados validados da página
        """
        page_num = ocr_result.get('page', 0)
        texto = ocr_result.get('text', '')
        
        # Extrai valores com rótulos
        valores_por_campo = self.label_extractor.extract_from_text(texto, page_num)
        
        # Converte para formato de movimentações
        movimentacoes = []
        
        # Para cada valor extraído, cria uma movimentação
        for campo, valores_list in valores_por_campo.items():
            for valor_info in valores_list:
                if valor_info['status_validacao'] == 'OK':
                    # Cria movimentação a partir do rótulo
                    movimentacao = self._create_movimentacao_from_label(
                        valor_info,
                        documento_id,
                        page_num
                    )
                    if movimentacao:
                        movimentacoes.append(movimentacao)
        
        return {
            'page': page_num,
            'movimentacoes': movimentacoes,
            'valores_raw': valores_por_campo,
            'tem_erros': any(
                v['status_validacao'] != 'OK'
                for values in valores_por_campo.values()
                for v in values
            )
        }
    
    def _create_movimentacao_from_label(
        self,
        valor_info: Dict,
        documento_id: str,
        page_num: int
    ) -> Optional[Dict]:
        """
        Cria movimentação a partir de um valor com rótulo
        
        Args:
            valor_info: Info do valor extraído
            documento_id: ID do documento
            page_num: Número da página
            
        Returns:
            Movimentação formatada ou None
        """
        import uuid
        from datetime import datetime
        
        # Mapeamento de campos para estrutura de movimentação
        campo = valor_info['campo']
        valor = valor_info['valor_decimal']
        
        movimentacao = {
            'id': str(uuid.uuid4()),
            'data': None,  # TODO: Extrair data da linha
            'descricao_item': valor_info['rotulo'],
            'entrada': 0.0,
            'saida': 0.0,
            'saldo': 0.0,
            'aplicacao': None,
            'resgate': None,
            'rendimentos': None,
            'tarifa_paga': None,
            'tarifa_devolvida': None,
            'saldo_tarifa': 0.0,
            'tipo_documento': 'EXTRATO_CONVENIO_MOVIMENTACAO',
            'origem_documento': f'pagina_{page_num}.pdf',
            'documento_id': documento_id,
            'linha_origem': 0,
            'texto_original': valor_info['linha_original'],
            'metodo_extracao': 'label_based',
            'confianca': 'ALTO',
            'valor_validado': True
        }
        
        # Mapeia valor para campo correto
        if campo == 'entrada':
            movimentacao['entrada'] = valor
        elif campo == 'saida':
            movimentacao['saida'] = valor
        elif campo in ['saldo', 'saldo_atual', 'saldo_anterior']:
            movimentacao['saldo'] = valor
        elif campo == 'aplicacao':
            movimentacao['aplicacao'] = valor
            movimentacao['entrada'] = valor
        elif campo == 'resgate':
            movimentacao['resgate'] = valor
            movimentacao['saida'] = valor
        elif campo in ['rendimento', 'rendimento_bruto', 'rendimento_liquido']:
            movimentacao['rendimentos'] = valor
            movimentacao['entrada'] = valor
        elif campo == 'tarifa_paga':
            movimentacao['tarifa_paga'] = valor
            movimentacao['saida'] = valor
        elif campo == 'tarifa_devolvida':
            movimentacao['tarifa_devolvida'] = valor
            movimentacao['entrada'] = valor
        
        return movimentacao
    
    def extract_convenio_data_from_pages(
        self,
        ocr_results: List[Dict],
        documento_id: str
    ) -> Dict:
        """
        Extrai dados de TODAS as páginas com validação
        
        Args:
            ocr_results: Lista de resultados do OCR
            documento_id: ID do documento
            
        Returns:
            Dados completos do convênio validados
        """
        logger.info(f"[SAFE_EXTRACTOR] Processando {len(ocr_results)} páginas com validação")
        
        todas_movimentacoes = []
        paginas_com_erro = []
        
        # Processa cada página
        for ocr_result in ocr_results:
            resultado_pagina = self.extract_from_page(ocr_result, documento_id)
            
            todas_movimentacoes.extend(resultado_pagina['movimentacoes'])
            
            if resultado_pagina['tem_erros']:
                paginas_com_erro.append(resultado_pagina['page'])
        
        # Calcula totais COM VALIDAÇÃO
        totais = self._calculate_safe_totals(todas_movimentacoes)
        
        # Monta resultado
        resultado = {
            'tipo_documento': 'EXTRATO_CONVENIO_MOVIMENTACAO',
            'documento_id': documento_id,
            'cabecalho': {
                'convenio': None,  # TODO: Extrair cabeçalho
                'convenente': None,
                'vigencia': None,
                'conta_corrente': None
            },
            'movimentacoes': todas_movimentacoes,
            'totais': totais,
            'validacao': {
                'total_movimentacoes': len(todas_movimentacoes),
                'paginas_processadas': len(ocr_results),
                'paginas_com_erro': paginas_com_erro,
                'tem_valores_bloqueados': totais.get('tem_valores_suspeitos', False)
            }
        }
        
        logger.info(
            f"[SAFE_EXTRACTOR] Extraído: {len(todas_movimentacoes)} movimentações, "
            f"{len(paginas_com_erro)} páginas com erro"
        )
        
        # Gera relatório detalhado
        resultado['relatorio_detalhado'] = self._generate_detailed_report(
            ocr_results, 
            todas_movimentacoes
        )
        
        return resultado
    
    def _generate_detailed_report(
        self,
        ocr_results: List[Dict],
        movimentacoes: List[Dict]
    ) -> Dict:
        """
        Gera relatório detalhado por página
        
        Args:
            ocr_results: Resultados do OCR
            movimentacoes: Movimentações extraídas
            
        Returns:
            Relatório estruturado
        """
        relatorio = {
            'total_paginas': len(ocr_results),
            'total_valores_extraidos': len(movimentacoes),
            'por_pagina': []
        }
        
        # Agrupa movimentações por página
        movs_por_pagina = {}
        for mov in movimentacoes:
            page = mov.get('origem_documento', 'desconhecida')
            if page not in movs_por_pagina:
                movs_por_pagina[page] = []
            movs_por_pagina[page].append(mov)
        
        # Cria relatório por página
        for ocr_result in ocr_results:
            page_num = ocr_result.get('page', 0)
            page_key = f'pagina_{page_num}.pdf'
            
            movs_pagina = movs_por_pagina.get(page_key, [])
            
            # Extrai texto para análise
            texto = ocr_result.get('text', '')
            valores_por_campo = self.label_extractor.extract_from_text(texto, page_num)
            
            relatorio_pagina = {
                'pagina': page_num,
                'valores_encontrados': len(movs_pagina),
                'valores_por_tipo': {},
                'texto_amostra': texto[:200] + '...' if len(texto) > 200 else texto
            }
            
            # Agrupa valores por tipo
            for mov in movs_pagina:
                rotulo = mov.get('descricao_item', 'Desconhecido')
                if rotulo not in relatorio_pagina['valores_por_tipo']:
                    relatorio_pagina['valores_por_tipo'][rotulo] = []
                
                relatorio_pagina['valores_por_tipo'][rotulo].append({
                    'entrada': mov.get('entrada', 0),
                    'saida': mov.get('saida', 0),
                    'saldo': mov.get('saldo', 0),
                    'aplicacao': mov.get('aplicacao'),
                    'resgate': mov.get('resgate'),
                    'rendimento': mov.get('rendimentos'),
                    'linha_original': mov.get('texto_original', '')[:100]
                })
            
            relatorio['por_pagina'].append(relatorio_pagina)
        
        return relatorio
    
    def _calculate_safe_totals(self, movimentacoes: List[Dict]) -> Dict:
        """
        Calcula totais COM VALIDAÇÃO DE SANIDADE
        
        Args:
            movimentacoes: Lista de movimentações
            
        Returns:
            Totais validados
        """
        totais = {
            'total_entrada': 0.0,
            'total_saida': 0.0,
            'saldo_final': 0.0,
            'total_aplicacao': 0.0,
            'total_resgate': 0.0,
            'total_rendimentos': 0.0,
            'count_movimentacoes': len(movimentacoes)
        }
        
        for mov in movimentacoes:
            if mov.get('valor_validado', False):  # Apenas valores validados
                totais['total_entrada'] += mov.get('entrada', 0) or 0
                totais['total_saida'] += mov.get('saida', 0) or 0
                totais['total_aplicacao'] += mov.get('aplicacao', 0) or 0
                totais['total_resgate'] += mov.get('resgate', 0) or 0
                totais['total_rendimentos'] += mov.get('rendimentos', 0) or 0
        
        totais['saldo_final'] = totais['total_entrada'] - totais['total_saida']
        
        # VALIDAÇÃO FINAL: Totais razoáveis?
        MAX_RAZOAVEL = 1_000_000_000  # 1 bilhão
        campos_bloqueados = []
        
        for campo, valor in totais.items():
            if isinstance(valor, (int, float)) and abs(valor) > MAX_RAZOAVEL:
                logger.error(f"🚨 TOTAL ABSURDO em '{campo}': R$ {valor:,.2f}")
                totais[campo] = None
                totais[f'{campo}_erro'] = f"Total absurdo: {valor:,.2f}"
                campos_bloqueados.append(campo)
        
        totais['tem_valores_suspeitos'] = len(campos_bloqueados) > 0
        totais['campos_bloqueados'] = campos_bloqueados
        
        return totais
