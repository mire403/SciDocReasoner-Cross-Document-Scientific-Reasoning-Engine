"""Extract semantic clauses from sentences"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Clause(BaseModel):
    """Represents a semantic clause (assertion, comparison, causal statement)"""
    clause_id: str
    text: str
    clause_type: str  # "assertion", "comparison", "causal", "other"
    sentence_id: str
    doc_id: str


class ClauseExtractor:
    """Extract semantic units (clauses) from sentences"""
    
    def __init__(self):
        # Patterns for different clause types
        self.comparison_patterns = [
            re.compile(r'\b(compared to|compared with|versus|vs\.?|better than|worse than|outperforms?|underperforms?|superior|inferior)\b', re.IGNORECASE),
            re.compile(r'\b(more|less|higher|lower|greater|smaller)\s+(than|compared to)\b', re.IGNORECASE),
        ]
        
        self.causal_patterns = [
            re.compile(r'\b(leads? to|causes?|results? in|because|due to|as a result|therefore|thus|hence|consequently)\b', re.IGNORECASE),
            re.compile(r'\b(if|when|after|before)\s+.+\s+(then|results? in)\b', re.IGNORECASE),
        ]
        
        self.assertion_patterns = [
            re.compile(r'\b(we (show|demonstrate|prove|find|observe|discover)|this (shows|demonstrates|proves|indicates|suggests)|results (show|demonstrate|indicate))\b', re.IGNORECASE),
            re.compile(r'\b(our (results|findings|analysis)|the (data|results|evidence) (show|indicate|suggest))\b', re.IGNORECASE),
        ]
    
    def extract_clauses(self, sentences: List[Dict[str, Any]]) -> List[Clause]:
        """Extract clauses from sentences"""
        clauses = []
        
        for sent in sentences:
            sentence_id = sent.get("sentence_id", "")
            doc_id = sent.get("doc_id", "")
            text = sent.get("text", "")
            
            # Try to identify clause type
            clause_type = self._identify_clause_type(text)
            
            # For now, treat each sentence as a clause
            # In future, could split complex sentences into multiple clauses
            clause_id = f"{sentence_id}_clause_0"
            clauses.append(Clause(
                clause_id=clause_id,
                text=text,
                clause_type=clause_type,
                sentence_id=sentence_id,
                doc_id=doc_id
            ))
        
        return clauses
    
    def _identify_clause_type(self, text: str) -> str:
        """Identify the type of semantic clause"""
        text_lower = text.lower()
        
        # Check for comparison
        for pattern in self.comparison_patterns:
            if pattern.search(text):
                return "comparison"
        
        # Check for causal
        for pattern in self.causal_patterns:
            if pattern.search(text):
                return "causal"
        
        # Check for assertion
        for pattern in self.assertion_patterns:
            if pattern.search(text):
                return "assertion"
        
        return "other"
    
    def extract_from_sentence(self, sentence: Dict[str, Any]) -> List[Clause]:
        """Extract clauses from a single sentence"""
        text = sentence.get("text", "")
        sentence_id = sentence.get("sentence_id", "")
        doc_id = sentence.get("doc_id", "")
        
        clause_type = self._identify_clause_type(text)
        
        return [Clause(
            clause_id=f"{sentence_id}_clause_0",
            text=text,
            clause_type=clause_type,
            sentence_id=sentence_id,
            doc_id=doc_id
        )]
