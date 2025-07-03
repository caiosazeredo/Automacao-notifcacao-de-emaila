#!/usr/bin/env python3
"""
Script de configuração rápida para Gmail to Telegram Forwarder
Executa verificações e guia o usuário através do setup inicial
"""

import os
import json
import sys
import requests
from pathlib import Path

def print_header():
    """Imprime cabeçalho do script"""
    print("="*60)
    print("📧➡️📱 GMAIL TO TELEGRAM FORWARDER")
    print("        Setup e Verificação Rápida")
    print("="*60)
    print()

def check_python_version():
    """Verifica versão do Python"""
    print("🐍 Verificando versão do Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ é necessário!")
        print(f"   Versão atual: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} OK")
    return True

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("\n📦 Verificando dependências...")
    
    # Mapeamento correto: nome do pacote pip -> nome do módulo Python
    package_modules = {
        'google-auth': 'google.auth',
        'google-auth-oauthlib': 'google_auth_oauthlib', 
        'google-api-python-client': 'googleapiclient',
        'requests': 'requests'
    }
    
    missing_packages = []
    
    for package_name, module_name in package_modules.items():
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name}")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n💡 Para instalar dependências faltantes:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_credentials():
    """Verifica se o arquivo de credenciais existe"""
    print("\n🔐 Verificando credenciais...")
    
    if not os.path.exists('credentials.json'):
        print("❌ Arquivo credentials.json não encontrado!")
        print("\n📋 Como obter:")
        print("1. Acesse: https://console.cloud.google.com/")
        print("2. Crie/selecione um projeto")
        print("3. Ative a Gmail API")
        print("4. Crie credenciais OAuth2 (Desktop Application)")
        print("5. Baixe e renomeie para 'credentials.json'")
        return False
    
    print("✅ credentials.json encontrado")
    return True

def check_config():
    """Verifica e cria configuração"""
    print("\n⚙️ Verificando configuração...")
    
    if not os.path.exists('config.json'):
        print("❌ Arquivo config.json não encontrado!")
        
        # Cria configuração básica
        config = {
            "telegram": {
                "bot_token": "SEU_BOT_TOKEN_AQUI",
                "chat_id": "SEU_CHAT_ID_AQUI"
            },
            "gmail": {
                "credentials_file": "credentials.json",
                "token_file": "token.pickle"
            },
            "filters": {
                "from_addresses": [],
                "subject_keywords": [],
                "body_keywords": [],
                "exclude_keywords": ["noreply", "no-reply"],
                "max_age_hours": 24
            },
            "settings": {
                "check_interval_seconds": 300,
                "include_attachments": True,
                "max_message_length": 4000,
                "send_full_email": True
            }
        }
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print("✅ config.json criado!")
        print("\n📋 Próximos passos:")
        print("1. Configure seu bot do Telegram:")
        print("   - Abra Telegram e procure @BotFather")
        print("   - Digite /newbot e siga instruções")
        print("   - Salve o token do bot")
        print("2. Obtenha seu Chat ID:")
        print("   - Envie /start para seu bot")
        print("   - Acesse: https://api.telegram.org/bot<TOKEN>/getUpdates")
        print("   - Procure por 'chat':{'id': NUMERO}")
        print("3. Edite config.json com suas credenciais")
        return False
    
    # Verifica se config está preenchido
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if (config['telegram']['bot_token'] == 'SEU_BOT_TOKEN_AQUI' or 
        config['telegram']['chat_id'] == 'SEU_CHAT_ID_AQUI'):
        print("❌ config.json não foi configurado!")
        print("💡 Edite o arquivo e configure bot_token e chat_id")
        return False
    
    print("✅ config.json configurado")
    return True

def test_telegram_connection():
    """Testa conexão com Telegram"""
    print("\n📱 Testando conexão com Telegram...")
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        bot_token = config['telegram']['bot_token']
        chat_id = config['telegram']['chat_id']
        
        # Testa bot
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print("❌ Token do bot inválido!")
            return False
        
        bot_info = response.json()
        print(f"✅ Bot conectado: @{bot_info['result']['username']}")
        
        # Testa envio de mensagem
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': '🧪 Teste de conexão - Gmail to Telegram Forwarder configurado com sucesso!'
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Mensagem de teste enviada!")
            return True
        else:
            print("❌ Erro ao enviar mensagem!")
            print(f"   Código: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar Telegram: {e}")
        return False

def show_next_steps():
    """Mostra próximos passos após configuração"""
    print("\n🚀 CONFIGURAÇÃO CONCLUÍDA!")
    print("\n📋 Próximos passos:")
    print("1. Execute o forwarder:")
    print("   python gmail_telegram_forwarder.py")
    print("\n2. Na primeira execução:")
    print("   - Uma janela do navegador abrirá")
    print("   - Faça login na sua conta Google")
    print("   - Autorize o acesso ao Gmail")
    print("\n3. Personalize os filtros no config.json:")
    print("   - from_addresses: emails específicos")
    print("   - subject_keywords: palavras no assunto")
    print("   - exclude_keywords: palavras para ignorar")
    print("\n4. Para executar em background:")
    print("   - Windows: Task Scheduler")
    print("   - Linux/Mac: cron ou screen")
    print("\n💡 Logs ficam em: gmail_telegram.log")
    print("📖 Manual completo: README.md")

def main():
    """Função principal do setup"""
    print_header()
    
    checks = [
        ("Python 3.7+", check_python_version),
        ("Dependências", check_dependencies), 
        ("Credenciais", check_credentials),
        ("Configuração", check_config),
        ("Telegram", test_telegram_connection)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
            break
    
    print("\n" + "="*60)
    
    if all_passed:
        show_next_steps()
    else:
        print("❌ CONFIGURAÇÃO INCOMPLETA")
        print("\n💡 Resolva os problemas acima e execute novamente:")
        print("   python setup.py")
    
    print("="*60)

if __name__ == "__main__":
    main()