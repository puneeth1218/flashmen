"""
Search Router: GET /api/v1/search
Global entity lookup for IP addresses, Bitcoin wallet addresses, and Transaction IDs.
"""

from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["Search"])


class SearchResultItem(BaseModel):
    entity_type: str = Field(..., description="Type of entity ('wallet', 'ip', 'txid')")
    entity_id: str = Field(..., description="Identifier matched")
    risk_score: float = Field(0.0, description="Associated risk score if evaluated")
    summary: str = Field("", description="Short summary description")


class SearchResponse(BaseModel):
    query: str
    results_count: int
    results: List[SearchResultItem]


@router.get("/search", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=2, description="Search term (IP, Wallet address, or TxID)")
) -> SearchResponse:
    """
    Performs global lookup matching search query against active IP addresses, wallets, and transaction hashes.
    """
    query_str = q.strip()
    mock_results: List[SearchResultItem] = []

    if "." in query_str or ":" in query_str:
        mock_results.append(
            SearchResultItem(
                entity_type="ip",
                entity_id=query_str,
                risk_score=78.5,
                summary=f"IP Address {query_str} observed with 45 active peer connections."
            )
        )
    elif query_str.startswith("1") or query_str.startswith("3") or query_str.startswith("bc1"):
        mock_results.append(
            SearchResultItem(
                entity_type="wallet",
                entity_id=query_str,
                risk_score=88.7,
                summary=f"Bitcoin Wallet {query_str} involved in 14 transactions."
            )
        )
    else:
        mock_results.append(
            SearchResultItem(
                entity_type="txid",
                entity_id=query_str,
                risk_score=45.0,
                summary=f"Transaction {query_str} broadcasted across 88 peer nodes."
            )
        )

    return SearchResponse(
        query=q,
        results_count=len(mock_results),
        results=mock_results
    )
