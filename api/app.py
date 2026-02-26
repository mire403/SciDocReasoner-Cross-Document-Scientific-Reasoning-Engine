"""FastAPI application for SciDocReasoner"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from pathlib import Path

from ..ingest import PDFParser, HTMLParser, MDParser
from ..preprocess import SentenceSplitter, ClauseExtractor
from ..extraction import EntityExtractor, ClaimExtractor, HypothesisDetector
from ..linking import EntityLinker
from ..graph import GraphBuilder
from ..reasoning import HypothesisInferencer
from ..query import QueryEngine
from ..utils.storage import StructuredStorage

app = FastAPI(
    title="SciDocReasoner API",
    description="Cross-Document Scientific Reasoning Engine",
    version="0.1.0"
)

# Initialize components
storage = StructuredStorage()
sentence_splitter = SentenceSplitter()
clause_extractor = ClauseExtractor()
entity_extractor = EntityExtractor()
claim_extractor = ClaimExtractor()
hypothesis_detector = HypothesisDetector()
entity_linker = EntityLinker()
graph_builder = GraphBuilder()
hypothesis_inferencer = HypothesisInferencer()

# Global graph storage (in production, use a database)
reasoning_graph = None


class DocumentUploadResponse(BaseModel):
    doc_id: str
    title: str
    status: str


class QueryRequest(BaseModel):
    query_type: str
    parameters: Dict[str, Any] = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "SciDocReasoner",
        "description": "Cross-Document Scientific Reasoning Engine",
        "version": "0.1.0",
        "status": "operational"
    }


@app.post("/upload/pdf", response_model=DocumentUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and parse a PDF document"""
    try:
        # Save uploaded file temporarily
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / file.filename
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Parse PDF
        parser = PDFParser()
        doc = parser.parse(str(temp_path))
        
        # Save to storage
        doc_dict = doc.model_dump()
        storage.save_document(doc.doc_id, doc_dict)
        
        # Clean up temp file
        temp_path.unlink()
        
        return DocumentUploadResponse(
            doc_id=doc.doc_id,
            title=doc.title,
            status="parsed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/html", response_model=DocumentUploadResponse)
async def upload_html(file: UploadFile = File(...)):
    """Upload and parse an HTML document"""
    try:
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / file.filename
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        parser = HTMLParser()
        doc = parser.parse(str(temp_path))
        
        doc_dict = doc.model_dump()
        storage.save_document(doc.doc_id, doc_dict)
        
        temp_path.unlink()
        
        return DocumentUploadResponse(
            doc_id=doc.doc_id,
            title=doc.title,
            status="parsed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/markdown", response_model=DocumentUploadResponse)
async def upload_markdown(file: UploadFile = File(...)):
    """Upload and parse a Markdown document"""
    try:
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / file.filename
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        parser = MDParser()
        doc = parser.parse(str(temp_path))
        
        doc_dict = doc.model_dump()
        storage.save_document(doc.doc_id, doc_dict)
        
        temp_path.unlink()
        
        return DocumentUploadResponse(
            doc_id=doc.doc_id,
            title=doc.title,
            status="parsed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/{doc_id}")
async def process_document(doc_id: str):
    """Process a document: extract entities, claims, and hypotheses"""
    try:
        # Load document
        doc_data = storage.load_document(doc_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Convert sections to format expected by processors
        sections = [
            {
                "section": section.get("section", ""),
                "raw_text": section.get("raw_text", ""),
                "sentences": section.get("sentences", [])
            }
            for section in doc_data.get("sections", [])
        ]
        
        # Split into sentences
        sentences = sentence_splitter.split_document(doc_id, sections)
        sentences_dict = [s.model_dump() for s in sentences]
        
        # Extract entities
        entities = entity_extractor.extract_entities(sentences_dict)
        entities_dict = [e.model_dump() for e in entities]
        storage.save_entities(doc_id, entities_dict)
        
        # Extract claims
        claims = claim_extractor.extract_claims(sentences_dict, entities_dict)
        claims_dict = [c.model_dump() for c in claims]
        storage.save_claims(doc_id, claims_dict)
        
        # Detect hypotheses
        hypotheses = hypothesis_detector.detect_hypotheses(sentences_dict, claims_dict)
        hypotheses_dict = [h.model_dump() for h in hypotheses]
        
        return {
            "doc_id": doc_id,
            "sentences": len(sentences),
            "entities": len(entities),
            "claims": len(claims),
            "hypotheses": len(hypotheses),
            "status": "processed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/build_graph")
async def build_graph(doc_ids: List[str]):
    """Build reasoning graph from multiple documents"""
    global reasoning_graph
    
    try:
        documents = []
        all_entities = []
        all_claims = []
        all_hypotheses = []
        
        # Load all documents and their extracted data
        for doc_id in doc_ids:
            doc_data = storage.load_document(doc_id)
            if doc_data:
                documents.append(doc_data)
            
            entities = storage.load_entities(doc_id)
            if entities:
                all_entities.extend(entities)
            
            claims = storage.load_claims(doc_id)
            if claims:
                all_claims.extend(claims)
        
        # Link entities across documents
        entity_links = entity_linker.link_entities(all_entities)
        
        # Build graph
        reasoning_graph = graph_builder.build_from_documents(
            documents=documents,
            entities=all_entities,
            claims=all_claims,
            hypotheses=all_hypotheses,
            entity_links=entity_links
        )
        
        # Infer additional hypotheses
        inferred_hypotheses = hypothesis_inferencer.infer_hypotheses(reasoning_graph)
        reasoning_graph = hypothesis_inferencer.add_inferred_hypotheses_to_graph(
            reasoning_graph,
            inferred_hypotheses
        )
        
        # Save graph
        graph_data = graph_builder.to_dict()
        storage.save_graph(graph_data)
        
        return {
            "status": "built",
            "num_nodes": graph_data["num_nodes"],
            "num_edges": graph_data["num_edges"],
            "inferred_hypotheses": len(inferred_hypotheses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query_graph(request: QueryRequest):
    """Query the reasoning graph"""
    global reasoning_graph
    
    if reasoning_graph is None:
        raise HTTPException(status_code=400, detail="Graph not built. Call /build_graph first.")
    
    query_engine = QueryEngine(reasoning_graph)
    query_type = request.query_type
    params = request.parameters
    
    try:
        if query_type == "hypothesis_support":
            result = query_engine.query_hypothesis_support(
                hypothesis_id=params.get("hypothesis_id"),
                hypothesis_text=params.get("hypothesis_text")
            )
        elif query_type == "entity_evolution":
            result = query_engine.query_entity_evolution(
                entity_name=params.get("entity_name"),
                entity_id=params.get("entity_id")
            )
        elif query_type == "unvalidated_hypotheses":
            result = query_engine.query_unvalidated_hypotheses(
                min_support=params.get("min_support", 2),
                max_contradictions=params.get("max_contradictions", 1)
            )
        elif query_type == "claim_relationships":
            result = query_engine.query_claim_relationships(
                claim_id=params.get("claim_id"),
                claim_text=params.get("claim_text")
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown query type: {query_type}. Supported: hypothesis_support, entity_evolution, unvalidated_hypotheses, claim_relationships"
            )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/stats")
async def get_graph_stats():
    """Get statistics about the reasoning graph"""
    global reasoning_graph
    
    if reasoning_graph is None:
        raise HTTPException(status_code=400, detail="Graph not built.")
    
    node_types = {}
    edge_types = {}
    
    for node_id, data in reasoning_graph.nodes(data=True):
        node_type = str(data.get("node_type", "unknown"))
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    for source, target, data in reasoning_graph.edges(data=True):
        edge_type = data.get("edge_type", "unknown")
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    return {
        "num_nodes": reasoning_graph.number_of_nodes(),
        "num_edges": reasoning_graph.number_of_edges(),
        "node_types": node_types,
        "edge_types": edge_types
    }


@app.get("/documents")
async def list_documents():
    """List all processed documents"""
    docs_dir = Path("data/storage/documents")
    if not docs_dir.exists():
        return {"documents": []}
    
    documents = []
    for doc_file in docs_dir.glob("*.json"):
        doc_id = doc_file.stem
        doc_data = storage.load_document(doc_id)
        if doc_data:
            documents.append({
                "doc_id": doc_id,
                "title": doc_data.get("title", ""),
                "authors": doc_data.get("authors", [])
            })
    
    return {"documents": documents}
