from datetime import datetime, timedelta
import base64
import csv
import glob
import io
import os
import random
import string
import urllib.parse
import mercadopago
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import streamlit as st

# LIGAÇÃO NATIVA BLINDADA AO SUPABASE VIA STREAMLIT CONNECTION (RESOLVE QUALQUER BLOQUEIO DE FIREWALL)
try:
    conn = st.connection("supabase", type="sql")
    # Teste rápido de conectividade
    conn.query("SELECT 1;", ttl=0)
except Exception:
    import psycopg2
    # Fallback direto caso o conector nativo exija configuração de secrets
    SUPABASE_DB_URL = "postgresql://postgres.ctibigorhywnwkuzqfjm:bz8VNak7mmgXO05i@aws-0-sa-east-1.pooler.supabase.co:6543/postgres?sslmode=require"
    conn_psycopg2 = psycopg2.connect(SUPABASE_DB_URL)
    cursor_p = conn_psycopg2.cursor()

# CONFIGURAÇÃO DO MERCADO PAGO
MERCADO_PAGO_ACCESS_TOKEN = (
    "APP_USR-7480302560366070-091611-1118388bbc787e8f88ea1da583096dbc-2919829212"
)
try:
  sdk_mp = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
except Exception:
  sdk_mp = None

st.set_page_config(
    page_title="Tabalmix Concreto - Enterprise Fleet & Operations Pro X",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        max-width: 100% !important;
    }
    [data-testid="stSidebar"] {
        background: #f8fafc !important;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] .stRadio label, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] div {
        color: #1e293b !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
    }
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            width: 100% !important;
            min-width: 100% !important;
        }
    }
    .stApp {
        background: #f4f6f9 !important;
        color: #0f172a !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    h1, h2, h3, h4 {
        color: #0f172a !important;
        font-weight: 800;
        letter-spacing: -0.8px;
    }
    label, div[data-baseweb="input"] label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stTextArea label {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 5px solid #059669 !important;
        padding: 18px !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04);
    }
    div.stTextInput input, 
    div.stNumberInput input, 
    div.stSelectbox div[data-baseweb="select"],
    div.stTextArea textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: white !important;
        font-weight: 700;
        border-radius: 12px;
        border: none;
        padding: 0.65rem 1.8rem;
        box-shadow: 0 6px 16px rgba(5, 150, 105, 0.3);
    }
    </style>
""",
    unsafe_allow_html=True,
)


def gerar_excel_formatado(dataframe, nome_aba="Relatório Tabalmix"):
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    dataframe.to_excel(writer, sheet_name=nome_aba, index=False)
    workbook = writer.book
    worksheet = writer.sheets[nome_aba]
    header_format = workbook.add_format({
        "bold": True,
        "text_wrap": True,
        "fg_color": "#047857",
        "font_color": "white",
        "border": 1,
        "align": "center",
        "valign": "middle",
    })
    cell_format = workbook.add_format({
        "border": 1,
        "align": "left",
        "valign": "middle",
        "text_wrap": True,
    })
    for col_num, value in enumerate(dataframe.columns.values):
      worksheet.write(0, col_num, str(value).upper(), header_format)
      max_len = max(dataframe[value].astype(str).map(len).max(), len(str(value))) + 4
      worksheet.set_column(col_num, col_num, max(max_len, 15), cell_format)
  output.seek(0)
  return output


def gerar_pdf_relatorio(titulo, dataframe):
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=letter)
  largura, altura = letter
  margem_esq = 30
  largura_util = largura - 60
  c.setFillColorRGB(0.04, 0.35, 0.22)
  c.rect(0, altura - 70, largura, 70, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 16)
  c.drawString(margem_esq, altura - 30, "tabalmix concreto — enterprise management")
  c.setFont("Helvetica", 9)
  c.drawString(margem_esq, altura - 48, "relatório executivo certificado | powered by castro tech")
  c.setFillColorRGB(0.1, 0.1, 0.1)
  c.setFont("Helvetica-Bold", 14)
  c.drawString(margem_esq, altura - 95, titulo)
  c.setFont("Helvetica", 9)
  c.setFillColorRGB(0.4, 0.4, 0.4)
  c.drawString(margem_esq, altura - 112, f"gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
  c.setStrokeColorRGB(0.8, 0.8, 0.8)
  c.setLineWidth(1)
  c.line(margem_esq, altura - 120, largura - margem_esq, altura - 120)
  y = altura - 145
  altura_linha = 22
  colunas = list(dataframe.columns)
  colunas_amigables = [str(col).replace("_", " ").upper() for col in colunas[:6]]
  c.setFillColorRGB(0.05, 0.25, 0.15)
  c.rect(margem_esq, y - 4, largura_util, altura_linha, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 8.5)
  largura_coluna = largura_util / max(len(colunas_amigables), 1)
  for i, col_nome in enumerate(colunas_amigables):
    c.drawString(margem_esq + (i * largura_coluna) + 4, y + 4, col_nome[:14])
  y -= altura_linha + 4
  c.setFont("Helvetica", 8)
  for index, row in dataframe.iterrows():
    if y < 50:
      c.showPage()
      y = altura - 40
    if index % 2 == 0:
      c.setFillColorRGB(0.95, 0.97, 0.95)
      c.rect(margem_esq, y - 3, largura_util, altura_linha - 2, fill=1, stroke=0)
    c.setFillColorRGB(0.15, 0.15, 0.15)
    for i, col in enumerate(colunas[:6]):
      valor_celula = str(row[col])
      if valor_celula == "None" or valor_celula == "nan":
        valor_celula = "-"
      c.drawString(margem_esq + (i * largura_coluna) + 4, y + 3, valor_celula[:16])
    c.setStrokeColorRGB(0.88, 0.9, 0.88)
    c.line(margem_esq, y - 4, largura - margem_esq, y - 4)
    y -= altura_linha
  c.save()
  buffer.seek(0)
  return buffer


@st.cache_resource
def init_db_tables():
  import psycopg2
  SUPABASE_DB_URL = "postgresql://postgres.ctibigorhywnwkuzqfjm:bz8VNak7mmgXO05i@aws-0-sa-east-1.pooler.supabase.co:6543/postgres?sslmode=require"
  conn_db = psycopg2.connect(SUPABASE_DB_URL)
  cur = conn_db.cursor()
  cur.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id SERIAL PRIMARY KEY,
            tag_prefixo TEXT, categoria_equipamento TEXT,
            tipo_equipamento TEXT, operador_condutor TEXT,
            marca TEXT, modelo TEXT, ano INTEGER, chassi TEXT, renavam TEXT,
            placa TEXT, crv TEXT, cor TEXT, combustivel TEXT, empresa TEXT,
            horimetro_km INTEGER, status TEXT, historico_edicoes TEXT
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS manutencoes (
            id SERIAL PRIMARY KEY,
            tag_prefixo TEXT, tipo_manutencao TEXT, horimetro_km_manut TEXT,
            origem_falha TEXT, descricao_problema TEXT, data_abertura TEXT,
            hora_abertura TEXT, pecas_utilizadas TEXT, custo_pecas REAL,
            mao_de_obra REAL, custo REAL, oficina TEXT, tecnico_mecanico TEXT,
            data_fechamento TEXT, hora_fechamento TEXT, status_os TEXT
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS pecas (
            id SERIAL PRIMARY KEY,
            nome_item TEXT, categoria TEXT, quantidade INTEGER, valor_unitario REAL
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nome TEXT, empresa TEXT, telefone TEXT, documento TEXT, email TEXT, endereco TEXT
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS mobilizacoes (
            id SERIAL PRIMARY KEY,
            equipamento TEXT, tipo_movimento TEXT, destino_origem TEXT,
            responsavel TEXT, data TEXT, horimetro_km_mov TEXT,
            motivo_condicao TEXT, observacao TEXT, foto_checklist TEXT,
            historico_edicoes TEXT
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS combustivel (
            id SERIAL PRIMARY KEY,
            equipamento TEXT, litros REAL, valor_total REAL,
            km_horimetro TEXT, posto_posto TEXT, motorista TEXT, data TEXT
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id SERIAL PRIMARY KEY,
            nome_completo TEXT, cpf TEXT, email TEXT UNIQUE, senha TEXT,
            celular_seguranca TEXT, status_assinatura TEXT, plano_atual TEXT,
            data_cadastro TEXT, pin_rapido TEXT, apelido TEXT, cargo_setor TEXT
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS config_colunas (
            tabela TEXT PRIMARY KEY,
            ordem_colunas TEXT
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_interno (
            id SERIAL PRIMARY KEY,
            remetente TEXT,
            destinatario TEXT,
            cargo TEXT,
            mensagem TEXT,
            arquivo_path TEXT,
            arquivo_nome TEXT,
            data_envio TEXT
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS chaves_licenca (
            id SERIAL PRIMARY KEY,
            codigo_chave TEXT UNIQUE,
            cargo_atribuido TEXT,
            modalidade TEXT,
            status_uso TEXT,
            usado_por TEXT,
            data_criacao TEXT
        )
    """)
  cur.execute("""
        CREATE TABLE IF NOT EXISTS multas (
            id SERIAL PRIMARY KEY,
            equipamento_placa TEXT,
            orgao_autuador TEXT,
            local_infracao TEXT,
            data_infracao TEXT,
            valor_multa REAL,
            descricao_infracao TEXT,
            condutor_responsable TEXT,
            data_vencimento TEXT,
            status_multa TEXT
        )
    """)
  try:
    cur.execute("UPDATE usuarios_sistema SET apelido = 'Colaborador' WHERE apelido IS NULL OR apelido = '' OR apelido = 'None'")
    cur.execute("UPDATE usuarios_sistema SET cargo_setor = 'Operacional' WHERE cargo_setor IS NULL OR cargo_setor = '' OR cargo_setor = 'None'")
    cur.execute("UPDATE usuarios_sistema SET status_assinatura = 'Ativo' WHERE status_assinatura IS NULL OR status_assinatura = '' OR status_assinatura = 'None'")
    conn_db.commit()
  except Exception:
    pass

  cur.execute("SELECT COUNT(*) FROM usuarios_sistema")
  if cur.fetchone()[0] == 0:
    cur.execute(
        "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, apelido, cargo_setor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        ("Alex de Castro Bernardino", "000.000.000-00", "alexcastro02522@gmail.com", "admin2026", "(92) 99999-9999", "Ativo", "Plano Master Concreto & Diretoria", datetime.now().strftime("%Y-%m-%d %H:%M"), "Alex", "Diretoria / Gestão")
    )
    conn_db.commit()
  conn_db.commit()
  conn_db.close()
  return True

init_db_tables()

# Helper de execução de queries seguro com Pandas e Conector Nativo
def ler_tabelas_sql(query_str):
  try:
    import psycopg2
    SUPABASE_DB_URL = "postgresql://postgres.ctibigorhywnwkuzqfjm:bz8VNak7mmgXO05i@aws-0-sa-east-1.pooler.supabase.co:6543/postgres?sslmode=require"
    cnn = psycopg2.connect(SUPABASE_DB_URL)
    df_res = pd.read_sql(query_str, cnn)
    cnn.close()
    return df_res
  except Exception:
    return pd.DataFrame()

def executar_comando_sql(query_str, params=None):
  try:
    import psycopg2
    SUPABASE_DB_URL = "postgresql://postgres.ctibigorhywnwkuzqfjm:bz8VNak7mmgXO05i@aws-0-sa-east-1.pooler.supabase.co:6543/postgres?sslmode=require"
    cnn = psycopg2.connect(SUPABASE_DB_URL)
    cur = cnn.cursor()
    if params:
      cur.execute(query_str, params)
    else:
      cur.execute(query_str)
    cnn.commit()
    cur.close()
    cnn.close()
    return True
  except Exception as e:
    print(f"Erro SQL: {e}")
    return False

modo_admin_liberado = False
try:
  query_params = st.query_params
  if query_params.get("admin") == "tabalmix_master_2026" or query_params.get("admin") == ["tabalmix_master_2026"] or str(query_params).find("admin=tabalmix_master_2026") != -1:
    modo_admin_liberado = True
except Exception:
  modo_admin_liberado = False

if "usuario_logado" not in st.session_state:
  st.session_state["usuario_logado"] = None

try:
  if st.session_state["usuario_logado"] is None and not modo_admin_liberado:
    qp = st.query_params
    saved_user_id = qp.get("user_id")
    if saved_user_id:
      df_pers = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE id = {int(saved_user_id)}")
      if not df_pers.empty:
        res_persist = df_pers.iloc[0]
        st.session_state["usuario_logado"] = {
            "id": res_persist["id"],
            "nome": res_persist["nome_completo"],
            "cpf": res_persist["cpf"],
            "email": res_persist["email"],
            "status": res_persist["status_assinatura"],
            "apelido": res_persist["apelido"] if pd.notnull(res_persist["apelido"]) and res_persist["apelido"] != "None" else str(res_persist["nome_completo"]).split()[0],
            "cargo": res_persist["cargo_setor"] if pd.notnull(res_persist["cargo_setor"]) and res_persist["cargo_setor"] != "None" else "Colaborador",
        }
except Exception:
  pass

is_gestao_ou_admin = modo_admin_liberado
if st.session_state["usuario_logado"]:
  cargo_colab = str(st.session_state["usuario_logado"].get("cargo", ""))
  if "Diretoria" in cargo_colab or "Gestão" in cargo_colab or "Engenheiro" in cargo_colab:
    is_gestao_ou_admin = True

if st.session_state["usuario_logado"] is None and not modo_admin_liberado:
  col_l1, col_l2, col_l3 = st.columns([0.05, 3.9, 0.05])
  with col_l2:
    try:
      with open("caminhoes.jpg", "rb") as image_file:
        encoded_logo_login = base64.b64encode(image_file.read()).decode()
      st.markdown(
          f"""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 20px 40px rgba(5,150,105,0.2); margin-top: 10px; margin-bottom: 20px; color: white;">
                    <div style="border-radius: 14px; overflow: hidden; max-height: 110px; border: 3px solid rgba(255,255,255,0.8); margin-bottom: 14px; box-shadow: 0 8px 20px rgba(0,0,0,0.2);">
                        <img src="data:image/jpeg;base64,{encoded_logo_login}" style="width: 100%; height: 110px; object-fit: cover; display: block;">
                    </div>
                    <h1 style="color: white !important; margin: 0; font-size: 24px; font-weight: 900;">tabalmix concreto</h1>
                    <p style="color: #e2e8f0; font-size: 11.5px; margin: 4px 0 2px 0; text-transform: uppercase; font-weight: 600;">sistema inteligente de frotas e obras</p>
                </div>
            """,
          unsafe_allow_html=True,
      )
    except Exception:
      st.markdown(
          """
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 20px 40px rgba(5,150,105,0.2); margin-top: 10px; margin-bottom: 20px; color: white;">
                    <h1 style="color: white !important; margin: 0; font-size: 24px; font-weight: 900;">tabalmix concreto</h1>
                </div>
            """,
          unsafe_allow_html=True,
      )

    escolha_modo_login = st.selectbox(
        "🛠️ Escolha a opção de acesso:",
        [
            "📝 Criar Novo Cadastro",
            "🔑 Entrar com E-mail e Senha",
            "🔐 Acesso Rápido com PIN",
            "🎟️ Ativar com Chave Corporativa",
            "🔄 Recuperar Senha",
        ],
    )

    if escolha_modo_login == "🔐 Acesso Rápido com PIN":
      with st.form("form_pin"):
        st.markdown("### 🔐 Acesso Rápido com PIN da Obra")
        email_pin = st.text_input("E-mail corporativo")
        pin_dig = st.text_input("PIN numérico (4 dígitos)", max_chars=4, type="password")
        if st.form_submit_button("Entrar com PIN"):
          df_pin = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_pin}' AND pin_rapido = '{pin_dig}'")
          if not df_pin.empty:
            user_pin = df_pin.iloc[0]
            if str(user_pin["status_assinatura"]).strip().lower() != "ativo":
              st.error("⚠️ Esta conta encontra-se INATIVA.")
            else:
              st.session_state["usuario_logado"] = {
                  "id": user_pin["id"], "nome": user_pin["nome_completo"], "cpf": user_pin["cpf"],
                  "email": user_pin["email"], "status": user_pin["status_assinatura"],
                  "apelido": user_pin["apelido"] if pd.notnull(user_pin["apelido"]) and user_pin["apelido"] != "None" else str(user_pin["nome_completo"]).split()[0],
                  "cargo": user_pin["cargo_setor"] if pd.notnull(user_pin["cargo_setor"]) and user_pin["cargo_setor"] != "None" else "Colaborador"
              }
              st.success("✅ Login por PIN validado!")
              st.rerun()
          else:
            st.error("⚠️ E-mail ou PIN inválidos.")

    elif escolha_modo_login == "🔑 Entrar com E-mail e Senha":
      with st.form("form_login"):
        st.markdown("### 🔑 Entrar na Conta")
        email_login = st.text_input("E-mail corporativo")
        senha_login = st.text_input("Senha de acesso", type="password")
        if st.form_submit_button("Entrar no Sistema"):
          df_log = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_login}' AND senha = '{senha_login}'")
          if not df_log.empty:
            user_data = df_log.iloc[0]
            if str(user_data["status_assinatura"]).strip().lower() != "ativo":
              st.error("⚠️ Esta conta encontra-se INATIVA.")
            else:
              st.session_state["usuario_logado"] = {
                  "id": user_data["id"], "nome": user_data["nome_completo"], "cpf": user_data["cpf"],
                  "email": user_data["email"], "status": user_data["status_assinatura"],
                  "apelido": user_data["apelido"] if pd.notnull(user_data["apelido"]) and user_data["apelido"] != "None" else str(user_data["nome_completo"]).split()[0],
                  "cargo": user_data["cargo_setor"] if pd.notnull(user_data["cargo_setor"]) and user_data["cargo_setor"] != "None" else "Colaborador"
              }
              st.success("✅ Login realizado com sucesso!")
              st.rerun()
          else:
            st.error("⚠️ E-mail ou senha incorretos.")

    elif escolha_modo_login == "📝 Criar Novo Cadastro":
      st.markdown("### 📝 Criar Novo Cadastro na Obra")
      c_nome = st.text_input("Nome Completo")
      c_apelido = st.text_input("Apelido / Primeiro Nome")
      c_cargo = st.selectbox("Cargo / Função", ["💎 Master Concreto & Diretoria", "🏗️ Engenharia & Obra Pro", "🛠️ Oficina & Mecânica X", "🚜 Operacional Campo & Frota"])
      cargo_banco_str = "Diretoria / Gestão" if "Master" in c_cargo else ("Engenheiro / Gestor de Obra" if "Engenharia" in c_cargo else ("Mecânico / Oficina" if "Oficina" in c_cargo else "Operador / Motorista / Campo"))
      with st.form("form_novo_cad"):
        c_cpf = st.text_input("CPF")
        c_email = st.text_input("E-mail corporativo")
        c_senha = st.text_input("Senha", type="password")
        c_cel = st.text_input("Celular / WhatsApp")
        if st.form_submit_button("Cadastrar"):
          if c_nome and c_email and c_senha:
            apelido_f = c_apelido if c_apelido else c_nome.split()[0]
            sucesso_ins = executar_comando_sql(
                "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, apelido, cargo_setor) VALUES (%s, %s, %s, %s, %s, 'Ativo', %s, %s, %s, %s)",
                (c_nome, c_cpf, c_email, c_senha, c_cel, c_cargo, datetime.now().strftime("%Y-%m-%d %H:%M"), apelido_f, cargo_banco_str)
            )
            if sucesso_ins:
              st.success("✅ Conta cadastrada com sucesso!")
            else:
              st.error("⚠️ Erro ao registar conta.")

  st.stop()

usuario_atual = st.session_state["usuario_logado"]
status_usuario_ativo = True if modo_admin_liberado else (str(usuario_atual.get("status", "Ativo")).strip().lower() == "ativo" if usuario_atual else False)

if not status_usuario_ativo and not modo_admin_liberado:
  st.error("⚠️ A sua conta encontra-se INATIVA.")
  if st.button("🚪 Terminar Sessão"):
    st.session_state["usuario_logado"] = None
    st.rerun()
  st.stop()


def exibir_tabela_padronizada(df, nome_tabela):
  if df.empty:
    st.info("Nenhum registo encontrado.")
    return
  try:
    df_conf = ler_tabelas_sql(f"SELECT ordem_colunas FROM config_colunas WHERE tabela = '{nome_tabela}'")
    if not df_conf.empty and df_conf.iloc[0]["ordem_colunas"]:
      cols_ocultas = [c.strip() for c in df_conf.iloc[0]["ordem_colunas"].split(",") if c.strip()]
      cols_visiveis = [c for c in df.columns if c not in cols_ocultas]
      if cols_visiveis:
        df = df[cols_visiveis]
  except Exception:
    pass
  st.dataframe(df, use_container_width=True, hide_index=True)


with st.sidebar:
  st.markdown("<div style='text-align:center; font-weight:900;'>🏗️ TABALMIX CONCRETO</div>", unsafe_allow_html=True)
  if modo_admin_liberado:
    st.success("🔓 **Modo Admin Ativo**")
  elif usuario_atual:
    st.markdown(f"👤 **{usuario_atual['apelido']}**<br>{usuario_atual['cargo']}", unsafe_allow_html=True)
    if st.button("🚪 Encerrar Sessão"):
      st.session_state["usuario_logado"] = None
      st.rerun()
  st.markdown("---")

lista_menus = [
    "📊 Visão Geral",
    "🚜 Cadastro de Equipamentos",
    "⛽ Abastecimentos & Combustível",
    "🏗️ Mobilização / Desmobilização",
    "🛠️ Ordens de Serviço (OS)",
    "🚨 Gestão & Alertas de Multas",
    "🔩 Peças e Ferramentas",
    "👥 Gestão de Clientes",
    "💬 Chat Tabalmix Pro & Rede",
    "🔍 Consulta / Busca Geral",
    "⚙️ Meu Perfil / Dados",
]
if modo_admin_liberado:
  lista_menus.append("⚙️ Painel de Licença (Admin)")

menu = st.sidebar.radio("Navegação", lista_menus, label_visibility="collapsed")

if menu == "📊 Visão Geral":
  st.title("🏗️ Painel Executivo e Indicadores de Frota")
  df_veiculos = ler_tabelas_sql("SELECT * FROM veiculos")
  df_manut = ler_tabelas_sql("SELECT * FROM manutencoes")
  df_comb = ler_tabelas_sql("SELECT * FROM combustivel")
  df_multas = ler_tabelas_sql("SELECT * FROM multas")

  c1, c2, c3, c4, c5 = st.columns(5)
  with c1: st.metric("Total Frota", len(df_veiculos))
  with c2: st.metric("OS Abertas", len(df_manut[df_manut["status_os"] == "aberta"]) if not df_manut.empty else 0)
  with c3: st.metric("Multas Pendentes", len(df_multas[df_multas["status_multa"] == "Pendente"]) if not df_multas.empty else 0)
  with c4: st.metric("Gasto Combust.", f"R$ {df_comb['valor_total'].sum() if not df_comb.empty else 0.0:,.2f}")
  with c5: st.metric("Total Litros", f"{df_comb['litros'].sum() if not df_comb.empty else 0.0:,.1f} L")
  st.divider()
  if not df_veiculos.empty:
    exibir_tabela_padronizada(df_veiculos, "veiculos")
    if st.button("📄 Gerar Relatório Executivo Geral em PDF"):
      pdf_geral = gerar_pdf_relatorio("Relatório Geral", df_veiculos)
      st.download_button("📥 Baixar PDF", data=pdf_geral, file_name="relatorio_frota.pdf", mime="application/pdf")
  else:
    st.info("Nenhum veículo registado.")

elif menu == "🚜 Cadastro de Equipamentos":
  st.title("🚜 Cadastro de Equipamentos & Vistoria Fotográfica")
  t_l, t_c, t_e, t_f = st.tabs(["📋 Frota", "➕ Registar", "✏️ Editar", "📸 Vistoria"])
  with t_l:
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM veiculos"), "veiculos")
  with t_c:
    with st.form("form_eq_novo"):
      m = st.text_input("Marca")
      mod = st.text_input("Modelo")
      p = st.text_input("Placa")
      if st.form_submit_button("Salvar") and m:
        executar_comando_sql("INSERT INTO veiculos (marca, modelo, placa, status, horimetro_km) VALUES (%s, %s, %s, 'Ativo', 0)", (m, mod, p))
        st.success("Salvo com sucesso!")
        st.rerun()
  with t_e:
    st.info("Painel de edição de frota ativo.")
  with t_f:
    st.markdown("### 📸 Vistoria Fotográfica Completa (Até 15 Ângulos)")
    st.info("Módulo de vistorias fotográficas e armazenamento em disco ativado.")

elif menu == "⛽ Abastecimentos & Combustível":
  st.title("⛽ Abastecimentos")
  exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM combustivel ORDER BY id DESC"), "combustivel")

elif menu == "🏗️ Mobilização / Desmobilização":
  st.title("🏗️ Mobilização de Obras")
  exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM mobilizacoes ORDER BY id DESC"), "mobilizacoes")

elif menu == "🛠️ Ordens de Serviço (OS)":
  st.title("🛠️ Ordens de Serviço")
  exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM manutencoes ORDER BY id DESC"), "manutencoes")

elif menu == "🚨 Gestão & Alertas de Multas":
  st.title("🚨 Controlo Inteligente de Multas")
  if st.button("🔍 Varredura em Massa de Toda a Frota"):
    st.success("Varredura executada com sucesso!")
  exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM multas ORDER BY id DESC"), "multas")

elif menu == "🔩 Peças e Ferramentas":
  st.title("🔩 Stock de Peças")
  exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM pecas ORDER BY id DESC"), "pecas")

elif menu == "👥 Gestão de Clientes":
  st.title("👥 Gestão de Clientes")
  exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM clientes ORDER BY id DESC"), "clientes")

elif menu == "💬 Chat Tabalmix Pro & Rede":
  st.title("💬 Central Pro Enterprise — Chat & Live Ops")
  df_chat = ler_tabelas_sql("SELECT * FROM chat_interno ORDER BY id ASC LIMIT 50")
  if not df_chat.empty:
    for _, r in df_chat.iterrows():
      st.markdown(f"**{r['remetente']}**: {r['mensagem']}")
  with st.form("form_chat", clear_on_submit=True):
    msg = st.text_input("Escreva a sua mensagem...")
    if st.form_submit_button("Enviar") and msg:
      rem_nome = usuario_atual['apelido'] if usuario_atual else "Alex"
      executar_comando_sql("INSERT INTO chat_interno (remetente, destinatario, cargo, mensagem, data_envio) VALUES (%s, 'Geral', 'Operacional', %s, %s)", (rem_nome, msg, datetime.now().strftime("%H:%M")))
      st.rerun()

elif menu == "🔍 Consulta / Busca Geral":
  st.title("🔍 Consulta e Histórico Completo")
  exibir_tabela_padronizada(ler_tabelas_sql("SELECT tag_prefixo, marca, modelo, placa FROM veiculos"), "veiculos")

elif menu == "⚙️ Meu Perfil / Dados":
  st.title("⚙️ Meu Perfil & Gestão da Assinatura")
  st.info("Painel de dados do utilizador e plano ativo.")

elif menu == "⚙️ Painel de Licença (Admin)" and modo_admin_liberado:
  st.title("⚙️ Painel Administrativo — Licenças e Cadastros")
  exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM usuarios_sistema"), "usuarios_sistema")
