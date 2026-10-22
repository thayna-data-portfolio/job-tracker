import streamlit as st
from config.settings import DICIONARIO_SKILLS
from controllers.auth_controller import AuthController


class AuthView:
    """
    View responsável pela interface de Login e Criação de Conta.
    """
    def __init__(self):
        self.auth_controller = AuthController()

    def renderizar(self) -> None:
        st.markdown(
            "<h1 style='text-align: center;'>🚀 JobTracker MVP</h1>"
            "<p style='text-align: center; color: gray;'>"
            "Busca automatizada de vagas no LinkedIn e inteligência de qualificações por cargo"
            "</p>",
            unsafe_allow_html=True
        )
        st.divider()

        col_esq, col_centro, col_dir = st.columns([1, 1.5, 1])

        with col_centro:
            aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])

            # ==========================================
            # ABA 1: LOGIN
            # ==========================================
            with aba_login:
                with st.form("form_login"):
                    st.subheader("Acesse sua conta")
                    email_login = st.text_input("E-mail", placeholder="seuemail@exemplo.com")
                    senha_login = st.text_input("Senha", type="password", placeholder="••••••")
                    btn_entrar = st.form_submit_button("Entrar no Dashboard", use_container_width=True, type="primary")

                    if btn_entrar:
                        with st.spinner("Autenticando no Firebase..."):
                            resultado = self.auth_controller.autenticar(email_login, senha_login)

                        if resultado["sucesso"]:
                            st.session_state["usuario_logado"] = resultado["usuario"]
                            st.success(resultado["mensagem"])
                            st.rerun()
                        else:
                            st.error(resultado["mensagem"])

            # ==========================================
            # ABA 2: CADASTRO
            # ==========================================
            with aba_cadastro:
                with st.form("form_cadastro"):
                    st.subheader("Crie sua conta gratuita")
                    nome_cad = st.text_input("Seu Nome", placeholder="Ex: Lucas Silva")
                    email_cad = st.text_input("Seu E-mail", placeholder="seuemail@exemplo.com")
                    senha_cad = st.text_input("Crie uma Senha (mín. 6 caracteres)", type="password")

                    lista_opcoes_skills = sorted(list(DICIONARIO_SKILLS.keys()))
                    skills_iniciais = st.multiselect(
                        "Quais qualificações/tecnologias você já conhece? (Opcional)",
                        options=lista_opcoes_skills,
                        help="Usaremos isso no Dashboard para mostrar o que você já tem e o que falta estudar para cada vaga."
                    )

                    btn_cadastrar = st.form_submit_button("Criar Conta e Entrar", use_container_width=True, type="primary")

                    if btn_cadastrar:
                        with st.spinner("Criando sua conta no Firebase..."):
                            resultado = self.auth_controller.cadastrar_usuario(
                                nome=nome_cad,
                                email=email_cad,
                                senha=senha_cad,
                                skills_iniciais=skills_iniciais
                            )

                        if resultado["sucesso"]:
                            st.session_state["usuario_logado"] = resultado["usuario"]
                            st.success(resultado["mensagem"])
                            st.rerun()
                        else:
                            st.error(resultado["mensagem"])