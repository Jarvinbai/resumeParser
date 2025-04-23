# main.py
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import tempfile
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
import json
from dotenv import load_dotenv

# Import our document parser
from document_parser import extract_text_from_file

load_dotenv()

# Create FastAPI app
app = FastAPI(title="Resume Parser API", description="API for parsing resumes using text extraction and Gemini API")

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Models for resume parsing
class ContactInformation(BaseModel):
    name: str = Field(description="Full name of the person")
    address: Optional[str] = Field(default=None, description="Physical address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    email: Optional[str] = Field(default=None, description="Email address")

class Education(BaseModel):
    institution: str = Field(description="Name of the educational institution")
    degree: str = Field(description="Degree obtained or pursuing")
    field_of_study: Optional[str] = Field(default=None, description="Major or field of study")
    gpa: Optional[float] = Field(default=None, description="GPA or score achieved")
    start_date: Optional[str] = Field(default=None, description="Start date of education")
    end_date: Optional[str] = Field(default=None, description="End date or expected completion date")

class Experience(BaseModel):
    company: str = Field(description="Company or organization name")
    position: str = Field(description="Job title or position")
    start_date: Optional[str] = Field(default=None, description="Start date of employment")
    end_date: Optional[str] = Field(default=None, description="End date of employment or 'Present' if current")
    description: Optional[str] = Field(default=None, description="Description of responsibilities and achievements")

class Skill(BaseModel):
    name: str = Field(description="Name of the skill")
    category: Optional[str] = Field(default=None, description="Category the skill belongs to (e.g., Technical, Soft, Language)")

class Resume(BaseModel):
    personal_info: ContactInformation = Field(description="Personal contact information")
    education: List[Education] = Field(description="Educational background")
    experience: List[Experience] = Field(description="Work experience")
    skills: List[Skill] = Field(description="Skills and competencies")
    certifications: Optional[List[str]] = Field(default=None, description="Professional certifications")

# Initialize Gemini API client
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("No Gemini API key found. Set the GEMINI_API_KEY environment variable in your .env file.")

MODEL_ID = "gemini-2.0-flash"
genai_client = genai.Client(api_key=API_KEY)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the upload form"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/parse-resume/")
async def parse_resume(
    file: UploadFile = File(...),
    secret_key: str = Form(...)
    ):
    """
    Parse a resume file by first extracting text and then using Gemini API
    """
    if secret_key != "bhajrangibhaijaan":
        return JSONResponse(
            status_code=401,  # Unauthorized
            content={"error": "Invalid secret key"}
        )
        # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported file format. Supported formats: {', '.join(allowed_extensions)}"}
        )
    
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        print(f"Temporary file created at: {temp_path}")
        
        # Extract text from the file
        try:
            # Reset file pointer to beginning
            with open(temp_path, "rb") as reopened_file:
                extracted_text = extract_text_from_file(reopened_file, file.filename)
                print(f"Successfully extracted text from {file.filename} ({len(extracted_text)} characters)")
                
                # Save extracted text for debugging if needed
                with open(f"{temp_path}.txt", "w", encoding="utf-8") as text_file:
                    text_file.write(extracted_text)
        except Exception as extract_error:
            print(f"Error extracting text: {str(extract_error)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to extract text from file: {str(extract_error)}"}
            )
        
        # Test basic API functionality first
        try:
            print("Testing basic API connectivity...")
            test_response = genai_client.models.generate_content(
                model=MODEL_ID,
                contents=["Test API connection. Please respond with 'API connection successful'."]
            )
            print(f"Basic API test result: {test_response.text}")
        except Exception as test_error:
            print(f"Basic API test failed: {str(test_error)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"API connection test failed: {str(test_error)}"}
            )
        
        # Send extracted text to Gemini API for structured parsing
        try:
            print("Sending extracted text to Gemini  API...")
            response = genai_client.models.generate_content(
                model=MODEL_ID,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"""
            You are a resume parser.

            Extract the following details from the resume text below and return the data in the following strict JSON format:

            {{
                "data": {{
                    "resume_id": "[Generate a random hash/id]",
                    "file_name": "{file.filename}",
                    "first_name": "",
                    "last_name": "",
                    "full_name": "",
                    "email_id": "",
                    "phone_number": "",
                    "gender": null,
                    "job_titles": "",
                    "category": "Information",
                    "sub_category": "Software developers and programmers",
                    "city": "",
                    "country": "",
                    "address": [
                        {{
                            "Street": "",
                            "City": "",
                            "State": "",
                            "StateIsoCode": "",
                            "Country": "",
                            "CountryCode": {{
                                "IsoAlpha2": "",
                                "IsoAlpha3": "",
                                "UNCode": ""
                            }},
                            "ZipCode": "",
                            "FormattedAddress": "",
                            "Type": "Present",
                            "ConfidenceScore": 7
                        }}
                    ],
                    "websites": [
                        {{
                            "Type": "",
                            "Url": ""
                        }}
                    ],
                    "qualifications": "",
                    "summary": "",
                    "employment_data": [
                        {{
                            "Employer": {{
                                "EmployerName": "",
                                "FormattedName": "",
                                "ConfidenceScore": 9
                            }},
                            "JobProfile": {{
                                "Title": "",
                                "FormattedName": "",
                                "RelatedSkills": []
                            }},
                            "Location": {{
                                "City": "",
                                "State": "",
                                "StateIsoCode": "",
                                "Country": "",
                                "CountryCode": {{
                                    "IsoAlpha2": "",
                                    "IsoAlpha3": "",
                                    "UNCode": ""
                                }}
                            }},
                            "JobPeriod": "",
                            "FormattedJobPeriod": "",
                            "StartDate": "",
                            "EndDate": "",
                            "IsCurrentEmployer": "",
                            "JobDescription": ""
                        }}
                    ],
                    "employers": "",
                    "total_experience_years": "",
                    "job_profile": "",
                    "salary_current": null,
                    "salary_expectations": null,
                    "current_employer": "",
                    "executive_summary": "",
                    "objectives": "",
                    "hobbies": "",
                    "plain_text": "{extracted_text}"
                }},
                "skills": [],
                "websites": [
                    {{
                        "Type": "",
                        "Url": ""
                    }}
                ],
            }}
            
            When extracting websites, identify the type (e.g., LinkedIn, GitHub, Portfolio, Personal) and provide the full URL. If multiple websites are found, include them all as separate objects in the websites array.
            For skills, extract all technical, soft, and domain-specific skills from the resume and present them as a comma-separated string.

            Only return the JSON. Do not use Markdown, bullet points, or extra text. Do not explain anything.

            RESUME TEXT:
            {extracted_text}
                                """
                            }
                        ]
                    }
                ],
                config={
                    "response_mime_type": "application/json"
                }
            )
            print("Structured content generation successful")
        except Exception as gen_error:
            print(f"Error during structured content generation: {str(gen_error)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Structured content generation failed: {str(gen_error)}"}
            )
        
        # Convert response to JSON
        try:
            print("Parsing response text to JSON...")
            parsed_data = json.loads(response.text)
            print("JSON parsing successful")
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing error: {str(json_error)}")
            print(f"Response text: {response.text[:200]}...")
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to parse response as JSON: {str(json_error)}"}
            )
        
        # Clean up temp files
        os.unlink(temp_path)
        if os.path.exists(f"{temp_path}.txt"):
            os.unlink(f"{temp_path}.txt")
        print("Temporary files cleaned up")
        
        return JSONResponse(content=parsed_data)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing file: {str(e)}"}
        )
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)