# 🚀 Como Configurar Google Vision API (GRATUITO)

## ✅ BENEFÍCIOS:
- **Precisão 10x maior** que Tesseract
- **Gratuito** até 1.000 páginas/mês
- **Especializado** em documentos financeiros
- **Lê números corretamente**

---

## 📝 PASSO 1: Criar conta Google Cloud (5 minutos)

1. Acesse: https://console.cloud.google.com/
2. Faça login com sua conta Google
3. **GRATUITO!** Não precisa de cartão de crédito para começar

---

## 📝 PASSO 2: Criar novo projeto (1 minuto)

1. No topo da página, clique em **"Selecionar um projeto"**
2. Clique em **"NOVO PROJETO"**
3. Nome do projeto: `convenio-ocr` (ou qualquer nome)
4. Clique em **"CRIAR"**

---

## 📝 PASSO 3: Ativar Google Vision API (1 minuto)

1. No menu lateral, vá em **"APIs e serviços" > "Biblioteca"**
2. Pesquise: `Vision API`
3. Clique em **"Cloud Vision API"**
4. Clique em **"ATIVAR"**

---

## 📝 PASSO 4: Criar credenciais (2 minutos)

1. No menu lateral, vá em **"APIs e serviços" > "Credenciais"**
2. Clique em **"+ CRIAR CREDENCIAIS"** no topo
3. Escolha **"Conta de serviço"**
4. Preencha:
   - **Nome da conta de serviço:** `ocr-service`
   - **ID da conta de serviço:** (gerado automaticamente)
   - **Descrição:** `Serviço de OCR para convênios`
5. Clique em **"CRIAR E CONTINUAR"**
6. Na parte de **"Conceder acesso"**, clique em **"CONTINUAR"** (não precisa selecionar função)
7. Clique em **"CONCLUIR"**

---

## 📝 PASSO 5: Baixar arquivo JSON (1 minuto)

1. Na lista de **Contas de serviço**, clique na conta que você criou (`ocr-service@...`)
2. Vá na aba **"CHAVES"**
3. Clique em **"ADICIONAR CHAVE" > "Criar nova chave"**
4. Escolha **"JSON"**
5. Clique em **"CRIAR"**
6. Um arquivo `.json` será baixado automaticamente
7. **SALVE ESTE ARQUIVO!** Ele contém suas credenciais

---

## 📝 PASSO 6: Configurar no sistema (30 segundos)

1. **Crie a pasta de credenciais:**
   ```
   C:\Users\teste\Desktop\convenio-novo\backend\credentials\
   ```

2. **Mova o arquivo JSON baixado** para dentro dessa pasta

3. **Renomeie o arquivo** para:
   ```
   google-vision-credentials.json
   ```

4. **Caminho final deve ser:**
   ```
   C:\Users\teste\Desktop\convenio-novo\backend\credentials\google-vision-credentials.json
   ```

---

## ✅ PRONTO!

O sistema vai detectar automaticamente as credenciais e usar Google Vision API!

---

## 🔒 SEGURANÇA:

⚠️ **NUNCA compartilhe o arquivo JSON!** Ele dá acesso ao seu projeto Google Cloud.

O arquivo está configurado para ser ignorado pelo Git (.gitignore).

---

## 💰 LIMITES GRATUITOS:

- **1.000 páginas/mês** GRÁTIS
- Depois disso: ~$1.50 por 1.000 páginas
- Mais que suficiente para uso normal!

---

## ❓ PROBLEMAS?

Se tiver erro, me avise e eu ajudo a resolver!
