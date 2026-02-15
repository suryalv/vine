#!/usr/bin/env python3
"""
End-to-end pipeline test for complex insurance documents.
Tests: parsing → chunking → (optional) upload → (optional) chat.
"""

import os
import sys
import json

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

from layers.parsing import parse_document
from layers.chunking import chunk_document

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))

# All test documents
DOCUMENTS = [
    # Existing documents
    'Commercial_Property_Policy_Meridian_Steel.pdf',
    'ACORD_125_Application_Pacific_Coast_Logistics.pdf',
    'Loss_Run_Report_5Year_Acme_Manufacturing.pdf',
    'Statement_of_Values_All_Locations.docx',
    'Endorsement_Package_Wind_Hail_Amended.docx',
    'UW_Submission_Summary_Greenfield_Agri.docx',
    # New complex documents
    'Workers_Comp_Retro_Rating_Atlas_Industries.pdf',
    'Excess_Umbrella_MultiLayer_TechCorp_Global.pdf',
    'CAT_Loss_Report_Hurricane_Damage_CrescentBay.docx',
    'DO_Fiduciary_Liability_Pinnacle_Healthcare.docx',
]


def test_parsing_and_chunking():
    """Test parsing and chunking for all documents."""
    print("=" * 70)
    print("PIPELINE TEST: Parsing & Chunking")
    print("=" * 70)
    print()

    total_pages = 0
    total_chunks = 0
    results = []

    for filename in DOCUMENTS:
        filepath = os.path.join(SAMPLE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP: {filename} (file not found)")
            continue

        print(f"  Testing: {filename}")
        print(f"  {'─' * 60}")

        # Parse — returns list of (page_number, text) tuples
        try:
            pages = parse_document(filepath)
            num_pages = len(pages)
            total_text_len = sum(len(text) for _, text in pages)
            print(f"    Parsed: {num_pages} pages, {total_text_len:,} chars total")

            # Show first 150 chars of each page
            for page_num, text in pages[:3]:
                text_preview = text[:150].replace('\n', ' ')
                print(f"    Page {page_num} preview: {text_preview}...")
            if num_pages > 3:
                print(f"    ... ({num_pages - 3} more pages)")

        except Exception as e:
            print(f"    PARSE ERROR: {e}")
            results.append({'file': filename, 'status': 'PARSE_ERROR', 'error': str(e)})
            print()
            continue

        # Chunk
        try:
            chunks = chunk_document(pages, filename)
            num_chunks = len(chunks)
            chunk_sizes = [len(c.text) for c in chunks]
            avg_chunk = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            min_chunk = min(chunk_sizes) if chunk_sizes else 0
            max_chunk = max(chunk_sizes) if chunk_sizes else 0

            print(f"    Chunked: {num_chunks} chunks")
            print(f"    Chunk sizes: avg={avg_chunk:.0f}, min={min_chunk}, max={max_chunk}")

            # Show sections found
            sections = set(c.section for c in chunks if c.section)
            if sections:
                print(f"    Sections detected: {len(sections)}")
                for s in sorted(sections)[:8]:
                    print(f"      - {s}")
                if len(sections) > 8:
                    print(f"      ... ({len(sections) - 8} more)")

            # Show sample chunks
            print(f"    Sample chunks:")
            for i, chunk in enumerate(chunks[:3]):
                text_preview = chunk.text[:120].replace('\n', ' ')
                print(f"      [{i+1}] Page {chunk.page}, Section: {chunk.section or 'N/A'}")
                print(f"          {text_preview}...")

            total_pages += num_pages
            total_chunks += num_chunks
            results.append({
                'file': filename,
                'status': 'OK',
                'pages': num_pages,
                'chunks': num_chunks,
                'total_chars': total_text_len,
                'avg_chunk_size': round(avg_chunk),
                'sections': len(sections),
            })

        except Exception as e:
            print(f"    CHUNK ERROR: {e}")
            results.append({'file': filename, 'status': 'CHUNK_ERROR', 'error': str(e)})

        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Documents tested: {len(results)}")
    print(f"  Successful: {sum(1 for r in results if r['status'] == 'OK')}")
    print(f"  Failed: {sum(1 for r in results if r['status'] != 'OK')}")
    print(f"  Total pages parsed: {total_pages}")
    print(f"  Total chunks created: {total_chunks}")
    print()

    # Results table
    print(f"  {'File':<55} {'Status':<8} {'Pages':<7} {'Chunks':<8} {'Sections'}")
    print(f"  {'─' * 55} {'─' * 8} {'─' * 7} {'─' * 8} {'─' * 8}")
    for r in results:
        if r['status'] == 'OK':
            print(f"  {r['file']:<55} {r['status']:<8} {r['pages']:<7} {r['chunks']:<8} {r['sections']}")
        else:
            print(f"  {r['file']:<55} {r['status']:<8} — {r.get('error', '')[:30]}")

    print()
    return results


def test_upload_api():
    """Try uploading documents via the API."""
    import requests

    BASE = "http://localhost:8000"
    print("=" * 70)
    print("PIPELINE TEST: API Upload")
    print("=" * 70)
    print()

    # Check health
    try:
        resp = requests.get(f"{BASE}/health", timeout=5)
        health = resp.json()
        print(f"  Backend status: {health['status']}")
        print(f"  LLM: {health['llm_backend']}, Embedding: {health['embedding_backend']}")
        print(f"  Gemini configured: {health['gemini_configured']}")
        if not health['gemini_configured']:
            print()
            print("  WARNING: Gemini API key not configured.")
            print("  Upload will fail at embedding step.")
            print("  Set GEMINI_API_KEY environment variable and restart backend.")
            print()
    except Exception as e:
        print(f"  Backend not reachable: {e}")
        return

    # Try uploading one document to see the actual error
    test_file = os.path.join(SAMPLE_DIR, 'Workers_Comp_Retro_Rating_Atlas_Industries.pdf')
    print(f"  Attempting upload: Workers_Comp_Retro_Rating_Atlas_Industries.pdf")
    try:
        with open(test_file, 'rb') as f:
            resp = requests.post(
                f"{BASE}/api/documents/upload",
                files={"file": ("Workers_Comp_Retro_Rating_Atlas_Industries.pdf", f, "application/pdf")},
                timeout=60,
            )
        if resp.status_code == 200:
            data = resp.json()
            print(f"  SUCCESS: {data['num_pages']} pages, {data['num_chunks']} chunks stored")
            print(f"  Document ID: {data['document_id']}")
        else:
            print(f"  FAILED ({resp.status_code}): {resp.json().get('detail', resp.text)}")
    except Exception as e:
        print(f"  ERROR: {e}")

    print()


def test_chat_queries():
    """Test chat queries against uploaded documents."""
    import requests

    BASE = "http://localhost:8000"
    print("=" * 70)
    print("PIPELINE TEST: Chat Queries")
    print("=" * 70)
    print()

    # Check if documents exist
    try:
        resp = requests.get(f"{BASE}/api/documents", timeout=5)
        docs = resp.json()
        if not docs:
            print("  No documents uploaded. Skipping chat tests.")
            return
        print(f"  Documents in store: {len(docs)}")
        for d in docs:
            print(f"    - {d['filename']} ({d['num_chunks']} chunks)")
        print()
    except Exception as e:
        print(f"  Backend error: {e}")
        return

    # Test queries
    queries = [
        "What is the total insured value for Atlas Industries across all states?",
        "Describe the retrospective rating plan parameters and the retro formula.",
        "What OSHA citations has Atlas Industries received and what are the penalties?",
        "What is the Named Storm deductible for Crescent Bay Resort?",
        "Explain the wind vs water causation allocation for the hurricane damage.",
        "What are the D&O coverage sides and their retentions for Pinnacle Healthcare?",
        "What is the EPLI wage and hour exclusion and why was it applied?",
        "Describe TechCorp's excess liability tower structure and total limits.",
        "What are the large loss claims for Atlas Marine Construction in Florida?",
        "What coverage gaps were identified in the Crescent Bay hurricane claim?",
    ]

    session_id = "test-session-001"
    for i, query in enumerate(queries):
        print(f"  Query {i+1}: {query[:70]}...")
        try:
            resp = requests.post(
                f"{BASE}/api/chat",
                json={"query": query, "session_id": session_id},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                answer_preview = data['answer'][:200].replace('\n', ' ')
                halluc = data['hallucination']
                actions = data.get('actions', [])
                print(f"    Answer: {answer_preview}...")
                print(f"    Hallucination: score={halluc.get('overall_score', 'N/A')}, "
                      f"rating={halluc.get('rating', 'N/A')}")
                print(f"    Sources: {len(data.get('sources', []))} chunks")
                print(f"    Actions: {len(actions)}")
                if actions:
                    for a in actions[:2]:
                        print(f"      - [{a.get('priority', '?')}] {a.get('action', '?')[:60]}")
            else:
                print(f"    FAILED ({resp.status_code}): {resp.json().get('detail', '')[:80]}")
        except Exception as e:
            print(f"    ERROR: {e}")
        print()


if __name__ == '__main__':
    # Phase 1: Test parsing and chunking (works without API key)
    results = test_parsing_and_chunking()

    # Phase 2: Test API upload (requires running backend + API key)
    test_upload_api()

    # Phase 3: Test chat (requires documents uploaded)
    test_chat_queries()
