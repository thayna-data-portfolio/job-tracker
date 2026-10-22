from typing import Dict, Any, Optional
import pandas as pd
from jobspy import scrape_jobs
from config.settings import LIMITE_VAGAS_PADRAO


class ScraperService:
    """
    Serviço responsável por navegar e coletar vagas usando o JobSpy.
    """
    def coletar_vagas_linkedin(
        self,
        termo_busca: str,
        localizacao: str = "Brazil",
        apenas_remoto: bool = False,
        tipo_vaga: Optional[str] = None,
        horas_publicacao: int = 72,
        quantidade: int = LIMITE_VAGAS_PADRAO
    ) -> Dict[str, Any]:
        """
        Executa a busca pública no LinkedIn via JobSpy e retorna um dicionário
        contendo o status da operação e o DataFrame de vagas.
        """
        try:
            parametros = {
                "site_name": ["linkedin"],
                "search_term": termo_busca,
                "location": localizacao,
                "is_remote": apenas_remoto,
                "hours_old": horas_publicacao,
                "results_wanted": quantidade,
                "fetch_description": True,
                "description_format": "markdown",
                "verbose": 0
            }

            if tipo_vaga:
                parametros["job_type"] = tipo_vaga

            df_vagas: pd.DataFrame = scrape_jobs(**parametros)

            # Verifica se o LinkedIn retornou bloqueio temporário (Erro 429)
            erros_jobspy = getattr(df_vagas, "attrs", {}).get("errors", {})
            if "linkedin" in erros_jobspy and df_vagas.empty:
                return {
                    "sucesso": False,
                    "erro": f"O LinkedIn limitou temporariamente as requisições (Erro 429). Aguarde 1 minuto e tente novamente. Detalhe: {erros_jobspy['linkedin']}",
                    "dataframe": pd.DataFrame()
                }

            if df_vagas is None or df_vagas.empty:
                return {
                    "sucesso": False,
                    "erro": "Nenhuma vaga encontrada com esses filtros no LinkedIn.",
                    "dataframe": pd.DataFrame()
                }

            return {
                "sucesso": True,
                "erro": None,
                "dataframe": df_vagas
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao executar o scraper no LinkedIn: {str(e)}",
                "dataframe": pd.DataFrame()
            }