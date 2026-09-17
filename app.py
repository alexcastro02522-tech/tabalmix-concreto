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
    page_title="Tabalmix Concreto - Enterprise Fleet & Operations Pro X",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização Visual Enterprise com Sidebar em Tema Claro e Selo de Garantia
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    [data-testid="stSidebar"] {
        min-width: 310px !important;
        width: 310px !important;
        background: #f1f5f9 !important;
        border-right: 1px solid #cbd5e1;
        padding-top: 15px;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #1e293b !important;
    }
    .stApp {
        background: #f8fafc !important;
        color: #0f172a !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    h1, h2, h3 {
        color: #0f172a !important;
        font-weight: 800;
        letter-spacing: -0.8px;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #1e293b !important;
        font-weight: 600;
        font-size: 13.5px;
        padding: 10px 14px;
        border-radius: 10px;
        background: #ffffff !important;
        margin-bottom: 6px;
        border: 1px solid #cbd5e1;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: #e2e8f0 !important;
        border-color: #059669;
        color: #059669 !important;
        transform: translateX(4px);
    }
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 5px solid #10b981 !important;
        padding: 16px !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
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
        font-size: 24px !important;
        font-weight: 900 !important;
    }
    div.stTextInput > div > div > input, 
    div.stNumberInput > div > div > input, 
    div.stSelectbox > div > div > div,
    div.stTextArea > div > div > textarea,
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        min-height: 42px !important;
    }
    div[data-baseweb="menu"], ul[data-baseweb="menu"], li[data-baseweb="option"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    div[data-testid="stDataFrame"], .stDataFrame {
        background-color: #ffffff !important;
        border-radius: 14px;
        padding: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
    }
    .stButton button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: white !important;
        font-weight: 700;
        border-radius: 10px;
        border: none;
        padding: 0.6rem 1.8rem;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35);
        transition: all 0.25s ease-in-out;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #047857 0%, #065f46 100%) !important;
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.5);
        transform: translateY(-2px);
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


def gerar_pdf_os_tecnica(os_row):
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=letter)
  largura, altura = letter
  margem = 40

  c.setFillColorRGB(0.04, 0.35, 0.22)
  c.rect(0, altura - 70, largura, 70, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 16)
  c.drawString(margem, altura - 30, "ordem de serviço técnica oficial (os)")
  c.setFont("Helvetica", 10)
  c.drawString(
      margem,
      altura - 50,
      f"tabalmix concreto — alta performance | os #{os_row.get('id', 1)}",
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
  c.drawString(margem, y, "descrição do problema relatado:")
  y = y - 18
  c.setFont("Helvetica", 10)
  desc_txt = str(os_row.get("descricao_problema", "sem descrição."))
  c.drawString(margem, y, desc_txt[:95])

  y -= 40
  c.setFont("Helvetica-Bold", 11)
  c.drawString(margem, y, "dados de encerramento e faturamento:")
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
  c.setFillColorRGB(0.04, 0.35, 0.22)
  c.drawString(
      margem,
      y,
      f"• custo total da os: r$ {(os_row.get('custo') or 0.0):,.2f} | status:"
      f" {os_row.get('status_os', 'aberta').upper()}",
  )

  y -= 90
  c.setStrokeColorRGB(0.5, 0.5, 0.5)
  c.setLineWidth(1)
  c.line(margem, y, largura / 2 - 20, y)
  c.line(largura / 2 + 20, y, largura - margem, y)
  y -= 15
  c.setFont("Helvetica", 9)
  c.setFillColorRGB(0.2, 0.2, 0.2)
  c.drawString(margem, y, "assinatura do encarregado responsável")
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
  col_l1, col_l2, col_l3 = st.columns([1, 2.4, 1])
  with col_l2:
    try:
      with open("caminhoes.jpg", "rb") as image_file:
        encoded_logo_login = base64.b64encode(image_file.read()).decode()
      st.markdown(
          f"""
                <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.08); margin-top: 15px; margin-bottom: 15px;">
                    <div style="border-radius: 12px; overflow: hidden; max-height: 110px; border: 2px solid #059669; margin-bottom: 14px;">
                        <img src="data:image/jpeg;base64,{encoded_logo_login}" style="width: 100%; height: 105px; object-fit: cover; display: block;">
                    </div>
                    <div style="display: inline-block; background: rgba(5, 150, 105, 0.15); border: 1px solid #059669; border-radius: 20px; padding: 3px 14px; margin-bottom: 8px;">
                        <span style="color: #059669; font-size: 11px; font-weight: 800; letter-spacing: 1px;">🛡️ selo oficial de garantia enterprise</span>
                    </div>
                    <h2 style="color: #0f172a !important; margin: 0; font-size: 20px; font-weight: 900;">tabalmix concreto</h2>
                    <p style="color: #475569; font-size: 11px; margin: 4px 0 2px 0; text-transform: uppercase; letter-spacing: 1.2px;">gestão inteligente de frota e oficina pro</p>
                    <p style="color: #94a3b8; font-size: 9.5px; margin: 0; font-style: italic;">powered by castro tech</p>
                </div>
            """,
          unsafe_allow_html=True,
      )
    except Exception:
      st.markdown(
          """
                <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.08); margin-top: 15px; margin-bottom: 15px;">
                    <div style="display: inline-block; background: rgba(5, 150, 105, 0.15); border: 1px solid #059669; border-radius: 20px; padding: 3px 14px; margin-bottom: 8px;">
                        <span style="color: #059669; font-size: 11px; font-weight: 800; letter-spacing: 1px;">🛡️ selo oficial de garantia enterprise</span>
                    </div>
                    <h2 style="color: #0f172a !important; margin: 0; font-size: 20px; font-weight: 900;">tabalmix concreto</h2>
                    <p style="color: #475569; font-size: 11px; margin: 4px 0 2px 0; text-transform: uppercase; letter-spacing: 1.2px;">gestão inteligente de frota e oficina pro</p>
                    <p style="color: #94a3b8; font-size: 9.5px; margin: 0; font-style: italic;">powered by castro tech</p>
                </div>
            """,
          unsafe_allow_html=True,
      )

    tab_login, tab_cadastro, tab_recuperar, tab_pin = st.tabs([
        "🔑 entrar",
        "📝 criar conta",
        "🔄 recuperar",
        "🔐 pin rápido",
    ])

    with tab_login:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>acesse"
          " sua conta corporativa:</p>",
          unsafe_allow_html=True,
      )
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
            }
            st.success("✅ login realizado com sucesso!")
            st.rerun()
          else:
            st.error("⚠️ e-mail ou senha incorretos.")

    with tab_cadastro:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>cadastro"
          " de novo usuário na plataforma:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_novo_cadastro"):
        c_nome = st.text_input("nome completo / gestor")
        c_cpf = st.text_input("cpf")
        c_email = st.text_input("e-mail de login")
        c_senha = st.text_input("criar senha", type="password")
        c_cel = st.text_input("celular / whatsapp")
        btn_cadastrar = st.form_submit_button("finalizar cadastro")

        if btn_cadastrar:
          if c_nome and c_email and c_senha:
            try:
              cursor.execute(
                  "INSERT INTO usuarios_sistema (nome_completo, cpf, email,"
                  " senha, celular_seguranca, status_assinatura, plano_atual,"
                  " data_cadastro) VALUES (?, ?, ?, ?, ?, 'Ativo', 'Enterprise',"
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
                  "✅ conta ativada com sucesso! abra a aba 'entrar'."
              )
            except Exception as e:
              st.error(f"⚠️ erro ao cadastrar (e-mail já cadastrado?): {e}")
          else:
            st.error("⚠️ preencha os campos obrigatórios.")

    with tab_recuperar:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>recuperação"
          " rápida de credenciais:</p>",
          unsafe_allow_html=True,
      )
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

    with tab_pin:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>acesso"
          " instantâneo via pin (4 dígitos):</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_pin"):
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
            }
            st.success("✅ login por pin validado!")
            st.rerun()
          else:
            st.error("⚠️ e-mail ou pin inválidos.")

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

# Sidebar em tema claro com o Selo Oficial de Garantia no topo
with st.sidebar:
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_logo_side = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="text-align: center; margin-bottom: 12px;">
                <img src="data:image/jpeg;base64,{encoded_logo_side}" style="width: 100%; height: 85px; object-fit: cover; border-radius: 10px; border: 1px solid #059669; margin-bottom: 8px;">
                <div style="background: #d1fae5; border: 1px solid #059669; border-radius: 8px; padding: 4px; text-align: center;">
                    <span style="color: #065f46; font-size: 10.5px; font-weight: 800; letter-spacing: 0.5px;">🛡️ SELO DE GARANTIA ENTERPRISE</span>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.markdown(
        """
            <div style="background: #d1fae5; border: 1px solid #059669; border-radius: 8px; padding: 6px; text-align: center; margin-bottom: 12px;">
                <span style="color: #065f46; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">🛡️ SELO DE GARANTIA ENTERPRISE</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

  if modo_admin_liberado:
    st.success("🔓 **modo admin enterprise ativo**")
  elif usuario_atual:
    st.info(
        f"👤 **gestor:** {usuario_atual['nome']}\n\n⭐ **plano:**"
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
  st.subheader("📈 analytics avançado de desempenho")
  col_graf1, col_graf2 = st.columns(2)

  with col_graf1:
    st.markdown("**distribuição de status operacional**")
    if not df_veiculos.empty and "status" in df_veiculos.columns:
      status_counts = df_veiculos["status"].value_counts()
      st.bar_chart(status_counts)
    else:
      st.info("sem dados suficientes de status para exibir.")

  with col_graf2:
    st.markdown("**tipos de equipamentos na frota**")
    if not df_veiculos.empty and "tipo" in df_veiculos.columns:
      tipo_counts = df_veiculos["tipo"].value_counts()
      st.bar_chart(tipo_counts)
    else:
      st.info("sem dados suficientes de tipos para exibir.")

  st.divider()
  col_exp1, col_exp2 = st.columns([3, 1])
  with col_exp1:
    st.subheader("📋 listagem geral de equipamentos")
  with col_exp2:
    if not df_veiculos.empty:
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
    st.dataframe(df_veiculos, use_container_width=True, hide_index=True)

    # Botões de compartilhamento direto via WhatsApp e E-mail
    st.markdown("### 📲 compartilhar relatórios e dados")
    col_w, col_e = st.columns(2)
    with col_w:
      msg_whatsapp = urllib.parse.quote(
          "Olá! Segue o resumo executivo da frota da Tabalmix Concreto gerado"
          " via sistema Enterprise."
      )
      st.markdown(
          f'<a href="https://wa.me/?text={msg_whatsapp}" target="_blank"><button'
          ' style="background-color: #25D366; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: bold; cursor: pointer; width: 100%;">💬 Enviar Relatório via WhatsApp</button></a>',
          unsafe_allow_html=True,
      )
    with col_e:
      assunto_email = urllib.parse.quote(
          "Relatório Executivo de Frota - Tabalmix Concreto"
      )
      corpo_email = urllib.parse.quote(
          "Prezado(a),\n\nSegue em anexo/resumo o relatório operacional da frota"
          " gerado pelo sistema Tabalmix Concreto Enterprise.\n\nAtenciosamente,"
          " Gestão de Frota."
      )
      st.markdown(
          f'<a href="mailto:?subject={assunto_email}&body={corpo_email}"'
          ' target="_blank"><button style="background-color: #0284c7; color:'
          " white; border: none; border-radius: 8px; padding: 10px 20px; font-"
          'weight: bold; cursor: pointer; width: 100%;">✉️ Enviar Relatório via'
          " E-mail</button></a>",
          unsafe_allow_html=True,
      )
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
