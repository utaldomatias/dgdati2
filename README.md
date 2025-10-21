# 🚀 Automação Piperun - Processamento de Leads

Sistema web para automatizar o upload de leads do Excel/CSV para o CRM Piperun com detecção automática de colunas.

## ✨ Funcionalidades

- 🔍 **Detecção automática** de colunas (Apollo, planilhas personalizadas)
- 📊 **Múltiplos formatos** (Excel .xlsx/.xls, CSV)
- 👥 **Múltiplos contatos** por empresa
- 📝 **Perguntas de pesquisa** automaticamente detectadas
- 🌐 **Interface web** com Streamlit
- 📋 **Logs em tempo real** do processamento

## 🚀 Deploy na AWS

### Opção 1: AWS App Runner
```bash
# Build da imagem
docker build -t piperun-automation .

# Push para ECR e deploy no App Runner
```

### Opção 2: AWS ECS/Fargate
```bash
# Deploy com Docker
docker run -p 8501:8501 \
  -e PIPERUN_API_TOKEN=seu_token \
  -e PIPELINE_ID=seu_pipeline \
  -e STAGE_ID=seu_stage \
  piperun-automation
```

## ⚙️ Configuração

1. **Variáveis de ambiente:**
   ```bash
   PIPERUN_API_TOKEN=seu_token_da_api
   PIPERUN_BASE_URL=https://api.pipe.run/v1
   PIPELINE_ID=id_do_pipeline
   STAGE_ID=id_do_estagio
   ```

2. **Desenvolvimento local:**
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

## 📊 Formatos Suportados

**Colunas detectadas automaticamente:**
- Empresa: Company, Account, Organization
- Nome: Name, Contact Name, First Name + Last Name
- Email: Email Address, Email
- Telefone: Phone Number, Mobile Phone, Work Phone
- Cargo: Job Title, Position, Title

**Perguntas de pesquisa:** Detecta automaticamente colunas com perguntas longas e cria notas no Piperun.

## 🏗️ Arquitetura

- **app.py**: Interface Streamlit
- **lead_processor.py**: Lógica de processamento
- **piperun_client.py**: Cliente da API Piperun
- **column_mapper.py**: Detecção inteligente de colunas