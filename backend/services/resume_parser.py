import pdfplumber
import docx
from pathlib import Path
import logging

logger = logging.getLogger( __name__ )


class ResumeParser :
    def parse ( self, file_path: str ) -> dict :
        """
        Parse resume from PDF or DOCX file

        Args:
            file_path: Path to resume file

        Returns:
            Dictionary with resume_text and word_count
        """
        file_path = Path( file_path )

        if not file_path.exists() :
            raise FileNotFoundError( f"File not found: {file_path}" )

        logger.info( f"Parsing resume: {file_path.name}" )

        # Parse based on file extension
        if file_path.suffix.lower() == '.pdf' :
            text = self._parse_pdf( file_path )
        elif file_path.suffix.lower() in ['.docx', '.doc'] :
            text = self._parse_docx( file_path )
        else :
            raise ValueError( f"Unsupported file format: {file_path.suffix}" )

        # Clean and validate
        text = text.strip()
        if not text :
            raise ValueError( "Resume appears to be empty" )

        word_count = len( text.split() )
        logger.info( f"Parsed resume: {word_count} words" )

        return {
            "resume_text" : text,
            "word_count" : word_count
        }

    def _parse_pdf ( self, file_path: Path ) -> str :
        """Extract text from PDF"""
        text_parts = []

        try :
            with pdfplumber.open( file_path ) as pdf :
                for page in pdf.pages :
                    page_text = page.extract_text()
                    if page_text :
                        text_parts.append( page_text )

            return "\n".join( text_parts )

        except Exception as e :
            logger.error( f"Error parsing PDF: {str( e )}" )
            raise Exception( f"Failed to parse PDF: {str( e )}" )

    def _parse_docx ( self, file_path: Path ) -> str :
        """Extract text from DOCX"""
        try :
            doc = docx.Document( file_path )
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join( paragraphs )

        except Exception as e :
            logger.error( f"Error parsing DOCX: {str( e )}" )
            raise Exception( f"Failed to parse DOCX: {str( e )}" )


# Singleton instance
resume_parser = ResumeParser()