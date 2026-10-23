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

        # 4. Consolida o resumo APENAS com as vagas encontradas nesta pesquisa
        resumo_atual = self.extractor_service.consolidar_resumo(
            cargo_slug=cargo_slug,
            titulo_exibicao=termo_limpo,
            lista_vagas=vagas_filtradas
        )


        return {
            "sucesso": True,
            "resumo": resumo_atual,
            "vagas": vagas_filtradas,
            "novas_coletadas": len(vagas_filtradas)
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


    # 5 Permite cadastro de novas skills 
    def adicionar_skill_catalogo(self, nome: str, area: str, sinonimos_str: str) -> Dict[str, Any]:
        nome = nome.strip()
        if not nome:
            return {"sucesso": False, "mensagem": "Informe o nome da qualificação."}

        doc_id = self.extractor_service.gerar_slug_cargo(nome).replace("-", "_")
        termos = [t.strip().lower() for t in sinonimos_str.split(",") if t.strip()]
        if nome.lower() not in termos:
            termos.insert(0, nome.lower())

        self.vaga_dao.cadastrar_nova_skill(doc_id=doc_id, nome=nome, area=area or "Geral", termos=termos)
        return {"sucesso": True, "mensagem": f"Qualificação '{nome}' salva no Firebase!"}


    def salvar_vaga_usuario(self, usuario, vaga, nome_categoria: str) -> Dict[str, Any]:
        """Salva uma vaga dentro da categoria escolhida (padrão: título pesquisado)."""
        categoria = nome_categoria.strip() or vaga.cargo_slug.replace("-", " ").title()

        if categoria not in usuario.vagas_salvas:
            usuario.vagas_salvas[categoria] = []

        # Evita duplicar a mesma vaga dentro da mesma categoria
        ids_existentes = [v.get("id_vaga") for v in usuario.vagas_salvas[categoria]]
        if vaga.id_vaga in ids_existentes:
            return {"sucesso": False, "mensagem": f"Esta vaga já está salva em '{categoria}'."}

        usuario.vagas_salvas[categoria].append(vaga.to_dict())
        self.usuario_dao.atualizar_vagas_salvas(usuario.email, usuario.vagas_salvas)
        return {"sucesso": True, "mensagem": f"Vaga salva na categoria '{categoria}'!"}

    def mover_vaga_categoria(self, usuario, id_vaga: str, cat_origem: str, cat_destino: str) -> Dict[str, Any]:
        """Move uma vaga salva de uma categoria para outra categoria personalizada."""
        cat_destino = cat_destino.strip()
        if not cat_destino or cat_origem == cat_destino:
            return {"sucesso": False, "mensagem": "Escolha um nome de categoria válido."}

        lista_origem = usuario.vagas_salvas.get(cat_origem, [])
        vaga_encontrada = next((v for v in lista_origem if v.get("id_vaga") == id_vaga), None)

        if not vaga_encontrada:
            return {"sucesso": False, "mensagem": "Vaga não encontrada na categoria de origem."}

        # Remove da origem
        usuario.vagas_salvas[cat_origem] = [v for v in lista_origem if v.get("id_vaga") != id_vaga]
        if not usuario.vagas_salvas[cat_origem]:
            del usuario.vagas_salvas[cat_origem]

        # Adiciona no destino
        if cat_destino not in usuario.vagas_salvas:
            usuario.vagas_salvas[cat_destino] = []
        if not any(v.get("id_vaga") == id_vaga for v in usuario.vagas_salvas[cat_destino]):
            usuario.vagas_salvas[cat_destino].append(vaga_encontrada)

        self.usuario_dao.atualizar_vagas_salvas(usuario.email, usuario.vagas_salvas)
        return {"sucesso": True, "mensagem": f"Vaga movida para '{cat_destino}'!"}

    def remover_vaga_salva(self, usuario, id_vaga: str, categoria: str) -> None:
        """Remove uma vaga de uma categoria salva."""
        if categoria in usuario.vagas_salvas:
            usuario.vagas_salvas[categoria] = [
                v for v in usuario.vagas_salvas[categoria] if v.get("id_vaga") != id_vaga
            ]
            if not usuario.vagas_salvas[categoria]:
                del usuario.vagas_salvas[categoria]
            self.usuario_dao.atualizar_vagas_salvas(usuario.email, usuario.vagas_salvas)

    def gerar_analise_categoria_salva(self, nome_categoria: str, vagas_dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Reconstrói os objetos Vaga e gera o ResumoCargo exclusivo daquela categoria salva."""
        from models.entities.vaga import Vaga
        objetos_vaga = [Vaga.from_dict(d) for d in vagas_dicts]
        slug = self.extractor_service.gerar_slug_cargo(nome_categoria)
        resumo = self.extractor_service.consolidar_resumo(
            cargo_slug=slug,
            titulo_exibicao=nome_categoria,
            lista_vagas=objetos_vaga
        )
        return {"resumo": resumo, "vagas": objetos_vaga}