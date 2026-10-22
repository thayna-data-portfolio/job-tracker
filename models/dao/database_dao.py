import os
import json
import streamlit as st
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

        cred = None

        # 1. Credencial local: útil durante o desenvolvimento
        if caminho_cred.exists():
            cred = credentials.Certificate(str(caminho_cred))

        # 2. Credencial armazenada em variável de ambiente
        elif os.getenv("FIREBASE_CREDENTIALS_JSON"):
            cred_dict = json.loads(
                os.getenv("FIREBASE_CREDENTIALS_JSON")
            )
            cred = credentials.Certificate(cred_dict)

        # 3. Secrets do Streamlit Cloud
        else:
            try:
                firebase_config = st.secrets.get(
                    "firebase_service_account"
                )

                if firebase_config:
                    cred = credentials.Certificate(
                        dict(firebase_config)
                    )

            except Exception:
                # Secrets podem não existir no ambiente local
                pass

        if cred is None:
            raise FileNotFoundError(
                "Credenciais do Firebase não encontradas. "
                "Configure o serviceAccountKey.json localmente "
                "ou os Secrets do Streamlit Cloud."
            )

        firebase_admin.initialize_app(cred)

        return firestore.client(database_id="job-tracker-db")

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

    def ler_colecao(self, nome_colecao: str, limite: int = 100) -> Dict[str, Dict[str, Any]]:
     docs = self.db.collection(nome_colecao).limit(limite).stream()
     return {doc.id: doc.to_dict() for doc in docs}