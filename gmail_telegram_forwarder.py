import os
import json
import time
import base64
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import pickle
import re

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_telegram.log'),
        logging.StreamHandler()
    ]
)

class GmailTelegramForwarder:
    def check_dependencies(self):
        """Verifica se todas as dependências estão instaladas"""
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
            except ImportError:
                missing_packages.append(package_name)
        
        return len(missing_packages) == 0
    
    def __init__(self, config_file='config.json'):
        """
        Inicializa o forwarder Gmail → Telegram
        
        Args:
            config_file (str): Caminho para arquivo de configuração
        """
        # Verifica dependências primeiro
        if not self.check_dependencies():
            raise ImportError("Dependências não instaladas corretamente!")
            
        self.config = self.load_config(config_file)
        self.gmail_service = None
        self.last_check_time = datetime.now() - timedelta(hours=1)
        
        # Scopes necessários para Gmail API
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        
        self.setup_gmail()
        
    def load_config(self, config_file):
        """Carrega configurações do arquivo JSON"""
        if not os.path.exists(config_file):
            self.create_sample_config(config_file)
            raise FileNotFoundError(f"Arquivo {config_file} criado. Configure suas credenciais!")
            
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_sample_config(self, config_file):
        """Cria arquivo de configuração de exemplo"""
        sample_config = {
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
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=4, ensure_ascii=False)
            
        logging.info(f"Arquivo de configuração criado: {config_file}")
        logging.info("Configure suas credenciais antes de continuar!")
    
    def setup_gmail(self):
        """Configura autenticação Gmail API"""
        creds = None
        token_file = self.config['gmail']['token_file']
        credentials_file = self.config['gmail']['credentials_file']
        
        # Carrega token salvo
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Se não há credenciais válidas, autoriza o usuário
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    raise FileNotFoundError(f"Arquivo {credentials_file} não encontrado!")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Salva credenciais para próxima execução
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        logging.info("Gmail API configurada com sucesso!")
    
    def get_new_emails(self):
        """Busca novos emails desde a última verificação"""
        try:
            # Converte tempo para timestamp
            after_timestamp = int(self.last_check_time.timestamp())
            
            # Constrói query de busca
            query_parts = [f'after:{after_timestamp}']
            
            # Adiciona filtros de remetente
            from_addresses = self.config['filters'].get('from_addresses', [])
            if from_addresses:
                from_query = ' OR '.join([f'from:{addr}' for addr in from_addresses])
                query_parts.append(f'({from_query})')
            
            # Adiciona filtros de assunto
            subject_keywords = self.config['filters'].get('subject_keywords', [])
            if subject_keywords:
                subject_query = ' OR '.join([f'subject:{kw}' for kw in subject_keywords])
                query_parts.append(f'({subject_query})')
            
            query = ' '.join(query_parts) if len(query_parts) > 1 else query_parts[0]
            
            # Busca emails
            results = self.gmail_service.users().messages().list(
                userId='me', q=query).execute()
            
            messages = results.get('messages', [])
            logging.info(f"Encontrados {len(messages)} novos emails")
            
            return messages
            
        except Exception as e:
            logging.error(f"Erro ao buscar emails: {e}")
            return []
    
    def get_email_details(self, message_id):
        """Obtém detalhes completos de um email"""
        try:
            message = self.gmail_service.users().messages().get(
                userId='me', id=message_id, format='full').execute()
            
            headers = message['payload'].get('headers', [])
            
            # Extrai informações do cabeçalho
            email_data = {
                'id': message_id,
                'subject': self.get_header_value(headers, 'Subject'),
                'from': self.get_header_value(headers, 'From'),
                'to': self.get_header_value(headers, 'To'),
                'date': self.get_header_value(headers, 'Date'),
                'body': '',
                'attachments': []
            }
            
            # Extrai corpo do email
            email_data['body'] = self.extract_email_body(message['payload'])
            
            # Extrai anexos se configurado
            if self.config['settings'].get('include_attachments', True):
                email_data['attachments'] = self.extract_attachments(message)
            
            return email_data
            
        except Exception as e:
            logging.error(f"Erro ao obter detalhes do email {message_id}: {e}")
            return None
    
    def get_header_value(self, headers, name):
        """Extrai valor de um cabeçalho específico"""
        for header in headers:
            if header['name'] == name:
                return header['value']
        return ''
    
    def extract_email_body(self, payload):
        """Extrai corpo do email de forma recursiva"""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                body += self.extract_email_body(part)
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data', '')
                if data:
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    # Remove tags HTML básicas
                    body = re.sub('<[^<]+?>', '', html_body)
        
        return body
    
    def extract_attachments(self, message):
        """Extrai informações sobre anexos"""
        attachments = []
        
        def process_parts(parts):
            for part in parts:
                if part.get('filename'):
                    attachment = {
                        'filename': part['filename'],
                        'mimeType': part['mimeType'],
                        'size': part['body'].get('size', 0),
                        'attachmentId': part['body'].get('attachmentId')
                    }
                    attachments.append(attachment)
                
                if 'parts' in part:
                    process_parts(part['parts'])
        
        if 'parts' in message['payload']:
            process_parts(message['payload']['parts'])
        
        return attachments
    
    def should_forward_email(self, email_data):
        """Verifica se o email deve ser encaminhado baseado nos filtros"""
        
        # Verifica palavras-chave de exclusão
        exclude_keywords = self.config['filters'].get('exclude_keywords', [])
        email_text = f"{email_data['subject']} {email_data['body']} {email_data['from']}".lower()
        
        for keyword in exclude_keywords:
            if keyword.lower() in email_text:
                logging.info(f"Email excluído por palavra-chave: {keyword}")
                return False
        
        # Verifica palavras-chave do corpo (se especificadas)
        body_keywords = self.config['filters'].get('body_keywords', [])
        if body_keywords:
            found_keyword = False
            for keyword in body_keywords:
                if keyword.lower() in email_data['body'].lower():
                    found_keyword = True
                    break
            if not found_keyword:
                return False
        
        return True
    
    def escape_markdown(self, text):
        """Escapa caracteres especiais do Markdown"""
        if not text:
            return ""
        
        # Caracteres que precisam ser escapados no Markdown
        special_chars = ['_', '*', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def format_telegram_message(self, email_data):
        """Formata email para envio no Telegram"""
        max_length = self.config['settings'].get('max_message_length', 4000)
        
        # Escapa dados para evitar problemas de formatação
        from_safe = self.escape_markdown(email_data['from'])
        subject_safe = self.escape_markdown(email_data['subject'])
        date_safe = self.escape_markdown(email_data['date'])
        
        # Cabeçalho do email
        message = f"📧 *Novo Email*\n\n"
        message += f"*De:* {from_safe}\n"
        message += f"*Assunto:* {subject_safe}\n"
        message += f"*Data:* {date_safe}\n\n"
        
        # Corpo do email
        if self.config['settings'].get('send_full_email', True):
            body = email_data['body'].strip()
            if len(body) > (max_length - len(message) - 200):
                body = body[:max_length - len(message) - 200] + "..."
            
            # Escapa o corpo do email
            body_safe = self.escape_markdown(body)
            message += f"*Conteúdo:*\n{body_safe}\n\n"
        
        # Anexos
        if email_data['attachments']:
            message += f"📎 *Anexos \\({len(email_data['attachments'])}\\):*\n"
            for att in email_data['attachments']:
                size_mb = att['size'] / (1024 * 1024) if att['size'] > 0 else 0
                filename_safe = self.escape_markdown(att['filename'])
                message += f"• {filename_safe} \\({size_mb:.1f} MB\\)\n"
        
        return message[:max_length]
    
    def send_telegram_message(self, message):
        """Envia mensagem para o Telegram"""
        try:
            bot_token = self.config['telegram']['bot_token']
            chat_id = self.config['telegram']['chat_id']
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'MarkdownV2'
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                logging.info("Mensagem enviada para Telegram com sucesso!")
                return True
            else:
                # Se falhar com MarkdownV2, tenta sem formatação
                logging.warning(f"Erro com Markdown: {response.text}")
                logging.info("Tentando enviar sem formatação...")
                
                # Remove formatação e envia texto simples
                simple_message = message.replace('*', '').replace('_', '').replace('`', '').replace('\\', '')
                
                data_simple = {
                    'chat_id': chat_id,
                    'text': simple_message
                }
                
                response_simple = requests.post(url, data=data_simple, timeout=30)
                
                if response_simple.status_code == 200:
                    logging.info("Mensagem enviada sem formatação com sucesso!")
                    return True
                else:
                    logging.error(f"Erro ao enviar para Telegram: {response_simple.status_code} - {response_simple.text}")
                    return False
                
        except Exception as e:
            logging.error(f"Erro ao enviar mensagem para Telegram: {e}")
            return False
    
    def send_attachment_to_telegram(self, attachment, message_id):
        """Envia anexo para o Telegram (se possível)"""
        try:
            # Baixa anexo do Gmail
            attachment_data = self.gmail_service.users().messages().attachments().get(
                userId='me', messageId=message_id, id=attachment['attachmentId']).execute()
            
            file_data = base64.urlsafe_b64decode(attachment_data['data'])
            
            bot_token = self.config['telegram']['bot_token']
            chat_id = self.config['telegram']['chat_id']
            
            # Decide o tipo de envio baseado no MIME type
            if attachment['mimeType'].startswith('image/'):
                url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                files = {'photo': (attachment['filename'], file_data)}
            elif attachment['mimeType'].startswith('video/'):
                url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
                files = {'video': (attachment['filename'], file_data)}
            else:
                url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                files = {'document': (attachment['filename'], file_data)}
            
            data = {'chat_id': chat_id}
            
            response = requests.post(url, data=data, files=files, timeout=60)
            
            if response.status_code == 200:
                logging.info(f"Anexo '{attachment['filename']}' enviado com sucesso!")
                return True
            else:
                logging.error(f"Erro ao enviar anexo: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Erro ao enviar anexo '{attachment['filename']}': {e}")
            return False
    
    def process_emails(self):
        """Processa novos emails e envia para Telegram"""
        logging.info("Verificando novos emails...")
        
        new_messages = self.get_new_emails()
        
        for message in new_messages:
            email_data = self.get_email_details(message['id'])
            
            if not email_data:
                continue
            
            if not self.should_forward_email(email_data):
                continue
            
            # Formata e envia mensagem
            telegram_message = self.format_telegram_message(email_data)
            
            if self.send_telegram_message(telegram_message):
                # Envia anexos se configurado e existirem
                if (self.config['settings'].get('include_attachments', True) and 
                    email_data['attachments']):
                    
                    for attachment in email_data['attachments']:
                        # Limita tamanho do anexo (Telegram tem limite de 50MB)
                        if attachment['size'] < 50 * 1024 * 1024:  # 50MB
                            self.send_attachment_to_telegram(attachment, message['id'])
                        else:
                            logging.warning(f"Anexo '{attachment['filename']}' muito grande para Telegram")
        
        # Atualiza timestamp da última verificação
        self.last_check_time = datetime.now()
        logging.info(f"Verificação concluída. Próxima em {self.config['settings']['check_interval_seconds']} segundos")
    
    def run(self):
        """Executa o forwarder em loop contínuo"""
        logging.info("Gmail to Telegram Forwarder iniciado!")
        logging.info(f"Verificando emails a cada {self.config['settings']['check_interval_seconds']} segundos")
        
        try:
            while True:
                self.process_emails()
                time.sleep(self.config['settings']['check_interval_seconds'])
                
        except KeyboardInterrupt:
            logging.info("Forwarder interrompido pelo usuário")
        except Exception as e:
            logging.error(f"Erro inesperado: {e}")
            raise

def main():
    """Função principal"""
    try:
        forwarder = GmailTelegramForwarder()
        forwarder.run()
    except ImportError as e:
        print(f"❌ Erro de dependências: {e}")
        print("\n📋 Soluções:")
        print("1. Certifique-se de estar no ambiente virtual:")
        print("   gmail_env\\Scripts\\activate")
        print("2. Instale as dependências:")
        print("   pip install google-auth google-auth-oauthlib google-api-python-client requests")
        print("3. Execute novamente o script")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\n📋 Passos para configurar:")
        print("1. Configure o arquivo config.json com suas credenciais")
        print("2. Baixe credentials.json do Google Cloud Console")
        print("3. Crie um bot no Telegram e obtenha o token")
        print("4. Execute novamente o script")
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        print(f"❌ Erro inesperado: {e}")
        print("Verifique o arquivo gmail_telegram.log para mais detalhes")

if __name__ == "__main__":
    main()