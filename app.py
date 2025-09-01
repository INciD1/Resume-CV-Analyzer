import os
import re
import pandas as pd
import numpy as np
import pdfplumber
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import shutil
import uuid
import json
import base64
from io import BytesIO

# ดาวน์โหลด NLTK data ที่จำเป็น
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# กำหนดค่าคงที่
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

# สร้าง Flask app
app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # จำกัดขนาดไฟล์: 16MB
app.secret_key = 'resume_analyzer_secret_key'

# สร้างโฟลเดอร์ถ้ายังไม่มี
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# นิยาม job descriptions สำหรับแต่ละประเภท
JOB_DESCRIPTIONS = {
    "business_development": """
    Job Title: Business Development Manager
    
    Requirements:
    - Bachelor's degree in Business Administration, Marketing, or related field
    - 3+ years of experience in business development, sales, or related roles
    - Strong communication and negotiation skills
    - Ability to identify and develop new business opportunities
    - Experience in market research and strategy development
    - Proficiency in CRM software
    - Knowledge of project management
    - Excellent presentation skills
    - Problem-solving and analytical abilities
    
    Responsibilities:
    - Develop and implement business development strategies
    - Identify and pursue new business opportunities
    - Build and maintain relationships with key clients and partners
    - Prepare and deliver presentations to potential clients
    - Conduct market research and competitive analysis
    - Collaborate with marketing and sales teams
    - Prepare reports on business development activities
    - Negotiate and close deals
    """,
    
    "designer": """
    Job Title: Designer
    
    Requirements:
    - Bachelor's degree in Design, Visual Arts, or related field
    - 2+ years of experience in design
    - Proficiency in design tools such as Figma, Sketch, Adobe Creative Suite
    - Strong portfolio demonstrating creative design solutions
    - Knowledge of design principles and visual communication
    - Experience with typography, color theory, and layout design
    - Understanding of branding and identity design
    - Basic knowledge of HTML and CSS
    - Excellent visual design skills
    
    Responsibilities:
    - Create visual designs for print and digital media
    - Develop brand identity elements and style guides
    - Design marketing materials and promotional content
    - Collaborate with marketing teams and clients
    - Create visual assets for websites and social media
    - Ensure design consistency across all materials
    - Present and defend design decisions
    - Stay updated on latest design trends and technologies
    """,
    
    "digital_media": """
    Job Title: Digital Media Specialist
    
    Requirements:
    - Bachelor's degree in Marketing, Communications, or related field
    - 2+ years of experience in digital media management
    - Proficiency in social media platforms and analytics tools
    - Experience with content creation and management
    - Knowledge of SEO and SEM principles
    - Familiarity with graphic design tools (e.g., Adobe Creative Suite)
    - Understanding of digital advertising platforms
    - Excellent writing and editing skills
    - Analytical mindset with attention to detail
    
    Responsibilities:
    - Develop and implement digital media strategies
    - Create and manage content for social media platforms
    - Monitor and analyze performance metrics of digital campaigns
    - Optimize content for SEO and user engagement
    - Manage paid digital advertising campaigns
    - Collaborate with marketing and creative teams
    - Stay updated on digital media trends and best practices
    - Report on digital media performance and ROI
    """,
    
    "engineering": """
    Job Title: Electrical Engineer
    
    Requirements:
    - Bachelor's degree in Electrical Engineering or related field
    - 3+ years of experience in electrical engineering
    - Proficiency in circuit design and analysis
    - Experience with electrical systems and power distribution
    - Knowledge of electrical codes and safety standards
    - Understanding of AutoCAD and simulation software
    - Familiarity with testing and measurement equipment
    - Experience with PCB design and prototyping
    - Problem-solving and analytical thinking skills
    
    Responsibilities:
    - Design and develop electrical systems and components
    - Create technical drawings and specifications
    - Test and evaluate electrical equipment
    - Troubleshoot electrical problems and implement solutions
    - Ensure compliance with safety standards and regulations
    - Collaborate with cross-functional engineering teams
    - Document technical specifications and processes
    - Stay updated on emerging technologies and trends
    """,
    
    "information_technology": """
    Job Title: IT Systems Administrator
    
    Requirements:
    - Bachelor's degree in Information Technology, Computer Science, or related field
    - 3+ years of experience in IT systems administration
    - Knowledge of network infrastructure and security
    - Experience with Windows and Linux operating systems
    - Familiarity with virtualization technologies
    - Understanding of backup and disaster recovery procedures
    - Knowledge of IT service management frameworks
    - Certification in relevant technologies (e.g., MCSA, CCNA)
    - Problem-solving and analytical skills
    
    Responsibilities:
    - Install, configure, and maintain IT systems and infrastructure
    - Monitor system performance and troubleshoot issues
    - Implement security measures and ensure data protection
    - Manage user accounts and access privileges
    - Perform regular backups and recovery tests
    - Update systems with patches and upgrades
    - Document IT procedures and policies
    - Provide technical support to end-users
    """,
    
    "sales": """
    Job Title: Sales Representative
    
    Requirements:
    - Bachelor's degree in Business, Marketing, or related field
    - 2+ years of experience in sales or customer service
    - Strong communication and interpersonal skills
    - Ability to understand customer needs and provide solutions
    - Experience with CRM software
    - Goal-oriented mindset and self-motivation
    - Time management and organizational skills
    - Basic knowledge of sales analytics
    - Negotiation and persuasion abilities
    
    Responsibilities:
    - Generate leads and identify sales opportunities
    - Build and maintain relationships with customers
    - Understand customer requirements and recommend appropriate products/services
    - Meet or exceed sales targets
    - Prepare and deliver sales presentations
    - Negotiate contracts and close deals
    - Maintain records of sales activities in CRM system
    - Collaborate with marketing and product teams
    """
}

class ResumeAnalyzer:
    def __init__(self):
        # กำหนดรายการทักษะที่ต้องการค้นหา
        self.skills_list = [
            # ทักษะทั่วไป
            "leadership", "communication", "teamwork", "problem solving", "project management", 
            "critical thinking", "time management", "decision making", "creativity", "presentation",
            
            # ทักษะด้านธุรกิจ
            "business development", "sales", "marketing", "crm", "market research", "strategy", 
            "negotiation", "client relationship", "business analysis", "account management",
            "financial planning", "budget management", "revenue forecasting", "business strategy",
            "risk assessment", "stakeholder management", "contract management", "business modeling",
            "competitive analysis", "market segmentation", "business operations", "venture capital",
            "mergers and acquisitions", "business valuation", "product development", "strategic partnerships",
    
            
            # ทักษะด้านดีไซน์
            "ui design", "ux design", "graphic design", "figma", "sketch", "adobe photoshop", 
            "adobe illustrator", "adobe xd", "typography", "wireframing", "prototyping",
            "branding", "visual design", "layout design", "color theory", "print design",
            
            # ทักษะด้านดิจิทัลมีเดีย
            "content creation", "social media", "seo", "sem", "digital marketing", "google analytics", 
            "content management", "blogging", "copywriting", "facebook ads", "google ads",
            "email marketing", "influencer marketing", "social media analytics", "content strategy",
            "video production", "podcast production", "digital storytelling", "user engagement",
            "conversion rate optimization", "marketing automation", "affiliate marketing", "mobile marketing",
            "tiktok marketing", "instagram marketing", "youtube optimization", "digital pr",

            # ทักษะด้านวิศวกรรมไฟฟ้า
            "circuit design", "electrical systems", "power distribution", "autocad", "pcb design",
            "electrical testing", "electrical codes", "power systems", "control systems", "simulation",
            "signal processing", "microcontrollers", "embedded systems", "power electronics", 
            "analog circuits", "digital circuits", "instrumentation", "FPGA", "PLC programming",
            "electronic troubleshooting", "schematic design", "high voltage systems", "electrical protection",
            "renewable energy systems", "electromagnetic compatibility", "sensor interfacing",
            
            # ทักษะด้านไอที
            "network administration", "system administration", "Windows Server", "linux", "Virtual Server", 
            "virtualization", "database management", "IT support", "troubleshooting","python", 
            "java", "javascript", "C++", "C#", "data structures", "Algorithms", "software development", "database design", 
            "McAfee Product/McAfee SIEM/EPO/NSM", "testing", "User Training/Support", "Data Security/Quality", 
            "Systems Implementation", "Process Improvement", "eClinicalWorks", "Microsoft System Center Configuration Manager", 
            "IT infrastructure", "Server 2003, Server 2008 R2", "Microsoft Office (2007, 2013)", 
            "Hardware/Software Troubleshooting,Network System Maintenance", "IT Staff Training",

            # ทักษะด้านการขาย (Sales)
            "lead generation", "cold calling", "sales prospecting", "sales closing", "upselling", 
            "cross-selling", "sales funnel management", "sales forecasting", "customer acquisition", 
            "sales presentation", "consultative selling", "relationship selling", "solution selling", 
            "territory management", "quota achievement", "sales pipeline", "b2b sales", "b2c sales", 
            "inside sales", "outside sales", "enterprise sales", "sales analytics", "sales automation",
            "customer retention", "contract negotiation", "customer success"
        ]
        
        # รายการคำที่ไม่ต้องการ
        self.stop_words = set(stopwords.words('english'))
        # ตัวแยกคำ
        self.word_tokenizer = nltk.tokenize.WordPunctTokenizer()
        # ตัวแปรเก็บข้อมูลผู้สมัคร
        self.candidates = []
    
    def extract_text_from_pdf(self, pdf_path):
        """อ่านข้อความจากไฟล์ PDF"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการอ่าน PDF: {e}")
        return text
    
    def extract_text_from_image(self, image_path):
        try:
            import requests
        
            # ใช้ API key จาก http://ocr.space/
            api_key = 'K81172011688957' 
        
            with open(image_path, 'rb') as f:
                payload = {'apikey': api_key, 'language': 'eng'}
                files = {'file': f}
                r = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
                result = r.json()
            
                if result['IsErroredOnProcessing'] == False:
                    return result['ParsedResults'][0]['ParsedText']
                else:
                    print(f"OCR API Error: {result['ErrorMessage']}")
                    return ""
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการอ่านรูปภาพ: {e}")
            return ""
    
    def clean_text(self, text):
        """ทำความสะอาดข้อความ"""
        if not text:
            return ""
        
        # แปลงเป็นตัวพิมพ์เล็ก
        text = text.lower()
        # ลบอักขระพิเศษ
        text = re.sub(r'[^\w\s]', ' ', text)
        # ลบช่องว่างซ้ำ
        text = re.sub(r'\s+', ' ', text)
        # ลบเลขหน้า
        text = re.sub(r'\d+\s*/\s*\d+', '', text)
        
        return text.strip()
    
    def extract_name(self, text):
        """สกัดชื่อจากข้อความ"""
        # ใช้วิธีง่ายๆ โดยสมมติว่าชื่อจะอยู่ในบรรทัดแรกๆ
        lines = text.split('\n')
        for line in lines[:5]:  # ดูแค่ 5 บรรทัดแรก
            # ตัดช่องว่างและคำที่ไม่จำเป็น
            line = line.strip()
            if len(line) > 0 and len(line.split()) <= 4 and not re.search(r'@|resume|cv', line.lower()):
                return line
        return "Unknown"
    
    def extract_email(self, text):
        """สกัดอีเมลจากข้อความ"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        if match:
            return match.group()
        return "No email found"
    
    def extract_skills(self, text):
        """สกัดทักษะจากข้อความ"""
        skills = []
        for skill in self.skills_list:
            if re.search(r'\b' + re.escape(skill) + r'\b', text.lower()):
                skills.append(skill)
        return skills
    
    def process_resume(self, file_path):
        filename = os.path.basename(file_path)
        file_ext = filename.rsplit('.', 1)[1].lower()
    
        # อ่านข้อความตามประเภทไฟล์
        if file_ext == 'pdf':
            raw_text = self.extract_text_from_pdf(file_path)
        elif file_ext in ['jpg', 'jpeg', 'png']:
            raw_text = self.extract_text_from_image(file_path)
        else:
            print(f"ไม่รองรับนามสกุลไฟล์: {file_ext}")
            return None
    
        if not raw_text:
            print(f"ไม่สามารถอ่านข้อความจาก {filename}")
            return None
    
        clean_text = self.clean_text(raw_text)
        name = self.extract_name(raw_text)
        email = self.extract_email(raw_text)
        skills = self.extract_skills(clean_text)
    
        candidate = {
            'filename': filename,
            'name': name,
            'email': email,
            'skills': skills,
            'skill_count': len(skills),
            'text': clean_text,
            'raw_text': raw_text
        }
    
        return candidate
    
    def process_resumes_from_directory(self, directory_path):
        self.candidates = []
    
        for filename in os.listdir(directory_path):
            if any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                file_path = os.path.join(directory_path, filename)
                candidate = self.process_resume(file_path)
                if candidate:
                    self.candidates.append(candidate)
    
        print(f"ประมวลผลเรซูเม่ทั้งหมด {len(self.candidates)} ไฟล์")
        return self.candidates
    
    def calculate_similarity(self, job_description):
        """คำนวณความเหมือนระหว่างเรซูเม่กับคำอธิบายงาน"""
        if not self.candidates:
            print("ไม่มีข้อมูลผู้สมัคร โปรดประมวลผลเรซูเม่ก่อน")
            return []
        
        # ทำความสะอาดคำอธิบายงาน
        clean_jd = self.clean_text(job_description)
        
        # สร้าง TF-IDF Vectorizer
        vectorizer = TfidfVectorizer(stop_words=list(self.stop_words))
        
        # รวมข้อความทั้งหมด (เรซูเม่ + คำอธิบายงาน)
        documents = [candidate['text'] for candidate in self.candidates] + [clean_jd]
        
        # แปลงข้อความเป็นเวกเตอร์ TF-IDF
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        # คำนวณความเหมือน (Cosine Similarity)
        cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
        
        # ตรวจสอบทักษะที่ตรงกับคำอธิบายงาน
        jd_skills = self.extract_skills(clean_jd)
        
        # คำนวณคะแนนทักษะที่ตรงกัน
        skill_scores = []
        for candidate in self.candidates:
            matching_skills = set(candidate['skills']).intersection(set(jd_skills))
            skill_score = len(matching_skills) / len(jd_skills) if jd_skills else 0
            skill_scores.append({
                'candidate': candidate,
                'matching_skills': list(matching_skills),
                'skill_score': skill_score,
                'cosine_similarity': float(cosine_similarities[self.candidates.index(candidate)])
            })
        
        # คำนวณคะแนนรวม (น้ำหนัก: 60% สำหรับทักษะ, 40% สำหรับความเหมือน)
        for score in skill_scores:
            score['total_score'] = (0.6 * score['skill_score']) + (0.4 * score['cosine_similarity'])
        
        # เรียงลำดับตามคะแนนรวม
        skill_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        return skill_scores
    
    def generate_visualizations(self, results, job_description, session_id):
        if not results:
            print("ไม่มีผลลัพธ์ที่จะแสดง")
            return {}
    
        visualization_data = {}
    
        # เตรียมข้อมูลสำหรับกราฟแท่ง
        names = [r['candidate']['name'] for r in results]
        skill_scores = [r['skill_score'] for r in results]
        similarity_scores = [r['cosine_similarity'] for r in results]
        total_scores = [r['total_score'] for r in results]
    
        visualization_data['bar_chart'] = {
            'labels': names,
            'datasets': [
                {'label': 'ทักษะ', 'data': skill_scores},
                {'label': 'เนื้อหา', 'data': similarity_scores},
                {'label': 'รวม', 'data': total_scores}
            ]
        }
    
        # เตรียมข้อมูลสำหรับ Heatmap
        jd_skills = self.extract_skills(self.clean_text(job_description))
        if jd_skills:
            all_skills = sorted(list(set(jd_skills)))
        
            if len(names) > 0 and len(all_skills) > 0:
                # สร้างเมทริกซ์ทักษะ
                skill_matrix = []
                for result in results:
                    candidate_skills = result['candidate']['skills']
                    row = []
                    for skill in all_skills:
                        row.append(1 if skill in candidate_skills else 0)
                    skill_matrix.append(row)
            
                visualization_data['heatmap'] = {
                    'labels': {
                        'x': all_skills,
                        'y': names
                    },
                    'data': skill_matrix
                }
    
        return visualization_data

def allowed_file(filename):
    """ตรวจสอบนามสกุลไฟล์ที่อนุญาต"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """หน้าแรก"""
    return render_template('index.html', job_categories=list(JOB_DESCRIPTIONS.keys()))

@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    """รับไฟล์และประมวลผล"""
    # ถ้าเป็น GET request ให้ redirect กลับไปที่หน้าแรก
    if request.method == 'GET':
        flash('กรุณาอัพโหลดไฟล์ผ่านหน้าแรก', 'warning')
        return redirect(url_for('index'))
    
    # ส่วนของ POST request (โค้ดเดิมที่มีอยู่แล้ว)
    if 'files[]' not in request.files:
        flash('ไม่พบไฟล์', 'error')
        return redirect(request.url)
    
    files = request.files.getlist('files[]')
    
    if not files or files[0].filename == '':
        flash('ไม่ได้เลือกไฟล์', 'error')
        return redirect(request.url)
    
    job_category = request.form.get('job_category')
    if job_category not in JOB_DESCRIPTIONS:
        flash('หมวดหมู่งานไม่ถูกต้อง', 'error')
        return redirect(request.url)
    
    # สร้าง session ID สำหรับการวิเคราะห์นี้
    session_id = str(uuid.uuid4())
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    # บันทึกไฟล์
    filenames = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            filenames.append(filename)
    
    if not filenames:
        flash('ไม่มีไฟล์ที่ถูกต้อง', 'error')
        return redirect(request.url)
    
    # ประมวลผลเรซูเม่
    analyzer = ResumeAnalyzer()
    analyzer.process_resumes_from_directory(upload_dir)
    
    if not analyzer.candidates:
        flash('ไม่สามารถวิเคราะห์เรซูเม่ได้', 'error')
        shutil.rmtree(upload_dir)
        return redirect(request.url)
    
    # วิเคราะห์เรซูเม่
    job_description = JOB_DESCRIPTIONS[job_category]
    results = analyzer.calculate_similarity(job_description)
    
    # สร้างการแสดงผลภาพ
    visualization_files = analyzer.generate_visualizations(results, job_description, session_id)
    
    # เตรียมข้อมูลสำหรับแสดงผล
    candidates_data = []
    for i, result in enumerate(results):
        candidate = result['candidate']
        candidates_data.append({
            'rank': i + 1,
            'name': candidate['name'],
            'email': candidate['email'],
            'matching_skills': result['matching_skills'],
            'skill_score': round(result['skill_score'] * 100, 2),
            'content_similarity': round(result['cosine_similarity'] * 100, 2),
            'total_score': round(result['total_score'] * 100, 2)
        })
    
    # บันทึกผลลัพธ์ลงไฟล์
    result_data = {
        'job_category': job_category,
        'candidates': candidates_data,
        'visualization_data': visualization_files
    }
    
    result_file = os.path.join(app.config['RESULTS_FOLDER'], f'{session_id}_results.json')
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=4)
        print(f"บันทึกไฟล์ JSON สำเร็จที่: {result_file}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการบันทึกไฟล์ JSON: {e}")
    
    return redirect(url_for('results', session_id=session_id))

@app.route('/results/<session_id>')
def results(session_id):
    result_file = os.path.join(app.config['RESULTS_FOLDER'], f'{session_id}_results.json')
    
    if not os.path.exists(result_file):
        flash('ไม่พบข้อมูลผลลัพธ์', 'error')
        return redirect(url_for('index'))
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        job_category = result_data['job_category']
        job_title = JOB_DESCRIPTIONS[job_category].split('\n')[1].strip()
        
        # เตรียมข้อมูลสำหรับกราฟแท่ง
        bar_chart_data = None
        heatmap_data = None
        
        if 'visualization_data' in result_data and result_data['visualization_data']:
            viz_data = result_data['visualization_data']
            if 'bar_chart' in viz_data:
                bar_chart_data = json.dumps(viz_data['bar_chart'])
            if 'heatmap' in viz_data:
                heatmap_data = json.dumps(viz_data['heatmap'])
        
        # ตรวจสอบข้อมูลกราฟ
        if not bar_chart_data and not heatmap_data:
            print("ไม่พบข้อมูลกราฟในไฟล์ JSON")
        
        return render_template(
            'results.html',
            job_category=job_category,
            job_title=job_title,
            candidates=result_data['candidates'],
            session_id=session_id,
            bar_chart_data=bar_chart_data,
            heatmap_data=heatmap_data
        )
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการแสดงผลลัพธ์: {e}")
        flash(f'เกิดข้อผิดพลาดในการแสดงผลลัพธ์: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """ดาวน์โหลดไฟล์"""
    return send_from_directory(app.config['RESULTS_FOLDER'], filename)

@app.route('/job_description/<job_category>')
def get_job_description(job_category):
    """คืนค่าคำอธิบายงานตามหมวดหมู่"""
    if job_category in JOB_DESCRIPTIONS:
        return JOB_DESCRIPTIONS[job_category]
    return 'ไม่พบคำอธิบายงาน'

@app.route('/api/chart_data/<session_id>')
def get_chart_data(session_id):
    result_file = os.path.join(app.config['RESULTS_FOLDER'], f'{session_id}_results.json')
    if os.path.exists(result_file):
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        return jsonify(result_data.get('visualization_data', {}))
    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True)