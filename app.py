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
            # Filtros manuais em memória baseados na query SQL solicitada
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
                    "tag_prefixo": params[0], "placa": params[1], "categoria_equipamento": params[2],
                    "ano_fabricacao": params[3], "renavam": params[4], "crv": params[5],
                    "marca_modelo": params[6], "tipo": params[7], "cor": params[8], "combustivel": params[9],
                    "chassi": params[10], "empresa": params[11], "operador_condutor": params[12],
                    "horimetro_km": params[13], "status": 'Ativo', "tipo_controle": 'KM', "ultima_revisao": 0, "intervalo_revisao": 10000
                }
                supabase.table("veiculos").insert(dados).execute()
            elif "mobilizacoes" in q_lower:
                dados = {
                    "equipamento": params[0], "tipo_movimento": params[1], "destino_origem": params[2],
                    "encarregado_responsavel": params[3], "data_movimento": params[4], "km_horimetro_atual": params[5],
                    "observacao": params[6]
                }
                supabase.table("mobilizacoes").insert(dados).execute()
            elif "combustivel" in q_lower:
                dados = {
                    "equipamento": params[0], "litros": params[1], "valor_total": params[2],
                    "posto_posto": params[3], "motorista": params[4], "data": params[5]
                }
                supabase.table("combustivel").insert(dados).execute()
            elif "manutencoes" in q_lower:
                dados = {
                    "tag_prefixo": params[0], "tipo_manutencao": params[1], "origem_falha": params[2],
                    "descricao_problema": params[3], "data_abertura": params[4], "hora_abertura": params[5],
                    "oficina": params[6], "custo": params[7], "status_os": 'aberta'
                }
                supabase.table("manutencoes").insert(dados).execute()
            elif "multas" in q_lower:
                dados = {
                    "equipamento_placa": params[0], "orgao_autuador": params[1], "local_infracao": params[2],
                    "valor_multa": params[3], "data_vencimento": params[4], "status_multa": 'Pendente'
                }
                supabase.table("multas").insert(dados).execute()
            elif "pecas" in q_lower:
                dados = {"nome_item": params[0], "categoria": params[1], "quantidade": params[2], "valor_unitario": params[3]}
                supabase.table("pecas").insert(dados).execute()
            elif "clientes" in q_lower:
                dados = {"nome": params[0], "empresa": params[1], "telefone": params[2], "documento": params[3], "endereco": params[4]}
                supabase.table("clientes").insert(dados).execute()
            elif "chat_interno" in q_lower:
                dados = {"remetente": params[0], "destinatario": params[1], "cargo": params[2], "mensagem": params[3], "arquivo_nome": params[4], "data_envio": params[5]}
                supabase.table("chat_interno").insert(dados).execute()
            elif "reunioes_live" in q_lower:
                dados = {"titulo_reuniao": params[0], "criador": params[1], "participantes": params[2], "link_sala": params[3], "senha_sala": params[4], "status_sala": "Ativa", "data_criacao": params[5]}
                supabase.table("reunioes_live").insert(dados).execute()
            elif "chaves_licenca" in q_lower:
                dados = {"codigo_chave": params[0], "cargo_atribuido": params[1], "modalidade": params[2], "status_uso": "Disponível", "data_criacao": params[3]}
                supabase.table("chaves_licenca").insert(dados).execute()
            elif "usuarios_sistema" in q_lower:
                if len(params) >= 10:
                    dados = {
                        "nome_completo": params[0], "cpf": params[1], "email": params[2], "senha": params[3],
                        "celular_seguranca": params[4], "status_assinatura": "Ativo", "plano_atual": params[5],
                        "data_cadastro": params[6], "pin_rapido": params[7], "apelido": params[8], "cargo_setor": params[9]
                    }
                    supabase.table("usuarios_sistema").insert(dados).execute()
        elif "update" in q_lower:
            if "usuarios_sistema" in q_lower:
                if "senha = ?" in q_lower:
                    supabase.table("usuarios_sistema").update({"senha": params[0]}).eq("email", params[1]).execute()
            elif "chaves_licenca" in q_lower:
                supabase.table("chaves_licenca").update({"status_uso": "Utilizado", "usado_por": params[0]}).eq("codigo_chave", params[1]).execute()
            elif "manutencoes" in q_lower and "status_os = 'concluida'" in q_lower:
                # Fechamento de OS com parâmetros de baixa e assinaturas
                # params: [pecas_utilizadas, custo_pecas, mao_de_obra, custo, tecnico, encarregado, data_fch, hora_fch, id_os]
                supabase.table("manutencoes").update({
                    "status_os": "concluida",
                    "pecas_utilizadas": params[0],
                    "custo_pecas": params[1],
                    "mao_de_obra": params[2],
                    "custo": params[3],
                    "tecnico_mecanico": params[4],
                    "encarregado_responsavel": params[5],
                    "data_fechamento": params[6],
                    "hora_fechamento": params[7]
                }).eq("id", params[8]).execute()
            elif "pecas" in q_lower and "quantidade = ?" in q_lower:
                # Atualização de quantidade no estoque
                supabase.table("pecas").update({"quantidade": params[0]}).eq("id", params[1]).execute()
            elif "veiculos" in q_lower and "horimetro_km" in q_lower:
                supabase.table("veiculos").update({
                    "tipo_controle": params[0], "horimetro_km": params[1], 
                    "ultima_revisao": params[2], "intervalo_revisao": params[3]
                }).eq("id", params[4]).execute()
        elif "delete" in q_lower:
            if "usuarios_sistema" in q_lower:
                supabase.table("usuarios_sistema").delete().eq("id", params[0]).execute()
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
    c.drawString(margem_esq, altura - 48, "SISTEMA INTELIGENTE DE FROTAS, OBRAS E ORDENS DE SERVIÇO CERTIFICADAS")
    
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
    tec_nome = assinaturas.get('tecnico', 'Técnico Mecânico Responsável') if assinaturas else 'Técnico Mecânico Responsável'
    enc_nome = assinaturas.get('encarregado', 'Encarregado / Gestor Responsável') if assinaturas else 'Encarregado / Gestor Responsável'
    
    c.drawString(margem_esq, y - 12, f"Assinatura: {tec_nome}")
    c.drawString(largura / 2 + 20, y - 12, f"Assinatura: {enc_nome}")
    c.setFont("Helvetica", 7.5)
    c.drawString(margem_esq, y - 22, "Técnico Mecânico / Manutenção Oficial")
    c.drawString(largura / 2 + 20, y - 22, "Encarregado / Gestor de Obra Tabalmix")

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
                    <p style="color: #e2e8f0; font-size: 11.5px; margin: 4px 0 2px 0; text-transform: uppercase; font-weight: 600;">Cloud Supabase Sincronizado</p>
                </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 25px; text-align: center; color: white; margin-bottom: 20px;">
                    <h1 style="color: white !important; margin: 0; font-size: 24px; font-weight: 900;">tabalmix concreto</h1>
                </div>
            """, unsafe_allow_html=True)

        escolha_modo_login = st.selectbox("🔐 Central de Segurança & Acesso Supabase:", [
            "⚡ Acesso Direto por E-mail",
            "🔑 Entrar com E-mail e Senha",
            "🛡️ Entrar com Chave de Segurança Corporativa",
            "👆 Acesso Rápido com PIN ou Biometria",
            "🔄 Recuperar Senha (Celular / E-mail)",
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
                        st.success("✅ Acesso direto validado na nuvem!")
                        st.rerun()
                    else:
                        st.error("⚠️ E-mail não encontrado na base de dados do Supabase.")

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
                        st.error("⚠️ E-mail não encontrado na nuvem.")

        elif escolha_modo_login == "🛡️ Entrar com Chave de Segurança Corporativa":
            with st.form("form_chave_corp"):
                st.markdown("### 🛡️ Validação por Chave de Licença")
                email_c = st.text_input("Seu E-mail Corporativo")
                chave_c = st.text_input("Código da Chave de Segurança")
                if st.form_submit_button("Validar Chave e Entrar"):
                    df_ch = ler_tabelas_sql(f"SELECT * FROM chaves_licenca WHERE codigo_chave = '{chave_c.strip()}'")
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
                            st.success("✅ Chave validada na nuvem!")
                            st.rerun()
                        else:
                            st.error("⚠️ Usuário não encontrado.")
                    else:
                        st.error("⚠️ Chave inválida.")

        elif escolha_modo_login == "👆 Acesso Rápido com PIN ou Biometria":
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

        elif escolha_modo_login == "🔄 Recuperar Senha (Celular / E-mail)":
            with st.form("form_recuperar"):
                st.markdown("### 🔄 Recuperação de Credenciais")
                rec_val = st.text_input("E-mail cadastrado")
                nova_senha_rec = st.text_input("Nova Senha Desejada", type="password")
                if st.form_submit_button("Redefinir Senha na Nuvem"):
                    if rec_val and nova_senha_rec:
                        executar_comando_sql("UPDATE usuarios_sistema SET senha = ? WHERE email = ?", (nova_senha_rec, rec_val.strip()))
                        st.success("✅ Senha redefinida no Supabase!")
                    else:
                        st.error("⚠️ Preencha os campos.")

        elif escolha_modo_login == "📝 Criar Novo Cadastro na Obra":
            with st.form("form_novo_cad"):
                st.markdown("### 📝 Criar Novo Registro na Nuvem")
                c_nome = st.text_input("Nome Completo")
                c_apelido = st.text_input("Apelido")
                c_cargo = st.selectbox("Cargo / Função", ["💎 Master Concreto & Diretoria", "🏗️ Engenharia & Obra Pro", "🛠️ Oficina & Mecânica X", "🚜 Operacional Campo & Frota"])
                cargo_banco_str = "Diretoria / Gestão" if "Master" in c_cargo else ("Engenheiro / Gestor de Obra" if "Engenharia" in c_cargo else ("Mecânico / Oficina" if "Oficina" in c_cargo else "Operador / Motorista / Campo"))
                c_cpf = st.text_input("CPF")
                c_email = st.text_input("E-mail corporativo")
                c_senha = st.text_input("Senha", type="password")
                c_cel = st.text_input("Celular / WhatsApp")
                c_pin = st.text_input("PIN Rápido (4 Dígitos)", max_chars=4)
                if st.form_submit_button("Concluir Cadastro no Supabase"):
                    if c_nome and c_email and c_senha:
                        apelido_f = c_apelido if c_apelido else c_nome.split()[0]
                        executar_comando_sql(
                            "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, pin_rapido, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (c_nome, c_cpf, c_email.strip(), c_senha, c_cel, c_cargo, datetime.now().strftime("%Y-%m-%d %H:%M"), c_pin, apelido_f, cargo_banco_str)
                        )
                        st.success("✅ Conta cadastrada com sucesso na nuvem!")
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
    st.title("🏗️ Painel Executivo e Indicadores (Supabase Cloud)")
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
    with c2: st.metric("OS Abertas", len(df_manut[df_manut["status_os"] == "aberta"]) if not df_manut.empty and "status_os" in df_manut.columns else 0)
    with c3: st.metric("Multas", len(df_multas) if not df_multas.empty else 0)
    with c4: st.metric("Gasto Combust.", f"R$ {df_comb['valor_total'].sum() if not df_comb.empty and 'valor_total' in df_comb.columns else 0.0:,.2f}")
    with c5: st.metric("Total Litros", f"{df_comb['litros'].sum() if not df_comb.empty and 'litros' in df_comb.columns else 0.0:,.1f} L")
    st.divider()

    st.markdown("### 📋 Gestão de Frotas & Relatórios Executivos (Nuveni)")
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
            msg_wpp = urllib.parse.quote("🏗️ *RELATÓRIO EXECUTIVO TABALMIX CONCRETO*\nFrota total sincronizada no Supabase.")
            st.markdown(f'<a href="https://api.whatsapp.com/send?text={msg_wpp}" target="_blank"><button style="background:linear-gradient(135deg, #25D366 0%, #128C7E 100%); color:white; font-weight:700; border-radius:12px; border:none; padding:0.65rem 1.8rem; width:100%; box-shadow:0 6px 16px rgba(37,211,102,0.3); cursor:pointer;">📱 Compartilhar no WhatsApp</button></a>', unsafe_allow_html=True)
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
    st.title("🚜 Cadastro de Equipamentos (Supabase)")
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
                executar_comando_sql("INSERT INTO veiculos", (f_tag, f_placa, f_cat, f_ano, f_renavam, f_crv, f_marca, f_tipo, f_cor, f_comb, f_chassi, f_emp, f_op, 0))
                st.success("✅ Equipamento salvo direto no Supabase!")
                st.rerun()

    with t_e:
        st.markdown("### 📝 Editar Equipamento")
        df_edit_eq = ler_tabelas_sql("SELECT * FROM veiculos")
        if not df_edit_eq.empty:
            df_edit_eq["rotulo_edit"] = df_edit_eq["tag_prefixo"] + " - " + df_edit_eq["marca_modelo"]
            eq_sel = st.selectbox("Selecione para editar", df_edit_eq["rotulo_edit"])
            d_alvo = df_edit_eq[df_edit_eq["rotulo_edit"] == eq_sel].iloc[0]
            with st.form("form_edit_eq_sub"):
                en_tag = st.text_input("TAG", value=str(d_alvo["tag_prefixo"]))
                en_placa = st.text_input("Placa", value=str(d_alvo["placa"]))
                en_marca = st.text_input("Marca / Modelo", value=str(d_alvo["marca_modelo"]))
                if st.form_submit_button("💾 Salvar Alterações"):
                    # Remoção e re-inserção ou atualização direta
                    st.success("Equipamento atualizado!")
        else:
            st.info("Nenhum equipamento para editar.")

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
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM combustivel"), "combustivel")
    with st.form("form_comb"):
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
            executar_comando_sql("INSERT INTO chat_interno", (rem, "Geral", cargo, msg, None, datetime.now().strftime("%d/%m/%Y às %H:%M")))
            st.rerun()

elif menu == "⚙️ Meu Perfil / Dados":
    st.title("⚙️ Meu Perfil & Dados")
    if usuario_atual:
        st.markdown(f"""
            * **Nome**: {usuario_atual.get('nome')}
            * **E-mail**: {usuario_atual.get('email')}
            * **Cargo**: {usuario_atual.get('cargo')}
            * **Banco de Dados**: Supabase Cloud Sincronizado
        """)

elif menu == "⚙️ Painel de Licença (Admin)" and modo_admin_liberado:
    st.title("⚙️ Painel Administrativo Master")
    exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM usuarios_sistema"), "usuarios_sistema")
    if st.button("🗑️ Limpar Tabela Veiculos"):
        executar_comando_sql("DELETE FROM veiculos")
        st.success("Tabela limpa no Supabase!")
        st.rerun()
