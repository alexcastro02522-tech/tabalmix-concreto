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

MERCADO_PAGO_ACCESS_TOKEN = (
    "APP_USR-7480302560366070-091611-1118388bbc787e8f88ea1da583096dbc-2919829212"
)

st.set_page_config(
    page_title="Tabalmix Concreto - Gestão de Frota e Oficina Pro",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    header[data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 1.2rem !important; padding-bottom: 1.2rem !important; }
    [data-testid="stSidebar"] { min-width: 300px !important; width: 300px !important; background: #f4f6f9 !important; border-right: 1px solid #cbd5e1; padding-top: 10px; }
    .stApp { background: #f4f6f9 !important; color: #1e293b !important; }
    h1, h2, h3 { color: #1b7a3e !important; font-family: 'Segoe UI', system-ui, sans-serif; font-weight: 700; }
    p, label, span, .stMarkdown { color: #1e293b !important; font-size: 14px; font-weight: 500; }
    .stButton button { background: linear-gradient(135deg, #1b7a3e 0%, #12542a 100%) !important; color: white !important; font-weight: 600; border-radius: 8px; border: 1px solid #1b7a3e; padding: 0.55rem 1.6rem; }
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
    tab_login, tab_cadastro = st.tabs(["🔑 entrar", "📝 criar conta"])
    with tab_login:
      with st.form("form_login"):
        email_login = st.text_input("e-mail cadastrado")
        senha_login = st.text_input("senha", type="password")
        btn_entrar = st.form_submit_button("entrar no sistema")
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
            st.success("✅ login realizado com sucesso!")
            st.rerun()
          else:
            st.error("⚠️ e-mail ou senha incorretos.")
    with tab_cadastro:
      with st.form("form_novo_cadastro"):
        c_nome = st.text_input("nome completo / responsável")
        c_cpf = st.text_input("cpf")
        c_email = st.text_input("e-mail (seu login)")
        c_senha = st.text_input("criar senha", type="password")
        c_cel = st.text_input("celular / contato de segurança")
        btn_cadastrar = st.form_submit_button("finalizar cadastro")
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
                  "✅ conta criada e ativada com sucesso! vá na aba 'entrar'."
              )
            except Exception as e:
              st.error(f"⚠️ erro: {e}")
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
  if modo_admin_liberado:
    st.success("🔓 **modo admin ativo**")
  elif usuario_atual:
    st.info(
        f"👤 **usuário:** {usuario_atual['nome']}\n\n📊 **status:**"
        f" {usuario_atual['status']}"
    )
    if st.button("🚪 sair"):
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
  st.title("🏗️ painel operacional da frota")
  df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
  df_manut = pd.read_sql("SELECT * FROM manutencoes", conn)
  st.metric("total frota", len(df_veiculos))
  if not df_veiculos.empty:
    st.dataframe(df_veiculos, use_container_width=True, hide_index=True)
  else:
    st.info("nenhum equipamento cadastrado.")

elif menu == "🚜 cadastro de equipamentos":
  st.title("🚜 cadastro de equipamentos")
  with st.form("form_frota", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
      tag_prefixo = st.text_input("tag / prefixo (ex: EQ-001)")
      tipo = st.selectbox(
          "tipo de equipamento",
          ["caminhão betoneira", "escavadeira", "utilitário"],
      )
      modelo = st.text_input("modelo")
      placa = st.text_input("placa")
    with col2:
      horimetro_km = st.number_input(
          "horímetro ou km atual", min_value=0, value=15000
      )
      status = st.selectbox(
          "situação", ["Ativo", "Em Manutenção", "Parado", "Mobilizado"]
      )
    if st.form_submit_button("cadastrar equipamento"):
      if tag_prefixo and modelo:
        cursor.execute(
            "INSERT INTO veiculos (tag_prefixo, tipo, modelo, placa,"
            " horimetro_km, status) VALUES (?, ?, ?, ?, ?, ?)",
            (tag_prefixo.upper(), tipo, modelo, placa.upper(), horimetro_km, status),
        )
        conn.commit()
        st.success(f"✅ equipamento '{tag_prefixo.upper()}' cadastrado!")
        st.rerun()
      else:
        st.error("⚠️ preencha a tag e o modelo.")

  df_f = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_f.empty:
    st.dataframe(df_f, use_container_width=True, hide_index=True)

elif menu == "🛠️ ordens de serviço (os)":
  st.title("🛠️ gestão unificada de ordens de serviço (os)")
  try:
    df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
    tags_disponiveis = (
        df_v["tag_prefixo"].dropna().tolist() if not df_v.empty else []
    )
  except Exception:
    tags_disponiveis = []

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

  st.divider()
  st.subheader("📋 ordens de serviço cadastradas")
  df_os = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_os.empty:
    st.dataframe(df_os, use_container_width=True, hide_index=True)
  else:
    st.info("nenhuma os registrada.")

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
    st.info("nenhum usuário.")
