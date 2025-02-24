from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
from resume import EnhancedJobScraper
from resume_optimizer import ResumeOptimizer
import os
from dotenv import load_dotenv
import logging
import subprocess
from datetime import datetime
from utils import validate_latex_content, clean_latex_content

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Resume ATS Optimizer API")

# Create required directories
os.makedirs("temp", exist_ok=True)
os.makedirs("modified", exist_ok=True)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store API key (in production, use proper env variables)
API_KEY_STORE = {}

class ApiKeyModel(BaseModel):
    api_key: str

class JobUrlModel(BaseModel):
    url: str
    api_key: str

class ResumeAnalysisModel(BaseModel):
    resume_content: str
    job_analysis: Dict
    api_key: str

class ModifyResumeModel(BaseModel):
    resume_content: str
    modifications: Dict
    company_name: str
    api_key: str

class ModifiedResumeRequest(BaseModel):
    resume_content: str
    comparison: Dict
    api_key: str
    company_name: str = "Company"  # Default value if not provided

@app.post("/api/set-api-key")
async def set_api_key(api_key_data: ApiKeyModel):
    """Validate and store Gemini API key"""
    try:
        # Validate API key by creating a test instance
        optimizer = ResumeOptimizer(api_key_data.api_key)
        API_KEY_STORE["key"] = api_key_data.api_key
        return {"status": "success", "message": "API key set successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/analyze-job-url")
async def analyze_job_url(data: JobUrlModel):
    """Extract and analyze job posting from URL"""
    try:
        job_scraper = EnhancedJobScraper(data.api_key)
        
        # Extract job content
        job_content = job_scraper.scrape_website(data.url)
        
        # Analyze job description
        analysis = job_scraper.analyze_job_description(job_content)
        
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing job URL: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    api_key: str = Form(...)
):
    """Handle resume file upload"""
    temp_path = None
    try:
        # Validate file extension
        if not file.filename.endswith('.tex'):
            raise ValueError("Only .tex files are allowed")

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = f"temp/resume_{timestamp}.tex"
        
        # Read file content
        content = await file.read()
        if not content:
            raise ValueError("Empty file")
            
        # Decode content
        try:
            resume_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError("Invalid file encoding. Please use UTF-8")
        
        # Clean LaTeX content
        resume_content = clean_latex_content(resume_content)
        
        # Log the content for debugging
        logger.debug(f"Received LaTeX content:\n{resume_content[:200]}...")  # Log first 200 chars
            
        # Validate LaTeX content
        if not validate_latex_content(resume_content):
            logger.error(f"LaTeX validation failed for content:\n{resume_content[:500]}")  # Log more content on error
            raise ValueError("Invalid LaTeX format. Please ensure your file contains proper LaTeX structure with \\documentclass and document environment.")
            
        # Save file
        with open(temp_path, "w", encoding='utf-8') as f:
            f.write(resume_content)
            
        logger.info(f"Successfully uploaded and validated resume: {file.filename}")
        
        return {
            "status": "success",
            "content": resume_content,
            "file_path": temp_path,
            "message": "Resume uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        # Cleanup on error
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Return more specific error messages
        error_msg = str(e)
        if "Invalid LaTeX format" in error_msg:
            error_msg = "Please ensure your LaTeX file contains \\documentclass, \\begin{document}, and \\end{document}"
        elif "UnicodeDecodeError" in error_msg:
            error_msg = "File encoding error. Please save your file with UTF-8 encoding"
            
        raise HTTPException(status_code=400, detail=error_msg)

@app.post("/api/optimize-resume")
async def optimize_resume(data: ResumeAnalysisModel):
    """Compare resume with job analysis"""
    try:
        optimizer = ResumeOptimizer(data.api_key)
        comparison = optimizer.analyze_resume_vs_jd(
            data.resume_content, 
            data.job_analysis
        )
        return comparison
    except Exception as e:
        logger.error(f"Error optimizing resume: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/generate-modified-resume")
async def generate_modified_resume(data: ModifiedResumeRequest):
    """Generate modified resume with optimizations"""
    try:
        optimizer = ResumeOptimizer(data.api_key)
        modified_resume = optimizer.generate_modified_resume(
            resume_content=data.resume_content,
            comparison_data=data.comparison,  # Pass the full comparison data
            company_name=data.company_name
        )
        return modified_resume
    except Exception as e:
        logger.error(f"Error generating modified resume: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/resume-analysis/{company_name}")
async def get_resume_analysis(company_name: str):
    """Get analysis for a specific resume"""
    try:
        modified_path = f"modified/{company_name}_resume.tex"
        temp_path = f"temp/{company_name}_original.tex"
        
        if not os.path.exists(modified_path) or not os.path.exists(temp_path):
            raise HTTPException(status_code=404, detail="Resume not found")
            
        with open(modified_path, "r", encoding='utf-8') as f:
            modified_content = f.read()
        with open(temp_path, "r", encoding='utf-8') as f:
            original_content = f.read()
            
        return {
            "original_content": original_content,
            "modified_content": modified_content
        }
    except Exception as e:
        logger.error(f"Error retrieving resume analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/resumes")
async def list_resumes():
    """List all modified resumes"""
    try:
        modified_files = os.listdir("modified")
        temp_files = os.listdir("temp")
        
        resumes = []
        for file in modified_files:
            if file.endswith(".tex"):
                company_name = file.replace("_resume.tex", "")
                resumes.append({
                    "company_name": company_name,
                    "modified_path": f"modified/{file}",
                    "original_path": f"temp/{company_name}_original.tex"
                })
                
        return {"resumes": resumes}
    except Exception as e:
        logger.error(f"Error listing resumes: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/resume/{company_name}/diff")
async def get_resume_diff(company_name: str):
    """Get a detailed diff between original and modified resume"""
    try:
        modified_path = f"modified/{company_name}_resume.tex"
        temp_path = f"temp/{company_name}_original.tex"
        
        if not os.path.exists(modified_path) or not os.path.exists(temp_path):
            raise HTTPException(status_code=404, detail="Resume not found")
            
        with open(modified_path, "r", encoding="utf-8") as f:
            modified = f.read()
        with open(temp_path, "r", encoding="utf-8") as f:
            original = f.read()
            
        # Get section-by-section differences
        sections_diff = {}
        for section in ["Technical Skills", "Experience", "Projects", "Education"]:
            orig_section = extract_section(original, section)
            mod_section = extract_section(modified, section)
            if orig_section != mod_section:
                sections_diff[section] = {
                    "original": orig_section,
                    "modified": mod_section
                }
        
        return {
            "sections_changed": list(sections_diff.keys()),
            "diff_details": sections_diff
        }
    except Exception as e:
        logger.error(f"Error getting resume diff: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/resume/{company_name}/stats")
async def get_resume_stats(company_name: str):
    """Get statistics and analysis of the resume optimization"""
    try:
        modified_path = f"modified/{company_name}_resume.tex"
        analysis_path = f"temp/{company_name}_analysis.json"
        
        if not os.path.exists(modified_path) or not os.path.exists(analysis_path):
            raise HTTPException(status_code=404, detail="Resume or analysis not found")
            
        with open(analysis_path, "r") as f:
            analysis = json.load(f)
            
        return {
            "ats_score": analysis.get("ats_score", 0),
            "keywords_added": len(analysis.get("missing_keywords", [])),
            "sections_modified": len(analysis.get("suggested_modifications", {})),
            "improvement_suggestions": analysis.get("improvement_suggestions", [])
        }
    except Exception as e:
        logger.error(f"Error getting resume stats: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/resume/convert-pdf")
async def convert_to_pdf(data: ModifyResumeModel):
    """Convert LaTeX resume to PDF"""
    try:
        # Save LaTeX content temporarily
        tex_path = f"temp/{data.company_name}_resume.tex"
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(data.resume_content)
        
        # Convert to PDF
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=400, 
                detail=f"PDF conversion failed: {result.stderr}"
            )
        
        pdf_path = tex_path.replace('.tex', '.pdf')
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=400, detail="PDF file not generated")
            
        return {"pdf_path": pdf_path}
    except Exception as e:
        logger.error(f"Error converting to PDF: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 