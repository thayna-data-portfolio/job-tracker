import streamlit as st
from views.auth_view import AuthView
from views.dashboard_view import DashboardView


def main():
    st.set_page_config(
        page_title="JobTracker MVP - Inteligência de Vagas",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Verifica se o usuário já está autenticado na sessão
    if "usuario_logado" not in st.session_state or st.session_state["usuario_logado"] is None:
        auth_view = AuthView()
        auth_view.renderizar()
    else:
        dashboard_view = DashboardView()
        dashboard_view.renderizar()


if __name__ == "__main__":
    main()