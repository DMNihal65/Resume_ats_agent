from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from collections import Counter
import time
import re
from typing import Dict, List

# Import required LangChain components
from langchain_google_genai import GoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class JobScraper:
    def __init__(self, gemini_api_key: str):
        self.setup_chrome_options()
        self.setup_llm(gemini_api_key)
        
    def setup_chrome_options(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--window-size=1920,1080")
        # Add additional options for better dynamic content handling
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--enable-javascript")
        
    def setup_llm(self, api_key: str):
        self.llm = GoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.3
        )
        
    def scrape_website(self, url: str) -> str:
        driver = webdriver.Chrome(options=self.chrome_options)
        try:
            print(f"Opening URL: {url}")
            driver.get(url)
            
            # Wait for the body to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll down the page to trigger lazy loading
            self.scroll_page(driver)
            
            # Wait for dynamic content
            time.sleep(3)
            
            # Get the final HTML
            html = driver.page_source
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            html = ""
            
        finally:
            driver.quit()
            
        return self.parse_html(html)
    
    def scroll_page(self, driver):
        # Scroll slowly down the page to trigger lazy loading
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def parse_html(self, html: str) -> str:
        if not html:
            return ""
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove unnecessary elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer']):
            element.decompose()
            
        # Get text content
        content = soup.get_text(separator="\n", strip=True)
        return content
    
    def analyze_job_description(self, text: str) -> Dict:
        # Split text into chunks if it's too long
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_text(text)
        
        # Create prompt template for job analysis
        prompt_template = """
        Analyze the following job description text and extract:
        1. Required skills
        2. Years of experience required
        3. Education requirements
        4. Key responsibilities
        5. Any important keywords that appear multiple times
        
        Text: {text}
        
        Provide the analysis in a structured format.
        """
        
        prompt = PromptTemplate(
            input_variables=["text"],
            template=prompt_template
        )
        
        # Create and run the chain
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        # Process each chunk and combine results
        all_results = []
        for chunk in chunks:
            result = chain.invoke({"text": chunk})
            all_results.append(result['text'])
        
        # Extract frequently mentioned skills
        skills = self.extract_skills(text)
        
        return {
            "llm_analysis": "\n".join(all_results),
            "frequent_skills": skills
        }
    
    def extract_skills(self, text: str) -> List[str]:
        # Common technical skills and keywords to look for
        skill_patterns = [
            r'python|java|javascript|react|node\.js|sql|aws|docker|kubernetes|git',
            r'machine learning|artificial intelligence|data science|deep learning',
            r'agile|scrum|devops|ci/cd|testing|debugging',
            # Add more patterns as needed
        ]
        
        # Find all matches
        all_skills = []
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text.lower())
            all_skills.extend([match.group() for match in matches])
        
        # Count frequencies
        skill_counts = Counter(all_skills)
        
        # Return skills mentioned more than twice
        frequent_skills = [skill for skill, count in skill_counts.items() if count >= 2]
        return frequent_skills

def main():
    # Replace with your Gemini API key
    GEMINI_API_KEY = "AIzaSyCkb4a_yq_Iviefm_FJHQr40ukm7BqlLww"
    
    scraper = JobScraper(GEMINI_API_KEY)
    
    url = input("Enter the job posting URL: ").strip()
    if not url:
        print("No URL provided.")
        return
    
    # Scrape the website
    print("Scraping website...")
    content = scraper.scrape_website(url)
    
    if not content:
        print("No content found.")
        return
    
    # Analyze the job description
    print("\nAnalyzing job description...")
    analysis = scraper.analyze_job_description(content)
    
    # Print results
    print("\nAnalysis Results:")
    print("-" * 50)
    print(analysis['llm_analysis'])
    
    print("\nFrequently Mentioned Skills:")
    print("-" * 50)
    for skill in analysis['frequent_skills']:
        print(f"- {skill}")

if __name__ == "__main__":
    main()