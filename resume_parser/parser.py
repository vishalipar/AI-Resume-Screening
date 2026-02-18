import re
import PyPDF2
import docx
from io import BytesIO

class ResumeParser:
    """Simple resume parser"""
    
    SKILLS_DATABASE = [
        'python', 'java', 'javascript', 'react', 'django', 'sql', 'aws',
        'docker', 'git', 'machine learning', 'data analysis', 'html', 'css'
    ]
    
    def extract_text_from_pdf(self, file_content):
        pdf_reader = PyPDF2.PdfReader(file_content)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def extract_text_from_docx(self, file_content):
        doc = docx.Document(file_content)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    def extract_name(self, text):
        # Simple: take first line
        lines = text.strip().split('\n')
        return lines[0].strip() if lines else "Unknown"
    
    def extract_email(self, text):
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""
    
    def extract_phone(self, text):
        phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
        matches = re.findall(phone_pattern, text)
        for match in matches:
            digits = re.sub(r'\D', '', match)
            if len(digits) >= 10:
                return match
        return ""
    
    def extract_skills(self, text):
        text_lower = text.lower()
        found_skills = []
        for skill in self.SKILLS_DATABASE:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills
    
    def parse_resume(self, file_obj, filename):
        """Main parsing function"""
        file_extension = filename.split('.')[-1].lower()
        file_content = BytesIO(file_obj.read())
        
        if file_extension == 'pdf':
            text = self.extract_text_from_pdf(file_content)
        elif file_extension in ['doc', 'docx']:
            text = self.extract_text_from_docx(file_content)
        else:
            return {'error': 'Unsupported file type'}
        
        return {
            'name': self.extract_name(text),
            'email': self.extract_email(text),
            'phone': self.extract_phone(text),
            'skills': self.extract_skills(text),
            'resume_text': text,
            'success': True
        }