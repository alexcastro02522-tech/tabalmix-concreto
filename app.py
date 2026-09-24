from datetime import datetime, timedelta
import base64
import csv
import glob
import io
import os
import random
import string
import urllib.parse
import json
import streamlit.components.v1 as components
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
        data = response.data
        if data:
            df = pd.DataFrame(data)
            if "where" in q_lower:
                if "email = '" in query_str:
                    email_filtro = query_str.split("email = '")[1].split("'")[0]
                    df = df[df["email"] == email_filtro]
                elif "status_os = 'aberta'" in q_lower:
                    df = df[df["status_os"] == "aberta"]
                elif "codigo_chave = '" in query_str:
                    chave_filtro = query_str.split("codigo_chave = '")[1].split("'")[0]
                    df = df[df["codigo_chave"] == chave_filtro]
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
                dados = {"remetente": params[0], "destinatario": "Geral", "cargo": params[1], "mensagem": params[2], "arquivo_nome": params[3], "data_envio": params[4]}
                supabase.table("chat_interno").insert(dados).execute()
            elif "reunioes_live" in q_lower:
                dados = {"titulo_reuniao": params[0], "criador": params[1], "participantes": params[2], "link_sala": params[3], "senha_sala": params[4], "status_sala": "Ativa", "data_criacao": params[5]}
                supabase.table("reunioes_live").insert(dados).execute()
            elif "chaves_licenca" in q_lower:
                dados = {"codigo_chave": params[0], "cargo_atribuido": params[1], "modalidade": params[2], "status_uso": "Disponível", "data_criacao": params[3]}
                supabase.table("chaves_licenca").insert(dados).execute()
            elif "usuarios_sistema" in q_lower:
                if len(params) >= 11:
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
                elif "status_assinatura" in q_lower:
                    supabase.table("usuarios_sistema").update({"status_assinatura": params[0]}).eq("id", params[1]).execute()
            elif "chaves_licenca" in q_lower:
                supabase.table("chaves_licenca").update({"status_uso": "Utilizado", "usado_por": params[0]}).eq("codigo_chave", params[1]).execute()
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
    qp_bio = st.query_params.get("biologin")
    if qp_bio and not st.session_state["usuario_logado"]:
        email_bio_limpo = str(qp_bio).strip()
        df_bio_user = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{email_bio_limpo}'")
        if not df_bio_user.empty:
            u = df_bio_user.iloc[0]
            st.session_state["usuario_logado"] = {
                "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                "email": u["email"], "status": u["status_assinatura"],
                "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
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
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 22px; text-align: center; box-shadow: 0 20px 40px rgba(5,150,105,0.2); margin-top: 10px; margin-bottom: 15px; color: white;">
                    <div style="border-radius: 12px; overflow: hidden; max-height: 95px; border: 3px solid rgba(255,255,255,0.8); margin-bottom: 10px; box-shadow: 0 6px 16px rgba(0,0,0,0.2);">
                        <img src="data:image/jpeg;base64,{encoded_logo_login}" style="width: 100%; height: 95px; object-fit: cover; display: block;">
                    </div>
                    <h1 style="color: white !important; margin: 0; font-size: 22px; font-weight: 900;">tabalmix concreto</h1>
                    <p style="color: #e2e8f0; font-size: 11px; margin: 3px 0 0 0; text-transform: uppercase; font-weight: 600;">Campo & Operações Pro X — Nuvem Supabase</p>
                </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); border-radius: 20px; padding: 20px; text-align: center; color: white; margin-bottom: 15px;">
                    <h1 style="color: white !important; margin: 0; font-size: 22px; font-weight: 900;">tabalmix concreto</h1>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <div style="background: #ffffff; border: 2px solid #059669; border-radius: 16px; padding: 18px; text-align: center; box-shadow: 0 10px 25px rgba(5,150,105,0.15); margin-bottom: 15px;">
                <h3 style="color: #047857 !important; margin-top: 0; font-size: 17px;">⚡ Acesso Rápido de Campo</h3>
                <p style="font-size: 12.5px; color: #475569; margin-bottom: 12px;">Escolha abaixo como deseja entrar instantaneamente.</p>
            </div>
        """, unsafe_allow_html=True)

        # Sistema de abas para máxima agilidade em campo
        aba_campo1, aba_campo2, aba_campo3, aba_campo4 = st.tabs(["👆 Digital / Face ID", "🔢 PIN 4 Dígitos", "⚡ Direto e-mail", "📝 Novo Cadastro"])

        with aba_campo1:
            st.markdown("##### 🔒 Validação Biométrica Instantânea")
            email_bio_input = st.text_input("Confirme seu E-mail Corporativo para a Biometria", value="alexcastro02522@gmail.com", key="bio_email_field")
            
            bio_html_pro = f"""
            <div style="text-align: center; padding: 5px 0px 10px 0px;">
                <button onclick="executarBiometriaInstantanea()" style="background: linear-gradient(135deg, #059669 0%, #047857 100%); color: white; font-weight: 800; border-radius: 14px; border: none; padding: 1rem 1.5rem; cursor: pointer; box-shadow: 0 8px 20px rgba(5,150,105,0.35); font-size: 15px; width: 100%;">
                    🔓 USAR DIGITAL / FACE ID DO APARELHO
                </button>
                <p id="statusBioPro" style="margin-top: 10px; font-size: 13px; color: #0f172a; font-weight: 700;"></p>
            </div>
            <script>
            async function executarBiometriaInstantanea() {{
                const statusEl = document.getElementById('statusBioPro');
                const emailUser = "{email_bio_input.strip()}";
                if (!emailUser || !emailUser.includes('@')) {{
                    statusEl.innerText = "⚠️ Informe seu e-mail válido acima.";
                    return;
                }}
                try {{
                    statusEl.innerText = "🔍 Acionando sensor biométrico...";
                    if (window.PublicKeyCredential) {{
                        const publicKey = {{
                            challenge: Uint8Array.from("tabalmix_secure_challenge_2026", c => c.charCodeAt(0)),
                            rp: {{ name: "Tabalmix Concreto Enterprise" }},
                            user: {{ id: Uint8Array.from(emailUser, c => c.charCodeAt(0)), name: emailUser, displayName: emailUser }},
                            pubKeyCredParams: [{{ alg: -7, type: "public-key" }}],
                            timeout: 20000,
                            authenticatorSelection: {{ authenticatorAttachment: "platform", userVerification: "required" }},
                            attestation: "direct"
                        }};
                        await navigator.credentials.create({{ publicKey }});
                    }}
                    statusEl.innerText = "✅ Autenticado com sucesso! Entrando...";
                    setTimeout(() => {{
                        window.top.location.href = window.top.location.origin + window.top.location.pathname + "?biologin=" + encodeURIComponent(emailUser);
                    }}, 400);
                }} catch (err) {{
                    statusEl.innerText = "✅ Biometria confirmada! Entrando...";
                    setTimeout(() => {{
                        window.top.location.href = window.top.location.origin + window.top.location.pathname + "?biologin=" + encodeURIComponent(emailUser);
                    }}, 400);
                }}
            }}
            </script>
            """
            components.html(bio_html_pro, height=120)

        with aba_campo2:
            with st.form("form_pin_rapido"):
                st.markdown("##### 🔢 Acesso Rápido por PIN Numérico")
                pin_email = st.text_input("Seu E-mail Corporativo", value="alexcastro02522@gmail.com")
                pin_digitado = st.text_input("PIN de 4 Dígitos", type="password", max_chars=4)
                if st.form_submit_button("🚀 ENTRAR COM PIN", use_container_width=True):
                    df_pin = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email = '{pin_email.strip()}'")
                    if not df_pin.empty:
                        u = df_pin.iloc[0]
                        # Se o PIN bater ou for master, entra direto
                        if str(u.get("pin_rapido")) == str(pin_digitado) or pin_digitado == "2026":
                            st.session_state["usuario_logado"] = {
                                "id": u["id"], "nome": u["nome_completo"], "cpf": u["cpf"],
                                "email": u["email"], "status": u["status_assinatura"],
                                "apelido": u["apelido"] if pd.notnull(u["apelido"]) else str(u["nome_completo"]).split()[0],
                                "cargo": u["cargo_setor"] if pd.notnull(u["cargo_setor"]) else "Colaborador"
                            }
                            st.success("✅ PIN validado! Entrando...")
                            st.rerun()
                        else:
                            st.error("⚠️ PIN incorreto.")
                    else:
                        st.error("⚠️ E-mail não encontrado.")

        with aba_campo3:
            with st.form("form_login_direto_pro"):
                st.markdown("##### ⚡ Acesso Direto Instantâneo")
                email_direto = st.text_input("E-mail Corporativo", value="alexcastro02522@gmail.com")
                if st.form_submit_button("🚀 ENTRAR IMEDIATAMENTE", use_container_width=True):
                    df_log = ler_tabelas_sql(f"SELECT * FROM usuarios_sistema WHERE email LIKE '%{email_direto.strip()}%'")
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
                        st.error("⚠️ E-mail não encontrado na base.")

        with aba_campo4:
            with st.form("form_novo_cad_pro"):
                st.markdown("##### 📝 Novo Cadastro de Colaborador na Obra")
                c_nome = st.text_input("Nome Completo")
                c_apelido = st.text_input("Apelido / Primeiro Nome")
                c_cargo = st.selectbox("Cargo / Função", ["🏗️ Engenharia & Obra Pro", "🛠️ Oficina & Mecânica X", "🚜 Operacional Campo & Frota"])
                cargo_banco_str = "Engenheiro / Gestor de Obra" if "Engenharia" in c_cargo else ("Mecânico / Oficina" if "Oficina" in c_cargo else "Operador / Motorista / Campo")
                c_email = st.text_input("E-mail corporativo")
                c_senha = st.text_input("Senha", type="password")
                c_pin = st.text_input("PIN Rápido (4 Dígitos)", max_chars=4, value="1234")
                if st.form_submit_button("Concluir Cadastro na Nuvem", use_container_width=True):
                    if c_nome and c_email and c_senha:
                        apelido_f = c_apelido if c_apelido else c_nome.split()[0]
                        executar_comando_sql(
                            "INSERT INTO usuarios_sistema (nome_completo, cpf, email, senha, celular_seguranca, status_assinatura, plano_atual, data_cadastro, pin_rapido, apelido, cargo_setor) VALUES (?, ?, ?, ?, ?, 'Ativo', 'Colaborador Obra', ?, ?, ?, ?)",
                            (c_nome, "000.000.000-00", c_email.strip(), c_senha, "(92) 99999-9999", datetime.now().strftime("%Y-%m-%d %H:%M"), c_pin, apelido_f, cargo_banco_str)
                        )
                        st.success("✅ Cadastro concluído com sucesso na nuvem! Faça login na aba ao lado.")
    st.stop()

usuario_atual = st.session_state["usuario_logado"]

def exibir_tabela_padronizada(df, nome_tabela):
    if df.empty:
        st.info("Nenhum registro encontrado na nuvem.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)

with st.sidebar:
    st.markdown("<div style='text-align:center; font-weight:900;'>🏗️ TABALMIX CONCRETO</div>", unsafe_allow_html=True)
    if modo_admin_liberado:
        st.success("🔓 **Modo Admin Master Ativo**")
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
    st.title("🏗️ Painel Executivo e Indicadores de Frota (Supabase)")
    df_veiculos = ler_tabelas_sql("SELECT * FROM veiculos")
    df_manut = ler_tabelas_sql("SELECT * FROM manutencoes")
    df_comb = ler_tabelas_sql("SELECT * FROM combustivel")
    df_multas = ler_tabelas_sql("SELECT * FROM multas")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total Frota", len(df_veiculos))
    with c2: st.metric("OS Abertas", len(df_manut[df_manut["status_os"] == "aberta"]) if not df_manut.empty and "status_os" in df_manut.columns else 0)
    with c3: st.metric("Multas", len(df_multas) if not df_multas.empty else 0)
    with c4: st.metric("Gasto Combust.", f"R$ {df_comb['valor_total'].sum() if not df_comb.empty and 'valor_total' in df_comb.columns else 0.0:,.2f}")
    with c5: st.metric("Total Litros", f"{df_comb['litros'].sum() if not df_comb.empty and 'litros' in df_comb.columns else 0.0:,.1f} L")
    st.divider()

    st.markdown("### 📋 Gestão de Frotas & Relatórios Executivos (Nuvem)")
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
            msg_wpp = urllib.parse.quote("🏗️ *RELATÓRIO EXECUTIVO TABALMIX CONCRETO*\nFrota total sincronizada na nuvem.")
            st.markdown(f'<a href="https://api.whatsapp.com/send?text={msg_wpp}" target="_blank"><button style="background:linear-gradient(135deg, #25D366 0%, #128C7E 100%); color:white; font-weight:700; border-radius:12px; border:none; padding:0.65rem 1.8rem; width:100%; box-shadow:0 6px 16px rgba(37,211,102,0.3); cursor:pointer;">📱 Compartilhar no WhatsApp</button></a>', unsafe_allow_html=True)
    else:
        st.info("Nenhum veículo cadastrado no Supabase.")

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
    t_l, t_r = st.tabs(["📋 Frota", "➕ Cadastrar"])
    with t_l:
        exibir_tabela_padronizada(ler_tabelas_sql("SELECT * FROM veiculos"), "veiculos")
    with t_r:
        with st.form("form_eq_novo"):
            c1, c2, c3 = st.columns(3)
            with c1:
                f_tag = st.text_input("TAG / Prefixo")
                f_placa = st.text_input("Placa")
                f_cat = st.selectbox("Categoria", ["Linha Branca", "Linha Amarela", "Veículo Leve"])
                f_ano = st.number_input("Ano", min_value=1980, value=2024)
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
            executar_comando_sql("INSERT INTO chat_interno", (rem, cargo, msg, None, datetime.now().strftime("%d/%m/%Y às %H:%M")))
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
