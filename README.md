# ConvênioProc - Sistema de Processamento de Convênios Bancários

Sistema completo para processamento de PDFs de convênios bancários usando OCR (Tesseract), com frontend React e backend Python/FastAPI.

## 📋 Visão Geral

- **Frontend**: React + Vite + Tailwind CSS + Framer Motion
- **Backend**: Python + FastAPI + Tesseract OCR + OpenCV
- **Funcionalidades**:
  - Upload de PDF
  - OCR com pré-processamento de imagem
  - Extração automática de dados bancários
  - Exportação para Excel/CSV
  - Interface moderna e responsiva

## 🚀 Como Rodar o Projeto

### Pré-requisitos

- Node.js 18+ e npm
- Python 3.11+
- Tesseract OCR instalado
- Poppler (para pdf2image)

### 1. Instalar Tesseract e Poppler

#### Windows:
- **Tesseract**: https://github.com/UB-Mannheim/tesseract/wiki
- **Poppler**: https://github.com/oschwartz10612/poppler-windows/releases
- Adicione ambos ao PATH do Windows

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-por poppler-utils
```

#### macOS:
```bash
brew install tesseract tesseract-lang poppler
```

### 2. Rodar o Frontend

```bash
# Instalar dependências
npm install

# Rodar servidor de desenvolvimento
npm run dev
```

O frontend estará disponível em: `http://localhost:5173`

### 3. Rodar o Backend

```bash
# Navegar para pasta backend
cd backend

# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Rodar servidor FastAPI
uvicorn main:app --reload
```

O backend estará disponível em: `http://localhost:8000`
Documentação da API: `http://localhost:8000/docs`

## 📁 Estrutura do Projeto

```
convenio-novo/
├── backend/                    # Backend Python/FastAPI
│   ├── main.py                # API principal
│   ├── requirements.txt       # Dependências Python
│   ├── README.md             # Documentação backend
│   └── services/             # Serviços de processamento
│       ├── ocr_service.py    # OCR com Tesseract
│       ├── page_filter.py    # Filtro de páginas
│       ├── extractor.py      # Extrator de dados
│       └── excel_export.py   # Exportador Excel
│
├── src/                       # Frontend React
│   ├── main.jsx              # Entry point
│   ├── App.jsx               # Componente principal
│   ├── index.css             # Estilos globais
│   ├── hooks/                # React hooks customizados
│   └── lib/                  # Utilitários
│
├── Pages/                     # Páginas da aplicação
│   └── Convenio.jsx          # Página principal
│
├── components/                # Componentes React
│   ├── convenio/             # Componentes específicos
│   │   ├── UploadSection.jsx
│   │   ├── ProcessingSection.jsx
│   │   └── ResultSection.jsx
│   └── UI/                   # Componentes UI reutilizáveis
│
├── index.html                # HTML principal
├── package.json              # Dependências Node.js
├── vite.config.js            # Configuração Vite
├── tailwind.config.js        # Configuração Tailwind
├── jsconfig.json             # Configuração JavaScript
└── README.md                 # Este arquivo
```

## 🎯 Fluxo de Uso

1. **Upload**: Usuário faz upload de PDF com dados de convênio
2. **Processamento**: 
   - PDF é convertido em imagens
   - Imagens são pré-processadas com OpenCV
   - OCR extrai texto com Tesseract
   - Páginas relevantes são filtradas
   - Dados bancários são extraídos
3. **Resultado**: Dados estruturados são exibidos em tabela
4. **Exportação**: Usuário pode exportar para Excel/CSV

## 🔧 Tecnologias

### Frontend
- React 18
- Vite
- Tailwind CSS
- Framer Motion (animações)
- Lucide React (ícones)

### Backend
- FastAPI
- Tesseract OCR
- OpenCV (pré-processamento)
- pdf2image
- openpyxl (Excel)
- Pydantic (validação)

## 📝 API Endpoints

- `GET /health` - Health check
- `POST /upload` - Upload e processa PDF
- `GET /result/{id}` - Retorna resultado
- `GET /export/{id}` - Exporta para Excel

Veja documentação completa em `/backend/README.md`

## 🐛 Troubleshooting

### Frontend não inicia
- Verifique se o Node.js está instalado: `node --version`
- Delete `node_modules` e rode `npm install` novamente

### Backend não inicia
- Verifique se o Python está instalado: `python --version`
- Ative o ambiente virtual
- Instale as dependências novamente

### Erro "TesseractNotFoundError"
- Verifique se o Tesseract está instalado
- No Windows, adicione ao PATH ou configure em `ocr_service.py`

### Erro "PDFInfoNotInstalledError"
- Instale o Poppler e adicione ao PATH

### OCR com baixa qualidade
- Verifique a qualidade do PDF original
- Aumente o DPI em `ocr_service.py` (padrão: 300)

## 📦 Build para Produção

### Frontend
```bash
npm run build
```
Arquivos estarão em `/dist`

### Backend
```bash
# Usar gunicorn para produção
pip install gunicorn
gunicorn main:app --workers 4 --bind 0.0.0.0:8000
```

## 🔒 Segurança

- Em produção, configure CORS adequadamente no backend
- Use variáveis de ambiente para configurações sensíveis
- Implemente autenticação e autorização conforme necessário
- Valide e sanitize todos os uploads de arquivos

## 📄 Licença

Este projeto é fornecido "como está" para fins educacionais e de demonstração.

## 👤 Autor

Desenvolvido com ❤️ para processar convênios bancários de forma automatizada.
