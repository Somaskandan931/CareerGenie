from fastapi import APIRouter, UploadFile, File, HTTPException
import logging

router = APIRouter()
logger = logging.getLogger( __name__ )


@router.post( "/parse" )  # This creates the endpoint /upload-resume/parse
async def parse_resume ( file: UploadFile = File( ... ) ) :
    try :
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]

        if file.content_type not in allowed_types :
            raise HTTPException( status_code=400, detail="Invalid file type" )

        # Mock parsing logic - replace with actual parsing
        mock_parsed_data = {
            "personal_info" : {
                "name" : "John Doe",
                "email" : "john.doe@example.com",
                "phone" : "+1-555-0123",
                "address" : "San Francisco, CA"
            },
            "education" : [],
            "experience" : [],
            "skills" : ["Python", "JavaScript", "SQL", "React"],
            "projects" : []
        }

        resume_text = f"{mock_parsed_data['personal_info']['name']} {' '.join( mock_parsed_data['skills'] )}"

        return {
            "parsed_data" : mock_parsed_data,
            "resume_text" : resume_text,
            "filename" : file.filename
        }

    except Exception as e :
        logger.error( f"Resume parsing error: {str( e )}" )
        raise HTTPException( status_code=500, detail="Resume parsing failed" )