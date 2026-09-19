import streamlit as st
import pandas as pd
import sqlite3
import io
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Tabalmix Concreto - Gestão de Frota e Oficina Pro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
header[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; }
[data-testid="stSidebar"] {
    min-width: 310px !important; width: 310px !important;
    background: linear-gradient(180deg, rgba(10, 40, 20, 0.98) 0%, rgba(2, 10, 5, 1) 100%) !important;
    border-right: 1px solid rgba(46, 204, 113, 0.3);
    padding-top: 10px;
}
.stApp {
    background: radial-gradient(circle at top left, #0f172a 0%, #07090e 60%);
    color: #f8fafc;
}
h1, h2, h3 { color: #2ecc71 !important; font-family: 'Segoe UI', system-ui, sans-serif; }
</style>
""", unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect("frota_profissional.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_patrimonio TEXT, tipo TEXT, marca TEXT, modelo TEXT, ano INTEGER,
        chassi TEXT, placa TEXT, horimetro_km INTEGER, combustivel TEXT,
        local_atual TEXT, responsavel TEXT, status TEXT, data_entrada TEXT, observacoes TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS manutencoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipamento TEXT, tipo_manutencao TEXT, horimetro_km_manut TEXT,
        problema TEXT, servico_realizado TEXT, pecas_utilizadas TEXT,
        custo_pecas REAL, mao_de_obra REAL, custo REAL, oficina TEXT,
        responsavel TEXT, status_os TEXT, data TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, empresa TEXT, telefone TEXT, documento TEXT, email TEXT, endereco TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS combustivel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipamento TEXT, litros REAL, valor_total REAL, km_horimetro TEXT,
        posto_posto TEXT, motorista TEXT, data TEXT
    )
    """)
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# Menu lateral atualizado SEM chat interno e COM compartilhamento via WhatsApp
st.sidebar.title("🛠️ Tabalmix Concreto")
menu = st.sidebar.radio(
    "Navegação do Sistema",
    [
        "Visão Geral",
        "Cadastro de Equipamentos",
        "Abastecimentos & Combustível",
        "Ordens de Serviço (OS)",
        "Gestão de Clientes",
        "Consulta / Busca Geral",
        "Meu Perfil / Dados"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Compartilhamento WhatsApp")
texto_compartilhar = st.sidebar.text_input("Resumo/Texto rápido:", "Relatório operacional Tabalmix Concreto.")
link_wpp_sidebar = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto_compartilhar)}"
st.sidebar.link_button("📤 Enviar para o WhatsApp", link_wpp_sidebar, use_container_width=True)

if menu == "Visão Geral":
    st.title("📊 Visão Geral da Frota e Operações")
    st.write("Painel gerencial atualizado — Comunicação integrada via WhatsApp.")
    
    df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
    st.metric("Total de Equipamentos Cadastrados", len(df_veiculos))
    
    st.subheader("Frota Ativa")
    st.dataframe(df_veiculos, use_container_width=True)
    
    texto_rel = f"*Tabalmix Concreto - Relatório de Visão Geral*\n- Total de Veículos/Frota: {len(df_veiculos)}\n- Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    st.link_button("📲 Compartilhar Relatório Geral no WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto_rel)}")

elif menu == "Cadastro de Equipamentos":
    st.title("🚜 Cadastro de Equipamentos")
    
    with st.form("form_veiculo"):
        col1, col2, col3 = st.columns(3)
        with col1:
            patrimonio = st.text_input("Código / Patrimônio")
            tipo = st.selectbox("Tipo", ["Caminhão Betoneira", "Pá Carregadeira", "Escavadeira", "Gerador", "Outros"])
            marca = st.text_input("Marca")
        with col2:
            modelo = st.text_input("Modelo")
            ano = st.number_input("Ano", min_value=1990, max_value=2030, value=2024)
            placa = st.text_input("Placa / Identificação")
        with col3:
            horimetro = st.number_input("Horômetro / KM Atual", value=0)
            local = st.text_input("Local Atual / Obra")
            status = st.selectbox("Status", ["Operacional", "Em Manutenção", "Parado"])
            
        submitted = st.form_submit_button("Cadastrar Equipamento")
        if submitted and patrimonio:
            cursor.execute("INSERT INTO veiculos (codigo_patrimonio, tipo, marca, modelo, ano, placa, horimetro_km, local_atual, status, data_entrada) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (patrimonio, tipo, marca, modelo, ano, placa, horimetro, local, status, datetime.now().strftime('%Y-%m-%d %H:%M')))
            conn.commit()
            st.success(f"Equipamento {patrimonio} cadastrado com sucesso!")
            
            detalhe_cad = f"*Novo Equipamento Cadastrado - Tabalmix*\n- Patrimônio: {patrimonio}\n- Tipo: {tipo}\n- Modelo: {modelo}\n- Status: {status}"
            st.link_button("📲 Compartilhar Cadastro no WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(detalhe_cad)}")

elif menu == "Abastecimentos & Combustível":
    st.title("⛽ Controle de Abastecimentos")
    with st.form("form_combustivel"):
        equipamento = st.text_input("Equipamento / Veículo")
        litros = st.number_input("Litros abastecidos", min_value=0.0, value=50.0)
        valor_total = st.number_input("Valor Total (R$)", min_value=0.0, value=250.0)
        motorista = st.text_input("Motorista / Responsável")
        data_abast = st.date_input("Data do Abastecimento")
        
        btn_abast = st.form_submit_button("Registrar Abastecimento")
        if btn_abast and equipamento:
            cursor.execute("INSERT INTO combustivel (equipamento, litros, valor_total, motorista, data) VALUES (?, ?, ?, ?, ?)",
                           (equipamento, litros, valor_total, motorista, str(data_abast)))
            conn.commit()
            st.success("Abastecimento registrado com sucesso!")
            
            res_abast = f"*Registro de Abastecimento - Tabalmix*\n- Equipamento: {equipamento}\n- Litros: {litros}L\n- Valor: R$ {valor_total:.2f}\n- Responsável: {motorista}"
            st.link_button("📲 Compartilhar Abastecimento no WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(res_abast)}")

elif menu == "Ordens de Serviço (OS)":
    st.title("🔧 Ordens de Serviço (OS)")
    with st.form("form_os"):
        equip_os = st.text_input("Equipamento / Máquina")
        tipo_manut = st.selectbox("Tipo de Manutenção", ["Preventiva", "Corretiva"])
        problema = st.text_area("Descrição do Problema / Serviço")
        custo_os = st.number_input("Custo Estimado (R$)", value=0.0)
        
        btn_os = st.form_submit_button("Criar Ordem de Serviço")
        if btn_os and equip_os:
            cursor.execute("INSERT INTO manutencoes (equipamento, tipo_manutencao, problema, custo, status_os, data) VALUES (?, ?, ?, ?, ?, ?)",
                           (equip_os, tipo_manut, problema, custo_os, "Aberta", datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            st.success("Ordem de Serviço criada!")
            
            res_os = f"*Nova Ordem de Serviço - Tabalmix*\n- Equipamento: {equip_os}\n- Tipo: {tipo_manut}\n- Problema: {problema}\n- Custo: R$ {custo_os:.2f}"
            st.link_button("📲 Compartilhar OS no WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(res_os)}")

elif menu == "Gestão de Clientes":
    st.title("👥 Gestão de Clientes")
    with st.form("form_cliente"):
        nome_cliente = st.text_input("Nome do Cliente / Contato")
        empresa_cli = st.text_input("Empresa")
        tel_cli = st.text_input("Telefone / WhatsApp")
        btn_cli = st.form_submit_button("Salvar Cliente")
        if btn_cli and nome_cliente:
            cursor.execute("INSERT INTO clientes (nome, empresa, telefone) VALUES (?, ?, ?)", (nome_cliente, empresa_cli, tel_cli))
            conn.commit()
            st.success("Cliente salvo!")

elif menu == "Consulta / Busca Geral":
    st.title("🔍 Consulta Geral no Sistema")
    termo = st.text_input("Digite o termo para buscar:")
    if termo:
        df_busca = pd.read_sql(f"SELECT * FROM veiculos WHERE codigo_patrimonio LIKE '%{termo}%' OR modelo LIKE '%{termo}%'", conn)
        st.dataframe(df_busca, use_container_width=True)

else:
    st.title("⚙️ Meu Perfil / Dados")
    st.write("Configurações do usuário e informações da empresa Tabalmix Concreto.")
