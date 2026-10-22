import streamlit as st
import pandas as pd
import plotly.express as px
from config.settings import (
    TIPOS_VAGA_MAP,
    PERIODO_HORAS_MAP,
    DICIONARIO_SKILLS,
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

        # Inicializa estado do dashboard caso ainda esteja vazio
        if "resumo_atual" not in st.session_state:
            st.session_state["resumo_atual"] = None
            st.session_state["vagas_atuais"] = []

        self._renderizar_sidebar(usuario)
        self._renderizar_barra_busca_linkedin(usuario)

        st.divider()

        if st.session_state["resumo_atual"] is not None:
            self._renderizar_painel_analitico(
                resumo=st.session_state["resumo_atual"],
                vagas=st.session_state["vagas_atuais"],
                usuario=usuario
            )
        else:
            st.info(
                "👆 Digite o **título da vaga** acima e clique em **Buscar Vagas no LinkedIn**, "
                "ou selecione na barra lateral esquerda um cargo já analisado no Firebase."
            )

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
            todas_skills = sorted(list(DICIONARIO_SKILLS.keys()))
            skills_selecionadas = st.multiselect(
                "Tecnologias que você domina:",
                options=todas_skills,
                default=[s for s in usuario.skills_usuario if s in todas_skills]
            )

            if set(skills_selecionadas) != set(usuario.skills_usuario):
                if st.button("💾 Salvar Minhas Skills", use_container_width=True, type="primary"):
                    self.auth_controller.atualizar_skills_usuario(usuario.email, skills_selecionadas)
                    usuario.skills_usuario = skills_selecionadas
                    st.session_state["usuario_logado"] = usuario
                    st.toast("Suas qualificações foram atualizadas!", icon="✅")
                    st.rerun()

            st.divider()

            # Seletor de cargos já salvos no Firebase (divididos por título da vaga)
            st.markdown("#### 📂 Cargos Salvos no Banco")
            try:
                resumos_salvos = self.vaga_controller.listar_cargos_analisados()
            except Exception:
                resumos_salvos = []

            if resumos_salvos:
                opcoes_cargos = {
                    f"{r.titulo_exibicao} ({r.total_vagas} vagas)": r.cargo_slug
                    for r in resumos_salvos
                }
                cargo_escolhido_label = st.selectbox(
                    "Alternar dashboard por título da vaga:",
                    options=list(opcoes_cargos.keys())
                )
                if st.button("📊 Carregar Dashboard Salvo", use_container_width=True):
                    slug = opcoes_cargos[cargo_escolhido_label]
                    dados_banco = self.vaga_controller.carregar_cargo_do_banco(slug)
                    if dados_banco["sucesso"]:
                        st.session_state["resumo_atual"] = dados_banco["resumo"]
                        st.session_state["vagas_atuais"] = dados_banco["vagas"]
                        st.rerun()
            else:
                st.caption("Nenhum cargo analisado ainda. Faça sua primeira busca!")

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

                if resultado.get("aviso"):
                    st.warning(resultado["aviso"])
                else:
                    st.success(
                        f"Varredura concluída! {resultado['novas_coletadas']} vagas processadas "
                        f"e salvas para o cargo '{resultado['resumo'].titulo_exibicao}'."
                    )
            else:
                st.error(resultado["mensagem"])

    # ==========================================================
    # 3. DASHBOARD DE INSIGHTS POR CARGO + LISTA DE VAGAS
    # ==========================================================
    def _renderizar_painel_analitico(
        self,
        resumo: ResumoCargo,
        vagas: List[Vaga],
        usuario: Usuario
    ) -> None:
        st.markdown(f"## 📊 Dashboard do Cargo: **{resumo.titulo_exibicao}**")

        # Cálculo de Match do usuário com as Top 10 skills do cargo
        top_skills_cargo = list(resumo.top_requisitos.keys())[:10]
        skills_em_comum = [s for s in top_skills_cargo if s in usuario.skills_usuario]
        skills_faltantes = [s for s in top_skills_cargo if s not in usuario.skills_usuario]
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

        aba_requisitos, aba_rotina_salario, aba_vagas = st.tabs([
            "🏆 Principais Qualificações Pedidas",
            "🛠️ Dia a Dia & Salários",
            f"📋 Vagas Encontradas ({len(vagas)})"
        ])

        # ----------------------------------------------------------
        # ABA 1: RANKING DE QUALIFICAÇÕES E GAP DE ESTUDO
        # ----------------------------------------------------------
        with aba_requisitos:
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
                    st.plotly_chart(fig, use_container_width=True)

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
                        for idx, sk in enumerate(skills_faltantes, 1):
                            qtd = resumo.top_requisitos.get(sk, 0)
                            st.markdown(f"{idx}. **{sk}** *(pedida em {qtd} vagas)*")
                    else:
                        st.balloons()
                        st.success("Parabéns! Você domina todo o Top 10 de requisitos deste cargo!")

        # ----------------------------------------------------------
        # ABA 2: O QUE VAI FAZER NO DIA A DIA E SALÁRIOS
        # ----------------------------------------------------------
        with aba_rotina_salario:
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
        with aba_vagas:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_modalidade = st.multiselect(
                    "Filtrar por Modalidade:",
                    options=["Remoto", "Híbrido", "Presencial / Não especificado"],
                    default=[]
                )
            with col_f2:
                filtro_skill = st.selectbox(
                    "Filtrar vagas que pedem a qualificação:",
                    options=["Todas"] + list(resumo.top_requisitos.keys())
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

                    with st.expander("Ver atividades do dia a dia e descrição completa"):
                        if vaga.dia_a_dia:
                            st.markdown("**Principais atividades identificadas:**")
                            for item in vaga.dia_a_dia:
                                st.markdown(f"- {item}")
                            st.divider()
                        st.markdown("**Descrição original da vaga:**")
                        st.markdown(vaga.descricao_bruta or "Descrição não disponibilizada pelo anunciante.")