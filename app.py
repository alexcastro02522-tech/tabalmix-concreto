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

# ESTILIZAÇÃO VISUAL PREMIUM ENTERPRISE ORIGINAL (UX/UI World Class - Sem Regressões)
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

    tab_login, tab_cadastro, tab_recuperar, tab_pin = st.tabs([
        "🔑 entrar na conta",
        "📝 cadastrar colaborador",
        "🔄 recuperar senha",
        "🔐 pin rápido (obra)",
    ])

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
        btn_cadastrar = st.form_submit_button("cadastrar e solicitar liberação")

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
                  " 'Inativo', 'Aguardando Pagamento/Liberação', ?, ?, ?)",
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
                  "✅ Conta cadastrada com sucesso! O acesso completo será liberado assim que o pagamento/aprovação for confirmado pela administração."
              )
            except Exception as e:
              st.error(f"⚠️ erro ao cadastrar (e-mail já cadastrado?): {e}")
          else:
            st.error("⚠️ preencha os campos obrigatórios.")

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

    with tab_pin:
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
          "⚠️ **conta inativa / aguardando liberação:** modo de prestígio (leitura) habilitado."
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
  else:
    st.info("nenhum equipamento cadastrado na frota.")

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
    exibir_tabela_padronizada(df_f, "cad_veiculos")

    st.markdown("---")
    st.markdown("### 🗑️ Remover Equipamento Duplicado ou Errado")
    with st.form("form_excluir_veiculo"):
      veiculos_map = {
          f"ID #{r['id']} - Tag: {r.get('tag_prefixo', '-')} | Modelo:"
          f" {r.get('modelo', '-')} | Placa: {r.get('placa', '-')}": r["id"]
          for _, r in df_f.iterrows()
      }
      sel_veiculo_excluir = st.selectbox(
          "Selecione o equipamento para excluir permanentemente:",
          list(veiculos_map.keys()),
      )
      btn_conf_excluir = st.form_submit_button(
          "🗑️ Excluir Equipamento Selecionado"
      )

      if btn_conf_excluir:
        id_para_apagar = veiculos_map[sel_veiculo_excluir]
        cursor.execute("DELETE FROM veiculos WHERE id = ?", (id_para_apagar,))
        conn.commit()
        st.success(
            f"✅ Equipamento #{id_para_apagar} excluído com sucesso da frota!"
        )
        st.rerun()

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
      st.success("✅ abastecimento registrado com sucesso!")
      st.rerun()

  df_c = pd.read_sql("SELECT * FROM combustivel", conn)
  if not df_c.empty:
    exibir_tabela_padronizada(df_c, "combustivel")

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
      st.success("✅ movimentação registrada com sucesso!")
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

  st.markdown("### 🟢 abertura de nova os (etapa 1)")
  with st.form("form_abertura_os", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
      if tags_disponiveis:
        tag_os = st.selectbox("tag / prefixo do equipamento", tags_disponiveis)
      else:
        tag_os = st.text_input("tag / prefixo do equipamento (manual)")
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
      tag_final_os = (
          str(tag_os).upper() if tag_os and str(tag_os).strip() else "EQ-GERAL"
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
  df_os = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_os.empty:
    exibir_tabela_padronizada(df_os, "manutencoes")

elif menu == "🔩 peças e ferramentas":
  st.title("🔩 controle de peças e ferramentas")
  with st.form("form_pecas"):
    c1, c2 = st.columns(2)
    with c1:
      nome_i = st.text_input("nome da peça ou ferramenta")
      cat = st.text_input("categoria")
    with c2:
      qtd = st.number_input("quantidade", min_value=1, value=1)
      v_unit = st.number_input("valor unitário (r$)", min_value=0.0)
    btn_cad_peca = st.form_submit_button("adicionar peça")
    if btn_cad_peca:
      cat_final = cat.strip() if cat and cat.strip() else "Geral"
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
      st.success("✅ cliente salvo com sucesso!")
      st.rerun()

  df_cli = pd.read_sql("SELECT * FROM clientes", conn)
  if not df_cli.empty:
    exibir_tabela_padronizada(df_cli, "clientes")

elif menu == "💬 chat tabalmix pro & rede":
  st.title("💬 Chat Tabalmix Pro & Chamada Interna")
  st.markdown(
      "Comunicação unificada e **Chamada de Vídeo Direta** dentro do"
      " sistema."
  )

  # BOTÃO DIRETO E VISÍVEL DE CHAMADA DE VÍDEO NATIVA
  with st.expander("🎥 ABRIR CÂMARA DE VÍDEO / ÁUDIO NA TELA", expanded=True):
    st.markdown(
        "Ligue a câmara diretamente no seu telemóvel para falar com a equipe:"
    )
    st.components.v1.html(
        """
        <div style="background: #0f172a; border-radius: 16px; padding: 15px; text-align: center; color: white; font-family: sans-serif;">
            <video id="localVideo" autoplay playsinline muted style="width: 100%; max-height: 220px; border-radius: 12px; background: #1e293b; border: 2px solid #059669; object-fit: cover; margin-bottom: 10px;"></video>
            <div>
                <button onclick="ligarCamera()" style="background: #059669; color: white; border: none; padding: 10px 18px; border-radius: 10px; font-weight: bold; cursor: pointer; font-size: 13px;">🟢 Ligar Câmara</button>
                <button onclick="desligarCamera()" style="background: #dc2626; color: white; border: none; padding: 10px 18px; border-radius: 10px; font-weight: bold; cursor: pointer; font-size: 13px; margin-left: 10px;">🔴 Desligar</button>
            </div>
        </div>
        <script>
        let localStream = null;
        async function ligarCamera() {
            try {
                localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                document.getElementById('localVideo').srcObject = localStream;
            } catch (err) {
                alert("Erro ao aceder à câmara: " + err);
            }
        }
        function desligarCamera() {
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                document.getElementById('localVideo').srcObject = null;
            }
        }
        </script>
        """,
        height=310,
    )

  st.markdown("---")
  if "sala_chat_ativa" not in st.session_state:
    st.session_state["sala_chat_ativa"] = "Geral (Equipe)"

  remetente_atual = (
      usuario_atual["apelido"]
      if usuario_atual
      else ("Administrador" if modo_admin_liberado else "Colaborador")
  )
  cargo_atual = usuario_atual["cargo"] if usuario_atual else "Gestão / ADM"

  st.markdown(f"#### 🗨️ Conversa Ativa: `{st.session_state['sala_chat_ativa']}`")
  df_msgs = pd.read_sql(
      "SELECT * FROM chat_interno WHERE destinatario = 'Geral (Equipe)'"
      " ORDER BY id DESC LIMIT 20",
      conn,
  )
  if not df_msgs.empty:
    for _, row_m in df_msgs.iterrows():
      st.markdown(
          f"""
            <div style="background: #f8fafc; border-radius: 10px; padding: 10px; margin-bottom: 8px; border: 1px solid #cbd5e1;">
                <b style="color: #047857; font-size: 12px;">{row_m['remetente']}</b><br>
                <span style="font-size: 13.5px; color: #0f172a;">{row_m['mensagem']}</span>
            </div>
        """,
          unsafe_allow_html=True,
      )

  with st.form("form_chat_sala_principal", clear_on_submit=True):
    msg_sala_txt = st.text_input("Escreva sua mensagem...")
    btn_enviar_sala_pro = st.form_submit_button("Enviar Mensagem")
    if btn_enviar_sala_pro and msg_sala_txt.strip():
      data_env_s = datetime.now().strftime("%d/%m às %H:%M")
      cursor.execute(
          "INSERT INTO chat_interno (remetente, destinatario, cargo,"
          " mensagem, arquivo_path, arquivo_nome, data_envio) VALUES (?, ?,"
          " ?, ?, ?, ?, ?)",
          (
              f"{remetente_atual} ({cargo_atual})",
              "Geral (Equipe)",
              cargo_atual,
              msg_sala_txt,
              "",
              "",
              data_env_s,
          ),
      )
      conn.commit()
      st.success("✅ Mensagem enviada!")
      st.rerun()

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
        " cargo_setor, pin_rapido FROM usuarios_sistema WHERE id = ?",
        (user_id_ativo,),
    )
    dados_db = cursor.fetchone()
    if dados_db:
      n_comp, n_cpf, n_email, n_cel, n_apelido, n_cargo, n_pin = dados_db
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

elif menu == "⚙️ painel de licença (admin)":
  st.title("⚙️ painel administrativo de colaboradores")
  df_users = pd.read_sql("SELECT * FROM usuarios_sistema", conn)
  if not df_users.empty:
    exibir_tabela_padronizada(df_users, "usuarios_sistema")
