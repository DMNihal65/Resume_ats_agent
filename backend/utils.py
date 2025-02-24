def validate_latex_content(content: str) -> bool:
    """Validate LaTeX content structure with more flexible rules"""
    try:
        content = content.strip()
        
        # Basic checks for common LaTeX elements
        basic_elements = [
            "\\documentclass",
            "\\begin{document}",
            "\\end{document}"
        ]
        
        # Convert content to lowercase for case-insensitive checking
        content_lower = content.lower()
        
        # Check if content starts with documentclass (allowing spaces and comments)
        lines = content.split('\n')
        found_documentclass = False
        for line in lines:
            line = line.strip()
            if line.startswith('%'):  # Skip comment lines
                continue
            if line.startswith('\\documentclass'):
                found_documentclass = True
                break
            if line and not line.startswith('%'):  # Found non-empty, non-comment line before documentclass
                return False
        
        if not found_documentclass:
            return False
        
        # Check for document environment
        if "\\begin{document}" not in content and "\\begin {document}" not in content:
            return False
        if "\\end{document}" not in content and "\\end {document}" not in content:
            return False
            
        # Count balanced environments
        begin_count = sum(1 for line in lines if '\\begin{' in line and not line.strip().startswith('%'))
        end_count = sum(1 for line in lines if '\\end{' in line and not line.strip().startswith('%'))
        
        if begin_count != end_count:
            return False
            
        return True
        
    except Exception as e:
        print(f"Error validating LaTeX: {str(e)}")
        return False 

def clean_latex_content(content: str) -> str:
    """Clean and normalize LaTeX content"""
    # Remove BOM if present
    content = content.strip('\ufeff')
    
    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove trailing whitespace from lines while preserving empty lines
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    
    # Ensure proper ending
    if not content.endswith('\n'):
        content += '\n'
    
    return '\n'.join(lines) 