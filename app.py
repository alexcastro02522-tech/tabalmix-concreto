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

# CONFIGURAÇÃO DO MERCADO PAGO (Token Oficial Integrado)
MERCADO_PAGO_ACCESS_TOKEN = (
    "APP_USR-5959521111272944-091612-0753df7e8e6f3065d831fff33f2257af-3692527935"
)

# Configuração da Página com Menu Fixo Expandido
st.set_page_config(
    page_title="Tabalmix Concreto - Gestão de Frota e Oficina Pro",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização Visual Corporativa Avançada
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
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
      "Sistema de Gestão de Frota e Operações | Powered by De Castro Tech",
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
  c.rect(
      margem_esq,
      y - 4,
      largura_util,
      altura_linha,
      fill=1,
      stroke=0,
  )
  c.setFillColorRGB(1, 1, 1)
  c.setFont("Helvetica-Bold", 8.5)
  largura_coluna = largura_util / len(colunas_amigables)

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
      c.rect(
          margem_esq,
          y - 3,
          largura_util,
          altura_linha - 2,
          fill=1,
          stroke=0,
      )
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
      "TABALMIX CONCRETO — Todos os direitos reservados. Tecnologia De Castro"
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
  dataframe.to_csv(output, index=False, sep=";")
  return output.getvalue().encode("utf-8")


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
        CREATE TABLE IF NOT EXISTS licenca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_assinatura TEXT,
            plano_atual TEXT,
            data_vencimento TEXT,
            chave_pix TEXT
        )
    """)
  cursor.execute("SELECT COUNT(*) FROM licenca")
  if cursor.fetchone()[0] == 0:
    vencimento_padrao = (datetime.now() + timedelta(days=30)).strftime(
        "%Y-%m-%d"
    )
    cursor.execute(
        "INSERT INTO licenca (status_assinatura, plano_atual, data_vencimento,"
        " chave_pix) VALUES (?, ?, ?, ?)",
        (
            "Ativo",
            "Mensal (R$ 250,00)",
            vencimento_padrao,
            "seu-email-pix@dominio.com",
        ),
    )
    conn.commit()
  conn.commit()
  return conn


conn = init_db()
cursor = conn.cursor()

df_licenca = pd.read_sql("SELECT * FROM licenca", conn)
status_atual = (
    df_licenca.iloc[0]["status_assinatura"] if not df_licenca.empty else "Ativo"
)
plano_atual = (
    df_licenca.iloc[0]["plano_atual"]
    if not df_licenca.empty and "plano_atual" in df_licenca.columns
    else "Mensal"
)
chave_pix_recebimento = (
    df_licenca.iloc[0]["chave_pix"]
    if not df_licenca.empty
    else "seu-pix@email.com"
)


# Função para bloquear ações de cadastro caso o status esteja inativo e exibir Mercado Pago
def verificar_licenca_para_acao():
  if status_atual != "Ativo":
    st.warning(
        "🔒 **Ação Bloqueada:** O sistema está com a licença pendente ou inativa."
        " Para cadastrar novos registros, contrate o plano abaixo:"
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
      if st.button("💳 Pagar Plano Mensal (R$ 250,00)"):
        try:
          sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
          preference_data = {
              "items": [{
                  "title": (
                      "Tabalmix Concreto - Assinatura Mensal de Sistema de"
                      " Gestão"
                  ),
                  "quantity": 1,
                  "unit_price": 250.0,
                  "currency_id": "BRL",
              }],
              "back_urls": {
                  "success": "https://streamlit.io",
                  "failure": "https://streamlit.io",
                  "pending": "https://streamlit.io",
              },
              "auto_return": "approved",
          }
          preference_response = sdk.preference().create(preference_data)
          checkout_url = (
              preference_response["response"].get("init_point")
              if "response" in preference_response
              else ""
          )
          if checkout_url:
            st.markdown(
                f'<meta http-equiv="refresh" content="0;url={checkout_url}">',
                unsafe_allow_html=True,
            )
            st.success(f"[Clique aqui para pagar via Mercado Pago]({checkout_url})")
        except Exception as e:
          st.error(f"Erro ao gerar pagamento: {e}")

    with col_p2:
      if st.button("🌟 Pagar Plano Anual (R$ 2.400,00)"):
        try:
          sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
          preference_data = {
              "items": [{
                  "title": "Tabalmix Concreto - Assinatura Anual",
                  "quantity": 1,
                  "unit_price": 2400.0,
                  "currency_id": "BRL",
              }],
              "back_urls": {
                  "success": "https://streamlit.io",
                  "failure": "https://streamlit.io",
                  "pending": "https://streamlit.io",
              },
              "auto_return": "approved",
          }
          preference_response = sdk.preference().create(preference_data)
          checkout_url = (
              preference_response["response"].get("init_point")
              if "response" in preference_response
              else ""
          )
          if checkout_url:
            st.markdown(
                f'<meta http-equiv="refresh" content="0;url={checkout_url}">',
                unsafe_allow_html=True,
            )
            st.success(f"[Clique aqui para pagar via Mercado Pago]({checkout_url})")
        except Exception as e:
          st.error(f"Erro ao gerar pagamento: {e}")
    return False
  return True


# Menu Lateral
with st.sidebar:
  st.markdown(
      """
            <div style="text-align: center; padding: 10px 0 15px 0;">
                <div style="font-size: 40px; margin-bottom: 2px;">🟢 🏗️</div>
                <h3 style="color: #2ecc71; margin: 0; font-size: 18px; font-weight: 800;">TABALMIX CONCRETO</h3>
                <p style="color: #94a3b8; font-size: 10px; margin: 2px 0 8px 0; text-transform: uppercase; letter-spacing: 1px;">Gestão de Frota & Operações</p>
                <p style="color: #e2e8f0; font-size: 11px; font-style: italic; font-weight: 500; line-height: 1.3; margin-bottom: 15px;">
                    "Tecnologia e robustez na concretagem."
                </p>
            </div>
        """,
      unsafe_allow_html=True,
  )

  if status_atual == "Ativo":
    st.success(
        "🛡️ **SISTEMA LICENCIADO**\n\n"
        f"**Plano:** {plano_atual}\n\n"
        "• Frota, Obras & Oficina\n"
        "• Powered by De Castro Tech"
    )
  else:
    st.error(
        "⚠️ **LICENÇA EXPIRADA**\n\nCadastros novos bloqueados até a renovação."
    )
  st.markdown("---")

menu = st.sidebar.radio(
    "Navegação do Sistema",
    [
        "📊 Visão Geral",
        "🚜 Frota e Maquinários",
        "⛽ Abastecimentos & Combustível",
        "🏗️ Mobilização / Desmobilização",
        "🛠️ Ordens de Serviço (OS)",
        "🔩 Peças e Ferramentas",
        "👥 Gestão de Clientes",
        "🔍 Consulta / Busca Geral",
        "⚙️ Painel de Licença (Admin)",
    ],
    label_visibility="collapsed",
)

if menu == "📊 Visão Geral":
  # Renderização segura via Base64 da foto 'caminhoes.jpg'
  try:
    with open("caminhoes.jpg", "rb") as image_file:
      encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
            <div style="width: 100%; border-radius: 14px; overflow: hidden; border: 2px solid #2ecc71; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <img src="data:image/jpeg;base64,{encoded_string}" style="width: 100%; display: block; object-fit: cover;">
            </div>
        """,
        unsafe_allow_html=True,
    )
  except Exception:
    st.info(
        "💡 Dica: Certifique-se de que o arquivo 'caminhoes.jpg' está enviado"
        " no GitHub."
    )

  st.markdown(
      """
            <div style="background: linear-gradient(135deg, rgba(5, 20, 10, 0.9) 0%, rgba(8, 30, 15, 0.85) 100%); padding: 30px; border-radius: 14px; border: 2px solid #2ecc71; margin-top: 15px; margin-bottom: 25px;">
                <h1 style="color: #2ecc71 !important; margin-bottom: 8px; font-size: 26px;">🏗️ Tabalmix - Painel Operacional da Frota</h1>
                <p style="color: #f1f5f9 !important; font-size: 15px; margin: 0; font-weight: 500;">Sistema corporativo avançado para controle de caminhões betoneira, maquinário pesado, obras e manutenções.</p>
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
        df_veiculos[
            df_veiculos["status"].isin(["Ativo", "Mobilizado", "Operando"])
        ]
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

elif menu == "🚜 Frota e Maquinários":
  st.title("🚜 Cadastro Completo de Veículos e Maquinário Pesado")
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
          "Horímetro ou Quilometragem Atual", min_value=0, value=15000, step=100
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
      if verificar_licenca_para_acao():
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
              f"✅ Ativo '{codigo_patrimonio.upper()} - {modelo}' cadastrado com"
              " sucesso!"
          )
        else:
          st.error(
              "⚠️ Preencha o Código de Patrimônio e o Modelo obrigatoriamente."
          )

  st.divider()
  st.subheader("Frota Registrada & Gerenciamento")
  df_f = pd.read_sql("SELECT * FROM veiculos", conn)
  if not df_f.empty:
    filtro_status_frota = st.selectbox(
        "🔍 Filtrar Tabela por Status",
        [
            "Todos os Status",
            "Ativo",
            "Mobilizado",
            "Em manutenção",
            "Parado",
            "Desmobilizado",
            "Inativo",
        ],
        key="filtro_frota_aba",
    )

    df_f_filtrado = df_f.copy()
    if filtro_status_frota != "Todos os Status":
      df_f_filtrado = df_f[df_f["status"] == filtro_status_frota]

    st.dataframe(df_f_filtrado, use_container_width=True)

    col_del1, col_del2 = st.columns([2, 1])
    with col_del1:
      veiculo_para_excluir = st.selectbox(
          "Selecione o ID do Equipamento para Excluir", df_f["id"].tolist()
      )
    with col_del2:
      st.write("")
      st.write("")
      if st.button("🗑️ Excluir Equipamento"):
        if verificar_licenca_para_acao():
          cursor.execute(
              "DELETE FROM veiculos WHERE id = ?", (veiculo_para_excluir,)
          )
          conn.commit()
          st.success("✅ Equipamento removido!")
          st.rerun()

    col_down1, col_down2 = st.columns(2)
    with col_down1:
      pdf_buffer = gerar_pdf_relatorio(
          "RELATÓRIO DE FROTA PRO - TABALMIX", df_f_filtrado
      )
      st.download_button(
          label="📥 Baixar Relatório em PDF",
          data=pdf_buffer,
          file_name="relatorio_frota_tabalmix.pdf",
          mime="application/pdf",
      )
    with col_down2:
      csv_buffer = gerar_csv_relatorio(df_f_filtrado)
      st.download_button(
          label="📊 Baixar Relatório em Planilha (.csv)",
          data=csv_buffer,
          file_name="relatorio_frota_tabalmix.csv",
          mime="text/csv",
      )
  else:
    st.info("Nenhum equipamento cadastrado na frota.")

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
        if verificar_licenca_para_acao():
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

    st.divider()
    st.subheader("Histórico de Abastecimentos Registrados")
    df_c_hist = pd.read_sql("SELECT * FROM combustivel", conn)
    if not df_c_hist.empty:
      st.markdown("##### 📅 Filtrar Histórico por Período")
      col_f1, col_f2 = st.columns(2)
      with col_f1:
        usar_filtro_data = st.checkbox(
            "Ativar Filtro de Datas em Abastecimentos"
        )
      if usar_filtro_data:
        col_d1, col_d2 = st.columns(2)
        with col_d1:
          data_inicio = st.date_input(
              "Data Inicial", datetime.now() - timedelta(days=30)
          )
        with col_d2:
          data_fim = st.date_input("Data Final", datetime.now())

        df_c_hist["data_dt"] = pd.to_datetime(
            df_c_hist["data"], errors="coerce"
        )
        df_c_filtrado = df_c_hist[
            (df_c_hist["data_dt"].dt.date >= data_inicio)
            & (df_c_hist["data_dt"].dt.date <= data_fim)
        ]
      else:
        df_c_filtrado = df_c_hist

      st.dataframe(
          df_c_filtrado.drop(columns=["data_dt"], errors="ignore"),
          use_container_width=True,
      )

      total_litros_filtrado = df_c_filtrado["litros"].sum()
      total_gasto_filtrado = df_c_filtrado["valor_total"].sum()
      st.info(
          f"📊 **Resumo do Período Selecionado:** {total_litros_filtrado:,.2f}"
          f" Litros | **Gasto Total:** R$ {total_gasto_filtrado:,.2f}"
      )

      col_dc1, col_dc2 = st.columns([2, 1])
      with col_dc1:
        comb_para_excluir = st.selectbox(
            "Selecione o ID para Remover do Histórico",
            df_c_hist["id"].tolist(),
        )
      with col_dc2:
        st.write("")
        st.write("")
        if st.button("🗑️ Excluir Abastecimento"):
          if verificar_licenca_para_acao():
            cursor.execute(
                "DELETE FROM combustivel WHERE id = ?", (comb_para_excluir,)
            )
            conn.commit()
            st.success("✅ Registro removido!")
            st.rerun()

      col_down1, col_down2 = st.columns(2)
      with col_down1:
        pdf_buffer = gerar_pdf_relatorio(
            "RELATÓRIO DE COMBUSTÍVEL - TABALMIX", df_c_filtrado
        )
        st.download_button(
            label="📥 Baixar Histórico Filtrado em PDF",
            data=pdf_buffer,
            file_name="relatorio_combustivel_tabalmix.pdf",
            mime="application/pdf",
        )
      with col_down2:
        csv_buffer = gerar_csv_relatorio(df_c_filtrado)
        st.download_button(
            label="📊 Baixar Histórico Filtrado em Planilha (.csv)",
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
        if verificar_licenca_para_acao():
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

    st.divider()
    st.subheader("Histórico de Mobilizações e Desmobilizações")
    df_mob_hist = pd.read_sql("SELECT * FROM mobilizacoes", conn)
    if not df_mob_hist.empty:
      st.dataframe(df_mob_hist, use_container_width=True)
      col_dm1, col_dm2 = st.columns([2, 1])
      with col_dm1:
        mob_para_excluir = st.selectbox(
            "Selecione o ID para Remover do Histórico",
            df_mob_hist["id"].tolist(),
        )
      with col_dm2:
        st.write("")
        st.write("")
        if st.button("🗑️ Excluir Registro de Mobilização"):
          if verificar_licenca_para_acao():
            cursor.execute(
                "DELETE FROM mobilizacoes WHERE id = ?", (mob_para_excluir,)
            )
            conn.commit()
            st.success("✅ Registro removido!")
            st.rerun()

      col_down1, col_down2 = st.columns(2)
      with col_down1:
        pdf_buffer = gerar_pdf_relatorio(
            "HISTÓRICO DE MOBILIZAÇÕES - TABALMIX", df_mob_hist
        )
        st.download_button(
            label="📥 Baixar Histórico em PDF",
            data=pdf_buffer,
            file_name="historico_mobilizacoes_tabalmix.pdf",
            mime="application/pdf",
        )
      with col_down2:
        csv_buffer = gerar_csv_relatorio(df_mob_hist)
        st.download_button(
            label="📊 Baixar Histórico em Planilha (.csv)",
            data=csv_buffer,
            file_name="historico_mobilizacoes_tabalmix.csv",
            mime="text/csv",
        )
    else:
      st.info("Nenhuma mobilização registrada até o momento.")

elif menu == "🛠️ Ordens de Serviço (OS)":
  st.title("🛠️ Gestão de Ordens de Serviço (OS) e Manutenções")

  df_m_resumo = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_m_resumo.empty:
    custo_total_pecas = df_m_resumo["custo_pecas"].sum()
    custo_total_mo = df_m_resumo["mao_de_obra"].sum()
    custo_geral_os = df_m_resumo["custo"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Gasto em Peças", f"R$ {custo_total_pecas:,.2f}")
    m2.metric("Total Mão de Obra", f"R$ {custo_total_mo:,.2f}")
    m3.metric("Custo Geral Manutenção", f"R$ {custo_geral_os:,.2f}")
    st.divider()

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
        problema = st.text_area(
            "Solicitação / Defeito Apresentado / Problema"
        )
        servico_realizado = st.text_area(
            "Serviços a Realizar / Realizados"
        )
      with col2:
        pecas_utilizadas = st.text_input(
            "Peças Utilizadas / Necessárias"
        )
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
                "Aguardando aprovação",
                "Concluída",
                "Cancelada",
            ],
        )
        data_os = st.date_input("Data de Abertura")

      abrir_os = st.form_submit_button(
          "Salvar e Emitir Ordem de Serviço (OS)"
      )
      if abrir_os:
        if verificar_licenca_para_acao():
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
  st.subheader("🖨️ Histórico de Ordens de Serviço & Recibo Oficial")
  df_m = pd.read_sql("SELECT * FROM manutencoes", conn)
  if not df_m.empty:
    st.markdown("##### 📅 Filtrar Ordens de Serviço por Período")
    col_fm1, col_fm2 = st.columns(2)
    with col_fm1:
      usar_filtro_os = st.checkbox(
          "Ativar Filtro de Datas em Ordens de Serviço"
      )
    if usar_filtro_os:
      col_od1, col_od2 = st.columns(2)
      with col_od1:
        os_data_inicio = st.date_input(
            "Início do Período", datetime.now() - timedelta(days=30), key="os_ini"
        )
      with col_od2:
        os_data_fim = st.date_input(
            "Fim do Período", datetime.now(), key="os_fim"
        )

      df_m["data_dt"] = pd.to_datetime(df_m["data"], errors="coerce")
      df_m_filtrado = df_m[
          (df_m["data_dt"].dt.date >= os_data_inicio)
          & (df_m["data_dt"].dt.date <= os_data_fim)
      ]
    else:
      df_m_filtrado = df_m

    st.dataframe(
        df_m_filtrado.drop(columns=["data_dt"], errors="ignore"),
        use_container_width=True,
    )

    custo_periodo_filtrado = df_m_filtrado["custo"].sum()
    st.info(
        f"🛠️ **Custo de Manutenção no Período Selecionado:** R$"
        f" {custo_periodo_filtrado:,.2f}"
    )

    col_os1, col_os2 = st.columns([2, 1])
    with col_os1:
      os_para_excluir = st.selectbox(
          "Selecione o ID da OS para Excluir", df_m["id"].tolist()
      )
    with col_os2:
      st.write("")
      st.write("")
      if st.button("🗑️ Excluir OS Selecionada"):
        if verificar_licenca_para_acao():
          cursor.execute(
              "DELETE FROM manutencoes WHERE id = ?", (os_para_excluir,)
          )
          conn.commit()
          st.success("✅ Ordem de Serviço excluída!")
          st.rerun()

    st.markdown("### Gerar Comprovante / Recibo da OS para Impressão")
    os_ids = df_m["id"].tolist()
    os_selecionada = st.selectbox(
        "Selecione o ID da OS para gerar o documento PDF/HTML", os_ids
    )
    if os_selecionada:
      os_dados = df_m[df_m["id"] == os_selecionada].iloc[0]
      recibo_html = f"""
                <div style="background-color: #ffffff; color: #000000; padding: 30px; border-radius: 10px; font-family: Arial, sans-serif; border: 2px solid #2ecc71;">
                    <h2 style="text-align: center; color: #1b7a3e; margin-bottom: 5px;">TABALMIX CONCRETO - ORDEM DE SERVIÇO #{os_dados['id']}</h2>
                    <p style="text-align: center; color: #555; font-size: 14px;">Controle Oficial de Manutenção e Oficina de Frotas</p>
                    <hr style="border: 1px solid #ccc; margin: 20px 0;">
                    <p><b>Equipamento / Patrimônio:</b> {os_dados['equipamento']}</p>
                    <p><b>Data de Abertura:</b> {os_dados['data']} | <b>Tipo:</b> {os_dados['tipo_manutencao']}</p>
                    <p><b>Status Atual:</b> <span style="color: #1b7a3e; font-weight: bold;">{os_dados['status_os']}</span></p>
                    <p><b>Oficina / Fornecedor:</b> {os_dados['oficina']} | <b>Responsável:</b> {os_dados['responsavel']}</p>
                    <hr style="border: 1px solid #eee; margin: 15px 0;">
                    <p><b>Problema Relatado:</b> {os_dados['problema']}</p>
                    <p><b>Serviços Realizados:</b> {os_dados['servico_realizado']}</p>
                    <p><b>Peças Utilizadas:</b> {os_dados['pecas_utilizadas']}</p>
                    <hr style="border: 1px solid #eee; margin: 15px 0;">
                    <p><b>Custo de Peças:</b> R$ {os_dados['custo_pecas']:,.2f} | <b>Mão de Obra:</b> R$ {os_dados['mao_de_obra']:,.2f}</p>
                    <p style="font-size: 16px; color: #1b7a3e;"><b>Custo Total da Manutenção: R$ {os_dados['custo']:,.2f}</b></p>
                </div>
            """
      st.markdown(recibo_html, unsafe_allow_html=True)
      col_down1, col_down2 = st.columns(2)
      with col_down1:
        st.info(
            "💡 **Dica para imprimir:** Pressione as teclas **Ctrl + P** no"
            " seu teclado."
        )
      with col_down2:
        csv_buffer = gerar_csv_relatorio(pd.DataFrame([os_dados]))
        st.download_button(
            label="📊 Baixar OS em Planilha (.csv)",
            data=csv_buffer,
            file_name=f"ordem_servico_{os_dados['id']}_tabalmix.csv",
            mime="text/csv",
        )
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
        quantidade = st.number_input(
            "Quantidade em Estoque", min_value=1, value=1
        )
        valor_unitario = st.number_input(
            "Valor Unitário (R$)", min_value=0.0, format="%.2f"
        )
      salvar_item = st.form_submit_button("Adicionar ao Estoque")
      if salvar_item:
        if verificar_licenca_para_acao():
          if nome_item:
            cursor.execute(
                "INSERT INTO pecas (nome_item, categoria, quantidade,"
                " valor_unitario) VALUES (?, ?, ?, ?)",
                (nome_item, categoria, quantidade, valor_unitario),
            )
            conn.commit()
            st.success(
                f"✅ Item '{nome_item}' cadastrado com sucesso no estoque!"
            )
          else:
            st.error("⚠️ Informe o nome da peça.")
  with tab2:
    df_p = pd.read_sql("SELECT * FROM pecas", conn)
    if not df_p.empty:
      st.dataframe(df_p, use_container_width=True)
      col_p1, col_p2 = st.columns([2, 1])
      with col_p1:
        peca_para_excluir = st.selectbox(
            "Selecione o ID do Item para Remover", df_p["id"].tolist()
        )
      with col_p2:
        st.write("")
        st.write("")
        if st.button("🗑️ Excluir Item"):
          if verificar_licenca_para_acao():
            cursor.execute(
                "DELETE FROM pecas WHERE id = ?", (peca_para_excluir,)
            )
            conn.commit()
            st.success("✅ Item removido!")
            st.rerun()
      col_down1, col_down2 = st.columns(2)
      with col_down1:
        pdf_buffer = gerar_pdf_relatorio(
            "INVENTÁRIO DE PEÇAS - TABALMIX", df_p
        )
        st.download_button(
            label="📥 Baixar Inventário em PDF",
            data=pdf_buffer,
            file_name="inventario_pecas_tabalmix.pdf",
            mime="application/pdf",
        )
      with col_down2:
        csv_buffer = gerar_csv_relatorio(df_p)
        st.download_button(
            label="📊 Baixar Inventário em Planilha (.csv)",
            data=csv_buffer,
            file_name="inventario_pecas_tabalmix.csv",
            mime="text/csv",
        )
    else:
      st.info("Nenhuma peça cadastrada no estoque.")

elif menu == "👥 Gestão de Clientes":
  st.title("👥 Cadastro de Clientes e Terceiros (Opcional)")
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
      if verificar_licenca_para_acao():
        if nome:
          cursor.execute(
              "INSERT INTO clientes (nome, empresa, telefone, documento, email,"
              " endereco) VALUES (?, ?, ?, ?, ?, ?)",
              (nome, empresa, telefone, documento, email, endereco),
          )
          conn.commit()
          st.success(f"✅ Cliente '{nome}' cadastrado com sucesso!")
        else:
          st.error("⚠️ O nome do cliente é obrigatório.")
  st.divider()
  st.subheader("Base de Clientes Cadastrados")
  df_cli = pd.read_sql("SELECT * FROM clientes", conn)
  if not df_cli.empty:
    st.dataframe(df_cli, use_container_width=True)
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
      cliente_para_excluir = st.selectbox(
          "Selecione o ID do Cliente para Remover", df_cli["id"].tolist()
      )
    with col_c2:
      st.write("")
      st.write("")
      if st.button("🗑️ Excluir Cliente"):
        if verificar_licenca_para_acao():
          cursor.execute(
              "DELETE FROM clientes WHERE id = ?", (cliente_para_excluir,)
          )
          conn.commit()
          st.success("✅ Cliente removido!")
          st.rerun()
      col_down1, col_down2 = st.columns(2)
      with col_down1:
        pdf_buffer = gerar_pdf_relatorio(
            "BASE DE CLIENTES - TABALMIX", df_cli
        )
        st.download_button(
            label="📥 Baixar Lista de Clientes em PDF",
            data=pdf_buffer,
            file_name="lista_clientes_tabalmix.pdf",
            mime="application/pdf",
        )
      with col_down2:
        csv_buffer = gerar_csv_relatorio(df_cli)
        st.download_button(
            label="📊 Baixar Clientes em Planilha (.csv)",
            data=csv_buffer,
            file_name="lista_clientes_tabalmix.csv",
            mime="text/csv",
        )
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
    st.subheader("🚜 Resultados na Frota / Equipamentos")
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

    st.subheader("🛠️ Resultados em Ordens de Serviço (OS)")
    df_b_manut = pd.read_sql(
        "SELECT * FROM manutencoes WHERE id LIKE ? OR equipamento LIKE ? OR"
        " problema LIKE ? OR servico_realizado LIKE ? OR oficina LIKE ?",
        conn,
        params=(termo_like, termo_like, termo_like, termo_like, termo_like),
    )
    if not df_b_manut.empty:
      st.dataframe(df_b_manut, use_container_width=True)
    else:
      st.info("Nenhuma Ordem de Serviço encontrada com este termo.")
  else:
    st.info(
        "👆 Digite um termo no campo acima para iniciar a busca em todo o"
        " sistema da Tabalmix."
    )

elif menu == "⚙️ Painel de Licença (Admin)":
  st.title("⚙️ Painel de Controle de Licença, Planos e Assinaturas")
  st.markdown(
      "Gerencie o status de acesso do sistema e defina o modelo comercial"
      " (Planos Mensal, Trimestral, Semestral ou Anual)."
  )

  with st.form("form_licenca"):
    novo_status = st.selectbox(
        "Status da Licença", ["Ativo", "Bloqueado por Inadimplência"]
    )
    escolha_plano = st.selectbox(
        "Plano Comercial Contratado",
        [
            "Mensal (R$ 250,00)",
            "Trimestral (R$ 700,00)",
            "Semestral (R$ 1.300,00)",
            "Anual (R$ 2.400,00)",
        ],
    )
    nova_chave_pix = st.text_input(
        "Sua Chave Pix (E-mail, CPF ou CNPJ)", value=chave_pix_recebimento
    )
    atualizar_licenca = st.form_submit_button("Salvar Configurações de Licença")
    if atualizar_licenca:
      cursor.execute(
          "UPDATE licenca SET status_assinatura = ?, plano_atual = ?, chave_pix"
          " = ? WHERE id = 1",
          (novo_status, escolha_plano, nova_chave_pix),
      )
      conn.commit()
      st.success("✅ Configurações de licença e planos atualizadas!")
      st.rerun()

  st.divider()
  st.subheader("💳 Área de Pagamento e Checkout Mercado Pago")
  st.write(
      "Caso deseje testar a contratação imediata via Pix/Cartão do Mercado"
      " Pago:"
  )

  col_m1, col_m2 = st.columns(2)
  with col_m1:
    if st.button("Pagar Plano Mensal (R$ 250,00)"):
      try:
        sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
        preference_data = {
            "items": [{
                "title": "Tabalmix Concreto - Mensal",
                "quantity": 1,
                "unit_price": 250.0,
                "currency_id": "BRL",
            }],
            "back_urls": {
                "success": "https://streamlit.io",
                "failure": "https://streamlit.io",
                "pending": "https://streamlit.io",
            },
            "auto_return": "approved",
        }
        preference_response = sdk.preference().create(preference_data)
        checkout_url = (
            preference_response["response"].get("init_point")
            if "response" in preference_response
            else ""
        )
        if checkout_url:
          st.success(f"[Clique aqui para abrir o pagamento]({checkout_url})")
      except Exception as e:
        st.error(f"Erro ao conectar com Mercado Pago: {e}")

  with col_m2:
    if st.button("Pagar Plano Anual (R$ 2.400,00)"):
      try:
        sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
        preference_data = {
            "items": [{
                "title": "Tabalmix Concreto - Anual",
                "quantity": 1,
                "unit_price": 2400.0,
                "currency_id": "BRL",
            }],
            "back_urls": {
                "success": "https://streamlit.io",
                "failure": "https://streamlit.io",
                "pending": "https://streamlit.io",
            },
            "auto_return": "approved",
        }
        preference_response = sdk.preference().create(preference_data)
        checkout_url = (
            preference_response["response"].get("init_point")
            if "response" in preference_response
            else ""
        )
        if checkout_url:
          st.success(f"[Clique aqui para abrir o pagamento]({checkout_url})")
      except Exception as e:
        st.error(f"Erro ao conectar com Mercado Pago: {e}")
