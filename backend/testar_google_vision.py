"""
Testa Google Vision API
Rode DEPOIS de configurar as credenciais
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
from services.google_vision_ocr import GoogleVisionOCR
import re

print("=" * 100)
print("TESTE GOOGLE VISION API")
print("=" * 100)

# Verifica credenciais
credentials_path = "credentials/google-vision-credentials.json"

if not os.path.exists(credentials_path) and 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
    print("\n❌ ERRO: Credenciais não encontradas!")
    print(f"\n📝 Você precisa:")
    print(f"   1. Seguir o guia: COMO_CONFIGURAR_GOOGLE_VISION.md")
    print(f"   2. Colocar o arquivo JSON em: {credentials_path}")
    print(f"\nOu configure a variável de ambiente GOOGLE_APPLICATION_CREDENTIALS")
    sys.exit(1)

print(f"\n✅ Credenciais encontradas!")

# Caminho do PDF
pdf_path = input("\nDigite o caminho do PDF: ").strip().strip('"').strip("'")

if not os.path.exists(pdf_path):
    print(f"\n❌ Arquivo não encontrado: {pdf_path}")
    sys.exit(1)

print(f"\n📄 PDF: {pdf_path}")

try:
    # Inicializa Google Vision
    print("\n⏳ Inicializando Google Vision API...")
    ocr = GoogleVisionOCR(credentials_path=credentials_path, batch_size=1, dpi=300)
    
    print("✅ Google Vision inicializado!")
    
    # Processa apenas primeira página
    print("\n⏳ Processando primeira página...")
    
    from pdf2image import convert_from_path
    images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
    
    if not images:
        print("❌ Erro ao converter PDF")
        sys.exit(1)
    
    print("✅ Imagem convertida!")
    
    # OCR
    print("\n⏳ Executando OCR com Google Vision...")
    texto = ocr.extract_text_from_image(images[0])
    
    print("\n" + "=" * 100)
    print("RESULTADO")
    print("=" * 100)
    
    print(f"\n📄 TEXTO EXTRAÍDO ({len(texto)} caracteres):")
    print("-" * 100)
    print(texto[:800])
    print("-" * 100)
    
    # Procura valores
    padrao_valor = r'\d+[\.,]\d{3}[\.,]\d{2}|\d+[\.,]\d{2}'
    valores = re.findall(padrao_valor, texto)
    
    print(f"\n💰 VALORES ENCONTRADOS: {len(valores)}")
    for i, v in enumerate(valores[:20], 1):
        print(f"  {i}. {v}")
    
    # Procura rótulos
    rotulos = ['SALDO ANTERIOR', 'SALDO ATUAL', 'APLICAÇÃO', 'RESGATE', 
               'RENDIMENTO', 'ENTRADA', 'SAÍDA', 'TARIFA']
    rotulos_encontrados = []
    
    for rotulo in rotulos:
        if rotulo in texto.upper():
            rotulos_encontrados.append(rotulo)
    
    print(f"\n🏷️ RÓTULOS ENCONTRADOS: {len(rotulos_encontrados)}")
    for r in rotulos_encontrados:
        print(f"  ✅ {r}")
    
    # Pontuação
    pontos = len(valores) + len(rotulos_encontrados)
    
    print("\n" + "=" * 100)
    print("AVALIAÇÃO")
    print("=" * 100)
    
    print(f"\n📊 PONTUAÇÃO: {pontos} pontos")
    
    if pontos > 10:
        print("✅ EXCELENTE! Google Vision leu o documento perfeitamente!")
    elif pontos > 5:
        print("✅ BOM! Google Vision funciona bem com este documento.")
    elif pontos > 0:
        print("⚠️ MÉDIO. Encontrou alguns dados mas não todos.")
    else:
        print("❌ RUIM. Não encontrou dados suficientes.")
    
    print("\n" + "=" * 100)
    
    if pontos > 5:
        print("🎉 SISTEMA PRONTO PARA USO COM GOOGLE VISION!")
        print("\n📝 PRÓXIMOS PASSOS:")
        print("   1. Reinicie o backend")
        print("   2. Faça upload de PDF pelo navegador")
        print("   3. Os valores serão extraídos CORRETAMENTE!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n💡 POSSÍVEIS SOLUÇÕES:")
    print("   1. Verifique se as credenciais estão corretas")
    print("   2. Verifique se a Vision API está ativada no Google Cloud")
    print("   3. Veja o guia: COMO_CONFIGURAR_GOOGLE_VISION.md")
