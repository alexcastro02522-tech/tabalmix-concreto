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
        border-left: 4px solid #1b7a3e !important;
        padding: 14px !important;
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
        font-size: 22px !important;
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
  c.drawString(margem_esq, altura - 25, "tabalmix concreto")
  c.setFont("Helvetica", 9)
  c.drawString(
      margem_esq,
      altura - 42,
      "sistema de gestão de frota e operações | powered by castro tech",
  )

  c.setFillColorRGB(0.15, 0.15, 0.15)
  c.setFont("Helvetica-Bold", 13)
  c.drawString(margem_esq, altura - 85, titulo)
  c.setFont("Helvetica", 8.5)
  c.setFillColorRGB(0.4, 0.4, 0.4)
  c.drawString(
      margem_esq,
      altura - 100,
      f"emitido em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
  )

  c.setStrokeColorRGB(0.8, 0.8, 0.8)
  c.setLineWidth(0.75)
  c.line(margem_esq, altura - 108, largura - margem_esq, altura - 108)

  y = altura - 135
  altura_linha = 20
  colunas = list(dataframe.columns)
  colunas_amigables = [
      str(col).replace("_", " ").lower() for col in colunas[:6]
  ]

  c.setFillColorRGB(0.08, 0.25, 0.13)
  c.rect(margem_esq, y - 4, largura_util, altura_linha, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 8)
  largura_coluna = largura_util / max(len(colunas_amigables), 1)

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
      c.rect(margem_esq, y - 3, largura_util, altura_linha - 2, fill=1, stroke=0)
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


def gerar_pdf_os_tecnica(os_row):
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=letter)
  largura, altura = letter
  margem = 40

  c.setFillColorRGB(0.08, 0.32, 0.16)
  c.rect(0, altura - 70, largura, 70, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 16)
  c.drawString(margem, altura - 30, "ordem de serviço técnica (os)")
  c.setFont("Helvetica", 10)
  c.drawString(
      margem,
      altura - 50,
      f"tabalmix concreto - sistema de gestão | os #{os_row.get('id', 1)}",
  )

  y = altura - 100
  c.setFillColorRGB(0.1, 0.1, 0.1)
  c.setFont("Helvetica-Bold", 11)
  c.drawString(margem, y, "dados do equipamento e abertura:")
  y = altura - 120
  c.setFont("Helvetica", 10)

  tag_eq = (
      os_row.get("tag_prefixo") or os_row.get("equipamento") or "não informado"
  )
  c.drawString(margem, y, f"• equipamento (tag): {tag_eq}")
  y -= 18
  c.drawString(
      margem,
      y,
      f"• tipo de manutenção: {os_row.get('tipo_manutencao', 'preventiva')}",
  )
  y -= 18
  c.drawString(
      margem,
      y,
      f"• horímetro / km: {os_row.get('horimetro_km_manut', 'não informado')}",
  )
  y -= 18
  c.drawString(
      margem,
      y,
      f"• origem da falha: {os_row.get('origem_falha', 'operação')}",
  )
  y -= 18
  c.drawString(
      margem,
      y,
      f"• abertura: {os_row.get('data_abertura', datetime.now().strftime('%Y-%m-%d'))} às"
      f" {os_row.get('hora_abertura', datetime.now().strftime('%H:%M'))}",
  )

  y -= 30
  c.setFont("Helvetica-Bold", 11)
  c.drawString(margem, y, "descrição do problema:")
  y = y - 18
  c.setFont("Helvetica", 10)
  desc_txt = str(os_row.get("descricao_problema", "sem descrição."))
  c.drawString(margem, y, desc_txt[:90])

  y -= 40
  c.setFont("Helvetica-Bold", 11)
  c.drawString(margem, y, "dados de encerramento e custos:")
  y -= 20
  c.setFont("Helvetica", 10)
  c.drawString(
      margem,
      y,
      f"• oficina responsável: {os_row.get('oficina', 'não informada')}",
  )
  y -= 18
  c.drawString(
      margem,
      y,
      f"• técnico / mecânico: {os_row.get('tecnico_mecanico', 'não informado')}",
  )
  y -= 18
  c.drawString(
      margem,
      y,
      f"• peças utilizadas: {os_row.get('pecas_utilizadas', 'nenhuma')}",
  )
  y -= 18
  c.drawString(
      margem,
      y,
      f"• custo de peças: r$ {(os_row.get('custo_pecas') or 0.0):,.2f}",
  )
  y -= 18
  c.drawString(
      margem,
      y,
      f"• custo mão de obra: r$ {(os_row.get('mao_de_obra') or 0.0):,.2f}",
  )
  y -= 22
  c.setFont("Helvetica-Bold", 11)
  c.setFillColorRGB(0.08, 0.32, 0.16)
  c.drawString(
      margem,
      y,
      f"• custo total da os: r$ {(os_row.get('custo') or 0.0):,.2f} | status:"
      f" {os_row.get('status_os', 'aberta')}",
  )

  y -= 90
  c.setStrokeColorRGB(0.5, 0.5, 0.5)
  c.setLineWidth(1)
  c.line(margem, y, largura / 2 - 20, y)
  c.line(largura / 2 + 20, y, largura - margem, y)
  y -= 15
  c.setFont("Helvetica", 9)
  c.setFillColorRGB(0.2, 0.2, 0.2)
  c.drawString(margem, y, "assinatura do encarregado")
  c.drawString(largura / 2 + 20, y, "assinatura do técnico / oficina")

  c.save()
  buffer.seek(0)
  return buffer


def init_db():
  conn = sqlite3.connect("frota_profissional.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_prefixo TEXT, tipo TEXT, marca TEXT, modelo TEXT,
            ano INTEGER, chassi TEXT, placa TEXT, horimetro_km INTEGER,
            combustivel TEXT, local_atual TEXT, operador_condutor TEXT,
            status TEXT, data_entrada TEXT, observacoes TEXT
        )
    """)
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
      "ALTER TABLE manutencoes ADD COLUMN status_os TEXT",
  ]:
    try:
      cursor.execute(col_sql)
    except Exception:
      pass

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
            motivo_condicao TEXT, observacao TEXT, foto_checklist TEXT
        )
    """)
  for col_mob in ["ALTER TABLE mobilizacoes ADD COLUMN foto_checklist TEXT"]:
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
            data_cadastro TEXT, pin_rapido TEXT
        )
    """)
  for col_pin in ["ALTER TABLE usuarios_sistema ADD COLUMN pin_rapido TEXT"]:
    try:
      cursor.execute(col_pin)
    except Exception:
      pass
  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

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

if "usuario_logado" not in st.session_state:
  st.session_state["usuario_logado"] = None

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
                        <span style="color: #1b7a3e; font-size: 10px; font-weight: 700; letter-spacing: 0.8px;">🛡️ selo oficial</span>
                    </div>
                    <h2 style="color: #1b7a3e !important; margin: 0; font-size: 18px; font-weight: 800;">tabalmix concreto</h2>
                    <p style="color: #475569; font-size: 11px; margin: 3px 0 2px 0; text-transform: uppercase; letter-spacing: 1px;">gestão de frota & operações</p>
                    <p style="color: #94a3b8; font-size: 9px; margin: 0; font-style: italic;">powered by castro tech</p>
                </div>
            """,
          unsafe_allow_html=True,
      )
    except Exception:
      st.markdown(
          """
                <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.06); margin-top: 15px; margin-bottom: 15px;">
                    <h2 style="color: #1b7a3e !important; margin: 0; font-size: 18px; font-weight: 800;">tabalmix concreto</h2>
                    <p style="color: #475569; font-size: 11px; margin: 3px 0 2px 0; text-transform: uppercase; letter-spacing: 1px;">gestão de frota & operações</p>
                    <p style="color: #94a3b8; font-size: 9px; margin: 0; font-style: italic;">powered by castro tech</p>
                </div>
            """,
          unsafe_allow_html=True,
      )

    tab_login, tab_cadastro, tab_recuperar, tab_pin = st.tabs([
        "🔑 entrar",
        "📝 criar conta",
        "🔄 recuperar",
        "🔐 acesso por pin",
    ])

    with tab_login:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>acesse"
          " sua conta corporativa:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_login"):
        email_login = st.text_input("e-mail cadastrado")
        senha_login = st.text_input("senha", type="password")
        cadastrar_pin = st.text_input(
            "criar pin rápido (4 números para acesso futuro - opcional)",
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
            }
            st.success("✅ login realizado com sucesso!")
            st.rerun()
          else:
            st.error("⚠️ e-mail ou senha incorretos.")

    with tab_cadastro:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>cadastre"
          " novo usuário:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_novo_cadastro"):
        c_nome = st.text_input("nome completo / responsável")
        c_cpf = st.text_input("cpf")
        c_email = st.text_input("e-mail corporativo (seu login)")
        c_senha = st.text_input("criar senha segura", type="password")
        c_cel = st.text_input("celular / contato de segurança")
        btn_cadastrar = st.form_submit_button("finalizar e ativar cadastro")

        if btn_cadastrar:
          if c_nome and c_email and c_senha:
            try:
              cursor.execute(
                  "INSERT INTO usuarios_sistema (nome_completo, cpf, email,"
                  " senha, celular_seguranca, status_assinatura, plano_atual,"
                  " data_cadastro) VALUES (?, ?, ?, ?, ?, 'Ativo', 'Mensal',"
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
                  "✅ conta criada e ativada com sucesso! abra a aba 'entrar'."
              )
            except Exception as e:
              st.error(f"⚠️ erro ao cadastrar (e-mail já existe?): {e}")
          else:
            st.error("⚠️ preencha os campos obrigatórios.")

    with tab_recuperar:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>recupere"
          " sua senha cadastrada:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_recuperar"):
        rec_email = st.text_input("informe seu e-mail cadastrado")
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
            st.error("⚠️ e-mail não encontrado no sistema.")

    with tab_pin:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>acesso"
          " rápido por pin (4 dígitos):</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_pin"):
        email_pin = st.text_input("e-mail da conta")
        pin_dig = st.text_input("pin de 4 dígitos", max_chars=4, type="password")
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
            }
            st.success("✅ login por pin realizado com sucesso!")
            st.rerun()
          else:
            st.error("⚠️ e-mail ou pin incorretos.")

  st.stop()

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

# Sidebar corporativa com navegação otimizada
with st.sidebar:
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_logo_side = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="text-align: center; margin-bottom: 10px;">
                <img src="data:image/jpeg;base64,{encoded_logo_side}" style="width: 100%; height: 75px; object-fit: cover; border-radius: 8px; border: 1px solid #1b7a3e;">
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    pass

  if modo_admin_liberado:
    st.success("🔓 **modo admin ativo**")
  elif usuario_atual:
    st.info(
        f"👤 **usuário:** {usuario_atual['nome']}\n\n📊 **status:**"
        f" {usuario_atual['status']}"
    )
    if st.button("🚪 encerrar sessão"):
      st.session_state["usuario_logado"] = None
      st.rerun()
  st.markdown("---")

menu = st.sidebar.radio(
    "navegação",
    [
        "📊 visão geral",
        "🚜 cadastro de equipamentos",
        "⛽ abastecimentos & combustível",
        "🏗️ mobilização / desmobilização",
        "🛠️ ordens de serviço (os)",
        "🔩 peças e ferramentas",
        "👥 gestão de clientes",
        "🔍 consulta / busca geral",
        "⚙️ meu perfil / dados",
        "⚙️ painel de licença (admin)",
    ],
    label_visibility="collapsed",
)

if menu == "📊 visão geral":
  st.title("🏗️ painel executivo e operacional da frota")
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

  # Métricas Executivas Superiores
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
    st.metric("total litros", f"{litros_totais:,.1f} l")

  st.divider()

  # Seção de Estatísticas Profissionais e Gráficos Rápidos
  st.subheader("📈 indicadores estatísticos de desempenho")
  col_graf1, col_graf2 = st.columns(2)

  with col_graf1:
    st.markdown("**distribuição de status da frota**")
    if not df_veiculos.empty and "status" in df_veiculos.columns:
      status_counts = df_veiculos["status"].value_counts()
      st.bar_chart(status_counts)
    else:
      st.info("sem dados suficientes de status para exibir.")

  with col_graf2:
    st.markdown("**tipos de equipamentos cadastrados**")
    if not df_veiculos.empty and "tipo" in df_veiculos.columns:
      tipo_counts = df_veiculos["tipo"].value_counts()
      st.bar_chart(tipo_counts)
    else:
      st.info("sem dados suficientes de tipos para exibir.")

  st.divider()
  st.subheader("📋 listagem geral de equipamentos")
  if not df_veiculos.empty:
    st.dataframe(df_veiculos, use_container_width=True, hide_index=True)
  else:
    st.info("nenhum equipamento cadastrado na frota.")

elif menu == "🚜 cadastro de equipamentos":
  st.title("🚜 cadastro de equipamentos e frota")
  with st.form("form_frota", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
      tag_prefixo = st.text_input("tag / prefixo (ex: EQ-001)")
      tipo = st.selectbox(
          "tipo de equipamento",
          [
              "caminhão betoneira",
              "caminhão basculante",
              "escavadeira",
              "utilitário",
              "trator",
          ],
      )
      marca = st.text_input("marca")
      modelo = st.text_input("modelo")
    with col2:
      ano = st.number_input(
          "ano de fabricação", min_value=1950, value=2024, step=1
      )
      placa = st.text_input("placa")
      horimetro_km = st.number_input(
          "horímetro ou km atual", min_value=0, value=15000, step=100
      )
      status = st.selectbox(
          "situação", ["Ativo", "Em Manutenção", "Parado", "Mobilizado"]
      )
    if st.form_submit_button("cadastrar equipamento"):
      if modelo:
        tag_final = (
            tag_prefixo.upper()
            if tag_prefixo and tag_prefixo.strip()
            else "EQ-00" + str(datetime.now().microsecond)[:3]
        )
        cursor.execute(
            "INSERT INTO veiculos (tag_prefixo, tipo, marca, modelo, ano,"
            " placa, horimetro_km, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                tag_final,
                tipo,
                marca,
                modelo,
                int(ano),
                placa.upper(),
                int(horimetro_km),
                status,
            ),
        )
        conn.commit()
        st.success(f"✅ equipamento '{tag_final}' cadastrado com sucesso!")
        st.rerun()
      else:
        st.error("⚠️ preencha ao menos o modelo do equipamento.")

  df_f = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_f.empty:
    st.dataframe(df_f, use_container_width=True, hide_index=True)

elif menu == "⛽ abastecimentos & combustível":
  st.title("⛽ controle de abastecimento e combustível")
  df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  tags_comb = (
      df_v["tag_prefixo"].dropna().tolist() if not df_v.empty else []
  )
  with st.form("form_comb"):
    c1, c2 = st.columns(2)
    with c1:
      if tags_comb:
        eq_comb = st.selectbox("equipamento / tag", tags_comb)
      else:
        eq_comb = st.text_input("equipamento / tag (manual)")
      litros = st.number_input("litros", min_value=0.1, value=100.0)
      val_tot = st.number_input("valor total (r$)", min_value=0.0, value=600.0)
    with c2:
      km_h = st.text_input("km ou horímetro")
      posto = st.text_input("posto / fornecedor")
      motorista = st.text_input("motorista / responsável")
      dt_ab = st.date_input("data")
    if st.form_submit_button("registrar abastecimento"):
      cursor.execute(
          "INSERT INTO combustivel (equipamento, litros, valor_total,"
          " km_horimetro, posto_posto, motorista, data) VALUES (?, ?, ?, ?, ?,"
          " ?, ?)",
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
      st.success("✅ abastecimento registrado com sucesso!")
      st.rerun()

  df_c = pd.read_sql("SELECT * FROM combustivel", conn)
  if not df_c.empty:
    st.dataframe(df_c, use_container_width=True, hide_index=True)

elif menu == "🏗️ mobilização / desmobilização":
  st.title("🏗️ mobilização e desmobilização de obras")
  df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  tags_mob = (
      df_v["tag_prefixo"].dropna().tolist() if not df_v.empty else []
  )
  with st.form("form_mob"):
    c1, c2 = st.columns(2)
    with c1:
      if tags_mob:
        eq_mob = st.selectbox("equipamento / tag", tags_mob)
      else:
        eq_mob = st.text_input("equipamento / tag (manual)")
      tipo_mov = st.selectbox(
          "movimentação",
          ["mobilização (envio)", "desmobilização (retorno)", "remanejamento"],
      )
      destino = st.text_input("obra / destino-origem")
    with c2:
      resp = st.text_input("responsável")
      dt_mob = st.date_input("data")
      obs = st.text_input("observação")

    foto_subida = st.file_uploader(
        "📷 anexar foto do check-list de recebimento / vistoria",
        type=["png", "jpg", "jpeg"],
    )

    if st.form_submit_button("registrar movimentação"):
      nome_foto = ""
      if foto_subida is not None:
        os.makedirs("uploads_checklists", exist_ok=True)
        nome_foto = (
            "uploads_checklists/"
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{foto_subida.name}"
        )
        with open(nome_foto, "wb") as f:
          f.write(foto_subida.getbuffer())

      cursor.execute(
          "INSERT INTO mobilizacoes (equipamento, tipo_movimento,"
          " destino_origem, responsavel, data, observacao, foto_checklist) VALUES"
          " (?, ?, ?, ?, ?, ?, ?)",
          (
              str(eq_mob).upper(),
              tipo_mov,
              destino,
              resp,
              str(dt_mob),
              obs,
              nome_foto,
          ),
      )
      conn.commit()
      st.success(
          "✅ movimentação e check-list fotográfico registrados com sucesso!"
      )
      st.rerun()

  df_mobs = pd.read_sql("SELECT * FROM mobilizacoes", conn)
  if not df_mobs.empty:
    st.dataframe(df_mobs, use_container_width=True, hide_index=True)
    for idx, row in df_mobs.iterrows():
      if row.get("foto_checklist") and os.path.exists(
          str(row["foto_checklist"])
      ):
        with st.expander(
            f"ver foto check-list #{row['id']} - {row['equipamento']}"
        ):
          st.image(row["foto_checklist"], width=300)

elif menu == "🛠️ ordens de serviço (os)":
  st.title("🛠️ gestão unificada de ordens de serviço (os)")
  df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  tags_disponiveis = (
      df_v["tag_prefixo"].dropna().tolist() if not df_v.empty else []
  )

  st.markdown("### 🟢 abertura de nova os (etapa 1)")
  with st.form("form_abertura_os", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
      if tags_disponiveis:
        tag_os = st.selectbox("tag / prefixo do equipamento", tags_disponiveis)
      else:
        tag_os = st.text_input(
            "tag / prefixo do equipamento (digite manualmente)"
        )

      tipo_manut = st.selectbox(
          "tipo de manutenção",
          ["preventiva", "corretiva", "preditiva", "revisão geral"],
      )
      horimetro_ab = st.text_input("horímetro / km na abertura")
      origem_f = st.selectbox(
          "origem da falha", ["falha na operação", "falha no equipamento"]
      )
    with c2:
      data_ab = st.date_input("data de abertura", value=datetime.now().date())
      hora_ab = st.text_input(
          "horário de abertura", value=datetime.now().strftime("%H:%M")
      )
      desc_prob = st.text_area(
          "descrição do problema apresentado pelo motorista"
      )

    if st.form_submit_button("abrir nova os"):
      tag_final_os = (
          str(tag_os).upper()
          if tag_os and str(tag_os).strip()
          else "EQ-GERAL"
      )
      cursor.execute(
          "INSERT INTO manutencoes (tag_prefixo, tipo_manutencao,"
          " horimetro_km_manut, origem_falha, descricao_problema,"
          " data_abertura, hora_abertura, status_os, custo, custo_pecas,"
          " mao_de_obra) VALUES (?, ?, ?, ?, ?, ?, ?, 'aberta', 0.0, 0.0,"
          " 0.0)",
          (
              tag_final_os,
              tipo_manut,
              horimetro_ab,
              origem_f,
              desc_prob,
              str(data_ab),
              hora_ab,
          ),
      )
      conn.commit()
      st.success("✅ os aberta com sucesso!")
      st.rerun()

  st.divider()
  st.subheader("📋 ordens de serviço cadastradas")
  df_os = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_os.empty:
    st.dataframe(df_os, use_container_width=True, hide_index=True)

    st.markdown("### 🔴 encerramento e faturamento de os (etapa 2)")
    with st.form("form_fechamento_os"):
      os_ids = (
          df_os[df_os["status_os"] == "aberta"]["id"].tolist()
          if "status_os" in df_os.columns
          else df_os["id"].tolist()
      )
      if os_ids:
        os_selecionada = st.selectbox(
            "selecione o id da os para fechar", os_ids
        )
        oficina_f = st.text_input("oficina responsável")
        tecnico_f = st.text_input("técnico / mecânico responsável")
        pecas_f = st.text_input("peças utilizadas")
        custo_pecas_f = st.number_input(
            "custo total de peças (r$)", min_value=0.0, value=0.0
        )
        mao_obra_f = st.number_input(
            "custo de mão de obra (r$)", min_value=0.0, value=0.0
        )
        data_fec = st.date_input(
            "data de fechamento", value=datetime.now().date()
        )
        hora_fec = st.text_input(
            "horário de fechamento", value=datetime.now().strftime("%H:%M")
        )

        btn_fechar_os = st.form_submit_button("encerrar os e gerar custos")
        if btn_fechar_os:
          custo_total = float(custo_pecas_f) + float(mao_obra_f)
          cursor.execute(
              "UPDATE manutencoes SET oficina = ?, tecnico_mecanico = ?,"
              " pecas_utilizadas = ?, custo_pecas = ?, mao_de_obra = ?,"
              " custo = ?, data_fechamento = ?, hora_fechamento = ?,"
              " status_os = 'fechada' WHERE id = ?",
              (
                  oficina_f,
                  tecnico_f,
                  pecas_f,
                  float(custo_pecas_f),
                  float(mao_obra_f),
                  custo_total,
                  str(data_fec),
                  hora_fec,
                  os_selecionada,
              ),
          )
          conn.commit()
          st.success(
              f"✅ os #{os_selecionada} fechada com sucesso! custo total:"
              f" r$ {custo_total:,.2f}"
          )
          st.rerun()
      else:
        st.info("não há ordens de serviço com status 'aberta' para encerrar.")

    for index, row in df_os.iterrows():
      if str(row.get("status_os")) == "fechada":
        pdf_os_buffer = gerar_pdf_os_tecnica(row)
        st.download_button(
            label=f"📄 baixar pdf da os #{row['id']}",
            data=pdf_os_buffer,
            file_name=f"ordem_servico_{row['id']}.pdf",
            mime="application/pdf",
            key=f"dl_os_{row['id']}",
        )
  else:
    st.info("nenhuma os registrada.")

elif menu == "🔩 peças e ferramentas":
  st.title("🔩 controle de peças e ferramentas")
  with st.form("form_pecas"):
    c1, c2 = st.columns(2)
    with c1:
      nome_i = st.text_input("nome da peça ou ferramenta")
      cat = st.selectbox(
          "categoria", ["reposição", "filtro/óleo", "ferramenta", "insumo"]
      )
    with c2:
      qtd = st.number_input("quantidade", min_value=1, value=1)
      v_unit = st.number_input("valor unitário (r$)", min_value=0.0)
    if st.form_submit_button("adicionar peça"):
      cursor.execute(
          "INSERT INTO pecas (nome_item, categoria, quantidade,"
          " valor_unitario) VALUES (?, ?, ?, ?)",
          (nome_i, cat, qtd, v_unit),
      )
      conn.commit()
      st.success("✅ peça cadastrada com sucesso!")
      st.rerun()

  df_p = pd.read_sql("SELECT * FROM pecas", conn)
  if not df_p.empty:
    st.dataframe(df_p, use_container_width=True, hide_index=True)

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
    if st.form_submit_button("salvar cliente"):
      cursor.execute(
          "INSERT INTO clientes (nome, empresa, telefone, documento, email,"
          " endereco) VALUES (?, ?, ?, ?, ?, ?)",
          (nome_c, emp, tel, doc, em, end),
      )
      conn.commit()
      st.success("✅ cliente salvo com sucesso!")
      st.rerun()

  df_cli = pd.read_sql("SELECT * FROM clientes", conn)
  if not df_cli.empty:
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

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
    eq_selecionado_historico = st.selectbox(
        "selecione a tag/prefixo para ver o histórico completo", lista_tags
    )
    if eq_selecionado_historico:
      df_eq_info = df_v_busca[
          df_v_busca["tag_prefixo"] == eq_selecionado_historico
      ]
      if not df_eq_info.empty:
        st.markdown(
            f"### dados do equipamento: **{eq_selecionado_historico}**"
        )
        st.dataframe(df_eq_info, use_container_width=True, hide_index=True)

        st.markdown("#### 🛠️ histórico de ordens de serviço")
        df_os_eq = pd.read_sql(
            "SELECT * FROM manutencoes WHERE tag_prefixo = ?",
            conn,
            params=(eq_selecionado_historico,),
        )
        if not df_os_eq.empty:
          st.dataframe(df_os_eq, use_container_width=True, hide_index=True)
        else:
          st.info("nenhuma os registrada para este equipamento.")

        st.markdown("#### ⛽ histórico de abastecimentos")
        df_comb_eq = pd.read_sql(
            "SELECT * FROM combustivel WHERE equipamento = ?",
            conn,
            params=(eq_selecionado_historico,),
        )
        if not df_comb_eq.empty:
          st.dataframe(df_comb_eq, use_container_width=True, hide_index=True)
        else:
          st.info("nenhum abastecimento registrado para este equipamento.")
  else:
    st.info("nenhum equipamento cadastrado para realizar consultas.")

elif menu == "⚙️ meu perfil / dados":
  st.title("⚙️ atualização de perfil")
  if usuario_atual:
    st.info(f"logado como: {usuario_atual['nome']} ({usuario_atual['email']})")

elif menu == "⚙️ painel de licença (admin)":
  st.title("⚙️ painel administrativo")
  df_users = pd.read_sql("SELECT * FROM usuarios_sistema", conn)
  if not df_users.empty:
    st.dataframe(df_users, use_container_width=True, hide_index=True)
  else:
    st.info("nenhum usuário cadastrado.")
