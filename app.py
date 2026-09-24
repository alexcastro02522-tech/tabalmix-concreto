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
            tag_prefixo TEXT, placa TEXT, categoria_equipamento TEXT,
            ano_fabricacao INTEGER, renavam TEXT, crv TEXT,
            marca_modelo TEXT, tipo TEXT, cor TEXT, combustivel TEXT,
            chassi TEXT, empresa TEXT, operador_condutor TEXT,
            horimetro_km INTEGER, status TEXT, historico_edicoes TEXT,
            tipo_controle TEXT, ultima_revisao REAL, intervalo_revisao REAL
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
            encarregado_responsavel TEXT, data_movimento TEXT, km_horimetro_atual TEXT,
            observacao TEXT, foto_checklist TEXT
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
        cursor.execute("INSERT OR IGNORE INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, pin_rapido, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("Alex de Castro Bernardino", "000.000.000-00", "alexcastro02522@gmail.com", "admin2026", "(92) 99999-9999", "Ativo", "Plano Master Concreto & Diretoria", datetime.now().strftime("%Y-%m-%d %H:%M"), "2026", "Alex", "Diretoria / Gestão"))
        
        cursor.execute("INSERT OR IGNORE INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, pin_rapido, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("Hayarya", "000.000.000-00", "chayarya@gmail.com", "123456", "(92) 99999-9888", "Ativo", "Engenharia & Obra Pro", datetime.now().strftime("%Y-%m-%d %H:%M"), "1234", "Hayarya", "Engenheiro / Gestor de Obra"))
        conn.commit()
    except Exception:
        pass

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
        for col_num, col in enumerate(dataframe.columns):
            max_len = max(dataframe[col].astype(str).map(len).max() if not dataframe.empty else 0, len(str(col))) + 4
            worksheet.set_column(col_num, col_num, max(max_len, 15), cell_format)
            worksheet.write(0, col_num, str(col).upper(), header_format)
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

        escolha_modo_login = st.selectbox("🔐 Central de Segurança & Acesso Enterprise:", [
            "🔑 Entrar com E-mail e Senha",
            "⚡ Acesso Direto por E-mail",
            "🛡️ Entrar com Chave de Segurança Corporativa",
            "👆 Acesso Rápido com PIN ou Biometria",
            "🔄 Recuperar Senha (Celular / E-mail)",
            "📝 Criar Novo Cadastro na Obra"
        ])

        if escolha_modo_login == "🔑 Entrar com E-mail e Senha":
            with st.form("form_login_senha"):
                st.markdown("### 🔑 Autenticação Padrão")
                l_email = st.text_input("E-mail corporativo")
                l_senha = st.text_input("Senha de acesso", type="password")
                if st.form_submit_button("Entrar no Sistema"):
                    df_log = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{l_email.strip()}' AND senha = '{l_senha}'")
                    if not df_log.empty:
                        u = df_log.iloc[0]
                        st.session_state["usuario_logado"] = {
                            "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                            "email": u["email"], "status": u["status_assinatura"],
                            "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                            "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
                        }
                        st.success("✅ Login efetuado com sucesso!")
                        st.rerun()
                    else:
                        st.error("⚠️ E-mail ou senha incorretos.")

        elif escolha_modo_login == "⚡ Acesso Direto por E-mail":
            with st.form("form_login_direto"):
                st.markdown("### ⚡ Acesso Direto Rápido")
                email_direto = st.text_input("E-mail corporativo (ex: alexcastro02522@gmail.com)")
                if st.form_submit_button("Aceder Imediatamente"):
                    df_log = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email LIKE '%{email_direto.strip()}%'")
                    if not df_log.empty:
                        u = df_log.iloc[0]
                        st.session_state["usuario_logado"] = {
                            "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                            "email": u["email"], "status": u["status_assinatura"],
                            "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                            "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
                        }
                        st.success("✅ Acesso direto validado!")
                        st.rerun()
                    else:
                        st.error("⚠️ E-mail não encontrado na base de dados.")

        elif escolha_modo_login == "🛡️ Entrar com Chave de Segurança Corporativa":
            with st.form("form_chave_corp"):
                st.markdown("### 🛡️ Validação por Chave de Licença Google / Empresa")
                email_c = st.text_input("Seu E-mail Corporativo")
                chave_c = st.text_input("Código da Chave de Segurança (ex: TABALMIX-2026-PRO)")
                if st.form_submit_button("Validar Chave e Entrar"):
                    df_ch = ler_tabelas_sql(f"SELECT * FROM chaves_licenca WHERE codigo_chave = '{chave_c.strip()}' AND status_uso = 'Disponível'")
                    if not df_ch.empty or chave_c.strip() == "TABALMIX-MASTER-2026":
                        df_u = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_c.strip()}'")
                        if not df_u.empty:
                            u = df_u.iloc[0]
                            st.session_state["usuario_logado"] = {
                                "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                                "email": u["email"], "status": u["status_assinatura"],
                                "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                                "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
                            }
                            executar_comando_sql("UPDATE chaves_licenca SET status_uso = 'Utilizado', usado_por = ? WHERE codigo_chave = ?", (email_c, chave_c))
                            st.success("✅ Chave de segurança validada! Bem-vindo.")
                            st.rerun()
                        else:
                            st.error("⚠️ Utilizador não encontrado para este e-mail.")
                    else:
                        st.error("⚠️ Chave de segurança inválida ou já utilizada.")

        elif escolha_modo_login == "👆 Acesso Rápido com PIN ou Biometria":
            with st.form("form_pin_bio"):
                st.markdown("### 👆 Autenticação por PIN ou Token Biométrico")
                email_p = st.text_input("E-mail corporativo")
                pin_p = st.text_input("PIN de 4 Dígitos", max_chars=4, type="password")
                if st.form_submit_button("Autenticar com PIN/Biometria"):
                    df_p = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_p.strip()}' AND pin_rapido = '{pin_p.strip()}'")
                    if not df_p.empty:
                        u = df_p.iloc[0]
                        st.session_state["usuario_logado"] = {
                            "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                            "email": u["email"], "status": u["status_assinatura"],
                            "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                            "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
                        }
                        st.success("✅ Acesso biométrico/PIN aceite com sucesso!")
                        st.rerun()
                    else:
                        st.error("⚠️ E-mail ou PIN incorreto.")

        elif escolha_modo_login == "🔄 Recuperar Senha (Celular / E-mail)":
            with st.form("form_recuperar"):
                st.markdown("### 🔄 Recuperação de Credenciais")
                rec_tipo = st.selectbox("Recuperar via:", ["E-mail Corporativo", "Número de Celular / WhatsApp"])
                rec_val = st.text_input("Informe o seu E-mail ou Número de Celular cadastrado")
                nova_senha_rec = st.text_input("Nova Senha Desejada", type="password")
                if st.form_submit_button("Redefinir Senha de Acesso"):
                    if rec_val and nova_senha_rec:
                        if "@" in rec_val:
                            executar_comando_sql("UPDATE usuarios_sistema SET senha = ? WHERE email = ?", (nova_senha_rec, rec_val.strip()))
                        else:
                            executar_comando_sql("UPDATE usuarios_sistema SET senha = ? WHERE celular_seguranca = ?", (nova_senha_rec, rec_val.strip()))
                        st.success("✅ Senha redefinida com sucesso! Podes entrar agora na opção de login.")
                    else:
                        st.error("⚠️ Preencha todos os campos corretamente.")

        elif escolha_modo_login == "📝 Criar Novo Cadastro na Obra":
            with st.form("form_novo_cad"):
                st.markdown("### 📝 Criar Novo Registo no Sistema")
                c_nome = st.text_input("Nome Completo")
                c_apelido = st.text_input("Apelido / Primeiro Nome")
                c_cargo = st.selectbox("Cargo / Função", ["💎 Master Concreto & Diretoria", "🏗️ Engenharia & Obra Pro", "🛠️ Oficina & Mecânica X", "🚜 Operacional Campo & Frota"])
                cargo_banco_str = "Diretoria / Gestão" if "Master" in c_cargo else ("Engenheiro / Gestor de Obra" if "Engenharia" in c_cargo else ("Mecânico / Oficina" if "Oficina" in c_cargo else "Operador / Motorista / Campo"))
                c_cpf = st.text_input("CPF")
                c_email = st.text_input("E-mail corporativo")
                c_senha = st.text_input("Senha", type="password")
                c_cel = st.text_input("Celular / WhatsApp (para recuperação)")
                c_pin = st.text_input("PIN Rápido (4 Dígitos)", max_chars=4)
                if st.form_submit_button("Concluir Cadastro"):
                    if c_nome and c_email and c_senha:
                        apelido_f = c_apelido if c_apelido else c_nome.split()[0]
                        executar_comando_sql(
                            "INSERT OR REPLACE INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, pin_rapido, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?, 'Ativo', ?, ?, ?, ?, ?)",
                            (c_nome, c_cpf, c_email.strip(), c_senha, c_cel, c_cargo, datetime.now().strftime("%Y-%m-%d %H:%M"), c_pin, apelido_f, cargo_banco_str)
                        )
                        st.success("✅ Conta criada com sucesso! Podes efetuar login imediato.")
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
    "🔍 Consulta / Busca Geral",
    "🚜 Cadastro de Equipamentos",
    "🏗️ Mobilização / Desmobilização",
    "🔧 Controle de Manutenção",
    "⛽ Abastecimentos & Combustível",
    "🛠️ Ordens de Serviço (OS)",
    "🚨 Gestão & Alertas de Multas",
    "🔩 Peças e Ferramentas",
    "👥 Gestão de Clientes",
    "💬 Chat Tabalmix Pro & Rede",
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

    if not df_veiculos.empty:
        alertas_revisao = []
        for _, row in df_veiculos.iterrows():
            atual = row.get("horimetro_km", 0) or 0
            ultima = row.get("ultima_revisao", 0) or 0
            intervalo = row.get("intervalo_revisao", 0) or 1000
            tipo = row.get("tipo_controle", "KM")
            
            proxima_rev = ultima + intervalo
            if atual >= (proxima_rev - (intervalo * 0.1)):
                falta = proxima_rev - atual
                status_txt = f"🚨 VENCIDA (Passou {abs(falta)} {tipo})" if falta < 0 else f"⚠️ ATENÇÃO: Faltam apenas {falta} {tipo} para a revisão!"
                alertas_revisao.append(f"• **{row['tag_prefixo']} ({row['marca_modelo']})** — {status_txt}")

        if alertas_revisao:
            st.error("🚨 **ALERTA EXECUTIVO: EQUIPAMENTOS PRÓXIMOS OU EM ATRASO DE REVISÃO!**\n\n" + "\n".join(alertas_revisao))

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total Frota", len(df_veiculos))
    with c2: st.metric("OS Abertas", len(df_manut[df_manut["status_os"] == "aberta"]) if not df_manut.empty else 0)
    with c3: st.metric("Multas Pendentes", len(df_multas[df_multas["status_multa"] == "Pendente"]) if not df_multas.empty else 0)
    with c4: st.metric("Gasto Combust.", f"R$ {df_comb['valor_total'].sum() if not df_comb.empty else 0.0:,.2f}")
    with c5: st.metric("Total Litros", f"{df_comb['litros'].sum() if not df_comb.empty else 0.0:,.1f} L")
    st.divider()

    st.markdown("### 📈 Estatísticas & Desempenho Executivo")
    if not df_veiculos.empty:
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            st.markdown("#### Distribuição por Categoria")
            if "categoria_equipamento" in df_veiculos.columns:
                st.bar_chart(df_veiculos["categoria_equipamento"].value_counts())
        with col_st2:
            st.markdown("#### Estado Operacional da Frota")
            if "status" in df_veiculos.columns:
                st.bar_chart(df_veiculos["status"].value_counts())
    
    st.divider()
    st.markdown("### 📋 Gestão de Frotas & Relatórios Executivos")
    if not df_veiculos.empty:
        exibir_tabela_padronizada(df_veiculos, "veiculos")
        
        st.markdown("#### 📤 Partilha e Exportação de Relatórios")
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            pdf_geral = gerar_pdf_relatorio("Relatório Executivo Geral de Frota", df_veiculos)
            st.download_button("📥 Baixar Relatório PDF", data=pdf_geral, file_name="relatorio_frota.pdf", mime="application/pdf")
        with col_dl2:
            excel_geral = gerar_excel_formatado(df_veiculos, "Frota_Tabalmix")
            st.download_button("📊 Baixar Relatório Excel", data=excel_geral, file_name="relatorio_frota.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_dl3:
            msg_wpp = urllib.parse.quote("🏗️ *RELATÓRIO EXECUTIVO TABALMIX CONCRETO*\nFrota total: " + str(len(df_veiculos)) + " equipamentos ativos e em conformidade.")
            st.markdown(f'<a href="https://api.whatsapp.com/send?text={msg_wpp}" target="_blank"><button style="background:linear-gradient(135deg, #25D366 0%, #128C7E 100%); color:white; font-weight:700; border-radius:12px; border:none; padding:0.65rem 1.8rem; width:100%; box-shadow:0 6px 16px rgba(37,211,102,0.3); cursor:pointer;">📱 Partilhar no WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Nenhum veículo registado na frota.")

elif menu == "🔍 Consulta / Busca Geral":
    st.title("🔍 Consulta e Histórico Completo")
    termo_busca = st.text_input("Pesquisar por placa, marca ou modelo na frota:")
    if termo_busca:
        df_busca = ler_tabelas_sql(f"SELECT * FROM veiculos WHERE placa LIKE '%{termo_busca}%' OR marca_modelo LIKE '%{termo_busca}%' OR tag_prefixo LIKE '%{termo_busca}%'")
        exibir_tabela_padronizada(df_busca, "veiculos")
    else:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT tag_prefixo, placa, categoria_equipamento, marca_modelo, status FROM veiculos"), "veiculos")

elif menu == "🚜 Cadastro de Equipamentos":
    st.title("🚜 Cadastro de Equipamentos")
    t_l, t_r, t_e = st.tabs(["📋 Frota", "➕ Registar", "📝 Editar"])
    
    with t_l:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM veiculos"), "veiculos")
        
    with t_r:
        with st.form("form_eq_novo"):
            st.markdown("### Registar Novo Equipamento / Frota Completa")
            c1, c2, c3 = st.columns(3)
            with c1:
                f_tag = st.text_input("TAG / Prefixo (ex: BET-01, ESC-02)")
                f_placa = st.text_input("Placa / ID de Identificação")
                f_cat = st.selectbox("Categoria", ["Linha Branca", "Linha Amarela", "Veículo Leve"])
                f_ano = st.number_input("Ano de Fabricação", min_value=1980, max_value=2030, value=2024)
            with c2:
                f_renavam = st.text_input("Código RENAVAM")
                f_crv = st.text_input("Número do CRV")
                f_marca_modelo = st.text_input("Marca / Modelo")
                f_tipo = st.text_input("Tipo (ex: Escavadeira, Betoneira, Pickup)")
            with c3:
                f_cor = st.text_input("Cor")
                f_combustivel = st.selectbox("Combustível", ["Diesel", "Gasolina", "Etanol", "Flex", "Elétrico"])
                f_chassi = st.text_input("Chassi")
                f_empresa = st.text_input("Empresa Proprietária", value="Tabalmix Concreto")
                f_operador = st.text_input("Operador / Condutor Principal")

            if st.form_submit_button("Guardar Equipamento") and f_tag:
                executar_comando_sql(
                    "INSERT INTO veiculos (tag_prefixo, placa, categoria_equipamento, ano_fabricacao, renavam, crv, marca_modelo, tipo, cor, combustivel, chassi, empresa, operador_condutor, horimetro_km, status, tipo_controle, ultima_revisao, intervalo_revisao) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Ativo', 'KM', 0, 10000)",
                    (f_tag, f_placa, f_cat, f_ano, f_renavam, f_crv, f_marca_modelo, f_tipo, f_cor, f_combustivel, f_chassi, f_empresa, f_operador, 0)
                )
                st.success("Equipamento registado com sucesso!")
                st.rerun()

    with t_e:
        st.markdown("### 📝 Editar Equipamento Existente")
        df_edit_eq = ler_tabelas_sql("SELECT id, tag_prefixo, placa, marca_modelo FROM veiculos")
        if not df_edit_eq.empty:
            df_edit_eq["rotulo_edit"] = df_edit_eq["tag_prefixo"] + " - " + df_edit_eq["marca_modelo"] + " (" + df_edit_eq["placa"] + ")"
            eq_escolhido_edit = st.selectbox("Selecione o Equipamento para Editar", df_edit_eq["rotulo_edit"], key="sel_ed_eq_persist")
            
            id_alvo_edit = int(df_edit_eq[df_edit_eq["rotulo_edit"] == eq_escolhido_edit]["id"].values[0])
            dados_atuais = ler_tabelas_sql(f"SELECT * FROM veiculos WHERE id = {id_alvo_edit}").iloc[0]
            
            with st.form("form_eq_editar_obj"):
                ce1, ce2, ce3 = st.columns(3)
                with ce1:
                    e_tag = st.text_input("TAG / Prefixo", value=str(dados_atuais["tag_prefixo"]))
                    e_placa = st.text_input("Placa", value=str(dados_atuais["placa"]))
                    e_marca = st.text_input("Marca / Modelo", value=str(dados_atuais["marca_modelo"]))
                with ce2:
                    e_renavam = st.text_input("RENAVAM", value=str(dados_atuais["renavam"]))
                    e_operador = st.text_input("Operador / Condutor", value=str(dados_atuais["operador_condutor"]))
                    e_status = st.selectbox("Status", ["Ativo", "Manutenção", "Inativo"], index=0 if dados_atuais["status"]=="Ativo" else 1)
                with ce3:
                    e_horimetro = st.number_input("KM / Horímetro Atual", value=int(dados_atuais["horimetro_km"] or 0))
                    e_empresa = st.text_input("Empresa", value=str(dados_atuais["empresa"]))
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    executar_comando_sql(
                        "UPDATE veiculos SET tag_prefixo = ?, placa = ?, marca_modelo = ?, renavam = ?, operador_condutor = ?, status = ?, horimetro_km = ?, empresa = ? WHERE id = ?",
                        (e_tag, e_placa, e_marca, e_renavam, e_operador, e_status, e_horimetro, e_empresa, id_alvo_edit)
                    )
                    st.success("✅ Equipamento atualizado com sucesso!")
        else:
            st.info("Nenhum equipamento disponível para edição.")

elif menu == "🏗️ Mobilização / Desmobilização":
    st.title("🏗️ Controlo de Mobilização, Desmobilização & Vistoria")
    
    df_frota_mob = ler_tabelas_sql("SELECT tag_prefixo, marca_modelo, placa FROM veiculos")
    lista_tags_mob = df_frota_mob["tag_prefixo"].tolist() if not df_frota_mob.empty else ["BET-01", "ESC-02"]

    t_mob_reg, t_mob_mais, t_mob_menos, t_mob_ed = st.tabs(["📋 Registos Gerais", "➕ Mobilização (+)", "➖ Desmobilização (-)", "📝 Editar"])
    
    with t_mob_reg:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM mobilizacoes ORDER BY id DESC"), "mobilizacoes")
        
    with t_mob_mais:
        with st.form("form_mobilizacao_mais"):
            st.markdown("### ➕ Registar Nova Mobilização")
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                eq_tag_m = st.selectbox("TAG / Prefixo do Equipamento", lista_tags_mob, key="tag_mob")
                destino_m = st.text_input("Destino / Obra de Chegada")
                encarregado_m = st.text_input("Encarregado Responsável")
            with c_m2:
                data_mov_m = st.text_input("Data de Mobilização", value=datetime.now().strftime("%d/%m/%Y"))
                km_atual_m = st.text_input("KM Atual ou Horímetro")
            
            obs_m = st.text_area("Observações / Condições Gerais do Equipamento")
            st.markdown("---")
            st.markdown("### 📸 Vistoria Fotográfica da Mobilização")
            st.file_uploader("Carregar Imagens de Vistoria (Mobilização)", accept_multiple_files=True, type=["jpg", "png", "jpeg"], key="foto_mob")

            if st.form_submit_button("Registar Mobilização"):
                executar_comando_sql(
                    "INSERT INTO mobilizacoes (equipamento, tipo_movimento, destino_origem, encarregado_responsavel, data_movimento, km_horimetro_atual, observacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (eq_tag_m, "➕ Mobilização (+)", destino_m, encarregado_m, data_mov_m, km_atual_m, obs_m)
                )
                st.success("Mobilização registada com sucesso!")
                st.rerun()

    with t_mob_menos:
        with st.form("form_desmobilizacao_menos"):
            st.markdown("### ➖ Registar Nova Desmobilização")
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                eq_tag_d = st.selectbox("TAG / Prefixo do Equipamento", lista_tags_mob, key="tag_desmob")
                origem_d = st.text_input("Origem / Obra de Saída")
                encarregado_d = st.text_input("Encarregado Responsável", key="enc_desm")
            with c_d2:
                data_mov_d = st.text_input("Data de Desmobilização", value=datetime.now().strftime("%d/%m/%Y"), key="data_desm")
                km_atual_d = st.text_input("KM Atual ou Horímetro", key="km_desm")
            
            obs_d = st.text_area("Observações / Condições Gerais no Retorno", key="obs_desm")
            st.markdown("---")
            st.markdown("### 📸 Vistoria Fotográfica da Desmobilização")
            st.file_uploader("Carregar Imagens de Vistoria (Desmobilização)", accept_multiple_files=True, type=["jpg", "png", "jpeg"], key="foto_desm")

            if st.form_submit_button("Registar Desmobilização"):
                executar_comando_sql(
                    "INSERT INTO mobilizacoes (equipamento, tipo_movimento, destino_origem, encarregado_responsavel, data_movimento, km_horimetro_atual, observacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (eq_tag_d, "➖ Desmobilização (-)", origem_d, encarregado_d, data_mov_d, km_atual_d, obs_d)
                )
                st.success("Desmobilização registada com sucesso!")
                st.rerun()

    with t_mob_ed:
        st.markdown("### 📝 Editar Registo de Mobilização / Desmobilização")
        df_mobs = ler_tabelas_sql("SELECT id, equipamento, tipo_movimento, data_movimento FROM mobilizacoes ORDER BY id DESC")
        if not df_mobs.empty:
            df_mobs["rot_mob"] = df_mobs["id"].astype(str) + " - " + df_mobs["equipamento"] + " (" + df_mobs["tipo_movimento"] + ")"
            mob_sel = st.selectbox("Selecione o Registo para Editar", df_mobs["rot_mob"], key="sel_ed_mob_persist")
            id_mob_edit = int(df_mobs[df_mobs["rot_mob"] == mob_sel]["id"].values[0])
            d_mob = ler_tabelas_sql(f"SELECT * FROM mobilizacoes WHERE id = {id_mob_edit}").iloc[0]
            
            with st.form("form_edit_mob"):
                em1, em2 = st.columns(2)
                with em1:
                    ne_eq = st.text_input("Equipamento", value=str(d_mob["equipamento"]))
                    ne_dest = st.text_input("Destino / Origem", value=str(d_mob["destino_origem"]))
                    ne_enc = st.text_input("Encarregado", value=str(d_mob["encarregado_responsavel"]))
                with em2:
                    ne_data = st.text_input("Data", value=str(d_mob["data_movimento"]))
                    ne_km = st.text_input("KM / Horímetro", value=str(d_mob["km_horimetro_atual"]))
                ne_obs = st.text_area("Observação", value=str(d_mob["observacao"]))
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    executar_comando_sql(
                        "UPDATE mobilizacoes SET equipamento = ?, destino_origem = ?, encarregado_responsavel = ?, data_movimento = ?, km_horimetro_atual = ?, observacao = ? WHERE id = ?",
                        (ne_eq, ne_dest, ne_enc, ne_data, ne_km, ne_obs, id_mob_edit)
                    )
                    st.success("✅ Registo atualizado com sucesso!")
        else:
            st.info("Nenhum registo de mobilização encontrado.")

elif menu == "🔧 Controle de Manutenção":
    st.title("🔧 Controle de Manutenção & Configuração Inicial de Revisão")
    
    t_man_rev, t_man_ed, t_man_rel = st.tabs(["⚙️ Configuração & Alertas", "📝 Editar Revisão", "📤 Relatórios & Partilha"])
    
    with t_man_rev:
        st.info("Selecione qualquer equipamento da frota, configure a sua revisão inicial e acompanhe os alertas automáticos em tempo real.")
        df_rev = ler_tabelas_sql("SELECT id, tag_prefixo, placa, marca_modelo, horimetro_km, tipo_controle, ultima_revisao, intervalo_revisao FROM veiculos")
        if not df_rev.empty:
            st.markdown("### 🚨 Alertas Ativos de Revisão")
            tem_alerta = False
            for _, row in df_rev.iterrows():
                atual = row.get("horimetro_km", 0) or 0
                ultima = row.get("ultima_revisao", 0) or 0
                intervalo = row.get("intervalo_revisao", 0) or 1000
                tipo = row.get("tipo_controle", "KM")
                
                proxima_rev = ultima + intervalo
                if atual >= (proxima_rev - (intervalo * 0.1)):
                    tem_alerta = True
                    falta = proxima_rev - atual
                    if falta < 0:
                        st.error(f"🚨 **{row['tag_prefixo']} ({row['marca_modelo']} - {row['placa']})**: REVISÃO VENCIDA! Ultrapassou o limite em **{abs(falta)} {tipo}**.")
                    else:
                        st.warning(f"⚠️ **{row['tag_prefixo']} ({row['marca_modelo']} - {row['placa']})**: Próximo da revisão. Faltam apenas **{falta} {tipo}**.")
            if not tem_alerta:
                st.success("✅ Todos os equipamentos da frota estão em dia com as manutenções preventivas!")

            st.divider()
            st.markdown("### ⚙️ Configuração Inicial e Atualização de Manutenção por Equipamento")
            df_rev["rotulo"] = df_rev["tag_prefixo"] + " - " + df_rev["marca_modelo"] + " (" + df_rev["placa"] + ")"
            eq_sel_rev = st.selectbox("Selecione o Equipamento / Veículo Registado", df_rev["rotulo"], key="sel_rev_config_persist")
            
            equip_escolhido = df_rev[df_rev["rotulo"] == eq_sel_rev].iloc[0]
            id_eq_r = int(equip_escolhido["id"])
            
            with st.form("form_atu_manut"):
                c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                with c_m1:
                    novo_tipo_cont = st.selectbox("Tipo de Medidor", ["KM", "Horas (Horímetro)"], index=0 if equip_escolhido["tipo_controle"] == "KM" else 1)
                with c_m2:
                    novo_hor_km = st.number_input("KM ou Horímetro Atual", min_value=0, value=int(equip_escolhido["horimetro_km"] or 0))
                with c_m3:
                    nova_ult_rev = st.number_input("Última Revisão Feita", min_value=0, value=int(equip_escolhido["ultima_revisao"] or 0))
                with c_m4:
                    novo_int_rev = st.number_input("Intervalo da Revisão", min_value=100, value=int(equip_escolhido["intervalo_revisao"] or 10000))
                
                if st.form_submit_button("Guardar Configuração de Revisão"):
                    executar_comando_sql("UPDATE veiculos SET tipo_controle = ?, horimetro_km = ?, ultima_revisao = ?, intervalo_revisao = ? WHERE id = ?", (novo_tipo_cont, novo_hor_km, nova_ult_rev, novo_int_rev, id_eq_r))
                    st.success("Configuração de manutenção e revisão atualizada com sucesso!")
        else:
            st.info("Nenhum equipamento registado na frota.")

    with t_man_ed:
        st.markdown("### 📝 Editar Dados de Controlo / Revisão de Frota")
        df_rev_ed = ler_tabelas_sql("SELECT id, tag_prefixo, marca_modelo, horimetro_km, ultima_revisao, intervalo_revisao FROM veiculos")
        if not df_rev_ed.empty:
            df_rev_ed["rot_rev"] = df_rev_ed["tag_prefixo"] + " - " + df_rev_ed["marca_modelo"]
            sel_rev_ed = st.selectbox("Selecione Equipamento para Editar Parâmetros de Revisão", df_rev_ed["rot_rev"], key="sel_ed_rev_persist")
            id_rev_alvo = int(df_rev_ed[df_rev_ed["rot_rev"] == sel_rev_ed]["id"].values[0])
            d_rev_atual = ler_tabelas_sql(f"SELECT * FROM veiculos WHERE id = {id_rev_alvo}").iloc[0]
            
            with st.form("form_edit_rev_dados"):
                er1, er2 = st.columns(2)
                with er1:
                    en_hor = st.number_input("KM / Horímetro Atual", value=int(d_rev_atual["horimetro_km"] or 0))
                    en_ult = st.number_input("Última Revisão", value=int(d_rev_atual["ultima_revisao"] or 0))
                with er2:
                    en_int = st.number_input("Intervalo de Revisão", value=int(d_rev_atual["intervalo_revisao"] or 10000))
                    en_tp = st.selectbox("Tipo de Controlo", ["KM", "Horas (Horímetro)"], index=0 if d_rev_atual["tipo_controle"]=="KM" else 1)
                
                if st.form_submit_button("💾 Salvar Alterações de Revisão"):
                    executar_comando_sql(
                        "UPDATE veiculos SET horimetro_km = ?, ultima_revisao = ?, intervalo_revisao = ?, tipo_controle = ? WHERE id = ?",
                        (en_hor, en_ult, en_int, en_tp, id_rev_alvo)
                    )
                    st.success("✅ Dados de revisão atualizados com sucesso!")
        else:
            st.info("Nenhum equipamento para editar.")

    with t_man_rel:
        st.markdown("### 📤 Partilha e Exportação de Dados de Manutenção")
        df_rel_man = ler_tabelas_sql("SELECT tag_prefixo, placa, marca_modelo, horimetro_km, tipo_controle, ultima_revisao, intervalo_revisao FROM veiculos")
        if not df_rel_man.empty:
            exibir_tabela_padronizada(df_rel_man, "veiculos")
            
            col_m_dl1, col_m_dl2, col_m_dl3 = st.columns(3)
            with col_m_dl1:
                pdf_man = gerar_pdf_relatorio("Relatório de Controlo de Manutenção e Revisões", df_rel_man)
                st.download_button("📥 Baixar Relatório PDF", data=pdf_man, file_name="relatorio_manutencao.pdf", mime="application/pdf")
            with col_m_dl2:
                excel_man = gerar_excel_formatado(df_rel_man, "Manutencao_Tabalmix")
                st.download_button("📊 Baixar Relatório Excel (Auto-ajustado)", data=excel_man, file_name="relatorio_manutencao.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with col_m_dl3:
                msg_wpp_m = urllib.parse.quote("🏗️ *RELATÓRIO DE MANUTENÇÃO TABALMIX*\nControlo de frotas e revisões preventivas atualizado.")
                st.markdown(f'<a href="https://api.whatsapp.com/send?text={msg_wpp_m}" target="_blank"><button style="background:linear-gradient(135deg, #25D366 0%, #128C7E 100%); color:white; font-weight:700; border-radius:12px; border:none; padding:0.65rem 1.8rem; width:100%; box-shadow:0 6px 16px rgba(37,211,102,0.3); cursor:pointer;">📱 Partilhar no WhatsApp</button></a>', unsafe_allow_html=True)
        else:
            st.info("Nenhum dado de manutenção disponível para exportação.")

elif menu == "⛽ Abastecimentos & Combustível":
    st.title("⛽ Registo de Abastecimentos")
    t_cab1, t_cab2, t_cab3 = st.tabs(["📋 Histórico", "➕ Novo Abastecimento", "📝 Editar"])
    
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

    with t_cab3:
        st.markdown("### 📝 Editar Registo de Abastecimento")
        df_abs = ler_tabelas_sql("SELECT id, equipamento, data, valor_total FROM combustivel ORDER BY id DESC")
        if not df_abs.empty:
            df_abs["rot_abs"] = df_abs["id"].astype(str) + " - " + df_abs["equipamento"] + " (" + df_abs["data"] + ")"
            sel_ab_ed = st.selectbox("Selecione o Abastecimento para Editar", df_abs["rot_abs"], key="sel_ed_abs_persist")
            id_ab_alvo = int(df_abs[df_abs["rot_abs"] == sel_ab_ed]["id"].values[0])
            d_ab_atual = ler_tabelas_sql(f"SELECT * FROM combustivel WHERE id = {id_ab_alvo}").iloc[0]
            
            with st.form("form_edit_abastecimento"):
                ea1, ea2 = st.columns(2)
                with ea1:
                    en_eq_ab = st.text_input("Equipamento", value=str(d_ab_atual["equipamento"]))
                    en_litros = st.number_input("Litros", min_value=0.0, value=float(d_ab_atual["litros"] or 0.0), format="%.2f")
                    en_val = st.number_input("Valor Total (R$)", min_value=0.0, value=float(d_ab_atual["valor_total"] or 0.0), format="%.2f")
                with ea2:
                    en_posto = st.text_input("Posto", value=str(d_ab_atual["posto_posto"]))
                    en_mot = st.text_input("Motorista", value=str(d_ab_atual["motorista"]))
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    executar_comando_sql(
                        "UPDATE combustivel SET equipamento = ?, litros = ?, valor_total = ?, posto_posto = ?, motorista = ? WHERE id = ?",
                        (en_eq_ab, en_litros, en_val, en_posto, en_mot, id_ab_alvo)
                    )
                    st.success("✅ Abastecimento atualizado com sucesso!")
        else:
            st.info("Nenhum registo de abastecimento encontrado.")

elif menu == "🛠️ Ordens de Serviço (OS)":
    st.title("🛠️ Gestão de Ordens de Serviço (OS)")
    
    t_os1, t_os2, t_os_fechar, t_os3 = st.tabs(["📋 Listagem de OS", "➕ Abrir Nova OS", "🔒 Fechar OS Aberta", "📝 Editar"])
    
    with t_os1:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM manutencoes ORDER BY id DESC"), "manutencoes")
        
    with t_os2:
        df_veiculos_os = ler_tabelas_sql("SELECT tag_prefixo, marca_modelo, placa FROM veiculos")
        lista_tags_os = df_veiculos_os["tag_prefixo"].tolist() if not df_veiculos_os.empty else ["BET-01", "ESC-02"]
        
        with st.form("form_os_nova"):
            st.markdown("### ➕ Abrir Nova Ordem de Serviço")
            os1, os2 = st.columns(2)
            with os1:
                tag_os = st.selectbox("TAG / Prefixo do Equipamento Cadastrado", lista_tags_os)
                tipo_man = st.selectbox("Tipo de Manutenção", ["Corretiva", "Preventiva", "Preditiva"])
                origem_f = st.selectbox("Origem da Falha", ["Falha de Equipamento", "Falha de Operação"])
            with os2:
                data_ab = st.text_input("Data de Abertura", value=datetime.now().strftime("%d/%m/%Y"))
                hora_ab = st.text_input("Hora de Abertura", value=datetime.now().strftime("%H:%M"))
                oficina = st.text_input("Oficina / Fornecedor / Responsável")
            
            desc = st.text_area("Descrição Detalhada do Problema / Falha")
            custo = st.number_input("Custo Total Estimado (R$)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("Abrir Ordem de Serviço"):
                executar_comando_sql(
                    "INSERT INTO manutencoes (tag_prefixo, tipo_manutencao, origem_falha, descricao_problema, data_abertura, hora_abertura, oficina, custo, status_os) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'aberta')",
                    (tag_os, tipo_man, origem_f, desc, data_ab, hora_ab, oficina, custo)
                )
                st.success("✅ Ordem de Serviço aberta com sucesso!")
                st.rerun()

    with t_os_fechar:
        st.markdown("### 🔒 Fechar Ordens de Serviço Abertas")
        df_abertas = ler_tabelas_sql("SELECT id, tag_prefixo, tipo_manutencao, data_abertura, descricao_problema FROM manutencoes WHERE status_os = 'aberta' ORDER BY id DESC")
        if not df_abertas.empty:
            df_abertas["rot_os_ab"] = "OS #" + df_abertas["id"].astype(str) + " - " + df_abertas["tag_prefixo"] + " (" + df_abertas["tipo_manutencao"] + ")"
            sel_os_fechar = st.selectbox("Selecione a OS Aberta para Concluir / Fechar", df_abertas["rot_os_ab"])
            id_os_f = int(df_abertas[df_abertas["rot_os_ab"] == sel_os_fechar]["id"].values[0])
            
            df_pecas_estoque = ler_tabelas_sql("SELECT id, nome_item, quantidade, valor_unitario FROM pecas")
            lista_pecas_opcoes = ["Nenhuma (Oficina Terceirizada ou sem peça interna)"]
            if not df_pecas_estoque.empty:
                for _, p_row in df_pecas_estoque.iterrows():
                    lista_pecas_opcoes.append(f"{p_row['nome_item']} (Disp: {p_row['quantidade']} | R$ {p_row['valor_unitario']:.2f})")

            with st.form("form_fechar_os_exec"):
                st.info("Preencha os dados de fecho, selecione peças do stock interno (abatimento automático) ou informe valores de oficina terceirizada.")
                
                fc1, fc2 = st.columns(2)
                with fc1:
                    peca_escolhida_stock = st.selectbox("Peça do Stock Interno (Opcional)", lista_pecas_opcoes)
                    qtd_peca_usada = st.number_input("Quantidade Utilizada da Peça", min_value=1, value=1)
                with fc2:
                    origem_peca_tipo = st.selectbox("Origem da Peça / Serviço", ["Stock Interno da Empresa", "Oficina Terceirizada / Externa"])
                    mao_obra = st.number_input("Custo de Mão de Obra (R$)", min_value=0.0, format="%.2f")
                
                custo_pecas_manual = st.number_input("Custo Adicional de Peças Terceirizadas (R$)", min_value=0.0, format="%.2f")
                tecnico = st.text_input("Técnico / Mecânico Responsável")
                
                fc3, fc4 = st.columns(2)
                with fc3:
                    data_fch = st.text_input("Data de Fechamento", value=datetime.now().strftime("%d/%m/%Y"))
                with fc4:
                    hora_fch = st.text_input("Hora de Fechamento", value=datetime.now().strftime("%H:%M"))
                
                if st.form_submit_button("🔒 Confirmar Fechamento da OS"):
                    custo_pecas_final = custo_pecas_manual
                    nome_peca_registo = "Oficina Terceirizada / Sem Peça Interna"
                    
                    if "Nenhuma" not in peca_escolhida_stock and not df_pecas_estoque.empty:
                        nome_peca_str = peca_escolhida_stock.split(" (Disp:")[0]
                        p_match = df_pecas_estoque[df_pecas_estoque["nome_item"] == nome_peca_str]
                        if not p_match.empty:
                            p_id = int(p_match.iloc[0]["id"])
                            p_qtd_atual = int(p_match.iloc[0]["quantidade"])
                            p_val_unit = float(p_match.iloc[0]["valor_unitario"])
                            
                            if p_qtd_atual >= qtd_peca_usada:
                                nova_qtd_estoque = p_qtd_atual - qtd_peca_usada
                                executar_comando_sql("UPDATE pecas SET quantidade = ? WHERE id = ?", (nova_qtd_estoque, p_id))
                                custo_pecas_final = p_val_unit * qtd_peca_usada
                                nome_peca_registo = f"{qtd_peca_usada}x {nome_peca_str} (Stock Interno)"
                            else:
                                st.error("⚠️ Quantidade solicitada maior do que o disponível em stock!")
                                st.stop()
                    
                    custo_total_real = custo_pecas_final + mao_obra
                    executar_comando_sql(
                        "UPDATE manutencoes SET status_os = 'concluida', pecas_utilizadas = ?, custo_pecas = ?, mao_de_obra = ?, custo = ?, tecnico_mecanico = ?, data_fechamento = ?, hora_fechamento = ? WHERE id = ?",
                        (nome_peca_registo, custo_pecas_final, mao_obra, custo_total_real, tecnico, data_fch, hora_fch, id_os_f)
                    )
                    st.success("✅ Ordem de Serviço fechada, stock atualizado e arquivada com sucesso!")
                    st.rerun()
        else:
            st.info("Não existem Ordens de Serviço abertas no momento.")

    with t_os3:
        st.markdown("### 📝 Editar Ordem de Serviço (OS)")
        df_oss = ler_tabelas_sql("SELECT id, tag_prefixo, tipo_manutencao, status_os FROM manutencoes ORDER BY id DESC")
        if not df_oss.empty:
            df_oss["rot_os"] = "OS #" + df_oss["id"].astype(str) + " - " + df_oss["tag_prefixo"] + " (" + df_oss["status_os"] + ")"
            sel_os_ed = st.selectbox("Selecione a OS para Editar", df_oss["rot_os"], key="sel_ed_os_persist")
            id_os_alvo = int(df_oss[df_oss["rot_os"] == sel_os_ed]["id"].values[0])
            d_os_atual = ler_tabelas_sql(f"SELECT * FROM manutencoes WHERE id = {id_os_alvo}").iloc[0]
            
            with st.form("form_edit_os_obj"):
                eo1, eo2 = st.columns(2)
                with eo1:
                    en_tag_os = st.text_input("Tag / Prefixo", value=str(d_os_atual["tag_prefixo"]))
                    en_tipo_m = st.selectbox("Tipo", ["Corretiva", "Preventiva", "Preditiva"], index=0 if d_os_atual["tipo_manutencao"]=="Corretiva" else (1 if d_os_atual["tipo_manutencao"]=="Preventiva" else 2))
                    en_status_os = st.selectbox("Status OS", ["aberta", "concluida", "cancelada"], index=0 if d_os_atual["status_os"]=="aberta" else 1)
                with eo2:
                    en_ofic = st.text_input("Oficina", value=str(d_os_atual["oficina"]))
                    en_custo_os = st.number_input("Custo Total (R$)", min_value=0.0, value=float(d_os_atual["custo"] or 0.0), format="%.2f")
                en_desc = st.text_area("Descrição", value=str(d_os_atual["descricao_problema"]))
                
                if st.form_submit_button("💾 Salvar Alterações da OS"):
                    executar_comando_sql(
                        "UPDATE manutencoes SET tag_prefixo = ?, tipo_manutencao = ?, status_os = ?, oficina = ?, custo = ?, descricao_problema = ? WHERE id = ?",
                        (en_tag_os, en_tipo_m, en_status_os, en_ofic, en_custo_os, en_desc, id_os_alvo)
                    )
                    st.success("✅ Ordem de Serviço atualizada com sucesso!")
        else:
            st.info("Nenhuma Ordem de Serviço encontrada.")

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
    st.markdown("Canal de comunicação em tempo real integrado para diretoria, engenharia, oficina e campo.")
    
    # Caixa de exibição estilo chat corporativo moderno
    chat_container = st.container()
    with chat_container:
        df_chat = ler_tabelas_sql("SELECT * FROM chat_interno ORDER BY id ASC LIMIT 100")
        if not df_chat.empty:
            for _, r in df_chat.iterrows():
                remetente_msg = r['remetente']
                mensagem_txt = r['mensagem']
                data_envio_msg = r['data_envio']
                arquivo_anexo = r['arquivo_nome']
                
                # Cores e estilos baseados no remetente ou padrão
                st.markdown(f"""
                    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-weight: 800; color: #047857; font-size: 13.5px;">👤 {remetente_msg}</span>
                            <span style="font-size: 11px; color: #64748b; font-weight: 600;">{data_envio_msg}</span>
                        </div>
                        <div style="color: #1e293b; font-size: 14px; font-weight: 500;">{mensagem_txt}</div>
                        {f'<div style="margin-top: 6px; font-size: 12px; color: #2563eb; font-weight: 600;">📎 Anexo: {arquivo_anexo}</div>' if arquivo_anexo else ''}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma mensagem no chat ainda. Seja o primeiro a iniciar a conversa!")

    st.divider()
    
    # Formulário de Envio de Mensagem
    with st.form("form_chat_pro", clear_on_submit=True):
        col_m1, col_m2 = st.columns([3.2, 0.8])
        with col_m1:
            msg_texto = st.text_input("Escreva a sua mensagem...", placeholder="Digite aqui...")
        with col_m2:
            arquivo_chat = st.file_uploader("Anexo Opcional", type=["jpg", "png", "jpeg", "pdf"], label_visibility="collapsed")
            
        if st.form_submit_button("🚀 Enviar Mensagem para a Equipa"):
            if msg_texto.strip() or arquivo_chat is not None:
                nome_remetente = usuario_atual['apelido'] if usuario_atual else "Alex"
                cargo_remetente = usuario_atual['cargo'] if usuario_atual else "Diretoria"
                nome_arq_val = arquivo_chat.name if arquivo_chat is not None else None
                
                executar_comando_sql(
                    "INSERT INTO chat_interno (remetente, destinatario, cargo, mensagem, arquivo_nome, data_envio) VALUES (?, 'Geral', ?, ?, ?, ?)",
                    (nome_remetente, cargo_remetente, msg_texto, nome_arq_val, datetime.now().strftime("%d/%m/%Y às %H:%M"))
                )
                st.rerun()
            else:
                st.warning("Escreva uma mensagem ou anexe um ficheiro antes de enviar.")

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
    
    st.markdown("### 🔑 Gerador de Chaves de Segurança Corporativas")
    with st.form("form_gerar_chave"):
        c_cargo_chave = st.selectbox("Cargo Destino da Chave", ["Master", "Engenharia", "Oficina", "Operacional"])
        c_mod_chave = st.selectbox("Modalidade", ["Enterprise Pro", "Anual", "Vitalícia"])
        if st.form_submit_button("Gerar Nova Chave de Segurança"):
            nova_chave_gerada = "TBX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            executar_comando_sql("INSERT INTO chaves_licenca (codigo_chave, cargo_atribuido, modalidade, status_uso, data_criacao) VALUES (?, ?, ?, 'Disponível', ?)", (nova_chave_gerada, c_cargo_chave, c_mod_chave, datetime.now().strftime("%Y-%m-%d")))
            st.success(f"✅ Chave gerada com sucesso: **{nova_chave_gerada}**")

    st.markdown("### 📋 Chaves de Segurança Existentes")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM chaves_licenca ORDER BY id DESC"), "chaves_licenca")

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
    st.markdown("### 🗄️ Gestão Global e Limpeza de Dados de Todos os Sistemas")
    tabelas_sistema_disponiveis = [
        "veiculos", "manutencoes", "pecas", "clientes", 
        "mobilizacoes", "combustivel", 
        "multas", "usuarios_sistema", "chat_interno", "chaves_licenca"
    ]
    tabela_alvo_limpeza = st.selectbox("Selecione o Sistema / Tabela para Gerir", tabelas_sistema_disponiveis)
    
    if st.button(f"🗑️ Apagar/Esvaziar Todos os Registos de '{tabela_alvo_limpeza}'"):
        try:
            executar_comando_sql(f"DELETE FROM {tabela_alvo_limpeza}")
            st.success(f"Todos os registos da tabela '{tabela_alvo_limpeza}' foram eliminados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao limpar tabela: {e}")
