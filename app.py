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

# ESTILIZAÇÃO VISUAL PREMIUM ENTERPRISE & CORREÇÃO DE INTERFACE MOBILE
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    button[kind="header"], [data-testid="collapsedControl"] svg {
        color: #047857 !important;
    }
    
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 3rem !important;
        max-width: 100% !important;
    }
    
    section[data-testid="stSidebar"] {
        background: #f8fafc !important;
        border-right: 1px solid #e2e8f0;
        padding-top: 0rem !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem !important;
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


def init_db():
  conn = sqlite3.connect("frota_profissional.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_prefixo TEXT, codigo_patrimonio TEXT, tipo TEXT,
            categoria_equipamento TEXT, marca TEXT, modelo TEXT, ano INTEGER,
            chassi TEXT, renavam TEXT, placa TEXT, crv TEXT, cor TEXT,
            combustivel TEXT, empresa TEXT, horimetro_km INTEGER, status TEXT,
            historico_edicoes TEXT
        )
    """)

  for col_sql in [
      "ALTER TABLE veiculos ADD COLUMN codigo_patrimonio TEXT",
      "ALTER TABLE veiculos ADD COLUMN tipo TEXT",
      "ALTER TABLE veiculos ADD COLUMN categoria_equipamento TEXT",
      "ALTER TABLE veiculos ADD COLUMN chassi TEXT",
      "ALTER TABLE veiculos ADD COLUMN renavam TEXT",
      "ALTER TABLE veiculos ADD COLUMN crv TEXT",
      "ALTER TABLE veiculos ADD COLUMN cor TEXT",
      "ALTER TABLE veiculos ADD COLUMN combustivel TEXT",
      "ALTER TABLE veiculos ADD COLUMN empresa TEXT",
      "ALTER TABLE veiculos ADD COLUMN historico_edicoes TEXT",
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
            colunas_permitidas TEXT
        )
    """)
  try:
    cursor.execute("ALTER TABLE config_colunas ADD COLUMN colunas_permitidas TEXT")
  except Exception:
    pass

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
        "UPDATE usuarios_sistema SET apelido = 'Alex' WHERE apelido IS"
        " NULL OR apelido = '' OR apelido = 'None'"
    )
    cursor.execute(
        "UPDATE usuarios_sistema SET cargo_setor = 'Diretoria / Gestão' WHERE"
        " cargo_setor IS NULL OR cargo_setor = '' OR cargo_setor = 'None'"
    )
    conn.commit()
  except Exception:
    pass

  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

if "usuario_logado" not in st.session_state:
  st.session_state["usuario_logado"] = {
      "id": 1,
      "nome": "Alex de Castro Bernardino",
      "cpf": "000.000.000-00",
      "email": "alex@tabalmix.com",
      "status": "Ativo",
      "apelido": "Alex",
      "cargo": "Diretoria / Gestão",
  }

usuario_atual = st.session_state["usuario_logado"]
status_usuario_ativo = True


def exibir_tabela_padronizada(df, nome_tabela):
  if df.empty:
    st.info("Nenhum registo encontrado.")
    return

  try:
    cursor.execute(
        "SELECT colunas_permitidas FROM config_colunas WHERE tabela = ?",
        (nome_tabela,),
    )
    res_conf = cursor.fetchone()
    if res_conf and res_conf[0]:
      cols_permitidas = [c.strip() for c in res_conf[0].split(",") if c.strip()]
      cols_existentes_validas = [c for c in cols_permitidas if c in df.columns]
      if cols_existentes_validas:
        df = df[cols_existentes_validas]
  except Exception:
    pass

  st.dataframe(df, use_container_width=True, hide_index=True)


with st.sidebar:
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_logo_side = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 14px; padding: 10px; text-align: center; margin-bottom: 8px; color: white; box-shadow: 0 4px 12px rgba(5,150,105,0.2);">
                <div style="font-size: 14px; font-weight: 900; margin-bottom: 6px; letter-spacing: -0.5px;">🏗️ TABALMIX CONCRETO</div>
                <div style="border-radius: 10px; overflow: hidden; max-height: 90px; border: 2px solid rgba(255,255,255,0.8); margin-bottom: 6px;">
                    <img src="data:image/jpeg;base64,{encoded_logo_side}" style="width: 100%; height: 90px; object-fit: cover;">
                </div>
                <div style="font-size: 9.5px; color: #e2e8f0; font-weight: 700; text-transform: uppercase;">⭐ Certificado Oficial | Castro Tech ⭐</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.markdown(
        """
            <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 14px; padding: 10px; text-align: center; margin-bottom: 8px; color: white;">
                <div style="font-size: 14px; font-weight: 900;">🏗️ TABALMIX CONCRETO</div>
                <div style="font-size: 9.5px; color: #e2e8f0; font-weight: 700;">⭐ Certificado Oficial | Castro Tech ⭐</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

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
      "⚙️ Painel de Licença (Admin)",
  ]

  menu = st.radio("Navegação", lista_menus, label_visibility="collapsed")

if menu == "📊 Visão Geral":
  st.title("🏗️ Painel Executivo e Indicadores de Frota")
  st.markdown(
      "Indicadores consolidados em tempo real para tomada de decisão"
      " executiva (Gestores, Engenheiros e Administradores)."
  )

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

  st.markdown("### 📈 Estatísticas e Gráficos de Desempenho (Primeiro Mundo)")
  col_g1, col_g2 = st.columns(2)

  with col_g1:
    st.markdown("#### 🛠️ Custo de Manutenção por Tipo")
    if (
        not df_manut.empty
        and "tipo_manutencao" in df_manut.columns
        and "custo" in df_manut.columns
    ):
      df_custo_tipo = (
          df_manut.groupby("tipo_manutencao")["custo"].sum().reset_index()
      )
      st.bar_chart(df_custo_tipo.set_index("tipo_manutencao"))
    else:
      st.info("Ainda sem dados suficientes para exibir o gráfico de manutenções.")

  with col_g2:
    st.markdown("#### ⛽ Consumo de Combustível (Litros) por Equipamento")
    if (
        not df_comb.empty
        and "equipamento" in df_comb.columns
        and "litros" in df_comb.columns
    ):
      df_litros_eq = (
          df_comb.groupby("equipamento")["litros"].sum().reset_index()
      )
      st.bar_chart(df_litros_eq.set_index("equipamento"))
    else:
      st.info("Ainda sem dados suficientes para exibir o gráfico de combustíveis.")

  st.divider()
  st.markdown("### 📋 Listagem Geral de Equipamentos")
  if not df_veiculos.empty:
    exibir_tabela_padronizada(df_veiculos, "veiculos")

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
      if st.button("📄 Gerar Relatório Executivo Geral em PDF"):
        pdf_geral = gerar_pdf_relatorio(
            "Relatório Executivo Geral da Frota", df_veiculos
        )
        st.download_button(
            label="📥 Baixar PDF Certificado",
            data=pdf_geral,
            file_name="relatorio_executivo_tabalmix.pdf",
            mime="application/pdf",
        )
    with col_dl2:
      if st.button("📊 Gerar Relatório Formatado em Excel"):
        excel_buf = gerar_excel_formatado(df_veiculos, "Frota_Geral")
        st.download_button(
            label="📥 Baixar Excel Pronto p/ Gestor",
            data=excel_buf,
            file_name="relatorio_frota_tabalmix.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
  else:
    st.info("Nenhum veículo registado na frota.")

elif menu == "🚜 Cadastro de Equipamentos":
  st.title("🚜 Cadastro Completo de Equipamentos e Frota")
  st.markdown(
      "Gira a frota, atribua a Linha do Equipamento, execute a vistoria"
      " fotográfica completa e personalize as colunas."
  )

  tab_eq_lista, tab_eq_cad, tab_eq_edit, tab_eq_foto, tab_eq_config = st.tabs([
      "📋 Frota Cadastrada",
      "➕ Registar Novo Equipamento",
      "✏️ Editar Frota & Histórico",
      "📸 Vistoria Fotográfica",
      "⚙️ Editar Colunas (Sistema)",
  ])

  with tab_eq_lista:
    df_f = pd.read_sql("SELECT * FROM veiculos", conn)
    if not df_f.empty:
      exibir_tabela_padronizada(df_f, "veiculos")
      if st.button("📊 Exportar Frota em Excel"):
        excel_f = gerar_excel_formatado(df_f, "Frota")
        st.download_button(
            label="📥 Baixar Excel da Frota",
            data=excel_f,
            file_name="frota_tabalmix.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
    else:
      st.info("Nenhum equipamento cadastrado ainda.")

  with tab_eq_cad:
    with st.form("form_cad_veiculo_completo"):
      st.markdown("### 🚜 Ficha Cadastral Detalhada do Veículo")
      c_e1, c_e2 = st.columns(2)
      with c_e1:
        f_prefixo = st.text_input("Tag / Prefixo (ex: EQ-001 / BET-12)")
        f_patrimonio = st.text_input("Código de Patrimônio")
        f_cat = st.selectbox(
            "Categoria do Equipamento",
            [
                "🟡 Linha Amarela (Escavadeiras, Pás, Retro)",
                "🟤 Linha Marrom (Tratores, Estacionários)",
                "🚚 Linha Concreto (Caminhões Betoneira e Bomba)",
                "🚛 Linha Branca / Apoio (Carrocerias, Utilitários)",
            ],
        )
        f_tipo = st.text_input("Tipo de Equipamento (ex: Betoneira 8m³)")
        f_marca = st.text_input("Marca (ex: Mercedes-Benz, Ford)")
        f_modelo = st.text_input("Modelo (ex: 2423 B, Cargo 2622 E)")
        f_ano = st.number_input("Ano de Fabricação", value=2024, step=1)
      with c_e2:
        f_chassi = st.text_input("Chassi")
        f_renavam = st.text_input("Renavam")
        f_crv = st.text_input("CRV")
        f_cor = st.text_input("Cor")
        f_comb = st.selectbox(
            "Combustível", ["Diesel S10", "Diesel S500", "Gasolina"]
        )
        f_horimetro = st.number_input(
            "Km / Horímetro Inicial", value=0, step=100
        )
        f_empresa = st.text_input("Empresa / Filial", value="Tabalmix Concreto")

      btn_salvar_eq = st.form_submit_button("💾 Salvar Equipamento Completo")
      if btn_salvar_eq:
        if f_marca and f_modelo:
          hist_cad_inicial = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Equipamento cadastrado com ficha completa."
          cursor.execute(
              "INSERT INTO veiculos (tag_prefixo, codigo_patrimonio, tipo,"
              " categoria_equipamento, marca, modelo, ano, chassi, renavam,"
              " placa, crv, cor, combustivel, empresa, horimetro_km, status,"
              " historico_edicoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?,"
              " ?, ?, ?, 'Ativo', ?)",
              (
                  f_prefixo,
                  f_patrimonio,
                  f_tipo,
                  f_cat,
                  f_marca,
                  f_modelo,
                  int(f_ano),
                  f_chassi,
                  f_renavam,
                  f_crv,
                  f_cor,
                  f_comb,
                  f_empresa,
                  int(f_horimetro),
                  hist_cad_inicial,
              ),
          )
          conn.commit()
          st.success(
              "✅ Equipamento cadastrado com ficha completa e registado na"
              " base!"
          )
          st.rerun()
        else:
          st.error("⚠️ Preencha pelo menos a Marca e o Modelo.")

  with tab_eq_edit:
    st.markdown("### ✏️ Editar Dados da Frota & Justificar Alteração")
    try:
      df_veiculos_edit = pd.read_sql(
          "SELECT * FROM veiculos ORDER BY id DESC", conn
      )
    except Exception:
      df_veiculos_edit = pd.DataFrame()

    if not df_veiculos_edit.empty:
      id_veiculo_sel = st.selectbox(
          "Selecione o Veículo / Equipamento para editar:",
          df_veiculos_edit["id"].tolist(),
          format_func=lambda x: f"ID #{x} — {df_veiculos_edit[df_veiculos_edit['id'] == x]['marca'].values[0]} {df_veiculos_edit[df_veiculos_edit['id'] == x]['modelo'].values[0]} (Placa: {df_veiculos_edit[df_veiculos_edit['id'] == x]['placa'].values[0]})",
      )
      veiculo_atual_reg = df_veiculos_edit[
          df_veiculos_edit["id"] == id_veiculo_sel
      ].iloc[0]

      with st.form(f"form_editar_veiculo_completo_{id_veiculo_sel}"):
        st.markdown(f"#### Editando Ficha do Veículo ID #{id_veiculo_sel}")
        e_pref = st.text_input(
            "Prefixo / Tag", value=str(veiculo_atual_reg["tag_prefixo"])
        )
        e_pat = st.text_input(
            "Código de Patrimônio",
            value=str(veiculo_atual_reg["codigo_patrimonio"]),
        )
        e_marca = st.text_input("Marca", value=str(veiculo_atual_reg["marca"]))
        e_modelo = st.text_input(
            "Modelo", value=str(veiculo_atual_reg["modelo"])
        )
        e_placa = st.text_input("Placa", value=str(veiculo_atual_reg["placa"]))
        e_cor = st.text_input("Cor", value=str(veiculo_atual_reg["cor"]))
        e_km = st.number_input(
            "Km / Horímetro",
            value=(
                int(veiculo_atual_reg["horimetro_km"])
                if pd.notnull(veiculo_atual_reg["horimetro_km"])
                else 0
            ),
            step=100,
        )

        st.markdown("---")
        motivo_edicao_veiculo = st.text_input(
            "Motivo da Atualização / Troca (Obrigatório)",
            placeholder="Ex: Correção de placa ou atualização de horímetro...",
        )

        btn_atualizar_veiculo = st.form_submit_button(
            "💾 Salvar Alterações e Histórico"
        )

        if btn_atualizar_veiculo:
          if not motivo_edicao_veiculo.strip():
            st.error("⚠️ O campo 'Motivo da Atualização' é obrigatório!")
          else:
            hist_anterior = (
                str(veiculo_atual_reg["historico_edicoes"])
                if pd.notnull(veiculo_atual_reg["historico_edicoes"])
                else ""
            )
            novo_item_hist = f"\n[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Atualizado. Motivo: {motivo_edicao_veiculo}"
            hist_atualizado_final = hist_anterior + novo_item_hist

            cursor.execute(
                "UPDATE veiculos SET tag_prefixo = ?, codigo_patrimonio = ?,"
                " marca = ?, modelo = ?, placa = ?, cor = ?, horimetro_km = ?,"
                " historico_edicoes = ? WHERE id = ?",
                (
                    e_pref,
                    e_pat,
                    e_marca,
                    e_modelo,
                    e_placa,
                    e_cor,
                    int(e_km),
                    hist_atualizado_final,
                    int(id_veiculo_sel),
                ),
            )
            conn.commit()
            st.success("✅ Ficha do veículo atualizada com histórico gravado!")
            st.rerun()
    else:
      st.info("Nenhum veículo registado para editar.")

  with tab_eq_foto:
    st.markdown("### 📸 Vistoria Fotográfica Completa (Até 15 Ângulos)")
    try:
      df_veiculos_f = pd.read_sql(
          "SELECT id, marca, modelo, placa FROM veiculos", conn
      )
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
          "Carregar fotografias da vistoria (múltiplos ângulos):",
          type=["png", "jpg", "jpeg"],
          accept_multiple_files=True,
      )

      if fotos_enviadas:
        os.makedirs("vistorias_frota", exist_ok=True)
        if st.button("🚀 Salvar Vistoria Fotográfica"):
          for idx, foto in enumerate(fotos_enviadas[:15]):
            nome_foto = f"vistoria_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}_{foto.name}"
            caminho_foto = os.path.join("vistorias_frota", nome_foto)
            with open(caminho_foto, "wb") as f_out:
              f_out.write(foto.getbuffer())
          st.success(
              "✅ Vistoria fotográfica armazenada com segurança na pasta do"
              " projeto!"
          )
    else:
      st.info("Registe primeiro um veículo na aba 'Registar Novo Equipamento'.")

  with tab_eq_config:
    st.markdown("### ⚙️ Gestor de Colunas Personalizadas (Sistema Inteiro)")
    st.markdown(
        "Marque abaixo **apenas** as colunas que você deseja manter visíveis."
        " As colunas desmarcadas serão ocultadas da exibição para você e para"
        " todos os colaboradores."
    )

    tabela_escolhida_aba = st.selectbox(
        "Selecione a Tabela do Sistema para Configurar:",
        [
            "veiculos",
            "manutencoes",
            "mobilizacoes",
            "combustivel",
            "pecas",
            "clientes",
        ],
    )

    try:
      df_cols_aba = pd.read_sql(
          f"SELECT * FROM {tabela_escolhida_aba} LIMIT 1", conn
      )
      todas_cols_sistema = list(df_cols_aba.columns)
    except Exception:
      todas_cols_sistema = []

    cursor.execute(
        "SELECT colunas_permitidas FROM config_colunas WHERE tabela = ?",
        (tabela_escolhida_aba,),
    )
    res_db_aba = cursor.fetchone()

    if res_db_aba and res_db_aba[0]:
      cols_salvas_aba = [c.strip() for c in res_db_aba[0].split(",") if c.strip()]
      def_cols_aba = [c for c in cols_salvas_aba if c in todas_cols_sistema]
    else:
      def_cols_aba = todas_cols_sistema

    colunas_mantidas_nova = st.multiselect(
        "Colunas visíveis na tabela:",
        todas_cols_sistema,
        default=def_cols_aba,
    )

    if st.button("💾 Salvar Configuração de Colunas"):
      if colunas_mantidas_nova:
        str_cols_final_aba = ",".join(colunas_mantidas_nova)
        cursor.execute(
            "INSERT OR REPLACE INTO config_colunas (tabela, colunas_permitidas)"
            " VALUES (?, ?)",
            (tabela_escolhida_aba, str_cols_final_aba),
        )
        conn.commit()
        st.success(
            f"✅ Configuração salva! A tabela '{tabela_escolhida_aba}' agora"
            " exibe apenas as colunas selecionadas."
        )
        st.rerun()
      else:
        st.warning("⚠️ Selecione pelo menos uma coluna.")

elif menu == "⛽ Abastecimentos & Combustível":
  st.title("⛽ Controle de Abastecimento e Combustível")
  tab_c_lista, tab_c_cad = st.tabs(
      ["📋 Histórico de Abastecimentos", "➕ Registar Abastecimento"]
  )
  with tab_c_lista:
    df_c = pd.read_sql("SELECT * FROM combustivel ORDER BY id DESC", conn)
    exibir_tabela_padronizada(df_c, "combustivel")
  with tab_c_cad:
    with st.form("form_abastecimento_completo"):
      eq_ab = st.text_input("Equipamento / Prefixo")
      litros_ab = st.number_input("Quantidade em Litros", value=100.0, step=10.0)
      valor_ab = st.number_input("Valor Total (R$)", value=600.0, step=50.0)
      posto_ab = st.text_input("Posto de Abastecimento")
      motorista_ab = st.text_input("Motorista / Responsável")
      btn_salvar_ab = st.form_submit_button("💾 Registar Abastecimento")
      if btn_salvar_ab and eq_ab:
        cursor.execute(
            "INSERT INTO combustivel (equipamento, litros, valor_total,"
            " km_horimetro, posto_posto, motorista, data) VALUES (?, ?, ?,"
            " '0', ?, ?, ?)",
            (
                eq_ab,
                litros_ab,
                valor_ab,
                posto_ab,
                motorista_ab,
                datetime.now().strftime("%d/%m/%Y %H:%M"),
            ),
        )
        conn.commit()
        st.success("✅ Abastecimento registado com sucesso!")
        st.rerun()

elif menu == "🏗️ Mobilização / Desmobilização":
  st.title("🏗️ Gestão de Mobilização e Desmobilização")
  tab_m_lista, tab_m_cad = st.tabs(
      ["📋 Histórico de Mobilizações", "➕ Registar Nova Mobilização"]
  )
  with tab_m_lista:
    df_mobs = pd.read_sql("SELECT * FROM mobilizacoes ORDER BY id DESC", conn)
    exibir_tabela_padronizada(df_mobs, "mobilizacoes")
  with tab_m_cad:
    with st.form("form_mobilizacao_completo"):
      eq_m = st.text_input("Equipamento")
      tipo_m = st.selectbox(
          "Tipo de Movimento",
          [
              "Mobilização para Obra",
              "Desmobilização",
              "Remanejamento",
          ],
      )
      dest_m = st.text_input("Destino / Origem")
      resp_m = st.text_input("Responsável Técnico")
      motivo_m = st.text_input("Condição / Motivo")
      btn_salvar_m = st.form_submit_button("💾 Salvar Mobilização")
      if btn_salvar_m and eq_m:
        cursor.execute(
            "INSERT INTO mobilizacoes (equipamento, tipo_movimento,"
            " destino_origem, responsavel, data, horimetro_km_mov,"
            " motivo_condicao, observacao) VALUES (?, ?, ?, ?, ?, '0', ?, '')",
            (
                eq_m,
                tipo_m,
                dest_m,
                resp_m,
                datetime.now().strftime("%d/%m/%Y"),
                motivo_m,
            ),
        )
        conn.commit()
        st.success("✅ Mobilização registada com sucesso!")
        st.rerun()

elif menu == "🛠️ Ordens de Serviço (OS)":
  st.title("🛠️ Ordens de Serviço (OS)")
  tab_os_lista, tab_os_cad = st.tabs(
      ["📋 Ordens de Serviço Abertas/Fechadas", "➕ Abrir Nova OS"]
  )
  with tab_os_lista:
    df_os = pd.read_sql("SELECT * FROM manutencoes ORDER BY id DESC", conn)
    exibir_tabela_padronizada(df_os, "manutencoes")
  with tab_os_cad:
    with st.form("form_os_completo"):
      eq_os = st.text_input("Equipamento / Prefixo")
      tipo_os = st.selectbox(
          "Tipo de Manutenção",
          ["Corretiva", "Preventiva", "Preditiva", "Emergencial"],
      )
      desc_os = st.text_area("Descrição do Problema / Serviço")
      custo_os = st.number_input("Custo Total Estimado (R$)", value=0.0, step=100.0)
      oficina_os = st.text_input("Oficina / Mecânico Responsável")
      btn_salvar_os = st.form_submit_button("💾 Abrir Ordem de Serviço")
      if btn_salvar_os and eq_os:
        cursor.execute(
            "INSERT INTO manutencoes (tag_prefixo, tipo_manutencao,"
            " horimetro_km_manut, origem_falha, descricao_problema,"
            " data_abertura, hora_abertura, pecas_utilizadas, custo_pecas,"
            " mao_de_obra, custo, oficina, tecnico_mecanico, data_fechamento,"
            " hora_fechamento, status_os) VALUES (?, ?, '0', 'Operação', ?, ?,"
            " ?, '', 0, 0, ?, ?, '', '', '', 'aberta')",
            (
                eq_os,
                tipo_os,
                desc_os,
                datetime.now().strftime("%d/%m/%Y"),
                datetime.now().strftime("%H:%M"),
                custo_os,
                oficina_os,
            ),
        )
        conn.commit()
        st.success("✅ Ordem de Serviço aberta com sucesso!")
        st.rerun()

elif menu == "🔩 Peças e Ferramentas":
  st.title("🔩 Controle de Peças e Ferramentas")
  tab_p_lista, tab_p_cad = st.tabs(["📋 Estoque Atual", "➕ Cadastrar Item"])
  with tab_p_lista:
    df_pecas = pd.read_sql("SELECT * FROM pecas ORDER BY id DESC", conn)
    exibir_tabela_padronizada(df_pecas, "pecas")
  with tab_p_cad:
    with st.form("form_peca_completo"):
      nome_p = st.text_input("Nome da Peça ou Ferramenta")
      cat_p = st.selectbox(
          "Categoria",
          ["Filtros e Óleos", "Correias", "Freios", "Ferramental", "Outros"],
      )
      qtd_p = st.number_input("Quantidade em Estoque", value=1, step=1)
      val_p = st.number_input("Valor Unitário (R$)", value=50.0, step=10.0)
      btn_salvar_p = st.form_submit_button("💾 Salvar no Estoque")
      if btn_salvar_p and nome_p:
        cursor.execute(
            "INSERT INTO pecas (nome_item, categoria, quantidade,"
            " valor_unitario) VALUES (?, ?, ?, ?)",
            (nome_p, cat_p, int(qtd_p), val_p),
        )
        conn.commit()
        st.success("✅ Peça registada no estoque!")
        st.rerun()

elif menu == "👥 Gestão de Clientes":
  st.title("👥 Gestão de Clientes")
  tab_cli_lista, tab_cli_cad = st.tabs(
      ["📋 Clientes Cadastrados", "➕ Cadastrar Cliente"]
  )
  with tab_cli_lista:
    df_cli = pd.read_sql("SELECT * FROM clientes ORDER BY id DESC", conn)
    exibir_tabela_padronizada(df_cli, "clientes")
  with tab_cli_cad:
    with st.form("form_cliente_completo"):
      nome_c = st.text_input("Nome do Cliente / Empresa")
      emp_c = st.text_input("Razão Social")
      tel_c = st.text_input("Telefone de Contato")
      doc_c = st.text_input("CPF / CNPJ")
      email_c = st.text_input("E-mail")
      end_c = st.text_input("Endereço Completo")
      btn_salvar_c = st.form_submit_button("💾 Salvar Cliente")
      if btn_salvar_c and nome_c:
        cursor.execute(
            "INSERT INTO clientes (nome, empresa, telefone, documento, email,"
            " endereco) VALUES (?, ?, ?, ?, ?, ?)",
            (nome_c, emp_c, tel_c, doc_c, email_c, end_c),
        )
        conn.commit()
        st.success("✅ Cliente cadastrado com sucesso!")
        st.rerun()

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
        </style>
    """,
      unsafe_allow_html=True,
  )
  st.title("💬 Central Pro Enterprise — Chat & Live Ops")
  st.markdown("Canal de comunicação interno em tempo real para equipe e diretoria.")

  df_msgs = pd.read_sql(
      "SELECT * FROM chat_interno ORDER BY id ASC LIMIT 60", conn
  )

  st.markdown('<div class="chat-container">', unsafe_allow_html=True)
  if not df_msgs.empty:
    for _, row_m in df_msgs.iterrows():
      st.markdown(
          f"**{row_m['remetente']}** ({row_m['data_envio']}):"
          f" {row_m['mensagem']}"
      )
  else:
    st.info("Ainda sem mensagens no chat.")
  st.markdown("</div>", unsafe_allow_html=True)

  with st.form("form_chat_completo", clear_on_submit=True):
    msg_txt = st.text_input("Escreva sua mensagem...")
    btn_env = st.form_submit_button("Enviar Mensagem")
    if btn_env and msg_txt:
      cursor.execute(
          "INSERT INTO chat_interno (remetente, destinatario, cargo, mensagem,"
          " arquivo_path, arquivo_nome, data_envio) VALUES (?, 'Geral',"
          " 'Diretoria', ?, '', '', ?)",
          (
              usuario_atual["apelido"],
              msg_txt,
              datetime.now().strftime("%H:%M — %d/%m"),
          ),
      )
      conn.commit()
      st.rerun()

elif menu == "🔍 Consulta / Busca Geral":
  st.title("🔍 Consulta e Histórico Completo")
  st.markdown("Pesquisa unificada em toda a base de dados do sistema.")
  termo_busca = st.text_input(
      "Digite o termo para buscar (Placa, Marca, Cliente, Peça):"
  )
  if termo_busca:
    df_v_busca = pd.read_sql(
        f"SELECT * FROM veiculos WHERE marca LIKE '%{termo_busca}%' OR modelo"
        f" LIKE '%{termo_busca}%' OR placa LIKE '%{termo_busca}%' OR"
        f" tag_prefixo LIKE '%{termo_busca}%'",
        conn,
    )
  else:
    df_v_busca = pd.read_sql("SELECT * FROM veiculos", conn)
  exibir_tabela_padronizada(df_v_busca, "veiculos")

elif menu == "⚙️ Meu Perfil / Dados":
  st.title("⚙️ Meu Perfil & Atualização Cadastral")
  st.markdown(f"**Usuário Conectado:** {usuario_atual['nome']}")
  st.markdown(f"**Cargo / Setor:** {usuario_atual['cargo']}")
  st.markdown(f"**E-mail:** {usuario_atual['email']}")
  st.success("🔓 Conta autenticada com privilégios de Administrador Master.")

elif menu == "⚙️ Painel de Licença (Admin)":
  st.title("⚙️ Painel Administrativo Master")
  st.markdown("Gerenciamento de chaves e licenças corporativas do sistema.")
  df_chaves = pd.read_sql("SELECT * FROM chaves_licenca", conn)
  exibir_tabela_padronizada(df_chaves, "chaves_licenca")
