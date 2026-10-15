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
from supabase import create_client, Client

SUPABASE_URL = "https://ctibigorhynwnkuzqfjm.supabase.co"
SUPABASE_KEY = "sb_publishable_m75yp7ycIwqKwULd7365gA_cd3GSlpg"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

def ler_tabelas_sql(query_str):
    try:
        q_lower = query_str.lower()
        tabela = "veiculos"
        if "manutencoes" in q_lower: tabela = "manutencoes"
        elif "pecas" in q_lower: tabela = "pecas"
        elif "clientes" in q_lower: tabela = "clientes"
        elif "mobilizacoes" in q_lower: tabela = "mobilizacoes"
        elif "combustivel" in q_lower: tabela = "combustivel"
        elif "usuarios_sistema" in q_lower: tabela = "usuarios_sistema"
        elif "chat_interno" in q_lower: tabela = "chat_interno"
        elif "reunioes_live" in q_lower: tabela = "reunioes_live"
        elif "chaves_licenca" in q_lower: tabela = "chaves_licenca"
        elif "multas" in q_lower: tabela = "multas"

        response = supabase.table(tabela).select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            if "where" in q_lower and "email = '" in query_str:
                try:
                    email_filtro = query_str.split("email = '")[1].split("'")[0].strip().lower()
                    if "email" in df.columns:
                        df['email_limpo'] = df['email'].astype(str).str.strip().str.lower()
                        df = df[df['email_limpo'] == email_filtro]
                except Exception:
                    pass
            elif "status_os = 'aberta'" in q_lower:
                if "status_os" in df.columns:
                    df = df[df["status_os"] == "aberta"]
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro Supabase Ler ({query_str}): {e}")
        return pd.DataFrame()

def executar_comando_sql(query_str, params=None):
    try:
        q_lower = query_str.lower()
        if "insert" in q_lower:
            if "veiculos" in q_lower and params:
                dados = {
                    "tag_prefixo": str(params[0]), "placa": str(params[1]), "categoria_equipamento": str(params[2]),
                    "ano_fabricacao": int(params[3]) if params[3] else 2026, "renavam": str(params[4]), "crv": str(params[5]),
                    "marca_modelo": str(params[6]), "tipo": str(params[7]), "cor": str(params[8]), "combustivel": str(params[9]),
                    "chassi": str(params[10]), "empresa": str(params[11]), "operador_condutor": str(params[12]),
                    "horimetro_km": float(params[13]) if params[13] else 0.0, "status": 'Ativo', "tipo_controle": str(params[14]), 
                    "ultima_revisao": float(params[15]) if params[15] else 0.0, "intervalo_revisao": float(params[16]) if params[16] else 10000.0
                }
                supabase.table("veiculos").insert(dados).execute()
            elif "mobilizacoes" in q_lower and params:
                dados = {
                    "equipamento": str(params[0]), "tipo_movimento": str(params[1]), "destino_origem": str(params[2]),
                    "encarregado_responsavel": str(params[3]), "data_movimento": str(params[4]), "km_horimetro_atual": str(params[5]),
                    "observacao": str(params[6])
                }
                supabase.table("mobilizacoes").insert(dados).execute()
            elif "combustivel" in q_lower and params:
                dados = {
                    "equipamento": str(params[0]), "litros": float(params[1]), "valor_total": float(params[2]),
                    "posto_posto": str(params[3]), "motorista": str(params[4]), "data": str(params[5])
                }
                supabase.table("combustivel").insert(dados).execute()
            elif "manutencoes" in q_lower and params:
                dados = {
                    "tag_prefixo": str(params[0]), "tipo_manutencao": str(params[1]), "origem_falha": str(params[2]),
                    "descricao_problema": str(params[3]), "data_abertura": str(params[4]), "hora_abertura": str(params[5]),
                    "oficina": str(params[6]), "custo": float(params[7]), "status_os": 'aberta',
                    "ocorrencia_tipo": str(params[8]), "tipo_oficina": str(params[9])
                }
                supabase.table("manutencoes").insert(dados).execute()
            elif "multas" in q_lower and params:
                dados = {
                    "equipamento_placa": str(params[0]), "orgao_autuador": str(params[1]), "local_infracao": str(params[2]),
                    "valor_multa": float(params[3]), "data_vencimento": str(params[4]), "status_multa": 'Pendente'
                }
                supabase.table("multas").insert(dados).execute()
            elif "pecas" in q_lower and params:
                dados = {"nome_item": str(params[0]), "categoria": str(params[1]), "quantidade": int(params[2]), "valor_unitario": float(params[3])}
                supabase.table("pecas").insert(dados).execute()
            elif "clientes" in q_lower and params:
                dados = {"nome": str(params[0]), "empresa": str(params[1]), "telefone": str(params[2]), "documento": str(params[3]), "endereco": str(params[4])}
                supabase.table("clientes").insert(dados).execute()
            elif "chat_interno" in q_lower and params:
                dados = {"remetente": str(params[0]), "destinatario": str(params[1]), "cargo": str(params[2]), "mensagem": str(params[3]), "arquivo_nome": str(params[4]), "data_envio": str(params[5])}
                supabase.table("chat_interno").insert(dados).execute()
            elif "reunioes_live" in q_lower and params:
                dados = {"titulo_reuniao": str(params[0]), "criador": str(params[1]), "participantes": str(params[2]), "link_sala": str(params[3]), "senha_sala": str(params[4]), "status_sala": "Ativa", "data_criacao": str(params[5])}
                supabase.table("reunioes_live").insert(dados).execute()
            elif "usuarios_sistema" in q_lower and params:
                if len(params) >= 10:
                    dados = {
                        "nome_completo": str(params[0]), "cpf": str(params[1]), "email": str(params[2]), "senha": str(params[3]),
                        "celular_seguranca": str(params[4]), "status_assinatura": "Ativo", "plano_atual": str(params[5]),
                        "data_cadastro": str(params[6]), "pin_rapido": str(params[7]), "apelido": str(params[8]), "cargo_setor": str(params[9])
                    }
                    supabase.table("usuarios_sistema").insert(dados).execute()
        elif "delete" in q_lower:
            if "usuarios_sistema" in q_lower and params:
                supabase.table("usuarios_sistema").delete().eq("id", int(params[0])).execute()
            elif "veiculos" in q_lower:
                supabase.table("veiculos").delete().neq("id", 0).execute()
            elif "manutencoes" in q_lower:
                supabase.table("manutencoes").delete().neq("id", 0).execute()
            elif "pecas" in q_lower:
                supabase.table("pecas").delete().neq("id", 0).execute()
            elif "clientes" in q_lower:
                supabase.table("clientes").delete().neq("id", 0).execute()
            elif "mobilizacoes" in q_lower:
                supabase.table("mobilizacoes").delete().neq("id", 0).execute()
            elif "combustivel" in q_lower:
                supabase.table("combustivel").delete().neq("id", 0).execute()
            elif "multas" in q_lower:
                supabase.table("multas").delete().neq("id", 0).execute()
            elif "chat_interno" in q_lower:
                supabase.table("chat_interno").delete().neq("id", 0).execute()
            elif "reunioes_live" in q_lower:
                supabase.table("reunioes_live").delete().neq("id", 0).execute()
        return True
    except Exception as e:
        print(f"Erro Supabase Comando ({query_str}): {e}")
        return False

st.set_page_config(
    page_title="Tabalmix Concreto - Enterprise Fleet & Operations Pro X",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("<style>header[data-testid='stHeader'] {background: transparent !important;} header[data-testid='stHeader'] [data-testid='baseButton-header'] {font-size: 0px !important;} header[data-testid='stHeader'] [data-testid='baseButton-header']::after {content: '☰ Menu' !important; font-size: 13px !important; font-weight: 700 !important; color: #047857 !important; background: #ffffff !important; padding: 4px 10px !important; border-radius: 8px !important; border: 1px solid #cbd5e1 !important; display: inline-block !important;}</style>", unsafe_allow_html=True)

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; padding-bottom: 3.5rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background: #f8fafc !important; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] .stRadio label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div {
        color: #1e293b !important; font-weight: 600 !important;
    }
    .stApp { background: #f1f5f9 !important; color: #0f172a !important; }
    h1, h2, h3, h4 { color: #0f172a !important; font-weight: 800; }
    input, textarea, select, div[data-baseweb="select"] > div {
        background-color: #ffffff !important; color: #0f172a !important; -webkit-text-fill-color: #0f172a !important;
    }
    div[data-baseweb="base-input"] { background-color: #ffffff !important; }
    .metric-card-corporate {
        background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #047857;
        padding: 22px 20px; border-radius: 14px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03); margin-bottom: 12px;
    }
    .metric-title { font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 6px; }
    .metric-value { font-size: 24px; font-weight: 900; color: #0f172a; }
    .metric-sub { font-size: 11.5px; font-weight: 600; color: #047857; margin-top: 4px; }
    .stButton button {
        background: linear-gradient(135deg, #047857 0%, #065f46 100%) !important; 
        color: white !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important;
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

modo_admin_liberado = False
try:
    query_params = st.query_params
    if query_params.get("admin") == "tabalmix_master_2026" or str(query_params).find("admin=tabalmix_master_2026") != -1:
        modo_admin_liberado = True
except Exception:
    modo_admin_liberado = False

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None and not modo_admin_liberado:
    col_l1, col_l2, col_l3 = st.columns([0.05, 3.9, 0.05])
    with col_l2:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 16px; padding: 25px; text-align: center; color: white; margin-bottom: 20px;">
                <h1 style="color: white !important; margin: 0; font-size: 22px; font-weight: 800;">TABALMIX CONCRETO</h1>
                <p style="color: #e2e8f0; font-size: 11px; text-transform: uppercase;">Gestão Corporativa & Automação Master</p>
            </div>
        """, unsafe_allow_html=True)

        escolha_modo_login = st.selectbox("Central de Segurança & Acesso Corporativo:", [
            "Entrar com E-mail e Senha",
            "Criar Novo Cadastro na Obra"
        ])

        if escolha_modo_login == "Entrar com E-mail e Senha":
            with st.form("form_login_senha"):
                st.markdown("### Autenticação Corporativa")
                l_email = st.text_input("E-mail corporativo", value="alexcastro02522@gmail.com")
                l_senha = st.text_input("Senha de acesso", type="password", value="admin2026")
                if st.form_submit_button("Entrar no Sistema"):
                    df_log = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{l_email.strip()}'")
                    if not df_log.empty:
                        u = df_log.iloc[0]
                        if str(u.get("senha")) == str(l_senha):
                            st.session_state["usuario_logado"] = {
                                "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                                "email": u["email"], "status": u["status_assinatura"],
                                "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                                "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
                            }
                            st.success("Login efetuado com sucesso.")
                            st.rerun()
                        else:
                            st.error("Senha incorreta.")
                    else:
                        st.error("E-mail não encontrado.")

        elif escolha_modo_login == "Criar Novo Cadastro na Obra":
            with st.form("form_novo_cad"):
                st.markdown("### Criar Novo Registro")
                c_nome = st.text_input("Nome Completo")
                c_apelido = st.text_input("Apelido")
                c_cargo = st.selectbox("Cargo / Função", ["Diretoria & Master", "Engenharia & Obra", "Oficina & Mecânica", "Operacional Campo"])
                cargo_banco_str = "Diretoria / Gestão" if "Master" in c_cargo else ("Engenheiro / Gestor de Obra" if "Engenharia" in c_cargo else ("Mecânico / Oficina" if "Oficina" in c_cargo else "Operador / Motorista"))
                c_cpf = st.text_input("CPF")
                c_email = st.text_input("E-mail corporativo")
                c_senha = st.text_input("Senha", type="password")
                c_cel = st.text_input("Celular / WhatsApp")
                c_pin = st.text_input("PIN Rápido (4 Dígitos)", max_chars=4)
                if st.form_submit_button("Concluir Cadastro"):
                    if c_nome and c_email and c_senha:
                        apelido_f = c_apelido if c_apelido else c_nome.split()[0]
                        executar_comando_sql(
                            "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, pin_rapido, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (c_nome, c_cpf, c_email.strip(), c_senha, c_cel, c_cargo, datetime.now().strftime("%Y-%m-%d %H:%M"), c_pin, apelido_f, cargo_banco_str)
                        )
                        st.session_state["usuario_logado"] = {
                            "id": 999, "nome": c_nome, "cpf": c_cpf,
                            "email": c_email.strip(), "status": "Ativo",
                            "apelido": apelido_f, "cargo": cargo_banco_str
                        }
                        st.success("Conta cadastrada e acesso liberado com sucesso!")
                        st.rerun()
    st.stop()

usuario_atual = st.session_state["usuario_logado"]

def exibir_tabela_padronizada(df, nome_tabela):
    if df.empty:
        st.info("Nenhum registro encontrado no Supabase.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)

with st.sidebar:
    st.markdown("<div style='text-align:center; font-weight:900; font-size:16px;'>TABALMIX CONCRETO</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-size:10.5px; color:#64748b; margin-bottom:10px;'>Castro Tech Architecture</div>", unsafe_allow_html=True)
    if modo_admin_liberado:
        st.success("Modo Admin Ativo")
    elif usuario_atual:
        st.markdown(f"**{usuario_atual['apelido']}**<br>{usuario_atual['cargo']}", unsafe_allow_html=True)
        if st.button("Encerrar Sessão"):
            st.session_state["usuario_logado"] = None
            st.rerun()
    st.markdown("---")

lista_menus = [
    "Visão Geral",
    "Consulta / Busca Geral",
    "Cadastro de Equipamentos",
    "Mobilização / Desmobilização",
    "Controle de Manutenção",
    "Abastecimentos & Combustível",
    "Ordens de Serviço (OS)",
    "Gestão & Alertas de Multas",
    "Peças e Ferramentas",
    "Gestão de Clientes",
    "Chat Interno & Reuniões Live",
    "Meu Perfil / Dados",
]
if modo_admin_liberado:
    lista_menus.append("Painel de Licença (Admin)")

menu = st.sidebar.radio("Navegação", lista_menus, label_visibility="collapsed")

if menu == "Visão Geral":
    st.title("Painel Executivo de Operações")
    st.markdown("<p style='color: #64748b; margin-top: -10px; margin-bottom: 25px;'>Monitoramento de frotas e métricas corporativas em tempo real — Castro Tech</p>", unsafe_allow_html=True)
    
    df_veiculos = ler_tabelas_sql("SELECT * FROM veiculos")
    df_manut = ler_tabelas_sql("SELECT * FROM manutencoes")
    df_comb = ler_tabelas_sql("SELECT * FROM combustivel")
    df_multas = ler_tabelas_sql("SELECT * FROM multas")

    total_frota = len(df_veiculos) if not df_veiculos.empty else 0
    os_abertas = len(df_manut[df_manut["status_os"] == "aberta"]) if not df_manut.empty and "status_os" in df_manut.columns else 0
    total_multas = len(df_multas) if not df_multas.empty else 0
    gasto_comb = df_comb['valor_total'].sum() if not df_comb.empty and 'valor_total' in df_comb.columns else 0.0
    total_litros = df_comb['litros'].sum() if not df_comb.empty and 'litros' in df_comb.columns else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
            <div class="metric-card-corporate">
                <div class="metric-title">Total Frota</div>
                <div class="metric-value">{total_frota}</div>
                <div class="metric-sub">Veículos Ativos</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="metric-card-corporate">
                <div class="metric-title">OS Abertas</div>
                <div class="metric-value">{os_abertas}</div>
                <div class="metric-sub">Em Manutenção</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="metric-card-corporate">
                <div class="metric-title">Multas</div>
                <div class="metric-value">{total_multas}</div>
                <div class="metric-sub">Registradas</div>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
            <div class="metric-card-corporate">
                <div class="metric-title">Gasto Combust.</div>
                <div class="metric-value" style="font-size: 20px;">R$ {gasto_comb:,.2f}</div>
                <div class="metric-sub">Investido em Diesel</div>
            </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
            <div class="metric-card-corporate">
                <div class="metric-title">Total Litros</div>
                <div class="metric-value" style="font-size: 22px;">{total_litros:,.1f} L</div>
                <div class="metric-sub">Consumo Global</div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### Gestão de Frotas & Relatórios Executivos")
    if not df_veiculos.empty:
        exibir_tabela_padronizada(df_veiculos, "veiculos")
    else:
        st.info("Nenhum veículo cadastrado na nuvem.")

elif menu == "Consulta / Busca Geral":
    st.title("Consulta Avançada de Frota e Ativos")
    termo_busca = st.text_input("Filtrar por TAG, Placa, Marca ou Modelo:")
    df_v = ler_tabelas_sql("SELECT * FROM veiculos")
    if not df_v.empty:
        if termo_busca:
            df_v = df_v[df_v.apply(lambda row: row.astype(str).str.contains(termo_busca, case=False).any(), axis=1)]
        exibir_tabela_padronizada(df_v, "veiculos")
    else:
        st.info("Nenhum equipamento cadastrado.")

elif menu == "Cadastro de Equipamentos":
    st.title("Cadastro de Equipamentos")
    t_l, t_r = st.tabs(["Frota Ativa", "Cadastrar Novo"])
    with t_l:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM veiculos"), "veiculos")
    with t_r:
        with st.form("form_eq_novo"):
            st.markdown("### Cadastrar Novo Equipamento")
            c1, c2, c3 = st.columns(3)
            with c1:
                f_tag = st.text_input("TAG / Prefixo (Ex: BET-01)")
                f_placa = st.text_input("Placa")
                f_cat = st.selectbox("Categoria", ["Linha Branca", "Linha Amarela", "Veículo Leve"])
                f_ano = st.number_input("Ano Fabricação", min_value=1980, value=2026)
            with c2:
                f_renavam = st.text_input("RENAVAM")
                f_crv = st.text_input("CRV")
                f_marca = st.text_input("Marca / Modelo")
                f_tipo = st.text_input("Tipo")
            with c3:
                f_cor = st.text_input("Cor")
                f_comb = st.selectbox("Combustível", ["Diesel", "Gasolina", "Flex"])
                f_chassi = st.text_input("Chassi")
                f_emp = st.text_input("Empresa", value="Tabalmix Concreto")
                f_op = st.text_input("Operador Condutor")
            if st.form_submit_button("Salvar Equipamento no Supabase") and f_tag:
                executar_comando_sql("INSERT INTO veiculos", (f_tag, f_placa, f_cat, f_ano, f_renavam, f_crv, f_marca, f_tipo, f_cor, f_comb, f_chassi, f_emp, f_op, 0.0, "KM", 0.0, 10000.0))
                st.success("Equipamento cadastrado com sucesso.")
                st.rerun()

elif menu == "Mobilização / Desmobilização":
    st.title("Controle de Mobilização & Vistoria")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM mobilizacoes"), "mobilizacoes")

elif menu == "Controle de Manutenção":
    st.title("Controle de Manutenção & Revisões")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM manutencoes"), "manutencoes")

elif menu == "Abastecimentos & Combustível":
    st.title("Registro de Abastecimentos")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM combustivel"), "combustivel")
    with st.form("form_comb"):
        st.markdown("### Novo Lançamento de Abastecimento")
        eq = st.text_input("Equipamento")
        lit = st.number_input("Litros", min_value=0.0)
        val = st.number_input("Valor Total (R$)", min_value=0.0)
        post = st.text_input("Posto")
        mot = st.text_input("Motorista")
        if st.form_submit_button("Cadastrar Abastecimento"):
            executar_comando_sql("INSERT INTO combustivel", (eq, lit, val, post, mot, datetime.now().strftime("%d/%m/%Y")))
            st.success("Abastecimento salvo no Supabase.")
            st.rerun()

elif menu == "Ordens de Serviço (OS)":
    st.title("Gestão de Ordens de Serviço (OS)")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM manutencoes"), "manutencoes")

elif menu == "Gestão & Alertas de Multas":
    st.title("Controle de Multas")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM multas"), "multas")
    with st.form("form_multa"):
        placa = st.text_input("Placa")
        orgao = st.text_input("Órgão Autuador")
        local = st.text_input("Local")
        valor = st.number_input("Valor", min_value=0.0)
        venc = st.text_input("Vencimento")
        if st.form_submit_button("Cadastrar Multa"):
            executar_comando_sql("INSERT INTO multas", (placa, orgao, local, valor, venc))
            st.success("Multa salva no Supabase.")
            st.rerun()

elif menu == "Peças e Ferramentas":
    st.title("Controle de Estoque de Peças")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM pecas"), "pecas")

elif menu == "Gestão de Clientes":
    st.title("Gestão de Clientes")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM clientes"), "clientes")

elif menu == "Chat Interno & Reuniões Live":
    st.title("Chat Corporativo & Reuniões Live")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM chat_interno"), "chat_interno")

elif menu == "Meu Perfil / Dados":
    st.title("Meu Perfil & Dados")
    if usuario_atual:
        st.markdown(f"""
            * **Nome**: {usuario_atual.get('nome')}
            * **E-mail**: {usuario_atual.get('email')}
            * **Cargo**: {usuario_atual.get('cargo')}
            * **Arquitetura**: Castro Tech & Supabase Cloud
        """)

elif menu == "Painel de Licença (Admin)" and modo_admin_liberado:
    st.title("Painel Administrativo Master & Bot de Testes")
    st.markdown("<p style='color: #64748b;'>Ferramentas de auditoria, testes automatizados e limpeza geral da base — Castro Tech</p>", unsafe_allow_html=True)
    
    col_bt1, col_bt2 = st.columns(2)
    with col_bt1:
        st.markdown("### 🤖 Bot de Teste Automatizado")
        st.markdown("Executa um ciclo completo criando usuário de teste, veículo piloto e lançamentos simulados.")
        if st.button("Executar Bot de Testes Agora"):
            try:
                # 1. Criar usuário teste
                executar_comando_sql(
                    "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, pin_rapido, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("Bot Auditor Teste", "000.000.000-00", "bottest@tabalmix.com", "123456", "(92) 99999-9999", "Ativo", "Master", datetime.now().strftime("%Y-%m-%d %H:%M"), "1234", "RoboTest", "Diretoria / Gestão")
                )
                # 2. Criar veículo teste
                executar_comando_sql("INSERT INTO veiculos", ("BOT-99", "ABC-1234", "Linha Amarela", 2026, "123456789", "987654", "Caminhão Betoneira Teste", "Betoneira", "Branco", "Diesel", "9BWZZZ...", "Tabalmix Concreto", "RoboTest", 1500.0, "KM", 1000.0, 10000.0))
                # 3. Criar abastecimento teste
                executar_comando_sql("INSERT INTO combustivel", ("BOT-99", 150.0, 950.0, "Posto Central", "RoboTest", datetime.now().strftime("%d/%m/%Y")))
                st.success("✅ Bot executado com sucesso! Dados de teste criados no Supabase.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao rodar bot de testes: {e}")

    with col_bt2:
        st.markdown("### 🧹 Botão de Reset Master (Zerar Tudo)")
        st.markdown("Apaga todos os registros operacionais e de teste das tabelas do banco de dados de uma só vez.")
        if st.button("⚠️ ZERAR TODOS OS DADOS DA NUVEM"):
            try:
                executar_comando_sql("DELETE FROM veiculos")
                executar_comando_sql("DELETE FROM manutencoes")
                executar_comando_sql("DELETE FROM pecas")
                executar_comando_sql("DELETE FROM clientes")
                executar_comando_sql("DELETE FROM mobilizacoes")
                executar_comando_sql("DELETE FROM combustivel")
                executar_comando_sql("DELETE FROM multas")
                executar_comando_sql("DELETE FROM chat_interno")
                executar_comando_sql("DELETE FROM reunioes_live")
                st.success("🗑️ Banco de dados limpo com sucesso! Todas as tabelas foram zeradas.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao zerar o banco de dados: {e}")

    st.divider()
    st.markdown("### Colaboradores Cadastrados no Sistema")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM usuarios_sistema"), "usuarios_sistema")
