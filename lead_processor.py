import pandas as pd
from collections import defaultdict
from piperun_client import PiperunClient
from column_mapper import ColumnMapper

class LeadProcessor:
    def __init__(self):
        self.piperun = PiperunClient()
        self.mapper = ColumnMapper()
    
    def load_file(self, file_path):
        """Carrega arquivo Excel ou CSV com leads"""
        try:
            if file_path.lower().endswith('.csv'):
                # Tenta diferentes encodings para CSV
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        print(f"CSV carregado com encoding: {encoding}")
                        return df
                    except UnicodeDecodeError:
                        continue
                raise Exception("Não foi possível decodificar o arquivo CSV")
            else:
                df = pd.read_excel(file_path)
                return df
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return None
    
    def consolidate_contact_fields(self, row, df_columns):
        """Consolida todos os telefones e emails de diferentes colunas"""
        # Colunas de telefone possíveis
        phone_columns = [
            'Work Direct Phone', 'Home Phone', 'Mobile Phone', 'Corporate Phone', 'Other Phone',
            'Phone Number', 'telefone', 'phone', 'celular', 'tel', 'telephone', 'mobile'
        ]
        
        # Colunas de email possíveis  
        email_columns = [
            'Email Address', 'Secondary Email', 'Tertiary Email',
            'email', 'e-mail', 'mail', 'correio'
        ]
        
        # Coleta todos os telefones
        all_phones = []
        for col in df_columns:
            if any(phone_col.lower() in col.lower() for phone_col in phone_columns):
                phone_value = str(row.get(col, '')).strip()
                if phone_value and phone_value != 'nan' and len(phone_value) > 5:
                    # Se tem múltiplos telefones separados por vírgula
                    if ',' in phone_value:
                        phones = [p.strip() for p in phone_value.split(',') if p.strip()]
                        all_phones.extend(phones)
                    else:
                        all_phones.append(phone_value)
        
        # Coleta todos os emails
        all_emails = []
        for col in df_columns:
            if any(email_col.lower() in col.lower() for email_col in email_columns):
                email_value = str(row.get(col, '')).strip()
                if email_value and email_value != 'nan' and '@' in email_value:
                    # Se tem múltiplos emails separados por vírgula
                    if ',' in email_value:
                        emails = [e.strip() for e in email_value.split(',') if e.strip() and '@' in e]
                        all_emails.extend(emails)
                    else:
                        all_emails.append(email_value)
        
        # Remove duplicatas mantendo ordem
        unique_phones = []
        for phone in all_phones:
            if phone not in unique_phones:
                unique_phones.append(phone)
        
        unique_emails = []
        for email in all_emails:
            if email not in unique_emails:
                unique_emails.append(email)
        
        return ','.join(unique_phones), ','.join(unique_emails)
    
    def group_by_company(self, df, column_mapping):
        """Agrupa contatos por empresa consolidando todos os telefones e emails"""
        grouped = defaultdict(list)
        
        for _, row in df.iterrows():
            # Usa mapeamento para encontrar empresa
            company_col = column_mapping.get('empresa')
            if not company_col:
                continue
                
            company = str(row.get(company_col, '')).strip()
            
            if company and company != 'nan':
                # Combina First Name + Last Name se disponíveis
                nome_completo = ''
                if column_mapping.get('primeiro_nome') and column_mapping.get('ultimo_nome'):
                    primeiro = str(row.get(column_mapping.get('primeiro_nome', ''), '')).strip()
                    ultimo = str(row.get(column_mapping.get('ultimo_nome', ''), '')).strip()
                    if primeiro and ultimo:
                        nome_completo = f"{primeiro} {ultimo}"
                    elif primeiro:
                        nome_completo = primeiro
                    elif ultimo:
                        nome_completo = ultimo
                
                # Se não tem First/Last Name, usa campo nome normal
                if not nome_completo:
                    nome_completo = str(row.get(column_mapping.get('nome', ''), '')).strip()
                
                if nome_completo and nome_completo != 'nan':
                    # Consolida todos os telefones e emails da linha
                    all_phones, all_emails = self.consolidate_contact_fields(row, df.columns)
                    
                    contact = {
                        'nome': nome_completo,
                        'email': all_emails if all_emails else str(row.get(column_mapping.get('email', ''), '')),
                        'telefone': all_phones if all_phones else str(row.get(column_mapping.get('telefone', ''), '')),
                        'cargo': str(row.get(column_mapping.get('cargo', ''), '')),
                        'empresa': company
                    }
                    
                    grouped[company].append(contact)
        
        return dict(grouped)
    
    def process_leads(self, file_path, tag=None, origin_id=None):
        """Processa leads e cria oportunidades no Piperun"""
        df = self.load_file(file_path)
        if df is None:
            return
        
        # Extrai nome da planilha
        import os
        sheet_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Análise inteligente de colunas
        column_mapping, missing_fields = self.mapper.analyze_columns_intelligently(df.columns.tolist())
        
        if missing_fields:
            print(f"\nERRO: Nao e possivel processar sem os campos obrigatorios")
            return
        
        # Encontra perguntas da pesquisa
        survey_questions = self.mapper.find_survey_questions(df.columns.tolist())
        print(f"Perguntas encontradas: {len(survey_questions)}")
        
        grouped_leads = self.group_by_company(df, column_mapping)
        
        for company, contacts in grouped_leads.items():
            print(f"\nProcessando empresa: {company}")
            
            created_persons = []
            
            # Cria TODAS as pessoas da empresa
            for i, contact in enumerate(contacts):
                print(f"  Pessoa {i+1}: {contact['nome']} ({contact.get('cargo', 'N/A')})")
                if contact['email'] and str(contact['email']) != 'nan':
                    print(f"    Email: {contact['email']}")
                if contact['telefone'] and str(contact['telefone']) != 'nan':
                    print(f"    Telefone: {contact['telefone']}")
                
                person = self.piperun.create_person(
                    name=contact['nome'],
                    email=contact['email'],
                    phone=contact['telefone'],
                    company_name=company,
                    job_title=contact.get('cargo', '')
                )
                
                if person:
                    created_persons.append(person)
                    print(f"    [OK] Pessoa criada com ID: {person.get('id')}")
                else:
                    print(f"    [ERRO] Falha ao criar pessoa: {contact['nome']}")
            
            # Cria oportunidade vinculada à pessoa principal
            if created_persons:
                main_person = created_persons[0]
                
                # Cria oportunidade
                deal_title = f"{sheet_name} - {company}"
                deal = self.piperun.create_deal(
                    title=deal_title,
                    person_id=main_person.get('id'),
                    company_id=main_person.get('company_id'),
                    pipeline_id=self.piperun.pipeline_id,
                    stage_id=self.piperun.stage_id,
                    tag=tag,
                    origin_id=origin_id
                )
                
                if deal:
                    print(f"  [OK] Oportunidade criada: {deal_title}")
                    print(f"  [OK] Vinculada à pessoa principal: {main_person.get('name')}")
                    
                    # Cria nota com as respostas da pesquisa
                    first_contact = contacts[0]
                    survey_questions = [
                        'Você é a pessoa responsável pela tomada de decisão no que diz respeito a adoção de novas tecnologias de cloud?',
                        'Qual é o nível de familiaridade da sua organização com serviços de nuvem, especificamente da AWS?',
                        'A sua organização está atualmente considerando ou planejando uma migração para a nuvem?',
                        'Quais são os principais desafios que sua organização enfrenta atualmente em termos de infraestrutura e tecnologia?',
                        'Sua organização já realizou alguma migração para a nuvem anteriormente? Se sim, qual foi a experiência?',
                        'Qual é o principal objetivo que sua organização espera alcançar ao considerar a migração para a nuvem?',
                        'Existe um budget de migração/otimização de cloud para esse ano?',
                        'Quais os principais desafios em relação à adoção de IA na companhia?',
                        'Qual pergunta gostaria que fosse respondida na iniciativa (ela pode ser feita durante o encontro)?'
                    ]
                    
                    notes_content = '=== INFORMAÇÕES DA PESQUISA ON THE ROAD ===\n\n'
                    
                    # Busca as respostas na linha original do DataFrame
                    company_col = column_mapping.get('empresa')
                    nome_col = column_mapping.get('nome')
                    
                    for _, row in df.iterrows():
                        if (str(row.get(company_col, '')) == company and 
                            str(row.get(nome_col, '')) == first_contact['nome']):
                            for question in survey_questions:
                                answer = str(row.get(question, '')).strip()
                                if answer and answer != 'nan' and answer != '':
                                    notes_content += f"P: {question}\n"
                                    notes_content += f"R: {answer}\n\n"
                            break
                    
                    # Cria nota vinculada à pessoa e à oportunidade
                    if notes_content.strip() != '=== INFORMAÇÕES DA PESQUISA ON THE ROAD ===':
                        note = self.piperun.create_note(
                            text=notes_content,
                            person_id=main_person.get('id'),
                            deal_id=deal.get('id')
                        )
                        if note:
                            print(f"  [OK] Nota criada com respostas da pesquisa")
                        else:
                            print(f"  [ERRO] Falha ao criar nota com respostas")
                    
                    # Adiciona outras pessoas como outros contatos da oportunidade
                    if len(created_persons) > 1:
                        for person in created_persons[1:]:
                            if self.piperun.add_deal_contact(deal.get('id'), person.get('id')):
                                print(f"    [OK] {person.get('name')} adicionado como outro contato")
                            else:
                                print(f"    [ERRO] Falha ao adicionar {person.get('name')} como outro contato")
                        print(f"  [OK] {len(created_persons)-1} outros contatos vinculados à oportunidade")
                else:
                    print(f"  [ERRO] Falha ao criar oportunidade para {company}")
            else:
                print(f"  [ERRO] Nenhuma pessoa foi criada para {company}")
        
        print("\n[CONCLUIDO] Verifique as oportunidades no seu Piperun!")