"""
Teste do novo extrator baseado em rótulos
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from services.financial_label_extractor import FinancialLabelExtractor

# Texto REAL de exemplo
texto_exemplo = """
Banco do Brasil
Extrato Conta Corrente

SALDO ANTERIOR 168.376,96
30/09/2015 APLICAÇÃO 100.000,00
04/11/2015 RESGATE 50.000,00  
15/11/2015 RENDIMENTO 1.234,56
SALDO ATUAL 219.611,52

Quantidade de cotas: 55.443,265418
Código transação: 3169800722
"""

print("=" * 80)
print("TESTE DO EXTRATOR BASEADO EM RÓTULOS")
print("=" * 80)

extractor = FinancialLabelExtractor()

# Extrai valores
valores_por_campo = extractor.extract_from_text(texto_exemplo, page_num=1)

print("\n📊 VALORES EXTRAÍDOS POR CAMPO:")
print("=" * 80)
for campo, valores in valores_por_campo.items():
    print(f"\n{campo.upper()}:")
    for v in valores:
        status_emoji = "✅" if v['status_validacao'] == 'OK' else "❌"
        print(f"  {status_emoji} Rótulo: {v['rotulo']}")
        print(f"     Valor: R$ {v['valor_decimal']:,.2f}" if v['valor_decimal'] else f"     Valor: SUSPEITO")
        print(f"     Página: {v['pagina']}")
        print(f"     Linha: {v['linha_original'][:60]}...")

# Calcula totais
print("\n" + "=" * 80)
print("TOTAIS CALCULADOS")
print("=" * 80)
totais = extractor.calculate_totals_safe(valores_por_campo)
for key, value in totais.items():
    if not key.endswith('_count') and not key.endswith('_erro') and not key.startswith('tem_') and not key.startswith('campos_'):
        if value is not None:
            print(f"{key}: R$ {value:,.2f}")
        else:
            print(f"{key}: BLOQUEADO (erro: {totais.get(key + '_erro', 'desconhecido')})")

# Validação
print("\n" + "=" * 80)
print("VALIDAÇÃO DA EXTRAÇÃO")
print("=" * 80)
validacao = extractor.validate_extraction(valores_por_campo, totais)
for key, value in validacao.items():
    print(f"{key}: {value}")

print("\n" + "=" * 80)
print("✅ TESTE CONCLUÍDO")
print("=" * 80)

# Teste com valor absurdo (para validar bloqueio)
print("\n" + "=" * 80)
print("TESTE COM VALOR ABSURDO (deve bloquear)")
print("=" * 80)

texto_absurdo = """
SALDO ANTERIOR 3.254.269.459,98
"""

valores_absurdo = extractor.extract_from_text(texto_absurdo, page_num=1)
totais_absurdo = extractor.calculate_totals_safe(valores_absurdo)

print("Resultado:")
if totais_absurdo.get('total_saldo_anterior') is None:
    print("✅ BLOQUEADO CORRETAMENTE!")
    print(f"   Motivo: {totais_absurdo.get('total_saldo_anterior_erro')}")
else:
    print("❌ ERRO: Deveria ter bloqueado!")
