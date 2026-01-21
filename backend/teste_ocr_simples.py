"""
Teste SIMPLES de OCR - SEM pré-processamento
Para verificar se o Tesseract funciona ANTES de otimizar
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pdf2image import convert_from_path
import pytesseract
import re

# Caminho do PDF
pdf_path = input("Digite o caminho do PDF: ").strip().strip('"').strip("'")

print("\n" + "=" * 100)
print("TESTE SIMPLES - OCR DIRETO (sem pré-processamento)")
print("=" * 100)

print("\n⏳ Convertendo primeira página em imagem (DPI 300)...")

try:
    # Converte apenas primeira página
    images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
    
    if not images:
        print("❌ Erro: Não conseguiu converter PDF")
        sys.exit(1)
    
    print("✅ Imagem convertida!")
    
    # Testa 3 configurações diferentes de Tesseract
    configs = [
        ('PSM 6 (Bloco de texto)', '--oem 3 --psm 6 -l por'),
        ('PSM 4 (Coluna única)', '--oem 3 --psm 4 -l por'),
        ('PSM 3 (Automático)', '--oem 3 --psm 3 -l por'),
    ]
    
    for nome, config in configs:
        print("\n" + "-" * 100)
        print(f"🔍 TESTANDO: {nome}")
        print("-" * 100)
        
        try:
            texto = pytesseract.image_to_string(images[0], config=config)
            
            print(f"\n📄 TEXTO EXTRAÍDO ({len(texto)} caracteres):")
            print(texto[:500])
            
            # Procura valores
            padrao_valor = r'\d+[\.,]\d{3}[\.,]\d{2}|\d+[\.,]\d{2}'
            valores = re.findall(padrao_valor, texto)
            
            print(f"\n💰 VALORES ENCONTRADOS: {len(valores)}")
            for i, v in enumerate(valores[:10], 1):
                print(f"  {i}. {v}")
            
            # Procura rótulos chave
            rotulos_encontrados = []
            rotulos = ['SALDO', 'ENTRADA', 'SAÍDA', 'APLICAÇÃO', 'RESGATE', 'RENDIMENTO']
            for rotulo in rotulos:
                if rotulo in texto.upper():
                    rotulos_encontrados.append(rotulo)
            
            print(f"\n🏷️ RÓTULOS ENCONTRADOS: {len(rotulos_encontrados)}")
            for r in rotulos_encontrados:
                print(f"  ✅ {r}")
            
            # Pontuação
            pontos = len(valores) + len(rotulos_encontrados)
            print(f"\n📊 PONTUAÇÃO: {pontos} pontos")
            
            if pontos > 5:
                print("✅ BOA configuração!")
            elif pontos > 0:
                print("⚠️ Configuração média")
            else:
                print("❌ Configuração ruim")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 100)
    print("CONCLUSÃO")
    print("=" * 100)
    print("""
Se ALGUMA configuração encontrou valores:
  → Tesseract funciona! Só precisa ajustar configuração
  
Se NENHUMA configuração encontrou valores:
  → Problema com qualidade do scan
  → Precisamos de OCR profissional (Google Vision API)
""")
    
except Exception as e:
    print(f"❌ ERRO GERAL: {e}")
    import traceback
    traceback.print_exc()
