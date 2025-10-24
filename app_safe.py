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
    
    # Lista de tags de oportunidades existentes
    existing_tags = [
        "Ação Ingresso SUP Summit 25", "acate-startups", "Acompanhamento Matheus", "Análise Pendente",
        "AWS [CS] - Partner First", "AWS [CS] - SMB", "AWS [PS]", "AWS [Startups]", 
        "AWS RoadShow - Floripa - Abril/2025", "AWS RoadShow Curitiba 2025", "AWS SaaS Forum - 2025",
        "AWS Summit 2025", "AWS Talks - GenIA - ISVs - 25/07/2025", "AWS Talks - ISVs - 04/07/25",
        "AWS Talks Florianópolis - Mar/2025", "CEI", "Cloud Experience 2025 - Curitiba",
        "Cloud Experience POA - 2025", "Cold lead", "Dep. Pré-vendas", "DG", "Du Joinville",
        "EBDI - RoadShow CTBA - 15/10", "EBDI - RoadShow FLN - 10/09", "EBDI - RoadShow POA - 23/09",
        "Expo Inovação - 2025", "ExpoEcomm - 06/2025", "FeiraHospitalar2025", "Hackaton - GeniusAI - 14/10/2025",
        "Incluir créditos", "Integrar APN", "LeadsPerHour", "Limpeza Funil DG", "Lista Raquel Belem",
        "Migrapack/Modpack", "Oktobercloud 2025", "Prospect", "PV - FTR", "PV - Assessment Gratuito",
        "PV - Assessment Suporte", "PV - Consultoria (1h gratuita)", "PV - Estimativa", "PV - Eventos",
        "PV - MAP", "PV - Ofertas e pacotes de serviço", "PV - PoCs ( MVPs Rápidos)", "Revisão diária",
        "Revisão Semanal", "SBAI", "Serveless day", "Site", "SMB", "SMB Greenfield", "StartUp",
        "Startup Insvetiment Summit 2025", "Startup Journey", "Startup summit 2024", "Startup Summit 2025",
        "Straas", "Tag teste", "TecnoSpeed 2025", "teste 2025", "TESTE-AUTOMACAO", "Update APN",
        "Vendas", "VTEX DAY 2025", "Web Summit 2024"
    ]
    
    tag_option = st.radio(
        "Escolha uma opção:",
        ["Usar tag existente", "Criar nova tag", "Sem tag"]
    )
    
    tag_input = None
    
    if tag_option == "Usar tag existente":
        selected_tag = st.selectbox(
            "Selecione a tag:",
            options=existing_tags
        )
        tag_input = selected_tag
        st.success(f"Tag selecionada: {selected_tag}")
    
    elif tag_option == "Criar nova tag":
        new_tag = st.text_input(
            "Nome da nova tag:",
            placeholder="Ex: Apollo-2024, Evento-SP"
        )
        if new_tag:
            tag_input = new_tag
            st.success(f"Nova tag: {new_tag}")
    
    else:
        st.info("Nenhuma tag será aplicada")
    
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
    
    # Lista de origens existentes
    existing_origins = [
        "1onda-evmello-aws-ate1kusd", "2onda-evmello-aws-prospeccaoativa", "Ação Ingresso SUP Summit 25",
        "ACATE - Associação Catarinense de Tecnologia", "ACIB - Prospecção ativa", "ativa", "AWS",
        "AWS - Bianca Mello", "AWS - Luís Martins", "AWS - Thays Feriotti", "AWS - Ana Carolina Albano",
        "AWS - Andrea Pastore", "AWS - Antonio Wisnesky", "AWS - Beatriz Nunes", "AWS - Caio Gomes",
        "AWS - Camille Heinen", "AWS - Carolina Vieira", "AWS - Catarina Saccomandi", "AWS - Chyenne Haddad",
        "AWS - Danilo Muniz", "AWS - Diagora", "AWS - Diagora Liara Fusinato", "AWS - Eduardo Freitas",
        "AWS - Eduardo Yoshioka", "AWS - Elisa Matsufugi", "AWS - Evandro Melo", "AWS - Felipe Santos",
        "AWS - Gabriel Martins", "AWS - Giovana Gaspar", "AWS - Gracco Lopes", "AWS - Javier Gomes",
        "AWS - Jessica Brombal", "AWS - João Pedro", "AWS - João Pedro, AWS Ace Program", "AWS - Joji Watanabe",
        "AWS - Julia Marotti", "AWS - Julia Pacheco", "AWS - Julia Vernizzi", "AWS - Laura Makrakis",
        "AWS - Leandro Silveira", "AWS - Luigi Martins", "AWS - Marcos Borges", "AWS - Maria Eduarda Mamede",
        "AWS - Mariana Portela", "AWS - Matheus Guedes", "AWS - Michelle Torres", "AWS - Natalia Konishi",
        "AWS - Natalia Reis", "AWS - Oliver", "AWS - Pedro Bonilha", "AWS - Pedro Shimabukuro",
        "AWS - Pedro Valiati", "AWS - Rafael Corrêa", "AWS - Rafael de Oliveira P Toledo", "AWS - Raquel Gossett",
        "AWS - Rodrigo Fernandes", "AWS - Ronaldo Oliveira", "AWS - Thais Gouveia Zilio", "AWS - Thiago Albano",
        "AWS - Thomas Martins", "AWS - Ulysses Pacheco", "AWS - Victor Parabre", "AWS - Yuri Santana",
        "AWS Ace Program", "AWS PS - Edutechs", "AWS Startups", "AWS Startups Greenfield", "AWS Talks - Floripa",
        "AWS- EDUTECHS", "AWS-SummitSP-2023", "AWS-talks", "Blusoft", "bpsi - Gabriel", "Capin",
        "Case | SP", "Cliente da base - ação CS", "Cliente da base - ação Sales", "Cloud Experience Curitiba - 2024",
        "Darwin Startups", "Dati Startups Journey", "Evento", "EVENTO", "evento", "Eventos", "Evoa",
        "Hospitalar 2023", "Inbound", "Indicação", "Indicação, Prospecção ativa", "Infinitto",
        "Instituto Gene", "Jantar Hospitalar 2024", "João Rezende", "Landing Page Dati", "leads per hour",
        "Lucy", "Mídias", "Oktobercloud 2024", "Oktorbercloud-2023", "Outro", "Outros", "outros",
        "Parceiro - DaRede", "Parceiro - Dragon DB", "Parceiro - ITFLEX", "Parceiro - MbLabs",
        "Parceiro - Mundo 365", "Pesquisa Google", "Pre", "prosp4", "Prospecção", "Prospecção ativa",
        "RD Summit", "Rd Summit 24", "road", "RoadShow Curitiba 2025", "sba", "sbai", "SBAI", "sbai",
        "Serveless day 2024", "site", "SITE - DATI", "SMB TD Synnex - Marcos Padua", "South Summit 2024",
        "Startup Summit 2025", "StartupRS", "StartupSC", "StartupSummit2021", "StartupSummit2022",
        "StartupSummit2023", "StartupSummit2024", "suporte", "TD Synnex - ISVs", "TDC Floripa 2024",
        "TDSynnex - Adilson Wada", "TDSynnex - Daniel Locci", "TDSynnex - Deise Darc", "TDSynnex - Zulma",
        "te", "Techshift(#TS)", "teste", "teste", "Vertical Cloud", "VUNO", "vuno", "Web Summit 2024",
        "Web Summit Lisboa 24", "Web Summit Rio 25"
    ]
    
    origin_option = st.radio(
        "Escolha uma opção:",
        ["Usar origem existente", "Criar nova origem", "Sem origem"]
    )
    
    origin_name = None
    
    if origin_option == "Usar origem existente":
        selected_origin = st.selectbox(
            "Selecione a origem:",
            options=existing_origins
        )
        origin_name = selected_origin
        st.success(f"Origem selecionada: {selected_origin}")
    
    elif origin_option == "Criar nova origem":
        new_origin = st.text_input(
            "Nome da nova origem:",
            placeholder="Ex: Prospecção, Site, LinkedIn"
        )
        if new_origin:
            origin_name = new_origin
            st.success(f"Nova origem: {new_origin}")
    
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
                            origins = client.get_origins()
                            for origin in origins:
                                if origin['name'] == origin_name:
                                    origin_id = origin['id']
                                    break
                            
                            # Se não encontrou, cria nova
                            if not origin_id:
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
                            tag=tag_input,
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