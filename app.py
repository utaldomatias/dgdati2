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
    
    # Campo para tag
    tag_input = st.text_input(
        "🏷️ Tag para oportunidades",
        placeholder="Ex: Apollo-2024, Evento-SP",
        help="Tag que será adicionada a todas as oportunidades"
    )
    
    if tag_input:
        st.success(f"Tag: {tag_input}")
    else:
        st.info("Nenhuma tag definida")
    
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
            st.session_state.origins = client.get_origins()
        except:
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
                            origin_id=origin_id
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