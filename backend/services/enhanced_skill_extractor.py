import re
from typing import List, Dict, Set
from collections import defaultdict


class EnhancedSkillExtractor :
    """Better skill extraction with context awareness"""

    def __init__ ( self ) :
        # Skill categories with variations
        self.skill_db = {
            "python" : ["python", "python3", "py", "django", "flask", "fastapi"],
            "javascript" : ["javascript", "js", "node.js", "nodejs", "react", "vue", "angular"],
            "machine_learning" : ["machine learning", "ml", "deep learning", "neural networks",
                                  "tensorflow", "pytorch", "scikit-learn"],
            "cloud" : ["aws", "azure", "gcp", "cloud", "ec2", "s3", "lambda"],
            "databases" : ["sql", "mysql", "postgresql", "mongodb", "redis", "nosql"],
            "devops" : ["docker", "kubernetes", "k8s", "ci/cd", "jenkins", "terraform"]
        }

        # Experience level indicators
        self.experience_keywords = {
            "expert" : ["expert", "advanced", "senior", "lead", "architect", "mastery"],
            "proficient" : ["proficient", "strong", "skilled", "experienced"],
            "intermediate" : ["intermediate", "working knowledge", "familiar with"],
            "beginner" : ["basic", "beginner", "learning", "exposure to"]
        }

    def extract_skills_with_context ( self, text: str ) -> List[Dict] :
        """Extract skills with proficiency levels and context"""
        text_lower = text.lower()
        skills_found = []

        # Extract skills with surrounding context
        for skill_category, variations in self.skill_db.items() :
            for variation in variations :
                pattern = rf'(.{{0,50}})\b{re.escape( variation )}\b(.{{0,50}})'
                matches = re.finditer( pattern, text_lower, re.IGNORECASE )

                for match in matches :
                    context = match.group( 1 ) + match.group( 0 ) + match.group( 2 )
                    proficiency = self._detect_proficiency( context )
                    years = self._extract_years( context )

                    skills_found.append( {
                        "skill" : skill_category,
                        "variation" : variation,
                        "proficiency" : proficiency,
                        "years_experience" : years,
                        "context" : context.strip()
                    } )
                    break  # Found this skill, move to next

        # Deduplicate by skill category
        unique_skills = {}
        for skill in skills_found :
            category = skill["skill"]
            if category not in unique_skills :
                unique_skills[category] = skill
            else :
                # Keep the one with higher proficiency
                if self._proficiency_score( skill["proficiency"] ) > \
                        self._proficiency_score( unique_skills[category]["proficiency"] ) :
                    unique_skills[category] = skill

        return list( unique_skills.values() )

    def _detect_proficiency ( self, context: str ) -> str :
        """Detect proficiency level from context"""
        context_lower = context.lower()

        for level, keywords in self.experience_keywords.items() :
            if any( kw in context_lower for kw in keywords ) :
                return level

        return "intermediate"  # Default

    def _extract_years ( self, context: str ) -> int :
        """Extract years of experience from context"""
        # Pattern: "5 years", "5+ years", "5-7 years"
        year_pattern = r'(\d+)\+?\s*(?:-\s*\d+\s*)?years?'
        match = re.search( year_pattern, context.lower() )

        if match :
            return int( match.group( 1 ) )
        return 0

    def _proficiency_score ( self, proficiency: str ) -> int :
        """Convert proficiency to numeric score"""
        scores = {"beginner" : 1, "intermediate" : 2, "proficient" : 3, "expert" : 4}
        return scores.get( proficiency, 2 )

    def compare_skills ( self, resume_skills: List[Dict], job_skills: List[Dict] ) -> Dict :
        """Compare resume skills with job requirements"""
        resume_skill_map = {s["skill"] : s for s in resume_skills}
        job_skill_map = {s["skill"] : s for s in job_skills}

        matched = []
        gaps = []
        overqualified = []

        # Check each job requirement
        for skill_name, job_skill in job_skill_map.items() :
            if skill_name in resume_skill_map :
                resume_skill = resume_skill_map[skill_name]
                resume_score = self._proficiency_score( resume_skill["proficiency"] )
                job_score = self._proficiency_score( job_skill["proficiency"] )

                if resume_score >= job_score :
                    matched.append( {
                        "skill" : skill_name,
                        "resume_level" : resume_skill["proficiency"],
                        "required_level" : job_skill["proficiency"],
                        "status" : "qualified"
                    } )
                elif resume_score == job_score - 1 :
                    matched.append( {
                        "skill" : skill_name,
                        "resume_level" : resume_skill["proficiency"],
                        "required_level" : job_skill["proficiency"],
                        "status" : "close_match"
                    } )
                else :
                    gaps.append( {
                        "skill" : skill_name,
                        "resume_level" : resume_skill["proficiency"],
                        "required_level" : job_skill["proficiency"],
                        "gap_severity" : "moderate"
                    } )
            else :
                gaps.append( {
                    "skill" : skill_name,
                    "resume_level" : "none",
                    "required_level" : job_skill["proficiency"],
                    "gap_severity" : "critical"
                } )

        # Check for overqualified skills
        for skill_name, resume_skill in resume_skill_map.items() :
            if skill_name not in job_skill_map :
                overqualified.append( {
                    "skill" : skill_name,
                    "level" : resume_skill["proficiency"]
                } )

        return {
            "matched_skills" : matched,
            "skill_gaps" : gaps,
            "bonus_skills" : overqualified,
            "overall_match" : len( matched ) / (len( matched ) + len( gaps )) * 100 if (matched or gaps) else 0
        }


# Usage Example
if __name__ == "__main__" :
    extractor = EnhancedSkillExtractor()

    # Example resume text
    resume_text = """
    Senior Software Engineer with 5 years of Python experience.
    Expert in machine learning and deep learning frameworks like TensorFlow.
    Working knowledge of AWS cloud services including EC2 and S3.
    Proficient in Docker and Kubernetes for containerization.
    """

    # Example job description
    job_text = """
    Looking for intermediate Python developer with 3+ years experience.
    Strong machine learning background required.
    Experience with cloud platforms (AWS preferred).
    Docker knowledge is a plus.
    """

    resume_skills = extractor.extract_skills_with_context( resume_text )
    job_skills = extractor.extract_skills_with_context( job_text )

    comparison = extractor.compare_skills( resume_skills, job_skills )

    print( "=== SKILL ASSESSMENT ===" )
    print( f"\nOverall Match: {comparison['overall_match']:.1f}%" )

    print( "\n✅ Matched Skills:" )
    for skill in comparison['matched_skills'] :
        print(
            f"  {skill['skill']}: {skill['resume_level']} (required: {skill['required_level']}) - {skill['status']}" )

    print( "\n⚠️ Skill Gaps:" )
    for gap in comparison['skill_gaps'] :
        print( f"  {gap['skill']}: {gap['resume_level']} → {gap['required_level']} ({gap['gap_severity']})" )

    print( "\n🌟 Bonus Skills:" )
    for bonus in comparison['bonus_skills'] :
        print( f"  {bonus['skill']}: {bonus['level']}" )