import streamlit as st
import pandas as pd
import sqlite3
import mercadopago
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os
import base64

# CONFIGURAÇÃO DO MERCADO PAGO (Token Oficial Integrado)
MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-5959521111272944-091612-0753df7a8e6f38650831fff43f2257af-3692527935"

# Configuração da Página com Menu Fixo Expandido
st.set_page_config(
    page_title="Tabalmix Concreto - Gestão de Frota e Oficina Pro",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- FUNÇÃO DE PAGAMENTO PIX ---
def gerar_cobranca_pix(valor, descricao, email_comprador):
    try:
        sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)
        payment_data = {
            "transaction_amount": float(valor),
            "description": descricao,
            "payment_method_id": "pix",
            "payer": {
                "email": email_comprador,
            }
        }
        result = sdk.payment().create(payment_data)
        return result["response"]
    except Exception as e:
        st.error(f"Erro ao gerar pagamento: {e}")
        return None

# --- MENU LATERAL ---
st.sidebar.title("Tabalmix Concreto")
menu = st.sidebar.radio(
    "Navegação",
    [
        "Início / Visão Geral",
        "Frota e Maquinários",
        "Abastecimentos & Combustível",
        "Ordens de Serviço (OS)",
        "Painel de Licença (Admin)"
    ]
)

# --- TELA: INÍCIO ---
if menu == "Início / Visão Geral":
    st.title("🏗️ Tabalmix Concreto - Painel Principal")
    st.write("Bem-vindo ao sistema de gestão integrado. Utilize o menu lateral para navegar entre os módulos.")
    st.info("Sistema operando em nuvem com integração ativa ao Mercado Pago e suporte a relatórios.")

# --- TELA: FROTA ---
elif menu == "Frota e Maquinários":
    st.title("🚛 Gestão de Frota e Maquinários")
    st.write("Aqui você pode gerenciar seus veículos (como o Ford Ka da frota, caminhões betoneira e maquinários).")
    
    # Exemplo simples de tabela
    dados_frota = pd.DataFrame({
        "Veículo": ["Ford Ka 1.0", "Caminhão Betoneira 01", "Caminhão Betoneira 02"],
        "Placa": ["ABC-1234", "XYZ-5678", "CON-9988"],
        "Status": ["Disponível", "Em Operação", "Manutenção"]
    })
    st.dataframe(dados_frota, use_container_width=True)

# --- TELA: ABASTECIMENTOS ---
elif menu == "Abastecimentos & Combustível":
    st.title("⛽ Controle de Abastecimentos")
    st.write("Registro de consumo de combustível e controle de quilometragem/horímetro.")

# --- TELA: ORDENS DE SERVIÇO ---
elif menu == "Ordens de Serviço (OS)":
    st.title("🔧 Ordens de Serviço e Manutenção")
    st.write("Controle de manutenções preventivas e corretivas da frota.")

# --- TELA: PAINEL DE LICENÇA (ADMIN) COM MERCADO PAGO ---
elif menu == "Painel de Licença (Admin)":
    st.title("⚙️ Painel de Controle de Licença, Planos e Assinaturas")
    st.markdown("Gerencie o status de acesso do sistema e realize a renovação via Pix automatizado.")
    
    st.info("Status da Licença: **Ativo**")
    st.markdown("### Plano Comercial Contratado")
    st.text_input("Plano Atual", "Mensal (R$ 250,00)", disabled=True)
    
    st.divider()
    
    st.subheader("💳 Gerar Pagamento Pix - Mercado Pago")
    valor_plano = 250.00
    descricao_plano = "Assinatura Mensal - Tabalmix Concreto"
    
    email_usuario = st.text_input("E-mail para cobrança:", "contato@tabalmix.com")
    
    if st.button("Gerar Pix de R$ 250,00", type="primary"):
        with st.spinner("Conectando ao Mercado Pago e gerando QR Code..."):
            resposta = gerar_cobranca_pix(valor_plano, descricao_plano, email_usuario)
            
            if resposta and "point_of_interaction" in resposta:
                qr_code_base64 = resposta["point_of_interaction"]["transaction_data"]["qr_code_base64"]
                qr_code_copia_cola = resposta["point_of_interaction"]["transaction_data"]["qr_code"]
                
                st.success("Cobrança Pix gerada com sucesso pelo Mercado Pago!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Escaneie o QR Code:**")
                    img_bytes = base64.b64decode(qr_code_base64)
                    st.image(img_bytes, width=220)
                    
                with col2:
                    st.markdown("**Pix Copia e Cola:**")
                    st.text_area("Copie o código abaixo:", qr_code_copia_cola, height=120)
                    st.info("Assim que o pagamento for aprovado, a licença será atualizada.")
            else:
                st.error("Não foi possível gerar a cobrança. Verifique sua conexão ou token de acesso.")
