import streamlit as st
import pandas as pd
import plotly.express as px
from config.settings import (
    TIPOS_VAGA_MAP,
    PERIODO_HORAS_MAP,
    LIMITE_VAGAS_PADRAO
)
from controllers.vaga_controller import VagaController
from controllers.auth_controller import AuthController
from models.entities.usuario import Usuario
from models.entities.resumo_cargo import ResumoCargo
from models.entities.vaga import Vaga
from typing import List


class DashboardView:
    """
    View principal que exibe os filtros de busca do LinkedIn, o Dashboard analítico
    dividido por título de vaga e a listagem com link de inscrição.
    """
    def __init__(self):
        self.vaga_controller = VagaController()
        self.auth_controller = AuthController()

    def renderizar(self) -> None:
        usuario: Usuario = st.session_state["usuario_logado"]

        if "resumo_atual" not in st.session_state:
            st.session_state["resumo_atual"] = None
            st.session_state["vagas_atuais"] = []

        self._renderizar_sidebar(usuario)

        aba_pesquisa, aba_salvas = st.tabs([
            "🔎 Pesquisar Vagas no LinkedIn",
            f"⭐ Minhas Vagas Salvas"
        ])

        with aba_pesquisa:
            self._renderizar_barra_busca_linkedin(usuario)
            st.divider()
            if st.session_state["resumo_atual"] is not None:
                self._renderizar_painel_analitico(
                    resumo=st.session_state["resumo_atual"],
                    vagas=st.session_state["vagas_atuais"],
                    usuario=usuario,
                    chave_contexto="pesquisa"
                )
            else:
                st.info("👆 Digite o **título da vaga** acima, escolha os filtros e clique em **Buscar no LinkedIn**.")

        with aba_salvas:
            self._renderizar_aba_vagas_salvas(usuario)

    # ==========================================================
    # 1. BARRA LATERAL (PERFIL, SKILLS DO USUÁRIO E HISTÓRICO)
    # ==========================================================
    def _renderizar_sidebar(self, usuario: Usuario) -> None:
        with st.sidebar:
            st.markdown(f"### 👤 Olá, {usuario.nome}!")
            st.caption(f"📧 {usuario.email}")

            if st.button("🚪 Sair da Conta", use_container_width=True):
                st.session_state.clear()
                st.rerun()

            st.divider()

            # Editor rápido de Skills do usuário para comparar com os requisitos da vaga
            st.markdown("#### 🛠️ Minhas Qualificações")
            todas_skills = self.vaga_controller.listar_opcoes_skills()
            skills_selecionadas = st.multiselect(
                "Qualificações que você domina:",
                options=todas_skills,
                default=[s for s in usuario.skills_usuario if s in todas_skills]
            )

            if set(skills_selecionadas) != set(usuario.skills_usuario):
                if st.button("💾 Salvar Minhas Skills", use_container_width=True, type="primary"):
                    self.auth_controller.atualizar_skills_usuario(usuario.email, skills_selecionadas)
                    usuario.skills_usuario = skills_selecionadas
                    st.session_state["usuario_logado"] = usuario
                    st.toast("Suas qualificações foram atualizadas no Firebase!", icon="✅")
                    st.rerun()
            

            # Exibe o painel de cadastro de skills no banco APENAS se o usuário for Admin
            if usuario.is_admin:
                st.divider()
                st.caption("🛡️ Painel do Administrador")
                with st.expander("➕ Cadastrar Nova Qualificação"):
                    nova_skill_nome = st.text_input("Nome da Qualificação", placeholder="Ex: Direito Tributário")
                    nova_skill_area = st.text_input("Área / Catálogo", placeholder="Ex: Jurídico, Dados, Saúde...")
                    nova_skill_termos = st.text_input(
                        "Palavras-chave para detectar na vaga (separadas por vírgula)",
                        placeholder="Ex: tributário, direito fiscal, icms"
                    )
                    if st.button("Adicionar ao Catálogo", use_container_width=True):
                        res_skill = self.vaga_controller.adicionar_skill_catalogo(
                            nome=nova_skill_nome,
                            area=nova_skill_area,
                            sinonimos_str=nova_skill_termos
                        )
                        if res_skill["sucesso"]:
                            st.session_state.pop("opcoes_skills_banco", None)
                            st.toast(res_skill["mensagem"], icon="✅")
                            st.rerun()
                        else:
                            st.warning(res_skill["mensagem"])


    # ==========================================================
    # 2. FORMULÁRIO DE FILTROS DO LINKEDIN (SCRAPER)
    # ==========================================================
    def _renderizar_barra_busca_linkedin(self, usuario: Usuario) -> None:
        st.subheader("🔎 Buscar Vagas no LinkedIn")

        with st.form("form_busca_linkedin"):
            col1, col2, col3 = st.columns([2.2, 1.5, 1.3])

            with col1:
                termo_busca = st.text_input(
                    "Título da Vaga / Cargo",
                    placeholder="Ex: Desenvolvedor Python, Analista de Dados, Estágio Java..."
                )
            with col2:
                localizacao = st.text_input(
                    "Localização",
                    value="São Paulo, Brazil",
                    help="Ex: Brazil, São Paulo, Brazil, Rio de Janeiro..."
                )
            with col3:
                tipo_vaga_label = st.selectbox(
                    "Tipo de Vaga",
                    options=list(TIPOS_VAGA_MAP.keys())
                )

            col4, col5, col6, col7 = st.columns([1.5, 1.5, 1.2, 1.5])

            with col4:
                periodo_label = st.selectbox(
                    "Data de Publicação",
                    options=list(PERIODO_HORAS_MAP.keys()),
                    index=1
                )
            with col5:
                quantidade = st.slider(
                    "Qtd. de vagas na varredura",
                    min_value=5,
                    max_value=35,
                    value=LIMITE_VAGAS_PADRAO,
                    step=5
                )
            with col6:
                st.write("")
                st.write("")
                apenas_remoto = st.checkbox("🏠 Apenas Remoto")
            with col7:
                st.write("")
                btn_buscar = st.form_submit_button(
                    "🚀 Buscar no LinkedIn",
                    use_container_width=True,
                    type="primary"
                )

        if btn_buscar:
            if not termo_busca.strip():
                st.warning("Por favor, digite o título da vaga que deseja procurar.")
                return

            with st.spinner(f"Navegando no LinkedIn para buscar vagas de '{termo_busca}' e extraindo requisitos..."):
                resultado = self.vaga_controller.buscar_e_processar_vagas(
                    termo_busca=termo_busca,
                    localizacao=localizacao,
                    apenas_remoto=apenas_remoto,
                    tipo_vaga=TIPOS_VAGA_MAP[tipo_vaga_label],
                    horas_publicacao=PERIODO_HORAS_MAP[periodo_label],
                    quantidade=quantidade,
                    email_usuario=usuario.email
                )

            if resultado["sucesso"]:
                st.session_state["resumo_atual"] = resultado["resumo"]
                st.session_state["vagas_atuais"] = resultado["vagas"]
                st.success(
                    f"Encontradas {resultado['novas_coletadas']} vagas para '{resultado['resumo'].titulo_exibicao}'!"
                )

            else:
                st.session_state["resumo_atual"] = None
                st.session_state["vagas_atuais"] = []
                st.warning(resultado["mensagem"])

    # ==========================================================
    # 3. DASHBOARD DE INSIGHTS POR CARGO + LISTA DE VAGAS
    # ==========================================================
    def _renderizar_painel_analitico(
        self,
        resumo: ResumoCargo,
        vagas: List[Vaga],
        usuario: Usuario,
        chave_contexto: str = "pesquisa",
        categoria_atual: str = None
    ) -> None:
        st.markdown(f"## 📊 Dashboard do Cargo: **{resumo.titulo_exibicao}**")

        # Cálculo de Match do usuário com as Top 10 skills do cargo
        requisitos_ordenados = sorted(
            resumo.top_requisitos.items(),
            key=lambda item: item[1],
            reverse=True
        )[:10]

        top_skills_cargo = [skill for skill, _ in requisitos_ordenados]
        skills_em_comum = [s for s in top_skills_cargo if s in usuario.skills_usuario]
        skills_faltantes = [
            (skill, qtd) for skill, qtd in requisitos_ordenados
            if skill not in usuario.skills_usuario
        ]
        pct_match = int((len(skills_em_comum) / len(top_skills_cargo)) * 100) if top_skills_cargo else 0
        skill_mais_pedida = top_skills_cargo[0] if top_skills_cargo else "N/A"
        vagas_com_salario = len(resumo.salarios_identificados)

        # Cards de Métricas Principais (KPIs)
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total de Vagas Analisadas", f"{resumo.total_vagas} vagas")
        kpi2.metric("Qualificação Nº 1", skill_mais_pedida)
        kpi3.metric("Compatibilidade do seu Perfil", f"{pct_match}% (Top 10 Skills)")
        kpi4.metric("Vagas com Salário Informado", f"{vagas_com_salario} de {resumo.total_vagas}")

        st.write("")

        secao_ativa = st.radio(
            "Navegação do Painel:",
            options=[
                "🏆 Principais Qualificações Pedidas",
                "🛠️ Dia a Dia & Salários",
                "📋 Vagas Encontradas"
            ],
            horizontal=True,
            label_visibility="collapsed",
            key=f"nav_painel_{chave_contexto}"
        )
        st.divider()

        # ----------------------------------------------------------
        # ABA 1: RANKING DE QUALIFICAÇÕES E GAP DE ESTUDO
        # ----------------------------------------------------------
        if secao_ativa == "🏆 Principais Qualificações Pedidas":
            if not resumo.top_requisitos:
                st.info("As descrições coletadas para este cargo ainda não trouxeram qualificações mapeadas.")
            else:
                col_grafico, col_gap = st.columns([1.7, 1.3])

                with col_grafico:
                    df_skills = pd.DataFrame(
                        list(resumo.top_requisitos.items()),
                        columns=["Qualificação", "Qtd. de Vagas"]
                    )
                    df_skills["% das Vagas"] = (
                        (df_skills["Qtd. de Vagas"] / max(resumo.total_vagas, 1)) * 100
                    ).round(1)
                    df_skills["Você possui?"] = df_skills["Qualificação"].apply(
                        lambda s: "Já domino ✅" if s in usuario.skills_usuario else "Falta estudar 📚"
                    )
                    df_skills = df_skills.sort_values(by="Qtd. de Vagas", ascending=True)

                    fig = px.bar(
                        df_skills,
                        x="Qtd. de Vagas",
                        y="Qualificação",
                        color="Você possui?",
                        orientation="h",
                        text=df_skills["% das Vagas"].apply(lambda x: f"{x}%"),
                        title=f"Requisitos mais pedidos para {resumo.titulo_exibicao}",
                        color_discrete_map={
                            "Já domino ✅": "#10B981",
                            "Falta estudar 📚": "#3B82F6"
                        }
                    )
                    fig.update_layout(height=450, yaxis_title="", xaxis_title="Número de Vagas")
                    st.plotly_chart(fig, use_container_width=True, key=f"grafico_{chave_contexto}_{resumo.cargo_slug}")

                with col_gap:
                    st.markdown("#### 🎯 Diagnóstico para o seu Perfil")
                    st.write(f"Analisando as **10 qualificações mais exigidas** para **{resumo.titulo_exibicao}**:")

                    st.markdown("**✅ O que você já domina:**")
                    if skills_em_comum:
                        st.success(", ".join(skills_em_comum))
                    else:
                        st.caption("Marque suas skills na barra lateral esquerda para comparar.")

                    st.markdown("**📚 O que mais cai nas vagas e vale estudar:**")
                    if skills_faltantes:
                        for idx, (sk, qtd) in enumerate(skills_faltantes, 1):
                            st.markdown(f"{idx}. **{sk}** *(pedida em {qtd} vagas)*")
                    else:
                        st.balloons()
                        st.success("Parabéns! Você domina todo o Top 10 de requisitos deste cargo!")

        # ----------------------------------------------------------
        # ABA 2: O QUE VAI FAZER NO DIA A DIA E SALÁRIOS
        # ----------------------------------------------------------
        elif secao_ativa == "🛠️ Dia a Dia & Salários":
            col_dia, col_sal = st.columns([1.5, 1.2])

            with col_dia:
                st.markdown(f"#### 🛠️ O que um(a) **{resumo.titulo_exibicao}** faz no dia a dia")
                if resumo.principais_atividades:
                    for atividade in resumo.principais_atividades:
                        st.markdown(f"- {atividade}")
                else:
                    st.caption("As vagas coletadas não detalharam tópicos separados de rotina.")

            with col_sal:
                st.markdown("#### 💰 Informações de Salário Encontradas")
                st.info(resumo.media_salarial_texto)

                if resumo.salarios_identificados:
                    st.markdown("**Faixas salariais capturadas nas vagas:**")
                    for sal in resumo.salarios_identificados:
                        st.markdown(f"- 💵 **{sal}**")
                else:
                    st.caption(
                        "Dica: A maioria das empresas no LinkedIn Brasil deixa o salário 'A combinar'. "
                        "Experimente ampliar a quantidade de vagas na busca para encontrar mais faixas abertas."
                    )

        # ----------------------------------------------------------
        # ABA 3: LISTA DE VAGAS COM LINK PARA INSCRIÇÃO
        # ----------------------------------------------------------
        elif secao_ativa == "📋 Vagas Encontradas":
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_modalidade = st.multiselect(
                    "Filtrar por Modalidade:",
                    options=["Remoto", "Híbrido", "Presencial / Não especificado"],
                    default=[],
                    key=f"mod_{chave_contexto}_{resumo.cargo_slug}"
                )
            with col_f2:
                filtro_skill = st.selectbox(
                    "Filtrar vagas que pedem a qualificação:",
                    options=["Todas"] + list(resumo.top_requisitos.keys()),
                    key=f"sk_{chave_contexto}_{resumo.cargo_slug}"
                )

            vagas_filtradas = vagas
            if filtro_modalidade:
                vagas_filtradas = [v for v in vagas_filtradas if v.modalidade in filtro_modalidade]
            if filtro_skill != "Todas":
                vagas_filtradas = [v for v in vagas_filtradas if filtro_skill in v.requisitos]

            st.caption(f"Exibindo **{len(vagas_filtradas)}** vaga(s) para **{resumo.titulo_exibicao}**.")

            for vaga in vagas_filtradas:
                with st.container(border=True):
                    c_info, c_btn = st.columns([3.5, 1.2])

                    with c_info:
                        st.markdown(f"### {vaga.titulo}")
                        st.markdown(
                            f"🏢 **{vaga.empresa}** &nbsp;|&nbsp; 📍 {vaga.localizacao} "
                            f"&nbsp;|&nbsp; 🏠 `{vaga.modalidade}` &nbsp;|&nbsp; 💰 **{vaga.salario}**"
                        )

                        if vaga.requisitos:
                            badges = " ".join([f"`{req}`" for req in vaga.requisitos])
                            st.markdown(f"**Qualificações pedidas:** {badges}")

                    with c_btn:
                        st.write("")
                        if vaga.link_inscricao:
                            st.link_button(
                                "Inscrever-se na Vaga ↗",
                                url=vaga.link_inscricao,
                                use_container_width=True,
                                type="primary"
                            )
                        if vaga.data_publicacao and vaga.data_publicacao != "None":
                            st.caption(f"📅 Publicada em: {vaga.data_publicacao}")

                        if chave_contexto == "pesquisa":
                            # Verifica se esta vaga já foi salva em alguma categoria do usuário
                            categoria_ja_salva = next(
                                (cat for cat, lista in usuario.vagas_salvas.items()
                                 if any(v.get("id_vaga") == vaga.id_vaga for v in lista)),
                                None
                            )

                            if categoria_ja_salva:
                                # Como o popover não é mais renderizado aqui, o quadrado some na hora!
                                st.button(
                                    f"✅ Salva em: {categoria_ja_salva}",
                                    key=f"ja_salva_{vaga.id_vaga}",
                                    disabled=True,
                                    use_container_width=True
                                )
                            else:
                                with st.popover("⭐ Salvar Vaga", use_container_width=True):
                                    categorias_existentes = list(usuario.vagas_salvas.keys())
                                    cat_padrao = resumo.titulo_exibicao
                                    if cat_padrao not in categorias_existentes:
                                        categorias_existentes.insert(0, cat_padrao)

                                    cat_escolhida = st.selectbox(
                                        "Salvar na categoria:",
                                        options=categorias_existentes + ["➕ Nova categoria..."],
                                        key=f"sel_cat_{vaga.id_vaga}"
                                    )
                                    if cat_escolhida == "➕ Nova categoria...":
                                        cat_final = st.text_input(
                                            "Nome da nova categoria:",
                                            placeholder="Ex: Prioridade Alta",
                                            key=f"nova_cat_{vaga.id_vaga}"
                                        )
                                    else:
                                        cat_final = cat_escolhida

                                    if st.button("Confirmar", key=f"btn_save_{vaga.id_vaga}", type="primary", use_container_width=True):
                                        res_save = self.vaga_controller.salvar_vaga_usuario(usuario, vaga, cat_final)
                                        if res_save["sucesso"]:
                                            st.session_state["usuario_logado"] = usuario
                                            st.toast(res_save["mensagem"], icon="⭐")
                                            st.rerun()
                                        else:
                                            st.warning(res_save["mensagem"])

                        elif chave_contexto == "salvas" and categoria_atual:
                            with st.popover("🗂️ Mudar Categoria", use_container_width=True):
                                nova_cat = st.text_input(
                                    "Mover para a categoria:",
                                    value=categoria_atual,
                                    key=f"move_in_{categoria_atual}_{vaga.id_vaga}"
                                )
                                if st.button("Mover Vaga", key=f"btn_mv_{categoria_atual}_{vaga.id_vaga}", use_container_width=True):
                                    res_mv = self.vaga_controller.mover_vaga_categoria(
                                        usuario, vaga.id_vaga, categoria_atual, nova_cat
                                    )
                                    if res_mv["sucesso"]:
                                        st.session_state["usuario_logado"] = usuario
                                        st.toast(res_mv["mensagem"], icon="🗂️")
                                        st.rerun()

                            if st.button("🗑️ Remover", key=f"del_{categoria_atual}_{vaga.id_vaga}", use_container_width=True):
                                self.vaga_controller.remover_vaga_salva(usuario, vaga.id_vaga, categoria_atual)
                                st.session_state["usuario_logado"] = usuario
                                st.toast("Vaga removida!", icon="🗑️")
                                st.rerun()

                    with st.expander("Ver atividades do dia a dia e descrição completa"):
                        if vaga.dia_a_dia:
                            st.markdown("**Principais atividades identificadas:**")
                            for item in vaga.dia_a_dia:
                                st.markdown(f"- {item}")
                            st.divider()
                        st.markdown("**Descrição original da vaga:**")
                        st.markdown(vaga.descricao_bruta or "Descrição não disponibilizada pelo anunciante.")

    # ==========================================================
    # 4. ABA DE VAGAS SALVAS E ANÁLISE POR CATEGORIA
    # ==========================================================
    def _renderizar_aba_vagas_salvas(self, usuario: Usuario) -> None:
        total_salvas = sum(len(v) for v in usuario.vagas_salvas.values())
        st.subheader(f"⭐ Minhas Vagas Salvas ({total_salvas})")

        if not usuario.vagas_salvas:
            st.info(
                "Você ainda não salvou nenhuma vaga. Faça uma busca na aba **Pesquisar Vagas no LinkedIn** "
                "e clique em **⭐ Salvar Vaga** nos cards que te interessarem!"
            )
            return

        opcoes_categorias = {
            f"📁 {nome_cat} ({len(lista)} vagas)": nome_cat
            for nome_cat, lista in usuario.vagas_salvas.items()
        }

        opcoes_categorias = {
            "⭐ Todas as vagas salvas": None,
            **opcoes_categorias
        }

        col_sel, col_renomear = st.columns([2, 1.5])

        with col_sel:
            label_selecionado = st.selectbox(
                "Escolha o agrupamento ou visualize todas as vagas:",
                options=list(opcoes_categorias.keys())
            )
            categoria_ativa = opcoes_categorias[label_selecionado]
    

        with col_renomear:
            if categoria_ativa is not None:
                with st.expander("✏️ Renomear esta categoria"):
                    novo_nome_grupo = st.text_input("Novo nome para o grupo:", value=categoria_ativa)
                    if st.button("Salvar Novo Nome", use_container_width=True):
                        novo_nome_limpo = novo_nome_grupo.strip()
                        if novo_nome_limpo and novo_nome_limpo != categoria_ativa:
                            vagas_do_grupo = usuario.vagas_salvas.pop(categoria_ativa)
                            usuario.vagas_salvas.setdefault(novo_nome_limpo, []).extend(vagas_do_grupo)
                            self.vaga_controller.usuario_dao.atualizar_vagas_salvas(usuario.email, usuario.vagas_salvas)
                            st.session_state["usuario_logado"] = usuario
                            st.rerun()

        st.divider()

        if categoria_ativa is None:
            vagas_dicts = [
                vaga
                for lista in usuario.vagas_salvas.values()
                for vaga in lista
            ]
            nome_analise = "Todas as vagas salvas"

        else: 
            vagas_dicts = usuario.vagas_salvas[categoria_ativa]
            nome_analise = categoria_ativa

        dados_analise = self.vaga_controller.gerar_analise_categoria_salva(
            nome_categoria=nome_analise,
            vagas_dicts=vagas_dicts
        )

        self._renderizar_painel_analitico(
            resumo=dados_analise["resumo"],
            vagas=dados_analise["vagas"],
            usuario=usuario,
            chave_contexto="salvas",
            categoria_atual=categoria_ativa
        )
