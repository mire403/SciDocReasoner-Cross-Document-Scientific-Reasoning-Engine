"""PDF document parser"""

import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import pypdf
from pydantic import BaseModel


class DocumentSection(BaseModel):
    """Represents a section in a document"""
    section: str
    sentences: List[str]
    raw_text: str


class ParsedDocument(BaseModel):
    """Structured representation of a parsed document"""
    doc_id: str
    title: str
    authors: List[str] = []
    abstract: str = ""
    sections: List[DocumentSection] = []
    metadata: Dict[str, Any] = {}


class PDFParser:
    """Parser for PDF documents"""
    
    def __init__(self):
        self.section_keywords = [
            "abstract", "introduction", "related work", "methodology", 
            "methods", "method", "results", "discussion", "conclusion",
            "references", "appendix"
        ]
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse a PDF file into structured format"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Generate doc_id from file hash
        doc_id = self._generate_doc_id(file_path)
        
        # Extract text from PDF
        text_content = self._extract_text(path)
        
        # Extract metadata
        metadata = self._extract_metadata(path)
        title = metadata.get("title", path.stem)
        authors = metadata.get("authors", [])
        
        # Split into sections
        sections = self._split_into_sections(text_content)
        
        return ParsedDocument(
            doc_id=doc_id,
            title=title,
            authors=authors,
            abstract=self._extract_abstract(sections),
            sections=sections,
            metadata=metadata
        )
    
    def _generate_doc_id(self, file_path: str) -> str:
        """Generate unique document ID from file"""
        path = Path(file_path)
        with open(path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:12]
        return f"doc_{file_hash}"
    
    def _extract_text(self, path: Path) -> str:
        """Extract text content from PDF"""
        text_parts = []
        try:
            with open(path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)
        except Exception as e:
            raise ValueError(f"Error reading PDF: {e}")
        
        return "\n\n".join(text_parts)
    
    def _extract_metadata(self, path: Path) -> Dict[str, Any]:
        """Extract metadata from PDF"""
        metadata = {}
        try:
            with open(path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                if pdf_reader.metadata:
                    metadata = {
                        "title": pdf_reader.metadata.get("/Title", ""),
                        "authors": pdf_reader.metadata.get("/Author", "").split(";") if pdf_reader.metadata.get("/Author") else [],
                        "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")),
                    }
        except Exception:
            pass
        
        return metadata
    
    def _extract_abstract(self, sections: List[DocumentSection]) -> str:
        """Extract abstract from sections"""
        for section in sections:
            if section.section.lower() == "abstract":
                return section.raw_text
        return ""
    
    def _split_into_sections(self, text: str) -> List[DocumentSection]:
        """Split text into sections based on headings"""
        sections = []
        lines = text.split('\n')
        
        current_section = "Introduction"
        current_text = []
        current_sentences = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section heading
            is_heading = False
            for keyword in self.section_keywords:
                if line.lower().startswith(keyword.lower()):
                    # Save previous section
                    if current_text:
                        sections.append(DocumentSection(
                            section=current_section,
                            sentences=current_sentences,
                            raw_text="\n".join(current_text)
                        ))
                    
                    # Start new section
                    current_section = line
                    current_text = [line]
                    current_sentences = []
                    is_heading = True
                    break
            
            if not is_heading:
                current_text.append(line)
                # Simple sentence splitting (will be refined in preprocess layer)
                sentences = self._simple_sentence_split(line)
                current_sentences.extend(sentences)
        
        # Add final section
        if current_text:
            sections.append(DocumentSection(
                section=current_section,
                sentences=current_sentences,
                raw_text="\n".join(current_text)
            ))
        
        return sections
    
    def _simple_sentence_split(self, text: str) -> List[str]:
        """Simple sentence splitting (will be refined later)"""
        import re
        # Split on sentence endings
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
