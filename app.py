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

# ESTILIZAÇÃO VISUAL PREMIUM ENTERPRISE (UX/UI World Class - Minimalista, Fluido e Sofisticado)
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
    
    /* REMOVE COMPLETAMENTE O BOTÃO DE RECOLHER E O TEXTO RESIDUAL DO TOPO DA BARRA LATERAL */
    [data-testid="stSidebar"] button[kind="header"], 
    [data-testid="stSidebar"] [data-testid="baseButton-header"],
    button[data-testid="baseButton-header"],
    header button,
    [data-testid="stSidebar"] header {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* OCULTA QUALQUER TEXTO RESIDUAL DE ÍCONE DO STREAMLIT NO TOPO */
    [data-testid="stSidebar"] > div:first-child div:first-child span {
        display: none !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0px !important;
    }
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] div.block-container {
        padding-top: 0px !important;
    }

    [data-testid="stSidebar"] {
        min-width: 320px !important;
        width: 320px !important;
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
        transition: transform 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.08);
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
    div[data-baseweb="menu"], ul[data-baseweb="menu"], li[data-baseweb="option"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
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
        background: linear-gradient(135deg, #047857 0%, #065f46 100%) !important;
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


def gerar_pdf_mobilizacao(mob_row):
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=letter)
  largura, altura = letter
  margem = 40

  c.setFillColorRGB(0.04, 0.35, 0.22)
  c.rect(0, altura - 70, largura, 70, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 16)
  c.drawString(
      margem, altura - 30, "laudo de check-list de mobilização / desmobilização"
  )
  c.setFont("Helvetica", 10)
  c.drawString(
      margem,
      altura - 50,
      f"tabalmix concreto — registro #{mob_row.get('id', 1)}",
  )

  y = altura - 100
  c.setFillColorRGB(0.1, 0.1, 0.1)
  c.setFont("Helvetica-Bold", 11)
  c.drawString(margem, y, "detalhes da movimentação:")
  y = altura - 125
  c.setFont("Helvetica", 10)

  c.drawString(
      margem, y, f"• equipamento (tag): {mob_row.get('equipamento', '-')}"
  )
  y -= 20
  c.drawString(
      margem, y, f"• tipo de movimento: {mob_row.get('tipo_movimento', '-')}"
  )
  y -= 20
  c.drawString(
      margem, y, f"• destino / origem: {mob_row.get('destino_origem', '-')}"
  )
  y -= 20
  c.drawString(
      margem, y, f"• responsável técnico: {mob_row.get('responsavel', '-')}"
  )
  y -= 20
  c.drawString(margem, y, f"• data da vistoria: {mob_row.get('data', '-')}")
  y -= 25
  c.drawString(
      margem, y, f"• observações: {mob_row.get('observacao', 'nenhuma')}"
  )

  y -= 50
  c.setFont("Helvetica-Bold", 11)
  c.drawString(
      margem,
      y,
      "evidências fotográficas anexadas: verifique no sistema os arquivos"
      " salvos.",
  )

  y -= 90
  c.setStrokeColorRGB(0.5, 0.5, 0.5)
  c.setLineWidth(1)
  c.line(margem, y, largura / 2 - 20, y)
  c.line(largura / 2 + 20, y, largura - margem, y)
  y -= 15
  c.setFont("Helvetica", 9)
  c.setFillColorRGB(0.2, 0.2, 0.2)
  c.drawString(margem, y, "assinatura do encarregado vistoriador")
  c.drawString(largura / 2 + 20, y, "assinatura do operador / motorista")

  c.save()
  buffer.seek(0)
  return buffer


def init_db():
  conn = sqlite3.connect("frota_profissional.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_prefixo TEXT, categoria_equipamento TEXT, tipo_equipamento TEXT,
            marca TEXT, modelo TEXT, ano INTEGER, chassi TEXT, renavam TEXT,
            placa TEXT, crv TEXT, cor TEXT, combustivel TEXT, empresa TEXT,
            operador_condutor TEXT, horimetro_km INTEGER, status TEXT, data_entrada TEXT, observacoes TEXT
        )
    """)

  for col_sql in [
      "ALTER TABLE veiculos ADD COLUMN categoria_equipamento TEXT",
      "ALTER TABLE veiculos ADD COLUMN tipo_equipamento TEXT",
      "ALTER TABLE veiculos ADD COLUMN chassi TEXT",
      "ALTER TABLE veiculos ADD COLUMN renavam TEXT",
      "ALTER TABLE veiculos ADD COLUMN crv TEXT",
      "ALTER TABLE veiculos ADD COLUMN cor TEXT",
      "ALTER TABLE veiculos ADD COLUMN combustivel TEXT",
      "ALTER TABLE veiculos ADD COLUMN empresa TEXT",
      "ALTER TABLE veiculos ADD COLUMN operador_condutor TEXT",
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
        CREATE TABLE IF NOT EXISTS alertas_sos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remetente TEXT,
            equipamento TEXT,
            motivo TEXT,
            data_alerta TEXT,
            status TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS avisos_fixados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT,
            mensagem TEXT,
            data_fixacao TEXT
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

# PERSISTÊNCIA INTELIGENTE DE SESSÃO NA OBRA (Salva o usuário ativo no navegador/query params para não deslogar ao atualizar)
try:
  if st.session_state["usuario_logado"] is None:
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

    # VITRINE DE VANTAGENS E PLANOS POR CARGO (DESIGN ULTRA SOFISTICADO)
    st.markdown(
        """
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 24px; margin-bottom: 25px; box-shadow: 0 10px 35px rgba(0,0,0,0.04); text-align: center;">
            <h3 style="color: #0f172a !important; font-size: 17px; margin-top: 0; font-weight: 800;">🌟 Vantagens e Recursos Exclusivos por Função na Obra</h3>
            <p style="font-size: 13px; color: #475569; margin-bottom: 18px;">Conheça o superpoder de cada plano corporativo integrado para a sua equipe:</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    v1, v2 = st.columns(2)
    with v1:
      st.markdown(
          """
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #059669; border-radius: 14px; padding: 18px; margin-bottom: 14px; box-shadow: 0 6px 18px rgba(0,0,0,0.03);">
                <span style="color: #065f46; font-size: 14.5px; font-weight: 700;">👑 Alta Gestão & Diretoria</span>
                <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0; line-height: 1.5;">Visão global da frota, relatórios executivos em PDF e recepção em tempo real dos <b>Alertas SOS</b> de pânico em campo.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
      st.markdown(
          """
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #d97706; border-radius: 14px; padding: 18px; margin-bottom: 14px; box-shadow: 0 6px 18px rgba(0,0,0,0.03);">
                <span style="color: #b45309; font-size: 14.5px; font-weight: 700;">🛠️ Oficina & Manutenção</span>
                <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0; line-height: 1.5;">Gestão ágil de Ordens de Serviço (OS), controle detalhado de estoque de peças e laudos de custos mecânicos.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    with v2:
      st.markdown(
          """
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #0284c7; border-radius: 14px; padding: 18px; margin-bottom: 14px; box-shadow: 0 6px 18px rgba(0,0,0,0.03);">
                <span style="color: #0369a1; font-size: 14.5px; font-weight: 700;">👷 Segurança do Trabalho (SST)</span>
                <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0; line-height: 1.5;">Conformidade regulamentada, vistorias fotográficas e emissão rápida de laudos de <b>Check-list de Mobilização</b>.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
      st.markdown(
          """
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #7c3aed; border-radius: 14px; padding: 18px; margin-bottom: 14px; box-shadow: 0 6px 18px rgba(0,0,0,0.03);">
                <span style="color: #6d28d9; font-size: 14.5px; font-weight: 700;">🚜 Operacional de Campo</span>
                <p style="font-size: 12px; color: #334155; margin: 6px 0 0 0; line-height: 1.5;">Praticidade diária, registros rápidos de abastecimento, chat integrado e acionamento instantâneo do <b>Botão SOS</b>.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    tab_login, tab_cadastro, tab_recuperar, tab_pin = st.tabs([
        "🔑 entrar na conta",
        "📝 cadastrar colaborador",
        "🔄 recuperar senha",
        "🔐 pin rápido (obra)",
    ])

    with tab_login:
      st.markdown(
          "<p style='font-size: 13.5px; color: #475569; margin-top: 12px; font-weight:"
          " 600;'>acesse sua conta corporativa:</p>",
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
                "apelido": (
                    user_data[9]
                    if len(user_data) > 9 and user_data[9] and user_data[9] != "None"
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
      st.markdown(
          "<p style='font-size: 13.5px; color: #475569; margin-top: 12px; font-weight:"
          " 600;'>cadastro de novo usuário e atribuição de plano por"
          " cargo:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_novo_cadastro"):
        c_nome = st.text_input("nome completo")
        c_apelido = st.text_input("primeiro nome ou apelido de guerra")
        c_cargo = st.selectbox(
            "cargo / plano na empresa",
            [
                "Diretoria / Gestão",
                "Segurança do Trabalho (SST)",
                "Engenheiro / Gestor de Obra",
                "Mecânico / Oficina",
                "Operador / Motorista",
                "Servente / Pedreiro / Campo",
            ],
        )
        c_cpf = st.text_input("cpf")
        c_email = st.text_input("e-mail corporativo de login")
        c_senha = st.text_input("criar senha", type="password")
        c_cel = st.text_input("celular / whatsapp")
        btn_cadastrar = st.form_submit_button("ativar conta com vantagens")

        if btn_cadastrar:
          if c_nome and c_email and c_senha:
            apelido_final = (
                c_apelido.strip()
                if c_apelido and c_apelido.strip() and c_apelido != "None"
                else c_nome.split()[0]
            )
            try:
              cursor.execute(
                  "INSERT INTO usuarios_sistema (nome_completo, cpf, email,"
                  " senha, celular_seguranca, status_assinatura, plano_atual,"
                  " data_cadastro, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?,"
                  " 'Ativo', 'Enterprise', ?, ?, ?)",
                  (
                      c_nome,
                      c_cpf,
                      c_email,
                      c_senha,
                      c_cel,
                      datetime.now().strftime("%Y-%m-%d %H:%M"),
                      apelido_final,
                      c_cargo,
                  ),
              )
              conn.commit()
              st.success(
                  "✅ conta ativada com sucesso com os benefícios do plano! abra"
                  " a aba 'entrar'."
              )
            except Exception as e:
              st.error(f"⚠️ erro ao cadastrar (e-mail já cadastrado?): {e}")
          else:
            st.error("⚠️ preencha os campos obrigatórios.")

    with tab_recuperar:
      st.markdown(
          "<p style='font-size: 13.5px; color: #475569; margin-top: 12px; font-weight:"
          " 600;'>recuperação rápida de credenciais:</p>",
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
          "<p style='font-size: 13.5px; color: #475569; margin-top: 12px; font-weight:"
          " 600;'>acesso instantâneo via pin (4 dígitos) na obra:</p>",
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
    for c in cols_atuais:
      if c not in cols_finais:
        cols_finais.append(c)
    df = df[cols_finais]

  st.dataframe(df, use_container_width=True, hide_index=True)


with st.sidebar:
  # TOPO DA BARRA LATERAL LIMPO E ALINHADO SEM TEXTOS RESIDUAIS
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
          "⚠️ **conta inativa:** modo de prestígio (leitura) habilitado."
      )
    if st.button("🚪 encerrar sessão"):
      st.session_state["usuario_logado"] = None
      try:
        st.query_params.clear()
      except Exception:
        pass
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
        "💬 chat tabalmix pro & rede",
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

  # LAYOUT ADAPTADO PARA MÓVEL (DIVIDIDO EM 3 E 2 COLUNAS)
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric("total frota", total_frota)
  with col2:
    st.metric("os abertas", os_abertas)
  with col3:
    st.metric("custo manut.", f"r$ {custo_total_manut:,.2f}")

  col4, col5 = st.columns(2)
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
    if modo_admin_liberado:
      with st.expander(
          "⚙️ [ADMIN] Configurar Posição e Ordem Padrão das Colunas (Frota)"
      ):
        cols_disp = list(df_veiculos.columns)
        nova_ordem_str = st.text_input(
            "Digite a ordem exata das colunas separadas por vírgula:",
            value=",".join(cols_disp),
            key="cfg_col_veiculos",
        )
        if st.button("💾 Salvar e Atualizar Ordem para Todos"):
          cursor.execute(
              "INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas)"
              " VALUES ('veiculos', ?)",
              (nova_ordem_str,),
          )
          conn.commit()
          st.success("✅ Ordem salva com sucesso para todos os colaboradores!")
          st.rerun()

    exibir_tabela_padronizada(df_veiculos, "veiculos")

    if status_usuario_ativo or modo_admin_liberado:
      st.markdown("### 📲 compartilhar relatórios e dados")
      col_w, col_e = st.columns(2)
      with col_w:
        msg_whatsapp = urllib.parse.quote(
            "Olá! Segue o resumo executivo da frota da Tabalmix Concreto gerado"
            " via sistema Enterprise."
        )
        st.markdown(
            f'<a href="https://wa.me/?text={msg_whatsapp}" target="_blank"><button'
            ' style="background-color: #25D366; color: white; border: none; border-radius: 12px; padding: 12px 20px; font-weight: bold; cursor: pointer; width: 100%; box-shadow: 0 4px 12px rgba(37,211,102,0.3);">💬 Enviar Relatório via WhatsApp</button></a>',
            unsafe_allow_html=True,
        )
      with col_e:
        assunto_email = urllib.parse.quote(
            "Relatório Executivo de Frota - Tabalmix Concreto"
        )
        corpo_email = urllib.parse.quote(
            "Prezado(a),\n\nSegue em anexo/resumo o relatório operacional da"
            " frota gerado pelo sistema Tabalmix Concreto"
            " Enterprise.\n\nAtenciosamente, Gestão de Frota."
        )
        st.markdown(
            f'<a href="mailto:?subject={assunto_email}&body={corpo_email}"'
            ' target="_blank"><button style="background-color: #0284c7; color:'
            " white; border: none; border-radius: 12px; padding: 12px 20px; font-"
            'weight: bold; cursor: pointer; width: 100%; box-shadow: 0 4px 12px'
            ' rgba(2,132,199,0.3);">✉️ Enviar Relatório via'
            " E-mail</button></a>",
            unsafe_allow_html=True,
        )
  else:
    st.info("nenhum equipamento cadastrado na frota.")

  st.divider()

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
    if not df_veiculos.empty and "tipo_equipamento" in df_veiculos.columns:
      tipo_counts = df_veiculos["tipo_equipamento"].value_counts()
      st.bar_chart(tipo_counts)
    else:
      st.info("sem dados suficientes de tipos para exibir.")

elif menu == "🚜 cadastro de equipamentos":
  st.title("🚜 cadastro completo de equipamentos e frota")
  if not status_usuario_ativo and not modo_admin_liberado:
    st.warning(
        "🔒 **Acesso restrito:** sua conta está inativa. Você pode visualizar"
        " os dados abaixo, mas o cadastro de novos itens está desativado."
    )
  with st.form("form_frota", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
      tag_prefixo = st.text_input("tag / prefixo (ex: EQ-001 / BET-12)")
      categoria_equipamento = st.text_input(
          "categoria do equipamento (ex: Linha Amarela, Linha Marrom, Linha"
          " Branca...)"
      )
      tipo_equipamento = st.text_input(
          "tipo de equipamento (ex: Caminhão Betoneira, Escavadeira, Pá"
          " Carregadeira...)"
      )
      marca = st.text_input("marca (ex: Volvo, Mercedes-Benz, Scania)")
      modelo = st.text_input("modelo (ex: FMX 420, Atego 2430)")
      ano = st.number_input(
          "ano de fabricação", min_value=1950, value=2024, step=1
      )
      chassi = st.text_input("número do chassi")
      renavam = st.text_input("número do renavam")
    with col2:
      placa = st.text_input("placa do veículo")
      crv = st.text_input("número do crv (certificado de registro)")
      cor = st.text_input("cor principal")
      combustivel = st.selectbox(
          "tipo de combustível",
          ["Diesel S10", "Diesel S500", "Gasolina", "Flex", "Elétrico"],
      )
      empresa = st.text_input("empresa / filial responsável")
      operador_condutor = st.text_input("operador / motorista responsável")
      horimetro_km = st.number_input(
          "horímetro ou km inicial", min_value=0, value=15000, step=100
      )
      status = st.selectbox(
          "situação operacional",
          ["Ativo", "Em Manutenção", "Parado", "Mobilizado"],
      )

    btn_cad_eq = st.form_submit_button("cadastrar equipamento completo")
    if btn_cad_eq:
      if not status_usuario_ativo and not modo_admin_liberado:
        st.error(
            "⚠️ Conta inativa: você não tem permissão para cadastrar novos"
            " equipamentos."
        )
      elif modelo:
        tag_final = (
            tag_prefixo.upper()
            if tag_prefixo and tag_prefixo.strip()
            else "EQ-00" + str(datetime.now().microsecond)[:3]
        )
        cat_final = (
            categoria_equipamento.strip()
            if categoria_equipamento and categoria_equipamento.strip()
            else "Geral"
        )
        tipo_final = (
            tipo_equipamento.strip()
            if tipo_equipamento and tipo_equipamento.strip()
            else "Equipamento"
        )
        cursor.execute(
            "INSERT INTO veiculos (tag_prefixo, categoria_equipamento,"
            " tipo_equipamento, marca, modelo, ano, chassi, renavam, placa, crv,"
            " cor, combustivel, empresa, operador_condutor, horimetro_km,"
            " status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                tag_final,
                cat_final,
                tipo_final,
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
                operador_condutor,
                int(horimetro_km),
                status,
            ),
        )
        conn.commit()
        st.success(
            f"✅ Equipamento '{tag_final}' cadastrado com ficha técnica"
            " completa!"
        )
        st.rerun()
      else:
        st.error("⚠️ Preencha ao menos o modelo do equipamento.")

  df_f = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_f.empty:
    if modo_admin_liberado:
      with st.expander(
          "⚙️ [ADMIN] Configurar Ordem Padrão das Colunas (Cadastro Frota)"
      ):
        cols_disp_f = list(df_f.columns)
        nova_ordem_f = st.text_input(
            "Ordem das colunas:",
            value=",".join(cols_disp_f),
            key="cfg_col_f",
        )
        if st.button("💾 Salvar Ordem", key="btn_sav_f"):
          cursor.execute(
              "INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas)"
              " VALUES ('cad_veiculos', ?)",
              (nova_ordem_f,),
          )
          conn.commit()
          st.success("✅ Ordem atualizada para todos os colaboradores!")
          st.rerun()
    exibir_tabela_padronizada(df_f, "cad_veiculos")

elif menu == "⛽ abastecimentos & combustível":
  st.title("⛽ controle de abastecimento e combustível")
  if not status_usuario_ativo and not modo_admin_liberado:
    st.warning(
        "🔒 **Acesso restrito:** sua conta está inativa. Você pode visualizar"
        " os registros, mas novos lançamentos estão desativados."
    )
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
    btn_cad_comb = st.form_submit_button("registrar abastecimento")
    if btn_cad_comb:
      if not status_usuario_ativo and not modo_admin_liberado:
        st.error(
            "⚠️ Conta inativa: você não tem permissão para registrar"
            " abastecimentos."
        )
      else:
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
    if modo_admin_liberado:
      with st.expander(
          "⚙️ [ADMIN] Configurar Ordem Padrão das Colunas (Abastecimento)"
      ):
        cols_disp_c = list(df_c.columns)
        nova_ordem_c = st.text_input(
            "Ordem das colunas:",
            value=",".join(cols_disp_c),
            key="cfg_col_c",
        )
        if st.button("💾 Salvar Ordem", key="btn_sav_c"):
          cursor.execute(
              "INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas)"
              " VALUES ('combustivel', ?)",
              (nova_ordem_c,),
          )
          conn.commit()
          st.success("✅ Ordem atualizada para todos os colaboradores!")
          st.rerun()
    exibir_tabela_padronizada(df_c, "combustivel")

elif menu == "🏗️ mobilização / desmobilização":
  st.title("🏗️ mobilização e desmobilização de obras")
  if not status_usuario_ativo and not modo_admin_liberado:
    st.warning(
        "🔒 **Acesso restrito:** sua conta está inativa. O modo de prestígio"
        " permite apenas visualização."
    )
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

    fotos_subidas = st.file_uploader(
        "📷 anexar fotos do check-list (selecione de 1 a 15 fotos: frente, trás,"
        " laterais, painel, pneus)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    btn_cad_mob = st.form_submit_button("registrar movimentação")
    if btn_cad_mob:
      if not status_usuario_ativo and not modo_admin_liberado:
        st.error(
            "⚠️ Conta inativa: você não tem permissão para registrar"
            " movimentações."
        )
      else:
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

        cursor.execute(
            "INSERT INTO mobilizacoes (equipamento, tipo_movimento,"
            " destino_origem, responsavel, data, observacao, foto_checklist)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(eq_mob).upper(),
                tipo_mov,
                destino,
                resp,
                str(dt_mob),
                obs,
                paths_str,
            ),
        )
        conn.commit()
        st.success(
            "✅ movimentação e check-list fotográfico múltiplo registrados com"
            " sucesso!"
        )
        st.rerun()

  df_mobs = pd.read_sql("SELECT * FROM mobilizacoes", conn)
  if not df_mobs.empty:
    if modo_admin_liberado:
      with st.expander(
          "⚙️ [ADMIN] Configurar Ordem Padrão das Colunas (Mobilizações)"
      ):
        cols_disp_m = list(df_mobs.columns)
        nova_ordem_m = st.text_input(
            "Ordem das colunas:",
            value=",".join(cols_disp_m),
            key="cfg_col_m",
        )
        if st.button("💾 Salvar Ordem", key="btn_sav_m"):
          cursor.execute(
              "INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas)"
              " VALUES ('mobilizacoes', ?)",
              (nova_ordem_m,),
          )
          conn.commit()
          st.success("✅ Ordem atualizada para todos os colaboradores!")
          st.rerun()
    exibir_tabela_padronizada(df_mobs, "mobilizacoes")

    for idx, row in df_mobs.iterrows():
      col_m_view1, col_m_view2 = st.columns([2, 1])
      with col_m_view1:
        if row.get("foto_checklist"):
          paths_lista = str(row["foto_checklist"]).split("|")
          with st.expander(
              f"📸 ver fotos do check-list #{row['id']} - {row['equipamento']} ("
              f"{len(paths_lista)} fotos)"
          ):
            for p_img in paths_lista:
              if p_img and os.path.exists(p_img):
                st.image(p_img, width=300)
      with col_m_view2:
        if status_usuario_ativo or modo_admin_liberado:
          pdf_mob_buf = gerar_pdf_mobilizacao(row)
          st.download_button(
              label=f"📄 baixar pdf check-list #{row['id']}",
              data=pdf_mob_buf,
              file_name=f"checklist_mobilizacao_{row['id']}.pdf",
              mime="application/pdf",
              key=f"dl_mob_pdf_{row['id']}",
          )

elif menu == "🛠️ ordens de serviço (os)":
  st.title("🛠️ gestão unificada de ordens de serviço (os)")
  if not status_usuario_ativo and not modo_admin_liberado:
    st.warning(
        "🔒 **Acesso restrito:** sua conta está inativa. Visualização de OS"
        " liberada, edição bloqueada."
    )
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
          "origem da falha", ["falha na operação", "falha na máquina"]
      )
    with c2:
      data_ab = st.date_input("data de abertura", value=datetime.now().date())
      hora_ab = st.text_input(
          "horário de abertura", value=datetime.now().strftime("%H:%M")
      )
      desc_prob = st.text_area(
          "descrição do problema apresentado pelo motorista"
      )

    btn_abrir_os = st.form_submit_button("abrir nova os")
    if btn_abrir_os:
      if not status_usuario_ativo and not modo_admin_liberado:
        st.error(
            "⚠️ Conta inativa: você não tem permissão para abrir novas OS."
        )
      else:
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
    if modo_admin_liberado:
      with st.expander(
          "⚙️ [ADMIN] Configurar Ordem Padrão das Colunas (Ordens de Serviço)"
      ):
        cols_disp_os = list(df_os.columns)
        nova_ordem_os = st.text_input(
            "Ordem das colunas:",
            value=",".join(cols_disp_os),
            key="cfg_col_os",
        )
        if st.button("💾 Salvar Ordem", key="btn_sav_os"):
          cursor.execute(
              "INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas)"
              " VALUES ('manutencoes', ?)",
              (nova_ordem_os,),
          )
          conn.commit()
          st.success("✅ Ordem atualizada para todos os colaboradores!")
          st.rerun()
    exibir_tabela_padronizada(df_os, "manutencoes")
  else:
    st.info("Nenhuma OS cadastrada no momento. Abra uma OS acima para gerenciar.")

  st.divider()
  st.markdown("### 🔴 encerramento e faturamento de os (etapa 2)")
  df_os_todas = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_os_todas.empty:
    with st.form("form_fechamento_os"):
      os_ids_disp = df_os_todas["id"].tolist()
      os_selecionada = st.selectbox(
          "selecione o id da os para fechar / gerenciar", os_ids_disp
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
        if not status_usuario_ativo and not modo_admin_liberado:
          st.error(
              "⚠️ Conta inativa: você não tem permissão para encerrar OS."
          )
        else:
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
              f"✅ OS #{os_selecionada} fechada com sucesso! Custo total:"
              f" R$ {custo_total:,.2f}"
          )
          st.rerun()

    for index, row in df_os_todas.iterrows():
      if str(row.get("status_os")) == "fechada":
        if status_usuario_ativo or modo_admin_liberado:
          pdf_os_buffer = gerar_pdf_os_tecnica(row)
          st.download_button(
              label=f"📄 Baixar PDF da OS Fechada #{row['id']}",
              data=pdf_os_buffer,
              file_name=f"ordem_servico_{row['id']}.pdf",
              mime="application/pdf",
              key=f"dl_os_{row['id']}",
          )
  else:
    st.info(
        "💡 *A Etapa 2 de encerramento ficará pronta para uso assim que a primeira"
        " OS for aberta na Etapa 1.*"
    )

elif menu == "🔩 peças e ferramentas":
  st.title("🔩 controle de peças e ferramentas")
  if not status_usuario_ativo and not modo_admin_liberado:
    st.warning(
        "🔒 **Acesso restrito:** conta inativa. Visualização permitida."
    )
  with st.form("form_pecas"):
    c1, c2 = st.columns(2)
    with c1:
      nome_i = st.text_input("nome da peça ou ferramenta")
      cat = st.text_input(
          "categoria (digite livremente, ex: Reposição, Filtro, Óleo, Pneu...)"
      )
    with c2:
      qtd = st.number_input("quantidade", min_value=1, value=1)
      v_unit = st.number_input("valor unitário (r$)", min_value=0.0)
    btn_cad_peca = st.form_submit_button("adicionar peça")
    if btn_cad_peca:
      if not status_usuario_ativo and not modo_admin_liberado:
        st.error(
            "⚠️ Conta inativa: você não tem permissão para cadastrar peças."
        )
      else:
        cat_final = (
            cat.strip() if cat and cat.strip() else "Geral"
        )
        cursor.execute(
            "INSERT INTO pecas (nome_item, categoria, quantidade,"
            " valor_unitario) VALUES (?, ?, ?, ?)",
            (nome_i, cat_final, qtd, v_unit),
        )
        conn.commit()
        st.success("✅ peça cadastrada com sucesso!")
        st.rerun()

  df_p = pd.read_sql("SELECT * FROM pecas", conn)
  if not df_p.empty:
    if modo_admin_liberado:
      with st.expander(
          "⚙️ [ADMIN] Configurar Ordem Padrão das Colunas (Peças)"
      ):
        cols_disp_p = list(df_p.columns)
        nova_ordem_p = st.text_input(
            "Ordem das colunas:",
            value=",".join(cols_disp_p),
            key="cfg_col_p",
        )
        if st.button("💾 Salvar Ordem", key="btn_sav_p"):
          cursor.execute(
              "INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas)"
              " VALUES ('pecas', ?)",
              (nova_ordem_p,),
          )
          conn.commit()
          st.success("✅ Ordem atualizada para todos os colaboradores!")
          st.rerun()
    exibir_tabela_padronizada(df_p, "pecas")

elif menu == "👥 gestão de clientes":
  st.title("👥 gestão de clientes")
  if not status_usuario_ativo and not modo_admin_liberado:
    st.warning(
        "🔒 **Acesso restrito:** conta inativa. Visualização de clientes"
        " liberada."
    )
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
      if not status_usuario_ativo and not modo_admin_liberado:
        st.error(
            "⚠️ Conta inativa: você não tem permissão para cadastrar clientes."
        )
      else:
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
    if modo_admin_liberado:
      with st.expander(
          "⚙️ [ADMIN] Configurar Ordem Padrão das Colunas (Clientes)"
      ):
        cols_disp_cl = list(df_cli.columns)
        nova_ordem_cl = st.text_input(
            "Ordem das colunas:",
            value=",".join(cols_disp_cl),
            key="cfg_col_cl",
        )
        if st.button("💾 Salvar Ordem", key="btn_sav_cl"):
          cursor.execute(
              "INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas)"
              " VALUES ('clientes', ?)",
              (nova_ordem_cl,),
          )
          conn.commit()
          st.success("✅ Ordem atualizada para todos os colaboradores!")
          st.rerun()
    exibir_tabela_padronizada(df_cli, "clientes")

elif menu == "💬 chat tabalmix pro & rede":
  st.title("💬 Chat Tabalmix Pro & Central de Operações")
  st.markdown(
      "Comunicação unificada Enterprise: chats privados 1 a 1, canais de"
      " equipes, mural de avisos fixados e alerta SOS de emergência."
  )

  # SCRIPTS JAVASCRIPT NATIVOS: ALARME SOS (ADMIN) + VIBRAÇÃO DE MENSAGEM (TODOS)
  st.markdown(
      """
        <script>
        function dispararAlarmeSOS() {
            try {
                if (navigator.vibrate) {
                    navigator.vibrate([600, 200, 600, 200, 1000]);
                }
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(950, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 1.5);
            } catch(e) {}
        }

        function vibrarMensagemChat() {
            try {
                if (navigator.vibrate) {
                    navigator.vibrate([200, 100, 200]);
                }
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(600, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.3);
            } catch(e) {}
        }
        </script>
    """,
      unsafe_allow_html=True,
  )

  # PAINEL DE ALERTA SOS EM CAMPO
  st.markdown(
      """
        <div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 14px; padding: 14px 20px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 15px rgba(239,68,68,0.1);">
            <div>
                <h4 style="margin: 0; color: #991b1b !important; font-size: 15.5px;">🚨 Botão de Pânico / Alerta SOS em Campo</h4>
                <p style="margin: 3px 0 0 0; font-size: 12px; color: #b91c1c;">Em caso de emergência ou pane grave, acione imediatamente para alertar a gerência e a oficina.</p>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  with st.expander("🚨 Acionar Alerta de Emergência SOS"):
    with st.form("form_sos_emergencia"):
      eq_sos = st.text_input(
          "Equipamento / Caminhão envolvido (ex: BET-05 ou EQ-01)"
      )
      motivo_sos = st.text_area(
          "Motivo do alerta (ex: pane elétrica, pneu estourado, acidente leve)"
      )
      btn_enviar_sos = st.form_submit_button(
          "🚨 DISPARAR ALERTA SOS IMEDIATO"
      )
      if btn_enviar_sos:
        if not motivo_sos:
          st.warning("⚠️ Descreva o motivo do alerta.")
        else:
          rem_sos = (
              usuario_atual["apelido"] if usuario_atual else "Colaborador"
          )
          dt_sos = datetime.now().strftime("%d/%m/%Y às %H:%M")
          cursor.execute(
              "INSERT INTO alertas_sos (remetente, equipamento, motivo,"
              " data_alerta, status) VALUES (?, ?, ?, ?, 'PENDENTE')",
              (rem_sos, eq_sos.upper(), motivo_sos, dt_sos),
          )
          conn.commit()
          st.error(
              "🚨 ALERTA SOS DISPARADO COM SUCESSO! A gerência foi notificada."
          )

  # EXIBIÇÃO DE ALERTAS SOS PENDENTES (DISPARA ALARME PARA ADMIN / GESTÃO / SEGURANÇA)
  cursor.execute(
      "SELECT * FROM alertas_sos WHERE status = 'PENDENTE' ORDER BY id DESC"
  )
  lista_sos_pend = cursor.fetchall()
  if lista_sos_pend and (
      modo_admin_liberado
      or (
          usuario_atual
          and any(
              c in usuario_atual["cargo"]
              for c in [
                  "Gestão",
                  "Gerente",
                  "Admin",
                  "Segurança",
                  "Engenheiro",
                  "Diretoria",
              ]
          )
      )
  ):
    st.markdown(
        """
            <script>
            if (typeof dispararAlarmeSOS === 'function') {
                dispararAlarmeSOS();
            }
            </script>
        """,
        unsafe_allow_html=True,
    )

  if lista_sos_pend:
    st.markdown(
        "<h4 style='color: #dc2626;'>⚠️ ALERTAS SOS ATIVOS NA FROTA:</h4>",
        unsafe_allow_html=True,
    )
    for sos_item in lista_sos_pend:
      col_sos_info, col_sos_btn = st.columns([4, 1])
      with col_sos_info:
        st.markdown(
            f"""
                <div style="background: #fef2f2; border-left: 5px solid #dc2626; padding: 12px; border-radius: 10px; margin-bottom: 8px; font-size: 13px; box-shadow: 0 3px 10px rgba(0,0,0,0.03);">
                    <b>🚨 Emergência #{sos_item[0]}</b> | Solicitante: <b>{sos_item[1]}</b> | Equipamento: <b>{sos_item[2]}</b><br>
                    <b>Relato:</b> {sos_item[3]} <br> <span style="color: #6b7280; font-size: 11.5px;">Registrado em: {sos_item[4]}</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
      with col_sos_btn:
        if st.button(f"✅ Resolver #{sos_item[0]}", key=f"btn_res_sos_{sos_item[0]}"):
          cursor.execute(
              "UPDATE alertas_sos SET status = 'RESOLVIDO' WHERE id = ?",
              (sos_item[0],),
          )
          conn.commit()
          st.success(f"✅ Alerta #{sos_item[0]} marcado como resolvido!")
          st.rerun()

  # MURAL DE AVISOS FIXADOS (PINNED NOTICES)
  st.markdown("---")
  st.markdown("#### 📌 Mural de Avisos Fixados (Diretoria / Oficina)")
  cursor.execute(
      "SELECT * FROM avisos_fixados ORDER BY id DESC LIMIT 2"
  )
  avisos_fix = cursor.fetchall()
  if avisos_fix:
    for av in avisos_fix:
      st.markdown(
          f"""
            <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(16,185,129,0.05);">
                <span style="font-size: 11.5px; font-weight: bold; color: #047857;">📌 Comunicado Oficial de {av[1]} ({av[3]})</span>
                <div style="font-size: 13.5px; color: #0f172a; margin-top: 3px;">{av[2]}</div>
            </div>
        """,
          unsafe_allow_html=True,
      )

  if modo_admin_liberado or (
      usuario_atual
      and any(
          c in usuario_atual["cargo"]
          for c in [
              "Gestão",
              "Gerente",
              "Admin",
              "Segurança",
              "Engenheiro",
              "Diretoria",
          ]
      )
  ):
    with st.expander("⚙️ [Gestão] Fixar Novo Aviso no Topo do Chat"):
      with st.form("form_fixar_aviso"):
        texto_aviso = st.text_area("Texto do comunicado oficial:")
        btn_fixar = st.form_submit_button("Fixar Comunicado")
        if btn_fixar and texto_aviso:
          autor_av = (
              usuario_atual["apelido"] if usuario_atual else "Administrador"
          )
          dt_av = datetime.now().strftime("%d/%m às %H:%M")
          cursor.execute(
              "INSERT INTO avisos_fixados (autor, mensagem, data_fixacao)"
              " VALUES (?, ?, ?)",
              (autor_av, texto_aviso, dt_av),
          )
          conn.commit()
          st.success("✅ Aviso fixado no topo com sucesso!")
          st.rerun()

  # SELETOR DE STATUS DO USUÁRIO
  st.markdown("---")
  status_escolhido = st.radio(
      "Meu Status Atual na Rede:",
      [
          "🟢 Disponível / Online",
          "🟡 Em Campo / Obra",
          "🔴 Ocupado / Reunião",
          "⚫ Ausente",
      ],
      horizontal=True,
  )

  # ABAS SUPERIORES
  tab_conversa, tab_contatos_rede = st.tabs(
      ["💬 Conversas & Chat Ativo", "👥 Rede de Colaboradores & Privado"]
  )

  if "sala_chat_ativa" not in st.session_state:
    st.session_state["sala_chat_ativa"] = "Geral (Equipe)"

  remetente_atual = (
      usuario_atual["apelido"]
      if usuario_atual
      else ("Administrador" if modo_admin_liberado else "Colaborador")
  )
  cargo_atual = usuario_atual["cargo"] if usuario_atual else "Gestão / ADM"
  link_meet = "https://meet.jit.si/TabalmixConcretoEnterprisePro"

  with tab_conversa:
    st.markdown(f"#### 🗨️ Conversa: `{st.session_state['sala_chat_ativa']}`")

    # CABEÇALHO DO CHAT ULTRA MODERNO
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 14px 20px; border-radius: 14px 14px 0 0; display: flex; align-items: center; justify-content: space-between; color: white; box-shadow: 0 6px 18px rgba(5,150,105,0.2);">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background: rgba(255,255,255,0.2); width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 19px; font-weight: bold; border: 2px solid white;">💬</div>
                <div>
                    <h4 style="margin: 0; color: white !important; font-size: 15.5px;">{st.session_state['sala_chat_ativa']}</h4>
                    <span style="font-size: 11px; opacity: 0.9;">status: {status_escolhido} • criptografia enterprise</span>
                </div>
            </div>
            <div style="display: flex; gap: 10px;">
                <a href="{link_meet}" target="_blank" title="Chamada de Áudio" style="background: rgba(255,255,255,0.25); padding: 8px 14px; border-radius: 50%; color: white; text-decoration: none; font-size: 15px; border: 1px solid rgba(255,255,255,0.4);">📞</a>
                <a href="{link_meet}" target="_blank" title="Chamada de Vídeo" style="background: rgba(255,255,255,0.25); padding: 8px 14px; border-radius: 50%; color: white; text-decoration: none; font-size: 15px; border: 1px solid rgba(255,255,255,0.4);">📹</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ÁREA DE MENSAGENS COM ESTILO FLUIDO
    st.markdown(
        """
        <div style="background: #ffffff; padding: 18px; border-radius: 0 0 14px 14px; border: 1px solid #e2e8f0; border-top: none; min-height: 280px; max-height: 380px; overflow-y: auto; margin-bottom: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.02);">
        """,
        unsafe_allow_html=True,
    )

    canal_corrente = st.session_state["sala_chat_ativa"]
    if canal_corrente == "Geral (Equipe)":
      df_msgs = pd.read_sql(
          "SELECT * FROM chat_interno WHERE destinatario = 'Geral (Equipe)'"
          " ORDER BY id DESC LIMIT 25",
          conn,
      )
    else:
      df_msgs = pd.read_sql(
          "SELECT * FROM chat_interno WHERE (destinatario = ? AND remetente LIKE"
          " ?) OR (destinatario LIKE ? AND remetente LIKE ?) ORDER BY id DESC"
          " LIMIT 25",
          conn,
          params=(
              canal_corrente,
              f"%{remetente_atual}%",
              f"%{remetente_atual}%",
              f"%{canal_corrente.split()[0]}%",
          ),
      )
      if df_msgs.empty:
        df_msgs = pd.read_sql(
            "SELECT * FROM chat_interno WHERE destinatario = ? ORDER BY id DESC"
            " LIMIT 25",
            conn,
            params=(canal_corrente,),
        )

    if not df_msgs.empty:
      ultima_msg_remetente = str(df_msgs.iloc[0]["remetente"])
      if (
          remetente_atual
          and remetente_atual.lower() not in ultima_msg_remetente.lower()
      ):
        st.markdown(
            """
                <script>
                if (typeof vibrarMensagemChat === 'function') {
                    vibrarMensagemChat();
                }
                </script>
            """,
            unsafe_allow_html=True,
        )

      for _, row_m in df_msgs.iterrows():
        is_me = (
            remetente_atual.lower() in str(row_m["remetente"]).lower()
            if remetente_atual
            else False
        )
        bg_balao = "#ecfdf5" if is_me else "#f8fafc"
        border_balao = "#10b981" if is_me else "#cbd5e1"
        align_balao = "margin-left: auto;" if is_me else "margin-right: auto;"

        st.markdown(
            f"""
                <div style="background: {bg_balao}; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; max-width: 82%; {align_balao} box-shadow: 0 3px 10px rgba(0,0,0,0.03); border: 1px solid {border_balao};">
                    <div style="font-size: 11px; color: #047857; font-weight: bold; margin-bottom: 3px;">{row_m['remetente']}</div>
                    <div style="font-size: 14px; color: #0f172a; white-space: pre-wrap; line-height: 1.4;">{row_m['mensagem']}</div>
                    <div style="font-size: 10px; color: #64748b; text-align: right; margin-top: 4px;">{row_m['data_envio']}</div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        if row_m["arquivo_path"] and os.path.exists(str(row_m["arquivo_path"])):
          with open(row_m["arquivo_path"], "rb") as f_down:
            st.download_button(
                label=f"📥 Baixar anexo: {row_m['arquivo_nome']}",
                data=f_down.read(),
                file_name=row_m["arquivo_nome"],
                key=f"dl_sala_msg_{row_m['id']}",
            )
    else:
      st.markdown(
          "<p style='text-align: center; color: #64748b; font-size: 13px;"
          " margin-top: 40px;'>Inicie a conversa enviando uma mensagem"
          " abaixo!</p>",
          unsafe_allow_html=True,
      )

    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("form_chat_sala_principal", clear_on_submit=True):
      msg_sala_txt = st.text_input("Digite sua mensagem corporativa...")
      file_sala_up = st.file_uploader(
          "Anexar documento ou foto",
          type=["png", "jpg", "jpeg", "pdf", "docx", "xlsx"],
      )
      btn_enviar_sala_pro = st.form_submit_button("➤ Enviar Mensagem")

      if btn_enviar_sala_pro:
        if not msg_sala_txt.strip() and not file_sala_up:
          st.warning("⚠️ Digite uma mensagem ou anexe um arquivo.")
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
                  canal_corrente,
                  cargo_atual,
                  msg_sala_txt,
                  path_s,
                  nome_s,
                  data_env_s,
              ),
          )
          conn.commit()
          st.success("✅ Mensagem enviada!")
          st.rerun()

  with tab_contatos_rede:
    st.markdown("#### 👥 Rede de Colaboradores & Conversas 1 a 1")
    col_btn_g, col_btn_adm = st.columns(2)
    with col_btn_g:
      if st.button("💬 Canal Geral da Equipe", key="btn_rede_geral_pro"):
        st.session_state["sala_chat_ativa"] = "Geral (Equipe)"
        st.success("✅ Conversa alterada para Canal Geral! Volte na aba 'Conversas'.")
        st.rerun()
    with col_btn_adm:
      if st.button("🛡️ Suporte Técnico ADM", key="btn_rede_adm_pro"):
        st.session_state["sala_chat_ativa"] = "Suporte ADM"
        st.success("✅ Conversa alterada para Suporte ADM! Volte na aba 'Conversas'.")
        st.rerun()

    st.markdown("---")
    st.markdown("**Contatos Ativos para Chat Privado:**")
    cursor.execute(
        "SELECT apelido, cargo_setor, email FROM usuarios_sistema WHERE"
        " status_assinatura = 'Ativo'"
    )
    colaboradores_rede = cursor.fetchall()

    encontrou_contato = False
    if colaboradores_rede:
      for idx_r, (r_nome, r_cargo, r_email) in enumerate(colaboradores_rede):
        nome_valido = (
            r_nome
            if r_nome and r_nome != "None"
            else (r_email.split("@")[0] if r_email else "Colaborador")
        )
        cargo_valido = r_cargo if r_cargo and r_cargo != "None" else "Operacional"

        if nome_valido != remetente_atual:
          encontrou_contato = True
          nome_privado = f"Privado: {nome_valido} ({cargo_valido})"
          st.markdown(
              f"""
                    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.02);">
                        <div>
                            <span style="font-size: 15px; font-weight: bold; color: #0f172a;">👤 {nome_valido}</span><br>
                            <span style="font-size: 12px; color: #64748b;">Setor: {cargo_valido} • 🟢 Online</span>
                        </div>
                    </div>
                """,
              unsafe_allow_html=True,
          )
          if st.button(
              f"🔒 Abrir Chat Privado com {nome_valido}",
              key=f"btn_chat_privado_{idx_r}",
          ):
            st.session_state["sala_chat_ativa"] = nome_privado
            st.success(
                f"✅ Chat privado com {nome_valido} aberto! Volte na aba"
                " 'Conversas & Chat Ativo'."
            )
            st.rerun()

    if not encontrou_contato:
      st.info(
          "Nenhum outro colaborador ativo no momento (você é o único usuário"
          " logado ou os demais cadastros estão sem apelido definido)."
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
        exibir_tabela_padronizada(df_eq_info, "busca_eq_info")

        st.markdown("#### 🛠️ histórico de ordens de serviço")
        df_os_eq = pd.read_sql(
            "SELECT * FROM manutencoes WHERE tag_prefixo = ?",
            conn,
            params=(eq_selecionado_historico,),
        )
        if not df_os_eq.empty:
          exibir_tabela_padronizada(df_os_eq, "busca_os_eq")
        else:
          st.info("nenhuma os registrada para este equipamento.")

        st.markdown("#### ⛽ histórico de abastecimentos")
        df_comb_eq = pd.read_sql(
            "SELECT * FROM combustivel WHERE equipamento = ?",
            conn,
            params=(eq_selecionado_historico,),
        )
        if not df_comb_eq.empty:
          exibir_tabela_padronizada(df_comb_eq, "busca_comb_eq")
        else:
          st.info("nenhum abastecimento registrado para este equipamento.")
  else:
    st.info("nenhum equipamento cadastrado para realizar consultas.")

elif menu == "⚙️ meu perfil / dados":
  st.title("⚙️ atualização de perfil")
  if usuario_atual:
    st.info(f"logado como: {usuario_atual['nome']} ({usuario_atual['email']})")

elif menu == "⚙️ painel de licença (admin)":
  st.title("⚙️ painel administrativo de colaboradores")
  st.markdown("Gerencie o status de acesso ou remova cadastros do sistema:")

  df_users = pd.read_sql(
      "SELECT id, nome_completo, email, status_assinatura, cargo_setor,"
      " data_cadastro FROM usuarios_sistema",
      conn,
  )
  if not df_users.empty:
    exibir_tabela_padronizada(df_users, "usuarios_sistema")

    st.markdown("---")
    st.subheader("🛠️ Ações Administrativas de Gestão de Usuários")

    user_dict_map = {
        f"#{r['id']} - {r['nome_completo']} ({r['email']})": r["id"]
        for _, r in df_users.iterrows()
    }

    if user_dict_map:
      sel_user_str = st.selectbox(
          "Selecione o colaborador para gerenciar:", list(user_dict_map.keys())
      )
      selected_user_id = user_dict_map[sel_user_str]

      col_acao1, col_acao2 = st.columns(2)
      with col_acao1:
        novo_status_adm = st.selectbox(
            "Alterar status de assinatura:", ["Ativo", "Inativo"]
        )
        if st.button("🔄 Atualizar Status do Usuário"):
          cursor.execute(
              "UPDATE usuarios_sistema SET status_assinatura = ? WHERE id = ?",
              (novo_status_adm, selected_user_id),
          )
          conn.commit()
          st.success(
              f"✅ Status do usuário #{selected_user_id} atualizado para"
              f" '{novo_status_adm}' com sucesso!"
          )
          st.rerun()

      with col_acao2:
        st.markdown(
            "<p style='color: #dc2626; font-weight: bold; margin-bottom:"
            " 18px;'>⚠️ Zona de Exclusão</p>",
            unsafe_allow_html=True,
        )
        if st.button("🗑️ Excluir Definitivamente este Cadastro"):
          cursor.execute(
              "DELETE FROM usuarios_sistema WHERE id = ?", (selected_user_id,)
          )
          conn.commit()
          st.success(
              f"✅ Cadastro #{selected_user_id} excluído com sucesso!"
          )
          st.rerun()
  else:
    st.info("nenhum usuário cadastrado.")

# ==============================================================================
# WIDGET FLUTUANTE DE CHAT RÁPIDO & VÍDEO NO CANTO INFERIOR DIREITO
# ==============================================================================
if "widget_chat_aberto" not in st.session_state:
  st.session_state["widget_chat_aberto"] = False

cursor.execute(
    "SELECT COUNT(*) FROM chat_interno WHERE destinatario LIKE ? OR destinatario"
    " = 'Geral (Equipe)'",
    (
        f"%{usuario_atual.get('apelido', '')}%"
        if usuario_atual
        else "%ADM%",
    ),
)
res_n = cursor.fetchone()
tem_msgs_pendentes = res_n[0] > 0 if res_n else False

if st.session_state["widget_chat_aberto"]:
  st.markdown(
      """
        <div style="position: fixed; bottom: 20px; right: 20px; width: 360px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 18px; box-shadow: 0 20px 45px rgba(0,0,0,0.25); z-index: 999999; padding: 16px; font-family: 'Plus Jakarta Sans', sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 12px;">
                <div style="font-weight: 800; font-size: 14px; color: #047857;">💬 Chat Tabalmix Rápido</div>
    """,
      unsafe_allow_html=True,
  )

  col_wc_l, col_wc_r = st.columns([4, 1])
  with col_wc_r:
    if st.button("❌", key="btn_fechar_widget_chat_flutuante"):
      st.session_state["widget_chat_aberto"] = False
      st.rerun()

  st.markdown(
      '<a href="https://meet.jit.si/TabalmixConcretoEnterprisePro"'
      ' target="_blank"><button style="background: #059669; color: white; width:'
      ' 100%; border: none; padding: 9px; border-radius: 10px; font-weight:'
      ' bold; cursor: pointer; margin-bottom: 12px; box-shadow: 0 4px 12px'
      ' rgba(5,150,105,0.3);">📹 Iniciar Vídeo Chamada Rápida</button></a>',
      unsafe_allow_html=True,
  )

  rem_widget_n = (
      usuario_atual["apelido"]
      if usuario_atual
      else ("Administrador" if modo_admin_liberado else "Colaborador")
  )
  rem_widget_c = usuario_atual["cargo"] if usuario_atual else "Gestão / ADM"

  with st.form("form_widget_chat_rapido", clear_on_submit=True):
    msg_w_input = st.text_input("Mensagem rápida:")
    btn_w_env = st.form_submit_button("Enviar")
    if btn_w_env and msg_w_input.strip():
      data_w_str = datetime.now().strftime("%d/%m às %H:%M")
      cursor.execute(
          "INSERT INTO chat_interno (remetente, destinatario, cargo,"
          " mensagem, arquivo_path, arquivo_nome, data_envio) VALUES (?, ?,"
          " ?, ?, ?, ?, ?)",
          (
              f"{rem_widget_n} ({rem_widget_c})",
              "Suporte ADM",
              rem_widget_c,
              msg_w_input,
              "",
              "",
              data_w_str,
          ),
      )
      conn.commit()
      st.success("✅ Enviado!")
      st.rerun()

  st.markdown("---")
  st.markdown("##### 📜 Últimas Mensagens:")
  df_widget_hist = pd.read_sql(
      "SELECT * FROM chat_interno ORDER BY id DESC LIMIT 3", conn
  )
  if not df_widget_hist.empty:
    for _, rw_w in df_widget_hist.iterrows():
      st.markdown(
          f"""
                <div style="background: #f8fafc; border-radius: 10px; padding: 8px; margin-bottom: 6px; font-size: 11.5px; border: 1px solid #e2e8f0;">
                    <b>{rw_w['remetente']}</b><br>
                    <span style="color: #0f172a;">{rw_w['mensagem']}</span>
                </div>
            """,
          unsafe_allow_html=True,
      )
  else:
    st.info("Sem mensagens recentes.")

else:
  badge_w = "🔴" if tem_msgs_pendentes else "🟢"
  st.markdown(
      """
        <style>
        .widget-chat-btn {
            position: fixed;
            bottom: 25px;
            right: 25px;
            background: #059669;
            color: white;
            border-radius: 50px;
            padding: 12px 20px;
            box-shadow: 0 10px 30px rgba(5,150,105,0.4);
            cursor: pointer;
            z-index: 999999;
            font-weight: 800;
            font-size: 13.5px;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

  col_bw_l, col_bw_r = st.columns([5, 1.4])
  with col_bw_r:
    if st.button(f"{badge_w} Chat Pro", key="btn_abrir_widget_chat_flutu"):
      st.session_state["widget_chat_aberto"] = True
      st.rerun()
