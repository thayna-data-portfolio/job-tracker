from datetime import datetime
from typing import List, Dict, Any


class Vaga:
    """
    Entidade que representa uma vaga de emprego processada.
    """
    def __init__(
        self,
        id_vaga: str,
        titulo: str,
        cargo_slug: str,
        empresa: str,
        localizacao: str,
        modalidade: str,
        tipo_vaga: str,
        nivel_experiencia: str,
        salario: str,
        link_inscricao: str,
        requisitos: List[str] = None,
        dia_a_dia: List[str] = None,
        descricao_bruta: str = "",
        data_publicacao: str = "",
        site_origem: str = "linkedin",
        coletado_em: str = None
    ):
        self.id_vaga = str(id_vaga)
        self.titulo = titulo.strip()
        self.cargo_slug = cargo_slug.strip().lower()
        self.empresa = empresa.strip() if empresa else "Empresa Confidencial"
        self.localizacao = localizacao.strip() if localizacao else "Brasil"
        self.modalidade = modalidade
        self.tipo_vaga = tipo_vaga
        self.nivel_experiencia = nivel_experiencia
        self.salario = salario or "Não informado"
        self.link_inscricao = link_inscricao
        self.requisitos = requisitos or []
        self.dia_a_dia = dia_a_dia or []
        self.descricao_bruta = descricao_bruta or ""
        self.data_publicacao = data_publicacao or ""
        self.site_origem = site_origem
        self.coletado_em = coletado_em or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_vaga": self.id_vaga,
            "titulo": self.titulo,
            "cargo_slug": self.cargo_slug,
            "empresa": self.empresa,
            "localizacao": self.localizacao,
            "modalidade": self.modalidade,
            "tipo_vaga": self.tipo_vaga,
            "nivel_experiencia": self.nivel_experiencia,
            "salario": self.salario,
            "link_inscricao": self.link_inscricao,
            "requisitos": self.requisitos,
            "dia_a_dia": self.dia_a_dia,
            "descricao_bruta": self.descricao_bruta,
            "data_publicacao": self.data_publicacao,
            "site_origem": self.site_origem,
            "coletado_em": self.coletado_em
        }

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> "Vaga":
        return cls(
            id_vaga=dados.get("id_vaga", ""),
            titulo=dados.get("titulo", ""),
            cargo_slug=dados.get("cargo_slug", ""),
            empresa=dados.get("empresa", ""),
            localizacao=dados.get("localizacao", ""),
            modalidade=dados.get("modalidade", "Não especificado"),
            tipo_vaga=dados.get("tipo_vaga", ""),
            nivel_experiencia=dados.get("nivel_experiencia", ""),
            salario=dados.get("salario", "Não informado"),
            link_inscricao=dados.get("link_inscricao", ""),
            requisitos=dados.get("requisitos", []),
            dia_a_dia=dados.get("dia_a_dia", []),
            descricao_bruta=dados.get("descricao_bruta", ""),
            data_publicacao=dados.get("data_publicacao", ""),
            site_origem=dados.get("site_origem", "linkedin"),
            coletado_em=dados.get("coletado_em")
        )