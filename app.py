# VERIFICAÇÃO GLOBAL DE CHAMADA PENDENTE COM AUTO-REFRESH EM TEMPO REAL NO SMARTPHONE DELA
if usuario_atual:
  nome_apelido_atual = usuario_atual["apelido"]
  cursor.execute(
      "SELECT mensagem, data_envio FROM chat_interno WHERE destinatario LIKE ? AND mensagem LIKE '%CHAMADA DE VÍDEO ATIVA%' ORDER BY id DESC LIMIT 1",
      (f"%{nome_apelido_atual}%",),
  )
  chamada_pendente = cursor.fetchone()
  if chamada_pendente:
    st.markdown(
        """
            <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 20px 26px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 15px 35px rgba(220,38,38,0.6); display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="color: white !important; margin: 0; font-size: 19px;">🚨 CHAMADA DE VÍDEO A TOCAR AGORA!</h3>
                    <p style="margin: 4px 0 0 0; font-size: 14.5px;">Alguém está a chamar-te em tempo real para uma reunião ao vivo.</p>
                </div>
                <a href="?p=chat" target="_self" style="background: white; color: #991b1b; padding: 12px 24px; border-radius: 12px; font-weight: 800; text-decoration: none; font-size: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">ATENDER CHAMADA</a>
            </div>
            <script>
                setTimeout(function(){
                    window.location.reload();
                }, 3000);
            </script>
        """,
        unsafe_allow_html=True,
    )
  else:
    st.markdown(
        """
            <script>
                setTimeout(function(){
                    window.location.reload();
                }, 8000);
            </script>
        """,
        unsafe_allow_html=True,
    )
