import streamlit as st
import pandas as pd
import io
from lead_processor import LeadProcessor
from column_mapper import ColumnMapper
import time
from contextlib import redirect_stdout

st.set_page_config(
    page_title="Automação Piperun",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Automação Piperun - Detecção Automática")
st.markdown("Sistema inteligente para processar qualquer formato de planilha")

# Sidebar com configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Seção de Tags - Versão Simples
    st.subheader("🏷️ Tags")
    
    tag_input = st.text_input(
        "Nome da tag:",
        placeholder="Ex: Apollo-2024, Evento-SP",
        help="Tag que será adicionada a todas as oportunidades"
    )
    
    if tag_input:
        st.success(f"Tag: {tag_input}")
    else:
        st.info("Nenhuma tag definida")
    
    st.markdown("---")
    
    # Campo para nome da oportunidade
    st.subheader("📝 Nome da Oportunidade")
    
    opportunity_name = st.text_input(
        "Prefixo do nome:",
        placeholder="Ex: Lista Outubro, Evento SP, Apollo 2024",
        help="Formato final: [Seu Nome] - [Nome da Empresa]"
    )
    
    if opportunity_name:
        st.success(f"Formato: {opportunity_name} - [Empresa]")
    else:
        st.info("Usará nome da planilha como padrão")
    
    st.markdown("---")
    
    # Campo para origem - Versão Simples
    st.subheader("🌍 Origem")
    
    origin_name = st.text_input(
        "Nome da origem:",
        placeholder="Ex: Prospecção, Site, LinkedIn",
        help="Nome da origem que será criada ou usada se já existir"
    )
    
    if origin_name:
        st.success(f"Origem: {origin_name}")
    else:
        st.info("Nenhuma origem será aplicada")

# Upload de arquivo
uploaded_file = st.file_uploader(
    "Escolha a planilha (Excel ou CSV)",
    type=['xlsx', 'xls', 'csv'],
    help="Sistema detecta automaticamente os campos"
)

if uploaded_file is not None:
    try:
        # Carrega arquivo
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Planilha carregada: {len(df)} linhas, {len(df.columns)} colunas")
        
        # Análise inteligente
        mapper = ColumnMapper()
        
        f = io.StringIO()
        with redirect_stdout(f):
            column_mapping, missing_fields = mapper.analyze_columns_intelligently(df.columns.tolist())
        analysis_output = f.getvalue()
        
        # Mostra análise
        with st.expander("🔍 Análise Automática", expanded=True):
            st.text(analysis_output)
        
        # Preview
        with st.expander("👀 Preview dos dados"):
            st.dataframe(df.head(5))
        
        # Botão processar
        if not missing_fields:
            if st.button("🚀 Processar no Piperun", type="primary"):
                # Salva arquivo temporário
                temp_file = f"temp_{uploaded_file.name}"
                with open(temp_file, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Processamento
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    processor = LeadProcessor()
                    
                    status_text.text("Processando...")
                    progress_bar.progress(50)
                    
                    # Buscar ou criar origem se especificada
                    origin_id = None
                    if origin_name:
                        try:
                            from piperun_client import PiperunClient
                            client = PiperunClient()
                            
                            # Busca origem existente
                            if hasattr(client, 'get_origins'):
                                origins = client.get_origins()
                                for origin in origins:
                                    if origin['name'].lower() == origin_name.lower():
                                        origin_id = origin['id']
                                        break
                            
                            # Se não encontrou, cria nova
                            if not origin_id and hasattr(client, 'create_origin'):
                                new_origin = client.create_origin(origin_name)
                                if new_origin:
                                    origin_id = new_origin['id']
                        except Exception as e:
                            st.warning(f"Erro ao processar origem: {str(e)}")
                    
                    # Captura logs
                    f = io.StringIO()
                    with redirect_stdout(f):
                        processor.process_leads(
                            temp_file, 
                            tag=tag_input.strip() if tag_input else None,
                            origin_id=origin_id,
                            custom_name=opportunity_name.strip() if opportunity_name else None
                        )
                    
                    processing_output = f.getvalue()
                    
                    # Conta resultados
                    empresas = processing_output.count("Processando empresa:")
                    pessoas = processing_output.count("[OK] Pessoa criada")
                    oportunidades = processing_output.count("[OK] Oportunidade criada")
                    
                    progress_bar.progress(100)
                    status_text.text("Concluído!")
                    
                    # Resultados
                    st.success("🎉 Processamento concluído!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Empresas", empresas)
                    with col2:
                        st.metric("Pessoas", pessoas)
                    with col3:
                        st.metric("Oportunidades", oportunidades)
                    
                    # Log detalhado
                    with st.expander("📋 Log Detalhado"):
                        st.text(processing_output)
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
                
                finally:
                    import os
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
        else:
            st.error(f"❌ Campos obrigatórios faltando: {', '.join(missing_fields)}")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar: {str(e)}")

st.markdown("---")
st.markdown("🔧 Sistema com detecção automática de colunas")