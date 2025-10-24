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
    
    # Seção de Tags
    st.subheader("🏷️ Tags")
    
    # Carregar tags existentes
    if 'tags' not in st.session_state:
        try:
            from piperun_client import PiperunClient
            client = PiperunClient()
            tags = client.get_tags()
            st.session_state.tags = tags if tags else []
        except Exception as e:
            st.error(f"Erro ao carregar tags: {str(e)}")
            st.session_state.tags = []
    
    # Opção de tag
    tag_option = st.radio(
        "Escolha uma opção:",
        ["Usar tag existente", "Criar nova tag", "Sem tag"]
    )
    
    tag_input = None
    
    if tag_option == "Usar tag existente":
        if st.session_state.tags:
            # Filtrar apenas tags de oportunidades (belongs = 1)
            opportunity_tags = [tag for tag in st.session_state.tags if tag.get('belongs') == 1]
            
            if opportunity_tags:
                tag_names = [tag['name'] for tag in opportunity_tags]
                selected_tag = st.selectbox(
                    "Selecione a tag:",
                    options=tag_names
                )
                tag_input = selected_tag
                st.success(f"Tag selecionada: {selected_tag}")
                
                # Mostrar quantas tags de oportunidades foram encontradas
                st.info(f"{len(opportunity_tags)} tags de oportunidades disponíveis")
            else:
                st.warning("Nenhuma tag de oportunidade encontrada")
        else:
            st.warning("Nenhuma tag encontrada")
    
    elif tag_option == "Criar nova tag":
        new_tag = st.text_input(
            "Nome da nova tag:",
            placeholder="Ex: Apollo-2024, Evento-SP"
        )
        if new_tag:
            tag_input = new_tag
            st.success(f"Nova tag: {new_tag}")
    
    else:  # Sem tag
        st.info("Nenhuma tag será aplicada")
    
    # Botão para recarregar tags
    if st.button("🔄 Recarregar Tags", help="Recarregar lista de tags"):
        try:
            from piperun_client import PiperunClient
            client = PiperunClient()
            st.session_state.tags = client.get_tags()
            st.success("Tags recarregadas!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao recarregar tags: {str(e)}")
    
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
    
    # Campo para origem
    st.subheader("🌍 Origem")
    
    # Botão para recarregar origens
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄", help="Recarregar origens"):
            try:
                from piperun_client import PiperunClient
                client = PiperunClient()
                st.session_state.origins = client.get_origins()
                st.success("Origens recarregadas!")
            except Exception as e:
                st.error(f"Erro ao recarregar: {str(e)}")
    
    # Carregar origens existentes
    if 'origins' not in st.session_state:
        try:
            from piperun_client import PiperunClient
            client = PiperunClient()
            origins = client.get_origins()
            st.session_state.origins = origins if origins else []
            if not origins:
                st.warning("Nenhuma origem encontrada")
        except Exception as e:
            st.error(f"Erro ao carregar origens: {str(e)}")
            st.session_state.origins = []
    
    # Opção de origem
    origin_option = st.radio(
        "Escolha uma opção:",
        ["Usar origem existente", "Criar nova origem"]
    )
    
    origin_id = None
    
    if origin_option == "Usar origem existente":
        if st.session_state.origins:
            origin_names = ["Nenhuma origem"] + [origin['name'] for origin in st.session_state.origins]
            selected_origin = st.selectbox(
                "Selecione a origem:",
                options=origin_names
            )
            
            if selected_origin != "Nenhuma origem":
                # Encontrar o ID da origem selecionada
                for origin in st.session_state.origins:
                    if origin['name'] == selected_origin:
                        origin_id = origin['id']
                        break
                
                st.success(f"Origem selecionada: {selected_origin}")
            else:
                st.info("Nenhuma origem será aplicada")
        else:
            st.warning("Nenhuma origem encontrada - clique em 🔄 para recarregar")
    
    else:  # Criar nova origem
        new_origin_name = st.text_input(
            "Nome da nova origem:",
            placeholder="Ex: Site, LinkedIn, Evento"
        )
        
        if new_origin_name:
            if st.button("➕ Criar Origem"):
                try:
                    from piperun_client import PiperunClient
                    client = PiperunClient()
                    new_origin = client.create_origin(new_origin_name)
                    
                    if new_origin:
                        origin_id = new_origin['id']
                        st.session_state.origins.append(new_origin)
                        st.success(f"✅ Origem '{new_origin_name}' criada com sucesso!")
                        st.info("Selecione 'Usar origem existente' para usar a nova origem")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erro ao criar origem")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

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