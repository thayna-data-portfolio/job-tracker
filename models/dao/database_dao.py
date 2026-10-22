import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import firebase_admin
from firebase_admin import credentials, firestore
from config.settings import BASE_DIR, FIREBASE_CREDENTIALS_PATH


class DatabaseDAO:
    """
    Conexão centralizada com o Firebase Cloud Firestore (Padrão Singleton).
    """
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(DatabaseDAO, cls).__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self):
        if self._inicializado:
            return

        self.db = self._conectar_firestore()
        self._inicializado = True

    def _conectar_firestore(self):
        if not firebase_admin._apps:
            caminho_cred = Path(FIREBASE_CREDENTIALS_PATH)
            if not caminho_cred.is_absolute():
                caminho_cred = BASE_DIR / caminho_cred

            if caminho_cred.exists():
                cred = credentials.Certificate(str(caminho_cred))
            elif os.getenv("FIREBASE_CREDENTIALS_JSON"):
                cred_dict = json.loads(os.getenv("FIREBASE_CREDENTIALS_JSON"))
                cred = credentials.Certificate(cred_dict)
            else:
                raise FileNotFoundError(
                    f"Arquivo de credencial do Firebase não encontrado em: '{caminho_cred}'. "
                    "Baixe o serviceAccountKey.json no console do Firebase e coloque na raiz do projeto."
                )

            firebase_admin.initialize_app(cred)

        return firestore.client()

    def buscar_documento(self, nome_colecao: str, doc_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db.collection(nome_colecao).document(str(doc_id)).get()
        return doc.to_dict() if doc.exists else None

    def salvar_documento(self, nome_colecao: str, doc_id: str, dados: Dict[str, Any]) -> None:
        self.db.collection(nome_colecao).document(str(doc_id)).set(dados, merge=True)

    def salvar_em_lote(self, nome_colecao: str, documentos: Dict[str, Dict[str, Any]]) -> None:
        if not documentos:
            return

        batch = self.db.batch()
        colecao_ref = self.db.collection(nome_colecao)

        for doc_id, dados in documentos.items():
            doc_ref = colecao_ref.document(str(doc_id))
            batch.set(doc_ref, dados, merge=True)

        batch.commit()

    def buscar_por_campo(self, nome_colecao: str, campo: str, valor: Any, limite: int = 50) -> List[Dict[str, Any]]:
        query = (
            self.db.collection(nome_colecao)
            .where(field_path=campo, op_string="==", value=valor)
            .limit(limite)
        )
        return [doc.to_dict() for doc in query.stream()]