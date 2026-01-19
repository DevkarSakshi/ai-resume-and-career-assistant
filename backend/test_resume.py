from resume_generator import ResumeGenerator

# Create a minimal resume data dictionary
resume_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "linkedin": "https://linkedin.com/in/johndoe",
    "portfolio": "https://github.com/johndoe",
    "summary": "Aspiring software engineer with strong Python skills.",
    "education": [{"details": "BSc Computer Science, XYZ University"}],
    "skills": {"technical": ["Python", "Git"], "soft": ["Communication"]},
    "experience": [{"details": "Intern at ABC Corp"}],
    "projects": [{"details": "Personal portfolio website"}],
    "achievements": ["Dean's List 2025"],
    "certifications": ["AWS Certified Developer"]
}

# Instantiate the generator
gen = ResumeGenerator()

# Generate PDF
pdf_file = gen.generate_pdf(resume_data, "test_resume.pdf")

print("PDF generated at:", pdf_file)
