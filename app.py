from datetime import datetime, timedelta
import base64
import csv
import glob
import io
import os
import sqlite3
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
    page_title="Tabalmix Concreto - Gestão de Frota e Oficina Pro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização Visual Corporativa Avançada + Correção Mobile
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    button[kind="header"], [data-testid="collapsedControl"] svg {
        color: #2ecc71 !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 100% !important;
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
    [data-testid="stSidebar"] .stRadio label {
        color: #e2e8f0 !important;
        font-weight: 600;
        font-size: 14px;
        padding: 10px 12px;
        border-radius: 8px;
        background: rgba(20, 60, 30, 0.7);
        margin-bottom: 5px;
        border: 1px solid rgba(46, 204, 113, 0.2);
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(46, 204, 113, 0.25);
        border-color: #2ecc71;
        color: #2ecc71 !important;
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
    div.stTextInput > div > div > input, 
    div.stNumberInput > div > div > input, 
    div.stSelectbox > div > div > div {
        background-color: rgba(15, 23, 42, 0.9) !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        min-height: 44px !important;
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


def gerar_pdf_relatorio(titulo, dataframe):
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=letter)
  largura, altura = letter
  margem_esq = 30
  largura_util = largura - 60

  c.setFillColorRGB(0.08, 0.32, 0.16)
  c.rect(0, altura - 65, largura, 65, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 15)
  c.drawString(margem_esq, altura - 28, "TABALMIX CONCRETO")
  c.setFont("Helvetica", 10)
  c.drawString(
      margem_esq,
      altura - 48,
      "Sistema de Gestão de Frota e Operações | Powered by Castro Tech",
  )

  c.setFillColorRGB(0.15, 0.15, 0.15)
  c.setFont("Helvetica-Bold", 14)
  c.drawString(margem_esq, altura - 95, titulo)
  c.setFont("Helvetica", 9)
  c.setFillColorRGB(0.4, 0.4, 0.4)
  c.drawString(
      margem_esq,
      altura - 112,
      f"Emitido em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
  )

  c.setStrokeColorRGB(0.8, 0.8, 0.8)
  c.setLineWidth(0.75)
  c.line(margem_esq, altura - 122, largura - margem_esq, altura - 122)

  y = altura - 155
  altura_linha = 22
  colunas = list(dataframe.columns)
  colunas_amigables = [
      str(col).replace("_", " ").upper() for col in colunas[:6]
  ]

  c.setFillColorRGB(0.08, 0.25, 0.13)
  c.rect(margem_esq, y - 4, largura_util, altura_linha, fill=1, stroke=0)
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 8.5)
  largura_coluna = largura_util / max(len(colunas_amigables), 1)

  for i, col_nome in enumerate(colunas_amigables):
    c.drawString(margem_esq + (i * largura_coluna) + 5, y + 3, col_nome[:14])

  y -= altura_linha + 2
  c.setFont("Helvetica", 8.5)

  for index, row in dataframe.iterrows():
    if y < 60:
      c.showPage()
      y = altura - 50
    if index % 2 == 0:
      c.setFillColorRGB(0.92, 0.97, 0.94)
      c.rect(margem_esq, y - 3, largura_util, altura_linha - 2, fill=1, stroke=0)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    for i, col in enumerate(colunas[:6]):
      valor_celula = str(row[col])
      if valor_celula == "None" or valor_celula == "nan":
        valor_celula = "-"
      c.drawString(
          margem_esq + (i * largura_coluna) + 5, y + 3, valor_celula[:16]
      )
    c.setStrokeColorRGB(0.8, 0.88, 0.83)
    c.line(margem_esq, y - 4, largura - margem_esq, y - 4)
    y -= altura_linha

  c.setStrokeColorRGB(0.7, 0.7, 0.7)
  c.line(margem_esq, 45, largura - margem_esq, 45)
  c.setFillColorRGB(0.5, 0.5, 0.5)
  c.setFont("Helvetica", 8)
  c.drawString(
      margem_esq,
      30,
      "TABALMIX CONCRETO — Todos os direitos reservados. Tecnologia Castro"
      " Tech.",
  )
  c.drawRightString(
      largura - margem_esq,
      30,
      f"Página 1 de 1 | Emitido em {datetime.now().strftime('%d/%m/%Y')}",
  )

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
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT,
            email TEXT UNIQUE,
            senha TEXT,
            cargo TEXT,
            pin_rapido TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_colunas (
            tabela TEXT PRIMARY KEY,
            colunas_permitidas TEXT
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

  # Inserir usuário Alex se não existir
  cursor.execute(
      "SELECT COUNT(*) FROM usuarios_sistema WHERE email = ?",
      ("alexcastro02522@gmail.com",),
  )
  if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO usuarios_sistema (nome_completo, email, senha, cargo,"
        " pin_rapido) VALUES (?, ?, ?, ?, ?)",
        (
            "Alex de Castro Bernardino",
            "alexcastro02522@gmail.com",
            "Alex275612@",
            "Diretoria / Gestão / Engenharia",
            "2756",
        ),
    )
    conn.commit()

  cursor.execute("SELECT COUNT(*) FROM licenca")
  if cursor.fetchone()[0] == 0:
    vencimento_padrao = (datetime.now() + timedelta(days=30)).strftime(
        "%Y-%m-%d"
    )
    cursor.execute(
        "INSERT INTO licenca (status_assinatura, plano_atual, data_vencimento,"
        " chave_pix) VALUES (?, ?, ?, ?)",
        ("Ativo", "Mensal (R$ 250,00)", vencimento_padrao, "alex@tabalmix.com"),
    )
    conn.commit()
  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

# Sessão do Usuário
if "usuario_logado" not in st.session_state:
  st.session_state["usuario_logado"] = None

# Menu Lateral & Identidade Visual com Selo Oficial
with st.sidebar:
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_logo = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="text-align: center; padding: 10px 0 15px 0;">
                <div style="border-radius: 12px; overflow: hidden; max-height: 110px; border: 2px solid #2ecc71; margin-bottom: 10px; box-shadow: 0 4px 15px rgba(46, 204, 113, 0.3);">
                    <img src="data:image/jpeg;base64,{encoded_logo}" style="width: 100%; height: 95px; object-fit: cover; display: block;">
                </div>
                <div style="display: inline-block; background: rgba(46, 204, 113, 0.15); border: 1px solid #2ecc71; border-radius: 20px; padding: 3px 12px; margin-bottom: 6px;">
                    <span style="color: #2ecc71; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">🛡️ SELO OFICIAL DE GARANTIA</span>
                </div>
                <h3 style="color: #2ecc71; margin: 0; font-size: 18px; font-weight: 800;">TABALMIX CONCRETO</h3>
                <p style="color: #94a3b8; font-size: 10px; margin: 2px 0 6px 0; text-transform: uppercase; letter-spacing: 1px;">Gestão de Frota & Operações</p>
                <p style="color: #e2e8f0; font-size: 11px; font-style: italic; font-weight: 500; line-height: 1.3; margin-bottom: 15px;">
                    "Tecnologia e robustez na concretagem por Castro Tech."
                </p>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.markdown(
        """
            <div style="text-align: center; padding: 10px 0 15px 0;">
                <div style="font-size: 40px; margin-bottom: 2px;">🟢 🛡️</div>
                <div style="display: inline-block; background: rgba(46, 204, 113, 0.15); border: 1px solid #2ecc71; border-radius: 20px; padding: 3px 12px; margin-bottom: 6px;">
                    <span style="color: #2ecc71; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">🛡️ SELO OFICIAL DE GARANTIA</span>
                </div>
                <h3 style="color: #2ecc71; margin: 0; font-size: 18px; font-weight: 800;">TABALMIX CONCRETO</h3>
                <p style="color: #94a3b8; font-size: 10px; margin: 2px 0 6px 0; text-transform: uppercase; letter-spacing: 1px;">Gestão de Frota & Operações</p>
                <p style="color: #e2e8f0; font-size: 11px; font-style: italic; font-weight: 500; line-height: 1.3; margin-bottom: 15px;">
                    "Tecnologia e robustez na concretagem por Castro Tech."
                </p>
            </div>
        """,
        unsafe_allow_html=True,
    )

  if st.session_state["usuario_logado"]:
    user_ativo = st.session_state["usuario_logado"]
    st.success(f"👤 **Logado:** {user_ativo['nome_completo']}")
    st.info(f"🔑 **Cargo:** {user_ativo['cargo']}")
    if st.button("🚪 Encerrar Sessão"):
      st.session_state["usuario_logado"] = None
      st.rerun()
  else:
    st.warning("🔒 Faça login para acesso completo.")

  st.markdown("---")

  lista_menus = [
      "📊 Visão Geral",
      "🚚 Frota e Maquinários",
      "⛽ Abastecimentos & Combustível",
      "🏗️ Mobilização / Desmobilização",
      "🛠️ Ordens de Serviço (OS)",
      "🔩 Peças e Ferramentas",
      "👥 Gestão de Clientes",
      "🔍 Consulta / Busca Geral",
      "🔑 Login / Autenticação",
      "⚙️ Painel de Licença (Admin)",
  ]

  menu = st.sidebar.radio("Navegação do Sistema", lista_menus, label_visibility="collapsed")

# Verificação de privilégios de Gestão / Engenharia
def verificar_permissao_gestor():
  if st.session_state["usuario_logado"] is not None:
    cargo = st.session_state["usuario_logado"].get("cargo", "")
    if any(
        termo in cargo
        for termo in ["Diretoria", "Gestão", "Engenharia", "Chefe"]
    ):
      return True
  return False


if menu == "📊 Visão Geral":
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="background: linear-gradient(135deg, rgba(15, 30, 20, 0.95) 0%, rgba(5, 15, 10, 0.95) 100%); border: 2px solid #2ecc71; border-radius: 16px; padding: 18px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <div style="border-radius: 12px; overflow: hidden; max-height: 320px; border: 1px solid rgba(46, 204, 113, 0.4); margin-bottom: 15px;">
                    <img src="data:image/jpeg;base64,{encoded_string}" style="width: 100%; height: 280px; object-fit: cover; display: block;">
                </div>
                <h2 style="color: #2ecc71 !important; margin: 0 0 6px 0; font-size: 22px;">🏗️ Tabalmix - Painel Operacional da Frota</h2>
                <p style="color: #cbd5e1 !important; font-size: 14px; margin: 0; font-weight: 500;">Sistema corporativo avançado para controle de caminhões betoneira, maquinário pesado, obras e manutenções | Powered by Castro Tech.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.markdown(
        """
            <div style="background: linear-gradient(135deg, rgba(15, 30, 20, 0.95) 0%, rgba(5, 15, 10, 0.95) 100%); border: 2px solid #2ecc71; border-radius: 16px; padding: 25px; margin-bottom: 25px;">
                <h2 style="color: #2ecc71 !important; margin: 0 0 6px 0; font-size: 22px;">🏗️ Tabalmix - Painel Operacional da Frota</h2>
                <p style="color: #cbd5e1 !important; font-size: 14px; margin: 0; font-weight: 500;">Sistema corporativo avançado para controle de caminhões betoneira, maquinário pesado, obras e manutenções | Powered by Castro Tech.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

  df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
  df_manut = pd.read_sql("SELECT * FROM manutencoes", conn)
  df_pecas = pd.read_sql("SELECT * FROM pecas", conn)
  df_comb = pd.read_sql("SELECT * FROM combustivel", conn)

  total_frota = len(df_veiculos)
  total_custo = df_manut["custo"].sum() if not df_manut.empty else 0.0
  total_combustivel = (
      df_comb["valor_total"].sum() if not df_comb.empty else 0.0
  )

  ativos_trabalhando = 0
  ativos_parados = 0
  if not df_veiculos.empty and "status" in df_veiculos.columns:
    ativos_trabalhando = len(
        df_veiculos[df_veiculos["status"].isin(["Ativo", "Mobilizado", "Operando"])]
    )
    ativos_parados = total_frota - ativos_trabalhando

  col1, col2, col3, col4, col5 = st.columns(5)
  col1.metric("Total Frota", total_frota)
  col2.metric("🟢 Trabalhando", ativos_trabalhando)
  col3.metric("🔴 Parados / Manut.", ativos_parados)
  col4.metric("Custo Manutenções", f"R$ {total_custo:,.2f}")
  col5.metric("Gasto Combustível", f"R$ {total_combustivel:,.2f}")

  st.divider()
  st.subheader("📋 Status Operacional da Frota e Maquinários")

  if not df_veiculos.empty:
    filtro_status = st.selectbox(
        "🔍 Filtrar Equipamentos por Status",
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

    st.dataframe(df_filtrado, use_container_width=True)

    col_down1, col_down2 = st.columns(2)
    with col_down1:
      pdf_buffer = gerar_pdf_relatorio(
          f"RELATÓRIO DE FROTA ({filtro_status}) - TABALMIX", df_filtrado
      )
      st.download_button(
          label="📥 Baixar Relatório Filtrado em PDF",
          data=pdf_buffer,
          file_name="relatorio_frota_tabalmix.pdf",
          mime="application/pdf",
      )
    with col_down2:
      csv_buffer = gerar_csv_relatorio(df_filtrado)
      st.download_button(
          label="📊 Baixar Relatório Filtrado em Planilha (.csv)",
          data=csv_buffer,
          file_name="relatorio_frota_tabalmix.csv",
          mime="text/csv",
      )
  else:
    st.info("Nenhum equipamento cadastrado.")

elif menu == "🚚 Frota e Maquinários":
  st.title("🚚 Cadastro Completo de Veículos e Maquinário Pesado")

  # Abas com restrições exclusivas para chefes, gestores e engenheiros
  eh_gestor = verificar_permissao_gestor()

  tabs_lista = ["📋 Frota Cadastrada"]
  if eh_gestor:
    tabs_lista.extend([
        "➕ Registar Novo Ativo",
        "✏️ Editar Ativo",
        "🗑️ Excluir Ativo",
        "⚙️ Gerir Colunas",
    ])

  abas_criadas = st.tabs(tabs_lista)

  with abas_criadas[0]:
    st.subheader("Frota Registrada no Sistema")
    df_f = pd.read_sql("SELECT * FROM veiculos", conn)
    if not df_f.empty:
      # Aplicar filtro de colunas personalizadas se houver
      try:
        cursor.execute(
            "SELECT colunas_permitidas FROM config_colunas WHERE tabela = ?",
            ("veiculos",),
        )
        res_conf = cursor.fetchone()
        if res_conf and res_conf[0]:
          cols_permitidas = [
              c.strip() for c in res_conf[0].split(",") if c.strip()
          ]
          cols_validas = [c for c in cols_permitidas if c in df_f.columns]
          if cols_validas:
            df_f = df_f[cols_validas]
      except Exception:
        pass

      st.dataframe(df_f, use_container_width=True)
      col_down1, col_down2 = st.columns(2)
      with col_down1:
        pdf_buffer = gerar_pdf_relatorio(
            "RELATÓRIO DE FROTA PRO - TABALMIX", df_f
        )
        st.download_button(
            label="📥 Baixar Relatório em PDF",
            data=pdf_buffer,
            file_name="relatorio_frota_tabalmix.pdf",
            mime="application/pdf",
        )
      with col_down2:
        csv_buffer = gerar_csv_relatorio(df_f)
        st.download_button(
            label="📊 Baixar Relatório em Planilha (.csv)",
            data=csv_buffer,
            file_name="relatorio_frota_tabalmix.csv",
            mime="text/csv",
        )
    else:
      st.info("Nenhum equipamento cadastrado na frota.")

  if eh_gestor:
    with abas_criadas[1]:
      st.subheader("➕ Registar Novo Ativo na Frota")
      with st.form("form_frota", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
          codigo_patrimonio = st.text_input(
              "Código Interno / Patrimônio (Ex: EQ-001)"
          )
          tipo = st.selectbox(
              "Tipo de Equipamento",
              [
                  "Caminhão Betoneira",
                  "Caminhão Basculante",
                  "Escavadeira / Maquinário Pesado",
                  "Carro / Utilitário",
                  "Trator / Agrícola",
              ],
          )
          marca = st.text_input("Marca (Ex: Volvo, Mercedes, Caterpillar)")
          modelo = st.text_input("Modelo")
          ano = st.number_input(
              "Ano de Fabricação", min_value=1950, value=2024, step=1
          )
          chassi = st.text_input("Número de Série / Chassi (Opcional)")
          placa = st.text_input("Placa (Quando houver)")
        with col2:
          horimetro_km = st.number_input(
              "Horímetro ou Quilometragem Atual",
              min_value=0,
              value=15000,
              step=100,
          )
          combustivel = st.selectbox(
              "Combustível", ["Diesel S10", "Diesel S500", "Gasolina", "Flex"]
          )
          local_atual = st.text_input("Local Atual / Obra")
          responsavel = st.text_input("Responsável pelo Ativo")
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
          observacoes = st.text_input("Observações / Documentação")

        salvar_ativo = st.form_submit_button("Cadastrar Ativo na Frota Pro")
        if salvar_ativo:
          if modelo and codigo_patrimonio:
            cursor.execute(
                "INSERT INTO veiculos (codigo_patrimonio, tipo, marca, modelo,"
                " ano, chassi, placa, horimetro_km, combustivel, local_atual,"
                " responsavel, status, data_entrada, observacoes) VALUES (?, ?,"
                " ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    codigo_patrimonio.upper(),
                    tipo,
                    marca,
                    modelo,
                    ano,
                    chassi,
                    placa.upper(),
                    int(horimetro_km),
                    combustivel,
                    local_atual,
                    responsavel,
                    status,
                    str(data_entrada),
                    observacoes,
                ),
            )
            conn.commit()
            st.success(
                f"✅ Ativo '{codigo_patrimonio.upper()} - {modelo}' cadastrado"
                " com sucesso!"
            )
            st.rerun()
          else:
            st.error("⚠️ Preencha o Código de Patrimônio e o Modelo.")

    with abas_criadas[2]:
      st.subheader("✏️ Editar Ativo Existente")
      df_edit = pd.read_sql("SELECT id, codigo_patrimonio, modelo FROM veiculos", conn)
      if not df_edit.empty:
        id_sel = st.selectbox(
            "Selecione o Ativo para Editar",
            df_edit["id"].tolist(),
            format_func=lambda x: f"ID #{x} — {df_edit[df_edit['id'] == x]['codigo_patrimonio'].values[0]} ({df_edit[df_edit['id'] == x]['modelo'].values[0]})",
        )
        ativo_reg = pd.read_sql(
            "SELECT * FROM veiculos WHERE id = ?", conn, params=(id_sel,)
        ).iloc[0]

        with st.form("form_edicao_ativo"):
          e_pat = st.text_input(
              "Código de Patrimônio",
              value=str(ativo_reg["codigo_patrimonio"]),
          )
          e_mod = st.text_input("Modelo", value=str(ativo_reg["modelo"]))
          e_loc = st.text_input(
              "Local Atual / Obra", value=str(ativo_reg["local_atual"])
          )
          e_km = st.number_input(
              "Horímetro / KM", value=int(ativo_reg["horimetro_km"]), step=100
          )
          e_status = st.selectbox(
              "Status",
              [
                  "Ativo",
                  "Em manutenção",
                  "Parado",
                  "Mobilizado",
                  "Desmobilizado",
              ],
              index=0,
          )

          salvar_edicao = st.form_submit_button("Salvar Alterações")
          if salvar_edicao:
            cursor.execute(
                "UPDATE veiculos SET codigo_patrimonio = ?, modelo = ?,"
                " local_atual = ?, horimetro_km = ?, status = ? WHERE id = ?",
                (e_pat, e_mod, e_loc, int(e_km), e_status, id_sel),
            )
            conn.commit()
            st.success("✅ Ativo atualizado com sucesso!")
            st.rerun()
      else:
        st.info("Nenhum ativo para editar.")

    with abas_criadas[3]:
      st.subheader("🗑️ Excluir Ativo da Frota")
      df_exc = pd.read_sql("SELECT id, codigo_patrimonio, modelo FROM veiculos", conn)
      if not df_exc.empty:
        id_exc = st.selectbox(
            "Selecione o Ativo para Excluir",
            df_exc["id"].tolist(),
            format_func=lambda x: f"ID #{x} — {df_exc[df_exc['id'] == x]['codigo_patrimonio'].values[0]} ({df_exc[df_exc['id'] == x]['modelo'].values[0]})",
            key="sel_exc_ativo",
        )
        if st.button("🗑️ Confirmar Exclusão do Ativo"):
          cursor.execute("DELETE FROM veiculos WHERE id = ?", (id_exc,))
          conn.commit()
          st.success("✅ Ativo excluído com sucesso!")
          st.rerun()
      else:
        st.info("Nenhum ativo para excluir.")

    with abas_criadas[4]:
      st.subheader("⚙️ Gerir Colunas Visíveis na Tabela")
      st.markdown(
          "Selecione quais colunas devem aparecer na tabela de frota para"
          " toda a equipe."
      )
      try:
        df_cols_ex = pd.read_sql("SELECT * FROM veiculos LIMIT 1", conn)
        todas_cols = list(df_cols_ex.columns)
      except Exception:
        todas_cols = []

      cursor.execute(
          "SELECT colunas_permitidas FROM config_colunas WHERE tabela = ?",
          ("veiculos",),
      )
      res_col = cursor.fetchone()
      cols_atuais = (
          [c.strip() for c in res_col[0].split(",")]
          if res_col and res_col[0]
          else todas_cols
      )

      cols_selecionadas = st.multiselect(
          "Colunas Ativas:", todas_cols, default=cols_atuais
      )
      if st.button("Salvar Configuração de Colunas"):
        str_cols = ",".join(cols_selecionadas)
        cursor.execute(
            "INSERT OR REPLACE INTO config_colunas (tabela, colunas_permitidas)"
            " VALUES (?, ?)",
            ("veiculos", str_cols),
        )
        conn.commit()
        st.success("✅ Configuração de colunas salva com sucesso!")
        st.rerun()

elif menu == "⛽ Abastecimentos & Combustível":
  st.title("⛽ Controle de Abastecimento e Consumo de Combustível")
  df_v = pd.read_sql("SELECT codigo_patrimonio, modelo FROM veiculos", conn)
  if df_v.empty:
    st.warning("Cadastre equipamentos na frota antes de registrar abastecimentos.")
  else:
    with st.form("form_combustivel", clear_on_submit=False):
      col1, col2 = st.columns(2)
      with col1:
        equipamento_comb = st.selectbox(
            "Equipamento / Patrimônio", df_v["codigo_patrimonio"].tolist()
        )
        litros = st.number_input(
            "Quantidade de Litros Abastecidos",
            min_value=0.1,
            value=100.0,
            format="%.2f",
        )
        valor_total = st.number_input(
            "Valor Total Pago (R$)", min_value=0.0, value=600.0, format="%.2f"
        )
      with col2:
        km_horimetro = st.text_input("KM ou Horímetro Atual do Veículo")
        posto = st.text_input("Posto / Fornecedor de Combustível")
        motorista = st.text_input("Motorista / Responsável")
        data_abastecimento = st.date_input("Data do Abastecimento")

      salvar_comb = st.form_submit_button("Registrar Abastecimento")
      if salvar_comb:
        cursor.execute(
            "INSERT INTO combustivel (equipamento, litros, valor_total,"
            " km_horimetro, posto_posto, motorista, data) VALUES (?, ?, ?,"
            " ?, ?, ?, ?)",
            (
                equipamento_comb,
                float(litros),
                float(valor_total),
                str(km_horimetro),
                posto,
                motorista,
                str(data_abastecimento),
            ),
        )
        conn.commit()
        st.success("✅ Abastecimento registrado com sucesso!")
        st.rerun()

  st.divider()
  st.subheader("Histórico de Abastecimentos Registrados")
  df_c_hist = pd.read_sql("SELECT * FROM combustivel", conn)
  if not df_c_hist.empty:
    st.dataframe(df_c_hist, use_container_width=True)
    col_down1, col_down2 = st.columns(2)
    with col_down1:
      pdf_buffer = gerar_pdf_relatorio(
          "RELATÓRIO DE COMBUSTÍVEL - TABALMIX", df_c_hist
      )
      st.download_button(
          label="📥 Baixar Histórico em PDF",
          data=pdf_buffer,
          file_name="relatorio_combustivel_tabalmix.pdf",
          mime="application/pdf",
      )
    with col_down2:
      csv_buffer = gerar_csv_relatorio(df_c_hist)
      st.download_button(
          label="📊 Baixar Histórico em Planilha (.csv)",
          data=csv_buffer,
          file_name="relatorio_combustivel_tabalmix.csv",
          mime="text/csv",
      )
  else:
    st.info("Nenhum abastecimento registrado até o momento.")

elif menu == "🏗️ Mobilização / Desmobilização":
  st.title("🏗️ Controle de Mobilização e Desmobilização de Obras")
  df_v = pd.read_sql("SELECT codigo_patrimonio, modelo FROM veiculos", conn)
  if df_v.empty:
    st.warning("Cadastre equipamentos na frota antes de registrar mobilizações.")
  else:
    with st.form("form_mob", clear_on_submit=False):
      col1, col2 = st.columns(2)
      with col1:
        equipamento_mob = st.selectbox(
            "Equipamento (Patrimônio / Modelo)",
            df_v["codigo_patrimonio"].tolist(),
        )
        tipo_movimento = st.selectbox(
            "Tipo de Movimentação",
            [
                "Mobilização (Envio para Obra)",
                "Desmobilização (Retorno de Obra)",
                "Remanejamento entre Frentes",
            ],
        )
        destino_origem = st.text_input("Nome da Obra / Local de Destino-Origem")
        horimetro_km_mov = st.text_input(
            "Horímetro / KM no Momento da Movimentação"
        )
      with col2:
        responsavel = st.text_input("Responsável pela Liberação")
        data_mob = st.date_input("Data da Movimentação")
        motivo_condicao = st.text_input(
            "Motivo da Saída / Condição do Equipamento"
        )
        observacao = st.text_input("Observações Gerais")

      salvar_mob = st.form_submit_button("Registrar Movimentação de Obra")
      if salvar_mob:
        cursor.execute(
            "INSERT INTO mobilizacoes (equipamento, tipo_movimento,"
            " destino_origem, responsavel, data, horimetro_km_mov,"
            " motivo_condicao, observacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                equipamento_mob,
                tipo_movimento,
                destino_origem,
                responsavel,
                str(data_mob),
                str(horimetro_km_mov),
                motivo_condicao,
                observacao,
            ),
        )
        conn.commit()
        st.success("✅ Histórico de mobilização registrado com sucesso!")
        st.rerun()

  st.divider()
  st.subheader("Histórico de Mobilizações e Desmobilizações")
  df_mob_hist = pd.read_sql("SELECT * FROM mobilizacoes", conn)
  if not df_mob_hist.empty:
    st.dataframe(df_mob_hist, use_container_width=True)
  else:
    st.info("Nenhuma mobilização registrada até o momento.")

elif menu == "🛠️ Ordens de Serviço (OS)":
  st.title("🛠️ Gestão de Ordens de Serviço (OS) e Manutenções")
  df_v = pd.read_sql("SELECT codigo_patrimonio, modelo FROM veiculos", conn)
  if df_v.empty:
    st.warning(
        "Cadastre pelo menos um equipamento antes de abrir uma Ordem de Serviço."
    )
  else:
    with st.form("form_os", clear_on_submit=False):
      col1, col2 = st.columns(2)
      with col1:
        equipamento_escolhido = st.selectbox(
            "Equipamento / Patrimônio", df_v["codigo_patrimonio"].tolist()
        )
        tipo_manutencao = st.selectbox(
            "Tipo de Manutenção",
            ["Preventiva", "Corretiva", "Preditiva", "Revisão Geral"],
        )
        horimetro_km_manut = st.text_input("Horímetro / KM na Entrada")
        problema = st.text_area("Solicitação / Defeito Apresentado / Problema")
        servico_realizado = st.text_area("Serviços a Realizar / Realizados")
      with col2:
        pecas_utilizadas = st.text_input("Peças Utilizadas / Necessárias")
        custo_pecas = st.number_input(
            "Valor Total das Peças (R$)", min_value=0.0, format="%.2f"
        )
        mao_de_obra = st.number_input(
            "Valor da Mão de Obra (R$)", min_value=0.0, format="%.2f"
        )
        oficina = st.text_input("Oficina / Fornecedor Responsável")
        responsavel_os = st.text_input("Responsável Técnico / Mecânico")
        status_os = st.selectbox(
            "Status da OS",
            [
                "Aberta",
                "Em análise",
                "Aguardando peça",
                "Em manutenção",
                "Concluída",
                "Cancelada",
            ],
        )
        data_os = st.date_input("Data de Abertura")

      abrir_os = st.form_submit_button("Salvar e Emitir Ordem de Serviço (OS)")
      if abrir_os:
        custo_total = custo_pecas + mao_de_obra
        cursor.execute(
            "INSERT INTO manutencoes (equipamento, tipo_manutencao,"
            " horimetro_km_manut, problema, servico_realizado,"
            " pecas_utilizadas, custo_pecas, mao_de_obra, custo, oficina,"
            " responsavel, status_os, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?,"
            " ?, ?, ?, ?, ?)",
            (
                equipamento_escolhido,
                tipo_manutencao,
                horimetro_km_manut,
                problema,
                servico_realizado,
                pecas_utilizadas,
                custo_pecas,
                mao_de_obra,
                custo_total,
                oficina,
                responsavel_os,
                status_os,
                str(data_os),
            ),
        )
        conn.commit()
        st.success("✅ Ordem de Serviço gerada e salva com sucesso!")
        st.rerun()

  st.divider()
  st.subheader("🗓️ Histórico de Ordens de Serviço")
  df_m = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_m.empty:
    st.dataframe(df_m, use_container_width=True)
  else:
    st.info("Nenhuma Ordem de Serviço cadastrada ainda.")

elif menu == "🔩 Peças e Ferramentas":
  st.title("🔩 Controle de Peças, Insumos e Ferramentas de Oficina")
  tab1, tab2 = st.tabs(["Cadastrar Item", "Inventário Atual"])
  with tab1:
    with st.form("form_estoque", clear_on_submit=False):
      col1, col2 = st.columns(2)
      with col1:
        nome_item = st.text_input(
            "Nome da Peça, Filtro ou Ferramenta (Ex: Óleo 15W40)"
        )
        categoria = st.selectbox(
            "Categoria",
            [
                "Peça de Reposição",
                "Filtro e Lubrificante",
                "Ferramenta de Oficina",
                "Insumo de Concretagem",
            ],
        )
      with col2:
        quantidade = st.number_input("Quantidade em Estoque", min_value=1, value=1)
        valor_unitario = st.number_input(
            "Valor Unitário (R$)", min_value=0.0, format="%.2f"
        )
      salvar_item = st.form_submit_button("Adicionar ao Estoque")
      if salvar_item:
        if nome_item:
          cursor.execute(
              "INSERT INTO pecas (nome_item, categoria, quantidade,"
              " valor_unitario) VALUES (?, ?, ?, ?)",
              (nome_item, categoria, quantidade, valor_unitario),
          )
          conn.commit()
          st.success(f"✅ Item '{nome_item}' cadastrado com sucesso no estoque!")
          st.rerun()
        else:
          st.error("⚠️ Informe o nome da peça.")
  with tab2:
    df_p = pd.read_sql("SELECT * FROM pecas", conn)
    if not df_p.empty:
      st.dataframe(df_p, use_container_width=True)
    else:
      st.info("Nenhuma peça cadastrada no estoque.")

elif menu == "👥 Gestão de Clientes":
  st.title("👥 Cadastro de Clientes e Terceiros")
  with st.form("form_cliente_prof", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
      nome = st.text_input("Nome Completo / Razão Social")
      empresa = st.text_input("Nome Fantasia da Empresa")
      telefone = st.text_input("Telefone / WhatsApp de Contato")
    with col2:
      documento = st.text_input("CPF ou CNPJ")
      email = st.text_input("E-mail Comercial")
      endereco = st.text_input("Endereço Completo / Cidade")
    salvar_cliente = st.form_submit_button("Salvar Cadastro de Cliente")
    if salvar_cliente:
      if nome:
        cursor.execute(
            "INSERT INTO clientes (nome, empresa, telefone, documento, email,"
            " endereco) VALUES (?, ?, ?, ?, ?, ?)",
            (nome, empresa, telefone, documento, email, endereco),
        )
        conn.commit()
        st.success(f"✅ Cliente '{nome}' cadastrado com sucesso!")
        st.rerun()
      else:
        st.error("⚠️ O nome do cliente é obrigatório.")

  st.divider()
  st.subheader("Base de Clientes Cadastrados")
  df_cli = pd.read_sql("SELECT * FROM clientes", conn)
  if not df_cli.empty:
    st.dataframe(df_cli, use_container_width=True)
  else:
    st.info("Nenhum cliente cadastrado no momento.")

elif menu == "🔍 Consulta / Busca Geral":
  st.title("🔍 Consulta e Busca Geral Inteligente")
  termo_busca = st.text_input(
      "Digite o que deseja buscar (Ex: EQ-001, Chassi, Placa, Cliente...)"
  )
  if termo_busca:
    termo_like = f"%{termo_busca}%"
    st.divider()
    st.subheader("🚚 Resultados na Frota / Equipamentos")
    df_b_veiculos = pd.read_sql(
        "SELECT * FROM veiculos WHERE codigo_patrimonio LIKE ? OR placa LIKE"
        " ? OR chassi LIKE ? OR modelo LIKE ? OR responsavel LIKE ?",
        conn,
        params=(termo_like, termo_like, termo_like, termo_like, termo_like),
    )
    if not df_b_veiculos.empty:
      st.dataframe(df_b_veiculos, use_container_width=True)
    else:
      st.info("Nenhum equipamento encontrado com este termo.")

elif menu == "🔑 Login / Autenticação":
  st.title("🔑 Acesso ao Sistema — Tabalmix Concreto")
  st.markdown("Entre com suas credenciais para liberar as funções gerenciais.")

  with st.form("form_login_sistema"):
    email_input = st.text_input(
        "E-mail corporativo", value="alexcastro02522@gmail.com"
    )
    senha_input = st.text_input(
        "Senha de acesso", type="password", value="Alex275612@"
    )
    btn_entrar = st.form_submit_button("Entrar no Sistema")

    if btn_entrar:
      cursor.execute(
          "SELECT * FROM usuarios_sistema WHERE email = ? AND senha = ?",
          (email_input.strip(), senha_input.strip()),
      )
      usuario_encontrado = cursor.fetchone()
      if usuario_encontrado:
        st.session_state["usuario_logado"] = {
            "id": usuario_encontrado[0],
            "nome_completo": usuario_encontrado[1],
            "email": usuario_encontrado[2],
            "cargo": usuario_encontrado[4],
        }
        st.success(
            f"✅ Bem-vindo de volta, {usuario_encontrado[1]}! Acesso liberado."
        )
        st.rerun()
      else:
        st.error("⚠️ E-mail ou senha incorretos.")

elif menu == "⚙️ Painel de Licença (Admin)":
  st.title("⚙️ Painel Administrativo Master")
  df_lic = pd.read_sql("SELECT * FROM licenca", conn)
  if not df_lic.empty:
    st.markdown(
        f"**Status da Licença:** {df_lic.iloc[0]['status_assinatura']}"
    )
    st.markdown(f"**Plano Ativo:** {df_lic.iloc[0]['plano_atual']}")
  st.info(
      "Painel de controle corporativo Castro Tech para a Tabalmix Concreto."
  )
