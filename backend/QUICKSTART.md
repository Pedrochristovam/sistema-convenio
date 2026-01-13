# QUICKSTART - Backend Refatorado

## 🚀 Instalação

```bash
cd backend
pip install -r requirements.txt
```

## ▶️ Rodar

```bash
python main.py
```

Ou com uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 Testar

### 1. Upload de PDF
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@convenio.pdf"
```

Resposta:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Upload realizado..."
}
```

### 2. Verificar Status
```bash
curl http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000
```

Resposta:
```json
{
  "job_id": "550e8400...",
  "status": "processing",
  "progress": 50.0,
  "message": "Processando PDF..."
}
```

### 3. Pegar Resultado
```bash
curl http://localhost:8000/result/550e8400-e29b-41d4-a716-446655440000
```

### 4. Exportar Excel
```bash
curl http://localhost:8000/export/550e8400-e29b-41d4-a716-446655440000 \
  -o resultado.xlsx
```

## 🐍 Exemplo Python

```python
import requests
import time

# 1. Upload
with open('convenio.pdf', 'rb') as f:
    resp = requests.post('http://localhost:8000/upload', files={'file': f})
    job_id = resp.json()['job_id']
    print(f"Job ID: {job_id}")

# 2. Polling (aguarda conclusão)
while True:
    status = requests.get(f'http://localhost:8000/status/{job_id}').json()
    
    print(f"{status['status']}: {status['progress']}% - {status['message']}")
    
    if status['status'] in ['done', 'error']:
        break
    
    time.sleep(5)  # Aguarda 5 segundos

# 3. Resultado
if status['status'] == 'done':
    result = requests.get(f'http://localhost:8000/result/{job_id}').json()
    print(f"\nRegistros encontrados: {result['records_found']}")
    for item in result['items']:
        print(f"  - {item['banco']}: {item['agencia']}/{item['conta']}")
```

## ⚙️ Configuração

### Variáveis de Ambiente (opcional)

```bash
# CORS (produção)
export CORS_ORIGINS="http://localhost:3000,https://meuapp.com"

# Tamanho máximo
export MAX_FILE_SIZE=104857600  # 100MB
```

### Ajustar Workers

No `main.py`:
```python
executor = ProcessPoolExecutor(max_workers=4)  # Aumentar para 4 workers
```

### Ajustar Batch Size

No `main.py` (função `process_pdf_worker`):
```python
ocr_service = OCRService(dpi=200, batch_size=20)  # 20 páginas por batch
```

## 🔍 Troubleshooting

### Erro: "Tesseract not found"
```bash
# Windows: Instale e adicione ao PATH
# https://github.com/UB-Mannheim/tesseract/wiki
```

### Erro: "Poppler not found"
```bash
# Windows: Instale Poppler e adicione ao PATH
# https://github.com/oschwartz10612/poppler-windows/releases
```

### RAM estourando
- Reduza `batch_size` (padrão: 10)
- Reduza `dpi` (padrão: 200)
- Reduza `max_workers` (padrão: 2)

### API travando
- Verifique logs: ProcessPoolExecutor deve estar ativo
- Confirme que `/status` retorna enquanto `/upload` processa
- Se travar, worker pode ter crashado (veja logs)

## 📊 Monitoramento

### Logs
```bash
# Todos os logs vão para stdout com timestamps
2024-01-13 10:00:00 - __main__ - INFO - [job-123] Worker iniciado
2024-01-13 10:00:05 - __main__ - INFO - [job-123] Batch processado, total: 10 páginas
```

### Health Check
```bash
curl http://localhost:8000/health
```

## 🎯 Diferenças da Versão Anterior

| Antes | Depois |
|-------|--------|
| `/upload` retorna resultado | `/upload` retorna `job_id` |
| Bloqueia até fim | Retorna em <1s |
| Sem progresso | GET `/status/{job_id}` |
| Sem limite de RAM | Batches controlados |
| `print()` | `logger` |

## 🔜 Próximas Melhorias

- [ ] Progresso em tempo real (Queue)
- [ ] Persistência (SQLite)
- [ ] Cancelamento de jobs
- [ ] Retry automático
- [ ] Métricas (Prometheus)
