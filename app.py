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

  tab_cad_mob,
