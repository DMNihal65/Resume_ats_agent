import streamlit as st
from pathlib import Path
import os
from typing import Dict, List
import json
from langchain_google_genai import GoogleGenerativeAI
from langchain.agents import Tool, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from resume import EnhancedJobScraper
import subprocess

class ResumeOptimizer:
    def __init__(self, gemini_api_key: str):
        self.setup_llm(gemini_api_key)
        self.job_scraper = EnhancedJobScraper(gemini_api_key)
        self.setup_output_parsers()

    def setup_llm(self, api_key: str):
        self.llm = GoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.2,
            max_output_tokens=2000
        )

    def setup_output_parsers(self):
        resume_analysis_schemas = [
            ResponseSchema(name="missing_keywords", type="List[str]", 
                         description="Keywords from job description missing in resume"),
            ResponseSchema(name="existing_keywords", type="List[str]", 
                         description="Keywords present in both resume and job description"),
            ResponseSchema(name="suggested_modifications", type="Dict", 
                         description="Suggested modifications for each section")
        ]
        self.resume_parser = StructuredOutputParser.from_response_schemas(resume_analysis_schemas)

    def read_latex_resume(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def analyze_resume_vs_jd(self, resume_text: str, jd_analysis: Dict) -> Dict:
        format_instructions = self.resume_parser.get_format_instructions()
        
        prompt = PromptTemplate(
            template="""Compare this resume with the job description analysis and suggest improvements:

            Resume LaTeX Content:
            {resume_text}

            Job Description Analysis:
            {jd_analysis}

            {format_instructions}

            Focus on:
            1. Missing important keywords (score > 5)
            2. Existing matching keywords
            3. Suggested modifications for each section

            Return the analysis in the specified JSON format.""",
            input_variables=["resume_text", "jd_analysis"],
            partial_variables={"format_instructions": format_instructions}
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.invoke({
            "resume_text": resume_text,
            "jd_analysis": json.dumps(jd_analysis, indent=2)
        })
        return self.resume_parser.parse(result['text'])

    def modify_latex_resume(self, resume_text: str, modifications: Dict, company_name: str) -> str:
        # First, analyze the LaTeX structure
        structure_prompt = PromptTemplate(
            template="""Analyze this LaTeX resume structure and identify the main sections:

            {resume_text}

            Return only the section names and their corresponding environments.""",
            input_variables=["resume_text"]
        )
        
        structure_chain = LLMChain(llm=self.llm, prompt=structure_prompt)
        sections = structure_chain.invoke({"resume_text": resume_text})

        # Now create the modification prompt
        modify_prompt = PromptTemplate(
            template="""You are a LaTeX expert. Modify this resume carefully following these rules:

            STRICT RULES:
            1. DO NOT remove or change ANY existing LaTeX commands or structure
            2. Only ADD or MODIFY content within existing sections
            3. Keep all LaTeX syntax (\begin{}, \end{}, etc.) exactly as is
            4. Only modify content between LaTeX commands
            5. Return the COMPLETE LaTeX document

            Original LaTeX Resume:
            ```latex
            {resume_text}
            ```

            Sections Identified:
            {sections}
            
            Requested Modifications:
            {modifications}
            
            Instructions:
            1. For each modification, find the matching section
            2. Add keywords and content WITHIN existing sections
            3. Preserve ALL LaTeX formatting and commands
            4. Return the complete modified LaTeX code

            IMPORTANT: Ensure every LaTeX command and environment remains intact.""",
            input_variables=["resume_text", "sections", "modifications"]
        )

        modify_chain = LLMChain(llm=self.llm, prompt=modify_prompt)
        result = modify_chain.invoke({
            "resume_text": resume_text,
            "sections": sections['text'],
            "modifications": json.dumps(modifications, indent=2)
        })

        # Validate the modified content
        validate_prompt = PromptTemplate(
            template="""Verify this modified LaTeX code maintains proper structure:
            
            {modified_text}
            
            Check:
            1. All \begin{} have matching \end{}
            2. All LaTeX commands are preserved
            3. Only content is modified, not structure
            
            If valid, return the code. If invalid, fix and return corrected code.""",
            input_variables=["modified_text"]
        )

        validate_chain = LLMChain(llm=self.llm, prompt=validate_prompt)
        validated_result = validate_chain.invoke({"modified_text": result['text']})

        return validated_result['text']

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
                st.subheader("Suggested Modifications")
                st.json(comparison.get("suggested_modifications", {}))

                if st.button("Generate Preview"):
                    with st.spinner("Generating modified resume preview..."):
                        company_name = job_url.split('//')[-1].split('/')[0].replace('.', '_')
                        
                        try:
                            modified_content = optimizer.modify_latex_resume(
                                resume_content, 
                                comparison["suggested_modifications"],
                                company_name
                            )
                            
                            # Show diffs between original and modified
                            st.subheader("Original Resume")
                            st.text_area("Original LaTeX Code", resume_content, height=200)
                            
                            st.subheader("Modified Resume")
                            st.text_area("Modified LaTeX Code", modified_content, height=200)
                            
                            # Store the modified content in session state
                            st.session_state.modified_content = modified_content
                            st.session_state.company_name = company_name
                            
                        except Exception as e:
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