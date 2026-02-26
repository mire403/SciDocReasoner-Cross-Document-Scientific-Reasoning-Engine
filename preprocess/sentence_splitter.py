"""Advanced sentence splitting for scientific documents"""

import re
from typing import List, Dict, Any
from pydantic import BaseModel


class Sentence(BaseModel):
    """Represents a single sentence with metadata"""
    sentence_id: str
    text: str
    section: str
    doc_id: str
    position: int  # Position in document


class SentenceSplitter:
    """Advanced sentence splitter for scientific text"""
    
    def __init__(self):
        # Patterns for sentence endings, accounting for scientific notation
        self.sentence_endings = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])'  # Standard sentence endings
        )
        # Exceptions: abbreviations, decimals, citations
        self.abbreviation_pattern = re.compile(
            r'\b(Dr|Mr|Mrs|Ms|Prof|etc|e\.g|i\.e|vs|cf|Fig|Eq|Ref|No|Vol|pp|al|et)\b\.',
            re.IGNORECASE
        )
        self.citation_pattern = re.compile(r'\[[\d,\s-]+\]|\([\d,\s-]+\)')
        self.decimal_pattern = re.compile(r'\d+\.\d+')
    
    def split_document(self, doc_id: str, sections: List[Dict[str, Any]]) -> List[Sentence]:
        """Split document sections into sentences"""
        sentences = []
        position = 0
        
        for section_data in sections:
            section_name = section_data.get("section", "Unknown")
            text = section_data.get("raw_text", "")
            
            section_sentences = self.split_text(text, doc_id, section_name, position)
            sentences.extend(section_sentences)
            position += len(section_sentences)
        
        return sentences
    
    def split_text(self, text: str, doc_id: str, section: str, start_position: int = 0) -> List[Sentence]:
        """Split text into sentences"""
        if not text.strip():
            return []
        
        # Remove citations temporarily to avoid splitting issues
        citation_placeholders = {}
        text_with_placeholders = self._replace_citations(text, citation_placeholders)
        
        # Split by sentence endings
        raw_sentences = self.sentence_endings.split(text_with_placeholders)
        
        # Restore citations and clean up
        sentences = []
        for idx, raw_sent in enumerate(raw_sentences):
            # Restore citations
            sent = self._restore_citations(raw_sent, citation_placeholders)
            sent = sent.strip()
            
            if not sent or len(sent) < 3:  # Skip very short fragments
                continue
            
            # Skip if it's just a citation or reference
            if re.match(r'^[\[\(][\d,\s-]+[\]\)]$', sent):
                continue
            
            sentence_id = f"{doc_id}_sent_{start_position + idx}"
            sentences.append(Sentence(
                sentence_id=sentence_id,
                text=sent,
                section=section,
                doc_id=doc_id,
                position=start_position + idx
            ))
        
        return sentences
    
    def _replace_citations(self, text: str, placeholders: Dict[str, str]) -> str:
        """Replace citations with placeholders"""
        matches = list(self.citation_pattern.finditer(text))
        for i, match in enumerate(matches):
            placeholder = f"__CITATION_{i}__"
            placeholders[placeholder] = match.group(0)
            text = text.replace(match.group(0), placeholder, 1)
        return text
    
    def _restore_citations(self, text: str, placeholders: Dict[str, str]) -> str:
        """Restore citations from placeholders"""
        for placeholder, citation in placeholders.items():
            text = text.replace(placeholder, citation)
        return text
    
    def split_section_sentences(self, section_sentences: List[str], doc_id: str, section: str, start_position: int = 0) -> List[Sentence]:
        """Split a list of pre-extracted sentences (from parser) into Sentence objects"""
        sentences = []
        for idx, sent_text in enumerate(section_sentences):
            if not sent_text.strip() or len(sent_text.strip()) < 3:
                continue
            
            sentence_id = f"{doc_id}_sent_{start_position + idx}"
            sentences.append(Sentence(
                sentence_id=sentence_id,
                text=sent_text.strip(),
                section=section,
                doc_id=doc_id,
                position=start_position + idx
            ))
        
        return sentences
