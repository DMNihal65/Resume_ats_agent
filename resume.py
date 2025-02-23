from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from collections import Counter
import re
import time
import json
from typing import Dict, List, Tuple

# LangChain components
from langchain_google_genai import GoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

class EnhancedJobScraper:
    def __init__(self, gemini_api_key: str):
        self.setup_chrome_options()
        self.setup_llm(gemini_api_key)
        self.setup_output_parsers()
        
    def setup_chrome_options(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--enable-javascript")
        self.chrome_options.page_load_strategy = 'eager'
        
    def setup_llm(self, api_key: str):
        self.llm = GoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.2,
            max_output_tokens=2000
        )
        
    def setup_output_parsers(self):
        response_schemas = [
            ResponseSchema(name="technical_skills", type="List[str]", description="Technical skills required"),
            ResponseSchema(name="soft_skills", type="List[str]", description="Soft skills required"),
            ResponseSchema(name="certifications", type="List[str]", description="Required certifications"),
            ResponseSchema(name="experience", type="str", description="Years of experience required"),
            ResponseSchema(name="education", type="List[str]", description="Education requirements"),
            ResponseSchema(name="keywords", type="List[str]", description="Important keywords from the job description")
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        
    def scrape_website(self, url: str) -> str:
        driver = webdriver.Chrome(options=self.chrome_options)
        try:
            print(f"Opening URL: {url}")
            driver.get(url)
            
            # Wait for job description content specifically
            WebDriverWait(driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".description__text")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-description-content")),
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
            )
            
            # Enhanced scrolling with dynamic wait
            self.scroll_page(driver)
            
            # Wait for text content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'experience') or contains(text(), 'skills')]"))
            )
            
            return self.clean_html(driver.page_source)
            
        except Exception as e:
            print(f"Scraping error: {e}")
            return ""
        finally:
            driver.quit()
    
    def scroll_page(self, driver):
        scroll_pause = 0.5
        current_height = 0
        max_scroll_attempts = 5
        
        for _ in range(max_scroll_attempts):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            new_height = driver.execute_script("return window.pageYOffset")
            if new_height == current_height:
                break
            current_height = new_height
    
    def clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for tag in ['script', 'style', 'meta', 'link', 'button', 'svg', 'img']:
            for element in soup.find_all(tag):
                element.decompose()
                
        # Focus on job description containers
        content = soup.find('div', class_=re.compile(r'description|content|body', re.I)) or soup.body
        return content.get_text(separator='\n', strip=True) if content else ''
    
    def analyze_job_description(self, text: str) -> Dict:
        cleaned_text = self.clean_text_with_llm(text)
        structured_analysis = self.get_structured_analysis(cleaned_text)
        keyword_analysis = self.analyze_keywords(cleaned_text)
        
        return {
            **structured_analysis,
            "keyword_ranking": keyword_analysis
        }
    
    def clean_text_with_llm(self, text: str) -> str:
        prompt = PromptTemplate(
            template="""Clean this job description text. Remove:
            - Company marketing content
            - Navigation instructions
            - Irrelevant sections
            Keep only job requirements and qualifications.
            Return ONLY the cleaned text without any formatting.\n\n{text}""",
            input_variables=["text"]
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.invoke({"text": text})['text']
    
    def get_structured_analysis(self, text: str) -> Dict:
        format_instructions = self.output_parser.get_format_instructions()
        
        prompt = PromptTemplate(
            template="""Analyze this job description for ATS optimization. Extract exactly:
            {format_instructions}
            
            Return ONLY JSON, no other text. Job Description:
            {text}""",
            input_variables=["text"],
            partial_variables={"format_instructions": format_instructions}
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.invoke({"text": text})
        return self.output_parser.parse(result['text'])
    
    def analyze_keywords(self, text: str) -> List[Tuple[str, int]]:
        prompt = PromptTemplate(
            template="""Identify ATS keywords from this job description. Return STRICTLY as:
            ```json
            {{"keywords": [["keyword", importance_score]]}}
            ```
            Scores 1-10 (10=most important). Consider:
            - Frequency
            - Position in text
            - Industry importance
            
            Text: {text}""",
            input_variables=["text"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.invoke({"text": text})['text']
        
        try:
            # Extract JSON from markdown code block
            json_str = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL).group(1)
            result = json.loads(json_str)
        except (AttributeError, json.JSONDecodeError) as e:
            print(f"JSON parsing error: {e}")
            return []
            
        # Enhance with frequency analysis
        word_counts = Counter(re.findall(r'\b[a-z]{4,}\b', text.lower()))
        enhanced_keywords = []
        
        for keyword, score in result.get('keywords', []):
            freq = word_counts.get(keyword.lower(), 0)
            enhanced_score = min(10, (score * 0.7) + (freq * 0.3))
            enhanced_keywords.append((keyword.title(), enhanced_score))
            
        return sorted(enhanced_keywords, key=lambda x: x[1], reverse=True)[:20]

def main():
    GEMINI_API_KEY = "AIzaSyCkb4a_yq_Iviefm_FJHQr40ukm7BqlLww"
    
    scraper = EnhancedJobScraper(GEMINI_API_KEY)
    
    url = input("Enter job posting URL: ").strip()
    if not url.startswith(('http://', 'https://')):
        print("Invalid URL format")
        return
    
    print("Scraping and analyzing...")
    content = scraper.scrape_website(url)
    
    if not content:
        print("Failed to extract content")
        return
    
    try:
        analysis = scraper.analyze_job_description(content)
        
        print("\nATS Optimization Report:")
        print("="*50)
        print("\nTechnical Skills:", ', '.join(analysis.get('technical_skills', [])))
        print("\nSoft Skills:", ', '.join(analysis.get('soft_skills', [])))
        print("\nCertifications:", ', '.join(analysis.get('certifications', [])))
        print("\nExperience Required:", analysis.get('experience', 'Not specified'))
        print("\nEducation:", ', '.join(analysis.get('education', [])))
        
        print("\nTop 20 ATS Keywords:")
        for keyword, score in analysis.get('keyword_ranking', []):
            print(f"{keyword}: {score:.1f}")
            
    except Exception as e:
        print(f"Analysis error: {e}")

if __name__ == "__main__":
    main()