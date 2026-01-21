"""
Extrator de valores financeiros BASEADO EM RÓTULOS

REGRA ABSOLUTA:
- NENHUM número é considerado valor financeiro sem rótulo associado
- É PROIBIDO somar números soltos
- É PROIBIDO inferir valores

AUTOR: Refatoração baseada em feedback do usuário
DATA: 2026-01-20
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class FinancialLabelExtractor:
    """Extrator que APENAS considera valores com rótulos válidos"""
    
    # WHITELIST FECHADA de rótulos financeiros válidos
    ROTULOS_VALIDOS = {
        # Saldos
        'SALDO ANTERIOR': 'saldo_anterior',
        'SALDO ATUAL': 'saldo_atual',
        'SALDO': 'saldo',
        
        # Movimentações
        'ENTRADA': 'entrada',
        'SAIDA': 'saida',
        'SAÍDA': 'saida',
        
        # Aplicações e resgates
        'APLICACAO': 'aplicacao',
        'APLICAÇÃO': 'aplicacao',
        'APLICACOES': 'aplicacao',
        'APLICAÇÕES': 'aplicacao',
        'RESGATE': 'resgate',
        'RESGATES': 'resgate',
        
        # Rendimentos
        'RENDIMENTO': 'rendimento',
        'RENDIMENTOS': 'rendimento',
        'RENDIMENTO BRUTO': 'rendimento_bruto',
        'RENDIMENTO LIQUIDO': 'rendimento_liquido',
        'RENDIMENTO LÍQUIDO': 'rendimento_liquido',
        
        # Tributos
        'IMPOSTO DE RENDA': 'ir',
        'IR': 'ir',
        'IOF': 'iof',
        'TARIFA': 'tarifa',
        'TARIFA PAGA': 'tarifa_paga',
        'TARIFA DEVOLVIDA': 'tarifa_devolvida',
        
        # Investimentos
        'VALOR DA COTA': 'valor_cota',
        'RENTABILIDADE': 'rentabilidade',
    }
    
    # Limites de sanidade (valores absurdos)
    VALOR_MAX_RAZOAVEL = 1_000_000_000  # 1 bilhão (já é muito!)
    VALOR_MIN_RAZOAVEL = -1_000_000_000
    
    def __init__(self):
        """Inicializa extrator baseado em rótulos"""
        # Compila regex para cada rótulo
        self.rotulo_patterns = {}
        for rotulo, campo in self.ROTULOS_VALIDOS.items():
            # Pattern: ROTULO seguido de valor numérico
            # Exemplo: "SALDO ANTERIOR 168.376,96"
            pattern = rf'\b{re.escape(rotulo)}\b\s*[\:\-]?\s*([0-9]+(?:\.[0-9]+)*(?:,[0-9]+)?)'
            self.rotulo_patterns[rotulo] = {
                'campo': campo,
                'pattern': re.compile(pattern, re.IGNORECASE)
            }
    
    def parse_brazilian_number(self, texto: str) -> Optional[Decimal]:
        """
        Converte número brasileiro para Decimal
        
        Args:
            texto: String com número (ex: "168.376,96")
            
        Returns:
            Decimal ou None se inválido
        """
        try:
            # Remove espaços
            texto = texto.strip()
            
            # Converte formato BR para US
            # "168.376,96" -> "168376.96"
            texto_normalizado = texto.replace('.', '').replace(',', '.')
            
            valor = Decimal(texto_normalizado)
            
            # Valida sanidade
            if valor > self.VALOR_MAX_RAZOAVEL:
                logger.warning(f"⚠️ Valor SUSPEITO (muito alto): {texto} = {valor}")
                return None
            
            if valor < self.VALOR_MIN_RAZOAVEL:
                logger.warning(f"⚠️ Valor SUSPEITO (muito baixo): {texto} = {valor}")
                return None
            
            return valor
            
        except (InvalidOperation, ValueError) as e:
            logger.debug(f"Valor inválido '{texto}': {e}")
            return None
    
    def extract_from_line(
        self, 
        linha: str, 
        page_num: int
    ) -> List[Dict]:
        """
        Extrai valores financeiros de uma linha APENAS com rótulos válidos
        
        Args:
            linha: Linha de texto do OCR
            page_num: Número da página
            
        Returns:
            Lista de valores extraídos com validação
        """
        valores_encontrados = []
        
        # Tenta cada rótulo válido
        for rotulo, config in self.rotulo_patterns.items():
            matches = config['pattern'].finditer(linha)
            
            for match in matches:
                texto_valor = match.group(1)
                valor_decimal = self.parse_brazilian_number(texto_valor)
                
                if valor_decimal is not None:
                    valores_encontrados.append({
                        'rotulo': rotulo,
                        'campo': config['campo'],
                        'valor_texto': texto_valor,
                        'valor_decimal': float(valor_decimal),
                        'pagina': page_num,
                        'linha_original': linha.strip(),
                        'status_validacao': 'OK',
                        'posicao_match': match.start()
                    })
                else:
                    # Valor ilegível ou suspeito
                    valores_encontrados.append({
                        'rotulo': rotulo,
                        'campo': config['campo'],
                        'valor_texto': texto_valor,
                        'valor_decimal': None,
                        'pagina': page_num,
                        'linha_original': linha.strip(),
                        'status_validacao': 'SUSPEITO',
                        'motivo': f'Valor fora dos limites razoáveis: {texto_valor}'
                    })
        
        return valores_encontrados
    
    def extract_from_text(
        self, 
        texto: str, 
        page_num: int
    ) -> Dict[str, List[Dict]]:
        """
        Extrai TODOS os valores financeiros de um texto com validação
        
        Args:
            texto: Texto completo da página
            page_num: Número da página
            
        Returns:
            Dicionário agrupado por campo
        """
        # Divide em linhas
        linhas = texto.split('\n')
        
        # Extrai de cada linha
        todos_valores = []
        for linha in linhas:
            if linha.strip():
                valores = self.extract_from_line(linha, page_num)
                todos_valores.extend(valores)
        
        # Agrupa por campo
        valores_por_campo = {}
        for valor in todos_valores:
            campo = valor['campo']
            if campo not in valores_por_campo:
                valores_por_campo[campo] = []
            valores_por_campo[campo].append(valor)
        
        return valores_por_campo
    
    def calculate_totals_safe(
        self, 
        valores_por_campo: Dict[str, List[Dict]]
    ) -> Dict[str, any]:
        """
        Calcula totais COM VALIDAÇÃO DE SANIDADE
        
        REGRA: Se houver valores suspeitos, BLOQUEIA o total do campo
        
        Args:
            valores_por_campo: Valores agrupados por campo
            
        Returns:
            Totais validados ou erro
        """
        totais = {}
        campos_com_erro = []
        
        for campo, valores in valores_por_campo.items():
            # Conta suspeitos
            valores_suspeitos = [
                v for v in valores 
                if v['status_validacao'] == 'SUSPEITO'
            ]
            
            # Se TEM valores suspeitos, BLOQUEIA o campo inteiro
            if valores_suspeitos:
                logger.warning(f"⚠️ Campo '{campo}' tem {len(valores_suspeitos)} valores suspeitos - BLOQUEANDO TOTAL")
                campos_com_erro.append(campo)
                totais[f'total_{campo}'] = None
                totais[f'total_{campo}_erro'] = f"{len(valores_suspeitos)} valores suspeitos detectados"
                totais[f'total_{campo}_count'] = 0
                continue
            
            # Filtra apenas valores OK
            valores_ok = [
                v['valor_decimal'] 
                for v in valores 
                if v['status_validacao'] == 'OK' and v['valor_decimal'] is not None
            ]
            
            if valores_ok:
                total = sum(valores_ok)
                
                # VALIDAÇÃO FINAL: Total razoável?
                if abs(total) > self.VALOR_MAX_RAZOAVEL:
                    logger.error(
                        f"🚨 TOTAL ABSURDO em '{campo}': R$ {total:,.2f} "
                        f"({len(valores_ok)} valores somados)"
                    )
                    totais[f'total_{campo}'] = None
                    totais[f'total_{campo}_erro'] = f"Total absurdo: {total:,.2f}"
                    campos_com_erro.append(campo)
                else:
                    totais[f'total_{campo}'] = total
                    totais[f'total_{campo}_count'] = len(valores_ok)
            else:
                totais[f'total_{campo}'] = 0.0
                totais[f'total_{campo}_count'] = 0
        
        # Adiciona flags de erro
        totais['tem_valores_suspeitos'] = len(campos_com_erro) > 0
        totais['campos_com_erro'] = campos_com_erro
        
        return totais
    
    def validate_extraction(
        self, 
        valores_por_campo: Dict[str, List[Dict]],
        totais: Dict
    ) -> Dict[str, any]:
        """
        Valida consistência da extração
        
        Returns:
            Relatório de validação
        """
        total_valores = sum(len(v) for v in valores_por_campo.values())
        valores_ok = sum(
            len([x for x in v if x['status_validacao'] == 'OK']) 
            for v in valores_por_campo.values()
        )
        valores_suspeitos = total_valores - valores_ok
        
        # Verifica se há totais bloqueados
        totais_bloqueados = [
            k for k, v in totais.items() 
            if k.endswith('_erro')
        ]
        
        return {
            'total_valores_extraidos': total_valores,
            'valores_ok': valores_ok,
            'valores_suspeitos': valores_suspeitos,
            'percentual_ok': (valores_ok / total_valores * 100) if total_valores > 0 else 0,
            'tem_erros_bloqueantes': len(totais_bloqueados) > 0,
            'erros_bloqueantes': totais_bloqueados,
            'campos_processados': list(valores_por_campo.keys())
        }
