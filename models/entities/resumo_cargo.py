from datetime import datetime
from typing import Dict, List, Any


class ResumoCargo:
    """
    Entidade que consolida as estatísticas e principais qualificações
    divididas por título de vaga (cargo_slug).
    """
    def __init__(
        self,
        cargo_slug: str,
        titulo_exibicao: str,
        total_vagas: int = 0,
        top_requisitos: Dict[str, int] = None,
        principais_atividades: List[str] = None,
        salarios_identificados: List[str] = None,
        media_salarial_texto: str = "A combinar / Não informado",
        atualizado_em: str = None
    ):
        self.cargo_slug = cargo_slug.strip().lower()
        self.titulo_exibicao = titulo_exibicao.strip()
        self.total_vagas = total_vagas
        self.top_requisitos = top_requisitos or {}
        self.principais_atividades = principais_atividades or []
        self.salarios_identificados = salarios_identificados or []
        self.media_salarial_texto = media_salarial_texto
        self.atualizado_em = atualizado_em or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cargo_slug": self.cargo_slug,
            "titulo_exibicao": self.titulo_exibicao,
            "total_vagas": self.total_vagas,
            "top_requisitos": self.top_requisitos,
            "principais_atividades": self.principais_atividades,
            "salarios_identificados": self.salarios_identificados,
            "media_salarial_texto": self.media_salarial_texto,
            "atualizado_em": self.atualizado_em
        }

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> "ResumoCargo":
        return cls(
            cargo_slug=dados.get("cargo_slug", ""),
            titulo_exibicao=dados.get("titulo_exibicao", ""),
            total_vagas=dados.get("total_vagas", 0),
            top_requisitos=dados.get("top_requisitos", {}),
            principais_atividades=dados.get("principais_atividades", []),
            salarios_identificados=dados.get("salarios_identificados", []),
            media_salarial_texto=dados.get("media_salarial_texto", "A combinar / Não informado"),
            atualizado_em=dados.get("atualizado_em")
        )