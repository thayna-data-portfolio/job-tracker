import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore



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

if not firebase_admin._apps:
    firebase_config = dict(st.secrets["firebase_service_account"])
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Nomes padronizados das coleções no Cloud Firestore
COLECAO_USUARIOS = "usuarios"
COLECAO_VAGAS = "vagas"
COLECAO_RESUMOS = "resumos_cargos"

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

# Catálogo base de Hard Skills para identificar e padronizar nos textos das vagas
DICIONARIO_SKILLS = {
    "Python": ["python"],
    "Java": [r"\bjava\b"],
    "JavaScript": ["javascript", r"\bjs\b"],
    "TypeScript": ["typescript", r"\bts\b"],
    "SQL": ["sql", "mysql", "postgresql", "postgres", "oracle", "pl/sql", "tsql"],
    "NoSQL / MongoDB": ["nosql", "mongodb", "firestore", "firebase", "redis", "dynamodb"],
    "React": ["react", "reactjs", "react.js"],
    "Node.js": ["node", "nodejs", "node.js", "express"],
    "FastAPI / Flask / Django": ["fastapi", "flask", "django"],
    "Spring Boot": ["spring", "spring boot"],
    "Docker": ["docker", "containers", "container"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "Azure": ["azure"],
    "Google Cloud (GCP)": ["gcp", "google cloud", "bigquery"],
    "Git / GitHub": [r"\bgit\b", "github", "gitlab", "versionamento"],
    "CI/CD": ["ci/cd", "github actions", "jenkins", "pipelines"],
    "Power BI / Dados": ["power bi", "powerbi", "tableau", "looker", "excel"],
    "Pandas / Análise de Dados": ["pandas", "numpy", "scipy", "etl", "databricks", "spark"],
    "Machine Learning / IA": ["machine learning", "scikit-learn", "sklearn", "nlp", "llm", "ia generativa", "deep learning"],
    "Linux": ["linux", "ubuntu", "bash", "shell"],
    "APIs REST": ["rest", "restful", "api rest", "graphql", "microsserviços", "microservices"],
    "Testes Automatizados": ["pytest", "junit", "selenium", "playwright", "cypress", "tdd", "testes unitários"],
    "Metodologias Ágeis": ["scrum", "kanban", "agile", "ágeis", "jira"]
}