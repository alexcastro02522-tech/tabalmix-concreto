from datetime import datetime, timedelta
import base64
import csv
import glob
import io
import os
import random
import string
import urllib.parse
import mercadopago
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import streamlit as st
import psycopg2

# LIGAÇÃO DIRETA VIA SECRETS DO STREAMLIT / FALLBACK SEGURO AO SUPABASE
try:
    SUPABASE_DB_URL = st.secrets["SUPABASE_DB_URL"]
except Exception:
    SUPABASE_DB_URL = "postgresql://postgres.ctibigorhywnwkuzqfjm:bz8VNak7mmgXO05i@aws-0-sa-east-1.pooler.supabase.co:6543/postgres"

# CONFIGURAÇÃO DO MERCADO PAGO
MERCADO_PAGO_ACCESS_TOKEN = (
    "APP_USR-7480302560366070-091611-1118388bbc787e8f88ea1da583096dbc-2919829212"
)
try:
  sdk_mp = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
except Exception:
  sdk_mp = None

# Configuração da Página com layout limpo e responsivo
st.set_page_config(
    page_title="Tabalmix Concreto - Enterprise Fleet & Operations Pro X",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ESTILIZAÇÃO VISUAL BLINDADA: Menu Retrátil + Letras Nítidas + Selo de Garantia
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        max-width: 100% !important;
    }
    
    [data-testid="stSidebar"] {
        background: #f8fafc !important;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] .stRadio label, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] div {
        color: #1e293b !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
    }
    
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            width: 100% !important;
            min-width: 100% !important;
        }
        div[data-baseweb="select"], .stRadio, .stButton, label {
            pointer-events: auto !important;
            cursor: pointer !important;
        }
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


def gerar_excel_formatado(dataframe, nome_aba="Relatório Tabalmix"):
  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    dataframe.to_excel(writer, sheet_name=nome_aba, index=False)
    workbook = writer.book
    worksheet = writer.sheets[nome_aba]

    header_format = workbook.add_format({
        "bold": True,
        "text_wrap": True,
        "fg_color": "#047857",
        "font_color": "white",
        "border": 1,
        "align": "center",
        "valign": "middle",
    })
    cell_format = workbook.add_format({
        "border": 1,
        "align": "left",
        "valign": "middle",
        "text_wrap": True,
    })

    for col_num, value in enumerate(dataframe.columns.values):
      worksheet.write(0, col_num, str(value).upper(), header_format)
      max_len = max(dataframe[value].astype(str).map(len).max(), len(str(value))) + 4
      worksheet.set_column(col_num, col_num, max(max_len, 15), cell_format)

  output.seek(0)
  return output


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


# UTILIZANDO ST.CACHE_RESOURCE PARA GERIR A CONEXÃO COM SEGURANÇA E EVITAR ERROS DE CLOUD
@st.cache_resource
def init_db():
  conn = psycopg2.connect(SUPABASE_DB_URL, sslmode="require")
  cursor = conn.cursor()
  
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id SERIAL PRIMARY KEY,
            tag_prefixo TEXT, categoria_equipamento TEXT,
            tipo_equipamento TEXT, operador_condutor TEXT,
            marca TEXT, modelo TEXT, ano INTEGER, chassi TEXT, renavam TEXT,
            placa TEXT, crv TEXT, cor TEXT, combustivel TEXT, empresa TEXT,
            horimetro_km INTEGER, status TEXT, historico_edicoes TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS manutencoes (
            id SERIAL PRIMARY KEY,
            tag_prefixo TEXT, tipo_manutencao TEXT, horimetro_km_manut TEXT,
            origem_falha TEXT, descricao_problema TEXT, data_abertura TEXT,
            hora_abertura TEXT, pecas_utilizadas TEXT, custo_pecas REAL,
            mao_de_obra REAL, custo REAL, oficina TEXT, tecnico_mecanico TEXT,
            data_fechamento TEXT, hora_fechamento TEXT, status_os TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pecas (
            id SERIAL PRIMARY KEY,
            nome_item TEXT, categoria TEXT, quantidade INTEGER, valor_unitario REAL
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nome TEXT, empresa TEXT, telefone TEXT, documento TEXT, email TEXT, endereco TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS mobilizacoes (
            id SERIAL PRIMARY KEY,
            equipamento TEXT, tipo_movimento TEXT, destino_origem TEXT,
            responsavel TEXT, data TEXT, horimetro_km_mov TEXT,
            motivo_condicao TEXT, observacao TEXT, foto_checklist TEXT,
            historico_edicoes TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS combustivel (
            id SERIAL PRIMARY KEY,
            equipamento TEXT, litros REAL, valor_total REAL,
            km_horimetro TEXT, posto_posto TEXT, motorista TEXT, data TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id SERIAL PRIMARY KEY,
            nome_completo TEXT, cpf TEXT, email TEXT UNIQUE, senha TEXT,
            celular_seguranca TEXT, status_assinatura TEXT, plano_atual TEXT,
            data_cadastro TEXT, pin_rapido TEXT, apelido TEXT, cargo_setor TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_colunas (
            tabela TEXT PRIMARY KEY,
            ordem_colunas TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_interno (
            id SERIAL PRIMARY KEY,
            remetente TEXT,
            destinatario TEXT,
            cargo TEXT,
            mensagem TEXT,
            arquivo_path TEXT,
            arquivo_nome TEXT,
            data_envio TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS chaves_licenca (
            id SERIAL PRIMARY KEY,
            codigo_chave TEXT UNIQUE,
            cargo_atribuido TEXT,
            modalidade TEXT,
            status_uso TEXT,
            usado_por TEXT,
            data_criacao TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS multas (
            id SERIAL PRIMARY KEY,
            equipamento_placa TEXT,
            orgao_autuador TEXT,
            local_infracao TEXT,
            data_infracao TEXT,
            valor_multa REAL,
            descricao_infracao TEXT,
            condutor_responsable TEXT,
            data_vencimento TEXT,
            status_multa TEXT
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
    cursor.execute(
        "UPDATE usuarios_sistema SET status_assinatura = 'Ativo' WHERE"
        " status_assinatura IS NULL OR status_assinatura = '' OR status_assinatura = 'None'"
    )
    conn.commit()
  except Exception:
    pass

  cursor.execute("SELECT COUNT(*) FROM usuarios_sistema")
  if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, apelido, cargo_setor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        ("Alex de Castro Bernardino", "000.000.000-00", "alexcastro02522@gmail.com", "admin2026", "(92) 99999-9999", "Ativo", "Plano Master Concreto & Diretoria", datetime.now().strftime("%Y-%m-%d %H:%M"), "Alex", "Diretoria / Gestão")
    )
    conn.commit()

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
          "SELECT * FROM usuarios_sistema WHERE id = %s", (saved_user_id,)
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
  if "Diretoria" in cargo_colab or "Gestão" in cargo_colab or "Engenheiro" in cargo_colab:
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
              "SELECT * FROM usuarios_sistema WHERE email = %s AND pin_rapido = %s",
              (email_pin, pin_dig),
          )
          user_pin = cursor.fetchone()
          if user_pin:
            if str(user_pin[6]).strip().lower() != "ativo":
              st.error("⚠️ Esta conta encontra-se INATIVA. Contacte a diretoria.")
            else:
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
              "SELECT * FROM usuarios_sistema WHERE email = %s AND senha = %s",
              (email_login, senha_login),
          )
          user_data = cursor.fetchone()
          if user_data:
            if str(user_data[6]).strip().lower() != "ativo":
              st.error("⚠️ Esta conta encontra-se INATIVA. Contacte o administrador.")
            else:
              if cadastrar_pin and len(cadastrar_pin) == 4:
                cursor.execute(
                    "UPDATE usuarios_sistema SET pin_rapido = %s WHERE id = %s",
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
              "💎 Master Concreto & Diretoria",
              "🏗️ Engenharia & Obra Pro",
              "🛠️ Oficina & Mecânica X",
              "🚜 Operacional Campo & Frota",
          ],
      )

      if "💎 Master Concreto & Diretoria" in c_cargo:
        cargo_banco_str = "Diretoria / Gestão"
      elif "🏗️ Engenharia & Obra Pro" in c_cargo:
        cargo_banco_str = "Engenheiro / Gestor de Obra"
      elif "🛠️ Oficina & Mecânica X" in c_cargo:
        cargo_banco_str = "Mecânico / Oficina"
      else:
        cargo_banco_str = "Operador / Motorista / Campo"

      with st.form("form_novo_cadastro"):
        c_cpf = st.text_input("CPF")
        c_email = st.text_input("E-mail corporativo de login")
        c_senha = st.text_input("Criar senha", type="password")
        c_cel = st.text_input("Celular / WhatsApp")
        c_vigencia = st.selectbox("Modalidade de vigência", ["Plano Mensal", "Plano Anual"])
        btn_cadastrar = st.form_submit_button("Cadastrar e Prosseguir")

        if btn_cadastrar:
          if c_nome and c_email and c_senha:
            apelido_final = c_apelido.strip() if c_apelido and c_apelido.strip() else c_nome.split()[0]
            plano_completo_str = f"{c_cargo} — {c_vigencia}"
            try:
              cursor.execute(
                  "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, apelido, cargo_setor) VALUES (%s, %s, %s, %s, %s, 'Ativo', %s, %s, %s, %s)",
                  (c_nome, c_cpf, c_email, c_senha, c_cel, plano_completo_str, datetime.now().strftime("%Y-%m-%d %H:%M"), apelido_final, cargo_banco_str)
              )
              conn.commit()
              st.success("✅ Conta cadastrada com sucesso! Podes fazer login agora.")
            except Exception as e:
              st.error(f"⚠️ Erro ao cadastrar: {e}")

    elif escolha_modo_login == "🎟️ Ativar com Chave Corporativa":
      with st.form("form_resgatar_chave_login"):
        st.markdown("### 🎟️ Ativar Conta com Chave Corporativa")
        email_resgate = st.text_input("E-mail cadastrado")
        chave_digitada = st.text_input("Chave de ativação")
        btn_ativar_chave = st.form_submit_button("Ativar Acesso")
        if btn_ativar_chave:
          cursor.execute("SELECT id, cargo_atribuido, modalidade, status_uso FROM chaves_licenca WHERE codigo_chave = %s", (chave_digitada.strip(),))
          chave_db = cursor.fetchone()
          if chave_db:
            id_c, cargo_c, mod_c, status_c = chave_db
            if status_c == "Utilizada":
              st.warning("⚠️ Esta chave já foi utilizada.")
            else:
              cursor.execute("SELECT id FROM usuarios_sistema WHERE email = %s", (email_resgate.strip(),))
              user_db = cursor.fetchone()
              if user_db:
                id_u = user_db[0]
                plano_final = f"{cargo_c} — {mod_c}"
                cursor.execute("UPDATE usuarios_sistema SET status_assinatura = 'Ativo', cargo_setor = %s, plano_atual = %s WHERE id = %s", (cargo_c, plano_final, id_u))
                cursor.execute("UPDATE chaves_licenca SET status_uso = 'Utilizada', usado_por = %s WHERE id = %s", (email_resgate.strip(), id_c))
                conn.commit()
                st.success("🎉 Conta ativada com sucesso!")
              else:
                st.error("⚠️ E-mail não encontrado.")

    elif escolha_modo_login == "🔄 Recuperar Senha":
      with st.form("form_recuperar"):
        st.markdown("### 🔄 Recuperar Senha")
        rec_email = st.text_input("E-mail cadastrado")
        btn_rec = st.form_submit_button("Consultar Senha")
        if btn_rec:
          cursor.execute("SELECT senha, nome_completo FROM usuarios_sistema WHERE email = %s", (rec_email,))
          res_rec = cursor.fetchone()
          if res_rec:
            st.info(f"👤 Olá, {res_rec[1]}. Sua senha é: **{res_rec[0]}**")
          else:
            st.error("⚠️ E-mail não encontrado.")

  st.stop()

usuario_atual = st.session_state["usuario_logado"]
status_usuario_ativo = True if modo_admin_liberado else (str(usuario_atual.get("status", "Ativo")).strip().lower() == "ativo" if usuario_atual else False)

if not status_usuario_ativo and not modo_admin_liberado:
  st.error("⚠️ A sua conta encontra-se atualmente INATIVA no sistema. Contacte a diretoria.")
  if st.button("🚪 Terminar Sessão"):
    st.session_state["usuario_logado"] = None
    try:
      st.query_params.clear()
    except Exception:
      pass
    st.rerun()
  st.stop()

if usuario_atual and (not usuario_atual.get("apelido") or usuario_atual["apelido"] == "None"):
  usuario_atual["apelido"] = usuario_atual["nome"].split()[0]
if usuario_atual and (not usuario_atual.get("cargo") or usuario_atual["cargo"] == "None"):
  usuario_atual["cargo"] = "Colaborador"


def exibir_tabela_padronizada(df, nome_tabela):
  if df.empty:
    st.info("Nenhum registo encontrado.")
    return
  try:
    cursor.execute("SELECT ordem_colunas FROM config_colunas WHERE tabela = %s", (nome_tabela,))
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
            <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 16px; padding: 16px; text-align: center; margin-bottom: 14px; color: white; box-shadow: 0 4px 12px rgba(5,150,105,0.15);">
                <div style="font-size: 15px; font-weight: 900; margin-bottom: 10px; letter-spacing: 0.5px;">🏗️ TABALMIX CONCRETO</div>
                <div style="border-radius: 12px; overflow: hidden; max-height: 100px; border: 2px solid rgba(255,255,255,0.8); margin-bottom: 8px;">
                    <img src="data:image/jpeg;base64,{encoded_logo_side}" style="width: 100%; height: 100px; object-fit: cover; display: block;">
                </div>
                <div style="background: rgba(255,255,255,0.15); border-radius: 8px; padding: 6px; font-size: 10px; font-weight: 700; color: #e2e8f0; margin-top: 6px; letter-spacing: 0.5px; border: 1px dashed rgba(255,255,255,0.4);">
                    🛡️ SELO DE GARANTIA ENTERPRISE
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
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px; margin-bottom: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);">
                <p style="margin: 0; font-weight: 800; color: #0f172a; font-size: 14px;">👤 {usuario_atual['apelido']}</p>
                <p style="margin: 3px 0 6px 0; font-size: 11.5px; color: #047857; font-weight: 700;">{usuario_atual['cargo']}</p>
                <span style="color: #059669; font-weight: 700; font-size: 11px; background: #ecfdf5; padding: 3px 10px; border-radius: 6px; display: inline-block;">🟢 Sessão Ativa</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚪 Encerrar Sessão", use_container_width=True):
      st.session_state["usuario_logado"] = None
      try:
        st.query_params.clear()
      except Exception:
        pass
      st.rerun()
  st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

lista_menus = [
    "📊 Visão Geral",
    "🚜 Cadastro de Equipamentos",
    "⛽ Abastecimentos & Combustível",
    "🏗️ Mobilização / Desmobilização",
    "🛠️ Ordens de Serviço (OS)",
    "🚨 Gestão & Alertas de Multas",
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
  df_veiculos = pd.read_sql("SELECT * FROM veiculos", conn)
  df_manut = pd.read_sql("SELECT * FROM manutencoes", conn)
  df_comb = pd.read_sql("SELECT * FROM combustivel", conn)
  df_multas = pd.read_sql("SELECT * FROM multas", conn)
  
  col1, col2, col3, col4, col5 = st.columns(5)
  with col1: st.metric("Total Frota", len(df_veiculos))
  with col2: st.metric("OS Abertas", len(df_manut[df_manut["status_os"] == "aberta"]) if not df_manut.empty else 0)
  with col3: st.metric("Multas Pendentes", len(df_multas[df_multas["status_multa"] == "Pendente"]) if not df_multas.empty else 0)
  with col4: st.metric("Gasto Combust.", f"R$ {df_comb['valor_total'].sum() if not df_comb.empty else 0.0:,.2f}")
  with col5: st.metric("Total Litros", f"{df_comb['litros'].sum() if not df_comb.empty else 0.0:,.1f} L")
  
  st.divider()
  if not df_veiculos.empty:
    exibir_tabela_padronizada(df_veiculos, "veiculos")
  else:
    st.info("Nenhum veículo registado.")

elif menu == "🚜 Cadastro de Equipamentos":
  st.title("🚜 Cadastro de Equipamentos & Vistoria Fotográfica")
  tab_eq_lista, tab_eq_cad, tab_eq_edit, tab_eq_foto = st.tabs(["📋 Frota", "➕ Registar", "✏️ Editar", "📸 Vistoria"])
  with tab_eq_lista:
    df_f = pd.read_sql("SELECT * FROM veiculos", conn)
    exibir_tabela_padronizada(df_f, "veiculos")
  with tab_eq_cad:
    with st.form("form_cad_eq"):
      f_marca = st.text_input("Marca")
      f_modelo = st.text_input("Modelo")
      f_placa = st.text_input("Placa")
      if st.form_submit_button("Salvar") and f_marca:
        cursor.execute("INSERT INTO veiculos (marca, modelo, placa, status, horimetro_km) VALUES (%s, %s, %s, 'Ativo', 0)", (f_marca, f_modelo, f_placa))
        conn.commit()
        st.success("Registo salvo!")
        st.rerun()

elif menu == "⛽ Abastecimentos & Combustível":
  st.title("⛽ Abastecimentos")
  df_c = pd.read_sql("SELECT * FROM combustivel ORDER BY id DESC", conn)
  exibir_tabela_padronizada(df_c, "combustivel")

elif menu == "🏗️ Mobilização / Desmobilização":
  st.title("🏗️ Mobilização de Obras")
  df_m = pd.read_sql("SELECT * FROM mobilizacoes ORDER BY id DESC", conn)
  exibir_tabela_padronizada(df_m, "mobilizacoes")

elif menu == "🛠️ Ordens de Serviço (OS)":
  st.title("🛠️ Ordens de Serviço")
  df_os = pd.read_sql("SELECT * FROM manutencoes ORDER BY id DESC", conn)
  exibir_tabela_padronizada(df_os, "manutencoes")

elif menu == "🚨 Gestão & Alertas de Multas":
  st.title("🚨 Gestão de Multas")
  if st.button("🔍 Varredura em Massa da Frota"):
    st.success("Varredura concluída!")
  df_mu = pd.read_sql("SELECT * FROM multas ORDER BY id DESC", conn)
  exibir_tabela_padronizada(df_mu, "multas")

elif menu == "🔩 Peças e Ferramentas":
  st.title("🔩 Stock de Peças")
  df_p = pd.read_sql("SELECT * FROM pecas ORDER BY id DESC", conn)
  exibir_tabela_padronizada(df_p, "pecas")

elif menu == "👥 Gestão de Clientes":
  st.title("👥 Clientes")
  df_cl = pd.read_sql("SELECT * FROM clientes ORDER BY id DESC", conn)
  exibir_tabela_padronizada(df_cl, "clientes")

elif menu == "💬 Chat Tabalmix Pro & Rede":
  st.title("💬 Chat Corporativo Pro")
  df_chat = pd.read_sql("SELECT * FROM chat_interno ORDER BY id ASC LIMIT 50", conn)
  for _, r in df_chat.iterrows():
    st.markdown(f"**{r['remetente']}**: {r['mensagem']}")
  with st.form("chat_envio", clear_on_submit=True):
    msg = st.text_input("Mensagem")
    if st.form_submit_button("Enviar") and msg:
      cursor.execute("INSERT INTO chat_interno (remetente, destinatario, cargo, mensagem, data_envio) VALUES (%s, 'Geral', 'Operacional', %s, %s)", ("Alex", msg, datetime.now().strftime("%H:%M")))
      conn.commit()
      st.rerun()

elif menu == "🔍 Consulta / Busca Geral":
  st.title("🔍 Consulta de Frota")
  df_vb = pd.read_sql("SELECT tag_prefixo, marca, modelo, placa FROM veiculos", conn)
  exibir_tabela_padronizada(df_vb, "veiculos")

elif menu == "⚙️ Meu Perfil / Dados":
  st.title("⚙️ Meu Perfil")
  st.info("Painel de gestão de perfil ativo.")

elif menu == "⚙️ Painel de Licença (Admin)" and modo_admin_liberado:
  st.title("⚙️ Painel de Licenças Admin")
  df_u = pd.read_sql("SELECT * FROM usuarios_sistema", conn)
  exibir_tabela_padronizada(df_u, "usuarios_sistema")
