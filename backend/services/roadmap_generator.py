import google.genai as genai
from typing import List, Dict, Optional
import logging
import json
import re

from backend.config import settings

_genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

logger = logging.getLogger( __name__ )

# Reliable resource database with working URLs
RELIABLE_RESOURCES = {
    "python" : [
        {"title" : "Python for Everybody", "type" : "course",
         "url" : "https://www.coursera.org/specializations/python",
         "duration" : "4 months", "difficulty" : "Beginner"},
        {"title" : "Python Official Tutorial", "type" : "docs",
         "url" : "https://docs.python.org/3/tutorial/",
         "duration" : "10 hours", "difficulty" : "Beginner"}
    ],
    "pytorch" : [
        {"title" : "PyTorch Official Tutorials", "type" : "docs",
         "url" : "https://pytorch.org/tutorials/",
         "duration" : "15 hours", "difficulty" : "Intermediate"},
        {"title" : "Deep Learning with PyTorch", "type" : "course",
         "url" : "https://www.udacity.com/course/deep-learning-pytorch--ud188",
         "duration" : "2 months", "difficulty" : "Intermediate"}
    ],
    "tensorflow" : [
        {"title" : "TensorFlow Official Tutorials", "type" : "docs",
         "url" : "https://www.tensorflow.org/tutorials",
         "duration" : "12 hours", "difficulty" : "Intermediate"},
        {"title" : "Deep Learning Specialization", "type" : "course",
         "url" : "https://www.coursera.org/specializations/deep-learning",
         "duration" : "6 months", "difficulty" : "Advanced"}
    ],
    "machine learning" : [
        {"title" : "Machine Learning by Andrew Ng", "type" : "course",
         "url" : "https://www.coursera.org/learn/machine-learning",
         "duration" : "11 weeks", "difficulty" : "Intermediate"},
        {"title" : "Introduction to ML", "type" : "book",
         "url" : "https://www.amazon.com/dp/0262043794",
         "duration" : "20 hours", "difficulty" : "Intermediate"}
    ],
    "docker" : [
        {"title" : "Docker Curriculum", "type" : "course",
         "url" : "https://docker-curriculum.com/",
         "duration" : "4 hours", "difficulty" : "Beginner"},
        {"title" : "Docker Official Docs", "type" : "docs",
         "url" : "https://docs.docker.com/get-started/",
         "duration" : "3 hours", "difficulty" : "Beginner"}
    ],
    "kubernetes" : [
        {"title" : "Kubernetes Basics", "type" : "docs",
         "url" : "https://kubernetes.io/docs/tutorials/kubernetes-basics/",
         "duration" : "6 hours", "difficulty" : "Intermediate"},
        {"title" : "CKAD Course", "type" : "course",
         "url" : "https://www.udemy.com/course/certified-kubernetes-application-developer/",
         "duration" : "25 hours", "difficulty" : "Advanced"}
    ],
    "aws" : [
        {"title" : "AWS Certified Cloud Practitioner", "type" : "course",
         "url" : "https://aws.amazon.com/certification/certified-cloud-practitioner/",
         "duration" : "20 hours", "difficulty" : "Beginner"},
        {"title" : "AWS Ramp-Up Guide", "type" : "docs",
         "url" : "https://aws.amazon.com/training/ramp-up-guides/",
         "duration" : "Varies", "difficulty" : "All levels"}
    ],
    "system design" : [
        {"title" : "Grokking System Design", "type" : "course",
         "url" : "https://www.educative.io/courses/grokking-the-system-design-interview",
         "duration" : "8 weeks", "difficulty" : "Advanced"},
        {"title" : "System Design Primer", "type" : "github",
         "url" : "https://github.com/donnemartin/system-design-primer",
         "duration" : "20 hours", "difficulty" : "Intermediate"}
    ],
    "bms" : [
        {"title" : "Battery Management Systems", "type" : "course",
         "url" : "https://www.udemy.com/course/battery-management-systems/",
         "duration" : "10 hours", "difficulty" : "Intermediate"},
        {"title" : "EV Battery Tech", "type" : "course",
         "url" : "https://www.coursera.org/learn/electric-vehicle-battery-technology",
         "duration" : "4 weeks", "difficulty" : "Intermediate"}
    ],
    "can bus" : [
        {"title" : "CAN Bus Explained", "type" : "tutorial",
         "url" : "https://www.csselectronics.com/pages/can-bus-tutorial",
         "duration" : "2 hours", "difficulty" : "Intermediate"},
        {"title" : "Automotive Protocols", "type" : "course",
         "url" : "https://www.udemy.com/course/automotive-ethernet/",
         "duration" : "5 hours", "difficulty" : "Advanced"}
    ],
    "plc" : [
        {"title" : "PLC Programming", "type" : "course",
         "url" : "https://www.plcacademy.com/",
         "duration" : "15 hours", "difficulty" : "Beginner"},
        {"title" : "SIEMENS PLC Training", "type" : "course",
         "url" : "https://www.udemy.com/course/siemens-plc-programming/",
         "duration" : "8 hours", "difficulty" : "Intermediate"}
    ],
    "sql" : [
        {"title" : "SQL Tutorial", "type" : "course",
         "url" : "https://www.w3schools.com/sql/",
         "duration" : "5 hours", "difficulty" : "Beginner"},
        {"title" : "Advanced SQL", "type" : "course",
         "url" : "https://www.coursera.org/learn/advanced-sql",
         "duration" : "4 weeks", "difficulty" : "Advanced"}
    ]
}


class RoadmapGenerator :
    def __init__ ( self ) :
        pass

    def _get_reliable_resources ( self, topic: str ) -> List[Dict] :
        """Get reliable resources for a topic"""
        topic_lower = topic.lower()

        # Direct match
        if topic_lower in RELIABLE_RESOURCES :
            return RELIABLE_RESOURCES[topic_lower]

        # Partial match
        for key, resources in RELIABLE_RESOURCES.items() :
            if key in topic_lower or topic_lower in key :
                return resources

        # Default resources
        return [
            {"title" : f"Learn {topic}", "type" : "course",
             "url" : f"https://www.coursera.org/search?query={topic.replace( ' ', '+' )}",
             "duration" : "Varies", "difficulty" : "Intermediate"},
            {"title" : f"{topic} Documentation", "type" : "docs",
             "url" : f"https://www.google.com/search?q={topic.replace( ' ', '+' )}+documentation",
             "duration" : "Varies", "difficulty" : "Intermediate"}
        ]

    def generate_roadmap ( self, resume_text: str, target_role: str, skill_gaps: List[str],
                           duration_weeks: int = 12, experience_level: Optional[str] = None ) -> Dict :
        logger.info( f"Generating {duration_weeks}-week roadmap for: {target_role}" )

        # Build resources section with reliable URLs
        resources_section = ""
        for skill in skill_gaps[:3] :
            resources = self._get_reliable_resources( skill )
            resources_section += f"\nFor {skill}:"
            for r in resources[:2] :
                resources_section += f"\n- {r['title']} ({r['type']}) - {r['url']}"

        prompt = f"""You are a career coach and curriculum designer.

Candidate wants to become: "{target_role}"
Resume excerpt: {resume_text[:1000]}
Skill gaps to address: {', '.join( skill_gaps ) if skill_gaps else 'general upskilling'}
Duration: {duration_weeks} weeks
Experience level: {experience_level or 'not specified'}

Reliable resources (use these exact URLs when matching topics):
{resources_section}

Respond ONLY with a valid JSON object with this exact structure:
{{
  "title": "{duration_weeks}-Week Path to {target_role}",
  "target_role": "{target_role}",
  "duration_weeks": {duration_weeks},
  "total_hours_estimated": <integer>,
  "summary": "<2-3 sentence overview>",
  "phases": [
    {{
      "phase_number": 1,
      "phase_title": "<e.g. Foundations>",
      "weeks": "1-3",
      "focus": "<focus area>",
      "weekly_tasks": [
        {{
          "week": 1,
          "topic": "<topic>",
          "description": "<what to learn and do>",
          "resources": [
            {{"title": "<name>", "type": "course|book|docs|video|practice", "url": "<use the reliable URL from above>", "duration": "<e.g. 4 hours>"}}
          ],
          "milestone": "<what to achieve by end of week>",
          "hours_per_week": <integer>
        }}
      ]
    }}
  ],
  "final_milestone": "<what candidate builds/achieves at end>",
  "tips": ["<tip 1>", "<tip 2>", "<tip 3>"]
}}

Use the reliable resource URLs provided. Make it specific and actionable."""

        try :
            response = _genai_client.models.generate_content(
                model=settings.GEMINI_SMART_MODEL,
                config=genai.types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=settings.MAX_TOKENS_ROADMAP,
                ),
                contents=prompt,
        )
            raw = response.text.strip()
            raw = re.sub( r"```json\s*", "", raw )
            raw = re.sub( r"```\s*", "", raw )
            brace_idx = raw.find( '{' )
            if brace_idx > 0 :
                raw = raw[brace_idx :]
            roadmap = json.loads( raw )

            # Post-process to ensure resources have valid URLs
            for phase in roadmap.get( 'phases', [] ) :
                for task in phase.get( 'weekly_tasks', [] ) :
                    for resource in task.get( 'resources', [] ) :
                        if not resource.get( 'url' ) or resource['url'] == 'null' or resource['url'] is None :
                            # Replace with reliable resource
                            reliable = self._get_reliable_resources( task['topic'] )
                            if reliable :
                                resource['url'] = reliable[0]['url']

            logger.info( f"Roadmap generated: {len( roadmap.get( 'phases', [] ) )} phases" )
            return roadmap
        except json.JSONDecodeError as e :
            logger.error( f"Roadmap JSON parse error: {e}" )
            return self._fallback_roadmap( target_role, skill_gaps, duration_weeks )
        except Exception as e :
            logger.error( f"Roadmap generation error: {e}" )
            raise Exception( f"Roadmap generation failed: {str( e )}" )

    def _fallback_roadmap ( self, target_role, skill_gaps, duration_weeks ) :
        weeks_per = max( 1, duration_weeks // max( len( skill_gaps ), 1 ) )
        phases = []
        for i, skill in enumerate( skill_gaps[:4] ) :
            sw = i * weeks_per + 1
            ew = sw + weeks_per - 1
            resources = self._get_reliable_resources( skill )
            phases.append( {
                "phase_number" : i + 1,
                "phase_title" : f"Learn {skill.title()}",
                "weeks" : f"{sw}-{ew}",
                "focus" : skill,
                "weekly_tasks" : [{
                    "week" : sw,
                    "topic" : skill.title(),
                    "description" : f"Study core concepts of {skill}",
                    "resources" : resources[:2],
                    "milestone" : f"Complete a small {skill} project",
                    "hours_per_week" : 8
                }]
            } )
        return {
            "title" : f"{duration_weeks}-Week Path to {target_role}",
            "target_role" : target_role,
            "duration_weeks" : duration_weeks,
            "total_hours_estimated" : duration_weeks * 8,
            "summary" : f"A structured plan to become a {target_role}.",
            "phases" : phases,
            "final_milestone" : f"Build a {target_role} portfolio project.",
            "tips" : ["1 hour daily consistently.", "Build projects — don't just watch tutorials.",
                      "Share progress on LinkedIn or GitHub."]
        }


_roadmap_generator = None


def get_roadmap_generator () -> RoadmapGenerator :
    global _roadmap_generator
    if _roadmap_generator is None :
        _roadmap_generator = RoadmapGenerator()
    return _roadmap_generator