"""
Testa o OCR DIRETAMENTE para ver o que está sendo capturado
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from services.ocr_service import OCRService
from PyPDF2 import PdfReader

# Caminho do PDF
pdf_path = input("Digite o caminho do PDF (ou pressione Enter para usar o último): ").strip()

# Remove aspas se existirem (Windows adiciona quando você copia o caminho)
if pdf_path:
    pdf_path = pdf_path.strip('"').strip("'")

if not pdf_path:
    # Pega o último PDF da pasta uploads
    import os
    from pathlib import Path
    uploads = Path("storage/uploads")
    if uploads.exists():
        pdfs = sorted(uploads.glob("*.pdf"), key=os.path.getmtime, reverse=True)
        if pdfs:
            pdf_path = str(pdfs[0])
            print(f"✓ Usando: {pdf_path}")
        else:
            print("❌ Nenhum PDF encontrado em storage/uploads")
            sys.exit(1)
    else:
        print("❌ Pasta storage/uploads não existe")
        sys.exit(1)

print("\n" + "=" * 100)
print("TESTE 1: EXTRAÇÃO DE TEXTO NATIVO (PyPDF2)")
print("=" * 100)

try:
    reader = PdfReader(pdf_path)
    print(f"Total de páginas: {len(reader.pages)}")
    
    # Testa primeira página
    page1 = reader.pages[0]
    texto_nativo = page1.extract_text()
    
    print("\n📄 TEXTO NATIVO DA PÁGINA 1:")
    print("-" * 100)
    print(texto_nativo[:500])
    print("-" * 100)
    
    if len(texto_nativo.strip()) > 100:
        print("✅ PDF tem TEXTO NATIVO! Podemos extrair SEM OCR!")
    else:
        print("⚠️ PDF tem pouco ou nenhum texto nativo. É um SCAN/IMAGEM.")
        
except Exception as e:
    print(f"❌ Erro ao extrair texto nativo: {e}")

print("\n" + "=" * 100)
print("TESTE 2: EXTRAÇÃO COM OCR (Tesseract)")
print("=" * 100)

try:
    ocr_service = OCRService(dpi=300, batch_size=1)
    
    print("Processando primeira página com OCR...")
    results = list(ocr_service.process_pdf_in_batches(pdf_path))
    
    if results and len(results[0]) > 0:
        texto_ocr = results[0][0].get('text', '')
        
        print("\n📄 TEXTO OCR DA PÁGINA 1:")
        print("-" * 100)
        print(texto_ocr[:500])
        print("-" * 100)
        
        # Procura por valores específicos
        print("\n🔍 PROCURANDO VALORES FINANCEIROS NO TEXTO OCR:")
        print("-" * 100)
        
        import re
        # Padrão de valores brasileiros
        padrao_valor = r'\d+[\.,]\d{3}[\.,]\d{2}|\d+[\.,]\d{2}'
        valores = re.findall(padrao_valor, texto_ocr)
        
        print(f"Valores encontrados: {len(valores)}")
        for i, v in enumerate(valores[:20], 1):
            print(f"  {i}. {v}")
        
        # Procura por rótulos
        print("\n🏷️ PROCURANDO RÓTULOS:")
        print("-" * 100)
        rotulos = ['SALDO ANTERIOR', 'SALDO ATUAL', 'APLICAÇÃO', 'RESGATE', 
                   'RENDIMENTO', 'ENTRADA', 'SAÍDA']
        for rotulo in rotulos:
            if rotulo in texto_ocr.upper():
                print(f"  ✅ {rotulo} - ENCONTRADO")
                # Mostra contexto
                pos = texto_ocr.upper().find(rotulo)
                contexto = texto_ocr[max(0, pos-20):pos+80]
                print(f"     Contexto: {contexto}")
            else:
                print(f"  ❌ {rotulo} - NÃO ENCONTRADO")
    else:
        print("❌ OCR não retornou resultados")
        
except Exception as e:
    print(f"❌ Erro no OCR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 100)
print("DIAGNÓSTICO")
print("=" * 100)

print("""
Se o PDF tem TEXTO NATIVO:
  → Devemos usar PyPDF2 para extrair texto (mais rápido e preciso)
  
Se o PDF é SCAN/IMAGEM:
  → Precisamos melhorar o OCR (ajustar DPI, pré-processamento)
  
Se o OCR não encontra os rótulos:
  → O pré-processamento da imagem está ruim
  → Devemos ajustar contrast, sharpen, threshold
""")
