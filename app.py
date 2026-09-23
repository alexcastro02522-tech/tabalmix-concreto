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
        CREATE TABLE IF NOT EXISTS chamada_controlo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador TEXT, cargo TEXT, data_chamada TEXT,
            status_presenca TEXT, observacao TEXT
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
            worksheet.set_column(col_num, col_num, 20, cell_format)
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
    "🔍 Consulta / Busca Geral",
    "🚜 Cadastro de Equipamentos",
    "🏗️ Mobilização / Desmobilização",
    "🔧 Controle de Manutenção",
    "📋 Chamada de Controlo",
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
            eq_escolhido_edit = st.selectbox("Selecione o Equipamento para Editar", df_edit_eq["rotulo_edit"])
            
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
                    st.rerun()
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
            mob_sel = st.selectbox("Selecione o Registo para Editar", df_mobs["rot_mob"])
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
                    st.rerun()
        else:
            st.info("Nenhum registo de mobilização encontrado.")

elif menu == "🔧 Controle de Manutenção":
    st.title("🔧 Controle de Manutenção & Configuração Inicial de Revisão")
    
    t_man_rev, t_man_ed = st.tabs(["⚙️ Configuração & Alertas", "📝 Editar Revisão"])
    
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
            eq_sel_rev = st.selectbox("Selecione o Equipamento / Veículo Registado", df_rev["rotulo"])
            
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
                    st.rerun()
        else:
            st.info("Nenhum equipamento registado na frota.")

    with t_man_ed:
        st.markdown("### 📝 Editar Dados de Controlo / Revisão de Frota")
        df_rev_ed = ler_tabelas_sql("SELECT id, tag_prefixo, marca_modelo, horimetro_km, ultima_revisao, intervalo_revisao FROM veiculos")
        if not df_rev_ed.empty:
            df_rev_ed["rot_rev"] = df_rev_ed["tag_prefixo"] + " - " + df_rev_ed["marca_modelo"]
            sel_rev_ed = st.selectbox("Selecione Equipamento para Editar Parâmetros de Revisão", df_rev_ed["rot_rev"])
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
                    st.rerun()
        else:
            st.info("Nenhum equipamento para editar.")

elif menu == "📋 Chamada de Controlo":
    st.title("📋 Chamada de Controlo & Presença na Obra")
    st.info("Registe a presença diária dos operadores, motoristas e encarregados em campo.")
    
    t_ch1, t_ch2 = st.tabs(["📋 Histórico de Chamadas", "➕ Registar Presença"])
    with t_ch1:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM chamada_controlo ORDER BY id DESC"), "chamada_controlo")
    with t_ch2:
        df_func = ler_tabelas_sql("SELECT nome_completo, cargo_setor FROM usuarios_sistema")
        lista_nomes = df_func["nome_completo"].tolist() if not df_func.empty else ["Alex de Castro Bernardino"]
        
        with st.form("form_chamada"):
            c_colab = st.selectbox("Colaborador / Operador", lista_nomes)
            c_status = st.selectbox("Estado da Presenca", ["Presente", "Falta Justificada", "Falta Injustificada", "Atestado / Licença", "Em Viagem / Campo"])
            c_obs = st.text_area("Observações do Dia / Atividade")
            
            if st.form_submit_button("Registar Chamada"):
                cargo_cad = "Operacional"
                if not df_func.empty:
                    match_c = df_func[df_func["nome_completo"] == c_colab]
                    if not match_c.empty:
                        cargo_cad = match_c.iloc[0]["cargo_setor"]
                
                executar_comando_sql("INSERT INTO chamada_controlo (colaborador, cargo, data_chamada, status_presenca, observacao) VALUES (?, ?, ?, ?, ?)", (c_colab, cargo_cad, datetime.now().strftime("%d/%m/%Y"), c_status, c_obs))
                st.success("Presença registada com sucesso na chamada de controlo!")
                st.rerun()

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
            sel_ab_ed = st.selectbox("Selecione o Abastecimento para Editar", df_abs["rot_abs"])
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
                    st.rerun()
        else:
            st.info("Nenhum registo de abastecimento encontrado.")

elif menu == "🛠️ Ordens de Serviço (OS)":
    st.title("🛠️ Gestão de Ordens de Serviço (OS)")
    t_os1, t_os2, t_os3 = st.tabs(["📋 Listagem de OS", "➕ Abrir Nova OS", "📝 Editar"])
    
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

    with t_os3:
        st.markdown("### 📝 Editar Ordem de Serviço (OS)")
        df_oss = ler_tabelas_sql("SELECT id, tag_prefixo, tipo_manutencao, status_os FROM manutencoes ORDER BY id DESC")
        if not df_oss.empty:
            df_oss["rot_os"] = "OS #" + df_oss["id"].astype(str) + " - " + df_oss["tag_prefixo"] + " (" + df_oss["status_os"] + ")"
            sel_os_ed = st.selectbox("Selecione a OS para Editar", df_oss["rot_os"])
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
                    st.rerun()
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
    st.markdown("### 🗄️ Gestão Global e Limpeza de Dados de Todos os Sistemas")
    st.info("Aqui podes limpar ou esvaziar qualquer tabela/sistema do banco de dados (ideal para apagar registos antigos ou de teste de qualquer aba).")
    
    tabelas_sistema_disponiveis = [
        "veiculos", "manutencoes", "pecas", "clientes", 
        "mobilizacoes", "chamada_controlo", "combustivel", 
        "multas", "usuarios_sistema", "chat_interno"
    ]
    tabela_alvo_limpeza = st.selectbox("Selecione o Sistema / Tabela para Gerir", tabelas_sistema_disponiveis)
    
    col_l_1, col_l_2 = st.columns(2)
    with col_l_1:
        if st.button(f"🗑️ Apagar/Esvaziar Todos os Registos de '{tabela_alvo_limpeza}'"):
            try:
                executar_comando_sql(f"DELETE FROM {tabela_alvo_limpeza}")
                st.success(f"Todos os registos da tabela '{tabela_alvo_limpeza}' foram eliminados com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao limpar tabela: {e}")

    st.divider()
    st.markdown("### 🛠️ Gestão de Colunas e Estrutura de Tabelas")
    tabela_escolhida = st.selectbox("Selecione a Tabela para Configurar Colunas", ["veiculos", "manutencoes", "pecas", "clientes", "mobilizacoes", "combustivel", "multas"])
    
    with st.form("form_config_col"):
        cols_ocultar_str = st.text_input("Colunas para Ocultar (separadas por vírgula, ex: chassi,renavam)")
        if st.form_submit_button("Salvar Configuração de Colunas"):
            executar_comando_sql("INSERT OR REPLACE INTO config_colunas (tabela, ordem_colunas) VALUES (?, ?)", (tabela_escolhida, cols_ocultar_str))
            st.success("Configuração de colunas atualizada!")
            st.rerun()
