import hashlib
from typing import Dict, Any, List
from models.entities.usuario import Usuario
from models.dao.usuario_dao import UsuarioDAO


class AuthController:
    """
    Controller responsável pelas regras de negócio de criação de conta e login.
    """
    def __init__(self):
        self.usuario_dao = UsuarioDAO()

    @staticmethod
    def _gerar_hash_senha(senha: str) -> str:
        """Transforma a senha em hash SHA-256 para nunca salvar senha pura no banco."""
        return hashlib.sha256(senha.encode("utf-8")).hexdigest()

    @staticmethod
    def _gerar_uid(email: str) -> str:
        """Gera um ID curto único baseado no e-mail."""
        return hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()[:12]

    def cadastrar_usuario(
        self,
        nome: str,
        email: str,
        senha: str,
        skills_iniciais: List[str] = None
    ) -> Dict[str, Any]:
        """Valida os dados e cria um novo usuário no Firestore."""
        nome = nome.strip()
        email = email.strip().lower()

        if not nome or not email or not senha:
            return {"sucesso": False, "mensagem": "Preencha todos os campos obrigatórios."}

        if "@" not in email or "." not in email:
            return {"sucesso": False, "mensagem": "Digite um endereço de e-mail válido."}

        if len(senha) < 6:
            return {"sucesso": False, "mensagem": "A senha deve ter pelo menos 6 caracteres."}

        # Verifica se o e-mail já está cadastrado no Firebase
        usuario_existente = self.usuario_dao.buscar_por_email(email)
        if usuario_existente:
            return {"sucesso": False, "mensagem": "Já existe uma conta cadastrada com este e-mail."}

        novo_usuario = Usuario(
            uid=self._gerar_uid(email),
            nome=nome,
            email=email,
            senha_hash=self._gerar_hash_senha(senha),
            skills_usuario=skills_iniciais or []
        )

        self.usuario_dao.salvar(novo_usuario)
        return {
            "sucesso": True,
            "mensagem": "Conta criada com sucesso!",
            "usuario": novo_usuario
        }

    def autenticar(self, email: str, senha: str) -> Dict[str, Any]:
        """Verifica e-mail e senha para realizar o login."""
        email = email.strip().lower()

        if not email or not senha:
            return {"sucesso": False, "mensagem": "Informe seu e-mail e senha."}

        usuario = self.usuario_dao.buscar_por_email(email)
        if not usuario:
            return {"sucesso": False, "mensagem": "Usuário não encontrado."}

        senha_hash_digitada = self._gerar_hash_senha(senha)
        if usuario.senha_hash != senha_hash_digitada:
            return {"sucesso": False, "mensagem": "Senha incorreta."}

        return {
            "sucesso": True,
            "mensagem": f"Bem-vindo(a), {usuario.nome}!",
            "usuario": usuario
        }

    def atualizar_skills_usuario(self, email: str, skills: List[str]) -> None:
        """Atualiza as skills do usuário logado."""
        self.usuario_dao.atualizar_skills(email, skills)