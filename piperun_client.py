import requests
import os
from dotenv import load_dotenv

load_dotenv()

class PiperunClient:
    def __init__(self):
        # Tenta usar secrets do Streamlit primeiro, depois .env
        try:
            import streamlit as st
            self.api_token = st.secrets["PIPERUN_API_TOKEN"]
            self.base_url = st.secrets["PIPERUN_BASE_URL"]
            self.pipeline_id = st.secrets["PIPELINE_ID"]
            self.stage_id = st.secrets["STAGE_ID"]
            pass
        except:
            # Fallback para .env (desenvolvimento local)
            self.api_token = os.getenv('PIPERUN_API_TOKEN')
            self.base_url = os.getenv('PIPERUN_BASE_URL')
            self.pipeline_id = os.getenv('PIPELINE_ID')
            self.stage_id = os.getenv('STAGE_ID')
            pass
        
        if not self.api_token:
            raise Exception("Token da API não encontrado")
            
        self.headers = {
            'token': self.api_token,
            'Content-Type': 'application/json'
        }
        pass
    

    def find_or_create_company(self, company_name):
        """Busca empresa existente ou cria nova"""
        # Busca empresa existente
        search_response = requests.get(
            f'https://api.pipe.run/v1/companies?name={company_name}',
            headers=self.headers
        )
        
        if search_response.status_code == 200:
            result = search_response.json()
            if result.get('success') and result.get('data'):
                companies = result['data']
                if companies:
                    return companies[0]  # Retorna primeira empresa encontrada
        
        # Se não encontrou, cria nova
        data = {'name': company_name}
        response = requests.post(
            'https://api.pipe.run/v1/companies',
            json=data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            result = response.json()
            if result.get('success') and result.get('data'):
                return result['data']
        
        print(f"Erro ao criar/buscar empresa: {response.status_code}")
        return None
    
    def create_person(self, name, email, phone, company_name, job_title='', linkedin_url=''):
        """Cria uma pessoa no Piperun"""
        # Remove valores 'nan' e vazios
        clean_email = email if email and str(email) != 'nan' else ''
        clean_phone = phone if phone and str(phone) != 'nan' else ''
        clean_company = company_name if company_name and str(company_name) != 'nan' else ''
        clean_job = job_title if job_title and str(job_title) != 'nan' else ''
        
        company_id = None
        if clean_company:
            # Busca ou cria empresa
            company = self.find_or_create_company(clean_company)
            if company:
                company_id = company.get('id')
        
        data = {
            'name': name
        }
        
        if clean_job:
            data['job_title'] = clean_job
            
        if company_id:
            data['company_id'] = company_id
            
        if clean_email:
            # Separa múltiplos emails por vírgula, ponto e vírgula ou quebra de linha
            email_separators = [',', ';', '\n', '|', ' ']
            emails = [clean_email]
            
            for separator in email_separators:
                if separator in clean_email:
                    emails = [e.strip() for e in clean_email.split(separator) if e.strip()]
                    break
            
            # Remove valores vazios e 'nan', valida formato de email
            emails = [e for e in emails if e and str(e) != 'nan' and '@' in e]
            
            if emails:
                data['contactEmails'] = emails
            
        if clean_phone:
            # Separa múltiplos telefones por vírgula, ponto e vírgula ou quebra de linha
            phone_separators = [',', ';', '\n', '|', '/']
            phones = [clean_phone]
            
            for separator in phone_separators:
                if separator in clean_phone:
                    phones = [p.strip() for p in clean_phone.split(separator) if p.strip()]
                    break
            
            # Remove valores vazios e 'nan'
            phones = [p for p in phones if p and str(p) != 'nan' and len(p) > 5]
            
            if phones:
                data['contactPhones'] = phones
        
        # Adiciona LinkedIn se fornecido
        if linkedin_url and str(linkedin_url) != 'nan' and linkedin_url.strip():
            data['linkedin'] = linkedin_url.strip()
        
        # Adiciona user_id para camilla@dati.com.br
        data['user_id'] = 97209
        
        response = requests.post(
            'https://api.pipe.run/v1/persons',
            json=data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            result = response.json()
            if result.get('success') and result.get('data'):
                person_data = result['data']
                person_id = person_data.get('id')
                
                # Marca que os contatos foram incluídos
                person_data['_contacts_included'] = bool(clean_email or clean_phone)
                
                # Adiciona informações extras para retorno
                person_data['_email'] = clean_email
                person_data['_phone'] = clean_phone
                person_data['_company_name'] = clean_company
                return person_data
            return result
        else:
            print(f"Erro ao criar pessoa: {response.status_code} - {response.text}")
            return None
    
    def add_deal_contact(self, deal_id, person_id):
        """Adiciona pessoa como outro contato da oportunidade"""
        response = requests.put(
            f'https://api.pipe.run/v1/deals/{deal_id}/persons/{person_id}',
            headers=self.headers
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"Erro ao adicionar contato à oportunidade: {response.status_code} - {response.text}")
            return False
    
    def create_note(self, text, person_id=None, deal_id=None, company_id=None):
        """Cria uma nota no Piperun"""
        data = {
            'text': text
        }
        
        if person_id:
            data['person_id'] = person_id
        if deal_id:
            data['deal_id'] = deal_id
        if company_id:
            data['company_id'] = company_id
            
        response = requests.post(
            'https://api.pipe.run/v1/notes',
            json=data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            result = response.json()
            if result.get('success') and result.get('data'):
                return result['data']
            return result
        else:
            print(f"Erro ao criar nota: {response.status_code} - {response.text}")
            return None
    
    def get_tags(self):
        """Busca todas as tags disponíveis com paginação"""
        all_tags = []
        page = 1
        
        while True:
            response = requests.get(
                f'https://api.pipe.run/v1/tags?page={page}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('data'):
                    tags = result['data']
                    all_tags.extend(tags)
                    
                    # Verifica se há próxima página
                    meta = result.get('meta', {})
                    if page >= meta.get('total_pages', 1):
                        break
                    
                    page += 1
                else:
                    break
            else:
                break
        
        return all_tags
    
    def create_or_get_tag(self, tag_name):
        """Cria uma tag ou retorna se já existe"""
        # Busca tags existentes
        tags = self.get_tags()
        
        # Procura tag existente
        for tag in tags:
            if tag.get('name') == tag_name and tag.get('belongs') == 1:  # 1 = oportunidade
                return tag.get('id')
        
        # Se não encontrou, cria nova tag
        data = {
            'name': tag_name,
            'belongs': 1,  # 1 = oportunidade
            'color': 'primary',  # Verde
            'active': True
        }
        
        response = requests.post(
            'https://api.pipe.run/v1/tags',
            json=data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            result = response.json()
            if result.get('success') and result.get('data'):
                return result['data'].get('id')
        
        print(f"Erro ao criar tag: {response.status_code} - {response.text}")
        return None
    
    def add_tag_to_deal(self, deal_id, tag_id):
        """Adiciona tag à oportunidade"""
        response = requests.put(
            f'https://api.pipe.run/v1/deals/{deal_id}/tags/{tag_id}',
            headers=self.headers
        )
        
        if response.status_code in [200, 204]:  # 204 = No Content (sucesso)
            return True
        else:
            print(f"Erro ao adicionar tag à oportunidade: {response.status_code} - {response.text}")
            return False
    
    def get_origins(self):
        """Busca todas as origens disponíveis com paginação"""
        all_origins = []
        page = 1
        
        while True:
            response = requests.get(
                f'https://api.pipe.run/v1/origins?page={page}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('data'):
                    origins = result['data']
                    all_origins.extend(origins)
                    
                    # Verifica se há próxima página
                    meta = result.get('meta', {})
                    if page >= meta.get('total_pages', 1):
                        break
                    
                    page += 1
                else:
                    break
            else:
                break
        
        return all_origins
    
    def create_origin(self, name):
        """Cria uma nova origem"""
        data = {
            'name': name,
            'active': True
        }
        
        response = requests.post(
            'https://api.pipe.run/v1/origins',
            json=data,
            headers=self.headers
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            if result.get('success') and result.get('data'):
                return result['data']
        
        print(f"Erro ao criar origem: {response.status_code} - {response.text}")
        return None
    
    def create_deal(self, title, person_id, company_id=None, value=0, pipeline_id=None, stage_id=None, notes='', tag=None, tags=None, origin_id=None):
        """Cria uma oportunidade no Piperun"""
        data = {
            'title': title,
            'person_id': person_id,
            'value': value,
            'pipeline_id': pipeline_id or self.pipeline_id,
            'stage_id': stage_id or self.stage_id
        }
        
        if company_id:
            data['company_id'] = company_id
            
        if notes:
            data['notes'] = notes
            
        if origin_id:
            data['origin_id'] = origin_id
        
        response = requests.post(
            'https://api.pipe.run/v1/deals',
            json=data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            result = response.json()
            if result.get('success') and result.get('data'):
                deal_data = result['data']
                
                # Se tem tag única, adiciona à oportunidade
                if tag:
                    tag_id = self.create_or_get_tag(tag)
                    if tag_id:
                        self.add_tag_to_deal(deal_data.get('id'), tag_id)
                
                # Se tem múltiplas tags, adiciona todas
                if tags:
                    for tag_name in tags:
                        tag_id = self.create_or_get_tag(tag_name)
                        if tag_id:
                            self.add_tag_to_deal(deal_data.get('id'), tag_id)
                
                return deal_data
            return result
        else:
            print(f"Erro ao criar oportunidade: {response.status_code} - {response.text}")
            return None