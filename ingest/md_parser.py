"""Markdown document parser"""

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any
import markdown
from bs4 import BeautifulSoup
from .pdf_parser import ParsedDocument, DocumentSection


class MDParser:
    """Parser for Markdown documents"""
    
    def __init__(self):
        self.section_keywords = [
            "abstract", "introduction", "related work", "methodology", 
            "methods", "method", "results", "discussion", "conclusion",
            "references", "appendix"
        ]
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse a Markdown file into structured format"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")
        
        # Generate doc_id
        doc_id = self._generate_doc_id(file_path)
        
        # Read markdown content
        with open(path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Extract title (from first # heading or filename)
        title = self._extract_title(md_content, path)
        
        # Extract authors (from YAML frontmatter if present)
        authors = self._extract_authors(md_content)
        
        # Split into sections
        sections = self._split_into_sections(md_content)
        
        return ParsedDocument(
            doc_id=doc_id,
            title=title,
            authors=authors,
            abstract=self._extract_abstract(sections),
            sections=sections,
            metadata={"source": "markdown", "file_path": str(path)}
        )
    
    def _generate_doc_id(self, file_path: str) -> str:
        """Generate unique document ID"""
        path = Path(file_path)
        with open(path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:12]
        return f"doc_{file_hash}"
    
    def _extract_title(self, content: str, path: Path) -> str:
        """Extract title from markdown"""
        # Try YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            title_match = re.search(r'^title:\s*(.+)$', frontmatter, re.MULTILINE)
            if title_match:
                return title_match.group(1).strip('"\'')
        
        # Try first # heading
        heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()
        
        return path.stem
    
    def _extract_authors(self, content: str) -> List[str]:
        """Extract authors from markdown"""
        authors = []
        
        # Try YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            author_match = re.search(r'^authors?:\s*(.+)$', frontmatter, re.MULTILINE | re.IGNORECASE)
            if author_match:
                author_str = author_match.group(1).strip('[]"\'')
                authors = [a.strip() for a in re.split(r'[,;]', author_str)]
        
        return authors
    
    def _extract_abstract(self, sections: List[DocumentSection]) -> str:
        """Extract abstract from sections"""
        for section in sections:
            if section.section.lower() == "abstract":
                return section.raw_text
        return ""
    
    def _split_into_sections(self, content: str) -> List[DocumentSection]:
        """Split markdown into sections based on headings"""
        sections = []
        
        # Split by markdown headings (# ## ###)
        lines = content.split('\n')
        current_section = "Introduction"
        current_text = []
        current_sentences = []
        
        for line in lines:
            # Check if line is a markdown heading
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if heading_match:
                # Save previous section
                if current_text:
                    sections.append(DocumentSection(
                        section=current_section,
                        sentences=current_sentences,
                        raw_text="\n".join(current_text)
                    ))
                
                # Start new section
                current_section = heading_match.group(2).strip()
                current_text = [line]
                current_sentences = []
            else:
                if line.strip():
                    current_text.append(line)
                    # Simple sentence splitting
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
        """Simple sentence splitting"""
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
