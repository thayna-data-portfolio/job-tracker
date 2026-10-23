from typing import Optional, List
from config.settings import COLECAO_USUARIOS
from models.dao.database_dao import DatabaseDAO
from models.entities.usuario import Usuario


class UsuarioDAO:
    """
    DAO responsável pelas operações de banco de dados da entidade Usuario.
    """
    def __init__(self):
        self.db_dao = DatabaseDAO()

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """Busca um usuário no Firestore usando o e-mail normalizado como chave."""
        email_limpo = email.strip().lower()
        dados = self.db_dao.buscar_documento(COLECAO_USUARIOS, email_limpo)
        if dados:
            return Usuario.from_dict(dados)
        return None

    def salvar(self, usuario: Usuario) -> None:
        """Salva ou atualiza os dados do usuário no Firestore."""
        # Usamos o email limpo como ID do documento para evitar duplicidade de contas
        self.db_dao.salvar_documento(
            nome_colecao=COLECAO_USUARIOS,
            doc_id=usuario.email,
            dados=usuario.to_dict()
        )

    def atualizar_skills(self, email: str, novas_skills: List[str]) -> None:
        """Atualiza a lista de qualificações que o usuário já possui."""
        email_limpo = email.strip().lower()
        self.db_dao.salvar_documento(
            nome_colecao=COLECAO_USUARIOS,
            doc_id=email_limpo,
            dados={"skills_usuario": novas_skills}
        )

    def atualizar_vagas_salvas(self, email: str, vagas_salvas: dict) -> None:
        """Salva no Firestore o dicionário de categorias e vagas salvas pelo usuário."""
        email_limpo = email.strip().lower()
        self.db_dao.salvar_documento(
            nome_colecao=COLECAO_USUARIOS,
            doc_id=email_limpo,
            dados={"vagas_salvas": vagas_salvas}
        )
