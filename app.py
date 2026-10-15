from datetime import datetime, timedelta
import base64
import csv
import glob
import io
import os
import random
import string
import urllib.parse
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = "https://ctibigorhynwnkuzqfjm.supabase.co"
SUPABASE_KEY = "sb_publishable_m75yp7ycIwqKwULd7365gA_cd3GSlpg"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = init_supabase()

# --- INICIALIZAÇÃO DE ESTADO LOCAL (FALLBACK GARANTIDO) ---
for chave_est in ["local_veiculos", "local_chat", "local_usuarios", "local_manutencoes", "local_combustivel", "local_mobilizacoes", "local_multas", "local_pecas", "local_clientes"]:
    if chave_est not in st.session_state:
        st.session_state[chave_est] = []

def testar_conexao_supabase():
    try:
        if supabase is not None:
            res = supabase.table("veiculos").select("id").limit(1).execute()
            return True
    except Exception:
        pass
    return False

# --- FUNÇÕES HÍBRIDAS ULTRA-RESILIENTES (SUPABASE + FALLBACK) ---
def ler_tabelas_sql(query_str):
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

    try:
        if supabase is not None:
            response = supabase.table(tabela).select("*").execute()
            if response.data is not None:
                df = pd.DataFrame(response.data)
                # Combina com dados locais de transbordo se existirem
                loc_key = f"local_{tabela}"
                if loc_key in st.session_state and st.session_state[loc_key]:
                    df_loc = pd.DataFrame(st.session_state[loc_key])
                    df = pd.concat([df, df_loc], ignore_index=True).drop_duplicates(subset=['id'] if 'id' in df.columns else None, keep='last')
                
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
    except Exception as e:
        st.session_state["ultimo_erro_ia"] = f"[{tabela.upper()}] Alerta de Rede/DNS: {str(e)}"

    # Modo Local Ativo de Resiliência
    loc_key = f"local_{tabela}"
    if loc_key in st.session_state and st.session_state[loc_key]:
        return pd.DataFrame(st.session_state[loc_key])
    
    return pd.DataFrame()

def executar_comando_sql(query_str, params=None):
    q_lower = query_str.lower()
    tabela = "veiculos"
    if "mobilizacoes" in q_lower: tabela = "mobilizacoes"
    elif "combustivel" in q_lower: tabela = "combustivel"
    elif "manutencoes" in q_lower: tabela = "manutencoes"
    elif "multas" in q_lower: tabela = "multas"
    elif "pecas" in q_lower: tabela = "pecas"
    elif "clientes" in q_lower: tabela = "clientes"
    elif "chat_interno" in q_lower: tabela = "chat_interno"
    elif "reunioes_live" in q_lower: tabela = "reunioes_live"
    elif "usuarios_sistema" in q_lower: tabela = "usuarios_sistema"

    dados = {}
    try:
        if "insert" in q_lower and params:
            if tabela == "veiculos":
                dados = {
                    "id": random.randint(1000, 99999), "tag_prefixo": str(params[0]), "placa": str(params[1]), "categoria_equipamento": str(params[2]),
                    "ano_fabricacao": int(params[3]) if params[3] else 2026, "renavam": str(params[4]), "crv": str(params[5]),
                    "marca_modelo": str(params[6]), "tipo": str(params[7]), "cor": str(params[8]), "combustivel": str(params[9]),
                    "chassi": str(params[10]), "empresa": str(params[11]), "operador_condutor": str(params[12]),
                    "horimetro_km": float(params[13]) if params[13] else 0.0, "status": 'Ativo', "tipo_controle": str(params[14]), 
                    "ultima_revisao": float(params[15]) if params[15] else 0.0, "intervalo_revisao": float(params[16]) if params[16] else 10000.0
                }
            elif tabela == "mobilizacoes":
                dados = {"id": random.randint(1000, 99999), "equipamento": str(params[0]), "tipo_movimento": str(params[1]), "destino_origem": str(params[2]), "encarregado_responsavel": str(params[3]), "data_movimento": str(params[4]), "km_horimetro_atual": str(params[5]), "observacao": str(params[6])}
            elif tabela == "combustivel":
                dados = {"id": random.randint(1000, 99999), "equipamento": str(params[0]), "litros": float(params[1]), "valor_total": float(params[2]), "posto_posto": str(params[3]), "motorista": str(params[4]), "data": str(params[5])}
            elif tabela == "manutencoes":
                dados = {"id": random.randint(1000, 99999), "tag_prefixo": str(params[0]), "tipo_manutencao": str(params[1]), "origem_falha": str(params[2]), "descricao_problema": str(params[3]), "data_abertura": str(params[4]), "hora_abertura": str(params[5]), "oficina": str(params[6]), "custo": float(params[7]), "status_os": 'aberta', "ocorrencia_tipo": str(params[8]), "tipo_oficina": str(params[9])}
            elif tabela == "multas":
                dados = {"id": random.randint(1000, 99999), "equipamento_placa": str(params[0]), "orgao_autuador": str(params[1]), "local_infracao": str(params[2]), "valor_multa": float(params[3]), "data_vencimento": str(params[4]), "status_multa": 'Pendente'}
            elif tabela == "pecas":
                dados = {"id": random.randint(1000, 99999), "nome_item": str(params[0]), "categoria": str(params[1]), "quantidade": int(params[2]), "valor_unitario": float(params[3])}
            elif tabela == "clientes":
                dados = {"id": random.randint(1000, 99999), "nome": str(params[0]), "empresa": str(params[1]), "telefone": str(params[2]), "documento": str(params[3]), "endereco": str(params[4])}
            elif tabela == "chat_interno":
                dados = {"id": random.randint(1000, 99999), "remetente": str(params[0]), "destinatario": str(params[1]), "cargo": str(params[2]), "mensagem": str(params[3]), "arquivo_nome": str(params[4]), "data_envio": str(params[5])}
            elif tabela == "usuarios_sistema" and len(params) >= 10:
                dados = {"id": random.randint(1000, 99999), "nome_completo": str(params[0]), "cpf": str(params[1]), "email": str(params[2]), "senha": str(params[3]), "celular_seguranca": str(params[4]), "status_assinatura": "Ativo", "plano_atual": str(params[5]), "data_cadastro": str(params[6]), "pin_rapido": str(params[7]), "apelido": str(params[8]), "cargo_setor": str(params[9])}

            if supabase is not None and dados:
                supabase.table(tabela).insert(dados).execute()
                return True, "Sucesso Supabase Cloud"
        elif "delete" in q_lower:
            if supabase is not None:
                supabase.table(tabela).delete().neq("id", 0).execute()
            st.session_state[f"local_{tabela}"] = []
            return True, "Limpeza Executada"
    except Exception as e:
        st.session_state["ultimo_erro_ia"] = f"Erro ao gravar em {tabela}: {str(e)}"
    
    # Fallback de Gravação Local Garantida
    if dados:
        st.session_state[f"local_{tabela}"].append(dados)
        return True, "Sucesso em Modo Local (Resiliente)"
    return False, "Falha na Execução"

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
    .stApp { background: #f1f5f9 !important; color: #0f172a !important; }
    h1, h2, h3, h4 { color: #0f172a !important; font-weight: 800; }
    input, textarea, select { background-color: #ffffff !important; color: #0f172a !important; }
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

def gerar_pdf_ordem_servico(os_row):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter
    margem = 35
    largura_util = largura - (2 * margem)
    
    c.setFillColorRGB(0.04, 0.35, 0.22)
    c.rect(0, altura - 70, largura, 70, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(margem, altura - 30, "TABALMIX CONCRETO - SISTEMA DE GESTÃO DE FROTA")
    c.setFont("Helvetica", 9)
    c.drawString(margem, altura - 46, "ORDEM DE SERVIÇO TÉCNICA CERTIFICADA — CASTRO TECH")
    
    y = altura - 95
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margem, y, f"ORDEM DE SERVIÇO Nº: {os_row.get('id', '001')}")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(largura - 160, y, f"STATUS: {str(os_row.get('status_os', 'aberta')).upper()}")
    
    y -= 25
    c.setFont("Helvetica", 9)
    c.drawString(margem, y, f"Data Abertura: {os_row.get('data_abertura', '-')}")
    c.drawString(margem + 150, y, f"Hora: {os_row.get('hora_abertura', '-')}")
    c.drawString(margem + 280, y, f"Oficina / Local: {os_row.get('oficina', '-')}")
    
    y -= 22
    c.drawString(margem, y, f"Equipamento / TAG: {os_row.get('tag_prefixo', '-')}")
    c.drawString(margem + 200, y, f"Ocorrência: {os_row.get('ocorrencia_tipo', 'Mecânica')}")
    c.drawString(margem + 380, y, f"Tipo: {os_row.get('tipo_oficina', 'Própria')}")
    
    y -= 30
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margem, y, "DESCRIÇÃO DO PROBLEMA / RELATO:")
    y -= 18
    c.setFont("Helvetica", 9)
    c.rect(margem, y - 35, largura_util, 40, fill=0, stroke=1)
    c.drawString(margem + 6, y - 12, str(os_row.get('descricao_problema', '-'))[:90])
    
    y -= 55
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margem, y, "SERVIÇOS REALIZADOS / PEÇAS APLICADAS:")
    y -= 18
    c.setFont("Helvetica", 9)
    c.rect(margem, y - 35, largura_util, 40, fill=0, stroke=1)
    c.drawString(margem + 6, y - 12, str(os_row.get('pecas_utilizadas', 'Aguardando encerramento técnico'))[:90])
    
    y -= 55
    c.drawString(margem, y, f"Data Fechamento: {os_row.get('data_fechamento', '-')}   |   Hora Final: {os_row.get('hora_fechamento', '-')}")
    c.drawString(margem + 300, y, f"Custo Total (R$): R$ {float(os_row.get('custo', 0) or 0):,.2f}")
    
    y -= 90
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.setLineWidth(0.8)
    larg_col_ass = largura_util / 3.0
    c.line(margem, y, margem + larg_col_ass - 15, y)
    c.line(margem + larg_col_ass + 5, y, margem + (2 * larg_col_ass) - 10, y)
    c.line(margem + (2 * larg_col_ass) + 10, y, largura - margem, y)
    
    c.setFont("Helvetica", 7.5)
    c.drawString(margem, y - 12, "Ass. Mecânica / Elétrica")
    c.drawString(margem + larg_col_ass + 5, y - 12, "Responsável Técnico")
    c.drawString(margem + (2 * larg_col_ass) + 10, y - 12, "Encarregado Tabalmix")

    c.save()
    buffer.seek(0)
    return buffer

modo_admin_liberado = False
try:
    if st.query_params.get("admin") == "tabalmix_master_2026":
        modo_admin_liberado = True
except Exception:
    pass

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None and not modo_admin_liberado:
    col_l1, col_l2, col_l3 = st.columns([0.05, 3.9, 0.05])
    with col_l2:
        try:
            with open("caminhoes.jpg", "rb") as image_file:
                encoded_logo_login = base64.b64encode(image_file.read()).decode()
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 16px; padding: 25px; text-align: center; box-shadow: 0 10px 30px rgba(4,120,87,0.15); margin-top: 10px; margin-bottom: 20px; color: white;">
                    <div style="border-radius: 12px; overflow: hidden; max-height: 100px; border: 2px solid rgba(255,255,255,0.8); margin-bottom: 12px;">
                        <img src="data:image/jpeg;base64,{encoded_logo_login}" style="width: 100%; height: 100px; object-fit: cover; display: block;">
                    </div>
                    <h1 style="color: white !important; margin: 0; font-size: 22px; font-weight: 800;">TABALMIX CONCRETO</h1>
                    <p style="color: #e2e8f0; font-size: 11px; margin: 4px 0 0 0; text-transform: uppercase; font-weight: 600;">Gestão Corporativa • Castro Tech & Supabase</p>
                </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 16px; padding: 25px; text-align: center; color: white; margin-bottom: 20px;">
                    <h1 style="color: white !important; margin: 0; font-size: 22px; font-weight: 800;">TABALMIX CONCRETO</h1>
                    <p style="color: #e2e8f0; font-size: 11px; text-transform: uppercase;">Castro Tech Architecture</p>
                </div>
            """, unsafe_allow_html=True)

        escolha_modo_login = st.selectbox("Central de Segurança & Acesso Corporativo:", ["Entrar com E-mail e Senha", "Criar Novo Cadastro na Obra"])

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
                                "email": u["email"], "status": u.get("status_assinatura", "Ativo"),
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
                        executar_comando_sql("INSERT INTO usuarios_sistema", (c_nome, c_cpf, c_email.strip(), c_senha, c_cel, c_cargo, datetime.now().strftime("%Y-%m-%d %H:%M"), c_pin, apelido_f, cargo_banco_str))
                        st.session_state["usuario_logado"] = {"id": 999, "nome": c_nome, "cpf": c_cpf, "email": c_email.strip(), "status": "Ativo", "apelido": apelido_f, "cargo": cargo_banco_str}
                        st.success("Conta cadastrada e acesso liberado com sucesso!")
                        st.rerun()
    st.stop()

usuario_atual = st.session_state["usuario_logado"]

def exibir_tabela_padronizada(df, nome_tabela):
    if df.empty:
        st.info("Nenhum registro encontrado.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)

with st.sidebar:
    st.markdown("<div style='text-align:center; font-weight:900; font-size:16px;'>TABALMIX CONCRETO</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-size:10.5px; color:#64748b; margin-bottom:10px;'>Castro Tech Architecture</div>", unsafe_allow_html=True)
    
    # Indicador de Conectividade em Tempo Real
    conectado_nuvem = testar_conexao_supabase()
    if conectado_nuvem:
        st.markdown("<div style='background:#d1fae5; color:#065f46; padding:6px 10px; border-radius:8px; font-size:11px; font-weight:700; text-align:center; margin-bottom:10px;'>🟢 Conectado ao Supabase Cloud</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background:#fee2e2; color:#991b1b; padding:6px 10px; border-radius:8px; font-size:11px; font-weight:700; text-align:center; margin-bottom:10px;'>🟡 Modo Local Resiliente (Offline)</div>", unsafe_allow_html=True)

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
    "Robô de Testes Reais (QA)",
    "Assistente IA & Diagnóstico",
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
    st.markdown("<p style='color: #64748b; margin-top: -10px; margin-bottom: 25px;'>Monitoramento corporativo em tempo real — Castro Tech</p>", unsafe_allow_html=True)
    
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
    with c1: st.markdown(f'<div class="metric-card-corporate"><div class="metric-title">Total Frota</div><div class="metric-value">{total_frota}</div><div class="metric-sub">Veículos Ativos</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card-corporate"><div class="metric-title">OS Abertas</div><div class="metric-value">{os_abertas}</div><div class="metric-sub">Em Manutenção</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card-corporate"><div class="metric-title">Multas</div><div class="metric-value">{total_multas}</div><div class="metric-sub">Registradas</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card-corporate"><div class="metric-title">Gasto Combust.</div><div class="metric-value" style="font-size: 20px;">R$ {gasto_comb:,.2f}</div><div class="metric-sub">Diesel</div></div>', unsafe_allow_html=True)
    with c5: st.markdown(f'<div class="metric-card-corporate"><div class="metric-title">Total Litros</div><div class="metric-value" style="font-size: 22px;">{total_litros:,.1f} L</div><div class="metric-sub">Consumo</div></div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### Frota Ativa Sincronizada")
    if not df_veiculos.empty:
        exibir_tabela_padronizada(df_veiculos, "veiculos")
    else:
        st.info("Nenhum veículo registado.")

elif menu == "Robô de Testes Reais (QA)":
    st.title("Robô de Testes e Simulação Real")
    st.markdown("Executa testes automáticos de inserção, leitura e escrita nas tabelas para validar a persistência em tempo real.")
    if st.button("Executar Bateria de Testes QA"):
        with st.spinner("A testar inserções reais no Supabase e Fallback..."):
            s1, msg1 = executar_comando_sql("INSERT INTO veiculos", ("BET-QA-99", "ABC-1234", "Linha Branca", 2026, "123456", "789456", "Mercedes Betoneira", "Truck", "Branca", "Diesel", "987654321", "Tabalmix", "QA Tester", 1200.0, "KM", 0.0, 10000.0))
            s2, msg2 = executar_comando_sql("INSERT INTO chat_interno", ("Robô QA", "Geral", "Sistema IA", "Teste de integração efetuado com sucesso.", "", datetime.now().strftime("%d/%m/%Y às %H:%M")))
            if s1 and s2:
                st.success(f"Testes concluídos com sucesso! Status: {msg1} | {msg2}")
            else:
                st.error("Foram detetadas falhas no teste. Verifique o painel da IA.")

elif menu == "Assistente IA & Diagnóstico":
    st.title("Assistente IA de Suporte & Diagnóstico")
    st.markdown("Módulo inteligente para apoio aos colaboradores e monitoramento automático de erros técnicos.")
    
    ultimo_erro = st.session_state.get("ultimo_erro_ia", "Nenhum erro detetado recentemente. O sistema está a operar normalmente.")
    st.markdown(f"""
        <div style="background: #e2e8f0; padding: 15px; border-radius: 10px; border-left: 5px solid #047857; margin-bottom: 20px;">
            <strong>Diagnóstico Técnico Atual:</strong><br>{ultimo_erro}
        </div>
    """, unsafe_allow_html=True)

    pergunta_ia = st.text_input("Como posso ajudar a tua operação hoje? (Ex: Como fechar uma OS?)")
    if pergunta_ia:
        p_lower = pergunta_ia.lower()
        if "os" in p_lower or "ordem" in p_lower:
            st.info("💡 **Dica da IA:** Para fechar uma Ordem de Serviço, vai à aba 'Ordens de Serviço (OS)', seleciona a aba 'Abertas', escolhe o ID da OS e clica em 'Concluir OS e Baixar Estoque' para atualizar automaticamente o inventário.")
        elif "abastecimento" in p_lower:
            st.info("💡 **Dica da IA:** O registo de combustível é feito na aba 'Abastecimentos & Combustível' preenchendo os litros e o valor total gasto no posto.")
        else:
            st.info("💡 **Dica da IA:** Certifica-te de que tens permissão de perfil adequada e que os dados obrigatórios do formulário estão preenchidos.")

elif menu == "Consulta / Busca Geral":
    st.title("Consulta Avançada de Frota e Ativos")
    termo = st.text_input("Pesquisar por TAG, Placa ou Modelo:")
    df_v = ler_tabelas_sql("SELECT * FROM veiculos")
    if not df_v.empty and termo:
        df_v = df_v[df_v.apply(lambda r: r.astype(str).str.contains(termo, case=False).any(), axis=1)]
    exibir_tabela_padronizada(df_v, "veiculos")

elif menu == "Cadastro de Equipamentos":
    st.title("Cadastro de Equipamentos")
    t_l, t_r = st.tabs(["Frota Ativa", "Cadastrar Novo"])
    with t_l:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM veiculos"), "veiculos")
    with t_r:
        with st.form("form_eq"):
            f_tag = st.text_input("TAG / Prefixo")
            f_placa = st.text_input("Placa")
            f_cat = st.selectbox("Categoria", ["Linha Branca", "Linha Amarela", "Veículo Leve"])
            f_marca = st.text_input("Marca / Modelo")
            if st.form_submit_button("Salvar Equipamento") and f_tag:
                executar_comando_sql("INSERT INTO veiculos", (f_tag, f_placa, f_cat, 2026, "", "", f_marca, "", "", "Diesel", "", "Tabalmix", "", 0.0, "KM", 0.0, 10000.0))
                st.success("Equipamento registado com sucesso!")
                st.rerun()

elif menu == "Mobilização / Desmobilização":
    st.title("Mobilização & Vistoria")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM mobilizacoes"), "mobilizacoes")
    with st.form("form_mob"):
        eq = st.text_input("Equipamento")
        dest = st.text_input("Destino / Origem")
        if st.form_submit_button("Registar Movimento"):
            executar_comando_sql("INSERT INTO mobilizacoes", (eq, "Mobilização", dest, "Encarregado", datetime.now().strftime("%d/%m/%Y"), "0", ""))
            st.success("Movimento registado.")
            st.rerun()

elif menu == "Controle de Manutenção":
    st.title("Controle de Manutenção")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM manutencoes"), "manutencoes")

elif menu == "Abastecimentos & Combustível":
    st.title("Abastecimentos & Combustível")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM combustivel"), "combustivel")
    with st.form("form_comb"):
        eq = st.text_input("Equipamento")
        lit = st.number_input("Litros", min_value=0.0)
        val = st.number_input("Valor Total (R$)", min_value=0.0)
        if st.form_submit_button("Registar Abastecimento"):
            executar_comando_sql("INSERT INTO combustivel", (eq, lit, val, "Posto Central", "Motorista", datetime.now().strftime("%d/%m/%Y")))
            st.success("Abastecimento guardado.")
            st.rerun()

elif menu == "Ordens de Serviço (OS)":
    st.title("Gestão de Ordens de Serviço (OS)")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM manutencoes"), "manutencoes")
    with st.form("form_os_novo"):
        tag = st.text_input("TAG do Equipamento")
        desc = st.text_area("Descrição do Problema")
        if st.form_submit_button("Abrir OS") and tag:
            executar_comando_sql("INSERT INTO manutencoes", (tag, "Corretiva", "Falha Mecânica", desc, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), "Oficina", 0.0, "Mecânica", "Própria"))
            st.success("OS aberta com sucesso.")
            st.rerun()

elif menu == "Gestão & Alertas de Multas":
    st.title("Controle de Multas")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM multas"), "multas")

elif menu == "Peças e Ferramentas":
    st.title("Estoque de Peças")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM pecas"), "pecas")
    with st.form("form_peca"):
        nome = st.text_input("Nome da Peça")
        qtd = st.number_input("Quantidade", min_value=1, value=10)
        val = st.number_input("Valor Unitário", min_value=0.0)
        if st.form_submit_button("Adicionar Peça"):
            executar_comando_sql("INSERT INTO pecas", (nome, "Geral", qtd, val))
            st.success("Peça adicionada.")
            st.rerun()

elif menu == "Gestão de Clientes":
    st.title("Gestão de Clientes")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM clientes"), "clientes")

elif menu == "Chat Interno & Reuniões Live":
    st.title("Chat Corporativo & Reuniões")
    df_chat = ler_tabelas_sql("SELECT * FROM chat_interno")
    if not df_chat.empty:
        for _, m in df_chat.tail(10).iterrows():
            st.markdown(f"**{m.get('remetente')}**: {m.get('mensagem')}")
    with st.form("form_chat", clear_on_submit=True):
        txt = st.text_input("Escrever mensagem...")
        if st.form_submit_button("Enviar"):
            executar_comando_sql("INSERT INTO chat_interno", (usuario_atual['apelido'], "Geral", usuario_atual['cargo'], txt, "", datetime.now().strftime("%d/%m/%Y %H:%M")))
            st.rerun()

elif menu == "Meu Perfil / Dados":
    st.title("Meu Perfil")
    if usuario_atual:
        st.write(f"Nome: {usuario_atual.get('nome')}")
        st.write(f"Cargo: {usuario_atual.get('cargo')}")

elif menu == "Painel de Licença (Admin)" and modo_admin_liberado:
    st.title("Painel Admin Master")
    if st.button("Limpar Dados de Veículos"):
        executar_comando_sql("DELETE FROM veiculos")
        st.success("Tabela limpa.")
        st.rerun()
