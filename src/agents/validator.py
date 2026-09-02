import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from ..models.state import MarketIntelligenceState
from ..models.validation import ClaimStatus, ClaimVerification, EvidenceQualityReport

logger = logging.getLogger(__name__)


class ValidatorAgent:
    """Evaluates extracted claims against collected source documents to detect hallucinations,

    unsupported statements, or contradictions.
    """

    @staticmethod
    def _stem_word(word: str) -> str:
        """Lightweight stemmer for token normalization."""
        w = word.lower()
        for suffix in ("ing", "tion", "tions", "ment", "ments", "ers", "er", "ies", "ed", "es", "s"):
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                return w[:-len(suffix)]
        return w

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extracts normalized, stemmed tokens (excluding common stop words)."""
        stop_words = {
            "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
            "of", "is", "are", "was", "were", "by", "that", "this", "it", "from",
            "as", "be", "all", "offers", "provides", "features", "starts", "starting",
            "begins", "beginning", "recently", "also", "into", "their", "more"
        }
        words = re.findall(r"\b[a-zA-Z0-9₹$%-]+\b", text.lower())
        tokens = []
        for w in words:
            if w not in stop_words and len(w) > 2:
                tokens.append(ValidatorAgent._stem_word(w))
        return tokens

    def _find_best_citation(
        self,
        claim_statement: str,
        source_chunks: List[Dict[str, Any]],
    ) -> Tuple[Optional[str], Optional[str], Optional[str], float]:
        """Finds the most relevant source sentence and computes an evidence match score."""
        claim_keywords = set(self._extract_keywords(claim_statement))
        if not claim_keywords:
            return None, None, None, 0.0

        best_citation = None
        best_chunk_id = None
        best_url = None
        best_overlap_ratio = 0.0

        for chunk in source_chunks:
            content = chunk.get("content", "")
            sentences = re.split(r"(?<=[.!?])\s+", content)
            for sentence in sentences:
                sent_keywords = set(self._extract_keywords(sentence))
                if not sent_keywords:
                    continue
                intersection = claim_keywords.intersection(sent_keywords)
                overlap = len(intersection) / len(claim_keywords)
                if overlap > best_overlap_ratio:
                    best_overlap_ratio = overlap
                    best_citation = sentence.strip()
                    best_chunk_id = chunk.get("chunk_id")
                    best_url = chunk.get("url")

        return best_citation, best_chunk_id, best_url, best_overlap_ratio

    def evaluate_claim(
        self,
        claim: Dict[str, Any],
        source_chunks: List[Dict[str, Any]],
    ) -> ClaimVerification:
        """Audits a single claim against available competitor source chunks."""
        statement = claim.get("statement", "")
        comp_name = claim.get("competitor_name", "")
        claim_id = claim.get("claim_id", "CLM-000")
        category = claim.get("category", "general")

        # Filter chunks to matching competitor
        relevant_chunks = [
            c for c in source_chunks
            if c.get("competitor_name", "").lower() == comp_name.lower()
        ]
        if not relevant_chunks:
            relevant_chunks = source_chunks

        citation, chunk_id, url, overlap = self._find_best_citation(statement, relevant_chunks)

        # Audit decision logic:
        # High grounding (>= 0.35 with stemmed tokens) indicates corroborated facts
        if overlap >= 0.35:
            status = ClaimStatus.VALIDATED
            confidence = min(0.98, 0.70 + (overlap * 0.3))
            notes = f"Grounding verified: {int(overlap * 100)}% keyword alignment with primary source."
        elif overlap >= 0.24:
            status = ClaimStatus.LOW_CONFIDENCE
            confidence = 0.60
            notes = "Partial evidence found; inferred from broader context."
        else:
            status = ClaimStatus.REQUIRES_REVIEW
            confidence = 0.20
            citation = "No matching evidence found in collected source chunks."
            notes = "Flagged: Statement cannot be verified against source material (potential hallucination)."

        return ClaimVerification(
            claim_id=claim_id,
            competitor_name=comp_name,
            category=category,
            statement=statement,
            status=status,
            confidence_score=round(confidence, 2),
            source_citation=citation,
            matched_source_id=chunk_id,
            matched_url=url,
            audit_notes=notes,
        )

    def run(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        raw_sources = state.get("raw_sources", [])
        intelligence = state.get("extracted_intelligence", {})
        claims = intelligence.get("claims", [])

        logger.info(f"Validator Agent auditing {len(claims)} claims against {len(raw_sources)} sources...")

        verifications: List[ClaimVerification] = []
        validated_count = 0
        review_count = 0

        for claim in claims:
            v = self.evaluate_claim(claim, raw_sources)
            verifications.append(v)
            if v.status == ClaimStatus.VALIDATED:
                validated_count += 1
            else:
                review_count += 1

        total = len(verifications)
        overall_conf = round((validated_count / total * 100), 1) if total > 0 else 0.0

        summary = (
            f"Audited {total} claims across {len(raw_sources)} primary source chunks. "
            f"{validated_count} claims verified with ground-truth citations. "
            f"{review_count} claim(s) flagged for human review. "
            f"Overall evidence reliability score: {overall_conf}%."
        )

        report = EvidenceQualityReport(
            total_claims=total,
            claims_validated=validated_count,
            claims_requiring_review=review_count,
            overall_confidence=overall_conf,
            verifications=verifications,
            summary_assessment=summary,
        )

        return {
            "validation_report": report.model_dump(),
            "current_stage": "validated",
        }
