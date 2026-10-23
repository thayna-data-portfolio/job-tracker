from typing import Dict, List, Optional
from config.settings import COLECAO_VAGAS, COLECAO_RESUMOS, COLECAO_SKILLS
from models.dao.database_dao import DatabaseDAO
from models.entities.vaga import Vaga
from models.entities.resumo_cargo import ResumoCargo


class VagaDAO:
    """
    DAO responsável por persistir e consultar Vagas e Resumos por Cargo no Firestore.
    """
    def __init__(self):
        self.db_dao = DatabaseDAO()

    def salvar_vagas_em_lote(self, vagas: List[Vaga]) -> None:
        """Grava múltiplas vagas de uma só vez no Firestore usando o id_vaga como chave."""
        documentos = {vaga.id_vaga: vaga.to_dict() for vaga in vagas if vaga.id_vaga}
        self.db_dao.salvar_em_lote(COLECAO_VAGAS, documentos)

    def buscar_vagas_por_cargo(self, cargo_slug: str, limite: int = 100) -> List[Vaga]:
        """Retorna todas as vagas salvas no Firestore para um determinado cargo_slug."""
        registros = self.db_dao.buscar_por_campo(
            nome_colecao=COLECAO_VAGAS,
            campo="cargo_slug",
            valor=cargo_slug,
            limite=limite
        )
        vagas = [Vaga.from_dict(r) for r in registros]
        # Ordena pelas vagas coletadas/publicadas mais recentemente
        vagas.sort(key=lambda v: v.data_publicacao or v.coletado_em, reverse=True)
        return vagas

    def salvar_resumo_cargo(self, resumo: ResumoCargo) -> None:
        """Salva ou atualiza o documento consolidado de estatísticas do cargo."""
        self.db_dao.salvar_documento(
            nome_colecao=COLECAO_RESUMOS,
            doc_id=resumo.cargo_slug,
            dados=resumo.to_dict()
        )

    def buscar_resumo_cargo(self, cargo_slug: str) -> Optional[ResumoCargo]:
        """Busca o resumo consolidado de um cargo específico."""
        dados = self.db_dao.buscar_documento(COLECAO_RESUMOS, cargo_slug)
        if dados:
            return ResumoCargo.from_dict(dados)
        return None

    def listar_todos_resumos(self) -> List[ResumoCargo]:
        """Lista todos os cargos que já possuem análise salva no banco."""
        colecao = self.db_dao.ler_colecao(COLECAO_RESUMOS, limite=50)
        resumos = [ResumoCargo.from_dict(d) for d in colecao.values()]
        resumos.sort(key=lambda r: r.atualizado_em, reverse=True)
        return resumos

    def obter_catalogo_skills(self) -> Dict[str, List[str]]:
        """
        Busca o dicionário de qualificações diretamente da coleção 'catalogo_skills' no Firebase.
        Se a coleção ainda não existir no Firestore, cria automaticamente com skills de várias áreas.
        """
        documentos = self.db_dao.ler_colecao(COLECAO_SKILLS, limite=200)

        if documentos:
            catalogo = {}
            for doc_id, dados in documentos.items():
                nome_exibicao = dados.get("nome", doc_id)
                sinonimos = dados.get("termos", [nome_exibicao.lower()])
                catalogo[nome_exibicao] = sinonimos
            return catalogo

        # Base inicial multi-áreas salva no Firestore apenas na 1ª execução
        skills_iniciais_firestore = {
            # Geral / Escritório / Idiomas
            "excel": {"nome": "Excel / Planilhas", "area": "Geral", "termos": ["excel", "planilhas", "procv", "vlookup", "tabelas dinâmicas"]},
            "pacote_office": {"nome": "Pacote Office", "area": "Geral", "termos": ["pacote office", "microsoft office", "word", "powerpoint", "office 365"]},
            "ingles": {"nome": "Inglês", "area": "Idiomas", "termos": ["inglês", "ingles", "english"]},
            "espanhol": {"nome": "Espanhol", "area": "Idiomas", "termos": ["espanhol", "spanish"]},
            "comunicacao": {"nome": "Comunicação / Oratória", "area": "Soft Skill", "termos": ["boa comunicação", "comunicação verbal", "comunicação escrita", "oratória", "redação"]},
            "metodologias_ageis": {"nome": "Metodologias Ágeis (Scrum/Kanban)", "area": "Gestão", "termos": ["scrum", "kanban", "agile", "metodologias ágeis", "jira"]},

            # Direito / Jurídico
            "direito_civil": {"nome": "Direito Civil / Processual Civil", "area": "Jurídico", "termos": ["direito civil", "processo civil", "processual civil", "cpc", "código civil"]},
            "direito_trabalhista": {"nome": "Direito Trabalhista", "area": "Jurídico", "termos": ["direito do trabalho", "trabalhista", "clt"]},
            "direito_empresarial": {"nome": "Direito Empresarial / Societário", "area": "Jurídico", "termos": ["direito empresarial", "societário", "contratos", "análise de contratos"]},
            "peticionamento": {"nome": "Elaboração de Peças / Peticionamento", "area": "Jurídico", "termos": ["peças processuais", "petições", "peticionamento", "pje", "esaj", "projudi", "acompanhamento processual"]},
            "lgpd_compliance": {"nome": "LGPD / Compliance", "area": "Jurídico", "termos": ["lgpd", "compliance", "proteção de dados", "regulatório"]},

            # Marketing / Comercial / Design
            "marketing_digital": {"nome": "Marketing Digital / Redes Sociais", "area": "Marketing", "termos": ["marketing digital", "redes sociais", "social media", "instagram", "tiktok", "conteúdo"]},
            "trafego_seo": {"nome": "Tráfego Pago / SEO / Google Ads", "area": "Marketing", "termos": ["google ads", "meta ads", "tráfego pago", "seo", "google analytics", "rd station", "crm"]},
            "design_canva": {"nome": "Photoshop / Illustrator / Canva", "area": "Design", "termos": ["photoshop", "illustrator", "canva", "figma", "edição de vídeo", "capcut"]},

            # Administração / Finanças / RH
            "financeiro_erp": {"nome": "SAP / ERP / Rotinas Financeiras", "area": "Finanças", "termos": ["sap", "totvs", "protheus", "erp", "contas a pagar", "contas a receber", "fluxo de caixa", "conciliação"]},
            "recrutamento_rh": {"nome": "Recrutamento & Seleção / DP", "area": "RH", "termos": ["recrutamento e seleção", "triagem de currículos", "departamento pessoal", "admissão", "folha de pagamento", "gupy"]},

            # Tecnologia & Dados
            "python": {"nome": "Python", "area": "Tecnologia", "termos": ["python"]},
            "sql": {"nome": "SQL / Banco de Dados", "area": "Tecnologia", "termos": ["sql", "mysql", "postgresql", "oracle", "modelagem de dados"]},
            "power_bi": {"nome": "Power BI / Dashboards", "area": "Dados", "termos": ["power bi", "powerbi", "tableau", "looker", "dax", "dashboards"]},
            "java": {"nome": "Java", "area": "Tecnologia", "termos": [r"\bjava\b", "spring boot"]},
            "javascript": {"nome": "JavaScript / TypeScript / React", "area": "Tecnologia", "termos": ["javascript", "typescript", "react", "node.js", "html", "css"]},
            "git": {"nome": "Git / GitHub", "area": "Tecnologia", "termos": [r"\bgit\b", "github", "gitlab"]},
            "cloud_docker": {"nome": "Cloud (AWS/Azure/GCP) & Docker", "area": "Tecnologia", "termos": ["aws", "azure", "google cloud", "gcp", "docker", "kubernetes"]},
            "ciencia_dados": {"nome": "Pandas / Machine Learning / ETL", "area": "Dados", "termos": ["pandas", "etl", "machine learning", "scikit-learn", "databricks", "spark", "estatística"]}
        }

        self.db_dao.salvar_em_lote(COLECAO_SKILLS, skills_iniciais_firestore)
        return {v["nome"]: v["termos"] for v in skills_iniciais_firestore.values()}