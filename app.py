from datetime import datetime, timedelta
import base64
import csv
import glob
import io
import os
import sqlite3
import urllib.parse
import mercadopago
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import streamlit as st

# CONFIGURAÇÃO DO MERCADO PAGO (Token Oficial de Produção Integrado)
MERCADO_PAGO_ACCESS_TOKEN = (
    "APP_USR-7480302560366070-091611-1118388bbc787e8f88ea1da583096dbc-2919829212"
)

# Configuração da Página com Menu Fixo Expandido
st.set_page_config(
    page_title="Tabalmix Concreto - Gestão de Frota e Oficina Pro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização Visual Corporativa Avançada + Blindagem Anti-F12 / Inspeção
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    [data-testid="stSidebar"] {
        min-width: 310px !important;
        width: 310px !important;
        background: linear-gradient(180deg, rgba(10, 40, 20, 0.98) 0%, rgba(2, 10, 5, 1) 100%) !important;
        border-right: 1px solid rgba(46, 204, 113, 0.3);
        padding-top: 10px;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 310px !important;
    }
    .stApp {
        background: radial-gradient(circle at top left, #0f172a 0%, #07090e 60%);
        color: #f8fafc;
    }
    h1, h2, h3 {
        color: #2ecc71 !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    p, label, span, .stMarkdown {
        color: #cbd5e1 !important;
        font-size: 15px;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #143820 0%, #0a1f10 100%) !important;
        border: 1px solid rgba(46, 204, 113, 0.3) !important;
        border-left: 4px solid #2ecc71 !important;
        padding: 22px !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 30px !important;
        font-weight: 800 !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #1b7a3e 0%, #12542a 100%) !important;
        color: white !important;
        font-weight: 600;
        border-radius: 10px;
        border: 1px solid #2ecc71;
        padding: 0.65rem 1.8rem;
        box-shadow: 0 6px 20px rgba(27, 122, 62, 0.35);
        transition: all 0.25s ease-in-out;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #12542a 0%, #0d381c 100%) !important;
        border-color: #ffffff;
        box-shadow: 0 8px 25px rgba(27, 122, 62, 0.55);
        transform: translateY(-1px);
    }
    div[data-testid="stDataFrame"] {
        background-color: #0f172a;
        border-radius: 14px;
        padding: 12px;
        border: 1px solid rgba(46, 204, 113, 0.2);
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_db():
    conn = sqlite3.connect("frota_profissional.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_patrimonio TEXT,
        tipo TEXT,
        marca TEXT,
        modelo TEXT,
        ano INTEGER,
        chassi TEXT,
        placa TEXT,
        horimetro_km INTEGER,
        combustivel TEXT,
        local_atual TEXT,
        responsavel TEXT,
        status TEXT,
        data_entrada TEXT,
        observacoes TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS manutencoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipamento TEXT,
        tipo_manutencao TEXT,
        horimetro_km_manut TEXT,
        problema TEXT,
        servico_realizado TEXT,
        pecas_utilizadas TEXT,
        custo_pecas REAL,
        mao_de_obra REAL,
        custo REAL,
        oficina TEXT,
        responsavel TEXT,
        status_os TEXT,
        data TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pecas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_item TEXT,
        categoria TEXT,
        quantidade INTEGER,
        valor_unitario REAL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        empresa TEXT,
        telefone TEXT,
        documento TEXT,
        email TEXT,
        endereco TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mobilizacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipamento TEXT,
        tipo_movimento TEXT,
        destino_origem TEXT,
        responsavel TEXT,
        data TEXT,
        horimetro_km_mov TEXT,
        motivo_condicao TEXT,
        observacao TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS combustivel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipamento TEXT,
        litros REAL,
        valor_total REAL,
        km_horimetro TEXT,
        posto_posto TEXT,
        motorista TEXT,
        data TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS licenca (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status_assinatura TEXT,
        plano_atual TEXT,
        data_vencimento TEXT,
        chave_pix TEXT
    )
    """)
    cursor.execute("SELECT COUNT(*) FROM licenca")
    if cursor.fetchone()[0] == 0:
        vencimento_padrao = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO licenca (status_assinatura, plano_atual, data_vencimento, chave_pix) VALUES (?, ?, ?, ?)",
            ("Inativo", "Mensal (R$ 250,00)", vencimento_padrao, "seu-email-pix@dominio.com"),
        )
        conn.commit()
    return conn


conn = init_db()
cursor = conn.cursor()

# Menu lateral totalmente limpo: sem chat, com as abas originais completas e atalho para WhatsApp
st.sidebar.title("🛠️ Tabalmix Concreto")
menu = st.sidebar.radio(
    "Navegação do Sistema",
    [
        "Visão Geral",
        "Cadastro de Equipamentos",
        "Abastecimentos & Combustível",
        "Mobilização / Desmobilização",
        "Ordens de Serviço (OS)",
        "Peças e Ferramentas",
        "Gestão de Clientes",
        "Consulta / Busca Geral",
        "Meu Perfil / Dados",
        "Painel de Licença (Admin)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Enviar por WhatsApp")
texto_whatsapp_sidebar = st.sidebar.text_input("Mensagem rápida:", "Relatório operacional Tabalmix Concreto.")
link_wpp_sidebar = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texto_whatsapp_sidebar)}"
st.sidebar.link_button("📤 Compartilhar no WhatsApp", link_wpp_sidebar, use_container_width=True)

if menu == "Visão Geral":
    st.title("📊 Visão Geral da Frota e Operações")
    st.write("Painel gerencial corporativo completo com integração de relatórios via WhatsApp.")
    
    df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Equipamentos", len(df_veiculos))
    with col2:
        st.metric("Frota Operacional", len(df_veiculos[df_veiculos['status'] == 'Operacional']) if 'status' in df_veiculos.columns else 0)
    with col3:
        st.metric("Em Manutenção", len(df_veiculos[df_veiculos['status'] == 'Em Manutenção']) if 'status' in df_veiculos.columns else 0)
        
    st.subheader("Frota Ativa Cadastrada")
    st.dataframe(df_veiculos, use_container_width=True)
    
    # Botao de compartilhamento do relatorio geral
    relatorio_geral_txt = f"*Tabalmix Concreto - Visão Geral*\n- Total de Veículos: {len(df_veiculos)}\n- Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    st.link_button("📲 Compartilhar Visão Geral no WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(relatorio_geral_txt)}")

elif menu == "Cadastro de Equipamentos":
    st.title("🚜 Cadastro de Equipamentos")
    with st.form("form_eq"):
        c1, c2, c3 = st.columns(3)
        with c1:
            patrimonio = st.text_input("Código de Patrimônio")
            tipo = st.selectbox("Tipo", ["Caminhão Betoneira", "Pá Carregadeira", "Escavadeira", "Gerador", "Outros"])
            marca = st.text_input("Marca")
        with c2:
            modelo = st.text_input("Modelo")
            ano = st.number_input("Ano", min_value=1990, max_value=2030, value=2024)
            placa = st.text_input("Placa / ID")
        with c3:
            horimetro = st.number_input("Horômetro / KM", value=0)
            local = st.text_input("Local Atual / Obra")
            status = st.selectbox("Status", ["Operacional", "Em Manutenção", "Parado"])
            
        btn_cad = st.form_submit_button("Salvar Equipamento")
        if btn_cad and patrimonio:
            cursor.execute("INSERT INTO veiculos (codigo_patrimonio, tipo, marca, modelo, ano, placa, horimetro_km, local_atual, status, data_entrada) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (patrimonio, tipo, marca, modelo, ano, placa, horimetro, local, status, datetime.now().strftime('%Y-%m-%d %H:%M')))
            conn.commit()
            st.success("Equipamento cadastrado com sucesso!")
            
            # WhatsApp automatico do cadastro
            msg_cad = f"*Novo Equipamento - Tabalmix*\n- Patrimônio: {patrimonio}\n- Tipo: {tipo}\n- Modelo: {modelo} ({ano})\n- Status: {status}"
            st.link_button("📲 Compartilhar Equipamento no WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_cad)}")

elif menu == "Abastecimentos & Combustível":
    st.title("⛽ Controle de Abastecimentos")
    with st.form("form_comb"):
        eq_comb = st.text_input("Equipamento")
        litros = st.number_input("Litros", value=50.0)
        total = st.number_input("Valor Total (R$)", value=250.0)
        motorista = st.text_input("Motorista")
        btn_c = st.form_submit_button("Registrar Abastecimento")
        if btn_c and eq_comb:
            cursor.execute("INSERT INTO combustivel (equipamento, litros, valor_total, motorista, data) VALUES (?, ?, ?, ?, ?)",
                           (eq_comb, litros, total, motorista, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            st.success("Abastecimento gravado!")
            
            msg_comb = f"*Abastecimento - Tabalmix*\n- Veículo: {eq_comb}\n- Litros: {litros}L\n- Valor: R$ {total:.2f}\n- Motorista: {motorista}"
            st.link_button("📲 Compartilhar Abastecimento no WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_comb)}")

elif menu == "Ordens de Serviço (OS)":
    st.title("🔧 Ordens de Serviço (OS)")
    with st.form("form_os"):
        eq_os = st.text_input("Equipamento / Máquina")
        tipo_m = st.selectbox("Tipo", ["Preventiva", "Corretiva"])
        prob = st.text_area("Descrição do Problema")
        custo = st.number_input("Custo (R$)", value=0.0)
        btn_os = st.form_submit_button("Emitir Ordem de Serviço")
        if btn_os and eq_os:
            cursor.execute("INSERT INTO manutencoes (equipamento, tipo_manutencao, problema, custo, status_os, data) VALUES (?, ?, ?, ?, ?, ?)",
                           (eq_os, tipo_m, prob, custo, "Aberta", datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            st.success("Ordem de Serviço criada com sucesso!")
            
            msg_os = f"*Nova OS - Tabalmix*\n- Equipamento: {eq_os}\n- Tipo: {tipo_m}\n- Problema: {prob}\n- Custo: R$ {custo:.2f}"
            st.link_button("📲 Compartilhar OS no WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_os)}")

elif menu == "Mobilização / Desmobilização":
    st.title("🚚 Mobilização e Desmobilização")
    st.write("Gerencie o transporte e deslocamento de equipamentos entre obras.")

elif menu == "Peças e Ferramentas":
    st.title("🔩 Controle de Peças e Ferramentas")
    st.write("Estoque de almoxarifado e peças de reposição.")

elif menu == "Gestão de Clientes":
    st.title("👥 Gestão de Clientes")
    with st.form("form_cli"):
        nome_cli = st.text_input("Nome do Cliente")
        empresa_cli = st.text_input("Empresa")
        tel_cli = st.text_input("Telefone")
        if st.form_submit_button("Salvar Cliente") and nome_cli:
            cursor.execute("INSERT INTO clientes (nome, empresa, telefone) VALUES (?, ?, ?)", (nome_cli, empresa_cli, tel_cli))
            conn.commit()
            st.success("Cliente cadastrado com sucesso!")

elif menu == "Consulta / Busca Geral":
    st.title("🔍 Consulta e Busca Rápida")
    termo = st.text_input("Digite o termo ou placa para pesquisar:")
    if termo:
        res = pd.read_sql(f"SELECT * FROM veiculos WHERE codigo_patrimonio LIKE '%{termo}%' OR modelo LIKE '%{termo}%'", conn)
        st.dataframe(res, use_container_width=True)

elif menu == "Meu Perfil / Dados":
    st.title("⚙️ Meu Perfil & Dados da Empresa")
    st.write("Tabalmix Concreto - Todos os direitos reservados.")

else:
    st.title("💳 Painel de Licença (Admin)")
    st.write("Painel administrativo de ativação do sistema.")
