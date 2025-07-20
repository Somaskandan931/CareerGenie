import rake_nltk
from typing import List

def extract_keywords(text: str, num_keywords: int = 10) -> List[str]:
    rake = rake_nltk.Rake()
    rake.extract_keywords_from_text(text)
    return rake.get_ranked_phrases()[:num_keywords]
