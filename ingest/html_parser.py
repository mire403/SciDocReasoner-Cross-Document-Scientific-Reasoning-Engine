"""HTML document parser (for arXiv, blogs, etc.)"""

import hashlib
from pathlib import Path
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from .pdf_parser import ParsedDocument, DocumentSection


class HTMLParser:
    """Parser for HTML documents"""
    
    def __init__(self):
        self.section_keywords = [
            "abstract", "introduction", "related work", "methodology", 
            "methods", "method", "results", "discussion", "conclusion",
            "references", "appendix"
        ]
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse an HTML file into structured format"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"HTML file not found: {file_path}")
        
        # Generate doc_id
        doc_id = self._generate_doc_id(file_path)
        
        # Parse HTML
        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'lxml')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract authors
        authors = self._extract_authors(soup)
        
        # Extract main content
        text_content = self._extract_text(soup)
        
        # Split into sections
        sections = self._split_into_sections(text_content, soup)
        
        return ParsedDocument(
            doc_id=doc_id,
            title=title,
            authors=authors,
            abstract=self._extract_abstract(sections),
            sections=sections,
            metadata={"source": "html", "file_path": str(path)}
        )
    
    def _generate_doc_id(self, file_path: str) -> str:
        """Generate unique document ID"""
        path = Path(file_path)
        with open(path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:12]
        return f"doc_{file_hash}"
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML"""
        # Try various title selectors
        title_selectors = [
            'h1.title',
            'h1',
            'title',
            '.title',
            '[class*="title"]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return "Untitled"
    
    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """Extract authors from HTML"""
        authors = []
        
        # Try various author selectors
        author_selectors = [
            '.authors',
            '[class*="author"]',
            'meta[name="author"]',
            '.author'
        ]
        
        for selector in author_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text:
                    # Split by common delimiters
                    authors.extend([a.strip() for a in text.split(',')])
        
        return list(set(authors))  # Remove duplicates
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Try to find main content area
        main_selectors = [
            'main',
            'article',
            '.content',
            '#content',
            'body'
        ]
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text()
        
        return soup.get_text()
    
    def _extract_abstract(self, sections: List[DocumentSection]) -> str:
        """Extract abstract from sections"""
        for section in sections:
            if section.section.lower() == "abstract":
                return section.raw_text
        return ""
    
    def _split_into_sections(self, text: str, soup: BeautifulSoup) -> List[DocumentSection]:
        """Split text into sections"""
        sections = []
        
        # Try to use HTML structure first
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        if headings:
            current_section = "Introduction"
            current_text = []
            current_sentences = []
            
            for heading in headings:
                heading_text = heading.get_text().strip()
                
                # Save previous section
                if current_text:
                    sections.append(DocumentSection(
                        section=current_section,
                        sentences=current_sentences,
                        raw_text="\n".join(current_text)
                    ))
                
                # Start new section
                current_section = heading_text
                current_text = [heading_text]
                current_sentences = []
                
                # Get content until next heading
                for sibling in heading.next_siblings:
                    if sibling.name in ['h1', 'h2', 'h3', 'h4']:
                        break
                    if hasattr(sibling, 'get_text'):
                        text = sibling.get_text().strip()
                        if text:
                            current_text.append(text)
                            sentences = self._simple_sentence_split(text)
                            current_sentences.extend(sentences)
            
            # Add final section
            if current_text:
                sections.append(DocumentSection(
                    section=current_section,
                    sentences=current_sentences,
                    raw_text="\n".join(current_text)
                ))
        else:
            # Fallback to text-based splitting
            lines = text.split('\n')
            current_section = "Introduction"
            current_text = []
            current_sentences = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                is_heading = False
                for keyword in self.section_keywords:
                    if line.lower().startswith(keyword.lower()):
                        if current_text:
                            sections.append(DocumentSection(
                                section=current_section,
                                sentences=current_sentences,
                                raw_text="\n".join(current_text)
                            ))
                        current_section = line
                        current_text = [line]
                        current_sentences = []
                        is_heading = True
                        break
                
                if not is_heading:
                    current_text.append(line)
                    sentences = self._simple_sentence_split(line)
                    current_sentences.extend(sentences)
            
            if current_text:
                sections.append(DocumentSection(
                    section=current_section,
                    sentences=current_sentences,
                    raw_text="\n".join(current_text)
                ))
        
        return sections
    
    def _simple_sentence_split(self, text: str) -> List[str]:
        """Simple sentence splitting"""
        import re
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
