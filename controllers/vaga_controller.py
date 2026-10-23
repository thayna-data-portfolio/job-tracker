from typing import Dict, Any, Optional, List
from config.settings import LIMITE_VAGAS_PADRAO
from models.services.scraper_service import ScraperService
from models.services.extractor_service import ExtractorService
from models.dao.vaga_dao import VagaDAO
from models.dao.usuario_dao import UsuarioDAO
from models.entities.resumo_cargo import ResumoCargo


class VagaController:
    """
    Controller que coordena a busca no LinkedIn, extração de qualificações
    e consolidação por título da vaga no Firestore.
    """
    def __init__(self):
        self.scraper_service = ScraperService()
        self.extractor_service = ExtractorService()
        self.vaga_dao = VagaDAO()
        self.usuario_dao = UsuarioDAO()

    def listar_opcoes_skills(self) -> List[str]:
        """Retorna a lista de nomes de skills cadastradas no Firebase para o usuário escolher."""
        catalogo = self.vaga_dao.obter_catalogo_skills()
        return sorted(list(catalogo.keys()))

    def buscar_e_processar_vagas(
        self,
        termo_busca: str,
        localizacao: str = "Brazil",
        apenas_remoto: bool = False,
        tipo_vaga: Optional[str] = None,
        horas_publicacao: int = 72,
        quantidade: int = LIMITE_VAGAS_PADRAO,
        email_usuario: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fluxo completo:
        1. Coleta vagas no LinkedIn via JobSpy
        2. Extrai requisitos, dia a dia e salário
        3. Salva vagas no Firestore (deduplicadas pelo ID)
        4. Recalcula e salva o ResumoCargo para aquele título de vaga
        """
        termo_limpo = termo_busca.strip()
        if not termo_limpo:
            return {"sucesso": False, "mensagem": "Digite o título da vaga para buscar."}

        cargo_slug = self.extractor_service.gerar_slug_cargo(termo_limpo)

        # 1. Coleta bruta no LinkedIn
        resultado_scraper = self.scraper_service.coletar_vagas_linkedin(
            termo_busca=termo_limpo,
            localizacao=localizacao,
            apenas_remoto=apenas_remoto,
            tipo_vaga=tipo_vaga,
            horas_publicacao=horas_publicacao,
            quantidade=quantidade
        )

        if not resultado_scraper["sucesso"]:
            return {
                "sucesso": False,
                "mensagem": "Não foram encontradas vagas no LinkedIn para os filtros selecionados."
            }

        catalogo_skills = self.vaga_dao.obter_catalogo_skills()

        vagas_filtradas = self.extractor_service.processar_dataframe_vagas(
            df=resultado_scraper["dataframe"],
            termo_busca=termo_limpo,
            catalogo_skills=catalogo_skills
        )

        if not vagas_filtradas:
            return {
                "sucesso": False,
                "mensagem": f"Não foram encontradas vagas com o título '{termo_limpo}' para os filtros selecionados."
            }

        # 2. Processa o DataFrame extraindo qualificações, dia a dia e salário
        novas_vagas = vagas_filtradas

        # 3. Salva as vagas em lote no Firestore (fazendo merge por id_vaga)
        self.vaga_dao.salvar_vagas_em_lote(novas_vagas)

        # 4. Busca todas as vagas acumuladas desse cargo no banco e atualiza o ResumoCargo
        todas_vagas_do_cargo = self.vaga_dao.buscar_vagas_por_cargo(cargo_slug)
        resumo_atualizado = self.extractor_service.consolidar_resumo(
            cargo_slug=cargo_slug,
            titulo_exibicao=termo_limpo,
            lista_vagas=todas_vagas_do_cargo
        )
        self.vaga_dao.salvar_resumo_cargo(resumo_atualizado)


        return {
            "sucesso": True,
            "aviso": None,
            "resumo": resumo_atualizado,
            "vagas": todas_vagas_do_cargo,
            "novas_coletadas": len(novas_vagas)
        }

    def carregar_cargo_do_banco(self, cargo_slug: str) -> Dict[str, Any]:
        """Carrega instantaneamente o dashboard de um cargo já salvo no Firestore sem acionar o scraper."""
        resumo = self.vaga_dao.buscar_resumo_cargo(cargo_slug)
        if not resumo:
            return {"sucesso": False, "mensagem": "Cargo ainda não possui dados salvos."}

        vagas = self.vaga_dao.buscar_vagas_por_cargo(cargo_slug)
        return {
            "sucesso": True,
            "resumo": resumo,
            "vagas": vagas
        }

    def listar_cargos_analisados(self) -> List[ResumoCargo]:
        """Retorna a lista de cargos já pesquisados e salvos no banco."""
        return self.vaga_dao.listar_todos_resumos()