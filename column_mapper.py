class ColumnMapper:
    """Mapeia diferentes formatos de planilha para campos padronizados"""
    
    def __init__(self):
        # Mapeamento de possíveis nomes de colunas (incluindo Apollo)
        self.column_mappings = {
            'empresa': [
                'company', 'company name', 'empresa', 'companhia', 'organização', 'organizacao',
                'cliente', 'client', 'razão social', 'razao social', 'organization', 'account', 
                'organization name', 'corp', 'corporation', 'firm', 'business', 'negócio',
                'instituição', 'instituicao', 'entidade', 'estabelecimento'
            ],
            'nome': [
                'nome completo', 'nome', 'name', 'pessoa_contato', 'contato', 'responsável', 
                'responsavel', 'pessoa', 'full name', 'contact name', 'person name', 
                'lead name', 'prospect name', 'cliente', 'representante', 'interlocutor'
            ],
            'primeiro_nome': [
                'first name', 'primeiro nome', 'nome', 'first', 'fname'
            ],
            'ultimo_nome': [
                'last name', 'ultimo nome', 'sobrenome', 'surname', 'last', 'lname', 'family name'
            ],
            'cargo': [
                'cargo', 'position', 'função', 'funcao', 'job title', 'job_title', 'title',
                'posição', 'posicao', 'role', 'designation', 'job function', 'seniority',
                'department', 'área', 'area', 'setor', 'função na empresa', 'ocupação', 'ocupacao'
            ],
            'email': [
                'email', 'e-mail', 'mail', 'correio', 'electronic mail', 'email address',
                'contact email', 'work email', 'business email', 'e_mail', 'endereço eletrônico',
                'endereco eletronico', 'correio eletrônico', 'correio eletronico'
            ],
            'telefone': [
                'telefone', 'phone', 'celular', 'tel', 'telephone', 'mobile', 'whatsapp',
                'phone number', 'mobile phone', 'work phone', 'business phone', 'contact number',
                'direct phone', 'office phone', 'fone', 'cel', 'número', 'numero', 'contato telefônico'
            ]
        }
    
    def map_columns(self, df_columns):
        """Mapeia colunas da planilha para campos padronizados"""
        mapped = {}
        df_columns_lower = [col.lower().strip() for col in df_columns]
        
        for field, possible_names in self.column_mappings.items():
            for possible_name in possible_names:
                # Busca correspondência exata
                if possible_name.lower() in df_columns_lower:
                    original_col = df_columns[df_columns_lower.index(possible_name.lower())]
                    mapped[field] = original_col
                    break
                # Busca correspondência parcial (contém a palavra)
                else:
                    for i, col_lower in enumerate(df_columns_lower):
                        if possible_name.lower() in col_lower:
                            mapped[field] = df_columns[i]
                            break
                    if field in mapped:
                        break
        
        # Detecção inteligente por padrões
        if not mapped.get('email'):
            for i, col in enumerate(df_columns):
                if '@' in str(col).lower() or 'mail' in str(col).lower():
                    mapped['email'] = col
                    break
        
        if not mapped.get('telefone'):
            for i, col in enumerate(df_columns):
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['phone', 'tel', 'fone', 'cel']):
                    mapped['telefone'] = col
                    break
        
        return mapped
    
    def validate_required_fields(self, mapped_columns):
        """Valida se os campos obrigatórios foram encontrados"""
        # Se tem primeiro_nome + ultimo_nome, considera como nome válido
        has_name = (mapped_columns.get('nome') or 
                   (mapped_columns.get('primeiro_nome') and mapped_columns.get('ultimo_nome')))
        
        required = ['empresa']
        missing = []
        
        if not mapped_columns.get('empresa'):
            missing.append('empresa')
        if not has_name:
            missing.append('nome')
            
        return missing
    
    def detect_apollo_format(self, df_columns):
        """Detecta se é uma planilha do Apollo"""
        apollo_indicators = [
            'account', 'organization', 'contact name', 'email address',
            'phone number', 'job title', 'seniority', 'department'
        ]
        
        df_columns_lower = [col.lower() for col in df_columns]
        matches = sum(1 for indicator in apollo_indicators if indicator in ' '.join(df_columns_lower))
        
        return matches >= 3  # Se tem 3+ indicadores, provavelmente é Apollo
    
    def find_survey_questions(self, df_columns):
        """Encontra colunas que parecem ser perguntas de pesquisa"""
        survey_keywords = [
            'decisão', 'decisao', 'responsável', 'responsavel',
            'aws', 'nuvem', 'cloud', 'migração', 'migracao',
            'desafios', 'infraestrutura', 'tecnologia', 'budget',
            'ia', 'inteligência artificial', 'pergunta',
            'decision', 'responsible', 'migration', 'challenges',
            'infrastructure', 'technology', 'artificial intelligence',
            'question', 'survey', 'poll'
        ]
        
        survey_columns = []
        for col in df_columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in survey_keywords):
                if len(col) > 30:  # Provavelmente é uma pergunta
                    survey_columns.append(col)
        
        return survey_columns
    
    def get_apollo_mapping_suggestions(self, df_columns):
        """Sugestões específicas para planilhas do Apollo"""
        suggestions = {}
        df_columns_lower = [col.lower() for col in df_columns]
        
        # Mapeamentos específicos do Apollo
        apollo_mappings = {
            'empresa': ['account', 'organization', 'company name'],
            'primeiro_nome': ['first name'],
            'ultimo_nome': ['last name'], 
            'nome': ['contact name', 'name'],
            'cargo': ['job title', 'title', 'seniority'],
            'email': ['email address', 'email'],
            'telefone': ['phone number', 'phone']
        }
        
        for field, apollo_fields in apollo_mappings.items():
            for apollo_field in apollo_fields:
                for i, col_lower in enumerate(df_columns_lower):
                    if apollo_field in col_lower:
                        suggestions[field] = df_columns[i]
                        break
                if field in suggestions:
                    break
        
        return suggestions
    
    def analyze_columns_intelligently(self, df_columns):
        """Analisa colunas de forma inteligente e retorna relatório detalhado"""
        mapped = self.map_columns(df_columns)
        
        print("\n=== ANALISE AUTOMATICA DE COLUNAS ===")
        print(f"Total de colunas encontradas: {len(df_columns)}")
        print(f"Colunas: {', '.join(df_columns)}")
        
        print("\n=== MAPEAMENTO DETECTADO ===")
        for field, column in mapped.items():
            field_name = {
                'empresa': 'Empresa',
                'nome': 'Nome Completo', 
                'primeiro_nome': 'Primeiro Nome',
                'ultimo_nome': 'Último Nome',
                'cargo': 'Cargo',
                'email': 'Email',
                'telefone': 'Telefone'
            }.get(field, field)
            print(f"  {field_name}: '{column}'")
        
        # Verifica campos obrigatórios
        missing = self.validate_required_fields(mapped)
        if missing:
            print(f"\nCAMPOS OBRIGATORIOS NAO ENCONTRADOS: {', '.join(missing)}")
        else:
            print("\nTodos os campos obrigatorios foram detectados!")
        
        # Detecta formato especial
        if self.detect_apollo_format(df_columns):
            print("\nFormato Apollo detectado")
        
        # Encontra perguntas de pesquisa
        survey_cols = self.find_survey_questions(df_columns)
        if survey_cols:
            print(f"\n{len(survey_cols)} perguntas de pesquisa encontradas")
        
        return mapped, missing