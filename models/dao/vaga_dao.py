from typing import List, Optional
from config.settings import COLECAO_VAGAS, COLECAO_RESUMOS
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