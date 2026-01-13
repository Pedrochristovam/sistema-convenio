# Backend - Processamento de Convênios Bancários

API FastAPI para processar PDFs de convênios bancários usando OCR (Tesseract) e extrair dados estruturados.

## 📋 Pré-requisitos

- Python 3.11+
- Tesseract OCR instalado no sistema
- Poppler (para pdf2image)

### Instalação do Tesseract

**Windows:**
1. Baixe o instalador em: https://github.com/UB-Mannheim/tesseract/wiki
2. Instale e adicione ao PATH
3. Baixe o pacote de idioma português (por.traineddata)

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-por
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

### Instalação do Poppler

**Windows:**
1. Baixe em: https://github.com/oschwartz10612/poppler-windows/releases
2. Extraia e adicione ao PATH

**Linux:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

## 🚀 Instalação

1. Navegue até a pasta backend:
```bash
cd backend
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## ▶️ Execução

Inicie o servidor FastAPI:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

O servidor estará disponível em: `http://localhost:8000`

Documentação interativa (Swagger): `http://localhost:8000/docs`

## 📡 Endpoints

### GET /health
Verifica se a API está funcionando.

**Resposta:**
```json
{
  "status": "healthy",
  "message": "API está funcionando corretamente"
}
```

### POST /upload
Faz upload de um PDF e processa o documento.

**Request:**
- Content-Type: `multipart/form-data`
- Body: arquivo PDF

**Resposta:**
```json
{
  "id": "uuid-do-processamento",
  "status": "completed",
  "total_pages": 10,
  "relevant_pages": 3,
  "records_found": 5,
  "items": [
    {
      "banco": "BANCO DO BRASIL",
      "agencia": "1234",
      "conta": "12345-6",
      "tipo_conta": "CORRENTE",
      "cpf_cnpj": "123.456.789-00",
      "valor": 1000.50
    }
  ]
}
```

### GET /result/{process_id}
Retorna o resultado de um processamento específico.

### GET /export/{process_id}
Exporta os dados extraídos para Excel (.xlsx).

## 🔧 Estrutura do Projeto

```
backend/
├── main.py                 # Aplicação FastAPI principal
├── requirements.txt        # Dependências Python
├── README.md              # Este arquivo
└── services/
    ├── __init__.py
    ├── ocr_service.py     # Serviço de OCR com Tesseract
    ├── page_filter.py     # Filtro de páginas relevantes
    ├── extractor.py       # Extrator de dados bancários
    └── excel_export.py    # Exportador para Excel
```

## 🎯 Fluxo de Processamento

1. **Upload**: PDF é recebido e salvo temporariamente
2. **OCR**: PDF é convertido em imagens e processado com Tesseract
3. **Filtro**: Apenas páginas com informações relevantes são mantidas
4. **Extração**: Dados bancários são extraídos usando regex
5. **Resposta**: Dados estruturados são retornados em JSON

## ⚙️ Configurações

O Tesseract está configurado para português (`-l por`). Para usar outros idiomas, edite `ocr_service.py`.

## 🐛 Troubleshooting

**Erro: "TesseractNotFoundError"**
- Verifique se o Tesseract está instalado e no PATH
- No Windows, pode ser necessário especificar o caminho em `pytesseract.pytesseract.tesseract_cmd`

**Erro: "pdf2image.exceptions.PDFInfoNotInstalledError"**
- Instale o Poppler e adicione ao PATH

**Baixa qualidade do OCR**
- Aumente o DPI em `ocr_service.py` (padrão: 300)
- Verifique a qualidade do PDF original

## 📝 Notas

- Arquivos temporários são automaticamente removidos após processamento
- Resultados são armazenados em memória (em produção, usar banco de dados)
- CORS está configurado para permitir todas as origens (ajustar em produção)
