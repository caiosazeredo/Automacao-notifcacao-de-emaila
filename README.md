# 📧➡️📱 Gmail to Telegram Forwarder

Substituto **gratuito e open-source** ao BeepMate! Este script Python monitora seu Gmail e encaminha emails automaticamente para o Telegram, incluindo anexos.

## 🚀 Funcionalidades

- ✅ **Monitoramento automático** do Gmail
- ✅ **Envio para Telegram** com anexos
- ✅ **Filtros personalizáveis** (remetente, assunto, palavras-chave)
- ✅ **Formatação rica** das mensagens
- ✅ **Logs detalhados** para debugging
- ✅ **Configuração flexível** via JSON
- ✅ **Totalmente gratuito** e sem limitações

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Conta Google
- Bot do Telegram

## 🛠️ Instalação

### 1. Clone/Baixe os arquivos

```bash
# Baixe os 3 arquivos:
# - gmail_telegram_forwarder.py
# - requirements.txt  
# - README.md
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

## 🔧 Configuração

### Passo 1: Configure o Gmail API

1. **Acesse o Google Cloud Console:**
   - Vá para https://console.cloud.google.com/
   - Crie um novo projeto ou selecione um existente

2. **Ative a Gmail API:**
   - Vá para "APIs & Services" > "Library"
   - Procure por "Gmail API" e clique em "ENABLE"

3. **Crie credenciais OAuth2:**
   - Vá para "APIs & Services" > "Credentials"
   - Clique em "CREATE CREDENTIALS" > "OAuth client ID"
   - Escolha "Desktop application"
   - Baixe o arquivo JSON e renomeie para `credentials.json`
   - Coloque na mesma pasta do script

### Passo 2: Crie um Bot do Telegram

1. **Abra o Telegram** e procure por `@BotFather`

2. **Crie um novo bot:**
   ```
   /newbot
   ```
   - Escolha um nome para seu bot
   - Escolha um username (deve terminar com 'bot')
   - **Salve o token** que aparecerá!

3. **Obtenha seu Chat ID:**
   - Envie `/start` para seu bot
   - Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
   - Procure por `"chat":{"id":NUMERO}` 
   - **Salve esse número** (seu Chat ID)

### Passo 3: Execute pela primeira vez

```bash
python gmail_telegram_forwarder.py
```

O script criará um arquivo `config.json` automaticamente.

### Passo 4: Configure o config.json

Abra o arquivo `config.json` e configure:

```json
{
    "telegram": {
        "bot_token": "1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "chat_id": "123456789"
    },
    "gmail": {
        "credentials_file": "credentials.json",
        "token_file": "token.pickle"
    },
    "filters": {
        "from_addresses": ["importante@empresa.com", "chefe@trabalho.com"],
        "subject_keywords": ["urgente", "importante"],
        "body_keywords": [],
        "exclude_keywords": ["noreply", "no-reply", "newsletter"],
        "max_age_hours": 24
    },
    "settings": {
        "check_interval_seconds": 300,
        "include_attachments": true,
        "max_message_length": 4000,
        "send_full_email": true
    }
}
```

### Passo 5: Execute novamente

```bash
python gmail_telegram_forwarder.py
```

Na primeira execução:
- Uma janela do navegador abrirá
- Faça login na sua conta Google
- Autorize o acesso ao Gmail
- O arquivo `token.pickle` será criado automaticamente

## ⚙️ Configurações Avançadas

### Filtros Disponíveis

```json
"filters": {
    "from_addresses": ["email1@exemplo.com"],     // Apenas destes remetentes
    "subject_keywords": ["urgente", "importante"], // Assunto deve conter
    "body_keywords": ["reunião", "projeto"],      // Corpo deve conter  
    "exclude_keywords": ["spam", "newsletter"],   // Excluir se contiver
    "max_age_hours": 24                          // Apenas emails recentes
}
```

### Configurações do Sistema

```json
"settings": {
    "check_interval_seconds": 300,    // Verificar a cada 5 minutos
    "include_attachments": true,      // Enviar anexos
    "max_message_length": 4000,       // Limite de caracteres
    "send_full_email": true          // Enviar email completo
}
```

## 🔄 Executando Continuamente

### No Windows (usando Task Scheduler):

1. Abra "Task Scheduler"
2. Crie nova tarefa
3. Configure para executar: `python C:\caminho\para\gmail_telegram_forwarder.py`
4. Defina para iniciar com o Windows

### No Linux/Mac (usando cron):

```bash
# Edite o crontab
crontab -e

# Adicione esta linha para executar na inicialização
@reboot cd /caminho/para/script && python gmail_telegram_forwarder.py
```

### Usando screen/tmux (Linux/Mac):

```bash
# Instale screen
sudo apt-get install screen  # Ubuntu/Debian
brew install screen          # Mac

# Execute em background
screen -S gmail-telegram
python gmail_telegram_forwarder.py

# Pressione Ctrl+A depois D para "detach"
# Para voltar: screen -r gmail-telegram
```

## 📊 Logs e Monitoramento

O script cria logs automáticos:
- **Arquivo:** `gmail_telegram.log`
- **Console:** Mostra atividade em tempo real

Exemplo de log:
```
2024-01-15 10:30:00 - INFO - Gmail API configurada com sucesso!
2024-01-15 10:30:05 - INFO - Verificando novos emails...
2024-01-15 10:30:06 - INFO - Encontrados 2 novos emails
2024-01-15 10:30:08 - INFO - Mensagem enviada para Telegram com sucesso!
```

## 🔧 Solução de Problemas

### Erro: "File not found: credentials.json"
- Baixe o arquivo de credenciais do Google Cloud Console
- Renomeie para `credentials.json`
- Coloque na mesma pasta do script

### Erro: "Invalid bot token"
- Verifique se copiou o token completo do BotFather
- Token deve ter formato: `1234567890:ABC-DEF...`

### Erro: "Chat not found"
- Envie `/start` para seu bot primeiro
- Verifique se o Chat ID está correto
- Chat ID deve ser um número (pode ser negativo)

### Emails não são encaminhados
- Verifique os filtros no `config.json`
- Veja os logs para entender o que está acontecendo
- Teste removendo todos os filtros temporariamente

### Anexos não funcionam
- Anexos maiores que 50MB não podem ser enviados
- Verifique se `include_attachments` está `true`
- Alguns tipos de arquivo podem ser bloqueados pelo Telegram

## 📱 Exemplo de Mensagem no Telegram

```
📧 Novo Email

De: chefe@empresa.com
Assunto: Reunião urgente amanhã
Data: Mon, 15 Jan 2024 14:30:00 +0000

Conteúdo:
Olá! Precisamos nos reunir amanhã às 9h para discutir o projeto. Por favor, confirme sua presença.

📎 Anexos (1):
• apresentacao.pdf (2.3 MB)
```

## 🆚 Comparação com BeepMate

| Funcionalidade | BeepMate | Este Script |
|---------------|----------|-------------|
| **Preço** | $4/mês | Gratuito |
| **WhatsApp** | ✅ | ❌ (Telegram) |
| **Anexos** | ✅ | ✅ |
| **Filtros** | ✅ | ✅ (Mais flexíveis) |
| **Personalização** | ❌ | ✅ (Código aberto) |
| **Logs** | ❌ | ✅ |
| **Auto-hospedado** | ❌ | ✅ |

## 🤝 Contribuindo

Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias  
- Fazer fork e contribuir com código
- Compartilhar configurações úteis

## 📄 Licença

Este projeto é livre para uso pessoal e comercial. Use como quiser!

## ⚠️ Aviso Legal

- Use apenas em contas próprias
- Respeite os termos de uso do Gmail e Telegram
- Este script não armazena seus dados
- Você é responsável pelo uso

---

**💡 Dica:** Este script é uma alternativa gratuita ao BeepMate, mas usa Telegram em vez de WhatsApp. O Telegram é mais flexível para automações e não tem as limitações do WhatsApp!