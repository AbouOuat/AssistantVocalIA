"""RAG (T2) — ingestion + retrieval sur pgvector. SQL direct (pas de retriever
LangChain — même logique que Path B : éviter une abstraction pour un besoin simple).

Sources : synthèses e-mails classifiées (Redis, emails_structured) + exports
sessions/*.md. Voir backend/scripts/ingest_rag.py pour l'ingestion et
eval/rag/run_eval.py pour l'évaluation (hit rate @k).
"""
import logging

from openai import AsyncOpenAI
from sqlalchemy import delete

from backend.config import get_settings
from backend.models import Document, SessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()

EMBEDDING_MODEL = "text-embedding-3-small"
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY or None)
    return _client


async def embed_text(text: str) -> list[float]:
    resp = await _get_client().embeddings.create(model=EMBEDDING_MODEL, input=text[:8000])
    return resp.data[0].embedding


async def upsert_document(
    user_id: int,
    content: str,
    source: str,
    external_id: str,
    metadata: dict | None = None,
) -> int:
    """Embed + upsert un document (remplace tout doc existant avec le même
    user_id/source/external_id — idempotent, relançable sans dupliquer)."""
    embedding = await embed_text(content)
    db = SessionLocal()
    try:
        db.execute(
            delete(Document).where(
                Document.user_id == user_id,
                Document.source == source,
                Document.external_id == external_id,
            )
        )
        doc = Document(
            user_id=user_id,
            content=content,
            embedding=embedding,
            source=source,
            external_id=external_id,
            doc_metadata=metadata or {},
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc.id
    finally:
        db.close()


async def search(user_id: int, query: str, k: int = 5, source: str | None = None) -> list[dict]:
    """Top-k documents par similarité cosinus à la requête (embeddée à la volée)."""
    query_embedding = await embed_text(query)
    db = SessionLocal()
    try:
        q = db.query(
            Document,
            Document.embedding.cosine_distance(query_embedding).label("distance"),
        ).filter(Document.user_id == user_id)
        if source:
            q = q.filter(Document.source == source)
        rows = q.order_by("distance").limit(k).all()
        return [
            {
                "id": doc.id,
                "content": doc.content,
                "source": doc.source,
                "external_id": doc.external_id,
                "metadata": doc.doc_metadata,
                "distance": float(dist),
                "similarity": 1 - float(dist),  # cosine_distance = 1 - cosine_similarity
            }
            for doc, dist in rows
        ]
    finally:
        db.close()


async def format_search_results(user_id: int, query: str, k: int = 5) -> str:
    """Réponse texte sourcée pour le tool `rechercher_historique`."""
    results = await search(user_id, query, k=k)
    if not results:
        return "Aucun document pertinent trouvé dans l'historique."
    lines = [f"## Résultats pour « {query} » ({len(results)})"]
    for r in results:
        src_label = "Email" if r["source"] == "email" else "Session"
        date = (r["metadata"] or {}).get("date", "")
        lines.append(
            f"- [{src_label}{' — ' + date if date else ''}] "
            f"(similarité {r['similarity']:.2f}) {r['content'][:280]}"
        )
    return "\n".join(lines)
