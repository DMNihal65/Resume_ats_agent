import streamlit as st
from pathlib import Path
import os
from typing import Dict, List, Any
import json
from langchain_google_genai import GoogleGenerativeAI
from langchain.agents import Tool, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from resume import EnhancedJobScraper
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resume_optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ResumeOptimizer:
    def __init__(self, gemini_api_key: str):
        self.setup_llm(gemini_api_key)
        self.job_scraper = EnhancedJobScraper(gemini_api_key)
        self.setup_output_parsers()
        self.setup_directories()
        self.cached_analysis = {}

    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        Path("temp").mkdir(exist_ok=True)
        Path("modified").mkdir(exist_ok=True)

    def setup_llm(self, api_key: str):
        self.llm = GoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.1,  # Lower temperature for more consistent output
            max_output_tokens=2000
        )

    def setup_output_parsers(self):
        # Simplify the schema to reduce parsing complexity
        resume_analysis_schemas = [
            ResponseSchema(name="missing_keywords", type="list", 
                         description="List of keywords from job description missing in resume"),
            ResponseSchema(name="existing_keywords", type="list", 
                         description="List of keywords present in both resume and job description"),
            ResponseSchema(name="suggested_modifications", type="dict", 
                         description="Dictionary of section modifications")
        ]
        self.resume_parser = StructuredOutputParser.from_response_schemas(resume_analysis_schemas)

    def read_latex_resume(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def analyze_resume_vs_jd(self, resume_text: str, jd_analysis: Dict) -> Dict:
        """Analyze resume against job description"""
        try:
            # Check cache first
            cache_key = f"{hash(resume_text)}-{hash(str(jd_analysis))}"
            if cache_key in self.cached_analysis:
                logger.info("Using cached analysis results")
                return self.cached_analysis[cache_key]

            prompt = PromptTemplate(
                template="""You are a resume optimization expert. Analyze this resume against the job description and provide a structured response.

                Resume Content:
                {resume_text}

                Job Description Analysis:
                {jd_analysis}

                STRICT OUTPUT FORMAT:
                You must return a JSON object with EXACTLY these keys and formats:
                {{
                    "missing_keywords": ["keyword1", "keyword2"],
                    "existing_keywords": ["keyword3", "keyword4"],
                    "suggested_modifications": {{
                        "section_name": {{
                            "content": "LaTeX formatted content",
                            "location": "start|end"
                        }}
                    }},
                    "ats_score": 85,
                    "improvement_suggestions": [
                        {{
                            "title": "suggestion title",
                            "description": "detailed description",
                            "priority": "high|medium|low",
                            "type": "warning|improvement"
                        }}
                    ]
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text or markdown
                2. ALL keys must be present in the response
                3. "missing_keywords" and "existing_keywords" must be arrays of strings
                4. "suggested_modifications" must contain section names from the resume
                5. Each modification must have both "content" and "location"
                6. "location" must be exactly "start" or "end"
                7. "content" must be valid LaTeX code
                8. "ats_score" must be a number between 0 and 100
                9. Do not include any explanatory text, only the JSON object

                ANALYZE AND RESPOND:""",
                input_variables=["resume_text", "jd_analysis"]
            )

            logger.info("Sending analysis prompt to LLM")
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({
                "resume_text": resume_text,
                "jd_analysis": json.dumps(jd_analysis, indent=2)
            })

            # Clean and parse the response
            response_text = result['text'].strip()
            # Remove any markdown code block indicators
            response_text = response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                response_text = response_text[start_idx:end_idx]
            
            # Parse and validate JSON
            analysis = json.loads(response_text)
            
            # Validate required keys
            required_keys = {
                "missing_keywords", 
                "existing_keywords", 
                "suggested_modifications",
                "ats_score",
                "improvement_suggestions"
            }
            
            if not all(key in analysis for key in required_keys):
                missing_keys = required_keys - set(analysis.keys())
                raise ValueError(f"Missing required keys: {missing_keys}")

            # Cache the results
            self.cached_analysis[cache_key] = analysis
            
            # Save analysis for later reference
            analysis_path = f"temp/{jd_analysis.get('company_name', 'default')}_analysis.json"
            with open(analysis_path, 'w') as f:
                json.dump(analysis, f, indent=2)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            raise

    def modify_latex_resume(self, resume_content: str, modifications: Dict, company_name: str) -> str:
        """Generate modified resume content with suggested changes"""
        try:
            prompt = PromptTemplate(
                template="""You are a LaTeX expert. Modify this resume according to the suggested modifications.
                
                Original Resume:
                {resume_content}
                
                Modifications to make:
                {modifications}
                
                STRICT RULES:
                1. Return ONLY the modified LaTeX content, no other text
                2. Keep all LaTeX formatting and structure intact
                3. Only modify the specified sections
                4. Add content exactly at the specified locations (start/end of sections)
                5. Ensure all LaTeX commands are valid
                6. Maintain proper spacing and indentation
                7. Do not remove any existing content
                8. Do not add any comments or explanations
                
                MODIFY AND RETURN THE COMPLETE LATEX RESUME:""",
                input_variables=["resume_content", "modifications"]
            )

            logger.info("Sending modification prompt to LLM")
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({
                "resume_content": resume_content,
                "modifications": json.dumps(modifications, indent=2)
            })

            modified_content = result['text'].strip()
            
            # Save the modified resume
            modified_path = f"modified/{company_name}_resume.tex"
            with open(modified_path, "w", encoding='utf-8') as f:
                f.write(modified_content)
            
            logger.info(f"Modified resume saved to {modified_path}")
            return modified_content

        except Exception as e:
            logger.error(f"Error modifying resume: {str(e)}")
            raise

    def generate_modified_resume(self, resume_content: str, comparison_data: Dict, company_name: str = "Company") -> Dict:
        """Generate modified resume based on comparison data"""
        try:
            if not comparison_data or not comparison_data.get('missing_keywords'):
                raise ValueError("Invalid comparison data")

            # First, split the resume into structural parts
            parts = self._split_latex_document(resume_content)
            
            # Identify sections that need modification
            sections_to_modify = self._identify_sections_to_modify(
                parts['sections'],
                comparison_data.get('missing_keywords', []),
                comparison_data.get('improvement_suggestions', [])
            )

            # Modify each section separately
            modified_sections = {}
            for section_name, section_content in sections_to_modify.items():
                modified_sections[section_name] = self._modify_section(
                    section_name,
                    section_content,
                    comparison_data
                )

            # Reconstruct the document
            modified_content = self._reconstruct_latex_document(
                parts['preamble'],
                {**parts['sections'], **modified_sections},
                parts['ending']
            )

            # Save the modified resume
            modified_path = f"modified/{company_name}_resume.tex"
            os.makedirs("modified", exist_ok=True)
            
            with open(modified_path, "w", encoding='utf-8') as f:
                f.write(modified_content)

            return {
                "status": "success",
                "modified_content": modified_content,
                "original_content": resume_content,
                "sections_modified": list(modified_sections.keys()),
                "file_path": modified_path
            }

        except Exception as e:
            logger.error(f"Error generating modified resume: {str(e)}")
            raise

    def _split_latex_document(self, content: str) -> Dict[str, Any]:
        """Split LaTeX document into preamble, sections, and ending"""
        lines = content.split('\n')
        preamble = []
        sections = {}
        ending = []
        
        current_section = None
        current_content = []
        in_document = False
        
        for line in lines:
            if '\\begin{document}' in line:
                in_document = True
                preamble.append(line)
            elif '\\end{document}' in line:
                in_document = False
                ending.append(line)
            elif not in_document:
                preamble.append(line)
            elif line.strip().startswith('\\section'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line.strip()
                current_content = [line]
            elif current_section:
                current_content.append(line)
            else:
                if not any(sections.values()):
                    preamble.append(line)
                else:
                    ending.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return {
            'preamble': '\n'.join(preamble),
            'sections': sections,
            'ending': '\n'.join(ending)
        }

    def _identify_sections_to_modify(self, sections: Dict[str, str], 
                                   missing_keywords: List[str], 
                                   improvements: List[Dict]) -> Dict[str, str]:
        """Identify which sections need modification"""
        sections_to_modify = {}
        
        # Create section-keyword mapping
        section_keywords = {
            'Experience': ['work', 'job', 'role', 'position', 'responsibility'],
            'Skills': ['skills', 'technologies', 'tools', 'languages'],
            'Projects': ['project', 'development', 'implementation'],
            'Education': ['education', 'degree', 'university'],
        }
        
        for section_name, section_content in sections.items():
            for keyword in missing_keywords:
                for section_type, indicators in section_keywords.items():
                    if any(indicator in section_name.lower() for indicator in indicators):
                        if section_name not in sections_to_modify:
                            sections_to_modify[section_name] = section_content
                        break
        
        return sections_to_modify

    def _modify_section(self, section_name: str, section_content: str, comparison_data: Dict) -> str:
        """Modify a single section with improvements"""
        prompt = PromptTemplate(
            template="""Modify this LaTeX resume section to incorporate relevant keywords and improvements.

            SECTION NAME: {section_name}
            
            ORIGINAL SECTION CONTENT:
            {section_content}

            KEYWORDS TO ADD:
            {keywords}

            IMPROVEMENTS TO MAKE:
            {improvements}

            INSTRUCTIONS:
            1. Keep the LaTeX formatting intact
            2. Add keywords naturally where they fit
            3. Apply relevant improvements
            4. Return only the modified section content
            5. Maintain all LaTeX environments and commands

            MODIFIED SECTION:""",
            input_variables=["section_name", "section_content", "keywords", "improvements"]
        )

        result = self.llm(prompt.format(
            section_name=section_name,
            section_content=section_content,
            keywords=", ".join(comparison_data.get('missing_keywords', [])),
            improvements="\n".join(f"- {imp['title']}" for imp in comparison_data.get('improvement_suggestions', []))
        ))

        return result.strip()

    def _reconstruct_latex_document(self, preamble: str, sections: Dict[str, str], ending: str) -> str:
        """Reconstruct the complete LaTeX document"""
        section_content = '\n\n'.join(sections.values())
        return f"{preamble}\n\n{section_content}\n\n{ending}"

def latex_to_pdf(tex_file: str):
    try:
        subprocess.run(['pdflatex', tex_file], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    st.title("ATS-Friendly Resume Optimizer")
    st.write("This tool helps optimize your resume for ATS systems by analyzing job descriptions and suggesting improvements.")

    # Create tabs for different stages
    setup_tab, analysis_tab, preview_tab, final_tab = st.tabs([
        "Setup", "Analysis", "Preview Changes", "Final Steps"
    ])

    with setup_tab:
        st.header("Initial Setup")
        api_key = st.text_input("Enter Gemini API Key:", type="password")
        
        if not api_key:
            st.warning("Please enter your Gemini API Key to continue.")
            return

        optimizer = ResumeOptimizer(api_key)
        uploaded_file = st.file_uploader("Upload your LaTeX Resume", type=['tex'])
        job_url = st.text_input("Enter Job Posting URL:")

    if uploaded_file and job_url:
        # Save uploaded file temporarily
        temp_resume_path = "temp_resume.tex"
        with open(temp_resume_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        try:
            # Read resume content
            resume_content = optimizer.read_latex_resume(temp_resume_path)

            with analysis_tab:
                st.header("Analysis Phase")
                
                with st.spinner("Analyzing job description..."):
                    job_content = optimizer.job_scraper.scrape_website(job_url)
                    jd_analysis = optimizer.job_scraper.analyze_job_description(job_content)
                    
                    st.subheader("Job Description Analysis")
                    st.write("Technical Skills:", ', '.join(jd_analysis.get('technical_skills', [])))
                    st.write("Soft Skills:", ', '.join(jd_analysis.get('soft_skills', [])))
                    
                    st.subheader("Keyword Rankings")
                    for keyword, score in jd_analysis.get('keyword_ranking', []):
                        if score > 5:
                            st.write(f"- {keyword}: {score}")

                with st.spinner("Comparing with your resume..."):
                    comparison = optimizer.analyze_resume_vs_jd(resume_content, jd_analysis)
                    
                    st.subheader("Resume Analysis")
                    st.write("Missing Important Keywords:", ", ".join(comparison.get("missing_keywords", [])))
                    st.write("Matching Keywords:", ", ".join(comparison.get("existing_keywords", [])))

            with preview_tab:
                st.header("Preview Changes")
                
                if 'jd_analysis' not in st.session_state:
                    st.session_state.jd_analysis = None
                
                if 'comparison' not in st.session_state:
                    st.session_state.comparison = None
                
                if st.button("Generate Preview"):
                    with st.spinner("Generating modified resume preview..."):
                        try:
                            # Store original content
                            if 'original_content' not in st.session_state:
                                st.session_state.original_content = resume_content
                            
                            # Use cached analysis if available
                            if st.session_state.jd_analysis is None:
                                st.session_state.jd_analysis = jd_analysis
                                st.session_state.comparison = comparison
                            
                            # Show suggested modifications
                            st.subheader("Suggested Modifications")
                            for section, mod_info in st.session_state.comparison.get("suggested_modifications", {}).items():
                                st.write(f"Section: {section}")
                                st.write(f"Content to add: {mod_info['content']}")
                                st.write(f"Location: {mod_info['location']}")
                                st.write("---")

                            # Generate modified content
                            company_name = job_url.split('//')[-1].split('/')[0].replace('.', '_')
                            modified_content = optimizer.modify_latex_resume(
                                st.session_state.original_content,
                                st.session_state.comparison["suggested_modifications"],
                                company_name
                            )
                            
                            if modified_content:
                                # Show diffs
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.subheader("Original Resume")
                                    st.text_area("Original LaTeX Code", st.session_state.original_content, height=400)
                                
                                with col2:
                                    st.subheader("Modified Resume")
                                    st.text_area("Modified LaTeX Code", modified_content, height=400)
                                
                                # Store the modified content
                                st.session_state.modified_content = modified_content
                                st.session_state.company_name = company_name
                            else:
                                st.error("Failed to generate modified resume")
                                
                        except Exception as e:
                            logging.error(f"Error in preview generation: {str(e)}")
                            st.error(f"Error generating preview: {str(e)}")

            with final_tab:
                st.header("Final Steps")
                if 'modified_content' in st.session_state:
                    if st.button("Apply Changes and Save"):
                        try:
                            new_resume_path = f"{st.session_state.company_name}_resume.tex"
                            
                            # Save modified resume
                            with open(new_resume_path, "w", encoding='utf-8') as f:
                                f.write(st.session_state.modified_content)

                            st.success(f"Modified resume saved as {new_resume_path}")

                            # PDF conversion option
                            if st.button("Convert to PDF"):
                                if latex_to_pdf(new_resume_path):
                                    pdf_path = new_resume_path.replace('.tex', '.pdf')
                                    st.success(f"PDF generated successfully: {pdf_path}")
                                else:
                                    st.error("Error generating PDF. Please ensure you have pdflatex installed.")
                        except Exception as e:
                            st.error(f"Error saving modifications: {str(e)}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            
        finally:
            # Cleanup
            if os.path.exists(temp_resume_path):
                os.remove(temp_resume_path)

if __name__ == "__main__":
    main() 