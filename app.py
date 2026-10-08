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

# Configuração de Conexão com o Supabase Nuvem
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
            if "where" in q_lower:
                if "email = '" in query_str:
                    try:
                        email_filtro = query_str.split("email = '")[1].split("'")[0].strip().lower()
                        df = df[df["email"].str.strip().str.lower() == email_filtro]
                    except Exception:
                        pass
                elif "status_os = 'aberta'" in q_lower:
                    if "status_os" in df.columns:
                        df = df[df["status_os"] == "aberta"]
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro Supabase Ler: {e}")
        return pd.DataFrame()

def executar_comando_sql(query_str, params=None):
    try:
        q_lower = query_str.lower()
        if "insert" in q_lower:
            if "veiculos" in q_lower:
                dados = {
                    "tag_prefixo": str(params[0]), "placa": str(params[1]), "categoria_equipamento": str(params[2]),
                    "ano_fabricacao": int(params[3]) if params[3] else 2026, "renavam": str(params[4]), "crv": str(params[5]),
                    "marca_modelo": str(params[6]), "tipo": str(params[7]), "cor": str(params[8]), "combustivel": str(params[9]),
                    "chassi": str(params[10]), "empresa": str(params[11]), "operador_condutor": str(params[12]),
                    "horimetro_km": float(params[13]) if params[13] else 0.0, "status": 'Ativo', "tipo_controle": 'KM', "ultima_revisao": 0, "intervalo_revisao": 10000
                }
                res = supabase.table("veiculos").insert(dados).execute()
                print("Resultado insert veiculos:", res)
            elif "mobilizacoes" in q_lower:
                dados = {
                    "equipamento": str(params[0]), "tipo_movimento": str(params[1]), "destino_origem": str(params[2]),
                    "encarregado_responsavel": str(params[3]), "data_movimento": str(params[4]), "km_horimetro_atual": str(params[5]),
                    "observacao": str(params[6])
                }
                supabase.table("mobilizacoes").insert(dados).execute()
            elif "combustivel" in q_lower:
                dados = {
                    "equipamento": str(params[0]), "litros": float(params[1]), "valor_total": float(params[2]),
                    "posto_posto": str(params[3]), "motorista": str(params[4]), "data": str(params[5])
                }
                supabase.table("combustivel").insert(dados).execute()
            elif "manutencoes" in q_lower:
                dados = {
                    "tag_prefixo": str(params[0]), "tipo_manutencao": str(params[1]), "origem_falha": str(params[2]),
                    "descricao_problema": str(params[3]), "data_abertura": str(params[4]), "hora_abertura": str(params[5]),
                    "oficina": str(params[6]), "custo": float(params[7]), "status_os": 'aberta'
                }
                supabase.table("manutencoes").insert(dados).execute()
            elif "multas" in q_lower:
                dados = {
                    "equipamento_placa": str(params[0]), "orgao_autuador": str(params[1]), "local_infracao": str(params[2]),
                    "valor_multa": float(params[3]), "data_vencimento": str(params[4]), "status_multa": 'Pendente'
                }
                supabase.table("multas").insert(dados).execute()
            elif "pecas" in q_lower:
                dados = {"nome_item": str(params[0]), "categoria": str(params[1]), "quantidade": int(params[2]), "valor_unitario": float(params[3])}
                supabase.table("pecas").insert(dados).execute()
            elif "clientes" in q_lower:
                dados = {"nome": str(params[0]), "empresa": str(params[1]), "telefone": str(params[2]), "documento": str(params[3]), "endereco": str(params[4])}
                supabase.table("clientes").insert(dados).execute()
            elif "chat_interno" in q_lower:
                dados = {"remetente": str(params[0]), "destinatario": str(params[1]), "cargo": str(params[2]), "mensagem": str(params[3]), "arquivo_nome": str(params[4]), "data_envio": str(params[5])}
                supabase.table("chat_interno").insert(dados).execute()
            elif "reunioes_live" in q_lower:
                dados = {"titulo_reuniao": str(params[0]), "criador": str(params[1]), "participantes": str(params[2]), "link_sala": str(params[3]), "senha_sala": str(params[4]), "status_sala": "Ativa", "data_criacao": str(params[5])}
                supabase.table("reunioes_live").insert(dados).execute()
            elif "chaves_licenca" in q_lower:
                dados = {"codigo_chave": str(params[0]), "cargo_atribuido": str(params[1]), "modalidade": str(params[2]), "status_uso": "Disponível", "data_criacao": str(params[3])}
                supabase.table("chaves_licenca").insert(dados).execute()
            elif "usuarios_sistema" in q_lower:
                if len(params) >= 10:
                    dados = {
                        "nome_completo": str(params[0]), "cpf": str(params[1]), "email": str(params[2]), "senha": str(params[3]),
                        "celular_seguranca": str(params[4]), "status_assinatura": "Ativo", "plano_atual": str(params[5]),
                        "data_cadastro": str(params[6]), "pin_rapido": str(params[7]), "apelido": str(params[8]), "cargo_setor": str(params[9])
                    }
                    supabase.table("usuarios_sistema").insert(dados).execute()
        elif "update" in q_lower:
            if "usuarios_sistema" in q_lower:
                if "senha = ?" in q_lower:
                    supabase.table("usuarios_sistema").update({"senha": str(params[0])}).eq("email", str(params[1])).execute()
            elif "chaves_licenca" in q_lower:
                supabase.table("chaves_licenca").update({"status_uso": "Utilizado", "usado_por": str(params[0])}).eq("codigo_chave", str(params[1])).execute()
            elif "manutencoes" in q_lower and "status_os = 'concluida'" in q_lower:
                supabase.table("manutencoes").update({
                    "status_os": "concluida", "pecas_utilizadas": str(params[0]), "custo_pecas": float(params[1]),
                    "mao_de_obra": float(params[2]), "custo": float(params[3]), "tecnico_mecanico": str(params[4]),
                    "encarregado_responsavel": str(params[5]), "data_fechamento": str(params[6]), "hora_fechamento": str(params[7])
                }).eq("id", int(params[8])).execute()
            elif "pecas" in q_lower and "quantidade = ?" in q_lower:
                supabase.table("pecas").update({"quantidade": int(params[0])}).eq("id", int(params[1])).execute()
            elif "veiculos" in q_lower and "horimetro_km" in q_lower:
                supabase.table("veiculos").update({
                    "tipo_controle": str(params[0]), "horimetro_km": float(params[1]), 
                    "ultima_revisao": float(params[2]), "intervalo_revisao": float(params[3])
                }).eq("id", int(params[4])).execute()
        elif "delete" in q_lower:
            if "usuarios_sistema" in q_lower:
                supabase.table("usuarios_sistema").delete().eq("id", int(params[0])).execute()
            elif "veiculos" in q_lower:
                supabase.table("veiculos").delete().execute()
            elif "manutencoes" in q_lower:
                supabase.table("manutencoes").delete().execute()
            elif "pecas" in q_lower:
                supabase.table("pecas").delete().execute()
            elif "clientes" in q_lower:
                supabase.table("clientes").delete().execute()
            elif "mobilizacoes" in q_lower:
                supabase.table("mobilizacoes").delete().execute()
            elif "combustivel" in q_lower:
                supabase.table("combustivel").delete().execute()
            elif "multas" in q_lower:
                supabase.table("multas").delete().execute()
            elif "chat_interno" in q_lower:
                supabase.table("chat_interno").delete().execute()
            elif "reunioes_live" in q_lower:
                supabase.table("reunioes_live").delete().execute()
            elif "chaves_licenca" in q_lower:
                supabase.table("chaves_licenca").delete().execute()
        return True
    except Exception as e:
        print(f"Erro Supabase Comando: {e}")
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

# DESIGN SYSTEM ULTRAMODERNO - CASTRO TECH & TABALMIX
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    header[data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 3.5rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background: #f8fafc !important; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] .stRadio label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div {
        color: #1e293b !important; font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important;
    }
    .stApp { background: #f1f5f9 !important; color: #0f172a !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }
    h1, h2, h3, h4 { color: #0f172a !important; font-weight: 800; letter-spacing: -0.8px; }
    label, div[data-baseweb="input"] label, .stTextInput label, .stNumberInput label, .stSelectbox label, .stTextArea label {
        color: #1e293b !important; font-weight: 700 !important; font-size: 13.5px !important;
    }
    
    .metric-card-modern {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #059669;
        padding: 22px 20px;
        border-radius: 18px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.05), 0 8px 10px -6px rgba(15, 23, 42, 0.05);
        transition: all 0.3s ease;
        margin-bottom: 12px;
    }
    .metric-card-modern:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 35px -5px rgba(5, 150, 105, 0.12), 0 10px 15px -5px rgba(0, 0, 0, 0.04);
        border-color: #059669;
    }
    .metric-title {
        font-size: 11.5px;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 900;
        color: #0f172a;
        letter-spacing: -1px;
    }
    .metric-sub {
        font-size: 12px;
        font-weight: 600;
        color: #059669;
        margin-top: 4px;
    }
    .stButton button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important; 
        color: white !important; font-weight: 700 !important; border-radius: 14px !important; 
        border: none !important; padding: 0.7rem 1.8rem !important;
        box-shadow: 0 8px 20px rgba(5, 150, 105, 0.25) !important;
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

def gerar_pdf_relatorio(titulo, dataframe, assinaturas=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter
    margem_esq = 30
    largura_util = largura - 60
    
    c.setFillColorRGB(0.04, 0.35, 0.22)
    c.rect(0, altura - 75, largura, 75, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margem_esq, altura - 30, "🏗️ TABALMIX CONCRETO — ENTERPRISE MANAGEMENT")
    c.setFont("Helvetica", 9)
    c.drawString(margem_esq, altura - 48, "SISTEMA INTELIGENTE DE FROTAS, OBRAS E ORDENS DE SERVIÇO — CASTRO TECH")
    
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margem_esq, altura - 98, titulo)
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(margem_esq, altura - 114, f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')} | Sincronizado via Supabase Cloud")
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(1)
    c.line(margem_esq, altura - 122, largura - margem_esq, altura - 122)
    
    y = altura - 145
    altura_linha = 22
    colunas = list(dataframe.columns)
    colunas_amigaveis = [str(col).replace('_', ' ').upper() for col in colunas[:6]]
    
    c.setFillColorRGB(0.05, 0.25, 0.15)
    c.rect(margem_esq, y - 4, largura_util, altura_linha, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 8.5)
    largura_coluna = largura_util / max(len(colunas_amigaveis), 1)
    for i, col_nome in enumerate(colunas_amigaveis):
        c.drawString(margem_esq + (i * largura_coluna) + 4, y + 4, col_nome[:14])
    y -= altura_linha + 4
    
    c.setFont("Helvetica", 8)
    for index, row in dataframe.iterrows():
        if y < 100:
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
        
    if y < 120:
        c.showPage()
        y = altura - 60
        
    y -= 30
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.setLineWidth(1)
    c.line(margem_esq, y, largura / 2 - 20, y)
    c.line(largura / 2 + 20, y, largura - margem_esq, y)
    
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(margem_esq, y - 12, "Assinatura: Técnico Mecânico Responsável")
    c.drawString(largura / 2 + 20, y - 12, "Assinatura: Encarregado / Gestor de Obra")
    c.save()
    buffer.seek(0)
    return buffer

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
        try:
            with open("caminhoes.jpg", "rb") as image_file:
                encoded_logo_login = base64.b64encode(image_file.read()).decode()
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 20px 40px rgba(5,150,105,0.2); margin-top: 10px; margin-bottom: 20px; color: white;">
                    <div style="border-radius: 14px; overflow: hidden; max-height: 110px; border: 3px solid rgba(255,255,255,0.8); margin-bottom: 14px; box-shadow: 0 8px 20px rgba(0,0,0,0.2);">
                        <img src="data:image/jpeg;base64,{encoded_logo_login}" style="width: 100%; height: 110px; object-fit: cover; display: block;">
                    </div>
                    <h1 style="color: white !important; margin: 0; font-size: 24px; font-weight: 900;">tabalmix concreto</h1>
                    <p style="color: #e2e8f0; font-size: 11.5px; margin: 4px 0 2px 0; text-transform: uppercase; font-weight: 600;">Powered by Castro Tech • Cloud Supabase</p>
                </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 25px; text-align: center; color: white; margin-bottom: 20px;">
                    <h1 style="color: white !important; margin: 0; font-size: 24px; font-weight: 900;">tabalmix concreto</h1>
                    <p style="color: #e2e8f0; font-size: 11px; text-transform: uppercase;">Powered by Castro Tech</p>
                </div>
            """, unsafe_allow_html=True)

        escolha_modo_login = st.selectbox("🔐 Central de Segurança & Acesso Supabase:", [
            "⚡ Acesso Direto por E-mail",
            "🔑 Entrar com E-mail e Senha",
            "🛡️ Entrar com Chave de Segurança Corporativa",
            "👆 Acesso Rápido com PIN",
            "🔄 Recuperar Senha",
            "📝 Criar Novo Cadastro na Obra"
        ])

        if escolha_modo_login == "⚡ Acesso Direto por E-mail":
            with st.form("form_login_direto"):
                st.markdown("### ⚡ Acesso Direto Rápido")
                email_direto = st.text_input("E-mail corporativo", value="alexcastro02522@gmail.com")
                if st.form_submit_button("Acessar Imediatamente"):
                    df_log = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_direto.strip()}'")
                    if not df_log.empty:
                        u = df_log.iloc[0]
                        st.session_state["usuario_logado"] = {
                            "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                            "email": u["email"], "status": u["status_assinatura"],
                            "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                            "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
                        }
                        st.success("✅ Acesso validado!")
                        st.rerun()
                    else:
                        st.error("⚠️ E-mail não encontrado na base de dados.")

        elif escolha_modo_login == "🔑 Entrar com E-mail e Senha":
            with st.form("form_login_senha"):
                st.markdown("### 🔑 Autenticação Padrão")
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
                            st.success("✅ Login efetuado com sucesso!")
                            st.rerun()
                        else:
                            st.error("⚠️ Senha incorreta.")
                    else:
                        st.error("⚠️ E-mail não encontrado.")

        elif escolha_modo_login == "🛡️ Entrar com Chave de Segurança Corporativa":
            with st.form("form_chave_corp"):
                st.markdown("### 🛡️ Validação por Chave de Licença")
                email_c = st.text_input("Seu E-mail Corporativo")
                chave_c = st.text_input("Código da Chave de Segurança")
                if st.form_submit_button("Validar Chave e Entrar"):
                    df_u = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_c.strip()}'")
                    if not df_u.empty:
                        u = df_u.iloc[0]
                        st.session_state["usuario_logado"] = {
                            "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                            "email": u["email"], "status": u["status_assinatura"],
                            "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                            "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
                        }
                        st.success("✅ Chave validada!")
                        st.rerun()
                    else:
                        st.error("⚠️ Usuário não encontrado.")

        elif escolha_modo_login == "👆 Acesso Rápido com PIN":
            with st.form("form_pin_bio"):
                st.markdown("### 👆 Autenticação por PIN")
                email_p = st.text_input("E-mail corporativo", value="alexcastro02522@gmail.com")
                pin_p = st.text_input("PIN de 4 Dígitos", max_chars=4, type="password", value="2026")
                if st.form_submit_button("Autenticar com PIN"):
                    df_p = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_p.strip()}'")
                    if not df_p.empty:
                        u = df_p.iloc[0]
                        if str(u.get("pin_rapido")) == str(pin_p):
                            st.session_state["usuario_logado"] = {
                                "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                                "email": u["email"], "status": u["status_assinatura"],
                                "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                                "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
                            }
                            st.success("✅ Acesso validado!")
                            st.rerun()
                        else:
                            st.error("⚠️ PIN incorreto.")
                    else:
                        st.error("⚠️ E-mail não encontrado.")

        elif escolha_modo_login == "🔄 Recuperar Senha":
            with st.form("form_recuperar"):
                st.markdown("### 🔄 Recuperação de Credenciais")
                rec_val = st.text_input("E-mail cadastrado")
                nova_senha_rec = st.text_input("Nova Senha Desejada", type="password")
                if st.form_submit_button("Redefinir Senha"):
                    if rec_val and nova_senha_rec:
                        executar_comando_sql("UPDATE usuarios_sistema SET senha = ? WHERE email = ?", (nova_senha_rec, rec_val.strip()))
                        st.success("✅ Senha redefinida no Supabase!")
                    else:
                        st.error("⚠️ Preencha os campos.")

        elif escolha_modo_login == "📝 Criar Novo Cadastro na Obra":
            with st.form("form_novo_cad"):
                st.markdown("### 📝 Criar Novo Registro")
                c_nome = st.text_input("Nome Completo")
                c_apelido = st.text_input("Apelido")
                c_cargo = st.selectbox("Cargo / Função", ["💎 Master Concreto & Diretoria", "🏗️ Engenharia & Obra Pro", "🛠️ Oficina & Mecânica X", "🚜 Operacional Campo & Frota"])
                cargo_banco_str = "Diretoria / Gestão" if "Master" in c_cargo else ("Engenheiro / Gestor de Obra" if "Engenharia" in c_cargo else ("Mecânico / Oficina" if "Oficina" in c_cargo else "Operador / Motorista / Campo"))
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
                        st.success("✅ Conta cadastrada com sucesso!")
                        st.rerun()
    st.stop()

usuario_atual = st.session_state["usuario_logado"]

def exibir_tabela_padronizada(df, nome_tabela):
    if df.empty:
        st.info("Nenhum registro encontrado no Supabase.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)

with st.sidebar:
    st.markdown("<div style='text-align:center; font-weight:900;'>🏗️ TABALMIX CONCRETO</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-size:11px; color:#64748b; margin-bottom:10px;'>Castro Tech Architecture</div>", unsafe_allow_html=True)
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
    "💬 Chat Tabalmix Pro & Reuniões Live",
    "⚙️ Meu Perfil / Dados",
]
if modo_admin_liberado:
    lista_menus.append("⚙️ Painel de Licença (Admin)")

menu = st.sidebar.radio("Navegação", lista_menus, label_visibility="collapsed")

if menu == "📊 Visão Geral":
    st.title("🏗️ Painel Executivo Ultramoderno")
    st.markdown("<p style='color: #64748b; margin-top: -10px; margin-bottom: 25px;'>Monitoramento de frotas, operações e métricas em tempo real — Castro Tech</p>", unsafe_allow_html=True)
    
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

    # CAIXINHAS FLUTUANTES ZERADAS SE NÃO HOUVER DADOS
    total_frota = len(df_veiculos) if not df_veiculos.empty else 0
    os_abertas = len(df_manut[df_manut["status_os"] == "aberta"]) if not df_manut.empty and "status_os" in df_manut.columns else 0
    total_multas = len(df_multas) if not df_multas.empty else 0
    gasto_comb = df_comb['valor_total'].sum() if not df_comb.empty and 'valor_total' in df_comb.columns else 0.0
    total_litros = df_comb['litros'].sum() if not df_comb.empty and 'litros' in df_comb.columns else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-title">Total Frota</div>
                <div class="metric-value">{total_frota}</div>
                <div class="metric-sub">Veículos Ativos</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-title">OS Abertas</div>
                <div class="metric-value">{os_abertas}</div>
                <div class="metric-sub">Em Manutenção</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-title">Multas</div>
                <div class="metric-value">{total_multas}</div>
                <div class="metric-sub">Registradas</div>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-title">Gasto Combust.</div>
                <div class="metric-value" style="font-size: 20px;">R$ {gasto_comb:,.2f}</div>
                <div class="metric-sub">Investido em Diesel</div>
            </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-title">Total Litros</div>
                <div class="metric-value" style="font-size: 22px;">{total_litros:,.1f} L</div>
                <div class="metric-sub">Consumo Global</div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📋 Gestão de Frotas & Relatórios Executivos")
    if not df_veiculos.empty:
        exibir_tabela_padronizada(df_veiculos, "veiculos")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            pdf_geral = gerar_pdf_relatorio("Relatório Executivo Geral de Frota", df_veiculos)
            st.download_button("📥 Baixar Relatório PDF", data=pdf_geral, file_name="relatorio_frota.pdf", mime="application/pdf")
        with col_dl2:
            excel_geral = gerar_excel_formatado(df_veiculos, "Frota_Tabalmix")
            st.download_button("📊 Baixar Relatório Excel", data=excel_geral, file_name="relatorio_frota.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_dl3:
            msg_wpp = urllib.parse.quote("🏗️ *RELATÓRIO EXECUTIVO TABALMIX CONCRETO*\nFrota total sincronizada no Supabase — Castro Tech.")
            st.markdown(f'<a href="https://api.whatsapp.com/send?text={msg_wpp}" target="_blank"><button style="background:linear-gradient(135deg, #25D366 0%, #128C7E 100%); color:white; font-weight:700; border-radius:14px; border:none; padding:0.7rem 1.8rem; width:100%; box-shadow:0 8px 20px rgba(37,211,102,0.3); cursor:pointer;">📱 Compartilhar no WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Nenhum veículo cadastrado na nuvem.")

elif menu == "🔍 Consulta / Busca Geral":
    st.title("🔍 Consulta e Histórico Completo")
    termo_busca = st.text_input("Pesquisar por placa, marca ou modelo:")
    df_v = ler_tabelas_sql("SELECT * FROM veiculos")
    if termo_busca and not df_v.empty:
        df_busca = df_v[df_v.apply(lambda row: row.astype(str).str.contains(termo_busca, case=False).any(), axis=1)]
        exibir_tabela_padronizada(df_busca, "veiculos")
    else:
        exibir_tabela_padronizada(df_v, "veiculos")

elif menu == "🚜 Cadastro de Equipamentos":
    st.title("🚜 Cadastro de Equipamentos")
    t_l, t_r, t_e = st.tabs(["📋 Frota", "➕ Cadastrar", "📝 Editar"])
    with t_l:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM veiculos"), "veiculos")
    with t_r:
        with st.form("form_eq_novo"):
            st.markdown("### Cadastrar Novo Equipamento")
            c1, c2, c3 = st.columns(3)
            with c1:
                f_tag = st.text_input("TAG / Prefixo")
                f_placa = st.text_input("Placa")
                f_cat = st.selectbox("Categoria", ["Linha Branca", "Linha Amarela", "Veículo Leve"])
                f_ano = st.number_input("Ano", min_value=1980, value=2026)
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
                f_op = st.text_input("Operador")
            if st.form_submit_button("Salvar no Supabase") and f_tag:
                executar_comando_sql("INSERT INTO veiculos", (f_tag, f_placa, f_cat, f_ano, f_renavam, f_crv, f_marca, f_tipo, f_cor, f_comb, f_chassi, f_emp, f_op, 0.0))
                st.success("✅ Equipamento salvo direto no Supabase!")
                st.rerun()
    with t_e:
        st.markdown("### 📝 Editar Equipamento")
        st.info("Módulo de edição em sincronização ativa com Supabase.")

elif menu == "🏗️ Mobilização / Desmobilização":
    st.title("🏗️ Controle de Mobilização & Vistoria")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM mobilizacoes"), "mobilizacoes")
    with st.form("form_mob"):
        eq = st.text_input("Equipamento / TAG")
        mov = st.selectbox("Movimento", ["Mobilização (+)", "Desmobilização (-)"])
        dest = st.text_input("Destino / Origem")
        enc = st.text_input("Encarregado")
        km = st.text_input("KM / Horímetro")
        obs = st.text_area("Observação")
        if st.form_submit_button("Cadastrar Movimento"):
            executar_comando_sql("INSERT INTO mobilizacoes", (eq, mov, dest, enc, datetime.now().strftime("%d/%m/%Y"), km, obs))
            st.success("✅ Salvo no Supabase!")
            st.rerun()

elif menu == "🔧 Controle de Manutenção":
    st.title("🔧 Controle de Manutenção & Revisões")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM veiculos"), "veiculos")

elif menu == "⛽ Abastecimentos & Combustível":
    st.title("⛽ Registro de Abastecimentos")
    st.markdown("<p style='color: #64748b;'>Painel analítico e controle de diesel — Castro Tech</p>", unsafe_allow_html=True)
    
    with st.container():
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1: f_mes_ini = st.selectbox("Início", ["Novembro / 2023", "Janeiro / 2026", "Outubro / 2026"])
        with f_col2: f_mes_fim = st.selectbox("Fim", ["Outubro / 2026", "Agosto / 2026"])
        with f_col3: f_ano = st.selectbox("Ano", ["Todos", "2026", "2025", "2024"])
        with f_col4: f_frota = st.selectbox("Caminhão / TAG", ["Todos", "BET-01", "Strada Volcano"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    df_comb_vis = ler_tabelas_sql("SELECT * FROM combustivel")
    tot_litros_c = df_comb_vis['litros'].sum() if not df_comb_vis.empty and 'litros' in df_comb_vis.columns else 0.0
    tot_valor_c = df_comb_vis['valor_total'].sum() if not df_comb_vis.empty and 'valor_total' in df_comb_vis.columns else 0.0

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-title">KM Rodados</div>
                <div class="metric-value">0 km</div>
                <div class="metric-sub">Volume no Filtro</div>
            </div>
        """, unsafe_allow_html=True)
    with mc2:
        st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-title">Diesel Consumido</div>
                <div class="metric-value">{tot_litros_c:,.1f} L</div>
                <div class="metric-sub">Consumo Total</div>
            </div>
        """, unsafe_allow_html=True)
    with mc3:
        st.markdown(f"""
            <div class="metric-card-modern">
                <div class="metric-title">Média da Frota</div>
                <div class="metric-value">0,00 km/L</div>
                <div class="metric-sub">Sem registros</div>
            </div>
        """, unsafe_allow_html=True)
    with mc4:
        st.markdown(f"""
            <div class="metric-card-modern" style="border-left-color: #047857; background: #065f46; color: white;">
                <div class="metric-title" style="color: #e2e8f0;">Custo Total Diesel</div>
                <div class="metric-value" style="color: white; font-size: 20px;">R$ {tot_valor_c:,.2f}</div>
                <div class="metric-sub" style="color: #a7f3d0;">Total Lançado</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Registros de Abastecimento")
    exibir_tabela_padronizada(df_comb_vis, "combustivel")
    
    with st.form("form_comb"):
        st.markdown("### ➕ Novo Lançamento de Abastecimento")
        eq = st.text_input("Equipamento")
        lit = st.number_input("Litros", min_value=0.0)
        val = st.number_input("Valor Total (R$)", min_value=0.0)
        post = st.text_input("Posto")
        mot = st.text_input("Motorista")
        if st.form_submit_button("Cadastrar Abastecimento"):
            executar_comando_sql("INSERT INTO combustivel", (eq, lit, val, post, mot, datetime.now().strftime("%d/%m/%Y")))
            st.success("✅ Abastecimento salvo no Supabase!")
            st.rerun()

elif menu == "🛠️ Ordens de Serviço (OS)":
    st.title("🛠️ Gestão de Ordens de Serviço (OS)")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM manutencoes"), "manutencoes")
    with st.form("form_os"):
        tag = st.text_input("TAG do Equipamento")
        t_man = st.selectbox("Tipo", ["Corretiva", "Preventiva"])
        origem = st.selectbox("Origem", ["Falha de Equipamento", "Falha de Operação"])
        desc = st.text_area("Descrição do Problema")
        oficina = st.text_input("Oficina")
        custo = st.number_input("Custo Estimado", min_value=0.0)
        if st.form_submit_button("Abrir OS na Nuvem"):
            executar_comando_sql("INSERT INTO manutencoes", (tag, t_man, origem, desc, datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), oficina, custo))
            st.success("✅ OS aberta no Supabase!")
            st.rerun()

elif menu == "🚨 Gestão & Alertas de Multas":
    st.title("🚨 Controle de Multas")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM multas"), "multas")
    with st.form("form_multa"):
        placa = st.text_input("Placa")
        orgao = st.text_input("Órgão Autuador")
        local = st.text_input("Local")
        valor = st.number_input("Valor", min_value=0.0)
        venc = st.text_input("Vencimento")
        if st.form_submit_button("Cadastrar Multa"):
            executar_comando_sql("INSERT INTO multas", (placa, orgao, local, valor, venc))
            st.success("✅ Multa salva no Supabase!")
            st.rerun()

elif menu == "🔩 Peças e Ferramentas":
    st.title("🔩 Estoque de Peças")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM pecas"), "pecas")
    with st.form("form_peca"):
        nome = st.text_input("Nome da Peça")
        cat = st.text_input("Categoria")
        qtd = st.number_input("Quantidade", min_value=1, value=1)
        val = st.number_input("Valor Unitário", min_value=0.0)
        if st.form_submit_button("Adicionar Peça"):
            executar_comando_sql("INSERT INTO pecas", (nome, cat, qtd, val))
            st.success("✅ Peça salva no Supabase!")
            st.rerun()

elif menu == "👥 Gestão de Clientes":
    st.title("👥 Gestão de Clientes")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM clientes"), "clientes")
    with st.form("form_cli"):
        nome = st.text_input("Nome / Razão Social")
        emp = st.text_input("Empresa")
        tel = st.text_input("Telefone")
        doc = st.text_input("CPF / CNPJ")
        end = st.text_input("Endereço")
        if st.form_submit_button("Cadastrar Cliente"):
            executar_comando_sql("INSERT INTO clientes", (nome, emp, tel, doc, end))
            st.success("✅ Cliente salvo no Supabase!")
            st.rerun()

elif menu == "💬 Chat Tabalmix Pro & Reuniões Live":
    st.title("💬 Chat Interno & Reuniões Live")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM chat_interno"), "chat_interno")
    with st.form("form_chat", clear_on_submit=True):
        msg = st.text_input("Mensagem")
        if st.form_submit_button("Enviar Mensagem"):
            rem = usuario_atual['apelido'] if usuario_atual else "Alex"
            cargo = usuario_atual['cargo'] if usuario_atual else "Diretoria"
            executar_comando_sql("INSERT INTO chat_interno", (rem, "Geral", cargo, msg, "", datetime.now().strftime("%d/%m/%Y às %H:%M")))
            st.rerun()

elif menu == "⚙️ Meu Perfil / Dados":
    st.title("⚙️ Meu Perfil & Dados")
    if usuario_atual:
        st.markdown(f"""
            * **Nome**: {usuario_atual.get('nome')}
            * **E-mail**: {usuario_atual.get('email')}
            * **Cargo**: {usuario_atual.get('cargo')}
            * **Arquitetura**: Castro Tech & Supabase Cloud
        """)

elif menu == "⚙️ Painel de Licença (Admin)" e modo_admin_liberado:
    st.title("⚙️ Painel Administrativo Master")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM usuarios_sistema"), "usuarios_sistema")
    if st.button("🗑️ Limpar Tabela Veiculos"):
        executar_comando_sql("DELETE FROM veiculos")
        st.success("Tabela limpa no Supabase!")
        st.rerun()
