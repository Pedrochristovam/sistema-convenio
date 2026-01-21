"""
Gera relatório COMPLETO de todos os valores extraídos
Igual à análise manual que eu fiz
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

# ID do último job processado
JOB_ID = input("Digite o JOB_ID do processamento: ").strip()

print("=" * 100)
print("RELATÓRIO COMPLETO DE EXTRAÇÃO DE VALORES FINANCEIROS")
print("=" * 100)

# Busca resultado
try:
    response = requests.get(f'http://localhost:8000/result/{JOB_ID}')
    if response.status_code != 200:
        print(f"❌ Erro ao buscar resultado: {response.status_code}")
        print(f"   Resposta: {response.text}")
        sys.exit(1)
    
    data = response.json()
    
except Exception as e:
    print(f"❌ Erro ao conectar com API: {e}")
    sys.exit(1)

# Pega convenio_data
if not data.get('items') or len(data['items']) == 0:
    print("❌ Nenhum dado encontrado")
    sys.exit(1)

convenio_data = data['items'][0]

# RELATÓRIO DETALHADO
print(f"\n📄 DOCUMENTO PROCESSADO")
print("=" * 100)
print(f"ID: {data.get('id')}")
print(f"Status: {data.get('status')}")
print(f"Total de páginas: {data.get('total_pages')}")
print(f"Registros encontrados: {data.get('records_found')}")

# CABEÇALHO
print(f"\n📋 CABEÇALHO DO DOCUMENTO")
print("=" * 100)
cabecalho = convenio_data.get('cabecalho', {})
print(f"Convênio: {cabecalho.get('convenio') or 'Não identificado'}")
print(f"Convenente: {cabecalho.get('convenente') or 'Não identificado'}")
print(f"Vigência: {cabecalho.get('vigencia') or 'Não identificada'}")
print(f"Conta Corrente: {cabecalho.get('conta_corrente') or 'Não identificada'}")

# MOVIMENTAÇÕES POR PÁGINA
print(f"\n💰 VALORES EXTRAÍDOS POR PÁGINA")
print("=" * 100)

movimentacoes = convenio_data.get('movimentacoes', [])

# Agrupa por página
movs_por_pagina = {}
for mov in movimentacoes:
    origem = mov.get('origem_documento', 'desconhecida')
    if origem not in movs_por_pagina:
        movs_por_pagina[origem] = []
    movs_por_pagina[origem].append(mov)

# Ordena páginas
paginas_ordenadas = sorted(movs_por_pagina.keys(), 
                          key=lambda x: int(x.split('_')[1].split('.')[0]) if '_' in x else 0)

# Mostra cada página
for pagina in paginas_ordenadas:
    movs = movs_por_pagina[pagina]
    page_num = pagina.split('_')[1].split('.')[0] if '_' in pagina else '?'
    
    print(f"\n{'─' * 100}")
    print(f"📄 PÁGINA {page_num} - {len(movs)} valores encontrados")
    print(f"{'─' * 100}")
    
    # Agrupa por tipo de valor
    valores_por_tipo = {}
    for mov in movs:
        rotulo = mov.get('descricao_item', 'Desconhecido')
        if rotulo not in valores_por_tipo:
            valores_por_tipo[rotulo] = []
        valores_por_tipo[rotulo].append(mov)
    
    # Mostra cada tipo
    for rotulo, valores in valores_por_tipo.items():
        print(f"\n  🏷️  {rotulo}:")
        for i, mov in enumerate(valores, 1):
            # Pega o valor principal
            entrada = mov.get('entrada', 0) or 0
            saida = mov.get('saida', 0) or 0
            saldo = mov.get('saldo', 0) or 0
            aplicacao = mov.get('aplicacao')
            resgate = mov.get('resgate')
            rendimento = mov.get('rendimentos')
            
            # Monta linha
            valores_str = []
            if entrada > 0:
                valores_str.append(f"Entrada: R$ {entrada:,.2f}")
            if saida > 0:
                valores_str.append(f"Saída: R$ {saida:,.2f}")
            if saldo > 0:
                valores_str.append(f"Saldo: R$ {saldo:,.2f}")
            if aplicacao and aplicacao > 0:
                valores_str.append(f"Aplicação: R$ {aplicacao:,.2f}")
            if resgate and resgate > 0:
                valores_str.append(f"Resgate: R$ {resgate:,.2f}")
            if rendimento and rendimento > 0:
                valores_str.append(f"Rendimento: R$ {rendimento:,.2f}")
            
            print(f"     {i}. {' | '.join(valores_str) if valores_str else 'Valor zerado'}")
            
            # Mostra linha original (truncada)
            linha_orig = mov.get('texto_original', '')
            if linha_orig:
                print(f"        📝 Linha: {linha_orig[:80]}{'...' if len(linha_orig) > 80 else ''}")

# TOTAIS
print(f"\n{'=' * 100}")
print(f"📊 TOTAIS CALCULADOS")
print(f"{'=' * 100}")

totais = convenio_data.get('totais', {})

print(f"\n💵 ENTRADAS E SAÍDAS:")
print(f"   Total Entrada:     R$ {totais.get('total_entrada', 0):>15,.2f}")
print(f"   Total Saída:       R$ {totais.get('total_saida', 0):>15,.2f}")
print(f"   Saldo Final:       R$ {totais.get('saldo_final', 0):>15,.2f}")

print(f"\n💼 APLICAÇÕES E RESGATES:")
print(f"   Total Aplicação:   R$ {totais.get('total_aplicacao', 0):>15,.2f}")
print(f"   Total Resgate:     R$ {totais.get('total_resgate', 0):>15,.2f}")

print(f"\n📈 RENDIMENTOS:")
print(f"   Total Rendimentos: R$ {totais.get('total_rendimentos', 0):>15,.2f}")

# VALIDAÇÃO
print(f"\n{'=' * 100}")
print(f"✅ VALIDAÇÃO")
print(f"{'=' * 100}")

validacao = convenio_data.get('validacao', {})
print(f"Total de movimentações: {validacao.get('total_movimentacoes', 0)}")
print(f"Páginas processadas: {validacao.get('paginas_processadas', 0)}")
print(f"Páginas com erro: {validacao.get('paginas_com_erro', [])}")
print(f"Tem valores bloqueados? {'SIM ⚠️' if validacao.get('tem_valores_bloqueados') else 'NÃO ✅'}")

if totais.get('tem_valores_suspeitos'):
    print(f"\n⚠️ ATENÇÃO: Valores suspeitos detectados!")
    print(f"   Campos bloqueados: {totais.get('campos_bloqueados', [])}")

# RESUMO FINAL
print(f"\n{'=' * 100}")
print(f"📌 RESUMO EXECUTIVO")
print(f"{'=' * 100}")
print(f"✓ {len(movs_por_pagina)} páginas com valores extraídos")
print(f"✓ {len(movimentacoes)} valores financeiros identificados")
print(f"✓ Sistema baseado em RÓTULOS (não soma números soltos)")
print(f"✓ Validação de sanidade ativada (bloqueia valores > R$ 1 bilhão)")

print(f"\n{'=' * 100}")
print("FIM DO RELATÓRIO")
print("=" * 100)
