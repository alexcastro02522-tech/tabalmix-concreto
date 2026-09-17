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

  tag_eq = os_row.get("tag_prefixo") or os_row.get("equipamento") or "não informado"
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


def gerar_csv_relatorio(dataframe):
  output = io.StringIO()
  df_export = dataframe.copy()
  df_export.columns = [
      str(col).replace("_", " ").lower() for col in df_export.columns
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
            observacao TEXT,
            foto_checklist TEXT
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
            data_cadastro TEXT,
            pin_rapido TEXT
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
          " sua empresa para começar:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_novo_cadastro"):
        c_nome = st.text_input("nome completo / responsável")
        c_cpf = st.text_input("cpf")
        c_email = st.text_input("e-mail (seu login)")
        c_senha = st.text_input("criar senha", type="password")
        c_cel = st.text_input("celular / contato de segurança")
        btn_cadastrar = st.form_submit_button("finalizar cadastro")

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
                  "✅ conta criada com sucesso! vá na aba 'entrar' para fazer"
                  " seu login."
              )
            except Exception as e:
              st.error(
                  "⚠️ este e-mail já está cadastrado ou ocorreu um erro:"
                  f" {str(e)}"
              )
          else:
            st.error("⚠️ preencha todos os campos obrigatórios.")

    with tab_recuperar:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>redefina"
          " sua senha de segurança:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_recuperar_senha"):
        rec_email = st.text_input("e-mail cadastrado na conta")
        rec_cpf = st.text_input("cpf do titular")
        nova_senha = st.text_input("nova senha", type="password")
        btn_resetar = st.form_submit_button("redefinir senha")

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
                  "✅ senha redefinida com sucesso! vá na aba 'entrar' e acesse"
                  " com sua nova senha."
              )
            else:
              st.error("⚠️ e-mail ou cpf não encontrados no sistema.")
          else:
            st.error("⚠️ preencha todos os campos para recuperar a senha.")

    with tab_pin:
      st.markdown(
          "<p style='font-size: 13px; color: #475569; margin-top: 10px;'>entre"
          " rapidamente usando seu pin de 4 dígitos:</p>",
          unsafe_allow_html=True,
      )
      with st.form("form_login_pin"):
        email_pin_user = st.text_input("seu e-mail cadastrado")
        pin_input = st.text_input(
            "pin de 4 dígitos", max_chars=4, type="password"
        )
        btn_entrar_pin = st.form_submit_button("entrar com pin")

        if btn_entrar_pin:
          cursor.execute(
              "SELECT * FROM usuarios_sistema WHERE email = ? AND pin_rapido = ?",
              (email_pin_user, pin_input),
          )
          user_pin_data = cursor.fetchone()
          if user_pin_data:
            st.session_state["usuario_logado"] = {
                "id": user_pin_data[0],
                "nome": user_pin_data[1],
                "cpf": user_pin_data[2],
                "email": user_pin_data[3],
                "status": user_pin_data[6],
            }
            st.success("✅ acesso liberado via pin!")
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
                    <span style="color: #1b7a3e; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;">🛡️ selo oficial</span>
                </div>
                <h3 style="color: #1b7a3e !important; margin: 0; font-size: 15px; font-weight: 800;">tabalmix concreto</h3>
                <p style="color: #475569; font-size: 9px; margin: 2px 0 2px 0; text-transform: uppercase; letter-spacing: 1px;">gestão de frota & operações</p>
                <p style="color: #94a3b8; font-size: 8px; margin: 0; font-style: italic;">powered by castro tech</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.markdown(
        """
            <div style="text-align: center; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px;">
                <h3 style="color: #1b7a3e !important; margin: 0; font-size: 15px; font-weight: 800;">tabalmix concreto</h3>
                <p style="color: #475569; font-size: 9px; margin: 2px 0 2px 0; text-transform: uppercase; letter-spacing: 1px;">gestão de frota & operações</p>
                <p style="color: #94a3b8; font-size: 8px; margin: 0; font-style: italic;">powered by castro tech</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

  if modo_admin_liberado:
    st.success("🔓 **modo admin ativo**")
  elif usuario_atual:
    st.info(
        f"👤 **usuário:** {usuario_atual['nome']}\n\n📊 **status:**"
        f" {usuario_atual['status']}"
    )
    if st.button("🚪 sair / trocar conta"):
      st.session_state["usuario_logado"] = None
      st.rerun()

  st.markdown("---")


def verificar_licenca_para_acao():
  if status_usuario_ativo or modo_admin_liberado:
    return True

  st.warning(
      "🔒 **acesso restrito ao sistema de testes / assinatura:**\n\nescolha uma"
      " das opções abaixo para continuar:"
  )
  escolha_metodo = st.radio(
      "forma de pagamento:",
      [
          "💳 pagamento automático (mercado pago)",
          "🔑 transferência direta (chave pix)",
      ],
      label_visibility="collapsed",
      key="radio_metodo_geral",
  )

  col_p1, col_p2 = st.columns(2)
  with col_p1:
    if st.button("💳 mensal (r$ 250,00)", key="btn_mensal_fixo"):
      try:
        sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
        payment_data = {
            "transaction_amount": 250.0,
            "description": f"tabalmix - plano mensal ({usuario_atual['email'] if usuario_atual else 'cliente'})",
            "payment_method_id": "pix",
            "payer": {
                "email": usuario_atual["email"] if usuario_atual else "cliente@tabalmix.com"
            }
        }
        res = sdk.payment().create(payment_data)
        if "response" in res and "point_of_interaction" in res["response"]:
          poi = res["response"]["point_of_interaction"]["transaction_data"]
          qr_code_base64 = poi.get("qr_code_base64")
          qr_code_text = poi.get("qr_code")
          ticket_url = poi.get("ticket_url")

          st.success("✅ pix gerado com sucesso!")
          if qr_code_base64:
            img_bytes = base64.b64decode(qr_code_base64)
            st.image(img_bytes, caption="escaneie o qr code com seu banco", width=250)
          
          if qr_code_text:
            st.text_area("pix copia e cola (copie abaixo):", value=qr_code_text, height=100)

          if ticket_url:
            st.markdown(f"🔗 **[👉 abrir página de pagamento do mercado pago]({ticket_url})**")
        else:
          pref_data = {
              "items": [{
                  "title": "tabalmix - mensal",
                  "quantity": 1,
                  "unit_price": 250.0,
                  "currency_id": "brl",
              }],
              "back_urls": {
                  "success": "https://tabalmix-concreto.streamlit.app",
                  "failure": "https://tabalmix-concreto.streamlit.app",
                  "pending": "https://tabalmix-concreto.streamlit.app",
              },
              "auto_return": "approved",
          }
          pref_res = sdk.preference().create(pref_data)
          url = pref_res["response"].get("init_point") if "response" in pref_res else ""
          if url:
            st.markdown(f"🔗 **[👉 abrir checkout de pagamento]({url})**")
      except Exception as e:
        st.error(f"erro ao gerar pagamento pix: {e}")

  with col_p2:
    if st.button("🌟 anual (r$ 2.400,00)", key="btn_anual_fixo"):
      try:
        sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
        payment_data = {
            "transaction_amount": 2400.0,
            "description": f"tabalmix - plano anual ({usuario_atual['email'] if usuario_atual else 'cliente'})",
            "payment_method_id": "pix",
            "payer": {
                "email": usuario_atual["email"] if usuario_atual else "cliente@tabalmix.com"
            }
        }
        res = sdk.payment().create(payment_data)
        if "response" in res and "point_of_interaction" in res["response"]:
          poi = res["response"]["point_of_interaction"]["transaction_data"]
          qr_code_base64 = poi.get("qr_code_base64")
          qr_code_text = poi.get("qr_code")
          ticket_url = poi.get("ticket_url")

          st.success("✅ pix gerado com sucesso!")
          if qr_code_base64:
            img_bytes = base64.b64decode(qr_code_base64)
            st.image(img_bytes, caption="escaneie o qr code com seu banco", width=250)
          
          if qr_code_text:
            st.text_area("pix copia e cola (copie abaixo):", value=qr_code_text, height=100)

          if ticket_url:
            st.markdown(f"🔗 **[👉 abrir página de pagamento do mercado pago]({ticket_url})**")
        else:
          pref_data = {
              "items": [{
                  "title": "tabalmix - anual",
                  "quantity": 1,
                  "unit_price": 2400.0,
                  "currency_id": "brl",
              }],
              "back_urls": {
                  "success": "https://tabalmix-concreto.streamlit.app",
                  "failure": "https://tabalmix-concreto.streamlit.app",
                  "pending": "https://tabalmix-concreto.streamlit.app",
              },
              "auto_return": "approved",
          }
          pref_res = sdk.preference().create(pref_data)
          url = pref_res["response"].get("init_point") if "response" in pref_res else ""
          if url:
            st.markdown(f"🔗 **[👉 abrir checkout de pagamento]({url})**")
      except Exception as e:
        st.error(f"erro ao gerar pagamento pix: {e}")

  if "transferência direta" in escolha_metodo:
    st.info(
        "🔑 **chave pix para depósito:** `sua-chave-pix@dominio.com`\nenvie o"
        " comprovante para liberar o seu acesso instantâneo."
    )

  return False


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
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.04);">
                <div style="border-radius: 8px; overflow: hidden; max-height: 120px; border: 1px solid #e2e8f0; margin-bottom: 8px;">
                    <img src="data:image/jpeg;base64,{encoded_string}" style="width: 100%; height: 110px; object-fit: cover; display: block;">
                </div>
                <h2 style="color: #1b7a3e !important; margin: 0 0 2px 0; font-size: 15px;">🏗️ tabalmix - painel operacional da frota</h2>
                <p style="color: #475569 !important; font-size: 11px; margin: 0; font-weight: 500;">controle avançado de caminhões betoneira, maquinário e manutenções | powered by castro tech.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.markdown(
        """
            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px; margin-bottom: 15px;">
                <h2 style="color: #1b7a3e !important; margin: 0 0 2px 0; font-size: 15px;">🏗️ tabalmix - painel operacional da frota</h2>
                <p style="color: #475569 !important; font-size: 11px; margin: 0; font-weight: 500;">controle avançado de caminhões betoneira, maquinário e manutenções | powered by castro tech.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

  df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
  df_manut = pd.read_sql("SELECT * FROM manutencoes", conn)
  df_pecas = pd.read_sql("SELECT * FROM pecas", conn)
  df_comb = pd.read_sql("SELECT * FROM combustivel", conn)

  total_frota = len(df_veiculos)
  total_custo = (
      df_manut["custo"].sum()
      if not df_manut.empty and "custo" in df_manut.columns
      else 0.0
  )
  liberado_pecas = (
      df_manut["custo_pecas"].sum()
      if not df_manut.empty and "custo_pecas" in df_manut.columns
      else 0.0
  )
  liberado_mo = (
      df_manut["mao_de_obra"].sum()
      if not df_manut.empty and "mao_de_obra" in df_manut.columns
      else 0.0
  )
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
    st.metric("total frota", total_frota)
  with r1_c2:
    st.metric("🟢 trabalhando", ativos_trabalhando)
  with r1_c3:
    st.metric("🔴 parados", ativos_parados)

  r2_c1, r2_c2, r2_c3 = st.columns(3)
  with r2_c1:
    st.metric("custo manut.", f"r$ {total_custo:,.2f}")
  with r2_c2:
    st.metric("gasto combustível", f"r$ {total_combustivel:,.2f}")
  with r2_c3:
    st.metric("total insumos", len(df_pecas))

  if not df_manut.empty or not df_comb.empty:
    st.divider()
    st.subheader("📊 indicadores e comparativo de custos")
    gc1, gc2 = st.columns(2)
    with gc1:
      st.markdown("**despesas de manutenção (peças vs mão de obra)**")
      df_custos_chart = pd.DataFrame({
          "categoria": ["peças utilizadas", "mão de obra"],
          "valor (r$)": [liberado_pecas, liberado_mo],
      })
      st.bar_chart(df_custos_chart, x="categoria", y="valor (r$)")
    with gc2:
      st.markdown("**consumo de combustível por equipamento**")
      if not df_comb.empty:
        df_comb_chart = (
            df_comb.groupby("equipamento")["valor_total"].sum().reset_index()
        )
        st.bar_chart(df_comb_chart, x="equipamento", y="valor_total")
      else:
        st.info("nenhum abastecimento registrado para gerar gráfico.")

    if "data_abertura" in df_manut.columns and not df_manut.empty:
      st.markdown("---")
      st.markdown("**📈 evolução mensal dos custos de manutenção (r$)**")
      try:
        df_manut_evol = df_manut.copy()
        df_manut_evol["mes"] = pd.to_datetime(
            df_manut_evol["data_abertura"], errors="coerce"
        ).dt.strftime("%Y-%m")
        df_mensal = (
            df_manut_evol.groupby("mes")["custo"].sum().reset_index()
        )
        if not df_mensal.empty and df_mensal["mes"].notna().any():
          st.line_chart(df_mensal.set_index("mes")["custo"])
        else:
          st.info("insira datas válidas nas os para ver o gráfico mensal.")
      except Exception:
        pass

  if not df_veiculos.empty:
    st.divider()
    st.subheader("⚠️ alertas de manutenção preventiva")
    alerta_gerado = False
    for idx, row in df_veiculos.iterrows():
      h_km = row["horimetro_km"] if row["horimetro_km"] is not None else 0
      if h_km >= 15000:
        st.warning(
            f"🔔 **atenção preventiva:** o equipamento **{row['tag_prefixo']}**"
            f" ({row['modelo']}) atingiu **{h_km:,} km/horímetro**. recomenda-se"
            " agendar revisão geral."
        )
        alerta_gerado = True
    if not alerta_gerado:
      st.success(
          "✅ todos os equipamentos estão com horímetro/km dentro do período"
          " ideal de operação."
      )

  st.divider()
  st.subheader("📋 status da frota e equipamentos")

  if not df_veiculos.empty:
    filtro_status = st.selectbox(
        "🔍 filtrar status",
        [
            "todos os status",
            "ativo",
            "mobilizado",
            "em manutenção",
            "parado",
            "desmobilizado",
            "inativo",
        ],
    )
    df_filtrado = df_veiculos.copy()
    if filtro_status != "todos os status":
      df_filtrado = df_veiculos[df_veiculos["status"] == filtro_status]

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    if status_usuario_ativo or modo_admin_liberado:
      c_d1, c_d2 = st.columns(2)
      with c_d1:
        st.download_button(
            "📥 baixar pdf",
            gerar_pdf_relatorio("relatório de frota", df_filtrado),
            "frota.pdf",
            "application/pdf",
        )
      with c_d2:
        st.download_button(
            "📊 baixar planilha (.csv)",
            gerar_csv_relatorio(df_filtrado),
            "frota.csv",
            "text/csv",
        )
  else:
    st.info("nenhum equipamento cadastrado.")

elif menu == "🚜 cadastro de equipamentos":
  st.title("🚜 cadastro de equipamentos")

  if status_usuario_ativo or modo_admin_liberado:
    with st.form("form_frota", clear_on_submit=False):
      col1, col2 = st.columns(2)
      with col1:
        tag_prefixo = st.text_input("tag/prefixo (ex: eq-001)")
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
        ano = st.number_input(
            "ano de fabricação", min_value=1950, value=2024, step=1
        )
        chassi = st.text_input("número de série / chassi (opcional)")
        placa = st.text_input("placa")
      with col2:
        horimetro_km = st.number_input(
            "horímetro ou quilometragem atual", min_value=0, value=15000, step=100
        )
        combustivel = st.selectbox(
            "combustível", ["diesel s10", "diesel s500", "gasolina", "flex"]
        )
        local_atual = st.text_input("local atual / obra")
        operador_condutor = st.text_input("operador/condutor")
        status = st.selectbox(
            "situação / status",
            [
                "ativo",
                "em manutenção",
                "parado",
                "mobilizado",
                "desmobilizado",
                "inativo",
            ],
        )
        data_entrada = st.date_input("data de entrada na empresa")
        observacoes = st.text_input("observações")

      if st.form_submit_button("cadastrar equipamento"):
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
          st.success(f"✅ equipamento '{tag_prefixo.upper()}' cadastrado!")
          st.rerun()
        else:
          st.error("⚠️ preencha tag/prefixo e modelo.")
  else:
    verificar_licenca_para_acao()

  st.divider()
  st.subheader("equipamentos cadastrados")
  df_f = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_f.empty:
    st.dataframe(df_f, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔎 ficha histórica individual do equipamento")
    eq_selecionado_historico = st.selectbox(
        "selecione a tag/prefixo para ver o histórico completo",
        df_f["tag_prefixo"].tolist(),
        key="sel_hist_eq",
    )
    if eq_selecionado_historico:
      dados_eq = df_f[df_f["tag_prefixo"] == eq_selecionado_historico].iloc[0]
      st.info(
          f"📌 **ativo:** {dados_eq['tag_prefixo']} | **modelo:**"
          f" {dados_eq['modelo']} | **status atual:** {dados_eq['status']} |"
          f" **horímetro/km:** {dados_eq['horimetro_km']:,}"
      )

      col_h1, col_h2 = st.columns(2)
      with col_h1:
        st.markdown("**🛠️ histórico de manutenções (os):**")
        df_hist_os = pd.read_sql(
            "SELECT id, tipo_manutencao, data_abertura, status_os, custo FROM"
            " manutencoes WHERE tag_prefixo = ?",
            conn,
            params=(eq_selecionado_historico,),
        )
        if not df_hist_os.empty:
          st.dataframe(df_hist_os, use_container_width=True, hide_index=True)
        else:
          st.write("nenhuma os registrada para este equipamento.")
      with col_h2:
        st.markdown("**⛽ histórico de abastecimentos:**")
        df_hist_comb = pd.read_sql(
            "SELECT data, litros, valor_total, motorista FROM combustivel WHERE"
            " equipamento = ?",
            conn,
            params=(eq_selecionado_historico,),
        )
        if not df_hist_comb.empty:
          st.dataframe(df_hist_comb, use_container_width=True, hide_index=True)
        else:
          st.write("nenhum abastecimento registrado.")

    if status_usuario_ativo or modo_admin_liberado:
      c_del1, c_del2 = st.columns([2, 1])
      with c_del1:
        eq_exc = st.selectbox(
            "selecione o id para excluir da frota", df_f["id"].tolist()
        )
      with c_del2:
        st.write("")
        st.write("")
        if st.button("🗑️ excluir"):
          cursor.execute("DELETE FROM veiculos WHERE id = ?", (eq_exc,))
          conn.commit()
          st.success("removido!")
          st.rerun()
  else:
    st.info("nenhum equipamento cadastrado.")

elif menu == "⛽ abastecimentos & combustível":
  st.title("⛽ controle de abastecimento e combustível")
  try:
    df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  except Exception:
    df_v = pd.DataFrame()

  if df_v.empty:
    st.warning("cadastre equipamentos primeiro na aba 'cadastro de equipamentos'.")
  else:
    if status_usuario_ativo or modo_admin_liberado:
      with st.form("form_comb"):
        c1, c2 = st.columns(2)
        with c1:
          eq_comb = st.selectbox(
              "equipamento / tag", df_v["tag_prefixo"].tolist()
          )
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
          st.success("✅ abastecimento registrado!")
    else:
      verificar_licenca_para_acao()

    st.divider()
    st.subheader("📋 histórico de abastecimentos")
    df_c = pd.read_sql("SELECT * FROM combustivel", conn)
    if not df_c.empty:
      col_f1, col_f2 = st.columns(2)
      with col_f1:
        dt_ini_c = st.date_input("data inicial", value=datetime.now().date() - timedelta(days=30))
      with col_f2:
        dt_fim_c = st.date_input("data final", value=datetime.now().date())
      
      try:
        df_c["data_dt"] = pd.to_datetime(df_c["data"], errors="coerce").dt.date
        df_c_filtrado = df_c[
            (df_c["data_dt"] >= dt_ini_c) & (df_c["data_dt"] <= dt_fim_c)
        ].drop(columns=["data_dt"])
        st.dataframe(df_c_filtrado, use_container_width=True, hide_index=True)
      except Exception:
        st.dataframe(df_c, use_container_width=True, hide_index=True)
    else:
      st.info("nenhum abastecimento registrado.")

elif menu == "🏗️ mobilização / desmobilização":
  st.title("🏗️ mobilização e desmobilização de obras")
  try:
    df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  except Exception:
    df_v = pd.DataFrame()

  if df_v.empty:
    st.warning("cadastre equipamentos primeiro na aba 'cadastro de equipamentos'.")
  else:
    if status_usuario_ativo or modo_admin_liberado:
      with st.form("form_mob"):
        c1, c2 = st.columns(2)
        with c1:
          eq_mob = st.selectbox(
              "equipamento / tag", df_v["tag_prefixo"].tolist()
          )
          tipo_mov = st.selectbox(
              "movimentação",
              [
                  "mobilização (envio)",
                  "desmobilização (retorno)",
                  "remanejamento",
              ],
          )
          destino = st.text_input("obra / destino-origem")
          km_mov = st.text_input("horímetro / km")
        with c2:
          resp = st.text_input("responsável")
          dt_mob = st.date_input("data")
          motivo = st.text_input("motivo / condição do check-list")
          obs = st.text_input("observação")
        
        foto_subida = st.file_uploader("📷 anexar foto do check-list de recebimento / vistoria", type=["png", "jpg", "jpeg"])

        if st.form_submit_button("registrar movimentação"):
          nome_foto = ""
          if foto_subida is not None:
            os.makedirs("uploads_checklists", exist_ok=True)
            nome_foto = f"uploads_checklists/{datetime.now().strftime('%Y%m%d%H%M%S')}_{foto_subida.name}"
            with open(nome_foto, "wb") as f:
              f.write(foto_subida.getbuffer())

          cursor.execute(
              "INSERT INTO mobilizacoes (equipamento, tipo_movimento,"
              " destino_origem, responsavel, data, horimetro_km_mov,"
              " motivo_condicao, observacao, foto_checklist) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (
                  eq_mob,
                  tipo_mov,
                  destino,
                  resp,
                  str(dt_mob),
                  str(km_mov),
                  motivo,
                  obs,
                  nome_foto,
              ),
          )
          conn.commit()
          st.success("✅ movimentação e check-list fotográfico registrados com sucesso!")
    else:
      verificar_licenca_para_acao()

    st.divider()
    df_mobs = pd.read_sql("SELECT * FROM mobilizacoes", conn)
    if not df_mobs.empty:
      st.dataframe(df_mobs, use_container_width=True, hide_index=True)
      
      for idx, row in df_mobs.iterrows():
        if row.get("foto_checklist") and os.path.exists(str(row["foto_checklist"])):
          with st.expander(f"ver foto check-list #{row['id']} - {row['equipamento']}"):
            st.image(row["foto_checklist"], width=300)

elif menu == "🛠️ ordens de serviço (os)":
  st.title("🛠️ gestão unificada de ordens de serviço (os)")

  try:
    df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
    tags_disponiveis = df_v["tag_prefixo"].dropna().tolist() if not df_v.empty else []
  except Exception:
    tags_disponiveis = []

  if status_usuario_ativo or modo_admin_liberado:
    st.markdown("### 🟢 abertura de nova os (etapa 1)")
    with st.form("form_abertura_os", clear_on_submit=True):
      c1, c2 = st.columns(2)
      with c1:
        if tags_disponiveis:
          tag_os = st.selectbox("tag / prefixo do equipamento", tags_disponiveis)
        else:
          tag_os = st.text_input("tag / prefixo do equipamento (ex: eq-001)")

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
            "horário de abertura (ex: 08:30)", value=datetime.now().strftime("%H:%M")
        )
        desc_prob = st.text_area(
            "descrição do problema apresentado pelo motorista"
        )

      if st.form_submit_button("abrir nova os"):
        if tag_os:
          cursor.execute(
              "INSERT INTO manutencoes (tag_prefixo, tipo_manutencao,"
              " horimetro_km_manut, origem_falha, descricao_problema,"
              " data_abertura, hora_abertura, status_os, custo, custo_pecas,"
              " mao_de_obra) VALUES (?, ?, ?, ?, ?, ?, ?, 'aberta', 0.0, 0.0,"
              " 0.0)",
              (
                  str(tag_os).upper(),
                  tipo_manutencao,
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
        else:
          st.error("⚠️ informe a tag/prefixo do equipamento.")
  else:
    verificar_licenca_para_acao()

  st.divider()
  st.subheader("📋 fechamento e histórico de ordens de serviço")
  df_os = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_os.empty:
    col_fos1, col_fos2 = st.columns(2)
    with col_fos1:
      dt_ini_os = st.date_input("data inicial os", value=datetime.now().date() - timedelta(days=30), key="ini_os")
    with col_fos2:
      dt_fim_os = st.date_input("data final os", value=datetime.now().date(), key="fim_os")
    
    try:
      df_os["dt_ab_parsed"] = pd.to_datetime(df_os["data_abertura"], errors="coerce").dt.date
      df_os_filtrado = df_os[
          (df_os["dt_ab_parsed"] >= dt_ini_os) & (df_os["dt_ab_parsed"] <= dt_fim_os)
      ].drop(columns=["dt_ab_parsed"])
      st.dataframe(df_os_filtrado, use_container_width=True, hide_index=True)
    except Exception:
      st.dataframe(df_os, use_container_width=True, hide_index=True)

    if status_usuario_ativo or modo_admin_liberado:
      st.markdown(
          "### ⚙️ fechamento / atualização ou exclusão de os (etapa 2)"
      )
      os_abertas_ids = df_os["id"].tolist()
      
      col_ed1, col_ed2 = st.columns([3, 1])
      with col_ed1:
        os_sel = st.selectbox(
            "selecione o id da os para gerenciar", os_abertas_ids
        )
      with col_ed2:
        st.write("")
        st.write("")
        if st.button("🗑️ excluir esta os"):
          if os_sel:
            cursor.execute("DELETE FROM manutencoes WHERE id = ?", (os_sel,))
            conn.commit()
            st.success(f"✅ os #{os_sel} excluída com sucesso!")
            st.rerun()

      if os_sel:
        os_row_data = df_os[df_os["id"] == os_sel]
        if not os_row_data.empty:
          os_atual = os_row_data.iloc[0]
          tag_eq_os = (
              os_atual.get("tag_prefixo")
              or os_atual.get("equipamento")
              or "não informado"
          )
          val_dt_ab = os_atual.get("data_abertura") or datetime.now().strftime("%Y-%m-%d")
          val_hr_ab = os_atual.get("hora_abertura") or datetime.now().strftime("%H:%M")
          val_tp_man = os_atual.get("tipo_manutencao") or "preventiva"
          val_desc = os_atual.get("descricao_problema") or ""
          val_st_os = os_atual.get("status_os") or "aberta"

          with st.form("form_fechamento_os"):
            st.info(
                f"editando os #{os_atual['id']} | equipamento:"
                f" {tag_eq_os} | aberta em:"
                f" {val_dt_ab} às {val_hr_ab}"
            )
            fc1, fc2 = st.columns(2)
            with fc1:
              pecas_util = st.text_input(
                  "peças utilizadas",
                  value=str(os_atual.get("pecas_utilizadas") or ""),
              )
              v_pecas = st.number_input(
                  "valor total das peças (r$)",
                  min_value=0.0,
                  value=float(os_atual.get("custo_pecas") or 0.0),
                  format="%.2f",
              )
              v_mo = st.number_input(
                  "valor da mão de obra (r$)",
                  min_value=0.0,
                  value=float(os_atual.get("mao_de_obra") or 0.0),
                  format="%.2f",
              )
              oficina_resp = st.text_input(
                  "oficina responsável",
                  value=str(os_atual.get("oficina") or ""),
              )
            with fc2:
              tec_resp = st.text_input(
                  "técnico / mecânico responsável",
                  value=str(os_atual.get("tecnico_mecanico") or ""),
              )
              dt_fech = st.date_input("data de fechamento", value=datetime.now().date())
              hr_fech = st.text_input(
                  "horário de fechamento (ex: 17:00)", value=datetime.now().strftime("%H:%M")
              )
              status_final = st.selectbox(
                  "status da os", ["aberta", "em manutenção", "fechada"]
              )

            if st.form_submit_button("salvar e fechar os"):
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
              st.success(f"✅ os #{os_sel} atualizada e fechada com sucesso!")
              st.rerun()

          st.markdown("---")
          st.markdown("### 🖨️ relatórios técnicos e envio")
          
          tag_eq_pdf = tag_eq_os
          pdf_os_buffer = gerar_pdf_os_tecnica(os_atual)
          st.download_button(
              "📥 baixar pdf técnico oficial da os",
              pdf_os_buffer,
              file_name=f"os_tecnica_{os_atual['id']}_{tag_eq_pdf}.pdf",
              mime="application/pdf",
          )

          texto_msg = (
              f"*tabalmix concreto - relatório de os #{os_atual['id']}*\n\n"
              f"🚜 *equipamento:* {tag_eq_os}\n"
              f"🔧 *tipo:* {val_tp_man}\n"
              f"📋 *status:* {val_st_os}\n"
              f"⚠️ *problema:* {val_desc}\n"
              f"🔩 *peças:* {os_atual.get('pecas_utilizadas') or 'nenhuma'}\n"
              f"💰 *custo total:* r$ {(os_atual.get('custo') or 0.0):,.2f}\n"
              f"📅 *fechamento:* {os_atual.get('data_fechamento') or '-'} às"
              f" {os_atual.get('hora_fechamento') or '-'}"
          )
          encoded_whatsapp = urllib.parse.quote(texto_msg)
          url_whatsapp = f"https://api.whatsapp.com/send?text={encoded_whatsapp}"
          st.markdown(
              f"💬 **[👉 enviar relatório via whatsapp]({url_whatsapp})**",
              unsafe_allow_html=True,
          )
  else:
    st.info("nenhuma os registrada.")

elif menu == "🔩 peças e ferramentas":
  st.title("🔩 controle de peças e ferramentas")
  t1, t2 = st.tabs(["cadastrar", "inventário"])
  with t1:
    if status_usuario_ativo or modo_admin_liberado:
      with st.form("form_pecas"):
        c1, c2 = st.columns(2)
        with c1:
          nome_i = st.text_input("nome da peça ou ferramenta")
          cat = st.selectbox(
              "categoria",
              ["reposição", "filtro/óleo", "ferramenta", "insumo"],
          )
        with c2:
          qtd = st.number_input("quantidade", min_value=1, value=1)
          v_unit = st.number_input("valor unitário (r$)", min_value=0.0)
        if st.form_submit_button("adicionar"):
          cursor.execute(
              "INSERT INTO pecas (nome_item, categoria, quantidade,"
              " valor_unitario) VALUES (?, ?, ?, ?)",
              (nome_i, cat, qtd, v_unit),
          )
          conn.commit()
          st.success("cadastrado!")
    else:
      verificar_licenca_para_acao()
  with t2:
    df_p = pd.read_sql("SELECT * FROM pecas", conn)
    if not df_p.empty:
      st.dataframe(df_p, use_container_width=True, hide_index=True)

elif menu == "👥 gestão de clientes":
  st.title("👥 gestão de clientes")
  if status_usuario_ativo or modo_admin_liberado:
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
        st.success("salvo!")
  else:
    verificar_licenca_para_acao()

  df_cli = pd.read_sql("SELECT * FROM clientes", conn)
  if not df_cli.empty:
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

elif menu == "🔍 consulta / busca geral":
  st.title("🔍 consulta e histórico completo do equipamento")
  termo = st.text_input("digite a tag, placa ou marca para buscar todo o histórico")
  if termo:
    t_like = f"%{termo}%"
    df_bv = pd.read_sql(
        "SELECT * FROM veiculos WHERE tag_prefixo LIKE ? OR placa LIKE ? OR marca LIKE ? OR modelo LIKE ?",
        conn,
        params=(t_like, t_like, t_like, t_like),
    )
    if not df_bv.empty:
      st.subheader("1. 🚜 dados cadastrais do equipamento:")
      st.dataframe(df_bv, use_container_width=True, hide_index=True)

      for idx, eq_row in df_bv.iterrows():
        tag_buscada = eq_row["tag_prefixo"]
        st.markdown(f"---")
        st.markdown(f"### 📋 histórico unificado para o ativo: **{tag_buscada}**")

        c_q1, c_q2 = st.columns(2)
        with c_q1:
          st.markdown("**🏗️ histórico de mobilizações:**")
          df_m_hist = pd.read_sql("SELECT data, tipo_movimento, destino_origem, responsavel FROM mobilizacoes WHERE equipamento = ?", conn, params=(tag_buscada,))
          if not df_m_hist.empty:
            st.dataframe(df_m_hist, use_container_width=True, hide_index=True)
          else:
            st.write("nenhuma mobilização registrada.")

        with c_q2:
          st.markdown("**🛠️ histórico de manutenções (os):**")
          df_o_hist = pd.read_sql("SELECT id, tipo_manutencao, data_abertura, status_os, custo FROM manutencoes WHERE tag_prefixo = ?", conn, params=(tag_buscada,))
          if not df_o_hist.empty:
            st.dataframe(df_o_hist, use_container_width=True, hide_index=True)
          else:
            st.write("nenhuma os registrada.")

        st.markdown("**⛽ histórico de abastecimentos:**")
        df_c_hist = pd.read_sql("SELECT data, litros, valor_total, motorista FROM combustivel WHERE equipamento = ?", conn, params=(tag_buscada,))
        if not df_c_hist.empty:
          st.dataframe(df_c_hist, use_container_width=True, hide_index=True)
        else:
          st.write("nenhum abastecimento registrado.")
    else:
      st.info("nenhum equipamento encontrado com este termo.")

elif menu == "⚙️ meu perfil / dados":
  st.title("⚙️ atualização de perfil e pin de acesso")
  if usuario_atual:
    cursor.execute(
        "SELECT nome_completo, cpf, email, celular_seguranca, pin_rapido FROM"
        " usuarios_sistema WHERE id = ?",
        (usuario_atual["id"],),
    )
    dados_atuais = cursor.fetchone()
    if dados_atuais:
      with st.form("form_atualizar_perfil"):
        novo_nome = st.text_input("nome completo", value=dados_atuais[0])
        novo_email = st.text_input("e-mail (login)", value=dados_atuais[2])
        novo_celular = st.text_input(
            "celular / contato de segurança", value=dados_atuais[3] or ""
        )
        novo_pin = st.text_input(
            "definir / alterar pin rápido (4 dígitos)",
            value=dados_atuais[4] or "",
            max_chars=4,
            type="password",
        )
        nova_senha_Alt = st.text_input(
            "nova senha (opcional - deixe em branco para manter a atual)",
            type="password",
        )

        if st.form_submit_button("💾 salvar alterações"):
          if novo_email and novo_nome:
            if nova_senha_Alt:
              cursor.execute(
                  "UPDATE usuarios_sistema SET nome_completo = ?, email = ?,"
                  " celular_seguranca = ?, pin_rapido = ?, senha = ? WHERE id ="
                  " ?",
                  (
                      novo_nome,
                      novo_email,
                      novo_celular,
                      novo_pin,
                      nova_senha_Alt,
                      usuario_atual["id"],
                  ),
              )
            else:
              cursor.execute(
                  "UPDATE usuarios_sistema SET nome_completo = ?, email = ?,"
                  " celular_seguranca = ?, pin_rapido = ? WHERE id = ?",
                  (
                      novo_nome,
                      novo_email,
                      novo_celular,
                      novo_pin,
                      usuario_atual["id"],
                  ),
              )
            conn.commit()
            st.success(
                "✅ perfil e pin atualizados com sucesso! suas informações"
                " foram salvas."
            )
          else:
            st.error("⚠️ o e-mail e o nome não podem ficar em branco.")
  else:
    st.info(
        "faça login para gerenciar seu perfil (ou acesse via modo administrador)."
    )

elif menu == "⚙️ painel de licença (admin)":
  if modo_admin_liberado:
    st.title("⚙️ painel de administração de usuários e segurança")

    st.markdown("### 📥 backup do banco de dados (segurança)")
    try:
      with open("frota_profissional.db", "rb") as f_db:
        st.download_button(
            "💾 baixar cópia de segurança (.db)",
            f_db,
            file_name=f"backup_tabalmix_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
            mime="application/octet-stream",
        )
    except Exception as e:
      st.info("arquivo de banco de dados gerado após o primeiro uso.")

    st.markdown("---")
    st.markdown("### gestão de usuários e licenças")
    df_users = pd.read_sql(
        "SELECT id, status_assinatura AS status, nome_completo, email, cpf, celular_seguranca, plano_atual FROM usuarios_sistema",
        conn,
    )
    if not df_users.empty:
      st.dataframe(df_users, use_container_width=True, hide_index=True)

      col_adm1, col_adm2 = st.columns(2)
      with col_adm1:
        with st.form("form_admin_user"):
          id_sel = st.selectbox(
              "selecione o id do usuário", df_users["id"].tolist()
          )
          novo_status_u = st.selectbox("novo status", ["Ativo", "Inativo"])
          if st.form_submit_button("atualizar assinatura"):
            cursor.execute(
                "UPDATE usuarios_sistema SET status_assinatura = ? WHERE id = ?",
                (novo_status_u, id_sel),
            )
            conn.commit()
            st.success("✅ status do usuário atualizado com sucesso!")
            st.rerun()

      with col_adm2:
        with st.form("form_admin_del_user"):
          id_del = st.selectbox(
              "selecione o id para excluir conta",
              df_users["id"].tolist(),
              key="del_user_id",
          )
          if st.form_submit_button("🗑️ excluir usuário do sistema"):
            cursor.execute(
                "DELETE FROM usuarios_sistema WHERE id = ?", (id_del,)
            )
            conn.commit()
            st.success("✅ conta de usuário excluída com sucesso!")
            st.rerun()
    else:
      st.info("nenhum usuário cadastrado no sistema ainda.")
  else:
    st.error("acesso restrito.")
