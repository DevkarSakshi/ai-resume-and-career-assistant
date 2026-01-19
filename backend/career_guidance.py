from typing import List, Dict
from datetime import datetime

class CareerGuidanceService:
    """Career guidance service aligned with SDG 8"""
    
    # Career paths database (can be expanded)
    CAREER_PATHS = {
        "software_development": {
            "title": "Software Development",
            "roles": ["Software Engineer", "Full Stack Developer", "Backend Developer", "Frontend Developer", "Mobile App Developer"],
            "required_skills": ["programming", "problem solving", "data structures", "algorithms"],
            "description": "Build and maintain software applications. High demand with growth opportunities.",
            "entry_level": ["Junior Developer", "Associate Software Engineer", "Software Developer Trainee"],
            "growth_path": "Senior Developer → Tech Lead → Engineering Manager → CTO"
        },
        "data_science": {
            "title": "Data Science & Analytics",
            "roles": ["Data Analyst", "Data Scientist", "Business Analyst", "Data Engineer"],
            "required_skills": ["python", "statistics", "sql", "machine learning", "data analysis"],
            "description": "Analyze data to extract insights and drive business decisions. Growing field with excellent prospects.",
            "entry_level": ["Junior Data Analyst", "Data Analyst Trainee", "Business Intelligence Intern"],
            "growth_path": "Data Analyst → Data Scientist → Senior Data Scientist → Chief Data Officer"
        },
        "web_development": {
            "title": "Web Development",
            "roles": ["Web Developer", "Frontend Developer", "React Developer", "UI/UX Developer"],
            "required_skills": ["html", "css", "javascript", "react", "frontend"],
            "description": "Create and maintain websites and web applications. Essential skill in the digital economy.",
            "entry_level": ["Junior Web Developer", "Frontend Developer Intern", "Web Developer Trainee"],
            "growth_path": "Junior Developer → Mid-level Developer → Senior Developer → Tech Lead"
        },
        "cybersecurity": {
            "title": "Cybersecurity",
            "roles": ["Security Analyst", "Cybersecurity Specialist", "Security Engineer", "Penetration Tester"],
            "required_skills": ["networking", "security", "linux", "cryptography", "ethical hacking"],
            "description": "Protect systems and data from cyber threats. Critical field with high demand.",
            "entry_level": ["Security Analyst Trainee", "Junior Security Analyst", "Cybersecurity Intern"],
            "growth_path": "Security Analyst → Security Engineer → Senior Security Engineer → CISO"
        },
        "cloud_computing": {
            "title": "Cloud Computing & DevOps",
            "roles": ["Cloud Engineer", "DevOps Engineer", "Site Reliability Engineer", "Cloud Architect"],
            "required_skills": ["aws", "docker", "kubernetes", "ci/cd", "cloud"],
            "description": "Manage cloud infrastructure and deployment pipelines. Rapidly growing field.",
            "entry_level": ["Junior Cloud Engineer", "DevOps Intern", "Cloud Support Engineer"],
            "growth_path": "Cloud Engineer → Senior Cloud Engineer → Cloud Architect → Head of Infrastructure"
        },
        "digital_marketing": {
            "title": "Digital Marketing",
            "roles": ["Digital Marketing Specialist", "SEO Specialist", "Social Media Manager", "Content Marketer"],
            "required_skills": ["seo", "social media", "content creation", "analytics", "communication"],
            "description": "Promote brands and products through digital channels. Creative and analytical field.",
            "entry_level": ["Digital Marketing Intern", "Marketing Assistant", "Social Media Intern"],
            "growth_path": "Marketing Specialist → Marketing Manager → Senior Marketing Manager → CMO"
        },
        "product_management": {
            "title": "Product Management",
            "roles": ["Associate Product Manager", "Product Analyst", "Product Owner", "Product Manager"],
            "required_skills": ["problem solving", "communication", "analytics", "project management", "user research"],
            "description": "Define and guide product development. Bridge between business and technology.",
            "entry_level": ["Product Intern", "Associate Product Manager", "Product Analyst"],
            "growth_path": "Associate PM → Product Manager → Senior PM → Director of Product → VP Product"
        },
        "consulting": {
            "title": "Business & Technology Consulting",
            "roles": ["Business Analyst", "Consultant", "Technology Consultant", "Management Trainee"],
            "required_skills": ["communication", "problem solving", "analytics", "business knowledge", "presentation"],
            "description": "Help organizations solve business problems and improve processes.",
            "entry_level": ["Consulting Intern", "Business Analyst", "Associate Consultant"],
            "growth_path": "Analyst → Consultant → Senior Consultant → Manager → Partner"
        }
    }
    
    async def get_career_suggestions(
        self,
        skills: List[str],
        interests: List[str],
        education: str,
        session_id: str
    ) -> Dict:
        """Get career suggestions based on user profile"""
        
        # Normalize inputs
        skills_lower = [s.lower().strip() for s in skills]
        interests_lower = [i.lower().strip() for i in interests]
        education_lower = education.lower() if education else ""
        
        # Score each career path
        scored_paths = []
        
        for path_id, path_data in self.CAREER_PATHS.items():
            score = 0
            matched_skills = []
            
            # Check skill matches
            required_skills = path_data["required_skills"]
            for skill in skills_lower:
                for req_skill in required_skills:
                    if req_skill in skill or skill in req_skill:
                        score += 2
                        matched_skills.append(skill)
                        break
            
            # Check interest matches
            path_title_lower = path_data["title"].lower()
            for interest in interests_lower:
                if any(word in interest for word in path_title_lower.split()) or \
                   any(word in path_title_lower for word in interest.split()):
                    score += 3
            
            # Check education relevance (simple keyword matching)
            tech_terms = ["computer", "engineering", "science", "technology", "it", "information"]
            if any(term in education_lower for term in tech_terms) and "tech" in path_id:
                score += 1
            
            scored_paths.append({
                "path_id": path_id,
                "score": score,
                "data": path_data,
                "matched_skills": list(set(matched_skills))
            })
        
        # Sort by score
        scored_paths.sort(key=lambda x: x["score"], reverse=True)
        
        # Get top 3 recommendations
        top_paths = scored_paths[:3]
        
        # Build response
        recommendations = []
        for path_info in top_paths:
            path_data = path_info["data"]
            recommendations.append({
                "title": path_data["title"],
                "description": path_data["description"],
                "entry_level_roles": path_data["entry_level"],
                "growth_path": path_data["growth_path"],
                "matched_skills": path_info["matched_skills"],
                "score": path_info["score"]
            })
        
        # Generate actionable advice
        advice = self._generate_actionable_advice(skills_lower, interests_lower, top_paths[0] if top_paths else None)
        
        return {
            "recommendations": recommendations,
            "actionable_advice": advice,
            "aligned_with_sdg8": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_actionable_advice(
        self,
        skills: List[str],
        interests: List[str],
        top_path: Dict
    ) -> List[str]:
        """Generate actionable career advice"""
        advice = []
        
        if not top_path:
            advice.append("📚 Start by building a strong foundation in programming and problem-solving skills.")
            advice.append("🎯 Explore different tech fields through online courses and projects.")
            advice.append("💼 Build a portfolio showcasing your projects and skills.")
            return advice
        
        top_path_data = top_path["data"]
        matched_skills = top_path.get("matched_skills", [])
        
        # Skill gap analysis
        required_skills = top_path_data["required_skills"]
        missing_skills = [skill for skill in required_skills 
                         if not any(skill in s or s in skill for s in skills)]
        
        if missing_skills:
            advice.append(f"🔧 **Skill Development**: Focus on learning {', '.join(missing_skills[:3])} to strengthen your profile for {top_path_data['title']} roles.")
        
        # Portfolio advice
        advice.append(f"💼 **Build a Portfolio**: Create 2-3 projects demonstrating your skills relevant to {top_path_data['title']}. Host them on GitHub.")
        
        # Entry-level positioning
        if top_path_data.get("entry_level"):
            advice.append(f"🎯 **Target Roles**: Start applying for entry-level positions like '{top_path_data['entry_level'][0]}' to gain experience.")
        
        # Networking advice
        advice.append("🤝 **Networking**: Join professional communities, attend meetups, and connect with professionals in your target field on LinkedIn.")
        
        # Certifications
        advice.append("📜 **Certifications**: Consider obtaining relevant certifications (e.g., AWS, Google Cloud, Microsoft Azure) to validate your skills.")
        
        # SDG 8 alignment
        advice.append("🌍 **SDG 8 Alignment**: Your career journey contributes to decent work and economic growth. Focus on continuous learning and skill development.")
        
        return advice
