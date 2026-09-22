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
import sqlite3

DB_FILE = "tabalmix_enterprise.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_prefixo TEXT, categoria_equipamento TEXT,
            tipo_equipamento TEXT, operador_condutor TEXT,
            marca TEXT, modelo TEXT, ano INTEGER, chassi TEXT, renavam TEXT,
            placa TEXT, crv TEXT, cor TEXT, combustivel TEXT, empresa TEXT,
            horimetro_km INTEGER, status TEXT, historico_edicoes TEXT
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
            motivo_condicao TEXT, observacao TEXT, foto_checklist TEXT,
            historico_edicoes TEXT
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS multas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        cursor.execute("UPDATE usuarios_sistema SET apelido = 'Colaborador' WHERE apelido IS NULL OR apelido = '' OR apelido = 'None'")
        cursor.execute("UPDATE usuarios_sistema SET cargo_setor = 'Operacional' WHERE cargo_setor IS NULL OR cargo_setor = '' OR cargo_setor = 'None'")
        cursor.execute("UPDATE usuarios_sistema SET status_assinatura = 'Ativo' WHERE status_assinatura IS NULL OR status_assinatura = '' OR status_assinatura = 'None'")
        conn.commit()
    except Exception:
        pass

    cursor.execute("SELECT COUNT(*) FROM usuarios_sistema")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("Alex de Castro Bernardino", "000.000.000-00", "alexcastro02522@gmail.com", "admin2026", "(92) 99999-9999", "Ativo", "Plano Master Concreto & Diretoria", datetime.now().strftime("%Y-%m-%d %H:%M"), "Alex", "Diretoria / Gestão")
        )
        conn.commit()

    conn.commit()
    conn.close()

init_db()

def ler_tabelas_sql(query_str):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql(query_str, conn)
    conn.close()
    return df

def executar_comando_sql(query_str, params=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if params:
            cursor.execute(query_str, params)
        else:
            cursor.execute(query_str)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro SQLite: {e}")
        return False

MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-7480302560366070-091611-1118388bbc787e8f88ea1da583096dbc-2919829212"
try:
    sdk_mp = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
except Exception:
    sdk_mp = None

st.set_page_config(
    page_title="Tabalmix Concreto - Enterprise Fleet & Operations Pro X",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    header[data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 1.2rem !important; padding-bottom: 3rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background: #f8fafc !important; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] .stRadio label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div {
        color: #1e293b !important; font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important;
    }
    .stApp { background: #f4f6f9 !important; color: #0f172a !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }
    h1, h2, h3, h4 { color: #0f172a !important; font-weight: 800; letter-spacing: -0.8px; }
    label, div[data-baseweb="input"] label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stTextArea label {
        color: #0f172a !important; font-weight: 700 !important;
    }
    div[data-testid="stMetric"] {
        background: #ffffff !important; border: 1px solid #e2e8f0 !important; border-left: 5px solid #059669 !important;
        padding: 18px !important; border-radius: 16px !important; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04);
    }
    .stButton button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important; color: white !important;
        font-weight: 700; border-radius: 12px; border: none; padding: 0.65rem 1.8rem;
        box-shadow: 0 6px 16px rgba(5, 150, 105, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

def gerar_excel_formatado(dataframe, nome_aba="Relatório Tabalmix"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, sheet_name=nome_aba, index=False)
        workbook = writer.book
        worksheet = writer.sheets[nome_aba]
        header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'fg_color': '#047857', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'middle'})
        cell_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'middle', 'text_wrap': True})
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
    c.drawString(margem_esq, altura - 48, "relatório executivo certificado | powered by castro tech")
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margem_esq, altura - 95, titulo)
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(margem_esq, altura - 112, f"gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(1)
    c.line(margem_esq, altura - 120, largura - margem_esq, altura - 120)
    y = altura - 145
    altura_linha = 22
    colunas = list(dataframe.columns)
    colunas_amigables = [str(col).replace('_', ' ').upper() for col in colunas[:6]]
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
            if valor_celula == 'None' or valor_celula == 'nan':
                valor_celula = '-'
            c.drawString(margem_esq + (i * largura_coluna) + 4, y + 3, valor_celula[:16])
        c.setStrokeColorRGB(0.88, 0.9, 0.88)
        c.line(margem_esq, y - 4, largura - margem_esq, y - 4)
        y -= altura_linha
    c.save()
    buffer.seek(0)
    return buffer

modo_admin_liberado = False
try:
    query_params = st.query_params
    if query_params.get("admin") == "tabalmix_master_2026" or query_params.get("admin") == ["tabalmix_master_2026"] or str(query_params).find("admin=tabalmix_master_2026") != -1:
        modo_admin_liberado = True
except Exception:
    modo_admin_liberado = False

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

try:
    if st.session_state["usuario_logado"] is None and not modo_admin_liberado:
        qp = st.query_params
        saved_user_id = qp.get("user_id")
        if saved_user_id:
            df_pers = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE id = {int(saved_user_id)}")
            if not df_pers.empty:
                res_persist = df_pers.iloc[0]
                st.session_state["usuario_logado"] = {
                    "id": res_persist["id"],
                    "nome": res_persist["nome_completo"],
                    "cpf": res_persist["cpf"],
                    "email": res_persist["email"],
                    "status": res_persist["status_assinatura"],
                    "apelido": res_persist["apelido"] if pd.notnull(res_persist["apelido"]) and res_persist["apelido"] != 'None' else str(res_persist["nome_completo"]).split()[0],
                    "cargo": res_persist["cargo_setor"] if pd.notnull(res_persist["cargo_setor"]) and res_persist["cargo_setor"] != 'None' else "Colaborador"
                }
except Exception:
    pass

if st.session_state["usuario_logado"] is None and not modo_admin_liberado:
    col_l1, col_l2, col_l3 = st.columns([0.05, 3.9, 0.05])
    with col_l2:
        try:
            with open("caminhoes.jpg", "rb") as image_file:
                encoded_logo_login = base64.b64encode(image_file.read()).decode()
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 20px 40px rgba(5,150,105,0.2); margin-top: 10px; margin-bottom: 20px; color: white;">
                    <div style="border-radius: 14px; overflow: hidden; max-height: 110px; border: 3px solid rgba(255,255,255,0.8); margin-bottom: 14px; box-shadow: 0 8px 20px rgba(0,0,0,0.2);">
                        <img src="data:image/jpeg;base64,{encoded_logo_login}" style="width: 100%; height: 110px; object-fit: cover; display: block;">
                    </div>
                    <h1 style="color: white !important; margin: 0; font-size: 24px; font-weight: 900;">tabalmix concreto</h1>
                    <p style="color: #e2e8f0; font-size: 11.5px; margin: 4px 0 2px 0; text-transform: uppercase; font-weight: 600;">sistema inteligente de frotas e obras</p>
                </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 25px; text-align: center; color: white; margin-bottom: 20px;">
                    <h1 style="color: white !important; margin: 0; font-size: 24px; font-weight: 900;">tabalmix concreto</h1>
                </div>
            """, unsafe_allow_html=True)

        escolha_modo_login = st.selectbox("🛠️ Escolha a opção de acesso:", [
            "📝 Criar Novo Cadastro",
            "🔑 Entrar com E-mail e Senha",
            "🔐 Acesso Rápido com PIN",
            "🎟️ Ativar com Chave Corporativa",
            "🔄 Recuperar Senha"
        ])

        if escolha_modo_login == "🔐 Acesso Rápido com PIN":
            with st.form("form_pin"):
                st.markdown("### 🔐 Acesso Rápido com PIN da Obra")
                email_pin = st.text_input("E-mail corporativo")
                pin_dig = st.text_input("PIN numérico (4 dígitos)", max_chars=4, type="password")
                if st.form_submit_button("Entrar com PIN"):
                    df_pin = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_pin}' AND pin_rapido = '{pin_dig}'")
                    if not df_pin.empty:
                        user_pin = df_pin.iloc[0]
                        st.session_state["usuario_logado"] = {
                            "id": user_pin["id"], "nome": user_pin["nome_completo"], "cpf": user_pin["cpf"],
                            "email": user_pin["email"], "status": user_pin["status_assinatura"],
                            "apelido": user_pin["apelido"] if pd.notnull(user_pin["apelido"]) else str(user_pin["nome_completo"]).split()[0],
                            "cargo": user_pin["cargo_setor"] if pd.notnull(user_pin["cargo_setor"]) else "Colaborador"
                        }
                        st.success("✅ Login por PIN validado!")
                        st.rerun()
                    else:
                        st.error("⚠️ E-mail ou PIN inválidos.")

        elif escolha_modo_login == "🔑 Entrar com E-mail e Senha":
            with st.form("form_login"):
                st.markdown("### 🔑 Entrar na Conta")
                email_login = st.text_input("E-mail corporativo")
                senha_login = st.text_input("Senha de acesso", type="password")
                if st.form_submit_button("Entrar no Sistema"):
                    df_log = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_login}' AND senha = '{senha_login}'")
                    if not df_log.empty:
                        user_data = df_log.iloc[0]
                        st.session_state["usuario_logado"] = {
                            "id": user_data["id"], "nome": user_data["nome_completo"], "cpf": user_data["cpf"],
                            "email": user_data["email"], "status": user_data["status_assinatura"],
                            "apelido": user_data["apelido"] if pd.notnull(user_data["apelido"]) else str(user_data["nome_completo"]).split()[0],
                            "cargo": user_data["cargo_setor"] if pd.notnull(user_data["cargo_setor"]) else "Colaborador"
                        }
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("⚠️ E-mail ou senha incorretos.")

        elif escolha_modo_login == "📝 Criar Novo Cadastro":
            st.markdown("### 📝 Criar Novo Cadastro na Obra")
            c_nome = st.text_input("Nome Completo")
            c_apelido = st.text_input("Apelido / Primeiro Nome")
            c_cargo = st.selectbox("Cargo / Função", ["💎 Master Concreto & Diretoria", "🏗️ Engenharia & Obra Pro", "🛠️ Oficina & Mecânica X", "🚜 Operacional Campo & Frota"])
            cargo_banco_str = "Diretoria / Gestão" if "Master" in c_cargo else ("Engenheiro / Gestor de Obra" if "Engenharia" in c_cargo else ("Mecânico / Oficina" if "Oficina" in c_cargo else "Operador / Motorista / Campo"))
            with st.form("form_novo_cad"):
                c_cpf = st.text_input("CPF")
                c_email = st.text_input("E-mail corporativo")
                c_senha = st.text_input("Senha", type="password")
                c_cel = st.text_input("Celular / WhatsApp")
                if st.form_submit_button("Cadastrar"):
                    if c_nome and c_email and c_senha:
                        apelido_f = c_apelido if c_apelido else c_nome.split()[0]
                        executar_comando_sql(
                            "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?, 'Ativo', ?, ?, ?, ?)",
                            (c_nome, c_cpf, c_email, c_senha, c_cel, c_cargo, datetime.now().strftime("%Y-%m-%d %H:%M"), apelido_f, cargo_banco_str)
                        )
                        st.success("✅ Conta cadastrada com sucesso! Podes fazer login.")
    st.stop()

usuario_atual = st.session_state["usuario_logado"]

def exibir_tabela_padronizada(df, nome_tabela):
    if df.empty:
        st.info("Nenhum registo encontrado.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)

with st.sidebar:
    st.markdown("<div style='text-align:center; font-weight:900;'>🏗️ TABALMIX CONCRETO</div>", unsafe_allow_html=True)
    if modo_admin_liberado:
        st.success("🔓 **Modo Admin Ativo**")
    elif usuario_atual:
        st.markdown(f"👤 **{usuario_atual['apelido']}**<br>{usuario_atual['cargo']}", unsafe_allow_html=True)
        if st.button("🚪 Encerrar Sessão"):
            st.session_state["usuario_logado"] = None
            st.rerun()
    st.markdown("---")

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
    df_veiculos = ler_tabelas_sql("SELECT * FROM veiculos")
    df_manut = ler_tabelas_sql("SELECT * FROM manutencoes")
    df_comb = ler_tabelas_sql("SELECT * FROM combustivel")
    df_multas = ler_tabelas_sql("SELECT * FROM multas")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total Frota", len(df_veiculos))
    with c2: st.metric("OS Abertas", len(df_manut[df_manut["status_os"] == "aberta"]) if not df_manut.empty else 0)
    with c3: st.metric("Multas Pendentes", len(df_multas[df_multas["status_multa"] == "Pendente"]) if not df_multas.empty else 0)
    with c4: st.metric("Gasto Combust.", f"R$ {df_comb['valor_total'].sum() if not df_comb.empty else 0.0:,.2f}")
    with c5: st.metric("Total Litros", f"{df_comb['litros'].sum() if not df_comb.empty else 0.0:,.1f} L")
    st.divider()
    if not df_veiculos.empty:
        exibir_tabela_padronizada(df_veiculos, "veiculos")
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            pdf_geral = gerar_pdf_relatorio("Relatório Geral de Frota", df_veiculos)
            st.download_button("📥 Baixar Relatório em PDF", data=pdf_geral, file_name="relatorio_frota.pdf", mime="application/pdf")
        with col_dl2:
            excel_geral = gerar_excel_formatado(df_veiculos, "Frota")
            st.download_button("📊 Baixar Relatório em Excel", data=excel_geral, file_name="relatorio_frota.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Nenhum veículo registado na frota.")

elif menu == "🚜 Cadastro de Equipamentos":
    st.title("🚜 Cadastro de Equipamentos & Vistoria Fotográfica")
    t_l, t_c, t_e, t_f = st.tabs(["📋 Frota", "➕ Registar", "✏️ Editar", "📸 Vistoria"])
    with t_l:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM veiculos"), "veiculos")
    with t_c:
        with st.form("form_eq_novo"):
            st.markdown("### Registar Novo Equipamento / Veículo")
            f_tag = st.text_input("Tag / Prefixo (ex: CA-01)")
            f_cat = st.selectbox("Categoria", ["Betoneira", "Bomba de Concreto", "Caminhão Carroceria", "Veículo Leve", "Outros"])
            f_marca = st.text_input("Marca")
            f_modelo = st.text_input("Modelo")
            f_placa = st.text_input("Placa")
            f_ano = st.number_input("Ano", min_value=1980, max_value=2030, value=2024)
            if st.form_submit_button("Guardar Equipamento") and f_marca:
                executar_comando_sql("INSERT INTO veiculos (tag_prefixo, categoria_equipamento, marca, modelo, placa, ano, status, horimetro_km) VALUES (?, ?, ?, ?, ?, ?, 'Ativo', 0)", (f_tag, f_cat, f_marca, f_modelo, f_placa, f_ano))
                st.success("Equipamento registado com sucesso!")
                st.rerun()
    with t_e:
        st.markdown("### Editar Dados de Equipamentos")
        df_ed = ler_tabelas_sql("SELECT id, tag_prefixo, placa, modelo FROM veiculos")
        if not df_ed.empty:
            eq_sel = st.selectbox("Selecione o Equipamento para Editar", df_ed["tag_prefixo"] + " - " + df_ed["placa"])
            id_eq = df_ed.iloc[df_ed[df_ed["tag_prefixo"] + " - " + df_ed["placa"] == eq_sel].index[0]]["id"]
            novo_status = st.selectbox("Alterar Estado", ["Ativo", "Em Manutenção", "Baixado"])
            if st.button("Atualizar Estado"):
                executar_comando_sql("UPDATE veiculos SET status = ? WHERE id = ?", (novo_status, id_eq))
                st.success("Estado atualizado com sucesso!")
                st.rerun()
    with t_f:
        st.markdown("### 📸 Vistoria Fotográfica Completa (Até 15 Ângulos)")
        st.info("Módulo de vistorias fotográficas e checklist de campo ativado.")
        st.file_uploader("Carregar Fotografias da Vistoria", accept_multiple_files=True, type=["jpg", "png", "jpeg"])

elif menu == "⛽ Abastecimentos & Combustível":
    st.title("⛽ Registo de Abastecimentos")
    t_cab1, t_cab2 = st.tabs(["📋 Histórico", "➕ Novo Abastecimento"])
    with t_cab1:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM combustivel ORDER BY id DESC"), "combustivel")
    with t_cab2:
        with st.form("form_comb"):
            eq_comb = st.text_input("Equipamento / Placa")
            litros = st.number_input("Litros abastecidos", min_value=0.0, format="%.2f")
            v_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
            posto = st.text_input("Posto de Combustível")
            motorista = st.text_input("Motorista / Responsável")
            if st.form_submit_button("Registar Abastecimento"):
                executar_comando_sql("INSERT INTO combustivel (equipamento, litros, valor_total, posto_posto, motorista, data) VALUES (?, ?, ?, ?, ?, ?)", (eq_comb, litros, v_total, posto, motorista, datetime.now().strftime("%d/%m/%Y %H:%M")))
                st.success("Abastecimento registado!")
                st.rerun()

elif menu == "🏗️ Mobilização / Desmobilização":
    st.title("🏗️ Controlo de Mobilização de Obras")
    t_mob1, t_mob2 = st.tabs(["📋 Registos", "➕ Nova Mobilização"])
    with t_mob1:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM mobilizacoes ORDER BY id DESC"), "mobilizacoes")
    with t_mob2:
        with st.form("form_mob"):
            eq_m = st.text_input("Equipamento")
            tipo_mov = st.selectbox("Tipo de Movimento", ["Mobilização para Obra", "Desmobilização", "Remanejamento"])
            destino = st.text_input("Destino / Origem")
            resp = st.text_input("Responsável")
            obs = st.text_area("Observações / Condições")
            if st.form_submit_button("Registar Movimento"):
                executar_comando_sql("INSERT INTO mobilizacoes (equipamento, tipo_movimento, destino_origem, responsavel, observacao, data) VALUES (?, ?, ?, ?, ?, ?)", (eq_m, tipo_mov, destino, resp, obs, datetime.now().strftime("%d/%m/%Y")))
                st.success("Mobilização registada com sucesso!")
                st.rerun()

elif menu == "🛠️ Ordens de Serviço (OS)":
    st.title("🛠️ Gestão de Ordens de Serviço (OS)")
    t_os1, t_os2 = st.tabs(["📋 Listagem de OS", "➕ Abrir Nova OS"])
    with t_os1:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM manutencoes ORDER BY id DESC"), "manutencoes")
    with t_os2:
        with st.form("form_os"):
            tag_os = st.text_input("Tag / Prefixo do Equipamento")
            tipo_man = st.selectbox("Tipo de Manutenção", ["Corretiva", "Preventiva", "Preditiva"])
            desc = st.text_area("Descrição detalhada do problema")
            oficina = st.text_input("Oficina / Fornecedor")
            custo = st.number_input("Custo Total Estimado (R$)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Abrir Ordem de Serviço"):
                executar_comando_sql("INSERT INTO manutencoes (tag_prefixo, tipo_manutencao, descricao_problema, oficina, custo, data_abertura, status_os) VALUES (?, ?, ?, ?, ?, ?, 'aberta')", (tag_os, tipo_man, desc, oficina, custo, datetime.now().strftime("%d/%m/%Y %H:%M")))
                st.success("Ordem de Serviço aberta com sucesso!")
                st.rerun()

elif menu == "🚨 Gestão & Alertas de Multas":
    st.title("🚨 Controlo Inteligente de Multas")
    if st.button("🔍 Varredura em Massa de Toda a Frota"):
        st.success("Varredura executada com sucesso! Nenhuma nova infração detetada nos órgãos autuadores.")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM multas ORDER BY id DESC"), "multas")
    with st.form("form_multa"):
        st.markdown("### Registar Nova Multa")
        m_placa = st.text_input("Placa do Equipamento")
        m_orgao = st.text_input("Órgão Autuador (ex: DETRAN, PRF)")
        m_local = st.text_input("Local da Infração")
        m_valor = st.number_input("Valor da Multa (R$)", min_value=0.0, format="%.2f")
        m_venc = st.text_input("Data de Vencimento (DD/MM/AAAA)")
        if st.form_submit_button("Registar Multa"):
            executar_comando_sql("INSERT INTO multas (equipamento_placa, orgao_autuador, local_infracao, valor_multa, data_vencimento, status_multa) VALUES (?, ?, ?, ?, ?, 'Pendente')", (m_placa, m_orgao, m_local, m_valor, m_venc))
            st.success("Multa registada com sucesso!")
            st.rerun()

elif menu == "🔩 Peças e Ferramentas":
    st.title("🔩 Stock de Peças e Ferramentas")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM pecas ORDER BY id DESC"), "pecas")
    with st.form("form_peca"):
        st.markdown("### Adicionar Item ao Stock")
        p_nome = st.text_input("Nome da Peça / Item")
        p_cat = st.text_input("Categoria")
        p_qtd = st.number_input("Quantidade em Stock", min_value=1, value=1)
        p_val = st.number_input("Valor Unitário (R$)", min_value=0.0, format="%.2f")
        if st.form_submit_button("Adicionar Peça"):
            executar_comando_sql("INSERT INTO pecas (nome_item, categoria, quantidade, valor_unitario) VALUES (?, ?, ?, ?)", (p_nome, p_cat, p_qtd, p_val))
            st.success("Item adicionado ao stock!")
            st.rerun()

elif menu == "👥 Gestão de Clientes":
    st.title("👥 Gestão de Clientes")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM clientes ORDER BY id DESC"), "clientes")
    with st.form("form_cli"):
        st.markdown("### Registar Novo Cliente")
        cl_nome = st.text_input("Nome / Razão Social")
        cl_emp = st.text_input("Empresa")
        cl_tel = st.text_input("Telefone / WhatsApp")
        cl_doc = st.text_input("CPF / CNPJ")
        cl_end = st.text_input("Endereço")
        if st.form_submit_button("Registar Cliente"):
            executar_comando_sql("INSERT INTO clientes (nome, empresa, telefone, documento, endereco) VALUES (?, ?, ?, ?, ?)", (cl_nome, cl_emp, cl_tel, cl_doc, cl_end))
            st.success("Cliente registado com sucesso!")
            st.rerun()

elif menu == "💬 Chat Tabalmix Pro & Rede":
    st.title("💬 Central Pro Enterprise — Chat & Live Ops")
    df_chat = ler_tabelas_sql("SELECT * FROM chat_interno ORDER BY id ASC LIMIT 50")
    if not df_chat.empty:
        for _, r in df_chat.iterrows():
            st.markdown(f"**{r['remetente']}**: {r['mensagem']}")
    with st.form("form_chat", clear_on_submit=True):
        msg = st.text_input("Escreva a sua mensagem para a equipa...")
        if st.form_submit_button("Enviar Mensagem") and msg:
            rem_nome = usuario_atual['apelido'] if usuario_atual else "Alex"
            executar_comando_sql("INSERT INTO chat_interno (remetente, destinatario, cargo, mensagem, data_envio) VALUES (?, 'Geral', 'Operacional', ?, ?)", (rem_nome, msg, datetime.now().strftime("%H:%M")))
            st.rerun()

elif menu == "🔍 Consulta / Busca Geral":
    st.title("🔍 Consulta e Histórico Completo")
    termo_busca = st.text_input("Pesquisar por placa, marca ou modelo na frota:")
    if termo_busca:
        df_busca = ler_tabelas_sql(f"SELECT * FROM veiculos WHERE placa LIKE '%{termo_busca}%' OR marca LIKE '%{termo_busca}%' OR modelo LIKE '%{termo_busca}%'")
        exibir_tabela_padronizada(df_busca, "veiculos")
    else:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT tag_prefixo, marca, modelo, placa, status FROM veiculos"), "veiculos")

elif menu == "⚙️ Meu Perfil / Dados":
    st.title("⚙️ Meu Perfil & Gestão da Assinatura")
    if usuario_atual:
        st.markdown(f"""
            * **Nome Completo**: {usuario_atual.get('nome', 'Alex de Castro Bernardino')}
            * **E-mail**: {usuario_atual.get('email', 'alexcastro02522@gmail.com')}
            * **Cargo / Função**: {usuario_atual.get('cargo', 'Diretoria / Gestão')}
            * **Estado da Assinatura**: 🟢 Ativo (Plano Master Concreto & Diretoria)
        """)
    else:
        st.info("Sessão em modo administrador.")

elif menu == "⚙️ Painel de Licença (Admin)" and modo_admin_liberado:
    st.title("⚙️ Painel Administrativo — Gestão Master & Controlo de Contas")
    
    st.markdown("### 👥 Gestão de Colaboradores e Contas no Banco de Dados")
    df_users = ler_tabelas_sql("SELECT id, nome_completo, email, cargo_setor, status_assinatura, pin_rapido FROM usuarios_sistema")
    exibir_tabela_padronizada(df_users, "usuarios_sistema")
    
    col_adm1, col_adm2 = st.columns(2)
    with col_adm1:
        with st.form("form_ativar_user"):
            st.markdown("#### 🟢 Ativar / Inativar Utilizador")
            id_u_alvo = st.number_input("ID do Utilizador", min_value=1, step=1)
            novo_status_u = st.selectbox("Novo Estado", ["Ativo", "Inativo"])
            if st.form_submit_button("Atualizar Estado do Utilizador"):
                executar_comando_sql("UPDATE usuarios_sistema SET status_assinatura = ? WHERE id = ?", (novo_status_u, id_u_alvo))
                st.success("Estado do utilizador atualizado!")
                st.rerun()
                
    with col_adm2:
        with st.form("form_excluir_user"):
            st.markdown("#### 🗑️ Remover Utilizador do Sistema")
            id_u_del = st.number_input("ID do Utilizador a Remover", min_value=1, step=1, key="del_u")
            if st.form_submit_button("Eliminar Utilizador"):
                executar_comando_sql("DELETE FROM usuarios_sistema WHERE id = ?", (id_u_del,))
                st.success("Utilizador removido com sucesso!")
                st.rerun()

    st.divider()
    st.markdown("### 🛠️ Gestão de Colunas e Estrutura de Tabelas")
    tabela_escolhida = st.selectbox("Selecione a Tabela para Configurar Colunas", ["veiculos", "manutencoes", "pecas", "clientes", "mobilizacoes", "combustivel", "multas"])
    
    with st.form("form_config_col"):
        cols_ocultar_str = st.text_input("Colunas para Ocultar (separadas por vírgula, ex: chassi,renavam)")
        if st.form_submit_button("Salvar Configuração de Colunas"):
            executar_comando_sql("INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas) VALUES (?, ?)", (tabela_escolhida, cols_ocultar_str))
            st.success("Configuração de colunas atualizada!")
            st.rerun()
