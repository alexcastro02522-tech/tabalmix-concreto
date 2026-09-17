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
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização Visual Corporativa Refinada em Tema Claro
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1.2rem !important;
    }
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        width: 300px !important;
        background: #f4f6f9 !important;
        border-right: 1px solid #cbd5e1;
        padding-top: 10px;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 300px !important;
        background: transparent !important;
    }
    .stApp {
        background: #f4f6f9 !important;
        color: #1e293b !important;
    }
    h1, h2, h3 {
        color: #1b7a3e !important;
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    p, label, span, .stMarkdown {
        color: #1e293b !important;
        font-size: 14px;
        font-weight: 500;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #1e293b !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #1e293b !important;
        font-weight: 600;
        font-size: 13.5px;
        padding: 10px 12px;
        border-radius: 8px;
        background: #ffffff !important;
        margin-bottom: 6px;
        border: 1px solid #cbd5e1;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: #e2e8f0 !important;
        border-color: #1b7a3e;
        color: #1b7a3e !important;
    }
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-left: 4px solid #cbd5e1 !important;
        padding: 12px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
    }
    div[data-testid="stMetric"] label {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 20px !important;
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
        border-radius: 8px !important;
        min-height: 40px !important;
    }
    div[data-baseweb="menu"], ul[data-baseweb="menu"], li[data-baseweb="option"], div[id*="popover"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    div[data-baseweb="menu"] div, span, option, div[id*="popover"] * {
        color: #0f172a !important;
    }
    div[data-testid="stDataFrame"], .stDataFrame {
        background-color: #ffffff !important;
        border-radius: 12px;
        padding: 10px;
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }
    div[data-testid="stDataFrame"] table, div[data-testid="stDataFrame"] tr, div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] td {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #1b7a3e 0%, #12542a 100%) !important;
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        border: 1px solid #1b7a3e;
        padding: 0.55rem 1.6rem;
        box-shadow: 0 4px 15px rgba(27, 122, 62, 0.25);
        transition: all 0.25s ease-in-out;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #12542a 0%, #0a381c 100%) !important;
        box-shadow: 0 6px 20px rgba(27, 122, 62, 0.4);
        transform: translateY(-1px);
    }
    </style>
    <script>
    document.addEventListener('keydown', function(e) {
        if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I') || (e.ctrlKey && e.key === 'u')) {
            e.preventDefault();
            alert('Acesso restrito pelo sistema de segurança.');
        }
    });
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
    });
    </script>
""",
    unsafe_allow_html=True,
)


def gerar_pdf_relatorio(titulo, dataframe):
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=letter)
  largura, altura = letter
  margem_esq = 30
  largura_util = largura - 60

  c.setFillColorRGB(0.08, 0.32, 0.16)
  c.rect(0, altura - 60, largura, 60, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 14)
  c.drawString(margem_esq, altura - 25, "TABALMIX CONCRETO")
  c.setFont("Helvetica", 9)
  c.drawString(
      margem_esq,
      altura - 42,
      "Sistema de Gestão de Frota e Operações | Powered by Castro Tech",
  )

  c.setFillColorRGB(0.15, 0.15, 0.15)
  c.setFont("Helvetica-Bold", 13)
  c.drawString(margem_esq, altura - 85, titulo)
  c.setFont("Helvetica", 8.5)
  c.setFillColorRGB(0.4, 0.4, 0.4)
  c.drawString(
      margem_esq,
      altura - 100,
      f"Emitido em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
  )

  c.setStrokeColorRGB(0.8, 0.8, 0.8)
  c.setLineWidth(0.75)
  c.line(margem_esq, altura - 108, largura - margem_esq, altura - 108)

  y = altura - 135
  altura_linha = 20
  colunas = list(dataframe.columns)
  colunas_amigables = [
      str(col).replace("_", " ").upper() for col in colunas[:6]
  ]

  c.setFillColorRGB(0.08, 0.25, 0.13)
  c.rect(
      margem_esq,
      y - 4,
      largura_util,
      altura_linha,
      fill=1,
      stroke=0,
  )
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 8)
  largura_coluna = largura_util / len(colunas_amigables)

  for i, col_nome in enumerate(colunas_amigables):
    c.drawString(margem_esq + (i * largura_coluna) + 4, y + 3, col_nome[:14])

  y -= altura_linha + 2
  c.setFont("Helvetica", 8)

  for index, row in dataframe.iterrows():
    if y < 50:
      c.showPage()
      y = altura - 40
    if index % 2 == 0:
      c.setFillColorRGB(0.94, 0.96, 0.94)
      c.rect(
          margem_esq,
          y - 3,
          largura_util,
          altura_linha - 2,
          fill=1,
          stroke=0,
      )
    c.setFillColorRGB(0.1, 0.1, 0.1)
    for i, col in enumerate(colunas[:6]):
      valor_celula = str(row[col])
      if valor_celula == "None" or valor_celula == "nan":
        valor_celula = "-"
      c.drawString(
          margem_esq + (i * largura_coluna) + 4, y + 3, valor_celula[:16]
      )
    c.setStrokeColorRGB(0.85, 0.88, 0.85)
    c.line(margem_esq, y - 4, largura - margem_esq, y - 4)
    y -= altura_linha

  c.save()
  buffer.seek(0)
  return buffer


def gerar_csv_relatorio(dataframe):
  output = io.StringIO()
  df_export = dataframe.copy()
  df_export.columns = [
      str(col).replace("_", " ").upper() for col in df_export.columns
  ]
  df_export.to_csv(output, index=False, sep=";", encoding="utf-8-sig")
  return output.getvalue().encode("utf-8-sig")


def init_db():
  conn = sqlite3.connect("frota_profissional.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_prefixo TEXT,
            tipo TEXT,
            marca TEXT,
            modelo TEXT,
            ano INTEGER,
            chassi TEXT,
            placa TEXT,
            horimetro_km INTEGER,
            combustivel TEXT,
            local_atual TEXT,
            operador_condutor TEXT,
            status TEXT,
            data_entrada TEXT,
            observacoes TEXT
        )
    """)
  
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS manutencoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_prefixo TEXT,
            tipo_manutencao TEXT,
            horimetro_km_manut TEXT,
            origem_falha TEXT,
            descricao_problema TEXT,
            data_abertura TEXT,
            hora_abertura TEXT,
            pecas_utilizadas TEXT,
            custo_pecas REAL,
            mao_de_obra REAL,
            custo REAL,
            oficina TEXT,
            tecnico_mecanico TEXT,
            data_fechamento TEXT,
            hora_fechamento TEXT,
            status_os TEXT
        )
    """)
  
  # Garantir compatibilidade de colunas caso a tabela já exista sem elas
  for col_sql in [
      "ALTER TABLE manutencoes ADD COLUMN tag_prefixo TEXT",
      "ALTER TABLE manutencoes ADD COLUMN tipo_manutencao TEXT",
      "ALTER TABLE manutencoes ADD COLUMN horimetro_km_manut TEXT",
      "ALTER TABLE manutencoes ADD COLUMN origem_falha TEXT",
      "ALTER TABLE manutencoes ADD COLUMN descricao_problema TEXT",
      "ALTER TABLE manutencoes ADD COLUMN data_abertura TEXT",
      "ALTER TABLE manutencoes ADD COLUMN hora_abertura TEXT",
      "ALTER TABLE manutencoes ADD COLUMN pecas_utilizadas TEXT",
      "ALTER TABLE manutencoes ADD COLUMN custo_pecas REAL",
      "ALTER TABLE manutencoes ADD COLUMN mao_de_obra REAL",
      "ALTER TABLE manutencoes ADD COLUMN custo REAL",
      "ALTER TABLE manutencoes ADD COLUMN oficina TEXT",
      "ALTER TABLE manutencoes ADD COLUMN tecnico_mecanico TEXT",
      "ALTER TABLE manutencoes ADD COLUMN data_fechamento TEXT",
      "ALTER TABLE manutencoes ADD COLUMN hora_fechamento TEXT",
      "ALTER TABLE manutencoes ADD COLUMN status_os TEXT"
  ]:
    try:
      cursor.execute(col_sql)
    except Exception:
      pass

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
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT,
            cpf TEXT,
            email TEXT UNIQUE,
            senha TEXT,
            celular_seguranca TEXT,
            status_assinatura TEXT,
            plano_atual TEXT,
            data_cadastro TEXT
        )
    """)
  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

# Verificação blindada de Administrador via URL param (?admin=1)
modo_admin_liberado = False
try:
  query_params = st.query_params
  if (
      query_params.get("admin") == "1"
      or query_params.get("admin") == ["1"]
      or str(query_params).find("admin=1") != -1
  ):
    modo_admin_liberado = True
except Exception:
  pass

# Gerenciamento de Sessão de Login
if "usuario_logado" not in st.session_state:
  st.session_state["usuario_logado"] = None

# TELA DE AUTENTICAÇÃO REFINADA COM CARTÃO DE BOAS-VINDAS E LOGO
if st.session_state["usuario_logado"] is None and not modo_admin_liberado:
  col_l1, col_l2, col_l3 = st.columns([1, 2.2, 1])
  with col_l2:
    try:
      with open("caminhoes.jpg", "rb") as image_file:
        encoded_logo_login = base64.b64encode(image_file.read()).decode()
      st.markdown(
          f"""
                <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.06); margin-top: 15px; margin-bottom: 15px;">
                    <div style="border-radius: 10px; overflow: hidden; max-height: 110px; border: 2px solid #1b7a3e; margin-bottom: 12px;">
                        <img src="data:image/jpeg;base64,{encoded_logo_login}" style="width: 100%; height: 100px; object-fit: cover; display: block;">
                    </div>
                    <div style="display: inline-block; background: rgba(27, 122, 62, 0.15); border: 1px solid #1b7a3e; border-radius: 20px; padding: 2px 12px; margin-bottom: 6px;">
                        <span style="color: #1b7a3e; font-size: 10px; font-weight: 700; letter-spacing: 0.8px;">🛡️ SELO OFICIAL</span>
                    </div>
                    <h2 style="color: #1b7a3e !important; margin: 0; font-size: 18px; font-weight: 800;">TABALMIX CONCRETO</h2>
                    <p style="color: #475569; font-size: 11px; margin: 3px 0 2px 0; text-transform: uppercase; letter-spacing: 1px;">Gestão de Frota & Operações</p>
                    <p style="color: #94a3b8; font-size: 9px; margin: 0; font-style: italic;">Powered by Castro Tech</p>
                </div>
            """,
          unsafe_allow_html=True,
      )
    except Exception:
      st.markdown(
          """
                <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.06); margin-top: 15px; margin-bottom: 15px;">
                    <h2 style="color: #1b7a3e !important; margin: 0; font-size: 18px; font-weight: 800;">TABALMIX CONCRETO</h2>
                    <p style="color: #475569; font-size: 11px; margin: 3px 0 2px 0; text-transform: uppercase; letter-spacing: 1px;">Gestão de Frota & Operações</p>
                    <p style="color: #94a3b8; font-size: 9px; margin: 0; font-style: italic;">Powered by Castro Tech</p>
                </div>
            """,
          unsafe_allow_html=True,
      )

    tab_login, tab_cadastro, tab_recuperar = st.tabs([
        "🔑 Entrar",
        "📝 Criar Conta",
        "🔄 Recuperar Senha",
    ])

    with tab_login:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>Acesse"
          " sua conta corporativa:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_login"):
        email_login = st.text_input("E-mail Cadastrado")
        senha_login = st.text_input("Senha", type="password")
        btn_entrar = st.form_submit_button("Entrar no Sistema")

        if btn_entrar:
          cursor.execute(
              "SELECT * FROM usuarios_sistema WHERE email = ? AND senha = ?",
              (email_login, senha_login),
          )
          user_data = cursor.fetchone()
          if user_data:
            st.session_state["usuario_logado"] = {
                "id": user_data[0],
                "nome": user_data[1],
                "cpf": user_data[2],
                "email": user_data[3],
                "status": user_data[6],
            }
            st.success("✅ Login realizado com sucesso!")
            st.rerun()
          else:
            st.error("⚠️ E-mail ou senha incorretos.")

    with tab_cadastro:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>Cadastre"
          " sua empresa para começar:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_novo_cadastro"):
        c_nome = st.text_input("Nome Completo / Responsável")
        c_cpf = st.text_input("CPF")
        c_email = st.text_input("E-mail (Seu Login)")
        c_senha = st.text_input("Criar Senha", type="password")
        c_cel = st.text_input("Celular / Contato de Segurança")
        btn_cadastrar = st.form_submit_button("Finalizar Cadastro")

        if btn_cadastrar:
          if c_nome and c_cpf and c_email and c_senha:
            try:
              cursor.execute(
                  "INSERT INTO usuarios_sistema (nome_completo, cpf, email,"
                  " senha, celular_seguranca, status_assinatura, plano_atual,"
                  " data_cadastro) VALUES (?, ?, ?, ?, ?, 'Inativo', 'Nenhum',"
                  " ?)",
                  (
                      c_nome,
                      c_cpf,
                      c_email,
                      c_senha,
                      c_cel,
                      datetime.now().strftime("%Y-%m-%d %H:%M"),
                  ),
              )
              conn.commit()
              st.success(
                  "✅ Conta criada com sucesso! Vá na aba 'Entrar' para fazer"
                  " seu login."
              )
            except Exception as e:
              st.error(
                  "⚠️ Este e-mail já está cadastrado ou ocorreu um erro:"
                  f" {str(e)}"
              )
          else:
            st.error("⚠️ Preencha todos os campos obrigatórios.")

    with tab_recuperar:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>Redefina"
          " sua senha de segurança:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_recuperar_senha"):
        rec_email = st.text_input("E-mail Cadastrado na Conta")
        rec_cpf = st.text_input("CPF do Titular")
        nova_senha = st.text_input("Nova Senha", type="password")
        btn_resetar = st.form_submit_button("Redefinir Senha")

        if btn_resetar:
          if rec_email and rec_cpf and nova_senha:
            cursor.execute(
                "SELECT id FROM usuarios_sistema WHERE email = ? AND cpf = ?",
                (rec_email, rec_cpf),
            )
            user_match = cursor.fetchone()
            if user_match:
              cursor.execute(
                  "UPDATE usuarios_sistema SET senha = ? WHERE email = ?",
                  (nova_senha, rec_email),
              )
              conn.commit()
              st.success(
                  "✅ Senha redefinida com sucesso! Vá na aba 'Entrar' e acesse"
                  " com sua nova senha."
              )
            else:
              st.error("⚠️ E-mail ou CPF não encontrados no sistema.")
          else:
            st.error("⚠️ Preencha todos os campos para recuperar a senha.")

  st.stop()

# RECUPERA DADOS DO USUÁRIO LOGADO
usuario_atual = st.session_state["usuario_logado"]
status_usuario_ativo = (
    True
    if modo_admin_liberado
    else (
        usuario_atual["status"] == "Ativo"
        if usuario_atual
        else False
    )
)

# Menu Lateral Sofisticado com Selo Oficial e Identificação do Usuário
with st.sidebar:
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_logo = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="text-align: center; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.04);">
                <div style="border-radius: 8px; overflow: hidden; max-height: 90px; border: 2px solid #1b7a3e; margin-bottom: 8px;">
                    <img src="data:image/jpeg;base64,{encoded_logo}" style="width: 100%; height: 80px; object-fit: cover; display: block;">
                </div>
                <div style="display: inline-block; background: rgba(27, 122, 62, 0.15); border: 1px solid #1b7a3e; border-radius: 20px; padding: 2px 10px; margin-bottom: 4px;">
                    <span style="color: #1b7a3e; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;">🛡️ SELO OFICIAL</span>
                </div>
                <h3 style="color: #1b7a3e !important; margin: 0; font-size: 15px; font-weight: 800;">TABALMIX CONCRETO</h3>
                <p style="color: #475569; font-size: 9px; margin: 2px 0 2px 0; text-transform: uppercase; letter-spacing: 1px;">Gestão de Frota & Operações</p>
                <p style="color: #94a3b8; font-size: 8px; margin: 0; font-style: italic;">Powered by Castro Tech</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.markdown(
        """
            <div style="text-align: center; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px;">
                <h3 style="color: #1b7a3e !important; margin: 0; font-size: 15px; font-weight: 800;">TABALMIX CONCRETO</h3>
                <p style="color: #475569; font-size: 9px; margin: 2px 0 2px 0; text-transform: uppercase; letter-spacing: 1px;">Gestão de Frota & Operações</p>
                <p style="color: #94a3b8; font-size: 8px; margin: 0; font-style: italic;">Powered by Castro Tech</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

  if modo_admin_liberado:
    st.success("🔓 **Modo Admin Ativo**")
  elif usuario_atual:
    st.info(
        f"👤 **Usuário:** {usuario_atual['nome']}\n\n📊 **Status:**"
        f" {usuario_atual['status']}"
    )
    if st.button("🚪 Sair / Trocar Conta"):
      st.session_state["usuario_logado"] = None
      st.rerun()

  st.markdown("---")


def verificar_licenca_para_acao():
  if status_usuario_ativo or modo_admin_liberado:
    return True

  st.warning(
      "🔒 **Sua assinatura está Inativa ou Pendente:**\n\nEscolha um plano"
      " abaixo para ativar o seu acesso de qualquer dispositivo:"
  )
  escolha_metodo = st.radio(
      "Forma de Pagamento:",
      [
          "💳 Pagamento Automático (Mercado Pago)",
          "🔑 Transferência Direta (Chave Pix)",
      ],
      label_visibility="collapsed",
  )

  if "Mercado Pago" in escolha_metodo:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
      if st.button("💳 Mensal (R$ 250,00)", key="btn_mensal_esc"):
        try:
          sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
          pref_data = {
              "items": [{
                  "title": (
                      f"Tabalmix - Mensal ({usuario_atual['email'] if usuario_atual else 'Cliente'})"
                  ),
                  "quantity": 1,
                  "unit_price": 250.0,
                  "currency_id": "BRL",
              }],
              "back_urls": {
                  "success": "https://tabalmix-concreto.streamlit.app",
                  "failure": "https://tabalmix-concreto.streamlit.app",
                  "pending": "https://tabalmix-concreto.streamlit.app",
              },
              "auto_return": "approved",
          }
          res = sdk.preference().create(pref_data)
          url = (
              res["response"].get("init_point") if "response" in res else ""
          )
          if url:
            if usuario_atual:
              cursor.execute(
                  "UPDATE usuarios_sistema SET status_assinatura = 'Ativo',"
                  " plano_atual = 'Mensal' WHERE id = ?",
                  (usuario_atual["id"],),
              )
              conn.commit()
            st.markdown(
                f"🔗 **[👉 ABRIR CHECKOUT DE PAGAMENTO]({url})**\n\n*(Após o"
                " pagamento, atualize a página)*"
            )
        except Exception as e:
          st.error(f"Erro: {e}")
    with col_p2:
      if st.button("🌟 Anual (R$ 2.400,00)", key="btn_anual_esc"):
        try:
          sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
          pref_data = {
              "items": [{
                  "title": (
                      f"Tabalmix - Anual ({usuario_atual['email'] if usuario_atual else 'Cliente'})"
                  ),
                  "quantity": 1,
                  "unit_price": 2400.0,
                  "currency_id": "BRL",
              }],
              "back_urls": {
                  "success": "https://tabalmix-concreto.streamlit.app",
                  "failure": "https://tabalmix-concreto.streamlit.app",
                  "pending": "https://tabalmix-concreto.streamlit.app",
              },
              "auto_return": "approved",
          }
          res = sdk.preference().create(pref_data)
          url = (
              res["response"].get("init_point") if "response" in res else ""
          )
          if url:
            if usuario_atual:
              cursor.execute(
                  "UPDATE usuarios_sistema SET status_assinatura = 'Ativo',"
                  " plano_atual = 'Anual' WHERE id = ?",
                  (usuario_atual["id"],),
              )
              conn.commit()
            st.markdown(
                f"🔗 **[👉 ABRIR CHECKOUT DE PAGAMENTO]({url})**\n\n*(Após o"
                " pagamento, atualize a página)*"
            )
        except Exception as e:
          st.error(f"Erro: {e}")
  else:
    st.info(
        "🔑 **Chave Pix para Depósito:** `sua-chave-pix@dominio.com`\nEnvie o"
        " comprovante para liberar o seu acesso instantâneo."
    )
  return False


menu = st.sidebar.radio(
    "Navegação",
    [
        "📊 Visão Geral",
        "🚜 CADASTRO DE EQUIPAMENTOS",
        "⛽ Abastecimentos & Combustível",
        "🏗️ Mobilização / Desmobilização",
        "🛠️ Ordens de Serviço (OS)",
        "🔩 Peças e Ferramentas",
        "👥 Gestão de Clientes",
        "🔍 Consulta / Busca Geral",
        "⚙️ Painel de Licença (Admin)",
    ],
    label_visibility="collapsed",
)

if menu == "📊 Visão Geral":
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.04);">
                <div style="border-radius: 8px; overflow: hidden; max-height: 120px; border: 1px solid #e2e8f0; margin-bottom: 8px;">
                    <img src="data:image/jpeg;base64,{encoded_string}" style="width: 100%; height: 110px; object-fit: cover; display: block;">
                </div>
                <h2 style="color: #1b7a3e !important; margin: 0 0 2px 0; font-size: 15px;">🏗️ Tabalmix - Painel Operacional da Frota</h2>
                <p style="color: #475569 !important; font-size: 11px; margin: 0; font-weight: 500;">Controle avançado de caminhões betoneira, maquinário e manutenções | Powered by Castro Tech.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.markdown(
        """
            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px; margin-bottom: 15px;">
                <h2 style="color: #1b7a3e !important; margin: 0 0 2px 0; font-size: 15px;">🏗️ Tabalmix - Painel Operacional da Frota</h2>
                <p style="color: #475569 !important; font-size: 11px; margin: 0; font-weight: 500;">Controle avançado de caminhões betoneira, maquinário e manutenções | Powered by Castro Tech.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

  df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
  df_manut = pd.read_sql("SELECT * FROM manutencoes", conn)
  df_pecas = pd.read_sql("SELECT * FROM pecas", conn)
  df_comb = pd.read_sql("SELECT * FROM combustivel", conn)

  total_frota = len(df_veiculos)
  total_custo = df_manut["custo"].sum() if not df_manut.empty and "custo" in df_manut.columns else 0.0
  liberado_pecas = (
      df_manut["custo_pecas"].sum() if not df_manut.empty and "custo_pecas" in df_manut.columns else 0.0
  )
  liberado_mo = df_manut["mao_de_obra"].sum() if not df_manut.empty and "mao_de_obra" in df_manut.columns else 0.0
  total_combustivel = (
      df_comb["valor_total"].sum() if not df_comb.empty else 0.0
  )

  ativos_trabalhando = 0
  ativos_parados = 0
  if not df_veiculos.empty and "status" in df_veiculos.columns:
    ativos_trabalhando = len(
        df_veiculos[
            df_veiculos["status"].isin(["Ativo", "Mobilizado", "Operando"])
        ]
    )
    ativos_parados = total_frota - ativos_trabalhando

  r1_c1, r1_c2, r1_c3 = st.columns(3)
  with r1_c1:
    st.metric("Total Frota", total_frota)
  with r1_c2:
    st.metric("🟢 Trabalhando", ativos_trabalhando)
  with r1_c3:
    st.metric("🔴 Parados", ativos_parados)

  r2_c1, r2_c2, r2_c3 = st.columns(3)
  with r2_c1:
    st.metric("Custo Manut.", f"R$ {total_custo:,.2f}")
  with r2_c2:
    st.metric("Gasto Combustível", f"R$ {total_combustivel:,.2f}")
  with r2_c3:
    st.metric("Total Insumos", len(df_pecas))

  if not df_manut.empty or not df_comb.empty:
    st.divider()
    st.subheader("📊 Indicadores e Comparativo de Custos")
    gc1, gc2 = st.columns(2)
    with gc1:
      st.markdown("**Despesas de Manutenção (Peças vs Mão de Obra)**")
      df_custos_chart = pd.DataFrame(
          {"Categoria": ["Peças Utilizadas", "Mão de Obra"], "Valor (R$)": [liberado_pecas, liberado_mo]}
      )
      st.bar_chart(df_custos_chart, x="Categoria", y="Valor (R$)")
    with gc2:
      st.markdown("**Consumo de Combustível por Equipamento**")
      if not df_comb.empty:
        df_comb_chart = df_comb.groupby("equipamento")["valor_total"].sum().reset_index()
        st.bar_chart(df_comb_chart, x="equipamento", y="valor_total")
      else:
        st.info("Nenhum abastecimento registrado para gerar gráfico.")

  if not df_veiculos.empty:
    st.divider()
    st.subheader("⚠️ Alertas de Manutenção Preventiva")
    alerta_gerado = False
    for idx, row in df_veiculos.iterrows():
      h_km = row["horimetro_km"] if row["horimetro_km"] is not None else 0
      if h_km >= 15000:
        st.warning(
            f"🔔 **Atenção Preventiva:** O equipamento **{row['tag_prefixo']}**"
            f" ({row['modelo']}) atingiu **{h_km:,} KM/Horímetro**. Recomenda-se"
            " agendar revisão geral."
        )
        alerta_gerado = True
    if not alerta_gerado:
      st.success(
          "✅ Todos os equipamentos estão com horímetro/KM dentro do período"
          " ideal de operação."
      )

  st.divider()
  st.subheader("📋 Status da Frota e Equipamentos")

  if not df_veiculos.empty:
    filtro_status = st.selectbox(
        "🔍 Filtrar Status",
        [
            "Todos os Status",
            "Ativo",
            "Mobilizado",
            "Em manutenção",
            "Parado",
            "Desmobilizado",
            "Inativo",
        ],
    )
    df_filtrado = df_veiculos.copy()
    if filtro_status != "Todos os Status":
      df_filtrado = df_veiculos[df_veiculos["status"] == filtro_status]

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    if status_usuario_ativo or modo_admin_liberado:
      c_d1, c_d2 = st.columns(2)
      with c_d1:
        st.download_button(
            "📥 Baixar PDF",
            gerar_pdf_relatorio("RELATÓRIO DE FROTA", df_filtrado),
            "frota.pdf",
            "application/pdf",
        )
      with c_d2:
        st.download_button(
            "📊 Baixar Planilha (.csv)",
            gerar_csv_relatorio(df_filtrado),
            "frota.csv",
            "text/csv",
        )
  else:
    st.info("Nenhum equipamento cadastrado.")

elif menu == "🚜 CADASTRO DE EQUIPAMENTOS":
  st.title("🚜 CADASTRO DE EQUIPAMENTOS")

  if status_usuario_ativo or modo_admin_liberado:
    with st.form("form_frota", clear_on_submit=False):
      col1, col2 = st.columns(2)
      with col1:
        tag_prefixo = st.text_input("TAG/PREFIXO (Ex: EQ-001)")
        tipo = st.selectbox(
            "Tipo de Equipamento",
            [
                "Caminhão Betoneira",
                "Caminhão Basculante",
                "Escavadeira",
                "Utilitário",
                "Trator",
            ],
        )
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        ano = st.number_input(
            "Ano de Fabricação", min_value=1950, value=2024, step=1
        )
        chassi = st.text_input("Número de Série / Chassi (Opcional)")
        placa = st.text_input("Placa")
      with col2:
        horimetro_km = st.number_input(
            "Horímetro ou Quilometragem Atual", min_value=0, value=15000, step=100
        )
        combustivel = st.selectbox(
            "Combustível", ["Diesel S10", "Diesel S500", "Gasolina", "Flex"]
        )
        local_atual = st.text_input("Local Atual / Obra")
        operador_condutor = st.text_input("Operador/Condutor")
        status = st.selectbox(
            "Situação / Status",
            [
                "Ativo",
                "Em manutenção",
                "Parado",
                "Mobilizado",
                "Desmobilizado",
                "Inativo",
            ],
        )
        data_entrada = st.date_input("Data de Entrada na Empresa")
        observacoes = st.text_input("Observações")

      if st.form_submit_button("Cadastrar Equipamento"):
        if modelo and tag_prefixo:
          cursor.execute(
              "INSERT INTO veiculos (tag_prefixo, tipo, marca, modelo, ano,"
              " chassi, placa, horimetro_km, combustivel, local_atual,"
              " operador_condutor, status, data_entrada, observacoes) VALUES (?,"
              " ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (
                  tag_prefixo.upper(),
                  tipo,
                  marca,
                  modelo,
                  ano,
                  chassi,
                  placa.upper(),
                  int(horimetro_km),
                  combustivel,
                  local_atual,
                  operador_condutor,
                  status,
                  str(data_entrada),
                  observacoes,
              ),
          )
          conn.commit()
          st.success(f"✅ Equipamento '{tag_prefixo.upper()}' cadastrado!")
          st.rerun()
        else:
          st.error("⚠️ Preencha TAG/PREFIXO e Modelo.")
  else:
    verificar_licenca_para_acao()

  st.divider()
  st.subheader("Equipamentos Cadastrados")
  df_f = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_f.empty:
    st.dataframe(df_f, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔎 Ficha Histórica Individual do Equipamento")
    eq_selecionado_historico = st.selectbox(
        "Selecione a TAG/Prefixo para ver o Histórico Completo",
        df_f["tag_prefixo"].tolist(),
        key="sel_hist_eq",
    )
    if eq_selecionado_historico:
      dados_eq = df_f[df_f["tag_prefixo"] == eq_selecionado_historico].iloc[0]
      st.info(
          f"📌 **Ativo:** {dados_eq['tag_prefixo']} | **Modelo:**"
          f" {dados_eq['modelo']} | **Status Atual:** {dados_eq['status']} |"
          f" **Horímetro/KM:** {dados_eq['horimetro_km']:,}"
      )

      col_h1, col_h2 = st.columns(2)
      with col_h1:
        st.markdown("**🛠️ Histórico de Manutenções (OS):**")
        df_hist_os = pd.read_sql(
            "SELECT id, tipo_manutencao, data_abertura, status_os, custo FROM"
            " manutencoes WHERE tag_prefixo = ?",
            conn,
            params=(eq_selecionado_historico,),
        )
        if not df_hist_os.empty:
          st.dataframe(df_hist_os, use_container_width=True, hide_index=True)
        else:
          st.write("Nenhuma OS registrada para este equipamento.")
      with col_h2:
        st.markdown("**⛽ Histórico de Abastecimentos:**")
        df_hist_comb = pd.read_sql(
            "SELECT data, litros, valor_total, motorista FROM combustivel WHERE"
            " equipamento = ?",
            conn,
            params=(eq_selecionado_historico,),
        )
        if not df_hist_comb.empty:
          st.dataframe(df_hist_comb, use_container_width=True, hide_index=True)
        else:
          st.write("Nenhum abastecimento registrado.")

    if status_usuario_ativo or modo_admin_liberado:
      c_del1, c_del2 = st.columns([2, 1])
      with c_del1:
        eq_exc = st.selectbox(
            "Selecione o ID para Excluir da Frota", df_f["id"].tolist()
        )
      with c_del2:
        st.write("")
        st.write("")
        if st.button("🗑️ Excluir"):
          cursor.execute("DELETE FROM veiculos WHERE id = ?", (eq_exc,))
          conn.commit()
          st.success("Removido!")
          st.rerun()
  else:
    st.info("Nenhum equipamento cadastrado.")

elif menu == "⛽ Abastecimentos & Combustível":
  st.title("⛽ Controle de Abastecimento e Combustível")
  try:
    df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  except Exception:
    df_v = pd.DataFrame()

  if df_v.empty:
    st.warning("Cadastre equipamentos primeiro na aba 'CADASTRO DE EQUIPAMENTOS'.")
  else:
    if status_usuario_ativo or modo_admin_liberado:
      with st.form("form_comb"):
        c1, c2 = st.columns(2)
        with c1:
          eq_comb = st.selectbox(
              "Equipamento / TAG", df_v["tag_prefixo"].tolist()
          )
          litros = st.number_input("Litros", min_value=0.1, value=100.0)
          val_tot = st.number_input("Valor Total (R$)", min_value=0.0, value=600.0)
        with c2:
          km_h = st.text_input("KM ou Horímetro")
          posto = st.text_input("Posto / Fornecedor")
          motorista = st.text_input("Motorista / Responsável")
          dt_ab = st.date_input("Data")
        if st.form_submit_button("Registrar Abastecimento"):
          cursor.execute(
              "INSERT INTO combustivel (equipamento, litros, valor_total,"
              " km_horimetro, posto_posto, motorista, data) VALUES (?, ?, ?,"
              " ?, ?, ?, ?)",
              (
                  eq_comb,
                  float(litros),
                  float(val_tot),
                  str(km_h),
                  posto,
                  motorista,
                  str(dt_ab),
              ),
          )
          conn.commit()
          st.success("✅ Abastecimento registrado!")
    else:
      verificar_licenca_para_acao()

    st.divider()
    df_c = pd.read_sql("SELECT * FROM combustivel", conn)
    if not df_c.empty:
      st.dataframe(df_c, use_container_width=True, hide_index=True)

elif menu == "🏗️ Mobilização / Desmobilização":
  st.title("🏗️ Mobilização e Desmobilização de Obras")
  try:
    df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  except Exception:
    df_v = pd.DataFrame()

  if df_v.empty:
    st.warning("Cadastre equipamentos primeiro na aba 'CADASTRO DE EQUIPAMENTOS'.")
  else:
    if status_usuario_ativo or modo_admin_liberado:
      with st.form("form_mob"):
        c1, c2 = st.columns(2)
        with c1:
          eq_mob = st.selectbox(
              "Equipamento / TAG", df_v["tag_prefixo"].tolist()
          )
          tipo_mov = st.selectbox(
              "Movimentação",
              [
                  "Mobilização (Envio)",
                  "Desmobilização (Retorno)",
                  "Remanejamento",
              ],
          )
          destino = st.text_input("Obra / Destino-Origem")
          km_mov = st.text_input("Horímetro / KM")
        with c2:
          resp = st.text_input("Responsável")
          dt_mob = st.date_input("Data")
          motivo = st.text_input("Motivo / Condição")
          obs = st.text_input("Observação")
        if st.form_submit_button("Registrar Movimentação"):
          cursor.execute(
              "INSERT INTO mobilizacoes (equipamento, tipo_movimento,"
              " destino_origem, responsavel, data, horimetro_km_mov,"
              " motivo_condicao, observacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (
                  eq_mob,
                  tipo_mov,
                  destino,
                  resp,
                  str(dt_mob),
                  str(km_mov),
                  motivo,
                  obs,
              ),
          )
          conn.commit()
          st.success("✅ Registrado com sucesso!")
    else:
      verificar_licenca_para_acao()

    st.divider()
    df_mobs = pd.read_sql("SELECT * FROM mobilizacoes", conn)
    if not df_mobs.empty:
      st.dataframe(df_mobs, use_container_width=True, hide_index=True)

elif menu == "🛠️ Ordens de Serviço (OS)":
  st.title("🛠️ Gestão Unificada de Ordens de Serviço (OS)")

  try:
    df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  except Exception:
    df_v = pd.DataFrame()

  if df_v.empty:
    st.warning("Cadastre equipamentos antes de abrir uma OS.")
  else:
    if status_usuario_ativo or modo_admin_liberado:
      st.markdown("### 🟢 Abertura de Nova OS (Etapa 1)")
      with st.form("form_abertura_os", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
          tag_os = st.selectbox(
              "Tag / Prefixo do Equipamento", df_v["tag_prefixo"].tolist()
          )
          tipo_manut = st.selectbox(
              "Tipo de Manutenção",
              ["Preventiva", "Corretiva", "Preditiva", "Revisão Geral"],
          )
          horimetro_ab = st.text_input("Horímetro / KM na Abertura")
          origem_f = st.selectbox(
              "Origem da Falha", ["Falha na Operação", "Falha no Equipamento"]
          )
        with c2:
          data_ab = st.date_input("Data de Abertura")
          hora_ab = st.text_input(
              "Horário de Abertura (Ex: 08:30)", value="08:00"
          )
          desc_prob = st.text_area(
              "Descrição do Problema Apresentado pelo Motorista"
          )

        if st.form_submit_button("Abrir Nova OS"):
          cursor.execute(
              "INSERT INTO manutencoes (tag_prefixo, tipo_manutencao,"
              " horimetro_km_manut, origem_falha, descricao_problema,"
              " data_abertura, hora_abertura, status_os, custo, custo_pecas,"
              " mao_de_obra) VALUES (?, ?, ?, ?, ?, ?, ?, 'Aberta', 0.0, 0.0,"
              " 0.0)",
              (
                  tag_os,
                  tipo_manutencao,
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
    else:
      verificar_licenca_para_acao()

    st.divider()
    st.subheader("📋 Fechamento e Histórico de Ordens de Serviço")
    df_os = pd.read_sql("SELECT * FROM manutencoes", conn)
    if not df_os.empty:
      st.dataframe(df_os, use_container_width=True, hide_index=True)

      if status_usuario_ativo or modo_admin_liberado:
        st.markdown(
            "### ⚙️ Fechamento / Atualização de OS Existente (Etapa 2)"
        )
        os_abertas_ids = df_os["id"].tolist()
        os_sel = st.selectbox(
            "Selecione o ID da OS para Preencher e Fechar", os_abertas_ids
        )

        if os_sel:
          os_row_data = df_os[df_os["id"] == os_sel]
          if not os_row_data.empty:
            os_atual = os_row_data.iloc[0]
            tag_eq_os = os_atual.get("tag_prefixo") or os_atual.get("equipamento") or "N/D"
            val_dt_ab = os_atual.get("data_abertura") or "N/D"
            val_hr_ab = os_atual.get("hora_abertura") or "N/D"
            val_tp_man = os_atual.get("tipo_manutencao") or "Preventiva"
            val_desc = os_atual.get("descricao_problema") or ""
            val_st_os = os_atual.get("status_os") or "Aberta"

            with st.form("form_fechamento_os"):
              st.info(
                  f"Editando OS #{os_atual['id']} | Equipamento:"
                  f" {tag_eq_os} | Aberta em:"
                  f" {val_dt_ab} às {val_hr_ab}"
              )
              fc1, fc2 = st.columns(2)
              with fc1:
                pecas_util = st.text_input(
                    "Peças Utilizadas",
                    value=str(os_atual.get("pecas_utilizadas") or ""),
                )
                v_pecas = st.number_input(
                    "Valor Total das Peças (R$)",
                    min_value=0.0,
                    value=float(os_atual.get("custo_pecas") or 0.0),
                    format="%.2f",
                )
                v_mo = st.number_input(
                    "Valor da Mão de Obra (R$)",
                    min_value=0.0,
                    value=float(os_atual.get("mao_de_obra") or 0.0),
                    format="%.2f",
                )
                oficina_resp = st.text_input(
                    "Oficina Responsável",
                    value=str(os_atual.get("oficina") or ""),
                )
              with fc2:
                tec_resp = st.text_input(
                    "Técnico / Mecânico Responsável",
                    value=str(os_atual.get("tecnico_mecanico") or ""),
                )
                dt_fech = st.date_input("Data de Fechamento")
                hr_fech = st.text_input(
                    "Horário de Fechamento (Ex: 17:00)", value="17:00"
                )
                status_final = st.selectbox(
                    "Status da OS", ["Aberta", "Em manutenção", "Fechada"]
                )

              if st.form_submit_button("Salvar e Fechar OS"):
                custo_total = v_pecas + v_mo
                cursor.execute(
                    "UPDATE manutencoes SET pecas_utilizadas = ?, custo_pecas ="
                    " ?, mao_de_obra = ?, custo = ?, oficina = ?,"
                    " tecnico_mecanico = ?, data_fechamento = ?, hora_fechamento"
                    " = ?, status_os = ? WHERE id = ?",
                    (
                        pecas_util,
                        v_pecas,
                        v_mo,
                        custo_total,
                        oficina_resp,
                        tec_resp,
                        str(dt_fech),
                        hr_fech,
                        status_final,
                        os_sel,
                    ),
                )
                conn.commit()
                st.success(f"✅ OS #{os_sel} atualizada e fechada com sucesso!")
                st.rerun()

            st.markdown("---")
            st.markdown("### 📲 Enviar Relatório da OS via WhatsApp")
            texto_msg = (
                f"*TABALMIX CONCRETO - RELATÓRIO DE OS #{os_atual['id']}*\n\n"
                f"🚜 *Equipamento:* {tag_eq_os}\n"
                f"🔧 *Tipo:* {val_tp_man}\n"
                f"📋 *Status:* {val_st_os}\n"
                f"⚠️ *Problema:* {val_desc}\n"
                f"🔩 *Peças:* {os_atual.get('pecas_utilizadas') or 'Nenhuma'}\n"
                f"💰 *Custo Total:* R$ {(os_atual.get('custo') or 0.0):,.2f}\n"
                f"📅 *Fechamento:* {os_atual.get('data_fechamento') or '-'} às"
                f" {os_atual.get('hora_fechamento') or '-'}"
            )
            encoded_whatsapp = urllib.parse.quote(texto_msg)
            url_whatsapp = f"https://api.whatsapp.com/send?text={encoded_whatsapp}"
            st.markdown(
                f"💬 **[👉 CLIQUE AQUI PARA ENVIAR OS VIA"
                f" WHATSAPP]({url_whatsapp})**",
                unsafe_allow_html=True,
            )
    else:
      st.info("Nenhuma OS registrada.")

elif menu == "🔩 Peças e Ferramentas":
  st.title("🔩 Controle de Peças e Ferramentas")
  t1, t2 = st.tabs(["Cadastrar", "Inventário"])
  with t1:
    if status_usuario_ativo or modo_admin_liberado:
      with st.form("form_pecas"):
        c1, c2 = st.columns(2)
        with c1:
          nome_i = st.text_input("Nome da Peça ou Ferramenta")
          cat = st.selectbox(
              "Categoria",
              ["Reposição", "Filtro/Óleo", "Ferramenta", "Insumo"],
          )
        with c2:
          qtd = st.number_input("Quantidade", min_value=1, value=1)
          v_unit = st.number_input("Valor Unitário (R$)", min_value=0.0)
        if st.form_submit_button("Adicionar"):
          cursor.execute(
              "INSERT INTO pecas (nome_item, categoria, quantidade,"
              " valor_unitario) VALUES (?, ?, ?, ?)",
              (nome_i, cat, qtd, v_unit),
          )
          conn.commit()
          st.success("Cadastrado!")
    else:
      verificar_licenca_para_acao()
  with t2:
    df_p = pd.read_sql("SELECT * FROM pecas", conn)
    if not df_p.empty:
      st.dataframe(df_p, use_container_width=True, hide_index=True)

elif menu == "👥 Gestão de Clientes":
  st.title("👥 Gestão de Clientes")
  if status_usuario_ativo or modo_admin_liberado:
    with st.form("form_cli"):
      c1, c2 = st.columns(2)
      with c1:
        nome_c = st.text_input("Nome / Razão Social")
        emp = st.text_input("Empresa")
        tel = st.text_input("Telefone")
      with c2:
        doc = st.text_input("CPF / CNPJ")
        em = st.text_input("E-mail")
        end = st.text_input("Endereço")
      if st.form_submit_button("Salvar Cliente"):
        cursor.execute(
            "INSERT INTO clientes (nome, empresa, telefone, documento, email,"
            " endereco) VALUES (?, ?, ?, ?, ?, ?)",
            (nome_c, emp, tel, doc, em, end),
        )
        conn.commit()
        st.success("Salvo!")
  else:
    verificar_licenca_para_acao()

  df_cli = pd.read_sql("SELECT * FROM clientes", conn)
  if not df_cli.empty:
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

elif menu == "🔍 Consulta / Busca Geral":
  st.title("🔍 Consulta Geral")
  termo = st.text_input("Digite o termo de busca (TAG, Placa, Cliente...)")
  if termo:
    t_like = f"%{termo}%"
    df_bv = pd.read_sql(
        "SELECT * FROM veiculos WHERE tag_prefixo LIKE ? OR placa LIKE ? OR"
        " modelo LIKE ?",
        conn,
        params=(t_like, t_like, t_like),
    )
    if not df_bv.empty:
      st.dataframe(df_bv, use_container_width=True, hide_index=True)
    else:
      st.info("Nenhum resultado.")

elif menu == "⚙️ Painel de Licença (Admin)":
  if modo_admin_liberado:
    st.title("⚙️ Painel de Administração de Usuários e Segurança")
    
    st.markdown("### 📥 Backup do Banco de Dados (Segurança)")
    try:
      with open("frota_profissional.db", "rb") as f_db:
        st.download_button(
            "💾 Baixar Cópia de Segurança (.db)",
            f_db,
            file_name=f"backup_tabalmix_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
            mime="application/octet-stream"
        )
    except Exception as e:
      st.info("Arquivo de banco de dados gerado após o primeiro uso.")

    st.markdown("---")
    st.markdown("### Gestão de Usuários e Licenças")
    df_users = pd.read_sql(
        "SELECT id, nome_completo, cpf, email, celular_seguranca,"
        " status_assinatura, plano_atual FROM usuarios_sistema",
        conn,
    )
    if not df_users.empty:
      st.dataframe(df_users, use_container_width=True, hide_index=True)

      with st.form("form_admin_user"):
        id_sel = st.selectbox(
            "Selecione o ID do Usuário", df_users["id"].tolist()
        )
        novo_status_u = st.selectbox("Novo Status", ["Ativo", "Inativo"])
        if st.form_submit_button("Atualizar Assinatura do Usuário"):
          cursor.execute(
              "UPDATE usuarios_sistema SET status_assinatura = ? WHERE id = ?",
              (novo_status_u, id_sel),
          )
          conn.commit()
          st.success("✅ Status do usuário atualizado com sucesso!")
          st.rerun()
    else:
      st.info("Nenhum usuário cadastrado no sistema ainda.")
  else:
    st.error("Acesso restrito.")
