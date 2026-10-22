from datetime import datetime
from typing import List, Dict, Any


class Usuario:
    """
    Entidade que representa um usuário do sistema.
    """
    def __init__(
        self,
        uid: str,
        nome: str,
        email: str,
        senha_hash: str,
        skills_usuario: List[str] = None,
        historico_buscas: List[str] = None,
        criado_em: str = None
    ):
        self.uid = uid
        self.nome = nome.strip()
        self.email = email.strip().lower()
        self.senha_hash = senha_hash
        self.skills_usuario = skills_usuario or []
        self.historico_buscas = historico_buscas or []
        self.criado_em = criado_em or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto Usuario para dicionário (para salvar no Firestore)."""
        return {
            "uid": self.uid,
            "nome": self.nome,
            "email": self.email,
            "senha_hash": self.senha_hash,
            "skills_usuario": self.skills_usuario,
            "historico_buscas": self.historico_buscas,
            "criado_em": self.criado_em
        }

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> "Usuario":
        """Reconstrói um objeto Usuario a partir de um documento do Firestore."""
        return cls(
            uid=dados.get("uid", ""),
            nome=dados.get("nome", ""),
            email=dados.get("email", ""),
            senha_hash=dados.get("senha_hash", ""),
            skills_usuario=dados.get("skills_usuario", []),
            historico_buscas=dados.get("historico_buscas", []),
            criado_em=dados.get("criado_em")
        )