"""bge-m3 임베딩 + Chroma 벡터DB 관리."""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = Path("chroma_data")
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"


class Retriever:
    """청크를 임베딩해 Chroma 컬렉션에 저장하고 검색하는 클래스."""

    def __init__(self) -> None:
        # 첫 호출 시 bge-m3 모델을 로컬에 다운로드 (~2GB).
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    def index(self, collection_name: str, chunks: list[str]) -> None:
        """주어진 청크들을 새 컬렉션에 임베딩 후 저장. 이미 있으면 덮어씀."""
        existing = [c.name for c in self.client.list_collections()]
        if collection_name in existing:
            self.client.delete_collection(collection_name)

        collection = self.client.create_collection(name=collection_name)
        embeddings = self.model.encode(chunks, show_progress_bar=True).tolist()
        ids = [f"{collection_name}_{i}" for i in range(len(chunks))]
        collection.add(ids=ids, embeddings=embeddings, documents=chunks)

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 3,
    ) -> list[str]:
        """query와 가장 가까운 청크 top_k개의 본문을 반환."""
        collection = self.client.get_collection(name=collection_name)
        query_emb = self.model.encode([query]).tolist()
        result = collection.query(query_embeddings=query_emb, n_results=top_k)
        return result["documents"][0]
