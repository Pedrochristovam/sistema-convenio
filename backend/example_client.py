"""
Exemplo de cliente Python para testar a API refatorada
"""

import requests
import time
from pathlib import Path


def process_pdf(pdf_path: str, api_url: str = "http://localhost:8000"):
    """
    Processa um PDF e aguarda o resultado
    
    Args:
        pdf_path: Caminho do arquivo PDF
        api_url: URL base da API
    """
    print(f"📄 Processando: {pdf_path}")
    print("=" * 60)
    
    # 1. Upload do PDF
    print("\n[1/4] Fazendo upload...")
    with open(pdf_path, 'rb') as f:
        response = requests.post(
            f"{api_url}/upload",
            files={"file": f}
        )
    
    if response.status_code != 200:
        print(f"❌ Erro no upload: {response.json()}")
        return
    
    data = response.json()
    job_id = data["job_id"]
    print(f"✅ Upload concluído")
    print(f"   Job ID: {job_id}")
    print(f"   Status: {data['status']}")
    
    # 2. Polling de status
    print("\n[2/4] Aguardando processamento...")
    start_time = time.time()
    
    while True:
        response = requests.get(f"{api_url}/status/{job_id}")
        status_data = response.json()
        
        status = status_data["status"]
        progress = status_data["progress"]
        message = status_data["message"]
        
        elapsed = time.time() - start_time
        print(f"   {status.upper()}: {progress:.1f}% - {message} ({elapsed:.1f}s)")
        
        # Verifica se terminou
        if status == "done":
            print("✅ Processamento concluído")
            break
        elif status == "error":
            print(f"❌ Erro: {message}")
            return
        
        time.sleep(2)  # Aguarda 2 segundos antes de checar novamente
    
    # 3. Buscar resultado
    print("\n[3/4] Buscando resultado...")
    response = requests.get(f"{api_url}/result/{job_id}")
    
    if response.status_code != 200:
        print(f"❌ Erro ao buscar resultado: {response.json()}")
        return
    
    result = response.json()
    print("✅ Resultado obtido")
    print(f"   Total de páginas: {result['total_pages']}")
    print(f"   Páginas relevantes: {result['relevant_pages']}")
    print(f"   Registros encontrados: {result['records_found']}")
    
    # Mostra registros
    print("\n📊 Dados extraídos:")
    for i, item in enumerate(result['items'], 1):
        print(f"\n   Registro {i}:")
        print(f"      Banco: {item.get('banco', '-')}")
        print(f"      Agência: {item.get('agencia', '-')}")
        print(f"      Conta: {item.get('conta', '-')}")
        print(f"      Tipo: {item.get('tipo_conta', '-')}")
        print(f"      CPF/CNPJ: {item.get('cpf_cnpj', '-')}")
        if item.get('valor'):
            print(f"      Valor: R$ {item['valor']:.2f}")
    
    # 4. Exportar para Excel (opcional)
    export = input("\n[4/4] Exportar para Excel? (s/n): ").strip().lower()
    
    if export == 's':
        print("📥 Exportando...")
        response = requests.get(f"{api_url}/export/{job_id}")
        
        if response.status_code == 200:
            filename = f"convenio_{job_id[:8]}.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ Arquivo salvo: {filename}")
        else:
            print(f"❌ Erro ao exportar: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("✨ Processo concluído!")


def test_concurrent_uploads(pdf_files: list, api_url: str = "http://localhost:8000"):
    """
    Testa upload concorrente de múltiplos PDFs
    
    Args:
        pdf_files: Lista de caminhos de PDFs
        api_url: URL base da API
    """
    print(f"🔄 Testando {len(pdf_files)} uploads simultâneos...")
    print("=" * 60)
    
    job_ids = []
    
    # Upload de todos os arquivos
    print("\n[1/2] Fazendo uploads...")
    for pdf_path in pdf_files:
        with open(pdf_path, 'rb') as f:
            response = requests.post(
                f"{api_url}/upload",
                files={"file": f}
            )
        
        if response.status_code == 200:
            job_id = response.json()["job_id"]
            job_ids.append(job_id)
            print(f"   ✅ {Path(pdf_path).name}: {job_id}")
        else:
            print(f"   ❌ {Path(pdf_path).name}: Erro")
    
    # Monitora todos os jobs
    print(f"\n[2/2] Monitorando {len(job_ids)} jobs...")
    
    completed = set()
    
    while len(completed) < len(job_ids):
        for job_id in job_ids:
            if job_id in completed:
                continue
            
            response = requests.get(f"{api_url}/status/{job_id}")
            status_data = response.json()
            
            if status_data["status"] in ["done", "error"]:
                completed.add(job_id)
                status_emoji = "✅" if status_data["status"] == "done" else "❌"
                print(f"   {status_emoji} {job_id[:8]}: {status_data['message']}")
        
        if len(completed) < len(job_ids):
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print(f"✨ Todos os {len(job_ids)} jobs concluídos!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python example_client.py <caminho_do_pdf>")
        print("  python example_client.py --concurrent <pdf1> <pdf2> <pdf3>")
        sys.exit(1)
    
    if sys.argv[1] == "--concurrent":
        # Teste de concorrência
        pdf_files = sys.argv[2:]
        test_concurrent_uploads(pdf_files)
    else:
        # Processamento único
        pdf_path = sys.argv[1]
        process_pdf(pdf_path)
