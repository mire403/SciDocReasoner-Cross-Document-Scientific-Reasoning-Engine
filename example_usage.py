"""
Example usage of SciDocReasoner

This script demonstrates how to use the SciDocReasoner system
to process documents and build a reasoning graph.
"""

import os
from pathlib import Path
from scidoc_reasoner.ingest import PDFParser, HTMLParser, MDParser
from scidoc_reasoner.preprocess import SentenceSplitter
from scidoc_reasoner.extraction import EntityExtractor, ClaimExtractor, HypothesisDetector
from scidoc_reasoner.linking import EntityLinker
from scidoc_reasoner.graph import GraphBuilder
from scidoc_reasoner.reasoning import HypothesisInferencer
from scidoc_reasoner.query import QueryEngine
from scidoc_reasoner.utils.storage import StructuredStorage


def process_document(file_path: str, storage: StructuredStorage):
    """Process a single document"""
    print(f"\n📄 Processing: {file_path}")
    
    # Determine parser based on file extension
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        parser = PDFParser()
    elif file_ext in ['.html', '.htm']:
        parser = HTMLParser()
    elif file_ext in ['.md', '.markdown']:
        parser = MDParser()
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")
    
    # Parse document
    doc = parser.parse(file_path)
    print(f"  ✓ Parsed: {doc.title}")
    
    # Save document
    doc_dict = doc.model_dump()
    storage.save_document(doc.doc_id, doc_dict)
    
    # Split into sentences
    sections = [
        {
            "section": section.section,
            "raw_text": section.raw_text,
            "sentences": section.sentences
        }
        for section in doc.sections
    ]
    
    sentence_splitter = SentenceSplitter()
    sentences = sentence_splitter.split_document(doc.doc_id, sections)
    sentences_dict = [s.model_dump() for s in sentences]
    print(f"  ✓ Split into {len(sentences)} sentences")
    
    # Extract entities
    entity_extractor = EntityExtractor()
    entities = entity_extractor.extract_entities(sentences_dict)
    entities_dict = [e.model_dump() for e in entities]
    storage.save_entities(doc.doc_id, entities_dict)
    print(f"  ✓ Extracted {len(entities)} entities")
    
    # Extract claims
    claim_extractor = ClaimExtractor()
    claims = claim_extractor.extract_claims(sentences_dict, entities_dict)
    claims_dict = [c.model_dump() for c in claims]
    storage.save_claims(doc.doc_id, claims_dict)
    print(f"  ✓ Extracted {len(claims)} claims")
    
    # Detect hypotheses
    hypothesis_detector = HypothesisDetector()
    hypotheses = hypothesis_detector.detect_hypotheses(sentences_dict, claims_dict)
    hypotheses_dict = [h.model_dump() for h in hypotheses]
    print(f"  ✓ Detected {len(hypotheses)} hypotheses")
    
    return {
        "doc": doc_dict,
        "entities": entities_dict,
        "claims": claims_dict,
        "hypotheses": hypotheses_dict
    }


def build_reasoning_graph(documents_data: list, storage: StructuredStorage):
    """Build the reasoning graph from processed documents"""
    print("\n🧠 Building Reasoning Graph...")
    
    # Collect all data
    all_documents = []
    all_entities = []
    all_claims = []
    all_hypotheses = []
    
    for doc_data in documents_data:
        all_documents.append(doc_data["doc"])
        all_entities.extend(doc_data["entities"])
        all_claims.extend(doc_data["claims"])
        all_hypotheses.extend(doc_data["hypotheses"])
    
    print(f"  📊 Total: {len(all_documents)} docs, {len(all_entities)} entities, "
          f"{len(all_claims)} claims, {len(all_hypotheses)} hypotheses")
    
    # Link entities across documents
    entity_linker = EntityLinker()
    entity_links = entity_linker.link_entities(all_entities)
    print(f"  ✓ Linked {len(entity_links)} entity clusters")
    
    # Build graph
    graph_builder = GraphBuilder()
    graph = graph_builder.build_from_documents(
        documents=all_documents,
        entities=all_entities,
        claims=all_claims,
        hypotheses=all_hypotheses,
        entity_links=entity_links
    )
    print(f"  ✓ Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # Infer additional hypotheses
    hypothesis_inferencer = HypothesisInferencer()
    inferred_hypotheses = hypothesis_inferencer.infer_hypotheses(graph, max_hypotheses=5)
    print(f"  ✓ Inferred {len(inferred_hypotheses)} additional hypotheses")
    
    # Add inferred hypotheses to graph
    graph = hypothesis_inferencer.add_inferred_hypotheses_to_graph(graph, inferred_hypotheses)
    
    # Save graph
    graph_data = graph_builder.to_dict()
    storage.save_graph(graph_data)
    
    return graph


def query_examples(graph):
    """Run example queries"""
    print("\n🔍 Running Example Queries...")
    
    query_engine = QueryEngine(graph)
    
    # Query 1: Find unvalidated hypotheses
    print("\n1️⃣ Query: Unvalidated Hypotheses")
    unvalidated = query_engine.query_unvalidated_hypotheses(min_support=2, max_contradictions=1)
    print(f"   Found {len(unvalidated)} unvalidated hypotheses")
    for hyp in unvalidated[:3]:  # Show first 3
        print(f"   - {hyp['text'][:80]}...")
        print(f"     Support: {hyp['supporting_count']}, Contradictions: {hyp['contradicting_count']}")
    
    # Query 2: Entity evolution (if entities exist)
    print("\n2️⃣ Query: Entity Evolution")
    # Get first entity from graph
    entities = [
        (node_id, data) for node_id, data in graph.nodes(data=True)
        if data.get("node_type").value == "entity"
    ]
    if entities:
        entity_node_id, entity_data = entities[0]
        entity_name = entity_data.get("text", "")
        evolution = query_engine.query_entity_evolution(entity_name=entity_name)
        print(f"   Entity: {entity_name}")
        print(f"   Related claims: {len(evolution.get('related_claims', []))}")
        print(f"   Related hypotheses: {len(evolution.get('related_hypotheses', []))}")
    
    # Query 3: Hypothesis support (if hypotheses exist)
    print("\n3️⃣ Query: Hypothesis Support")
    hypotheses = [
        (node_id, data) for node_id, data in graph.nodes(data=True)
        if data.get("node_type").value == "hypothesis"
    ]
    if hypotheses:
        hyp_node_id, hyp_data = hypotheses[0]
        hyp_text = hyp_data.get("text", "")
        support = query_engine.query_hypothesis_support(hypothesis_text=hyp_text)
        print(f"   Hypothesis: {hyp_text[:80]}...")
        print(f"   Supporting claims: {len(support.get('supporting', []))}")
        print(f"   Contradicting claims: {len(support.get('contradicting', []))}")


def main():
    """Main example workflow"""
    print("=" * 60)
    print("SciDocReasoner — Cross-Document Scientific Reasoning Engine")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not set in environment variables")
        print("   Set it in .env file or export it before running")
        return
    
    # Initialize storage
    storage = StructuredStorage()
    
    # Example: Process documents (replace with your document paths)
    document_paths = [
        # Add your document paths here
        # "path/to/paper1.pdf",
        # "path/to/paper2.html",
        # "path/to/paper3.md",
    ]
    
    if not document_paths:
        print("\n📝 No documents specified. Please add document paths to document_paths list.")
        print("   Example:")
        print('   document_paths = ["paper1.pdf", "paper2.pdf"]')
        return
    
    # Process all documents
    documents_data = []
    for doc_path in document_paths:
        if Path(doc_path).exists():
            try:
                doc_data = process_document(doc_path, storage)
                documents_data.append(doc_data)
            except Exception as e:
                print(f"  ✗ Error processing {doc_path}: {e}")
        else:
            print(f"  ✗ File not found: {doc_path}")
    
    if not documents_data:
        print("\n⚠️  No documents were successfully processed.")
        return
    
    # Build reasoning graph
    graph = build_reasoning_graph(documents_data, storage)
    
    # Run example queries
    query_examples(graph)
    
    print("\n" + "=" * 60)
    print("✅ Processing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
