from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from typing import List
from pydantic import BaseModel

# Import ML functions
from app.ml.resume_parser import extract_text_from_pdf, parse_resume_text
from app.ml.embeddings import show_embeddings, store_embedding, semantic_search
from app.ml.ats import ats_score
from app.ml.summary import generate_summary
from app.ml.fraud_detection import detect_fraud
from app.ml.query_assistant import parse_query
from app.ml.candidate_ranker import rank_candidates
from app.ml.skill_graph import generate_skill_graph
from app.ml.dedupe import dedupe_check

# Create main router with /ml/v1 prefix
router = APIRouter(prefix="/ml/v1", tags=["ML APIs"])

# Create root router for backward compatibility
root_router = APIRouter(tags=["Resume Parser"])


# Pydantic models for reindex endpoint
class CandidateData(BaseModel):
    id: str
    text: str


class ReindexRequest(BaseModel):
    candidates: List[CandidateData]


class ReindexResponse(BaseModel):
    status: str
    indexed_candidates: int
    message: str


class SummaryRequest(BaseModel):
    name: str
    experience: int
    skills: List[str] = []


@root_router.post("/parse_resume")
async def parse_resume_root(file: UploadFile = File(...)):
    """
    Parse a resume PDF file and extract structured data.
    Root-level endpoint for backward compatibility.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text from PDF
        text = extract_text_from_pdf(content)
        
        # Parse resume text
        result = parse_resume_text(text)
        
        # Include raw text so backend can store it
        result["resume_text"] = text[:10000]
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")


@router.post("/parse_resume")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """
    Parse a resume PDF file and extract structured data.
    This is the main endpoint called by the backend service.
    """
    return await parse_resume_root(file)


@router.post("/skill_extract")
def skill_extract(text: str):
    """Extract skills from plain text"""
    result = parse_resume_text(text)
    return result


@router.post("/embeddings")
def embeddings(candidate_id: str, text: str):
    """Store candidate embedding"""
    store_embedding(candidate_id, text)
    return {"status": "vector stored"}


@router.post("/semantic_search")
def search(query: str, n_results: int = 10):
    """Semantic search for candidates"""
    results = semantic_search(query, n_results=n_results)
    return results


@router.post("/ats_score")
def ats(resume_text: str, jd_text: str):
    """Calculate ATS score between resume and job description"""
    score = ats_score(resume_text, jd_text)
    return {"ats_score": score}


@router.post("/summary")
def summary(body: SummaryRequest):
    """Generate candidate summary"""
    result = generate_summary(body.name, body.experience, body.skills)
    return {"summary": result}


@router.post("/fraud_detect")
def fraud(claimed: int, computed: int):
    """Detect fraud in candidate data"""
    result = detect_fraud(claimed, computed)
    return result


@router.post("/query_parse")
def query(nl_query: str):
    """Parse natural language query"""
    filters = parse_query(nl_query)
    return filters


@router.post("/skill_graph")
def skill_graph(skills: List[str] = Form(...)):
    """Generate skill graph"""
    return generate_skill_graph(skills)


@router.post("/dedupe_check")
def dedupe(text: str):
    """Check for duplicate resumes"""
    return dedupe_check(text)


@router.get("/show_embeddings")
def show():
    """Show all stored embeddings"""
    return show_embeddings()


@router.get("/candidate_rank")
def candidate_rank(job_description: str):
    """Rank candidates by job description"""
    results = rank_candidates(job_description)
    return {"ranking": results}


@router.post("/reindex_embeddings", response_model=ReindexResponse)
def reindex_embeddings(request: ReindexRequest):
    """
    Reindex all candidates into ChromaDB for semantic search.
    
    This endpoint accepts a list of candidates with their IDs and text content,
    generates embeddings, and stores them in ChromaDB. It safely handles
    duplicates by upserting (update or insert).
    
    Example request:
    {
        "candidates": [
            {"id": "uuid-1", "text": "resume text..."},
            {"id": "uuid-2", "text": "resume text..."}
        ]
    }
    """
    try:
        indexed_count = 0
        
        for candidate in request.candidates:
            try:
                # Store embedding (upsert handles duplicates)
                store_embedding(candidate.id, candidate.text)
                indexed_count += 1
            except Exception as e:
                # Log error but continue with other candidates
                print(f"Failed to index candidate {candidate.id}: {str(e)}")
                continue
        
        return ReindexResponse(
            status="success",
            indexed_candidates=indexed_count,
            message=f"Successfully indexed {indexed_count} out of {len(request.candidates)} candidates"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reindexing failed: {str(e)}"
        )
