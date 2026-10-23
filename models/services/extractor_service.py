import re
import unicodedata
from collections import Counter
from typing import List, Dict, Tuple, Optional
import pandas as pd

from models.entities.vaga import Vaga
from models.entities.resumo_cargo import ResumoCargo


class ExtractorService:
    """
    Serviço de NLP/Regex para extrair qualificações, rotina do dia a dia
    e faixa salarial a partir das descrições brutas do JobSpy.
    """

    @staticmethod
    def remover_acentos(texto: str) -> str:
        nfkd = unicodedata.normalize("NFKD", texto.strip().lower())
        return "".join(c for c in nfkd if not unicodedata.combining(c))
    
    @staticmethod
    def gerar_slug_cargo(titulo_cargo: str) -> str:
        """
        Normaliza o título buscado para servir de chave agrupadora no Firestore.
        Ex: 'Desenvolvedor Python Júnior' -> 'desenvolvedor-python-junior'
        """
        texto = unicodedata.normalize("NFKD", titulo_cargo.strip().lower())
        texto_sem_acento = "".join(
            c for c in texto if not unicodedata.combining(c)
        )
        slug = re.sub(r"[^a-z0-9]+", "-", texto_sem_acento).strip("-")
        return slug or "cargo-geral"

    @classmethod
    def _vaga_pertence_ao_cargo_buscado(cls, titulo_vaga: str, termo_busca: str) -> bool:
        """
        Garante que o TÍTULO da vaga retornada pelo LinkedIn realmente corresponda
        ao nível (ex: estágio) e à área que o usuário pesquisou.
        """
        titulo_norm = cls.remover_acentos(titulo_vaga)
        busca_norm = cls.remover_acentos(termo_busca)

        sinonimos_estagio = ("estagio", "estagiario", "estagiaria", "intern", "internship")
        cargos_superiores = ("pleno", "senior", "sr", "coordenador", "gerente", "especialista", "lead", "tech lead")

        busca_pede_estagio = any(s in busca_norm for s in sinonimos_estagio)

        # 1. Se o usuário buscou por Estágio, barra vagas de Pleno/Sênior ou que não sejam de estágio
        if busca_pede_estagio:
            if any(re.search(rf"\b{c}\b", titulo_norm) for c in cargos_superiores):
                return False
            if not any(s in titulo_norm for s in sinonimos_estagio):
                return False

        # 2. Verifica se as palavras-chave da área buscada estão no TÍTULO da vaga
        stopwords = {
            "de", "em", "da", "do", "para", "com", "na", "no", "e", "ou",
            "vaga", "pessoa", "estagio", "estagiario", "estagiaria", "junior", "jr", "pleno", "senior"
        }
        palavras_area = [p for p in re.findall(r"[a-z0-9]+", busca_norm) if p not in stopwords and len(p) > 2]

        # Mapa de equivalência para títulos (ex: buscar "Direito" aceita "Jurídico" no título)
        equivalencias_area = {
            "direito": ["direito", "juridico", "juridica", "advogado", "advocacia", "civel", "trabalhista", "contencioso", "contratos"],
            "dados": ["dados", "data", "bi", "analytics", "business intelligence", "estatistica"],
            "ti": ["ti", "tecnologia", "suporte", "infraestrutura", "sistemas", "software", "desenvolvedor", "dev"],
            "marketing": ["marketing", "comunicacao", "midias", "social media", "conteudo", "growth"]
        }

        for palavra in palavras_area:
            termos_aceitos = equivalencias_area.get(palavra, [palavra])
            if not any(t in titulo_norm for t in termos_aceitos):
                return False

        return True


    @staticmethod
    def extrair_requisitos(descricao: str, catalogo_skills: Dict[str, List[str]]) -> List[str]:
        """Identifica quais qualificações do catálogo Firebase estão presentes na descrição da vaga."""
        if not descricao or not isinstance(descricao, str):
            return []

        texto_lower = descricao.lower()
        skills_encontradas = []

        for nome_skill, padroes in catalogo_skills.items():
            for padrao in padroes:
                if padrao.startswith(r"\b"):
                    if re.search(padrao, texto_lower):
                        skills_encontradas.append(nome_skill)
                        break
                else:
                    # Garante correspondência de palavra/termo
                    regex_termo = r"(?<!\w)" + re.escape(padrao.strip()) + r"(?!\w)"
                    if re.search(regex_termo, texto_lower):
                        skills_encontradas.append(nome_skill)
                        break

        return sorted(list(set(skills_encontradas)))

    @staticmethod
    def extrair_dia_a_dia(descricao: str) -> List[str]:
        """
        Extrai tópicos de responsabilidades e rotina do dia a dia da descrição.
        """
        if not descricao or not isinstance(descricao, str):
            return []

        linhas = descricao.splitlines()
        atividades = []
        capturando_secao = False

        gatilhos_inicio = (
            "dia a dia", "responsabilidades", "atribuições", "o que você vai fazer",
            "suas missões", "desafios", "como será", "atividades", "responsibilities", "what you will do"
        )
        gatilhos_fim = (
            "requisitos", "qualificações", "o que esperamos", "benefícios",
            "diferenciais", "sobre a empresa", "requirements", "qualifications", "benefits"
        )
        verbos_acao = (
            "desenvolver", "criar", "manter", "atuar", "implementar", "participar",
            "construir", "realizar", "apoiar", "elaborar", "analisar", "integrar",
            "garantir", "projetar", "automatizar", "colaborar", "dar suporte"
        )

        for linha in linhas:
            linha_limpa = re.sub(r"^[\s\*\-\•\+\>\d\.\)]+", "", linha).strip()
            linha_lower = linha_limpa.lower()

            if not linha_limpa:
                continue

            if any(g in linha_lower for g in gatilhos_inicio) and len(linha_limpa) < 90:
                capturando_secao = True
                continue

            if capturando_secao and any(g in linha_lower for g in gatilhos_fim) and len(linha_limpa) < 90:
                capturando_secao = False

            eh_topico = linha.strip().startswith(("*", "-", "•"))
            comeca_com_verbo = linha_lower.startswith(verbos_acao)

            if (capturando_secao and eh_topico) or comeca_com_verbo:
                if 20 <= len(linha_limpa) <= 180:
                    atividades.append(linha_limpa)

            if len(atividades) >= 5:
                break

        return atividades

    @staticmethod
    def extrair_salario(linha_df: pd.Series, descricao: str) -> str:
        """
        Verifica se o JobSpy retornou salário estruturado ou busca padrões 'R$ X.XXX' no texto.
        """
        min_val = linha_df.get("min_amount")
        max_val = linha_df.get("max_amount")
        moeda = linha_df.get("currency") or "R$"

        if pd.notna(min_val) and pd.notna(max_val) and float(min_val) > 0:
            return f"{moeda} {float(min_val):,.0f} - {float(max_val):,.0f}".replace(",", ".")
        if pd.notna(min_val) and float(min_val) > 0:
            return f"{moeda} {float(min_val):,.0f}".replace(",", ".")

        if descricao and isinstance(descricao, str):
            padrao_brl = r"R\$\s?\d{1,3}(?:\.\d{3})+(?:,\d{2})?(?:\s?(?:a|até|-)\s?R\$\s?\d{1,3}(?:\.\d{3})+(?:,\d{2})?)?"
            match = re.search(padrao_brl, descricao, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return "Não informado"

    def processar_dataframe_vagas(
        self,
        df: pd.DataFrame,
        termo_busca: str,
        catalogo_skills: Optional[Dict[str, List[str]]] = None
    ) -> List[Vaga]:
        """Converte cada linha do DataFrame do JobSpy em um objeto Vaga enriquecido."""
        cargo_slug = self.gerar_slug_cargo(termo_busca)
        vagas_processadas: List[Vaga] = []

        for _, row in df.iterrows():
            titulo_vaga = str(row.get("title") or "").strip()
            if not titulo_vaga:
                continue

            #Barra vagas fora do tema/nível pesquisado
            if not self._vaga_pertence_ao_cargo_buscado(titulo_vaga, termo_busca):
                continue
            id_bruto = row.get("id") or row.get("job_url") or ""
            id_limpo = re.sub(r"[^a-zA-Z0-9_-]", "_", str(id_bruto))
            descricao = str(row.get("description") or "")

            eh_remoto = bool(row.get("is_remote"))
            wfh_type = str(row.get("work_from_home_type") or "").lower()
            if eh_remoto or "remote" in wfh_type or "remoto" in descricao.lower():
                modalidade = "Remoto"
            elif "híbrido" in descricao.lower() or "hibrido" in descricao.lower() or "hybrid" in wfh_type:
                modalidade = "Híbrido"
            else:
                modalidade = "Presencial / Não especificado"

            link = str(row.get("job_url_direct") or row.get("job_url") or "")
            if not link or link == "nan":
                link = str(row.get("job_url") or "")

            vaga = Vaga(
                id_vaga=id_limpo,
                titulo=str(row.get("title") or termo_busca),
                cargo_slug=cargo_slug,
                empresa=str(row.get("company") or "Empresa Confidencial"),
                localizacao=str(row.get("location") or "Brasil"),
                modalidade=modalidade,
                tipo_vaga=str(row.get("job_type") or "Não informado"),
                nivel_experiencia=str(row.get("job_level") or "Não informado"),
                salario=self.extrair_salario(row, descricao),
                link_inscricao=link,
                requisitos=self.extrair_requisitos(descricao,catalogo_skills or {}),
                dia_a_dia=self.extrair_dia_a_dia(descricao),
                descricao_bruta=descricao,
                data_publicacao=str(row.get("date_posted") or ""),
                site_origem=str(row.get("site") or "linkedin")
            )
            vagas_processadas.append(vaga)

        return vagas_processadas

    @staticmethod
    def consolidar_resumo(
        cargo_slug: str,
        titulo_exibicao: str,
        lista_vagas: List[Vaga]
    ) -> ResumoCargo:
        """
        Agrega todas as vagas daquele cargo para gerar o ranking de requisitos,
        principais atividades do dia a dia e resumo salarial.
        """
        contador_skills = Counter()
        todas_atividades = []
        salarios_validos = []

        for vaga in lista_vagas:
            contador_skills.update(vaga.requisitos)
            todas_atividades.extend(vaga.dia_a_dia)
            if vaga.salario and vaga.salario != "Não informado":
                salarios_validos.append(f"{vaga.salario} ({vaga.empresa})")

        top_requisitos = dict(contador_skills.most_common(15))

        # Remove atividades duplicadas mantendo a ordem de aparição
        atividades_unicas = []
        vistos = set()
        for ativ in todas_atividades:
            chave = ativ[:40].lower()
            if chave not in vistos:
                vistos.add(chave)
                atividades_unicas.append(ativ)
            if len(atividades_unicas) >= 10:
                break

        if salarios_validos:
            media_texto = f"{len(salarios_validos)} vaga(s) com salário divulgado (Ex: {salarios_validos[0]})"
        else:
            media_texto = "Nenhuma vaga divulgou salário aberto no texto"

        return ResumoCargo(
            cargo_slug=cargo_slug,
            titulo_exibicao=titulo_exibicao.title(),
            total_vagas=len(lista_vagas),
            top_requisitos=top_requisitos,
            principais_atividades=atividades_unicas,
            salarios_identificados=salarios_validos[:10],
            media_salarial_texto=media_texto
        )