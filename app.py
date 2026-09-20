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
import streamlit.components.v1 as components

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

# ESTILIZAÇÃO VISUAL PREMIUM ENTERPRISE
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .block-container {
        padding-top: 1rem !important;
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
        font-family: 'Plus Jakarta Sans', sans-serif !important;
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
        pin_dig = st.text_input(
            "PIN numérico (4 dígitos)", max_chars=4, type="password"
        )
        btn_pin_sub = st.form_submit_button("Entrar com PIN")
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
            st.success("✅ Login por PIN validado!")
            st.rerun()
          else:
            st.error("⚠️ E-mail ou PIN inválidos.")

    elif escolha_modo_login == "🔑 Entrar com E-mail e Senha":
      with st.form("form_login"):
        st.markdown("### 🔑 Entrar na Conta")
        email_login = st.text_input("E-mail corporativo")
        senha_login = st.text_input("Senha de acesso", type="password")
        cadastrar_pin = st.text_input(
            "Cadastrar PIN rápido (4 dígitos - opcional)",
            max_chars=4,
            type="password",
        )
        btn_entrar = st.form_submit_button("Entrar no Sistema")

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
            st.success("✅ Login realizado com sucesso!")
            st.rerun()
          else:
            st.error("⚠️ E-mail ou senha incorretos.")

    elif escolha_modo_login == "📝 Criar Novo Cadastro":
      st.markdown("### 📝 Criar Novo Cadastro na Obra")
      c_nome = st.text_input("Nome Completo")
      c_apelido = st.text_input("Apelido / Primeiro Nome")
      c_cargo = st.selectbox(
          "Cargo / Função na Empresa",
          [
              "Diretoria / Gestão",
              "Engenheiro / Gestor de Obra",
              "Mecânico / Oficina",
              "Operador / Motorista / Campo",
          ],
      )

      with st.form("form_novo_cadastro"):
        c_cpf = st.text_input("CPF")
        c_email = st.text_input("E-mail corporativo de login")
        c_senha = st.text_input("Criar senha", type="password")
        c_cel = st.text_input("Celular / WhatsApp")
        c_vigencia = st.selectbox(
            "Modalidade de vigência",
            ["Plano Mensal (30 dias)", "Plano Anual (365 dias)"],
        )
        btn_cadastrar = st.form_submit_button(
            "Cadastrar e Prosseguir para Pagamento"
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
              st.success("✅ Conta cadastrada com sucesso!")
            except Exception as e:
              st.error(f"⚠️ Erro ao cadastrar: {e}")

    elif escolha_modo_login == "🎟️ Ativar com Chave Corporativa":
      with st.form("form_resgatar_chave_login"):
        st.markdown("### 🎟️ Ativar Conta com Chave Corporativa")
        email_resgate = st.text_input("E-mail cadastrado na conta")
        chave_digitada = st.text_input("Chave de ativação")
        btn_ativar_chave = st.form_submit_button("Ativar Acesso com Chave")
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
              st.warning("⚠️ Esta chave já foi utilizada.")
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
                st.success("🎉 Conta ativada com sucesso!")
              else:
                st.error("⚠️ E-mail não encontrado.")

    elif escolha_modo_login == "🔄 Recuperar Senha":
      with st.form("form_recuperar"):
        st.markdown("### 🔄 Recuperar Senha")
        rec_email = st.text_input("Digite seu e-mail cadastrado")
        btn_rec = st.form_submit_button("Consultar Senha")
        if btn_rec:
          cursor.execute(
              "SELECT senha, nome_completo FROM usuarios_sistema WHERE email ="
              " ?",
              (rec_email,),
          )
          res_rec = cursor.fetchone()
          if res_rec:
            st.info(f"👤 Olá, {res_rec[1]}. Sua senha é: **{res_rec[0]}**")
          else:
            st.error("⚠️ E-mail não encontrado.")

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
    st.info("Nenhum registro encontrado.")
    return
  
  # Sistema de Gestão e Ocultação de Colunas para o Administrador / Gestor
  try:
    cursor.execute("SELECT ordem_colunas FROM config_colunas WHERE tabela = ?", (nome_tabela,))
    res_conf = cursor.fetchone()
    if res_conf and res_conf[0]:
      cols_ocultas = [c.strip() for c in res_conf[0].split(",") if c.strip()]
      cols_visiveis = [c for c in df.columns if c not in cols_ocultas]
      if cols_visiveis:
        df = df[cols_visiveis]
  except Exception:
    pass

  st.dataframe(df, use_container_width=True, hide_index=True)


with st.sidebar:
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_logo_side = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 16px; padding: 14px; text-align: center; margin-bottom: 12px; color: white;">
                <div style="font-size: 15px; font-weight: 900; margin-bottom: 8px;">🏗️ TABALMIX CONCRETO</div>
                <div style="border-radius: 12px; overflow: hidden; max-height: 105px; border: 2px solid rgba(255,255,255,0.8); margin-bottom: 8px;">
                    <img src="data:image/jpeg;base64,{encoded_logo_side}" style="width: 100%; height: 100px; object-fit: cover;">
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    pass

  if modo_admin_liberado:
    st.success("🔓 **Modo Admin Enterprise Ativo**")
  elif usuario_atual:
    st.markdown(
        f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px; margin-bottom: 12px;">
                <p style="margin: 0; font-weight: bold; color: #0f172a; font-size: 14px;">👤 {usuario_atual['apelido']}</p>
                <p style="margin: 3px 0 4px 0; font-size: 11.5px; color: #047857; font-weight: 700;">{usuario_atual['cargo']}</p>
                <span style="color: #059669; font-weight: bold; font-size: 11px; background: #ecfdf5; padding: 2px 8px; border-radius: 6px; display: inline-block;">🟢 Sessão Ativa</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚪 Encerrar Sessão"):
      st.session_state["usuario_logado"] = None
      try:
        st.query_params.clear()
      except Exception:
        pass
      st.rerun()
  st.markdown("---")

lista_menus = [
    "📊 Visão Geral",
    "🚜 Cadastro de Equipamentos",
    "⛽ Abastecimentos & Combustível",
    "🏗️ Mobilização / Desmobilização",
    "🛠️ Ordens de Serviço (OS)",
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
  st.markdown("Indicadores consolidados em tempo real para tomada de decisão executiva.")

  df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
  df_manut = pd.read_sql("SELECT * FROM manutencoes", conn)
  df_comb = pd.read_sql("SELECT * FROM combustivel", conn)
  df_pecas = pd.read_sql("SELECT * FROM pecas", conn)
  df_cli = pd.read_sql("SELECT * FROM clientes", conn)

  col1, col2, col3, col4, col5 = st.columns(5)
  with col1:
    st.metric("Total Frota", len(df_veiculos))
  with col2:
    st.metric(
        "OS Abertas",
        len(df_manut[df_manut["status_os"] == "aberta"])
        if not df_manut.empty
        else 0,
    )
  with col3:
    st.metric(
        "Custo Manut.",
        f"R$ {df_manut['custo'].sum() if not df_manut.empty else 0.0:,.2f}",
    )
  with col4:
    st.metric(
        "Gasto Combust.",
        f"R$ {df_comb['valor_total'].sum() if not df_comb.empty else 0.0:,.2f}",
    )
  with col5:
    st.metric(
        "Total Litros",
        f"{df_comb['litros'].sum() if not df_comb.empty else 0.0:,.1f} L",
    )

  st.divider()

  # ESTATÍSTICAS E GRÁFICOS EXECUTIVOS
  st.markdown("### 📈 Estatísticas e Gráficos de Desempenho")
  col_g1, col_g2 = st.columns(2)

  with col_g1:
    st.markdown("#### 🛠️ Custo de Manutenção por Tipo")
    if not df_manut.empty and "tipo_manutencao" in df_manut.columns and "custo" in df_manut.columns:
      df_custo_tipo = df_manut.groupby("tipo_manutencao")["custo"].sum().reset_index()
      st.bar_chart(df_custo_tipo.set_index("tipo_manutencao"))
    else:
      st.info("Ainda sem dados suficientes para exibir o gráfico de manutenções.")

  with col_g2:
    st.markdown("#### ⛽ Consumo de Combustível (Litros) por Equipamento")
    if not df_comb.empty and "equipamento" in df_comb.columns and "litros" in df_comb.columns:
      df_litros_eq = df_comb.groupby("equipamento")["litros"].sum().reset_index()
      st.bar_chart(df_litros_eq.set_index("equipamento"))
    else:
      st.info("Ainda sem dados suficientes para exibir o gráfico de combustíveis.")

  st.divider()
  st.markdown("### 📋 Resumo Geral da Frota em Operação")
  if not df_veiculos.empty:
    exibir_tabela_padronizada(df_veiculos, "veiculos")
    if st.button("📄 Gerar Relatório Executivo Geral em PDF"):
      pdf_geral = gerar_pdf_relatorio("Relatório Executivo Geral da Frota", df_veiculos)
      st.download_button(
          label="📥 Baixar PDF Certificado",
          data=pdf_geral,
          file_name="relatorio_executivo_tabalmix.pdf",
          mime="application/pdf"
      )
  else:
    st.info("Nenhum veículo registado na frota.")

elif menu == "🚜 Cadastro de Equipamentos":
  st.title("🚜 Cadastro de Equipamentos & Vistoria Fotográfica")
  st.markdown(
      "Gira a frota, atribua linhas operacionais (Linha Amarela, Marrom,"
      " Concreto) e execute a vistoria fotográfica completa."
  )

  tab_eq_lista, tab_eq_cad, tab_eq_foto = st.tabs([
      "📋 Frota Cadastrada",
      "➕ Registar Novo Equipamento",
      "📸 Vistoria Fotográfica (Até 15 Imagens)",
  ])

  with tab_eq_lista:
    df_f = pd.read_sql("SELECT * FROM veiculos", conn)
    if not df_f.empty:
      exibir_tabela_padronizada(df_f, "veiculos")
    else:
      st.info("Nenhum equipamento cadastrado ainda.")

  with tab_eq_cad:
    with st.form("form_cad_veiculo_novo"):
      st.markdown("### 🚜 Novo Veículo / Equipamento")
      c_e1, c_e2 = st.columns(2)
      with c_e1:
        f_prefixo = st.text_input("Prefixo / Tag (ex: BET-01)")
        f_cat = st.selectbox(
            "Linha / Categoria Operacional",
            [
                "🟡 Linha Amarela (Escavadeiras, Pás, Retro)",
                "🟤 Linha Marrom (Tratores, Estacionários)",
                "🚚 Linha Concreto (Caminhões Betoneira e Bomba)",
                "🚛 Linha Branca / Apoio (Carrocerias, Utilitários)",
            ],
        )
        f_marca = st.text_input("Marca (ex: Mercedes-Benz, Ford, Caterpillar)")
        f_modelo = st.text_input("Modelo (ex: 2423 B, Cargo 2622)")
        f_ano = st.number_input("Ano de Fabricação", value=2020, step=1)
        f_cor = st.text_input("Cor")
      with c_e2:
        f_placa = st.text_input("Placa")
        f_chassi = st.text_input("Chassi")
        f_renavam = st.text_input("Renavam")
        f_comb = st.selectbox("Combustível", ["Diesel S10", "Diesel S500", "Gasolina"])
        f_horimetro = st.number_input(
            "Km / Horímetro Atual", value=0, step=100
        )
        f_empresa = st.text_input("Empresa / Filial", value="Tabalmix Concreto")

      btn_salvar_eq = st.form_submit_button("💾 Salvar Equipamento na Frota")
      if btn_salvar_eq:
        if f_marca and f_modelo:
          cursor.execute(
              "INSERT INTO veiculos (tag_prefixo, categoria_equipamento, marca,"
              " modelo, ano, chassi, renavam, placa, crv, cor, combustivel,"
              " empresa, horimetro_km, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?,"
              " '', ?, ?, ?, ?, 'Ativo')",
              (
                  f_prefixo,
                  f_cat,
                  f_marca,
                  f_modelo,
                  int(f_ano),
                  f_chassi,
                  f_renavam,
                  f_placa,
                  f_cor,
                  f_comb,
                  f_empresa,
                  int(f_horimetro),
              ),
          )
          conn.commit()
          st.success("✅ Equipamento e linha operacional registados com sucesso!")
          st.rerun()
        else:
          st.error("⚠️ Preencha pelo menos a Marca e o Modelo.")

  with tab_eq_foto:
    st.markdown("### 📸 Vistoria Fotográfica Completa (Até 15 Ângulos)")
    st.markdown(
        "Registe fotos detalhadas (Frente, Verso, Laterais, Rodas, Pneus,"
        " Motor, Cabine, etc.) para auditoria e controle de danos."
    )

    try:
      df_veiculos_f = pd.read_sql("SELECT id, marca, modelo, placa FROM veiculos", conn)
    except Exception:
      df_veiculos_f = pd.DataFrame()

    if not df_veiculos_f.empty:
      veiculo_vistoria = st.selectbox(
          "Selecione o veículo para anexar as fotografias:",
          [
              f"ID {r['id']} — {r['marca']} {r['modelo']} (Placa: {r['placa']})"
              for _, r in df_veiculos_f.iterrows()
          ],
      )

      fotos_enviadas = st.file_uploader(
          "Carregar fotografias da vistoria (Selecione até 15 imagens de uma vez):",
          type=["png", "jpg", "jpeg"],
          accept_multiple_files=True,
      )

      if fotos_enviadas:
        st.info(f"📸 {len(fotos_enviadas)} imagens selecionadas para carregamento.")
        os.makedirs("vistorias_frota", exist_ok=True)

        if st.button("🚀 Salvar e Armazenar Vistoria Fotográfica"):
          for idx, foto in enumerate(fotos_enviadas[:15]):
            nome_foto = (
                f"vistoria_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}_{foto.name}"
            )
            caminho_foto = os.path.join("vistorias_frota", nome_foto)
            with open(caminho_foto, "wb") as f_out:
              f_out.write(foto.getbuffer())

          st.success(
              "✅ Vistoria fotográfica armazenada com sucesso no sistema e"
              " pronta para auditoria!"
          )
    else:
      st.info(
          "Registe primeiro um veículo na aba 'Registar Novo Equipamento' para"
          " poder realizar a vistoria."
      )

elif menu == "⛽ Abastecimentos & Combustível":
  st.title("⛽ Controle de Abastecimento e Combustível")
  st.markdown("Registe e gira todos os abastecimentos da frota em campo.")

  tab_c_lista, tab_c_cad = st.tabs([
      "📋 Histórico de Abastecimentos",
      "➕ Registar Abastecimento",
  ])

  with tab_c_lista:
    df_c = pd.read_sql("SELECT * FROM combustivel ORDER BY id DESC", conn)
    if not df_c.empty:
      exibir_tabela_padronizada(df_c, "combustivel")
      if st.button("📄 Gerar Relatório em PDF de Combustível"):
        pdf_c = gerar_pdf_relatorio("Relatório de Abastecimento", df_c)
        st.download_button(
            label="📥 Baixar PDF Certificado",
            data=pdf_c,
            file_name="relatorio_combustivel.pdf",
            mime="application/pdf",
        )
    else:
      st.info("Nenhum abastecimento registado.")

  with tab_c_cad:
    with st.form("form_abastecimento_novo"):
      c_ab1, c_ab2 = st.columns(2)
      with c_ab1:
        eq_ab = st.text_input("Equipamento / Prefixo")
        litros_ab = st.number_input("Quantidade em Litros", value=100.0, step=10.0)
        valor_ab = st.number_input("Valor Total (R$)", value=600.0, step=50.0)
      with c_ab2:
        km_ab = st.text_input("Km ou Horímetro no Posto")
        posto_ab = st.text_input("Posto / Fornecedor")
        motorista_ab = st.text_input("Motorista / Responsável")

      btn_salvar_ab = st.form_submit_button("💾 Salvar Abastecimento")
      if btn_salvar_ab:
        if eq_ab:
          cursor.execute(
              "INSERT INTO combustivel (equipamento, litros, valor_total,"
              " km_horimetro, posto_posto, motorista, data) VALUES (?, ?, ?, ?,"
              " ?, ?, ?)",
              (
                  eq_ab,
                  litros_ab,
                  valor_ab,
                  km_ab,
                  posto_ab,
                  motorista_ab,
                  datetime.now().strftime("%d/%m/%Y %H:%M"),
              ),
          )
          conn.commit()
          st.success("✅ Abastecimento registado com sucesso!")
          st.rerun()
        else:
          st.error("⚠️ Informe o equipamento.")

elif menu == "🏗️ Mobilização / Desmobilização":
  st.title("🏗️ Gestão de Mobilização e Desmobilização de Obras")
  st.markdown(
      "Registe novas movimentações selecionando o veículo da frota e edite com"
      " justificativa obrigatória guardada no banco de dados."
  )

  try:
    df_veiculos_mob = pd.read_sql(
        "SELECT id, tag_prefixo, categoria_equipamento, marca, modelo, placa FROM"
        " veiculos",
        conn,
    )
  except Exception:
    df_veiculos_mob = pd.DataFrame()

  lista_veiculos_opcoes = []
  if not df_veiculos_mob.empty:
    lista_veiculos_opcoes = [
        f"[{r['categoria_equipamento']}] ID {r['id']} — {r['marca']} {r['modelo']} (Placa: {r['placa'] if r['placa'] else 'N/A'})"
        for _, r in df_veiculos_mob.iterrows()
    ]
  else:
    lista_veiculos_opcoes = ["Nenhum veículo cadastrado (Cadastre na aba ao lado)"]

  tab_cad_mob, tab_edit_mob = st.tabs([
      "➕ Registar Nova Movimentação",
      "✏️ Editar Registos & Histórico",
  ])

  with tab_cad_mob:
    with st.form("form_mob_novo"):
      c1, c2 = st.columns(2)
      with c1:
        veiculo_escolhido = st.selectbox(
            "Selecionar Equipamento / Linha da Frota", lista_veiculos_opcoes
        )
        tipo_mov = st.selectbox(
            "Tipo de Movimento",
            [
                "Mobilização (Envio para Obra)",
                "Desmobilização (Retorno)",
                "Remanejamento",
            ],
        )
        destino = st.text_input("Obra / Destino-Origem")
      with c2:
        resp = st.text_input("Responsável / Motorista")
        dt_mob = st.date_input("Data da Ocorrência")
        motivo_inicial = st.text_input(
            "Motivo / Condição Inicial (Ex: Início de fundação na Obra Central)"
        )
        obs = st.text_area("Observações operacionais")

      btn_cad_mob = st.form_submit_button("💾 Salvar Nova Movimentação")
      if btn_cad_mob:
        if destino and "Nenhum veículo" not in veiculo_escolhido:
          hist_inicial = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Criado por {resp if resp else 'Operacional'} — Motivo inicial: {motivo_inicial}"
          cursor.execute(
              "INSERT INTO mobilizacoes (equipamento, tipo_movimento,"
              " destino_origem, responsavel, data, motivo_condicao, observacao,"
              " foto_checklist, historico_edicoes) VALUES (?, ?, ?, ?, ?, ?, ?,"
              " '', ?)",
              (
                  veiculo_escolhido,
                  tipo_mov,
                  destino,
                  resp,
                  str(dt_mob),
                  motivo_inicial,
                  obs,
                  hist_inicial,
              ),
          )
          conn.commit()
          st.success(
              "✅ Movimentação de mobilização registada com sucesso na base de"
              " dados!"
          )
          st.rerun()
        else:
          st.error(
              "⚠️ Seleciona um veículo válido e preenche o destino/obra."
          )

  with tab_edit_mob:
    st.markdown("### ✏️ Editar Informações e Registar Motivo da Alteração")
    try:
      df_mobs_edit = pd.read_sql(
          "SELECT * FROM mobilizacoes ORDER BY id DESC", conn
      )
    except Exception:
      df_mobs_edit = pd.DataFrame()

    if not df_mobs_edit.empty:
      exibir_tabela_padronizada(df_mobs_edit, "mobilizacoes")

      id_mob_sel = st.selectbox(
          "Selecione o ID da mobilização para editar:",
          df_mobs_edit["id"].tolist(),
      )
      reg_atual = df_mobs_edit[df_mobs_edit["id"] == id_mob_sel].iloc[0]

      with st.form(f"form_editar_mob_{id_mob_sel}"):
        st.markdown(f"#### Editando Registo ID #{id_mob_sel}")
        e_eq = st.selectbox(
            "Equipamento / Linha",
            lista_veiculos_opcoes,
            index=0,
        )
        e_tipo = st.selectbox(
            "Tipo de Movimento",
            [
                "Mobilização (Envio para Obra)",
                "Desmobilização (Retorno)",
                "Remanejamento",
            ],
        )
        e_dest = st.text_input("Obra / Destino", value=str(reg_atual["destino_origem"]))
        e_resp = st.text_input("Responsável", value=str(reg_atual["responsavel"]))
        e_obs = st.text_area("Observações", value=str(reg_atual["observacao"]))

        st.markdown("---")
        st.markdown(
            "🔴 **OBRIGATÓRIO:** Informe abaixo o motivo exato da alteração (Ex:"
            " motorista desistiu, troca de última hora, alteração de destino):"
        )
        motivo_alteracao = st.text_input(
            "Motivo da Edição / Atualização",
            placeholder="Ex: Motorista recusou viagem por motivo pessoal...",
        )

        btn_salvar_edicao = st.form_submit_button(
            "💾 Atualizar Registo e Salvar Histórico"
        )

        if btn_salvar_edicao:
          if not motivo_alteracao.strip():
            st.error(
                "⚠️ O campo 'Motivo da Edição' é obrigatório para guardar na"
                " base de dados!"
            )
          else:
            historico_antigo = (
                str(reg_atual["historico_edicoes"])
                if reg_atual["historico_edicoes"]
                else ""
            )
            novo_historico_item = f"\n[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Editado. Motivo: {motivo_alteracao}"
            historico_atualizado = historico_antigo + novo_historico_item

            cursor.execute(
                "UPDATE mobilizacoes SET equipamento = ?, tipo_movimento = ?,"
                " destino_origem = ?, responsavel = ?, observacao = ?,"
                " historico_edicoes = ? WHERE id = ?",
                (
                    e_eq,
                    e_tipo,
                    e_dest,
                    e_resp,
                    e_obs,
                    historico_atualizado,
                    int(id_mob_sel),
                ),
            )
            conn.commit()
            st.success(
                "✅ Registo atualizado com sucesso e motivo guardado no"
                " histórico do banco de dados!"
            )
            st.rerun()
    else:
      st.info("Nenhuma mobilização registada para editar.")

elif menu == "🛠️ Ordens de Serviço (OS)":
  st.title("🛠️ Gestão Unificada de Ordens de Serviço (OS)")
  st.markdown(
      "Gira manutenções preventivas, corretivas e custos de oficina mecânica."
  )

  tab_os_lista, tab_os_cad = st.tabs([
      "📋 Ordens de Serviço Registadas",
      "➕ Abrir Nova OS",
  ])

  with tab_os_lista:
    df_os = pd.read_sql("SELECT * FROM manutencoes ORDER BY id DESC", conn)
    if not df_os.empty:
      exibir_tabela_padronizada(df_os, "manutencoes")
      if st.button("📄 Gerar Relatório em PDF de OS"):
        pdf_os = gerar_pdf_relatorio("Relatório de Ordens de Serviço", df_os)
        st.download_button(
            label="📥 Baixar PDF Certificado",
            data=pdf_os,
            file_name="relatorio_ordens_servico.pdf",
            mime="application/pdf",
        )
    else:
      st.info("Nenhuma Ordem de Serviço registada.")

  with tab_os_cad:
    with st.form("form_os_novo"):
      o1, o2 = st.columns(2)
      with o1:
        os_prefixo = st.text_input("Equipamento / Prefixo")
        os_tipo = st.selectbox(
            "Tipo de Manutenção",
            ["Corretiva", "Preventiva", "Revisão Periódica"],
        )
        os_prob = st.text_area("Descrição do Problema / Serviço")
      with o2:
        os_custo_pecas = st.number_input("Custo de Peças (R$)", value=0.0, step=50.0)
        os_mao = st.number_input("Mão de Obra (R$)", value=0.0, step=50.0)
        os_oficina = st.text_input("Oficina / Mecânico Responsável")
        os_status = st.selectbox("Status da OS", ["aberta", "concluida"])

      btn_salvar_os = st.form_submit_button("💾 Salvar Ordem de Serviço")
      if btn_salvar_os:
        if os_prefixo:
          custo_total_os = os_custo_pecas + os_mao
          cursor.execute(
              "INSERT INTO manutencoes (tag_prefixo, tipo_manutencao,"
              " horimetro_km_manut, origem_falha, descricao_problema,"
              " data_abertura, hora_abertura, pecas_utilizadas, custo_pecas,"
              " mao_de_obra, custo, oficina, tecnico_mecanico, data_fechamento,"
              " hora_fechamento, status_os) VALUES (?, ?, '0', 'Campo', ?, ?,"
              " '', '', ?, ?, ?, ?, '', '', '', ?)",
              (
                  os_prefixo,
                  os_tipo,
                  os_prob,
                  datetime.now().strftime("%d/%m/%Y"),
                  os_custo_pecas,
                  os_mao,
                  custo_total_os,
                  os_oficina,
                  os_status,
              ),
          )
          conn.commit()
          st.success("✅ Ordem de Serviço aberta com sucesso!")
          st.rerun()
        else:
          st.error("⚠️ Informe o equipamento.")

elif menu == "🔩 Peças e Ferramentas":
  st.title("🔩 Controle de Peças e Ferramentas")
  st.markdown("Gira o stock de peças e materiais no almoxarifado da obra.")

  tab_p_lista, tab_p_cad = st.tabs([
      "📋 Stock Atual",
      "➕ Registar Peça / Item",
  ])

  with tab_p_lista:
    df_pecas = pd.read_sql("SELECT * FROM pecas ORDER BY id DESC", conn)
    if not df_pecas.empty:
      exibir_tabela_padronizada(df_pecas, "pecas")
    else:
      st.info("Nenhuma peça registada no stock.")

  with tab_p_cad:
    with st.form("form_peca_novo"):
      p1, p2 = st.columns(2)
      with p1:
        p_nome = st.text_input("Nome da Peça / Item")
        p_cat = st.text_input("Categoria (ex: Filtros, Óleo, Pneus)")
      with p2:
        p_qtd = st.number_input("Quantidade em Stock", value=1, step=1)
        p_val = st.number_input("Valor Unitário (R$)", value=0.0, step=10.0)

      btn_salvar_peca = st.form_submit_button("💾 Adicionar Item ao Stock")
      if btn_salvar_peca:
        if p_nome:
          cursor.execute(
              "INSERT INTO pecas (nome_item, categoria, quantidade,"
              " valor_unitario) VALUES (?, ?, ?, ?)",
              (p_nome, p_cat, int(p_qtd), float(p_val)),
          )
          conn.commit()
          st.success("✅ Peça adicionada ao stock com sucesso!")
          st.rerun()
        else:
          st.error("⚠️ Informe o nome da peça.")

elif menu == "👥 Gestão de Clientes":
  st.title("👥 Gestão de Clientes e Obras Parceiras")
  st.markdown("Registo e contacto dos clientes e construtoras atendidas.")

  tab_cli_lista, tab_cli_cad = st.tabs([
      "📋 Clientes Registados",
      "➕ Registar Novo Cliente",
  ])

  with tab_cli_lista:
    df_cli = pd.read_sql("SELECT * FROM clientes ORDER BY id DESC", conn)
    if not df_cli.empty:
      exibir_tabela_padronizada(df_cli, "clientes")
    else:
      st.info("Nenhum cliente registado.")

  with tab_cli_cad:
    with st.form("form_cliente_novo"):
      cl1, cl2 = st.columns(2)
      with cl1:
        c_nome = st.text_input("Nome do Cliente / Responsável")
        c_emp = st.text_input("Nome da Empresa / Construtora")
        c_tel = st.text_input("Telefone / WhatsApp")
      with cl2:
        c_doc = st.text_input("CPF / CNPJ")
        c_email = st.text_input("E-mail")
        c_end = st.text_input("Endereço da Obra")

      btn_salvar_cli = st.form_submit_button("💾 Salvar Cliente")
      if btn_salvar_cli:
        if c_nome:
          cursor.execute(
              "INSERT INTO clientes (nome, empresa, telefone, documento, email,"
              " endereco) VALUES (?, ?, ?, ?, ?, ?)",
              (c_nome, c_emp, c_tel, c_doc, c_email, c_end),
          )
          conn.commit()
          st.success("✅ Cliente registado com sucesso!")
          st.rerun()
        else:
          st.error("⚠️ Informe o nome do cliente.")

elif menu == "💬 Chat Tabalmix Pro & Rede":
  st.markdown(
      """
        <style>
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 540px;
            overflow-y: auto;
            padding: 16px;
            background: #f8fafc;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
        }
        .msg-row {
            display: flex;
            width: 100%;
            margin-bottom: 2px;
        }
        .msg-row-eu {
            justify-content: flex-end;
        }
        .msg-row-outro {
            justify-content: flex-start;
        }
        .msg-bubble {
            padding: 12px 18px;
            border-radius: 16px;
            max-width: 85%;
            font-family: 'Plus Jakarta Sans', sans-serif;
            position: relative;
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        }
        .msg-bubble-eu {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: white;
            border-top-right-radius: 3px;
        }
        .msg-bubble-outro {
            background: #ffffff;
            color: #0f172a;
            border: 1px solid #e2e8f0;
            border-top-left-radius: 3px;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

  st.title("💬 Central Pro Enterprise — Chat & Live Ops")
  st.markdown("Comunicação em tempo real com balões limpos estilo WhatsApp.")

  cursor.execute(
      "SELECT id, apelido, cargo_setor FROM usuarios_sistema ORDER BY id DESC"
  )
  todos_usuarios_db = cursor.fetchall()

  tab_chat_txt, tab_videocall = st.tabs([
      "💬 Canal de Mensagens Live",
      "📞 Chamada Direta de Vídeo Integrada",
  ])

  with tab_chat_txt:
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
      if todos_usuarios_db:
        opcoes_colab = [
            f"👤 {u[1]} — Cargo: {u[2]} (ID: {u[0]})" for u in todos_usuarios_db
        ]
        colab_escolhido_str = st.selectbox(
            "Canal / Conversa Privada com:",
            ["🌐 Canal Geral (Toda a Equipe)"] + opcoes_colab,
        )
      else:
        colab_escolhido_str = "🌐 Canal Geral (Toda a Equipe)"
    with col_f2:
      termo_busca_chat = st.text_input(
          "🔍 Pesquisa Global", placeholder="Ex: pneu, beta..."
      )

    remetente_atual = (
        usuario_atual["apelido"] if usuario_atual else "Administrador Master"
    )
    cargo_atual = (
        usuario_atual["cargo"] if usuario_atual else "Diretoria / Gestão"
    )

    if termo_busca_chat.strip():
      df_msgs = pd.read_sql(
          "SELECT * FROM chat_interno WHERE mensagem LIKE ? ORDER BY id ASC LIMIT"
          " 60",
          conn,
          params=(f"%{termo_busca_chat}%",),
      )
    elif "Canal Geral" in colab_escolhido_str:
      df_msgs = pd.read_sql(
          "SELECT * FROM chat_interno WHERE destinatario LIKE '%Canal Geral%'"
          " OR destinatario LIKE '%Equipe Geral%' ORDER BY id ASC LIMIT 60",
          conn,
      )
    else:
      nome_colab_alvo = colab_escolhido_str.split("—")[0].replace("👤", "").strip()
      df_msgs = pd.read_sql(
          "SELECT * FROM chat_interno WHERE destinatario LIKE ? OR remetente"
          " LIKE ? ORDER BY id ASC LIMIT 60",
          conn,
          params=(f"%{nome_colab_alvo}%", f"%{nome_colab_alvo}%"),
      )

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    if not df_msgs.empty:
      for _, row_m in df_msgs.iterrows():
        is_eu = remetente_atual in str(row_m["remetente"])
        row_class = "msg-row msg-row-eu" if is_eu else "msg-row msg-row-outro"
        bubble_class = (
            "msg-bubble msg-bubble-eu" if is_eu else "msg-bubble msg-bubble-outro"
        )
        cor_autor = "#d1fae5" if is_eu else "#047857"

        st.markdown(
            f"""
            <div class="{row_class}">
                <div class="{bubble_class}">
                    <div style="font-size: 10px; font-weight: 800; color: {cor_autor}; margin-bottom: 4px; display: flex; justify-content: space-between; gap: 15px;">
                        <span>👤 {row_m['remetente']} ➔ {row_m['destinatario']} &nbsp; • &nbsp; <b>[⋮]</b></span>
                        <span style="opacity: 0.8;">{row_m['data_envio']}</span>
                    </div>
                    <div style="font-size: 13.5px; line-height: 1.4; white-space: pre-wrap;">{row_m['mensagem']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(f"⚙️ Opções da Mensagem #{row_m['id']}", expanded=False):
          col_m1, col_m2, col_m3 = st.columns([1, 2, 1])

          with col_m1:
            texto_limpo_js = (
                str(row_m["mensagem"])
                .replace('"', '\\"')
                .replace("\n", " ")
                .replace("\r", " ")
            )
            copiar_html_min = f"""
                    <button onclick="navigator.clipboard.writeText('{texto_limpo_js}'); alert('📋 Copiado!');" style="background:#059669; color:white; border:none; padding:6px 10px; border-radius:6px; font-size:11px; font-weight:700; cursor:pointer; width:100%;">📋 Copiar</button>
                """
            components.html(copiar_html_min, height=32)

          with col_m2:
            if todos_usuarios_db:
              lista_enc = [
                  f"👤 {u[1]} — Cargo: {u[2]}" for u in todos_usuarios_db
              ]
              destino_fwd = st.selectbox(
                  "Reencaminhar para:",
                  ["🌐 Canal Geral"] + lista_enc,
                  key=f"sel_fwd_{row_m['id']}",
              )
              if st.button("🚀 Enviar Reencaminhado", key=f"btn_fwd_{row_m['id']}"):
                data_env_fwd = datetime.now().strftime("%H:%M — %d/%m")
                msg_fwd_texto = (
                    f"[Encaminhado de {row_m['remetente']}]\n{row_m['mensagem']}"
                )
                cursor.execute(
                    "INSERT INTO chat_interno (remetente, destinatario, cargo,"
                    " mensagem, arquivo_path, arquivo_nome, data_envio) VALUES"
                    " (?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"{remetente_atual} ({cargo_atual})",
                        destino_fwd,
                        cargo_atual,
                        msg_fwd_texto,
                        "",
                        "",
                        data_env_fwd,
                    ),
                )
                conn.commit()
                st.success("✅ Reencaminhado!")
                st.rerun()

          with col_m3:
            if st.button("🗑️ Apagar", key=f"del_b_{row_m['id']}"):
              cursor.execute(
                  "DELETE FROM chat_interno WHERE id = ?", (row_m["id"],)
              )
              conn.commit()
              st.rerun()

        if row_m["arquivo_path"] and os.path.exists(str(row_m["arquivo_path"])):
          if row_m["arquivo_nome"].lower().endswith((".png", ".jpg", ".jpeg")):
            st.image(
                row_m["arquivo_path"],
                caption=f"Mídia de {row_m['remetente']}",
                width=240,
            )
          with open(row_m["arquivo_path"], "rb") as f_down:
            st.download_button(
                label=f"📥 Baixar: {row_m['arquivo_nome']}",
                data=f_down.read(),
                file_name=row_m["arquivo_nome"],
                key=f"dl_chat_arq_{row_m['id']}",
            )
        st.markdown(
            "<hr style='margin: 4px 0; border: none; border-top: 1px solid"
            " #e2e8f0;'>",
            unsafe_allow_html=True,
        )
    else:
      st.info("Ainda sem mensagens nesta conversa. Envia a primeira abaixo!")

    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("form_chat_direto_pro", clear_on_submit=True):
      col_msg1, col_msg2 = st.columns([3, 1])
      with col_msg1:
        msg_sala_txt = st.text_input(
            "Escreve a tua mensagem operacional...",
            placeholder="Mensagem segura...",
        )
      with col_msg2:
        file_sala_up = st.file_uploader(
            "Anexar Mídia",
            type=["png", "jpg", "jpeg", "pdf", "docx"],
            label_visibility="collapsed",
        )

      btn_enviar_chat = st.form_submit_button("🚀 Enviar Mensagem")

      if btn_enviar_chat:
        if not msg_sala_txt.strip() and not file_sala_up:
          st.warning("⚠️ Escreve uma mensagem ou anexa um arquivo.")
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

          data_env_s = datetime.now().strftime("%H:%M — %d/%m")
          cursor.execute(
              "INSERT INTO chat_interno (remetente, destinatario, cargo,"
              " mensagem, arquivo_path, arquivo_nome, data_envio) VALUES (?, ?,"
              " ?, ?, ?, ?, ?)",
              (
                  f"{remetente_atual} ({cargo_atual})",
                  colab_escolhido_str,
                  cargo_atual,
                  msg_sala_txt,
                  path_s,
                  nome_s,
                  data_env_s,
              ),
          )
          conn.commit()
          st.rerun()

  with tab_videocall:
    st.markdown("### 📞 Central de Chamada Direta Pessoal")
    if todos_usuarios_db:
      alvos_chamada = [f"{u[1]} ({u[2]})" for u in todos_usuarios_db]
      alvo_selecionado = st.selectbox(
          "Quem vai receber o convite para a reunião?",
          alvos_chamada,
          key="sel_alvo_video",
      )
    else:
      alvo_selecionado = "Equipe Geral"

    nome_sala_direta = f"TabalmixDirectCall{ ''.join(e for e in alvo_selecionado.split()[0] if e.isalnum()) }2026"
    link_direto_jitsi = f"https://meet.jit.si/{nome_sala_direta}#config.prejoinPageEnabled=false&config.disableDeepLinking=true&config.requireDisplayName=false"

    if st.button("🚀 Criar Sala e Enviar Convite", key="btn_ligar_integ"):
      remetente_notif = (
          usuario_atual["apelido"] if usuario_atual else "Administrador"
      )
      msg_alerta_chamada = f"🚨 **CHAMADA DE VÍDEO ATIVA:** {remetente_notif} iniciou uma reunião!\n\n🔗 **Clica para entrar:**\n{link_direto_jitsi}"
      data_env_notif = datetime.now().strftime("%H:%M — %d/%m")
      try:
        cursor.execute(
            "INSERT INTO chat_interno (remetente, destinatario, cargo,"
            " mensagem, arquivo_path, arquivo_nome, data_envio) VALUES (?, ?,"
            " ?, ?, ?, ?, ?)",
            (
                f"{remetente_notif} (Diretoria)",
                alvo_selecionado,
                "Alerta",
                msg_alerta_chamada,
                "",
                "",
                data_env_notif,
            ),
        )
        conn.commit()
      except Exception:
        pass
      st.success("Convite enviado com sucesso para o chat!")
      st.rerun()

elif menu == "🔍 Consulta / Busca Geral":
  st.title("🔍 Consulta e Histórico Completo")
  df_v_busca = pd.read_sql(
      "SELECT tag_prefixo, modelo, placa FROM veiculos", conn
  )
  if not df_v_busca.empty:
    exibir_tabela_padronizada(df_v_busca, "busca_eq_info")
  else:
    st.info("Nenhum registo encontrado para consulta.")

elif menu == "⚙️ Meu Perfil / Dados":
  st.title("⚙️ Meu Perfil & Credenciais Corporativas")
  if usuario_atual:
    st.info(f"Logado como: {usuario_atual['nome']} ({usuario_atual['cargo']})")

elif menu == "⚙️ Painel de Licença (Admin)" and modo_admin_liberado:
  st.title("⚙️ Painel Administrativo de Chaves & Licenças & Gestão de Colunas")
  
  tab_adm_l1, tab_adm_l2 = st.tabs(["🎟️ Gestão de Licenças", "⚙️ Gestão de Colunas (Ocultar)"])
  
  with tab_adm_l1:
    df_chaves = pd.read_sql("SELECT * FROM chaves_licenca", conn)
    if not df_chaves.empty:
      exibir_tabela_padronizada(df_chaves, "chaves_licenca")
    else:
      st.info("Nenhuma chave registada.")

  with tab_adm_l2:
    st.markdown("### ⚙️ Ocultar Colunas Indesejadas das Tabelas")
    tabela_escolhida_ocultar = st.selectbox("Selecione a Tabela:", ["veiculos", "manutencoes", "mobilizacoes", "combustivel", "pecas", "clientes"])
    try:
      df_ex_cols = pd.read_sql(f"SELECT * FROM {tabela_escolhida_ocultar} LIMIT 1", conn)
      todas_cols_tabela = list(df_ex_cols.columns)
    except Exception:
      todas_cols_tabela = []

    cursor.execute("SELECT ordem_colunas FROM config_colunas WHERE tabela = ?", (tabela_escolhida_ocultar,))
    res_oc = cursor.fetchone()
    cols_ja_ocultas = [c.strip() for c in res_oc[0].split(",")] if res_oc and res_oc[0] else []

    colunas_para_ocultar = st.multiselect(
        "Selecione as colunas que deseja ocultar nas tabelas:",
        todas_cols_tabela,
        default=[c for c in cols_ja_ocultas if c in todas_cols_tabela]
    )

    if st.button("💾 Salvar Configuração de Colunas"):
      str_ocultas_final = ",".join(colunas_para_ocultar)
      cursor.execute("INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas) VALUES (?, ?)", (tabela_escolhida_ocultar, str_ocultas_final))
      conn.commit()
      st.success("✅ Configuração de colunas atualizada com sucesso!")
      st.rerun()
