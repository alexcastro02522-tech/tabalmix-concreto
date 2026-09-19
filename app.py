from datetime import datetime, timedelta
import base64
import csv
import glob
import io
import os
import random
import sqlite3
import string
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
try:
  sdk_mp = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
except Exception:
  sdk_mp = None

# Configuração da Página
st.set_page_config(
    page_title="Tabalmix Concreto - Enterprise Fleet & Operations Pro X",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ESTILIZAÇÃO VISUAL PREMIUM ENTERPRISE ORIGINAL
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 100% !important;
    }
    
    [data-testid="stSidebar"] {
        min-width: 310px !important;
        width: 310px !important;
        background: #f8fafc !important;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #1e293b !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
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
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #334155 !important;
        font-weight: 600;
        font-size: 13.5px;
        padding: 11px 16px;
        border-radius: 12px;
        background: #ffffff !important;
        margin-bottom: 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.01);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: #ecfdf5 !important;
        border-color: #059669;
        color: #047857 !important;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(5,150,105,0.08);
    }
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 5px solid #059669 !important;
        padding: 18px !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04);
    }
    div[data-testid="stMetric"] label {
        color: #64748b !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 26px !important;
        font-weight: 800 !important;
    }
    div.stTextInput > div > div > input, 
    div.stNumberInput > div > div > input, 
    div.stSelectbox > div > div > div,
    div.stTextArea > div > div > textarea,
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        min-height: 44px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    div.stTextInput > div > div > input:focus, 
    div.stNumberInput > div > div > input:focus,
    div.stTextArea > div > div > textarea:focus {
        border-color: #059669 !important;
        box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15) !important;
    }
    div[data-testid="stDataFrame"], .stDataFrame {
        background-color: #ffffff !important;
        border-radius: 16px;
        padding: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 30px -5px rgba(0,0,0,0.04);
    }
    .stButton button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: white !important;
        font-weight: 700;
        border-radius: 12px;
        border: none;
        padding: 0.65rem 1.8rem;
        box-shadow: 0 6px 16px rgba(5, 150, 105, 0.3);
        transition: all 0.25s ease-in-out;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #047857 100%, #065f46 100%) !important;
        box-shadow: 0 8px 22px rgba(5, 150, 105, 0.45);
        transform: translateY(-2px);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e2e8f0;
        padding: 6px;
        border-radius: 14px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 10px;
        color: #334155;
        font-weight: 600;
        font-size: 13px;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #047857 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    </style>
""",
    unsafe_allow_html=True,
)


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
  c.drawString(
      margem_esq,
      altura - 48,
      "relatório executivo certificado | powered by castro tech",
  )

  c.setFillColorRGB(0.1, 0.1, 0.1)
  c.setFont("Helvetica-Bold", 14)
  c.drawString(margem_esq, altura - 95, titulo)
  c.setFont("Helvetica", 9)
  c.setFillColorRGB(0.4, 0.4, 0.4)
  c.drawString(
      margem_esq,
      altura - 112,
      f"gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
  )

  c.setStrokeColorRGB(0.8, 0.8, 0.8)
  c.setLineWidth(1)
  c.line(margem_esq, altura - 120, largura - margem_esq, altura - 120)

  y = altura - 145
  altura_linha = 22
  colunas = list(dataframe.columns)
  colunas_amigables = [
      str(col).replace("_", " ").upper() for col in colunas[:6]
  ]

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
      c.drawString(
          margem_esq + (i * largura_coluna) + 4, y + 3, valor_celula[:16]
      )
    c.setStrokeColorRGB(0.88, 0.9, 0.88)
    c.line(margem_esq, y - 4, largura - margem_esq, y - 4)
    y -= altura_linha

  c.save()
  buffer.seek(0)
  return buffer


def init_db():
  conn = sqlite3.connect("frota_profissional.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_prefixo TEXT, categoria_equipamento TEXT,
            marca TEXT, modelo TEXT, ano INTEGER, chassi TEXT, renavam TEXT,
            placa TEXT, crv TEXT, cor TEXT, combustivel TEXT, empresa TEXT,
            horimetro_km INTEGER, status TEXT
        )
    """)

  for col_sql in [
      "ALTER TABLE veiculos ADD COLUMN categoria_equipamento TEXT",
      "ALTER TABLE veiculos ADD COLUMN chassi TEXT",
      "ALTER TABLE veiculos ADD COLUMN renavam TEXT",
      "ALTER TABLE veiculos ADD COLUMN crv TEXT",
      "ALTER TABLE veiculos ADD COLUMN cor TEXT",
      "ALTER TABLE veiculos ADD COLUMN combustivel TEXT",
      "ALTER TABLE veiculos ADD COLUMN empresa TEXT",
  ]:
    try:
      cursor.execute(col_sql)
    except Exception:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS manutencoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_prefixo TEXT, tipo_manutencao TEXT, horimetro_km_manut TEXT,
            origem_falha TEXT, descricao_problema TEXT, data_abertura TEXT,
            hora_abertura TEXT, pecas_utilizadas TEXT, custo_pecas REAL,
            mao_de_obra REAL, custo REAL, oficina TEXT, tecnico_mecanico TEXT,
            data_fechamento TEXT, hora_fechamento TEXT, status_os TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pecas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_item TEXT, categoria TEXT, quantidade INTEGER, valor_unitario REAL
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, empresa TEXT, telefone TEXT, documento TEXT, email TEXT, endereco TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS mobilizacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento TEXT, tipo_movimento TEXT, destino_origem TEXT,
            responsavel TEXT, data TEXT, horimetro_km_mov TEXT,
            motivo_condicao TEXT, observacao TEXT, foto_checklist TEXT,
            historico_edicoes TEXT
        )
    """)
  for col_mob in [
      "ALTER TABLE mobilizacoes ADD COLUMN foto_checklist TEXT",
      "ALTER TABLE mobilizacoes ADD COLUMN historico_edicoes TEXT",
  ]:
    try:
      cursor.execute(col_mob)
    except Exception:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS combustivel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipamento TEXT, litros REAL, valor_total REAL,
            km_horimetro TEXT, posto_posto TEXT, motorista TEXT, data TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT, cpf TEXT, email TEXT UNIQUE, senha TEXT,
            celular_seguranca TEXT, status_assinatura TEXT, plano_atual TEXT,
            data_cadastro TEXT, pin_rapido TEXT, apelido TEXT, cargo_setor TEXT
        )
    """)
  for col_user in [
      "ALTER TABLE usuarios_sistema ADD COLUMN apelido TEXT",
      "ALTER TABLE usuarios_sistema ADD COLUMN cargo_setor TEXT",
  ]:
    try:
      cursor.execute(col_user)
    except Exception:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_colunas (
            tabela TEXT PRIMARY KEY,
            ordem_colunas TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_interno (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remetente TEXT,
            destinatario TEXT,
            cargo TEXT,
            mensagem TEXT,
            arquivo_path TEXT,
            arquivo_nome TEXT,
            data_envio TEXT
        )
    """)
  for col_chat_dest in ["ALTER TABLE chat_interno ADD COLUMN destinatario TEXT"]:
    try:
      cursor.execute(col_chat_dest)
    except Exception:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS chaves_licenca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_chave TEXT UNIQUE,
            cargo_atribuido TEXT,
            modalidade TEXT,
            status_uso TEXT,
            usado_por TEXT,
            data_criacao TEXT
        )
    """)

  try:
    cursor.execute(
        "UPDATE usuarios_sistema SET apelido = 'Colaborador' WHERE apelido IS"
        " NULL OR apelido = '' OR apelido = 'None'"
    )
    cursor.execute(
        "UPDATE usuarios_sistema SET cargo_setor = 'Operacional' WHERE"
        " cargo_setor IS NULL OR cargo_setor = '' OR cargo_setor = 'None'"
    )
    conn.commit()
  except Exception:
    pass

  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

# CHAVE SECRETA DE ADMINISTRADOR
modo_admin_liberado = False
try:
  query_params = st.query_params
  if (
      query_params.get("admin") == "tabalmix_master_2026"
      or query_params.get("admin") == ["tabalmix_master_2026"]
      or str(query_params).find("admin=tabalmix_master_2026") != -1
  ):
    modo_admin_liberado = True
  else:
    modo_admin_liberado = False
except Exception:
  modo_admin_liberado = False

if "usuario_logado" not in st.session_state:
  st.session_state["usuario_logado"] = None

# PERSISTÊNCIA INTELIGENTE DE SESSÃO NA OBRA
try:
  if st.session_state["usuario_logado"] is None and not modo_admin_liberado:
    qp = st.query_params
    saved_user_id = qp.get("user_id")
    if saved_user_id:
      cursor.execute(
          "SELECT * FROM usuarios_sistema WHERE id = ?", (saved_user_id,)
      )
      res_persist = cursor.fetchone()
      if res_persist:
        st.session_state["usuario_logado"] = {
            "id": res_persist[0],
            "nome": res_persist[1],
            "cpf": res_persist[2],
            "email": res_persist[3],
            "status": res_persist[6],
            "apelido": (
                res_persist[9]
                if len(res_persist) > 9
                and res_persist[9]
                and res_persist[9] != "None"
                else res_persist[1].split()[0]
            ),
            "cargo": (
                res_persist[10]
                if len(res_persist) > 10
                and res_persist[10]
                and res_persist[10] != "None"
                else "Colaborador"
            ),
        }
except Exception:
  pass

is_gestao_ou_admin = modo_admin_liberado
if st.session_state["usuario_logado"]:
  cargo_colab = str(st.session_state["usuario_logado"].get("cargo", ""))
  if "Diretoria" in cargo_colab or "Gestão" in cargo_colab:
    is_gestao_ou_admin = True

if st.session_state["usuario_logado"] is None and not modo_admin_liberado:
  col_l1, col_l2, col_l3 = st.columns([0.15, 3.7, 0.15])
  with col_l2:
    try:
      with open("caminhoes.jpg", "rb") as image_file:
        encoded_logo_login = base64.b64encode(image_file.read()).decode()
      st.markdown(
          f"""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 24px; padding: 35px; text-align: center; box-shadow: 0 25px 50px rgba(5,150,105,0.25); margin-top: 15px; margin-bottom: 25px; color: white;">
                    <div style="border-radius: 16px; overflow: hidden; max-height: 130px; border: 3px solid rgba(255,255,255,0.8); margin-bottom: 18px; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
                        <img src="data:image/jpeg;base64,{encoded_logo_login}" style="width: 100%; height: 125px; object-fit: cover; display: block;">
                    </div>
                    <div style="display: inline-block; background: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.4); border-radius: 20px; padding: 4px 18px; margin-bottom: 12px;">
                        <span style="color: white; font-size: 11px; font-weight: 800; letter-spacing: 1.5px;">🛡️ PLATAFORMA ENTERPRISE CERTIFICADA</span>
                    </div>
                    <h1 style="color: white !important; margin: 0; font-size: 28px; font-weight: 900; letter-spacing: -0.8px;">tabalmix concreto</h1>
                    <p style="color: #e2e8f0; font-size: 12.5px; margin: 6px 0 2px 0; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;">sistema inteligente de frotas, obras e oficina pro</p>
                    <p style="color: #cbd5e1; font-size: 10px; margin: 0; font-style: italic;">powered by castro tech</p>
                </div>
            """,
          unsafe_allow_html=True,
      )
    except Exception:
      st.markdown(
          """
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 24px; padding: 35px; text-align: center; box-shadow: 0 25px 50px rgba(5,150,105,0.25); margin-top: 15px; margin-bottom: 25px; color: white;">
                    <div style="display: inline-block; background: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.4); border-radius: 20px; padding: 4px 18px; margin-bottom: 12px;">
                        <span style="color: white; font-size: 11px; font-weight: 800; letter-spacing: 1.5px;">🛡️ PLATAFORMA ENTERPRISE CERTIFICADA</span>
                    </div>
                    <h1 style="color: white !important; margin: 0; font-size: 28px; font-weight: 900; letter-spacing: -0.8px;">tabalmix concreto</h1>
                    <p style="color: #e2e8f0; font-size: 12.5px; margin: 6px 0 2px 0; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;">sistema inteligente de frotas, obras e oficina pro</p>
                    <p style="color: #cbd5e1; font-size: 10px; margin: 0; font-style: italic;">powered by castro tech</p>
                </div>
            """,
          unsafe_allow_html=True,
      )

    tab_pin, tab_login, tab_cadastro, tab_chave, tab_recuperar = st.tabs([
        "🔐 pin rápido",
        "🔑 entrar",
        "📝 cadastrar",
        "🎟️ resgatar",
        "🔄 recuperar",
    ])

    with tab_pin:
      with st.form("form_pin"):
        st.markdown("### 🔐 Acesso Rápido com PIN da Obra")
        email_pin = st.text_input("e-mail da conta corporativa")
        pin_dig = st.text_input(
            "pin numérico (4 dígitos)", max_chars=4, type="password"
        )
        btn_pin_sub = st.form_submit_button("entrar com pin")
        if btn_pin_sub:
          cursor.execute(
              "SELECT * FROM usuarios_sistema WHERE email = ? AND pin_rapido ="
              " ?",
              (email_pin, pin_dig),
          )
          user_pin = cursor.fetchone()
          if user_pin:
            st.session_state["usuario_logado"] = {
                "id": user_pin[0],
                "nome": user_pin[1],
                "cpf": user_pin[2],
                "email": user_pin[3],
                "status": user_pin[6],
                "apelido": (
                    user_pin[9]
                    if len(user_pin) > 9 and user_pin[9] != "None"
                    else user_pin[1].split()[0]
                ),
                "cargo": (
                    user_pin[10]
                    if len(user_pin) > 10
                    and user_pin[10]
                    and user_pin[10] != "None"
                    else "Colaborador"
                ),
            }
            try:
              st.query_params["user_id"] = str(user_pin[0])
            except Exception:
              pass
            st.success("✅ login por pin validado!")
            st.rerun()
          else:
            st.error("⚠️ e-mail ou pin inválidos.")

    with tab_login:
      with st.form("form_login"):
        email_login = st.text_input("e-mail corporativo")
        senha_login = st.text_input("senha de acesso", type="password")
        cadastrar_pin = st.text_input(
            "cadastrar pin rápido (4 dígitos - opcional)",
            max_chars=4,
            type="password",
        )
        btn_entrar = st.form_submit_button("entrar no sistema")

        if btn_entrar:
          cursor.execute(
              "SELECT * FROM usuarios_sistema WHERE email = ? AND senha = ?",
              (email_login, senha_login),
          )
          user_data = cursor.fetchone()
          if user_data:
            if cadastrar_pin and len(cadastrar_pin) == 4:
              cursor.execute(
                  "UPDATE usuarios_sistema SET pin_rapido = ? WHERE id = ?",
                  (cadastrar_pin, user_data[0]),
              )
              conn.commit()

            st.session_state["usuario_logado"] = {
                "id": user_data[0],
                "nome": user_data[1],
                "cpf": user_data[2],
                "email": user_data[3],
                "status": user_data[6],
                "apelido": (
                    user_data[9]
                    if len(user_data) > 9 and user_data[9] != "None"
                    else user_data[1].split()[0]
                ),
                "cargo": (
                    user_data[10]
                    if len(user_data) > 10
                    and user_data[10]
                    and user_data[10] != "None"
                    else "Colaborador"
                ),
            }
            try:
              st.query_params["user_id"] = str(user_data[0])
            except Exception:
              pass
            st.success("✅ login realizado com sucesso!")
            st.rerun()
          else:
            st.error("⚠️ e-mail ou senha incorretos.")

    with tab_cadastro:
      with st.form("form_novo_cadastro"):
        c_nome = st.text_input("nome completo")
        c_apelido = st.text_input("primeiro nome ou apelido de guerra")
        c_cargo = st.selectbox(
            "cargo / função na empresa",
            [
                "Diretoria / Gestão",
                "Engenheiro / Gestor de Obra",
                "Mecânico / Oficina",
                "Operador / Motorista / Campo",
            ],
        )

        if "Diretoria" in c_cargo:
          sugestao_preco = (
              "💎 Master Concreto & Diretoria — Mensal: R$ 299,90 | Anual: R$"
              " 2.999,00"
          )
          valor_num = 299.90
        elif "Engenheiro" in c_cargo:
          sugestao_preco = (
              "🏗️ Engenharia & Obra Pro — Mensal: R$ 189,90 | Anual: R$ 1.899,00"
          )
          valor_num = 189.90
        elif "Mecânico" in c_cargo:
          sugestao_preco = (
              "🛠️ Oficina & Mecânica X — Mensal: R$ 119,90 | Anual: R$ 1.199,00"
          )
          valor_num = 119.90
        else:
          sugestao_preco = (
              "🚜 Operacional Campo & Frota — Mensal: R$ 69,90 | Anual: R$"
              " 699,00"
          )
          valor_num = 69.90

        st.info(f"💡 **Plano Sugerido para a Função:**\n\n{sugestao_preco}")

        c_cpf = st.text_input("cpf")
        c_email = st.text_input("e-mail corporativo de login")
        c_senha = st.text_input("criar senha", type="password")
        c_cel = st.text_input("celular / whatsapp")
        c_vigencia = st.selectbox(
            "modalidade de vigência",
            ["Plano Mensal (30 dias)", "Plano Anual (365 dias)"],
        )
        btn_cadastrar = st.form_submit_button(
            "cadastrar e prosseguir para pagamento"
        )

        if btn_cadastrar:
          if c_nome and c_email and c_senha:
            apelido_final = (
                c_apelido.strip()
                if c_apelido and c_apelido.strip() and c_apelido != "None"
                else c_nome.split()[0]
            )
            plano_completo_str = f"{c_cargo} — {c_vigencia}"
            try:
              cursor.execute(
                  "INSERT INTO usuarios_sistema (nome_completo, cpf, email,"
                  " senha, celular_seguranca, status_assinatura, plano_atual,"
                  " data_cadastro, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?,"
                  " 'Inativo', ?, ?, ?, ?)",
                  (
                      c_nome,
                      c_cpf,
                      c_email,
                      c_senha,
                      c_cel,
                      plano_completo_str,
                      datetime.now().strftime("%Y-%m-%d %H:%M"),
                      apelido_final,
                      c_cargo,
                  ),
              )
              conn.commit()
              st.success(
                  "✅ Conta cadastrada com sucesso! Podes efetuar o pagamento"
                  " abaixo ou inserir uma chave de ativação."
              )
            except Exception as e:
              st.error(f"⚠️ erro ao cadastrar (e-mail já cadastrado?): {e}")
          else:
            st.error("⚠️ preencha os campos obrigatórios.")

      st.markdown("---")
      st.markdown("### 💳 Pagamento Automático (Pix ou Cartão via Mercado Pago)")
      if st.button("Gerar Pagamento Mercado Pago"):
        if sdk_mp:
          try:
            preference_data = {
                "items": [{
                    "title": "Assinatura Tabalmix Concreto",
                    "quantity": 1,
                    "unit_price": float(
                        valor_num if "valor_num" in locals() else 69.90
                    ),
                }],
                "back_urls": {
                    "success": "https://tabalmix-concreto.streamlit.app/",
                    "failure": "https://tabalmix-concreto.streamlit.app/",
                },
            }
            preference_response = sdk_mp.preference().create(preference_data)
            link_pagamento = preference_response["response"].get(
                "init_point", "#"
            )
            st.markdown(
                f"🔗 **[Clique aqui para abrir o checkout seguro do Mercado"
                f" Pago]({link_pagamento})**",
                unsafe_allow_html=True,
            )
          except Exception as ex:
            st.error(
                f"⚠️ Erro ao gerar link de pagamento: {ex}. Podes usar uma"
                " chave de ativação."
            )
        else:
          st.error("⚠️ SDK do Mercado Pago não configurado.")

    with tab_chave:
      with st.form("form_resgatar_chave_login"):
        st.markdown("### 🎟️ Ativar Conta com Chave Corporativa")
        email_resgate = st.text_input("e-mail cadastrado na conta")
        chave_digitada = st.text_input(
            "chave de ativação (ex: TABALMIX-XXXX-XXXX)"
        )
        btn_ativar_chave = st.form_submit_button("ativar acesso com chave")

        if btn_ativar_chave:
          cursor.execute(
              "SELECT id, cargo_atribuido, modalidade, status_uso FROM"
              " chaves_licenca WHERE codigo_chave = ?",
              (chave_digitada.strip(),),
          )
          chave_db = cursor.fetchone()
          if chave_db:
            id_c, cargo_c, mod_c, status_c = chave_db
            if status_c == "Utilizada":
              st.warning("⚠️ Esta chave já foi utilizada por outro usuário.")
            else:
              cursor.execute(
                  "SELECT id FROM usuarios_sistema WHERE email = ?",
                  (email_resgate.strip(),),
              )
              user_db = cursor.fetchone()
              if user_db:
                id_u = user_db[0]
                plano_final = f"{cargo_c} — {mod_c}"
                cursor.execute(
                    "UPDATE usuarios_sistema SET status_assinatura = 'Ativo',"
                    " cargo_setor = ?, plano_atual = ?, data_cadastro = ? WHERE"
                    " id = ?",
                    (
                        cargo_c,
                        plano_final,
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        id_u,
                    ),
                )
                cursor.execute(
                    "UPDATE chaves_licenca SET status_uso = 'Utilizada',"
                    " usado_por = ? WHERE id = ?",
                    (email_resgate.strip(), id_c),
                )
                conn.commit()
                st.success(
                    "🎉 **Parabéns! Sua conta foi ativada com sucesso.**"
                    " Faça login na aba 'entrar'."
                )
              else:
                st.error("⚠️ E-mail não encontrado no sistema.")
          else:
            st.error("⚠️ Chave de ativação inválida.")

    with tab_recuperar:
      with st.form("form_recuperar"):
        rec_email = st.text_input("digite seu e-mail cadastrado")
        btn_rec = st.form_submit_button("consultar senha")
        if btn_rec:
          cursor.execute(
              "SELECT senha, nome_completo FROM usuarios_sistema WHERE email ="
              " ?",
              (rec_email,),
          )
          res_rec = cursor.fetchone()
          if res_rec:
            st.info(
                f"👤 olá, {res_rec[1]}. sua senha cadastrada é: **{res_rec[0]}**"
            )
          else:
            st.error("⚠️ e-mail não encontrado.")

  st.stop()

usuario_atual = st.session_state["usuario_logado"]
status_usuario_ativo = (
    True
    if modo_admin_liberado
    else (
        str(usuario_atual.get("status", "Ativo")).strip().lower() == "ativo"
        if usuario_atual
        else False
    )
)

if usuario_atual and (
    not usuario_atual.get("apelido") or usuario_atual["apelido"] == "None"
):
  usuario_atual["apelido"] = usuario_atual["nome"].split()[0]
if usuario_atual and (
    not usuario_atual.get("cargo") or usuario_atual["cargo"] == "None"
):
  usuario_atual["cargo"] = "Colaborador"


def exibir_tabela_padronizada(df, nome_tabela):
  if df.empty:
    st.info("nenhum registro encontrado.")
    return

  cursor.execute(
      "SELECT ordem_colunas FROM config_colunas WHERE tabela = ?",
      (nome_tabela,),
  )
  res_ordem = cursor.fetchone()
  cols_atuais = list(df.columns)

  if res_ordem and res_ordem[0]:
    cols_salvas = res_ordem[0].split(",")
    cols_finais = [c for c in cols_salvas if c in cols_atuais]
    if cols_finais:
      df = df[cols_finais]

  if is_gestao_ou_admin:
    with st.expander(
        f"⚙️ [DIRETORIA] Gerir Colunas e Registos ({nome_tabela})", expanded=False
    ):
      colunas_selecionadas_pelo_admin = st.multiselect(
          "Colunas ativas:",
          options=cols_atuais,
          default=(
              cols_finais
              if "cols_finais" in locals() and cols_finais
              else cols_atuais
          ),
          key=f"sel_cols_diretoria_{nome_tabela}",
      )
      if st.button(
          "💾 Salvar Colunas", key=f"btn_salvar_cols_{nome_tabela}"
      ):
        if colunas_selecionadas_pelo_admin:
          ordem_str = ",".join(colunas_selecionadas_pelo_admin)
          cursor.execute(
              "INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas)"
              " VALUES (?, ?)",
              (nome_tabela, ordem_str),
          )
          conn.commit()
          st.success("✅ Configuração de colunas salva com sucesso!")
          st.rerun()
        else:
          st.warning("⚠️ Selecione pelo menos uma coluna.")

      if "id" in df.columns:
        st.markdown("---")
        id_para_excluir = st.selectbox(
            "Seleciona o ID exato para excluir:",
            df["id"].tolist(),
            key=f"sel_exc_diretoria_{nome_tabela}",
        )
        if st.button(
            "🗑️ Excluir Registo Selecionado",
            key=f"btn_exc_diretoria_{nome_tabela}",
        ):
          tabela_sql = (
              "veiculos"
              if "veiculo" in nome_tabela.lower() or nome_tabela == "veiculos"
              else (
                  "manutencoes"
                  if "manutencao" in nome_tabela.lower()
                  else (
                      "mobilizacoes"
                      if "mobilizacao" in nome_tabela.lower()
                      else (
                          "combustivel"
                          if "combustivel" in nome_tabela.lower()
                          else (
                              "pecas"
                              if "peca" in nome_tabela.lower()
                              else (
                                  "clientes"
                                  if "cliente" in nome_tabela.lower()
                                  else ""
                              )
                          )
                      )
                  )
              )
          )
          if tabela_sql:
            cursor.execute(
                f"DELETE FROM {tabela_sql} WHERE id = ?", (id_para_excluir,)
            )
            conn.commit()
            st.success("✅ Registo excluído com sucesso!")
            st.rerun()

  st.dataframe(df, use_container_width=True, hide_index=True, column_config={})


with st.sidebar:
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_logo_side = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 16px; padding: 14px; text-align: center; margin-top: 0px; margin-bottom: 12px; box-shadow: 0 10px 25px rgba(5,150,105,0.2); color: white;">
                <div style="font-size: 15px; font-weight: 900; letter-spacing: -0.5px; margin-bottom: 8px; color: white;">🏗️ TABALMIX CONCRETO</div>
                <div style="border-radius: 12px; overflow: hidden; max-height: 105px; border: 2px solid rgba(255,255,255,0.8); margin-bottom: 8px; box-shadow: 0 6px 15px rgba(0,0,0,0.15);">
                    <img src="data:image/jpeg;base64,{encoded_logo_side}" style="width: 100%; height: 100px; object-fit: cover; display: block;">
                </div>
                <div style="background: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.4); border-radius: 10px; padding: 5px; text-align: center;">
                    <span style="color: white; font-size: 10px; font-weight: 800; letter-spacing: 0.8px;">🛡️ SELO DE GARANTIA ENTERPRISE</span>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.markdown(
        """
            <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 16px; padding: 14px; text-align: center; margin-top: 0px; margin-bottom: 12px; box-shadow: 0 10px 25px rgba(5,150,105,0.2); color: white;">
                <div style="font-size: 15px; font-weight: 900; letter-spacing: -0.5px; margin-bottom: 8px; color: white;">🏗️ TABALMIX CONCRETO</div>
                <div style="background: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.4); border-radius: 10px; padding: 6px; text-align: center;">
                    <span style="color: white; font-size: 10.5px; font-weight: 800; letter-spacing: 0.8px;">🛡️ SELO DE GARANTIA ENTERPRISE</span>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  if modo_admin_liberado:
    st.success("🔓 **modo admin enterprise ativo**")
  elif usuario_atual:
    st.markdown(
        f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                <p style="margin: 0; font-weight: bold; color: #0f172a; font-size: 14px;">👤 {usuario_atual['apelido']}</p>
                <p style="margin: 3px 0 4px 0; font-size: 11.5px; color: #047857; font-weight: 700;">{usuario_atual['cargo']}</p>
                <span style="color: #059669; font-weight: bold; font-size: 11px; background: #ecfdf5; padding: 2px 8px; border-radius: 6px; display: inline-block;">🟢 Sessão Fixa na Obra</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if not status_usuario_ativo:
      st.warning(
          "⚠️ **conta inativa:** insira uma chave de ativação válida ou efetue"
          " o pagamento."
      )
    if st.button("🚪 encerrar sessão"):
      st.session_state["usuario_logado"] = None
      try:
        st.query_params.clear()
      except Exception:
        pass
      st.rerun()
  st.markdown("---")

lista_menus = [
    "📊 visão geral",
    "🚜 cadastro de equipamentos",
    "⛽ abastecimentos & combustível",
    "🏗️ mobilização / desmobilização",
    "🛠️ ordens de serviço (os)",
    "🔩 peças e ferramentas",
    "👥 gestão de clientes",
    "💬 chat tabalmix pro & rede",
    "🔍 consulta / busca geral",
    "⚙️ meu perfil / dados",
]

if modo_admin_liberado:
  lista_menus.append("⚙️ painel de licença (admin)")

menu = st.sidebar.radio("navegação", lista_menus, label_visibility="collapsed")

if menu == "📊 visão geral":
  st.title("🏗️ painel executivo e indicadores de frota")
  df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_veiculos.empty and "tag_prefixo" in df_veiculos.columns:
    df_veiculos["tag_prefixo"] = df_veiculos["tag_prefixo"].fillna(
        "NÃO INFORMADO"
    )

  df_manut = pd.read_sql("SELECT * FROM manutencoes", conn)
  df_comb = pd.read_sql("SELECT * FROM combustivel", conn)

  total_frota = len(df_veiculos)
  custo_total_manut = (
      df_manut["custo"].sum()
      if not df_manut.empty and "custo" in df_manut.columns
      else 0.0
  )
  gasto_total_comb = (
      df_comb["valor_total"].sum() if not df_comb.empty else 0.0
  )
  litros_totais = df_comb["litros"].sum() if not df_comb.empty else 0.0

  os_abertas = (
      len(df_manut[df_manut["status_os"] == "aberta"])
      if not df_manut.empty and "status_os" in df_manut.columns
      else 0
  )

  col1, col2, col3, col4, col5 = st.columns(5)
  with col1:
    st.metric("total frota", total_frota)
  with col2:
    st.metric("os abertas", os_abertas)
  with col3:
    st.metric("custo manut.", f"r$ {custo_total_manut:,.2f}")
  with col4:
    st.metric("gasto combust.", f"r$ {gasto_total_comb:,.2f}")
  with col5:
    st.metric("total litros", f"{litros_totais:,.1f} L")

  st.divider()

  col_exp1, col_exp2 = st.columns([3, 1])
  with col_exp1:
    st.subheader("📋 listagem geral de equipamentos")
  with col_exp2:
    if not df_veiculos.empty and (status_usuario_ativo or modo_admin_liberado):
      pdf_buf = gerar_pdf_relatorio(
          "Relatório Consolidado da Frota - Tabalmix", df_veiculos
      )
      st.download_button(
          "📥 exportar relatório pdf",
          pdf_buf,
          file_name="relatorio_frota.pdf",
          mime="application/pdf",
      )

  if not df_veiculos.empty:
    exibir_tabela_padronizada(df_veiculos, "veiculos")
  else:
    st.info("nenhum equipamento cadastrado na frota.")

elif menu == "🚜 cadastro de equipamentos":
  st.title("🚜 cadastro limpo de equipamentos e frota")
  with st.form("form_frota", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
      tag_prefixo = st.text_input("tag / prefixo (ex: EQ-001 / BET-12)")
      categoria_equipamento = st.text_input("categoria do equipamento")
      marca = st.text_input("marca")
      modelo = st.text_input("modelo")
      ano = st.number_input(
          "ano de fabricação", min_value=1950, value=2024, step=1
      )
      chassi = st.text_input("número do chassi")
      renavam = st.text_input("número do renavam")
    with col2:
      placa = st.text_input("placa do veículo")
      crv = st.text_input("número do crv")
      cor = st.text_input("cor principal")
      combustivel = st.selectbox(
          "tipo de combustível",
          ["Diesel S10", "Diesel S500", "Gasolina", "Flex", "Elétrico"],
      )
      empresa = st.text_input("empresa / filial responsável")
      horimetro_km = st.number_input(
          "horímetro ou km inicial", min_value=0, value=15000, step=100
      )
      status = st.selectbox(
          "situação operacional",
          ["Ativo", "Em Manutenção", "Parado", "Mobilizado"],
      )

    btn_cad_eq = st.form_submit_button("cadastrar equipamento limpo")
    if btn_cad_eq and modelo:
      tag_final = (
          tag_prefixo.upper()
          if tag_prefixo and tag_prefixo.strip()
          else "EQ-00" + str(datetime.now().microsecond)[:3]
      )
      cursor.execute(
          "INSERT INTO veiculos (tag_prefixo, categoria_equipamento, marca,"
          " modelo, ano, chassi, renavam, placa, crv, cor, combustivel,"
          " empresa, horimetro_km, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,"
          " ?, ?, ?, ?, ?)",
          (
              tag_final,
              categoria_equipamento,
              marca,
              modelo,
              int(ano),
              chassi.upper(),
              renavam,
              placa.upper(),
              crv,
              cor,
              combustivel,
              empresa,
              int(horimetro_km),
              status,
          ),
      )
      conn.commit()
      st.success(f"✅ Equipamento '{tag_final}' cadastrado com sucesso!")
      st.rerun()

  df_f = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_f.empty:
    exibir_tabela_padronizada(df_f, "veiculos")

elif menu == "⛽ abastecimentos & combustível":
  st.title("⛽ controle de abastecimento e combustível")
  df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  tags_comb = (
      df_v["tag_prefixo"].dropna().tolist() if not df_v.empty else []
  )
  with st.form("form_comb"):
    c1, c2 = st.columns(2)
    with c1:
      eq_comb = st.selectbox(
          "equipamento / tag", tags_comb if tags_comb else ["MANUAL"]
      )
      litros = st.number_input("litros", min_value=0.1, value=100.0)
      val_tot = st.number_input("valor total (r$)", min_value=0.0, value=600.0)
    with c2:
      km_h = st.text_input("km ou horímetro")
      posto = st.text_input("posto / fornecedor")
      motorista = st.text_input("motorista / responsável")
      dt_ab = st.date_input("data")
    btn_cad_comb = st.form_submit_button("registrar abastecimento")
    if btn_cad_comb:
      cursor.execute(
          "INSERT INTO combustivel (equipamento, litros, valor_total,"
          " km_horimetro, posto_posto, motorista, data) VALUES (?, ?, ?, ?, ?, ?,"
          " ?)",
          (
              str(eq_comb).upper(),
              float(litros),
              float(val_tot),
              str(km_h),
              posto,
              motorista,
              str(dt_ab),
          ),
      )
      conn.commit()
      st.success("✅ abastecimento registrado!")
      st.rerun()

  df_c = pd.read_sql("SELECT * FROM combustivel", conn)
  if not df_c.empty:
    exibir_tabela_padronizada(df_c, "combustivel")

elif menu == "🏗️ mobilização / desmobilização":
  st.title("🏗️ mobilização e desmobilização de obras")
  with st.form("form_mob"):
    c1, c2 = st.columns(2)
    with c1:
      eq_mob = st.text_input("equipamento / tag (ex: EQ-001)")
      tipo_mov = st.selectbox(
          "movimentação",
          [
              "mobilização (envio)",
              "desmobilização (retorno)",
              "remanejamento",
          ],
      )
      destino = st.text_input("obra / destino-origem")
    with c2:
      resp = st.text_input("responsável / motorista")
      dt_mob = st.date_input("data")
      obs = st.text_input("observação")

    fotos_subidas = st.file_uploader(
        "📷 anexar fotos do check-list",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    btn_cad_mob = st.form_submit_button("registrar movimentação")
    if btn_cad_mob:
      caminhos_fotos = []
      if fotos_subidas:
        os.makedirs("uploads_checklists", exist_ok=True)
        for f_item in fotos_subidas[:15]:
          nome_f = (
              "uploads_checklists/"
              f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{f_item.name}"
          )
          with open(nome_f, "wb") as f_out:
            f_out.write(f_item.getbuffer())
          caminhos_fotos.append(nome_f)

      paths_str = "|".join(caminhos_fotos)
      hist_inicial = (
          f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Criado por"
          f" {resp} — Destino: {destino}"
      )
      cursor.execute(
          "INSERT INTO mobilizacoes (equipamento, tipo_movimento,"
          " destino_origem, responsavel, data, observacao, foto_checklist,"
          " historico_edicoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
          (
              str(eq_mob).upper(),
              tipo_mov,
              destino,
              resp,
              str(dt_mob),
              obs,
              paths_str,
              hist_inicial,
          ),
      )
      conn.commit()
      st.success("✅ movimentação registrada!")
      st.rerun()

  df_mobs = pd.read_sql("SELECT * FROM mobilizacoes", conn)
  if not df_mobs.empty:
    exibir_tabela_padronizada(df_mobs, "mobilizacoes")

elif menu == "🛠️ ordens de serviço (os)":
  st.title("🛠️ gestão unificada de ordens de serviço (os)")
  df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  tags_disponiveis = (
      df_v["tag_prefixo"].dropna().tolist() if not df_v.empty else []
  )

  st.markdown("### 🟢 abertura de nova os")
  with st.form("form_abertura_os", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
      tag_os = st.selectbox(
          "tag / prefixo", tags_disponiveis if tags_disponiveis else ["GERAL"]
      )
      tipo_manut = st.selectbox(
          "tipo", ["preventiva", "corretiva", "preditiva", "revisão geral"]
      )
      horimetro_ab = st.text_input("horímetro / km")
      origem_f = st.selectbox("origem", ["operação", "máquina"])
    with c2:
      data_ab = st.date_input("data", value=datetime.now().date())
      hora_ab = st.text_input("hora", value=datetime.now().strftime("%H:%M"))
      desc_prob = st.text_area("descrição do problema")

    btn_abrir_os = st.form_submit_button("abrir nova os")
    if btn_abrir_os:
      cursor.execute(
          "INSERT INTO manutencoes (tag_prefixo, tipo_manutencao,"
          " horimetro_km_manut, origem_falha, descricao_problema,"
          " data_abertura, hora_abertura, status_os, custo, custo_pecas,"
          " mao_de_obra) VALUES (?, ?, ?, ?, ?, ?, ?, 'aberta', 0.0, 0.0,"
          " 0.0)",
          (
              str(tag_os).upper(),
              tipo_manut,
              horimetro_ab,
              origem_f,
              desc_prob,
              str(data_ab),
              hora_ab,
          ),
      )
      conn.commit()
      st.success("✅ OS aberta com sucesso!")
      st.rerun()

  df_os = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_os.empty:
    exibir_tabela_padronizada(df_os, "manutencoes")

elif menu == "🔩 peças e ferramentas":
  st.title("🔩 controle de peças e ferramentas")
  with st.form("form_pecas"):
    c1, c2 = st.columns(2)
    with c1:
      nome_i = st.text_input("nome da peça")
      cat = st.text_input("categoria")
    with c2:
      qtd = st.number_input("quantidade", min_value=1, value=1)
      v_unit = st.number_input("valor unitário (r$)", min_value=0.0)
    btn_cad_peca = st.form_submit_button("adicionar peça")
    if btn_cad_peca:
      cursor.execute(
          "INSERT INTO pecas (nome_item, categoria, quantidade,"
          " valor_unitario) VALUES (?, ?, ?, ?)",
          (nome_i, cat.strip() if cat else "Geral", qtd, v_unit),
      )
      conn.commit()
      st.success("✅ Peça adicionada!")
      st.rerun()

  df_p = pd.read_sql("SELECT * FROM pecas", conn)
  if not df_p.empty:
    exibir_tabela_padronizada(df_p, "pecas")

elif menu == "👥 gestão de clientes":
  st.title("👥 gestão de clientes")
  with st.form("form_cli"):
    c1, c2 = st.columns(2)
    with c1:
      nome_c = st.text_input("nome / razão social")
      emp = st.text_input("empresa")
      tel = st.text_input("telefone")
    with c2:
      doc = st.text_input("cpf / cnpj")
      em = st.text_input("e-mail")
      end = st.text_input("endereço")
    btn_cad_cli = st.form_submit_button("salvar cliente")
    if btn_cad_cli:
      cursor.execute(
          "INSERT INTO clientes (nome, empresa, telefone, documento, email,"
          " endereco) VALUES (?, ?, ?, ?, ?, ?)",
          (nome_c, emp, tel, doc, em, end),
      )
      conn.commit()
      st.success("✅ Cliente salvo!")
      st.rerun()

  df_cli = pd.read_sql("SELECT * FROM clientes", conn)
  if not df_cli.empty:
    exibir_tabela_padronizada(df_cli, "clientes")

elif menu == "💬 chat tabalmix pro & rede":
  st.title("💬 Central Pro de Mensagens e Rede Interna")
  st.markdown(
      "Sistema unificado de comunicação: envie mensagens instantâneas e fotos"
      " da obra em tempo real para toda a equipe."
  )

  if usuario_atual:
    cursor.execute(
        "SELECT id, apelido, cargo_setor FROM usuarios_sistema WHERE email != ?",
        (usuario_atual["email"],),
    )
  else:
    cursor.execute("SELECT id, apelido, cargo_setor FROM usuarios_sistema")
  colegas_db = cursor.fetchall()
  lista_nomes_colegas = [f"{c[1]} ({c[2]})" for c in colegas_db]

  tab_chat_txt, tab_videochat = st.tabs([
      "💬 Chat Direto & Fotos",
      "📹 Videoconferência & Chamada de Voz",
  ])

  with tab_chat_txt:
    st.markdown("#### 💬 Conversas Diretas & Envio de Fotos da Obra")

    destinatario_chat = st.selectbox(
        "Enviar mensagem/foto para:",
        ["Geral (Toda a Equipe)"] + lista_nomes_colegas,
    )

    df_msgs = pd.read_sql(
        "SELECT * FROM chat_interno ORDER BY id DESC LIMIT 30", conn
    )
    if not df_msgs.empty:
      for _, row_m in df_msgs.iterrows():
        st.markdown(
            f"""
                <div style="background: #ffffff; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; border: 1px solid #e2e8f0; box-shadow: 0 3px 10px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <b style="color: #047857; font-size: 12.5px;">👤 {row_m['remetente']} ➔ Para: {row_m['destinatario']}</b>
                        <span style="font-size: 10px; color: #64748b;">{row_m['data_envio']}</span>
                    </div>
                    <div style="font-size: 14px; color: #0f172a; white-space: pre-wrap; line-height: 1.4;">{row_m['mensagem']}</div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        if row_m["arquivo_path"] and os.path.exists(str(row_m["arquivo_path"])):
          if row_m["arquivo_nome"].lower().endswith((".png", ".jpg", ".jpeg")):
            st.image(
                row_m["arquivo_path"],
                caption=f"Foto enviada por {row_m['remetente']}",
                use_column_width=True,
            )
          with open(row_m["arquivo_path"], "rb") as f_down:
            st.download_button(
                label=f"📥 Baixar anexo: {row_m['arquivo_nome']}",
                data=f_down.read(),
                file_name=row_m["arquivo_nome"],
                key=f"dl_chat_arq_{row_m['id']}",
            )
    else:
      st.info("Nenhuma mensagem ou foto enviada no chat ainda.")

    remetente_atual = (
        usuario_atual["apelido"] if usuario_atual else "Administrador Master"
    )
    cargo_atual = (
        usuario_atual["cargo"] if usuario_atual else "Diretoria / Gestão"
    )

    with st.form("form_chat_direto", clear_on_submit=True):
      msg_sala_txt = st.text_input("Escreva sua mensagem...")
      file_sala_up = st.file_uploader(
          "Anexar foto da obra ou documento (opcional)",
          type=["png", "jpg", "jpeg", "pdf", "docx"],
      )
      btn_enviar_chat = st.form_submit_button("➤ Enviar para o Colega")

      if btn_enviar_chat:
        if not msg_sala_txt.strip() and not file_sala_up:
          st.warning("⚠️ Digite uma mensagem ou anexe uma foto.")
        else:
          path_s = ""
          nome_s = ""
          if file_sala_up is not None:
            os.makedirs("chat_documentos", exist_ok=True)
            nome_s = file_sala_up.name
            path_s = (
                "chat_documentos/"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome_s}"
            )
            with open(path_s, "wb") as f_out_s:
              f_out_s.write(file_sala_up.getbuffer())

          data_env_s = datetime.now().strftime("%d/%m às %H:%M")
          cursor.execute(
              "INSERT INTO chat_interno (remetente, destinatario, cargo,"
              " mensagem, arquivo_path, arquivo_nome, data_envio) VALUES (?, ?,"
              " ?, ?, ?, ?, ?)",
              (
                  f"{remetente_atual} ({cargo_atual})",
                  destinatario_chat,
                  cargo_atual,
                  msg_sala_txt,
                  path_s,
                  nome_s,
                  data_env_s,
              ),
          )
          conn.commit()
          st.success("✅ Mensagem/Foto enviada com sucesso!")
          st.rerun()

  with tab_videochat:
    st.markdown("### 📹 Sala de Videoconferência & Chamada de Voz ao Vivo")
    st.markdown(
        "Clica no botão abaixo para abrir a sala segura de vídeo e áudio em"
        " tempo real com a equipa (compatível com telemóvel e PC):"
    )
    url_sala_jitsi = (
        "https://meet.jit.si/TabalmixConcretoEnterpriseSalaOficial2026"
    )
    st.markdown(
        f"""
            <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%); border-radius: 16px; padding: 25px; text-align: center; color: white; box-shadow: 0 10px 25px rgba(5,150,105,0.3); margin-top: 15px;">
                <h2 style="color: white !important; margin-bottom: 10px;">🔴 Sala de Vídeo e Áudio Ativa</h2>
                <p style="font-size: 14px; margin-bottom: 20px;">fale diretamente com os operadores, motoristas e engenheiros da obra por voz e câmara.</p>
                <a href="{url_sala_jitsi}" target="_blank" style="background: white; color: #047857; padding: 12px 28px; border-radius: 12px; font-weight: 800; text-decoration: none; font-size: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: inline-block;">🎥 ENTRAR NA VIDEOLLAMADA AGORA</a>
            </div>
        """,
        unsafe_allow_html=True,
    )

elif menu == "🔍 consulta / busca geral":
  st.title("🔍 consulta e histórico completo do equipamento")
  df_v_busca = pd.read_sql(
      "SELECT tag_prefixo, modelo, placa FROM veiculos", conn
  )
  lista_tags = (
      df_v_busca["tag_prefixo"].dropna().tolist()
      if not df_v_busca.empty
      else []
  )
  if lista_tags:
    eq_sel = st.selectbox("selecione a tag/prefixo", lista_tags)
    if eq_sel:
      df_eq_info = df_v_busca[df_v_busca["tag_prefixo"] == eq_sel]
      exibir_tabela_padronizada(df_eq_info, "busca_eq_info")

elif menu == "⚙️ meu perfil / dados":
  st.title("⚙️ Meu Perfil & Credenciais Corporativas")
  if usuario_atual:
    user_id_ativo = usuario_atual.get("id")
    cursor.execute(
        "SELECT nome_completo, cpf, email, celular_seguranca, apelido,"
        " cargo_setor, pin_rapido, status_assinatura, plano_atual,"
        " data_cadastro FROM usuarios_sistema WHERE id = ?",
        (user_id_ativo,),
    )
    dados_db = cursor.fetchone()
    if dados_db:
      (
          n_comp,
          n_cpf,
          n_email,
          n_cel,
          n_apelido,
          n_cargo,
          n_pin,
          st_assinatura,
          plano_atual,
          dt_cad,
      ) = dados_db

      cargo_str = str(n_cargo) if n_cargo else "Operacional"
      if "Diretoria" in cargo_str or "Gestão" in cargo_str:
        nome_plano_comercial = "💎 Master Concreto & Diretoria"
        valor_mensal_ref = "R$ 299,90 / mês"
        valor_anual_ref = "R$ 2.999,00 / ano"
      elif "Engenheiro" in cargo_str:
        nome_plano_comercial = "🏗️ Engenharia & Obra Pro"
        valor_mensal_ref = "R$ 189,90 / mês"
        valor_anual_ref = "R$ 1.899,00 / ano"
      elif "Mecânico" in cargo_str:
        nome_plano_comercial = "🛠️ Oficina & Mecânica X"
        valor_mensal_ref = "R$ 119,90 / mês"
        valor_anual_ref = "R$ 1.199,00 / ano"
      else:
        nome_plano_comercial = "🚜 Operacional Campo & Frota"
        valor_mensal_ref = "R$ 69,90 / mês"
        valor_anual_ref = "R$ 699,00 / ano"

      dias_restantes = "Ativo"
      try:
        if dt_cad:
          data_inicio = datetime.strptime(dt_cad[:10], "%Y-%m-%d")
          dias_decorridos = (datetime.now() - data_inicio).days
          limite_dias = 365 if "Anual" in str(plano_atual) else 30
          dias_restantes = max(0, limite_dias - dias_decorridos)
      except Exception:
        dias_restantes = "30"

      st.markdown(
          f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
                    <h3 style="margin-top: 0; color: #047857; font-size: 18px;">💳 Licença e Categoria de Acesso na Obra</h3>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Perfil / Cargo:</b> {n_cargo}</p>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Plano Atribuído:</b> <span style="color: #059669; font-weight: bold;">{nome_plano_comercial}</span></p>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Valores de Referência:</b> Mensal ({valor_mensal_ref}) | Anual ({valor_anual_ref})</p>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Modalidade Atual:</b> {plano_atual if plano_atual else 'Plano Mensal'}</p>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Dias Restantes para Renovação:</b> <span style="color: #2563eb; font-weight: bold; font-size: 16px;">{dias_restantes} dias</span></p>
                </div>
            """,
          unsafe_allow_html=True,
      )

      with st.form("form_atualizar_meu_perfil"):
        novo_nome = st.text_input("Nome Completo", value=n_comp or "")
        novo_apelido = st.text_input("Apelido de Guerra", value=n_apelido or "")
        novo_cel = st.text_input("Celular / WhatsApp", value=n_cel or "")
        btn_salvar_perfil = st.form_submit_button("💾 Salvar Alterações")
        if btn_salvar_perfil and novo_nome:
          cursor.execute(
              "UPDATE usuarios_sistema SET nome_completo = ?, apelido = ?,"
              " celular_seguranca = ? WHERE id = ?",
              (novo_nome, novo_apelido, novo_cel, user_id_ativo),
          )
          conn.commit()
          st.success("✅ Perfil atualizado com sucesso!")
          st.rerun()
  else:
    st.info(
        "🔓 Estás logado como Administrador Master. As tuas credenciais de"
        " gestão são geridas pelo link de acesso seguro."
    )

elif menu == "⚙️ painel de licença (admin)" and modo_admin_liberado:
  st.title("⚙️ Painel Administrativo de Chaves & Licenças Corporativas")
  st.markdown(
      "Gere chaves de ativação em lote para a empresa ou gerencie os acessos"
      " dos colaboradores."
  )

  tab_gerar_chaves, tab_ver_chaves, tab_gerenciar_users = st.tabs([
      "🎟️ Gerar Chaves em Lote",
      "📋 Chaves Geradas",
      "👥 Gerenciar Colaboradores",
  ])

  with tab_gerar_chaves:
    with st.form("form_gerar_chaves_lote"):
      st.markdown("### 🔑 Gerador de Chaves de Ativação")
      qtd_chaves = st.number_input(
          "Quantidade de chaves a gerar", min_value=1, max_value=50, value=5
      )
      cargo_chave = st.selectbox(
          "Cargo / Função associada à chave",
          [
              "Diretoria / Gestão",
              "Engenheiro / Gestor de Obra",
              "Mecânico / Oficina",
              "Operador / Motorista / Campo",
          ],
      )
      modalidade_chave = st.selectbox(
          "Modalidade da Licença",
          ["Plano Mensal (30 dias)", "Plano Anual (365 dias)"],
      )
      btn_gerar_lote = st.form_submit_button("🚀 Gerar Lote de Chaves")

      if btn_gerar_lote:
        chaves_criadas = []
        for _ in range(int(qtd_chaves)):
          parte1 = "".join(
              random.choices(string.ascii_uppercase + string.digits, k=4)
          )
          parte2 = "".join(
              random.choices(string.ascii_uppercase + string.digits, k=4)
          )
          codigo = f"TABALMIX-{parte1}-{parte2}"
          try:
            cursor.execute(
                "INSERT INTO chaves_licenca (codigo_chave, cargo_atribuido,"
                " modalidade, status_uso, usado_por, data_criacao) VALUES (?,"
                " ?, ?, 'Disponível', 'N/A', ?)",
                (
                    codigo,
                    cargo_chave,
                    modalidade_chave,
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            )
            chaves_criadas.append(codigo)
          except Exception:
            pass
        conn.commit()
        st.success(
            f"✅ {len(chaves_criadas)} chaves geradas com sucesso! Veja na aba"
            " 'Chaves Geradas'."
        )

  with tab_ver_chaves:
    st.markdown("### 📋 Relatório de Chaves de Ativação")
    df_chaves = pd.read_sql("SELECT * FROM chaves_licenca", conn)
    if not df_chaves.empty:
      exibir_tabela_padronizada(df_chaves, "chaves_licenca")
    else:
      st.info("Nenhuma chave gerada ainda.")

  with tab_gerenciar_users:
    st.markdown("### 👥 Gerenciamento de Colaboradores & Planos")
    df_users = pd.read_sql("SELECT * FROM usuarios_sistema", conn)
    if not df_users.empty:
      exibir_tabela_padronizada(df_users, "usuarios_sistema")

      st.markdown("---")
      st.markdown("### ✍️ Atualizar Cargo ou Plano de um Colaborador")
      lista_emails_users = df_users["email"].tolist()
      colab_selecionado = st.selectbox(
          "Selecione o colaborador pelo e-mail",
          lista_emails_users,
          key="sel_colab_usr",
      )

      with st.form("form_editar_colaborador_admin"):
        novo_cargo_adm = st.selectbox(
            "Novo Cargo / Função",
            [
                "Diretoria / Gestão",
                "Engenheiro / Gestor de Obra",
                "Mecânico / Oficina",
                "Operador / Motorista / Campo",
            ],
            key="adm_novo_cargo",
        )
        novo_status_adm = st.selectbox(
            "Status da Conta", ["Ativo", "Inativo"], key="adm_novo_status"
        )
        nova_modalidade_adm = st.selectbox(
            "Modalidade de Plano",
            ["Plano Mensal (30 days)", "Plano Anual (365 days)"],
            key="adm_nova_mod",
        )
        btn_atualizar_adm = st.form_submit_button(
            "💾 Salvar Alterações do Colaborador"
        )

        if btn_atualizar_adm:
          novo_plano_str = f"{novo_cargo_adm} — {nova_modalidade_adm}"
          cursor.execute(
              "UPDATE usuarios_sistema SET cargo_setor = ?, status_assinatura"
              " = ?, plano_atual = ? WHERE email = ?",
              (
                  novo_cargo_adm,
                  novo_status_adm,
                  novo_plano_str,
                  colab_selecionado,
              ),
          )
          conn.commit()
          st.success(
              f"✅ Colaborador **{colab_selecionado}** atualizado com sucesso!"
          )
          st.rerun()
