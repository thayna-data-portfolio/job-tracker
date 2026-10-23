import os
from pathlib import Path
from dotenv import load_dotenv


# Carrega variáveis do arquivo .env local
load_dotenv()

# Caminho raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent


def obter_config(chave: str, valor_padrao: str = "") -> str:
    """
    Busca a configuração primeiro no .env / variáveis de ambiente.
    Quando estiver hospedado no Streamlit Cloud, busca em st.secrets.
    """
    valor = os.getenv(chave)
    if valor is not None:
        return valor
    try:
        import streamlit as st
        if chave in st.secrets:
            return str(st.secrets[chave])
    except Exception:
        pass
    return valor_padrao


# Caminho da credencial do Firebase Admin
FIREBASE_CREDENTIALS_PATH = obter_config("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")


# Nomes padronizados das coleções no Cloud Firestore
COLECAO_USUARIOS = "usuarios"
COLECAO_VAGAS = "vagas"
COLECAO_RESUMOS = "resumos_cargos"
COLECAO_SKILLS = "catalogo_skills"

# Parâmetros padrão de busca no LinkedIn
LIMITE_VAGAS_PADRAO = int(obter_config("LIMITE_VAGAS_PADRAO", "20"))
PAIS_PADRAO = obter_config("PAIS_PADRAO", "Brazil")

# Mapeamento de filtros da interface (View -> JobSpy)
TIPOS_VAGA_MAP = {
    "Todos": None,
    "Tempo Integral (CLT/PJ)": "fulltime",
    "Estágio": "internship",
    "Meio Período": "parttime",
    "Contrato / Temporário": "contract"
}

PERIODO_HORAS_MAP = {
    "Últimas 24 horas": 24,
    "Últimos 3 dias (72h)": 72,
    "Última semana": 168,
    "Último mês": 720
}
