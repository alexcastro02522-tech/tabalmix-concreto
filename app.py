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

# ESTILIZAÇÃO VISUAL PREMIUM ENTERPRISE ORIGINAL
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
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 5px solid #059669 !important;
        padding: 18px !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04);
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

# CHAVE SECRETA DE ADMINISTRADOR
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

# PERSISTÊNCIA INTELIGENTE DE SESSÃO NA OBRA
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
                    <div style="display: inline-block; background: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.4); border-radius: 16px; padding: 3px 14px; margin-bottom: 10px;">
                        <span style="color: white; font-size: 10.5px; font-weight: 800; letter-spacing: 1.2px;">🛡️ PLATAFORMA ENTERPRISE CERTIFICADA</span>
                    </div>
                    <h1 style="color: white !important; margin: 0; font-size: 24px; font-weight: 900; letter-spacing: -0.5px;">tabalmix concreto</h1>
                    <p style="color: #e2e8f0; font-size: 11.5px; margin: 4px 0 2px 0; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">sistema inteligente de frotas e obras</p>
                    <p style="color: #cbd5e1; font-size: 9.5px; margin: 0; font-style: italic;">powered by castro tech</p>
                </div>
            """,
          unsafe_allow_html=True,
      )
    except Exception:
      st.markdown(
          """
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 20px 40px rgba(5,150,105,0.2); margin-top: 10px; margin-bottom: 20px; color: white;">
                    <div style="display: inline-block; background: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.4); border-radius: 16px; padding: 3px 14px; margin-bottom: 10px;">
                        <span style="color: white; font-size: 10.5px; font-weight: 800; letter-spacing: 1.2px;">🛡️ PLATAFORMA ENTERPRISE CERTIFICADA</span>
                    </div>
                    <h1 style="color: white !important; margin: 0; font-size: 24px; font-weight: 900; letter-spacing: -0.5px;">tabalmix concreto</h1>
                    <p style="color: #e2e8f0; font-size: 11.5px; margin: 4px 0 2px 0; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">sistema inteligente de frotas e obras</p>
                    <p style="color: #cbd5e1; font-size: 9.5px; margin: 0; font-style: italic;">powered by castro tech</p>
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

      if "Diretoria" in c_cargo:
        sugestao_preco = (
            "💎 Master Concreto & Diretoria — Mensal: R$ 299,90 | Anual: R$"
            " 2.999,00"
        )
        valor_num = 299.90
      elif "Engenheiro" in c_cargo:
        sugestao_preco = (
            "🏗️ Engenharia & Obra Pro — Mensal: R$ 189,90 | Anual: R$ 1.899,00"
        )
        valor_num = 189.90
      elif "Mecânico" in c_cargo:
        sugestao_preco = (
            "🛠️ Oficina & Mecânica X — Mensal: R$ 119,90 | Anual: R$ 1.199,00"
        )
        valor_num = 119.90
      else:
        sugestao_preco = (
            "🚜 Operacional Campo & Frota — Mensal: R$ 69,90 | Anual: R$ 699,00"
        )
        valor_num = 69.90

      st.info(f"💡 **Plano Sugerido:**\n\n{sugestao_preco}")

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
              st.success(
                  "✅ Conta cadastrada com sucesso! Podes efetuar o pagamento"
                  " abaixo ou inserir uma chave de ativação."
              )
            except Exception as e:
              st.error(f"⚠️ Erro ao cadastrar (e-mail já cadastrado?): {e}")
          else:
            st.error("⚠️ Preencha os campos obrigatórios.")

      st.markdown("---")
      st.markdown("### 💳 Pagamento Automático (Mercado Pago)")
      if st.button("Gerar Link de Pagamento Mercado Pago"):
        if sdk_mp:
          try:
            preference_data = {
                "items": [{
                    "title": "Assinatura Tabalmix Concreto",
                    "quantity": 1,
                    "unit_price": float(
                        valor_num if "valor_num" in locals() else 69.90
                    ),
                }],
                "back_urls": {
                    "success": "https://tabalmix-concreto.streamlit.app/",
                    "failure": "https://tabalmix-concreto.streamlit.app/",
                },
            }
            preference_response = sdk_mp.preference().create(preference_data)
            link_pagamento = preference_response["response"].get(
                "init_point", "#"
            )
            st.markdown(
                f"🔗 **[Clique aqui para abrir o checkout seguro do Mercado"
                f" Pago]({link_pagamento})**",
                unsafe_allow_html=True,
            )
          except Exception as ex:
            st.error(
                f"⚠️ Erro ao gerar link de pagamento: {ex}. Podes usar uma"
                " chave de ativação."
            )
        else:
          st.error("⚠️ SDK do Mercado Pago não configurado.")

    elif escolha_modo_login == "🎟️ Ativar com Chave Corporativa":
      with st.form("form_resgatar_chave_login"):
        st.markdown("### 🎟️ Ativar Conta com Chave Corporativa")
        email_resgate = st.text_input("E-mail cadastrado na conta")
        chave_digitada = st.text_input(
            "Chave de ativação (ex: TABALMIX-XXXX-XXXX)"
        )
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
              st.warning("⚠️ Esta chave já foi utilizada por outro usuário.")
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
                st.success(
                    "🎉 **Parabéns! Sua conta foi ativada com sucesso.**"
                    " Altera no menu para 'Entrar' e faz login."
                )
              else:
                st.error("⚠️ E-mail não encontrado no sistema.")
          else:
            st.error("⚠️ Chave de ativação inválida.")

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
            st.info(
                f"👤 Olá, {res_rec[1]}. Sua senha cadastrada é: **{res_rec[0]}**"
            )
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

# VERIFICAÇÃO GLOBAL DE CHAMADA PENDENTE COM AUTO-REFRESH EM TEMPO REAL NO SMARTPHONE DELA
if usuario_atual:
  nome_apelido_atual = usuario_atual["apelido"]
  cursor.execute(
      "SELECT mensagem, data_envio FROM chat_interno WHERE destinatario LIKE ? AND mensagem LIKE '%CHAMADA DE VÍDEO ATIVA%' ORDER BY id DESC LIMIT 1",
      (f"%{nome_apelido_atual}%",),
  )
  chamada_pendente = cursor.fetchone()
  if chamada_pendente:
    st.markdown(
        f"""
            <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 18px 24px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 15px 35px rgba(220,38,38,0.5); display: flex; justify-content: space-between; align-items: center; animation: pulse 1s infinite;">
                <div>
                    <h3 style="color: white !important; margin: 0; font-size: 18px;">🚨 CHAMADA DE VÍDEO A TOCAR AGORA!</h3>
                    <p style="margin: 4px 0 0 0; font-size: 14px;">Alguém está a chamar-te em tempo real para uma reunião ao vivo.</p>
                </div>
                <a href="?p=chat" target="_self" style="background: white; color: #991b1b; padding: 12px 24px; border-radius: 12px; font-weight: 800; text-decoration: none; font-size: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">ATENDER CHAMADA</a>
            </div>
            <script>
                // Força o smartphone dela a atualizar a página automaticamente a cada 4 segundos para tocar na hora
                setTimeout(function(){
                    window.location.reload();
                }, 4000);
            </script>
        """,
        unsafe_allow_html=True,
    )


def exibir_tabela_padronizada(df, nome_tabela):
  if df.empty:
    st.info("Nenhum registro encontrado.")
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
    if cols_finais:
      df = df[cols_finais]

  if is_gestao_ou_admin:
    with st.expander(
        f"⚙️ [DIRETORIA] Gerir Colunas e Registos ({nome_tabela})", expanded=False
    ):
      colunas_selecionadas_pelo_admin = st.multiselect(
          "Colunas ativas:",
          options=cols_atuais,
          default=(
              cols_finais
              if "cols_finais" in locals() and cols_finais
              else cols_atuais
          ),
          key=f"sel_cols_diretoria_{nome_tabela}",
      )
      if st.button(
          "💾 Salvar Colunas", key=f"btn_salvar_cols_{nome_tabela}"
      ):
        if colunas_selecionadas_pelo_admin:
          ordem_str = ",".join(colunas_selecionadas_pelo_admin)
          cursor.execute(
              "INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas)"
              " VALUES (?, ?)",
              (nome_tabela, ordem_str),
          )
          conn.commit()
          st.success("✅ Configuração de colunas salva com sucesso!")
          st.rerun()
        else:
          st.warning("⚠️ Selecione pelo menos uma coluna.")

      if "id" in df.columns:
        st.markdown("---")
        id_para_excluir = st.selectbox(
            "Seleciona o ID exato para excluir:",
            df["id"].tolist(),
            key=f"sel_exc_diretoria_{nome_tabela}",
        )
        if st.button(
            "🗑️ Excluir Registo Selecionado",
            key=f"btn_exc_diretoria_{nome_tabela}",
        ):
          tabela_sql = (
              "veiculos"
              if "veiculo" in nome_tabela.lower() or nome_tabela == "veiculos"
              else (
                  "manutencoes"
                  if "manutencao" in nome_tabela.lower()
                  else (
                      "mobilizacoes"
                      if "mobilizacao" in nome_tabela.lower()
                      else (
                          "combustivel"
                          if "combustivel" in nome_tabela.lower()
                          else (
                              "pecas"
                              if "peca" in nome_tabela.lower()
                              else (
                                  "clientes"
                                  if "cliente" in nome_tabela.lower()
                                  else ""
                              )
                          )
                      )
                  )
              )
          )
          if tabela_sql:
            cursor.execute(
                f"DELETE FROM {tabela_sql} WHERE id = ?", (id_para_excluir,)
            )
            conn.commit()
            st.success("✅ Registo excluído com sucesso!")
            st.rerun()

  st.dataframe(df, use_container_width=True, hide_index=True, column_config={})


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
    st.success("🔓 **Modo Admin Enterprise Ativo**")
  elif usuario_atual:
    st.markdown(
        f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                <p style="margin: 0; font-weight: bold; color: #0f172a; font-size: 14px;">👤 {usuario_atual['apelido']}</p>
                <p style="margin: 3px 0 4px 0; font-size: 11.5px; color: #047857; font-weight: 700;">{usuario_atual['cargo']}</p>
                <span style="color: #059669; font-weight: bold; font-size: 11px; background: #ecfdf5; padding: 2px 8px; border-radius: 6px; display: inline-block;">🟢 Sessão Ativa</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if not status_usuario_ativo:
      st.warning(
          "⚠️ **Conta Inativa:** insira uma chave de ativação válida ou efetue"
          " o pagamento."
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
    st.metric("Total Frota", total_frota)
  with col2:
    st.metric("OS Abertas", os_abertas)
  with col3:
    st.metric("Custo Manut.", f"R$ {custo_total_manut:,.2f}")
  with col4:
    st.metric("Gasto Combust.", f"R$ {gasto_total_comb:,.2f}")
  with col5:
    st.metric("Total Litros", f"{litros_totais:,.1f} L")

  st.divider()

  col_exp1, col_exp2 = st.columns([3, 1])
  with col_exp1:
    st.subheader("📋 Listagem Geral de Equipamentos")
  with col_exp2:
    if not df_veiculos.empty and (status_usuario_ativo or modo_admin_liberado):
      pdf_buf = gerar_pdf_relatorio(
          "Relatório Consolidado da Frota - Tabalmix", df_veiculos
      )
      st.download_button(
          "📥 Exportar Relatório PDF",
          pdf_buf,
          file_name="relatorio_frota.pdf",
          mime="application/pdf",
      )

  if not df_veiculos.empty:
    exibir_tabela_padronizada(df_veiculos, "veiculos")
  else:
    st.info("Nenhum equipamento cadastrado na frota.")

elif menu == "🚜 Cadastro de Equipamentos":
  st.title("🚜 Cadastro de Equipamentos e Frota")
  with st.form("form_frota", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
      tag_prefixo = st.text_input("Tag / Prefixo (ex: EQ-001 / BET-12)")
      categoria_equipamento = st.text_input("Categoria do equipamento")
      marca = st.text_input("Marca")
      modelo = st.text_input("Modelo")
      ano = st.number_input(
          "Ano de fabricação", min_value=1950, value=2024, step=1
      )
      chassi = st.text_input("Número do chassi")
      renavam = st.text_input("Número do renavam")
    with col2:
      placa = st.text_input("Placa do veículo")
      crv = st.text_input("Número do CRV")
      cor = st.text_input("Cor principal")
      combustivel = st.selectbox(
          "Tipo de combustível",
          ["Diesel S10", "Diesel S500", "Gasolina", "Flex", "Elétrico"],
      )
      empresa = st.text_input("Empresa / filial responsável")
      horimetro_km = st.number_input(
          "Horímetro ou KM inicial", min_value=0, value=15000, step=100
      )
      status = st.selectbox(
          "Situação operacional",
          ["Ativo", "Em Manutenção", "Parado", "Mobilizado"],
      )

    btn_cad_eq = st.form_submit_button("Cadastrar Equipamento")
    if btn_cad_eq and modelo:
      tag_final = (
          tag_prefixo.upper()
          if tag_prefixo and tag_prefixo.strip()
          else "EQ-00" + str(datetime.now().microsecond)[:3]
      )
      cursor.execute(
          "INSERT INTO veiculos (tag_prefixo, categoria_equipamento, marca,"
          " modelo, ano, chassi, renavam, placa, crv, cor, combustivel,"
          " empresa, horimetro_km, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,"
          " ?, ?, ?, ?, ?)",
          (
              tag_final,
              categoria_equipamento,
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
              int(horimetro_km),
              status,
          ),
      )
      conn.commit()
      st.success(f"✅ Equipamento '{tag_final}' cadastrado com sucesso!")
      st.rerun()

  df_f = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_f.empty:
    exibir_tabela_padronizada(df_f, "veiculos")

elif menu == "⛽ Abastecimentos & Combustível":
  st.title("⛽ Controle de Abastecimento e Combustível")
  df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  tags_comb = (
      df_v["tag_prefixo"].dropna().tolist() if not df_v.empty else []
  )
  with st.form("form_comb"):
    c1, c2 = st.columns(2)
    with c1:
      eq_comb = st.selectbox(
          "Equipamento / Tag", tags_comb if tags_comb else ["MANUAL"]
      )
      litros = st.number_input("Litros", min_value=0.1, value=100.0)
      val_tot = st.number_input("Valor total (R$)", min_value=0.0, value=600.0)
    with c2:
      km_h = st.text_input("KM ou Horímetro")
      posto = st.text_input("Posto / Fornecedor")
      motorista = st.text_input("Motorista / Responsável")
      dt_ab = st.date_input("Data")
    btn_cad_comb = st.form_submit_button("Registrar Abastecimento")
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
      st.success("✅ Abastecimento registrado!")
      st.rerun()

  df_c = pd.read_sql("SELECT * FROM combustivel", conn)
  if not df_c.empty:
    exibir_tabela_padronizada(df_c, "combustivel")

elif menu == "🏗️ Mobilização / Desmobilização":
  st.title("🏗️ Mobilização e Desmobilização de Obras")
  with st.form("form_mob"):
    c1, c2 = st.columns(2)
    with c1:
      eq_mob = st.text_input("Equipamento / Tag (ex: EQ-001)")
      tipo_mov = st.selectbox(
          "Movimentação",
          [
              "Mobilização (Envio)",
              "Desmobilização (Retorno)",
              "Remanejamento",
          ],
      )
      destino = st.text_input("Obra / Destino-Origem")
    with c2:
      resp = st.text_input("Responsável / Motorista")
      dt_mob = st.date_input("Data")
      obs = st.text_input("Observação")

    fotos_subidas = st.file_uploader(
        "📷 Anexar fotos do check-list",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    btn_cad_mob = st.form_submit_button("Registrar Movimentação")
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
      hist_inicial = (
          f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Criado por"
          f" {resp} — Destino: {destino}"
      )
      cursor.execute(
          "INSERT INTO mobilizacoes (equipamento, tipo_movimento,"
          " destino_origem, responsavel, data, observacao, foto_checklist,"
          " historico_edicoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
          (
              str(eq_mob).upper(),
              tipo_mov,
              destino,
              resp,
              str(dt_mob),
              obs,
              paths_str,
              hist_inicial,
          ),
      )
      conn.commit()
      st.success("✅ Movimentação registrada!")
      st.rerun()

  df_mobs = pd.read_sql("SELECT * FROM mobilizacoes", conn)
  if not df_mobs.empty:
    exibir_tabela_padronizada(df_mobs, "mobilizacoes")

elif menu == "🛠️ Ordens de Serviço (OS)":
  st.title("🛠️ Gestão Unificada de Ordens de Serviço (OS)")
  df_v = pd.read_sql("SELECT tag_prefixo FROM veiculos", conn)
  tags_disponiveis = (
      df_v["tag_prefixo"].dropna().tolist() if not df_v.empty else []
  )

  st.markdown("### 🟢 Abertura de Nova OS")
  with st.form("form_abertura_os", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
      tag_os = st.selectbox(
          "Tag / Prefixo", tags_disponiveis if tags_disponiveis else ["GERAL"]
      )
      tipo_manut = st.selectbox(
          "Tipo", ["Preventiva", "Corretiva", "Preditiva", "Revisão Geral"]
      )
      horimetro_ab = st.text_input("Horímetro / KM")
      origem_f = st.selectbox("Origem", ["Operação", "Máquina"])
    with c2:
      data_ab = st.date_input("Data", value=datetime.now().date())
      hora_ab = st.text_input("Hora", value=datetime.now().strftime("%H:%M"))
      desc_prob = st.text_area("Descrição do problema")

    btn_abrir_os = st.form_submit_button("Abrir Nova OS")
    if btn_abrir_os:
      cursor.execute(
          "INSERT INTO manutencoes (tag_prefixo, tipo_manutencao,"
          " horimetro_km_manut, origem_falha, descricao_problema,"
          " data_abertura, hora_abertura, status_os, custo, custo_pecas,"
          " mao_de_obra) VALUES (?, ?, ?, ?, ?, ?, ?, 'aberta', 0.0, 0.0,"
          " 0.0)",
          (
              str(tag_os).upper(),
              tipo_manut,
              horimetro_ab,
              origem_f,
              desc_prob,
              str(data_ab),
              hora_ab,
          ),
      )
      conn.commit()
      st.success("✅ OS aberta com sucesso!")
      st.rerun()

  df_os = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_os.empty:
    exibir_tabela_padronizada(df_os, "manutencoes")

elif menu == "🔩 Peças e Ferramentas":
  st.title("🔩 Controle de Peças e Ferramentas")
  with st.form("form_pecas"):
    c1, c2 = st.columns(2)
    with c1:
      nome_i = st.text_input("Nome da peça")
      cat = st.text_input("Categoria")
    with c2:
      qtd = st.number_input("Quantidade", min_value=1, value=1)
      v_unit = st.number_input("Valor unitário (R$)", min_value=0.0)
    btn_cad_peca = st.form_submit_button("Adicionar Peça")
    if btn_cad_peca:
      cursor.execute(
          "INSERT INTO pecas (nome_item, categoria, quantidade,"
          " valor_unitario) VALUES (?, ?, ?, ?)",
          (nome_i, cat.strip() if cat else "Geral", qtd, v_unit),
      )
      conn.commit()
      st.success("✅ Peça adicionada!")
      st.rerun()

  df_p = pd.read_sql("SELECT * FROM pecas", conn)
  if not df_p.empty:
    exibir_tabela_padronizada(df_p, "pecas")

elif menu == "👥 Gestão de Clientes":
  st.title("👥 Gestão de Clientes")
  with st.form("form_cli"):
    c1, c2 = st.columns(2)
    with c1:
      nome_c = st.text_input("Nome / Razão Social")
      emp = st.text_input("Empresa")
      tel = st.text_input("Telefone")
    with c2:
      doc = st.text_input("CPF / CNPJ")
      em = st.text_input("E-mail")
      end = st.text_input("Endereço")
    btn_cad_cli = st.form_submit_button("Salvar Cliente")
    if btn_cad_cli:
      cursor.execute(
          "INSERT INTO clientes (nome, empresa, telefone, documento, email,"
          " endereco) VALUES (?, ?, ?, ?, ?, ?)",
          (nome_c, emp, tel, doc, em, end),
      )
      conn.commit()
      st.success("✅ Cliente salvo!")
      st.rerun()

  df_cli = pd.read_sql("SELECT * FROM clientes", conn)
  if not df_cli.empty:
    exibir_tabela_padronizada(df_cli, "clientes")

elif menu == "💬 Chat Tabalmix Pro & Rede":
  st.markdown(
      """
        <style>
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 520px;
            overflow-y: auto;
            padding: 16px;
            background: #f8fafc;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
        }
        .msg-card-eu {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: white;
            padding: 14px 18px;
            border-radius: 16px 16px 4px 16px;
            max-width: 75%;
            align-self: flex-end;
            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.15);
            margin-left: auto;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        .msg-card-outro {
            background: #ffffff;
            color: #0f172a;
            padding: 14px 18px;
            border-radius: 16px 16px 16px 4px;
            max-width: 75%;
            align-self: flex-start;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
            margin-right: auto;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

  st.title("💬 Central Pro Enterprise — Chat & Live Ops")
  st.markdown(
      "Comunicação em tempo real de nível mundial entre a obra, mecânica e"
      " diretoria."
  )

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
            "Canal / Destinatário:",
            ["🌐 Canal Geral (Toda a Equipe)"] + opcoes_colab,
        )
      else:
        colab_escolhido_str = "🌐 Canal Geral (Toda a Equipe)"
    with col_f2:
      termo_busca_chat = st.text_input(
          "🔍 Pesquisa Global", placeholder="Ex: pneu, beta..."
      )

    if termo_busca_chat.strip():
      df_msgs = pd.read_sql(
          "SELECT * FROM chat_interno WHERE mensagem LIKE ? ORDER BY id ASC LIMIT"
          " 50",
          conn,
          params=(f"%{termo_busca_chat}%",),
      )
    else:
      df_msgs = pd.read_sql(
          "SELECT * FROM chat_interno ORDER BY id ASC LIMIT 50", conn
      )

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    remetente_atual = (
        usuario_atual["apelido"] if usuario_atual else "Administrador Master"
    )
    cargo_atual = (
        usuario_atual["cargo"] if usuario_atual else "Diretoria / Gestão"
    )

    if not df_msgs.empty:
      for _, row_m in df_msgs.iterrows():
        is_eu = remetente_atual in str(row_m["remetente"])
        estilo_classe = "msg-card-eu" if is_eu else "msg-card-outro"
        cor_autor = "#d1fae5" if is_eu else "#047857"

        st.markdown(
            f"""
                    <div class="{estilo_classe}">
                        <div style="font-size: 11px; font-weight: 800; color: {cor_autor}; margin-bottom: 4px; display: flex; justify-content: space-between; gap: 15px;">
                            <span>👤 {row_m['remetente']} ➔ {row_m['destinatario']}</span>
                            <span style="opacity: 0.8; font-weight: 500;">{row_m['data_envio']}</span>
                        </div>
                        <div style="font-size: 14px; line-height: 1.4; white-space: pre-wrap;">{row_m['mensagem']}</div>
                    </div>
                """,
            unsafe_allow_html=True,
        )

        if row_m["arquivo_path"] and os.path.exists(str(row_m["arquivo_path"])):
          if row_m["arquivo_nome"].lower().endswith((".png", ".jpg", ".jpeg")):
            st.image(
                row_m["arquivo_path"],
                caption=f"Mídia de {row_m['remetente']}",
                width=280,
            )
          with open(row_m["arquivo_path"], "rb") as f_down:
            st.download_button(
                label=f"📥 Baixar anexo: {row_m['arquivo_nome']}",
                data=f_down.read(),
                file_name=row_m["arquivo_nome"],
                key=f"dl_chat_arq_{row_m['id']}",
            )
    else:
      st.info("Ainda sem mensagens neste canal. Começa a conversa abaixo!")

    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("form_chat_direto_pro", clear_on_submit=True):
      col_msg1, col_msg2 = st.columns([3, 1])
      with col_msg1:
        msg_sala_txt = st.text_input(
            "Escreve a tua mensagem operacional...",
            placeholder="Mensagem segura para a equipa...",
        )
      with col_msg2:
        file_sala_up = st.file_uploader(
            "Anexar Mídia",
            type=["png", "jpg", "jpeg", "pdf", "docx"],
            label_visibility="collapsed",
        )

      btn_enviar_chat = st.form_submit_button(
          "🚀 Enviar Mensagem Instantânea"
      )

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
    st.markdown(
        "### 📞 Central de Chamada Direta Pessoal (Vídeo e Voz em Tempo Real)"
    )
    st.markdown(
        "Seleciona o colaborador (ex: Hayarya) para iniciar a chamada e"
        " notificar o dispositivo dele em tempo real:"
    )

    if todos_usuarios_db:
      alvos_chamada = [f"{u[1]} ({u[2]})" for u in todos_usuarios_db]
      alvo_selecionado = st.selectbox(
          "Quem vai receber a chamada ao vivo?",
          alvos_chamada,
          key="sel_alvo_video",
      )
    else:
      alvo_selecionado = "Equipe Geral"

    nome_sala_direta = f"TabalmixDirectCall{alvo_selecionado.split()[0]}2026"

    if "chamada_ativa" not in st.session_state:
      st.session_state["chamada_ativa"] = False

    col_b1, col_b2 = st.columns(2)
    with col_b1:
      if st.button("📞 Disparar Chamada e Ligar", key="btn_ligar_integ"):
        st.session_state["chamada_ativa"] = True

        remetente_notif = (
            usuario_atual["apelido"] if usuario_atual else "Administrador"
        )
        msg_alerta_chamada = (
            f"🚨 **CHAMADA DE VÍDEO ATIVA:** {remetente_notif} está a chamar-te"
            " para uma reunião ao vivo!"
        )
        data_env_notif = datetime.now().strftime("%H:%M — %d/%m")

        try:
          cursor.execute(
              "INSERT INTO chat_interno (remetente, destinatario, cargo,"
              " mensagem, arquivo_path, arquivo_nome, data_envio) VALUES (?, ?,"
              " ?, ?, ?, ?, ?)",
              (
                  "SISTEMA LIVE",
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

        st.success(f"Sinal de chamada enviado para {alvo_selecionado}!")
        st.rerun()
    with col_b2:
      if st.button("🔴 Desligar / Fechar Chamada", key="btn_desligar_integ"):
        st.session_state["chamada_ativa"] = False
        st.rerun()

    if st.session_state["chamada_ativa"]:
      st.markdown(f"**🟢 Chamada em curso com: {alvo_selecionado}**")
      jitsi_embed_html = f"""
            <div style="width: 100%; height: 600px; border-radius: 16px; overflow: hidden; background: #000; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
                <iframe src="https://meet.jit.si/{nome_sala_direta}#config.prejoinPageEnabled=false&config.disableDeepLinking=true&config.requireDisplayName=false&interfaceConfigOverwrite.MOBILE_APP_PROMO=false" 
                        allow="camera; microphone; fullscreen; display-capture" 
                        style="width: 100%; height: 100%; border: none;">
                </iframe>
            </div>
        """
      st.components.v1.html(jitsi_embed_html, height=620)
    else:
      st.info(
          "💡 Clica em 'Disparar Chamada e Ligar' para abrir o vídeo e"
          " notificar o colaborador instantaneamente."
      )

elif menu == "🔍 Consulta / Busca Geral":
  st.title("🔍 Consulta e Histórico Completo do Equipamento")
  df_v_busca = pd.read_sql(
      "SELECT tag_prefixo, modelo, placa FROM veiculos", conn
  )
  lista_tags = (
      df_v_busca["tag_prefixo"].dropna().tolist()
      if not df_v_busca.empty
      else []
  )
  if lista_tags:
    eq_sel = st.selectbox("Selecione a tag/prefixo", lista_tags)
    if eq_sel:
      df_eq_info = df_v_busca[df_v_busca["tag_prefixo"] == eq_sel]
      exibir_tabela_padronizada(df_eq_info, "busca_eq_info")

elif menu == "⚙️ Meu Perfil / Dados":
  st.title("⚙️ Meu Perfil & Credenciais Corporativas")
  if usuario_atual:
    user_id_ativo = usuario_atual.get("id")
    cursor.execute(
        "SELECT nome_completo, cpf, email, celular_seguranca, apelido,"
        " cargo_setor, pin_rapido, status_assinatura, plano_atual,"
        " data_cadastro FROM usuarios_sistema WHERE id = ?",
        (user_id_ativo,),
    )
    dados_db = cursor.fetchone()
    if dados_db:
      (
          n_comp,
          n_cpf,
          n_email,
          n_cel,
          n_apelido,
          n_cargo,
          n_pin,
          st_assinatura,
          plano_atual,
          dt_cad,
      ) = dados_db

      cargo_str = str(n_cargo) if n_cargo else "Operacional"
      if "Diretoria" in cargo_str or "Gestão" in cargo_str:
        nome_plano_comercial = "💎 Master Concreto & Diretoria"
        valor_mensal_ref = "R$ 299,90 / mês"
        valor_anual_ref = "R$ 2.999,00 / ano"
      elif "Engenheiro" in cargo_str:
        nome_plano_comercial = "🏗️ Engenharia & Obra Pro"
        valor_mensal_ref = "R$ 189,90 / mês"
        valor_anual_ref = "R$ 1.899,00 / ano"
      elif "Mecânico" in cargo_str:
        nome_plano_comercial = "🛠️ Oficina & Mecânica X"
        valor_mensal_ref = "R$ 119,90 / mês"
        valor_anual_ref = "R$ 1.199,00 / ano"
      else:
        nome_plano_comercial = "🚜 Operacional Campo & Frota"
        valor_mensal_ref = "R$ 69,90 / mês"
        valor_anual_ref = "R$ 699,00 / ano"

      dias_restantes = "Ativo"
      try:
        if dt_cad:
          data_inicio = datetime.strptime(dt_cad[:10], "%Y-%m-%d")
          dias_decorridos = (datetime.now() - data_inicio).days
          limite_dias = 365 if "Anual" in str(plano_atual) else 30
          dias_restantes = max(0, limite_dias - dias_decorridos)
      except Exception:
        dias_restantes = "30"

      st.markdown(
          f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
                    <h3 style="margin-top: 0; color: #047857; font-size: 18px;">💳 Licença e Categoria de Acesso na Obra</h3>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Perfil / Cargo:</b> {n_cargo}</p>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Plano Atribuído:</b> <span style="color: #059669; font-weight: bold;">{nome_plano_comercial}</span></p>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Valores de Referência:</b> Mensal ({valor_mensal_ref}) | Anual ({valor_anual_ref})</p>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Modalidade Atual:</b> {plano_atual if plano_atual else 'Plano Mensal'}</p>
                    <p style="margin: 6px 0; font-size: 14px;"><b>Dias Restantes para Renovação:</b> <span style="color: #2563eb; font-weight: bold; font-size: 16px;">{dias_restantes} dias</span></p>
                </div>
            """,
          unsafe_allow_html=True,
      )

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
  else:
    st.info(
        "🔓 Estás logado como Administrador Master. As tuas credenciais de"
        " gestão são geridas pelo link de acesso seguro."
    )

elif menu == "⚙️ Painel de Licença (Admin)" and modo_admin_liberado:
  st.title("⚙️ Painel Administrativo de Chaves & Licenças Corporativas")
  st.markdown(
      "Gere chaves de ativação em lote para a empresa ou gerencie os acessos"
      " dos colaboradores."
  )

  tab_gerar_chaves, tab_ver_chaves, tab_gerenciar_users = st.tabs([
      "🎟️ Gerar Chaves em Lote",
      "📋 Chaves Geradas",
      "👥 Gerenciar Colaboradores",
  ])

  with tab_gerar_chaves:
    with st.form("form_gerar_chaves_lote"):
      st.markdown("### 🔑 Gerador de Chaves de Ativação")
      qtd_chaves = st.number_input(
          "Quantidade de chaves a gerar", min_value=1, max_value=50, value=5
      )
      cargo_chave = st.selectbox(
          "Cargo / Função associada à chave",
          [
              "Diretoria / Gestão",
              "Engenheiro / Gestor de Obra",
              "Mecânico / Oficina",
              "Operador / Motorista / Campo",
          ],
      )
      modalidade_chave = st.selectbox(
          "Modalidade da Licença",
          ["Plano Mensal (30 dias)", "Plano Anual (365 dias)"],
      )
      btn_gerar_lote = st.form_submit_button("🚀 Gerar Lote de Chaves")

      if btn_gerar_lote:
        chaves_criadas = []
        for _ in range(int(qtd_chaves)):
          parte1 = "".join(
              random.choices(string.ascii_uppercase + string.digits, k=4)
          )
          parte2 = "".join(
              random.choices(string.ascii_uppercase + string.digits, k=4)
          )
          codigo = f"TABALMIX-{parte1}-{parte2}"
          try:
            cursor.execute(
                "INSERT INTO chaves_licenca (codigo_chave, cargo_atribuido,"
                " modalidade, status_uso, usado_por, data_criacao) VALUES (?,"
                " ?, ?, 'Disponível', 'N/A', ?)",
                (
                    codigo,
                    cargo_chave,
                    modalidade_chave,
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            )
            chaves_criadas.append(codigo)
          except Exception:
            pass
        conn.commit()
        st.success(
            f"✅ {len(chaves_criadas)} chaves geradas com sucesso! Veja na aba"
            " 'Chaves Geradas'."
        )

  with tab_ver_chaves:
    st.markdown("### 📋 Relatório de Chaves de Ativação")
    df_chaves = pd.read_sql("SELECT * FROM chaves_licenca", conn)
    if not df_chaves.empty:
      exibir_tabela_padronizada(df_chaves, "chaves_licenca")
    else:
      st.info("Nenhuma chave gerada ainda.")

  with tab_gerenciar_users:
    st.markdown("### 👥 Gerenciamento de Colaboradores & Planos")
    df_users = pd.read_sql("SELECT * FROM usuarios_sistema", conn)
    if not df_users.empty:
      exibir_tabela_padronizada(df_users, "usuarios_sistema")

      st.markdown("---")
      st.markdown("### ✍️ Atualizar Cargo ou Plano de um Colaborador")
      lista_emails_users = df_users["email"].tolist()
      colab_selecionado = st.selectbox(
          "Selecione o colaborador pelo e-mail",
          lista_emails_users,
          key="sel_colab_usr",
      )

      with st.form("form_editar_colaborador_admin"):
        novo_cargo_adm = st.selectbox(
            "Novo Cargo / Função",
            [
                "Diretoria / Gestão",
                "Engenheiro / Gestor de Obra",
                "Mecânico / Oficina",
                "Operador / Motorista / Campo",
            ],
            key="adm_novo_cargo",
        )
        novo_status_adm = st.selectbox(
            "Status da Conta", ["Ativo", "Inativo"], key="adm_novo_status"
        )
        nova_modalidade_adm = st.selectbox(
            "Modalidade de Plano",
            ["Plano Mensal (30 dias)", "Plano Anual (365 dias)"],
            key="adm_nova_mod",
        )
        btn_atualizar_adm = st.form_submit_button(
            "💾 Salvar Alterações do Colaborador"
        )

        if btn_atualizar_adm:
          novo_plano_str = f"{novo_cargo_adm} — {nova_modalidade_adm}"
          cursor.execute(
              "UPDATE usuarios_sistema SET cargo_setor = ?, status_assinatura"
              " = ?, plano_atual = ? WHERE email = ?",
              (
                  novo_cargo_adm,
                  novo_status_adm,
                  novo_plano_str,
                  colab_selecionado,
              ),
          )
          conn.commit()
          st.success(
              f"✅ Colaborador **{colab_selecionado}** atualizado com sucesso!"
          )
          st.rerun()
