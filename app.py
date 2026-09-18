elif menu == "💬 chat tabalmix pro & rede":
  st.title("💬 Chat Tabalmix Pro & Central de Operações")
  st.markdown(
      "Comunicação unificada Enterprise: chats privados 1 a 1, canais de"
      " equipes, mural de avisos fixados e alerta SOS de emergência."
  )

  st.markdown(
      """
        <script>
        function dispararAlarmeSOS() {
            try {
                if (navigator.vibrate) {
                    navigator.vibrate([600, 200, 600, 200, 1000]);
                }
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(950, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 1.5);
            } catch(e) {}
        }

        function vibrarMensagemChat() {
            try {
                if (navigator.vibrate) {
                    navigator.vibrate([200, 100, 200]);
                }
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(600, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.3);
            } catch(e) {}
        }
        </script>
    """,
      unsafe_allow_html=True,
  )

  st.markdown(
      """
        <div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 14px; padding: 14px 20px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 15px rgba(239,68,68,0.1);">
            <div>
                <h4 style="margin: 0; color: #991b1b !important; font-size: 15.5px;">🚨 Botão de Pânico / Alerta SOS em Campo</h4>
                <p style="margin: 3px 0 0 0; font-size: 12px; color: #b91c1c;">Em caso de emergência ou pane grave, acione imediatamente para alertar a gerência e a oficina.</p>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  with st.expander("🚨 Acionar Alerta de Emergência SOS"):
    with st.form("form_sos_emergencia"):
      eq_sos = st.text_input(
          "Equipamento / Caminhão envolvido (ex: BET-05 ou EQ-01)"
      )
      motivo_sos = st.text_area(
          "Motivo do alerta (ex: pane elétrica, pneu estourado, acidente leve)"
      )
      btn_enviar_sos = st.form_submit_button(
          "🚨 DISPARAR ALERTA SOS IMEDIATO"
      )
      if btn_enviar_sos:
        if not motivo_sos:
          st.warning("⚠️ Descreva o motivo do alerta.")
        else:
          rem_sos = (
              usuario_atual["apelido"] if usuario_atual else "Colaborador"
          )
          dt_sos = datetime.now().strftime("%d/%m/%Y às %H:%M")
          cursor.execute(
              "INSERT INTO alertas_sos (remetente, equipamento, motivo,"
              " data_alerta, status) VALUES (?, ?, ?, ?, 'PENDENTE')",
              (rem_sos, eq_sos.upper(), motivo_sos, dt_sos),
          )
          conn.commit()
          st.error(
              "🚨 ALERTA SOS DISPARADO COM SUCESSO! A gerência foi notificada."
          )

  cursor.execute(
      "SELECT * FROM alertas_sos WHERE status = 'PENDENTE' ORDER BY id DESC"
  )
  lista_sos_pend = cursor.fetchall()
  if lista_sos_pend and (
      modo_admin_liberado
      or (
          usuario_atual
          and any(
              c in usuario_atual["cargo"]
              for c in [
                  "Gestão",
                  "Gerente",
                  "Admin",
                  "Segurança",
                  "Engenheiro",
                  "Diretoria",
              ]
          )
      )
  ):
    st.markdown(
        """
            <script>
            if (typeof dispararAlarmeSOS === 'function') {
                dispararAlarmeSOS();
            }
            </script>
        """,
        unsafe_allow_html=True,
    )

  if lista_sos_pend:
    st.markdown(
        "<h4 style='color: #dc2626;'>⚠️ ALERTAS SOS ATIVOS NA FROTA:</h4>",
        unsafe_allow_html=True,
    )
    for sos_item in lista_sos_pend:
      col_sos_info, col_sos_btn = st.columns([4, 1])
      with col_sos_info:
        st.markdown(
            f"""
                <div style="background: #fef2f2; border-left: 5px solid #dc2626; padding: 12px; border-radius: 10px; margin-bottom: 8px; font-size: 13px; box-shadow: 0 3px 10px rgba(0,0,0,0.03);">
                    <b>🚨 Emergência #{sos_item[0]}</b> | Solicitante: <b>{sos_item[1]}</b> | Equipamento: <b>{sos_item[2]}</b><br>
                    <b>Relato:</b> {sos_item[3]} <br> <span style="color: #6b7280; font-size: 11.5px;">Registrado em: {sos_item[4]}</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
      with col_sos_btn:
        if st.button(f"✅ Resolver #{sos_item[0]}", key=f"btn_res_sos_{sos_item[0]}"):
          cursor.execute(
              "UPDATE alertas_sos SET status = 'RESOLVIDO' WHERE id = ?",
              (sos_item[0],),
          )
          conn.commit()
          st.success(f"✅ Alerta #{sos_item[0]} marcado como resolvido!")
          st.rerun()

  st.markdown("---")
  st.markdown("#### 📌 Mural de Avisos Fixados (Diretoria / Engenharia)")
  
  # BUSCA ATÉ 5 AVISOS RECENTES
  cursor.execute("SELECT * FROM avisos_fixados ORDER BY id DESC LIMIT 5")
  avisos_fix = cursor.fetchall()
  
  eh_alto_escalao = modo_admin_liberado or (
      usuario_atual
      and any(
          c in usuario_atual["cargo"]
          for c in [
              "Gestão",
              "Gerente",
              "Admin",
              "Diretoria",
              "Engenheiro",
          ]
      )
  )

  if avisos_fix:
    for av in avisos_fix:
      col_av_txt, col_av_del = st.columns([12, 1])
      with col_av_txt:
        st.markdown(
            f"""
              <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; box-shadow: 0 4px 12px rgba(16,185,129,0.05);">
                  <span style="font-size: 11.5px; font-weight: bold; color: #047857;">📌 Comunicado Oficial de {av[1]} ({av[3]})</span>
                  <div style="font-size: 13.5px; color: #0f172a; margin-top: 3px;">{av[2]}</div>
              </div>
          """,
            unsafe_allow_html=True,
        )
      with col_av_del:
        if eh_alto_escalao:
          if st.button("❌", key=f"del_aviso_{av[0]}", help="Excluir este aviso"):
            cursor.execute("DELETE FROM avisos_fixados WHERE id = ?", (av[0],))
            conn.commit()
            st.success("✅ Aviso excluído com sucesso!")
            st.rerun()
  else:
    st.info("Nenhum aviso fixado no momento.")

  # APENAS ALTO ESCALÃO PODE ADICIONAR AVISOS
  if eh_alto_escalao:
    with st.expander("⚙️ [Alto Escalão] Fixar Novo Aviso no Mural"):
      with st.form("form_fixar_aviso"):
        texto_aviso = st.text_area("Texto do comunicado oficial (máximo de 5 avisos visíveis):")
        btn_fixar = st.form_submit_button("Fixar Comunicado")
        if btn_fixar and texto_aviso:
          # Verifica quantos avisos já existem
          cursor.execute("SELECT COUNT(*) FROM avisos_fixados")
          total_av = cursor.fetchone()[0]
          
          if total_av >= 5:
            st.warning("⚠️ O mural atingiu o limite de 5 avisos. Exclua um aviso antigo usando o botão '❌' ao lado para poder fixar um novo.")
          else:
            autor_av = (
                usuario_atual["apelido"] if usuario_atual else "Diretoria"
            )
            dt_av = datetime.now().strftime("%d/%m às %H:%M")
            cursor.execute(
                "INSERT INTO avisos_fixados (autor, mensagem, data_fixacao)"
                " VALUES (?, ?, ?)",
                (autor_av, texto_aviso, dt_av),
            )
            conn.commit()
            st.success("✅ Aviso fixado no topo com sucesso!")
            st.rerun()

  st.markdown("---")
  status_escolhido = st.radio(
      "Meu Status Atual na Rede:",
      [
          "🟢 Disponível / Online",
          "🟡 Em Campo / Obra",
          "🔴 Ocupado / Reunião",
          "⚫ Ausente",
      ],
      horizontal=True,
  )

  tab_conversa, tab_contatos_rede = st.tabs(
      ["💬 Conversas & Chat Ativo", "👥 Rede de Colaboradores & Privado"]
  )

  if "sala_chat_ativa" not in st.session_state:
    st.session_state["sala_chat_ativa"] = "Geral (Equipe)"

  remetente_atual = (
      usuario_atual["apelido"]
      if usuario_atual
      else ("Administrador" if modo_admin_liberado else "Colaborador")
  )
  cargo_atual = usuario_atual["cargo"] if usuario_atual else "Gestão / ADM"
  link_meet = "https://meet.jit.si/TabalmixConcretoEnterprisePro"

  with tab_conversa:
    st.markdown(f"#### 🗨️ Conversa: `{st.session_state['sala_chat_ativa']}`")

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 14px 20px; border-radius: 14px 14px 0 0; display: flex; align-items: center; justify-content: space-between; color: white; box-shadow: 0 6px 18px rgba(5,150,105,0.2);">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background: rgba(255,255,255,0.2); width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 19px; font-weight: bold; border: 2px solid white;">💬</div>
                <div>
                    <h4 style="margin: 0; color: white !important; font-size: 15.5px;">{st.session_state['sala_chat_ativa']}</h4>
                    <span style="font-size: 11px; opacity: 0.9;">status: {status_escolhido} • criptografia enterprise</span>
                </div>
            </div>
            <div style="display: flex; gap: 10px;">
                <a href="{link_meet}" target="_blank" title="Chamada de Áudio" style="background: rgba(255,255,255,0.25); padding: 8px 14px; border-radius: 50%; color: white; text-decoration: none; font-size: 15px; border: 1px solid rgba(255,255,255,0.4);">📞</a>
                <a href="{link_meet}" target="_blank" title="Chamada de Vídeo" style="background: rgba(255,255,255,0.25); padding: 8px 14px; border-radius: 50%; color: white; text-decoration: none; font-size: 15px; border: 1px solid rgba(255,255,255,0.4);">📹</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="background: #ffffff; padding: 18px; border-radius: 0 0 14px 14px; border: 1px solid #e2e8f0; border-top: none; min-height: 280px; max-height: 380px; overflow-y: auto; margin-bottom: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.02);">
        """,
        unsafe_allow_html=True,
    )

    canal_corrente = st.session_state["sala_chat_ativa"]
    if canal_corrente == "Geral (Equipe)":
      df_msgs = pd.read_sql(
          "SELECT * FROM chat_interno WHERE destinatario = 'Geral (Equipe)'"
          " ORDER BY id DESC LIMIT 25",
          conn,
      )
    else:
      df_msgs = pd.read_sql(
          "SELECT * FROM chat_interno WHERE (destinatario = ? AND remetente LIKE"
          " ?) OR (destinatario LIKE ? AND remetente LIKE ?) ORDER BY id DESC"
          " LIMIT 25",
          conn,
          params=(
              canal_corrente,
              f"%{remetente_atual}%",
              f"%{remetente_atual}%",
              f"%{canal_corrente.split()[0]}%",
          ),
      )
      if df_msgs.empty:
        df_msgs = pd.read_sql(
            "SELECT * FROM chat_interno WHERE destinatario = ? ORDER BY id DESC"
            " LIMIT 25",
            conn,
            params=(canal_corrente,),
        )

    if not df_msgs.empty:
      ultima_msg_remetente = str(df_msgs.iloc[0]["remetente"])
      if (
          remetente_atual
          and remetente_atual.lower() not in ultima_msg_remetente.lower()
      ):
        st.markdown(
            """
                <script>
                if (typeof vibrarMensagemChat === 'function') {
                    vibrarMensagemChat();
                }
                </script>
            """,
            unsafe_allow_html=True,
        )

      for _, row_m in df_msgs.iterrows():
        is_me = (
            remetente_atual.lower() in str(row_m["remetente"]).lower()
            if remetente_atual
            else False
        )
        bg_balao = "#ecfdf5" if is_me else "#f8fafc"
        border_balao = "#10b981" if is_me else "#cbd5e1"
        align_balao = "margin-left: auto;" if is_me else "margin-right: auto;"

        st.markdown(
            f"""
                <div style="background: {bg_balao}; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; max-width: 82%; {align_balao} box-shadow: 0 3px 10px rgba(0,0,0,0.03); border: 1px solid {border_balao};">
                    <div style="font-size: 11px; color: #047857; font-weight: bold; margin-bottom: 3px;">{row_m['remetente']}</div>
                    <div style="font-size: 14px; color: #0f172a; white-space: pre-wrap; line-height: 1.4;">{row_m['mensagem']}</div>
                    <div style="font-size: 10px; color: #64748b; text-align: right; margin-top: 4px;">{row_m['data_envio']}</div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        if row_m["arquivo_path"] and os.path.exists(str(row_m["arquivo_path"])):
          with open(row_m["arquivo_path"], "rb") as f_down:
            st.download_button(
                label=f"📥 Baixar anexo: {row_m['arquivo_nome']}",
                data=f_down.read(),
                file_name=row_m["arquivo_nome"],
                key=f"dl_sala_msg_{row_m['id']}",
            )
    else:
      st.markdown(
          "<p style='text-align: center; color: #64748b; font-size: 13px;"
          " margin-top: 40px;'>Inicie a conversa enviando uma mensagem"
          " abaixo!</p>",
          unsafe_allow_html=True,
      )

    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("form_chat_sala_principal", clear_on_submit=True):
      msg_sala_txt = st.text_input("Digite sua mensagem corporativa...")
      file_sala_up = st.file_uploader(
          "Anexar documento ou foto",
          type=["png", "jpg", "jpeg", "pdf", "docx", "xlsx"],
      )
      btn_enviar_sala_pro = st.form_submit_button("➤ Enviar Mensagem")

      if btn_enviar_sala_pro:
        if not msg_sala_txt.strip() and not file_sala_up:
          st.warning("⚠️ Digite uma mensagem ou anexe um arquivo.")
        else:
          path_s = ""
          nome_s = ""
          if file_sala_up is not None:
            os.makedirs("chat_documentos", exist_ok=True)
            nome_s = file_sala_up.name
            path_s = (
                "chat_documentos/"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome_s}"
            )
            with open(path_s, "wb") as f_out_s:
              f_out_s.write(file_sala_up.getbuffer())

          data_env_s = datetime.now().strftime("%d/%m às %H:%M")
          cursor.execute(
              "INSERT INTO chat_interno (remetente, destinatario, cargo,"
              " mensagem, arquivo_path, arquivo_nome, data_envio) VALUES (?, ?,"
              " ?, ?, ?, ?, ?)",
              (
                  f"{remetente_atual} ({cargo_atual})",
                  canal_corrente,
                  cargo_atual,
                  msg_sala_txt,
                  path_s,
                  nome_s,
                  data_env_s,
              ),
          )
          conn.commit()
          st.success("✅ Mensagem enviada!")
          st.rerun()

  with tab_contatos_rede:
    st.markdown("#### 👥 Rede de Colaboradores & Conversas 1 a 1")
    col_btn_g, col_btn_adm = st.columns(2)
    with col_btn_g:
      if st.button("💬 Canal Geral da Equipe", key="btn_rede_geral_pro"):
        st.session_state["sala_chat_ativa"] = "Geral (Equipe)"
        st.success("✅ Conversa alterada para Canal Geral! Volte na aba 'Conversas'.")
        st.rerun()
    with col_btn_adm:
      if st.button("🛡️ Suporte Técnico ADM", key="btn_rede_adm_pro"):
        st.session_state["sala_chat_ativa"] = "Suporte ADM"
        st.success("✅ Conversa alterada para Suporte ADM! Volte na aba 'Conversas'.")
        st.rerun()

    st.markdown("---")
    st.markdown("**Contatos Ativos para Chat Privado:**")
    cursor.execute(
        "SELECT apelido, cargo_setor, email FROM usuarios_sistema WHERE"
        " status_assinatura = 'Ativo'"
    )
    colaboradores_rede = cursor.fetchall()

    encontrou_contato = False
    if colaboradores_rede:
      for idx_r, (r_nome, r_cargo, r_email) in enumerate(colaboradores_rede):
        nome_valido = (
            r_nome
            if r_nome and r_nome != "None"
            else (r_email.split("@")[0] if r_email else "Colaborador")
        )
        cargo_valido = r_cargo if r_cargo and r_cargo != "None" else "Operacional"

        if nome_valido != remetente_atual:
          encontrou_contato = True
          nome_privado = f"Privado: {nome_valido} ({cargo_valido})"
          st.markdown(
              f"""
                    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(0,0,0,0.02);">
                        <div>
                            <span style="font-size: 15px; font-weight: bold; color: #0f172a;">👤 {nome_valido}</span><br>
                            <span style="font-size: 12px; color: #64748b;">Setor: {cargo_valido} • 🟢 Online</span>
                        </div>
                    </div>
                """,
              unsafe_allow_html=True,
          )
          if st.button(
              f"🔒 Abrir Chat Privado com {nome_valido}",
              key=f"btn_chat_privado_{idx_r}",
          ):
            st.session_state["sala_chat_ativa"] = nome_privado
            st.success(
                f"✅ Chat privado com {nome_valido} aberto! Volte na aba"
                " 'Conversas & Chat Ativo'."
            )
            st.rerun()

    if not encontrou_contato:
      st.info(
          "Nenhum outro colaborador ativo no momento (você é o único usuário"
          " logado ou os demais cadastros estão sem apelido definido)."
      )
