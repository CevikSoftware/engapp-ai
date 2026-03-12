"""
CEFR (Common European Framework of Reference for Languages) Configuration Module
================================================================================
Central configuration for difficulty levels across all modules.

CEFR Levels:
  - A1 (Beginner)
  - A2 (Elementary)  
  - A1-A2 (Beginner - Elementary)
  - B1 (Pre-Intermediate)
  - B2 (Intermediate)
  - A2-B1 (Elementary - Pre-Intermediate)
  - B1-B2 (Pre-Int. - Intermediate)
  - C1 (Upper-Intermediate)
  - C2 (Advanced)
  - B2-C1 (Intermediate - Upper-Int.)
  - C1-C2 (Upper-Int. - Advanced)
"""

from enum import Enum
from typing import Dict, Any


class CEFRLevel(str, Enum):
    """
    CEFR difficulty levels for all modules.
    Includes single levels and combined/transitional levels.
    """
    A1 = "A1"
    A2 = "A2"
    A1_A2 = "A1-A2"
    B1 = "B1"
    B2 = "B2"
    A2_B1 = "A2-B1"
    B1_B2 = "B1-B2"
    C1 = "C1"
    C2 = "C2"
    B2_C1 = "B2-C1"
    C1_C2 = "C1-C2"


# Human-readable labels for UI display
CEFR_LABELS: Dict[str, str] = {
    "A1": "A1 (Beginner)",
    "A2": "A2 (Elementary)",
    "A1-A2": "A1-A2 (Beginner - Elementary)",
    "B1": "B1 (Pre-Intermediate)",
    "B2": "B2 (Intermediate)",
    "A2-B1": "A2-B1 (Elementary - Pre-Int.)",
    "B1-B2": "B1-B2 (Pre-Int. - Intermediate)",
    "C1": "C1 (Upper-Intermediate)",
    "C2": "C2 (Advanced)",
    "B2-C1": "B2-C1 (Intermediate - Upper-Int.)",
    "C1-C2": "C1-C2 (Upper-Int. - Advanced)",
}

# Ordered list for UI selectbox (from easiest to hardest)
CEFR_OPTIONS = list(CEFR_LABELS.keys())
CEFR_OPTIONS_WITH_LABELS = list(CEFR_LABELS.values())

# Default level index (B1 = index 3)
CEFR_DEFAULT_INDEX = 3


# =============================================================================
# CEFR CONTENT SPECIFICATIONS
# =============================================================================
# Each level defines exact parameters for content generation.
# All generators MUST use these specs to ensure consistency.
# =============================================================================

CEFR_SPECS: Dict[str, Dict[str, Any]] = {
    "A1": {
        "label": "A1 (Beginner)",
        "vocabulary": {
            "description": "Very basic, everyday words only",
            "word_count_range": "500-1000 words known",
            "examples": "hello, water, food, house, big, small, go, like",
            "restrictions": "No phrasal verbs, no idioms, no abstract words"
        },
        "grammar": {
            "tenses": "Present simple, present continuous ONLY",
            "structures": "Simple SVO sentences, basic yes/no questions, simple negatives",
            "connectors": "and, but, because",
            "restrictions": "No passive, no conditionals, no relative clauses"
        },
        "sentence_length": {
            "words_per_sentence": "3-7 words",
            "min": 3,
            "max": 7
        },
        "text_length_multiplier": 0.5,
        "content": {
            "topics": "Self, family, daily routines, basic needs, simple descriptions",
            "complexity": "Concrete, tangible, immediately relevant",
            "style": "Very short paragraphs, repetitive structures for reinforcement"
        },
        "conversation": {
            "response_length": "1 sentence",
            "pace": "Very slow, patient, encouraging",
            "exchanges_short": "3-4",
            "exchanges_medium": "5-7",
            "exchanges_long": "8-10"
        },
        "assessment": {
            "question_style": "Direct factual, explicitly stated in text",
            "distractors": "Obviously incorrect",
            "blanks_per_question": 1,
            "builder_words": "3-5 words",
            "vocab_level": "Most common 500 words",
            "scoring_leniency": "Very lenient (70-100 for decent attempts)"
        }
    },
    
    "A2": {
        "label": "A2 (Elementary)",
        "vocabulary": {
            "description": "Common everyday words and basic expressions",
            "word_count_range": "1000-2000 words known",
            "examples": "beautiful, important, decide, restaurant, holiday, sometimes",
            "restrictions": "Avoid complex phrasal verbs, limited idioms"
        },
        "grammar": {
            "tenses": "Present simple, present continuous, past simple, going to (future)",
            "structures": "Simple compound sentences, basic comparatives/superlatives, there is/are",
            "connectors": "and, but, because, so, then, also, first, next",
            "restrictions": "No past perfect, no passive voice, no third conditional"
        },
        "sentence_length": {
            "words_per_sentence": "5-10 words",
            "min": 5,
            "max": 10
        },
        "text_length_multiplier": 0.65,
        "content": {
            "topics": "Shopping, travel, work basics, hobbies, simple stories",
            "complexity": "Familiar situations, predictable content",
            "style": "Short paragraphs, clear structure"
        },
        "conversation": {
            "response_length": "1-2 sentences",
            "pace": "Slow, clear, supportive",
            "exchanges_short": "4-5",
            "exchanges_medium": "6-8",
            "exchanges_long": "10-14"
        },
        "assessment": {
            "question_style": "Straightforward comprehension, main ideas",
            "distractors": "Plausible but clearly wrong on careful reading",
            "blanks_per_question": 1,
            "builder_words": "5-8 words",
            "vocab_level": "Common A2 vocabulary",
            "scoring_leniency": "Lenient (65-95 typical range)"
        }
    },
    
    "A1-A2": {
        "label": "A1-A2 (Beginner - Elementary)",
        "vocabulary": {
            "description": "Basic everyday words transitioning to common expressions",
            "word_count_range": "750-1500 words known",
            "examples": "family, school, weather, want, need, happy, because",
            "restrictions": "No phrasal verbs, avoid abstract vocabulary"
        },
        "grammar": {
            "tenses": "Present simple, present continuous, basic past simple",
            "structures": "Simple SVO, basic compound sentences with and/but/because",
            "connectors": "and, but, because, so",
            "restrictions": "No perfect tenses, no passive, no conditionals"
        },
        "sentence_length": {
            "words_per_sentence": "4-8 words",
            "min": 4,
            "max": 8
        },
        "text_length_multiplier": 0.55,
        "content": {
            "topics": "Daily life, family, simple routines, basic preferences",
            "complexity": "Concrete and familiar, slightly expanding topics",
            "style": "Short paragraphs, some repetition, clear vocabulary"
        },
        "conversation": {
            "response_length": "1-2 sentences",
            "pace": "Slow, patient, clear pronunciation",
            "exchanges_short": "3-5",
            "exchanges_medium": "6-8",
            "exchanges_long": "9-12"
        },
        "assessment": {
            "question_style": "Simple factual questions, basic comprehension",
            "distractors": "Clearly incorrect",
            "blanks_per_question": 1,
            "builder_words": "4-6 words",
            "vocab_level": "High-frequency basic words",
            "scoring_leniency": "Very lenient (70-100)"
        }
    },
    
    "B1": {
        "label": "B1 (Pre-Intermediate)",
        "vocabulary": {
            "description": "Moderate vocabulary including common phrasal verbs and collocations",
            "word_count_range": "2000-3500 words known",
            "examples": "significant, opportunity, although, experience, look forward to, get along with",
            "restrictions": "Avoid highly academic or technical terms"
        },
        "grammar": {
            "tenses": "All simple tenses, present perfect, past continuous, first conditional",
            "structures": "Relative clauses (who/which/that), passive voice (simple), reported speech (basic)",
            "connectors": "however, although, while, therefore, as a result, on the other hand",
            "restrictions": "Avoid complex inversion, cleft sentences"
        },
        "sentence_length": {
            "words_per_sentence": "8-14 words",
            "min": 8,
            "max": 14
        },
        "text_length_multiplier": 0.8,
        "content": {
            "topics": "Work, education, current events, personal experiences, opinions",
            "complexity": "Both concrete and some abstract topics, cause-effect relationships",
            "style": "Well-structured paragraphs, topic sentences, logical flow"
        },
        "conversation": {
            "response_length": "2-3 sentences",
            "pace": "Natural moderate pace",
            "exchanges_short": "5-7",
            "exchanges_medium": "8-12",
            "exchanges_long": "14-20"
        },
        "assessment": {
            "question_style": "Inference, vocabulary-in-context, cause-effect",
            "distractors": "Plausible, requiring careful reading",
            "blanks_per_question": 2,
            "builder_words": "7-12 words",
            "vocab_level": "B1 intermediate vocabulary",
            "scoring_leniency": "Balanced (55-90 typical range)"
        }
    },
    
    "A2-B1": {
        "label": "A2-B1 (Elementary - Pre-Int.)",
        "vocabulary": {
            "description": "Common expressions transitioning to moderate vocabulary",
            "word_count_range": "1500-2500 words known",
            "examples": "interesting, agree, opinion, suggest, improve, actually",
            "restrictions": "Limited phrasal verbs, avoid complex idioms"
        },
        "grammar": {
            "tenses": "Present simple/continuous, past simple/continuous, present perfect (basic), going to/will",
            "structures": "Simple compound/complex sentences, basic comparatives, some relative clauses",
            "connectors": "and, but, because, so, however, also, first, then, finally",
            "restrictions": "No past perfect, limited passive, no third conditional"
        },
        "sentence_length": {
            "words_per_sentence": "6-12 words",
            "min": 6,
            "max": 12
        },
        "text_length_multiplier": 0.7,
        "content": {
            "topics": "Travel, work, hobbies, simple opinions, everyday situations",
            "complexity": "Mostly familiar, starting to handle some abstract topics",
            "style": "Clear paragraphs, developing logical structure"
        },
        "conversation": {
            "response_length": "1-2 sentences",
            "pace": "Moderately slow, clear",
            "exchanges_short": "4-6",
            "exchanges_medium": "7-10",
            "exchanges_long": "12-16"
        },
        "assessment": {
            "question_style": "Main ideas, basic inference, vocabulary comprehension",
            "distractors": "Plausible but distinguishable",
            "blanks_per_question": 1,
            "builder_words": "5-10 words",
            "vocab_level": "Common transitional vocabulary",
            "scoring_leniency": "Moderately lenient (60-95)"
        }
    },
    
    "B2": {
        "label": "B2 (Intermediate)",
        "vocabulary": {
            "description": "Rich vocabulary including idioms, phrasal verbs, and formal/informal register",
            "word_count_range": "3500-5000 words known",
            "examples": "substantial, phenomenon, consequently, take into account, come across, break through",
            "restrictions": "Avoid highly specialized academic jargon"
        },
        "grammar": {
            "tenses": "All tenses including past perfect, future continuous, future perfect",
            "structures": "Complex relative clauses, all conditionals (0-3), passive (all forms), reported speech (advanced)",
            "connectors": "nevertheless, furthermore, in spite of, provided that, as long as, whereas",
            "restrictions": "Avoid extremely rare grammatical constructions"
        },
        "sentence_length": {
            "words_per_sentence": "10-18 words",
            "min": 10,
            "max": 18
        },
        "text_length_multiplier": 1.0,
        "content": {
            "topics": "Social issues, science, culture, abstract concepts, professional contexts",
            "complexity": "Abstract reasoning, multiple perspectives, nuanced arguments",
            "style": "Well-developed paragraphs, varied sentence structures, cohesive devices"
        },
        "conversation": {
            "response_length": "2-4 sentences",
            "pace": "Natural pace with varied rhythm",
            "exchanges_short": "6-8",
            "exchanges_medium": "10-14",
            "exchanges_long": "16-22"
        },
        "assessment": {
            "question_style": "Implied meanings, author's intent, text structure, tone analysis",
            "distractors": "Sophisticated, requiring critical analysis",
            "blanks_per_question": 2,
            "builder_words": "10-15 words",
            "vocab_level": "B2 advanced vocabulary",
            "scoring_leniency": "Balanced to strict (50-85 typical range)"
        }
    },
    
    "B1-B2": {
        "label": "B1-B2 (Pre-Int. - Intermediate)",
        "vocabulary": {
            "description": "Expanding from moderate to rich vocabulary, including common idioms",
            "word_count_range": "2500-4000 words known",
            "examples": "apparently, definitely, regarding, deal with, figure out, make sense",
            "restrictions": "Some phrasal verbs and idioms, avoid very technical terms"
        },
        "grammar": {
            "tenses": "All main tenses, present perfect continuous, past perfect (basic), all conditionals (basic)",
            "structures": "Relative clauses, passive voice, basic reported speech, comparatives/superlatives (complex)",
            "connectors": "however, although, despite, as a result, in addition, on the other hand",
            "restrictions": "Limited inversion, avoid very complex clause nesting"
        },
        "sentence_length": {
            "words_per_sentence": "9-16 words",
            "min": 9,
            "max": 16
        },
        "text_length_multiplier": 0.9,
        "content": {
            "topics": "News, education, environment, technology, personal development",
            "complexity": "Both concrete and abstract, developing argumentation skills",
            "style": "Structured paragraphs, growing variety in sentence types"
        },
        "conversation": {
            "response_length": "2-3 sentences",
            "pace": "Natural pace",
            "exchanges_short": "5-7",
            "exchanges_medium": "9-13",
            "exchanges_long": "15-20"
        },
        "assessment": {
            "question_style": "Inference, vocabulary in context, author purpose, basic analysis",
            "distractors": "Plausible, requiring careful analysis",
            "blanks_per_question": 2,
            "builder_words": "8-14 words",
            "vocab_level": "Intermediate transitional vocabulary",
            "scoring_leniency": "Balanced (55-90)"
        }
    },
    
    "C1": {
        "label": "C1 (Upper-Intermediate)",
        "vocabulary": {
            "description": "Sophisticated vocabulary including academic, professional, and literary terms",
            "word_count_range": "5000-8000 words known",
            "examples": "ubiquitous, paradigm, notwithstanding, impeccable, unprecedented, epitomize",
            "restrictions": "None - full range of vocabulary appropriate"
        },
        "grammar": {
            "tenses": "All tenses and aspects used naturally and appropriately",
            "structures": "Inversion, cleft sentences, mixed conditionals, advanced passive, ellipsis",
            "connectors": "inasmuch as, notwithstanding, insofar as, be that as it may, thereby",
            "restrictions": "None"
        },
        "sentence_length": {
            "words_per_sentence": "12-22 words",
            "min": 12,
            "max": 22
        },
        "text_length_multiplier": 1.2,
        "content": {
            "topics": "Academic subjects, complex social issues, philosophy, professional expertise",
            "complexity": "Nuanced arguments, implicit meanings, sophisticated reasoning",
            "style": "Academic register, varied rhetorical devices, precise language"
        },
        "conversation": {
            "response_length": "3-5 sentences",
            "pace": "Fast natural pace with complex structures",
            "exchanges_short": "7-9",
            "exchanges_medium": "12-16",
            "exchanges_long": "18-25"
        },
        "assessment": {
            "question_style": "Critical analysis, evaluation, rhetorical devices, subtle implications",
            "distractors": "Very sophisticated, testing deep comprehension",
            "blanks_per_question": 3,
            "builder_words": "12-18 words",
            "vocab_level": "C1 sophisticated vocabulary",
            "scoring_leniency": "Strict (40-80 typical range)"
        }
    },
    
    "B2-C1": {
        "label": "B2-C1 (Intermediate - Upper-Int.)",
        "vocabulary": {
            "description": "Rich to sophisticated vocabulary, transitioning to academic register",
            "word_count_range": "4000-6500 words known",
            "examples": "comprehensive, inevitable, contribute to, distinguish, rationale, elaborate",
            "restrictions": "Minimally restricted - most vocabulary accessible"
        },
        "grammar": {
            "tenses": "All tenses including perfect continuous forms",
            "structures": "Complex conditionals, some inversion, advanced relative clauses, passive variations",
            "connectors": "nevertheless, furthermore, notwithstanding, provided that, insofar as",
            "restrictions": "Limited use of very rare structures"
        },
        "sentence_length": {
            "words_per_sentence": "11-20 words",
            "min": 11,
            "max": 20
        },
        "text_length_multiplier": 1.1,
        "content": {
            "topics": "Professional, academic, social commentary, cultural analysis",
            "complexity": "Advanced reasoning, multiple viewpoints, nuanced analysis",
            "style": "Academic and professional writing, sophisticated cohesion"
        },
        "conversation": {
            "response_length": "2-4 sentences",
            "pace": "Fast, natural rhythm",
            "exchanges_short": "6-8",
            "exchanges_medium": "11-15",
            "exchanges_long": "17-23"
        },
        "assessment": {
            "question_style": "Analysis, synthesis, implied meanings, evaluation",
            "distractors": "Sophisticated, requiring nuanced understanding",
            "blanks_per_question": 2,
            "builder_words": "11-16 words",
            "vocab_level": "Advanced transitional vocabulary",
            "scoring_leniency": "Moderately strict (45-85)"
        }
    },
    
    "C2": {
        "label": "C2 (Advanced)",
        "vocabulary": {
            "description": "Near-native vocabulary including rare, literary, colloquial and domain-specific terms",
            "word_count_range": "8000+ words known",
            "examples": "ephemeral, pragmatic, juxtapose, quintessential, serendipity, dichotomy",
            "restrictions": "None"
        },
        "grammar": {
            "tenses": "All tenses with nuanced aspect distinctions",
            "structures": "All structures including rare forms, stylistic inversion, fronting, any complexity",
            "connectors": "Full range including formal, literary, and archaic connectors",
            "restrictions": "None"
        },
        "sentence_length": {
            "words_per_sentence": "14-25+ words",
            "min": 14,
            "max": 25
        },
        "text_length_multiplier": 1.3,
        "content": {
            "topics": "Any topic including specialized academic, literary criticism, abstract philosophy",
            "complexity": "Highest complexity, subtle humor, cultural nuances, implicit reasoning",
            "style": "Full stylistic range, literary techniques, rhetorical mastery"
        },
        "conversation": {
            "response_length": "3-6 sentences",
            "pace": "Fast, sophisticated, natural native-like pace",
            "exchanges_short": "8-10",
            "exchanges_medium": "14-18",
            "exchanges_long": "20-30"
        },
        "assessment": {
            "question_style": "Critical evaluation, argumentation analysis, stylistic analysis, assumption testing",
            "distractors": "Extremely sophisticated near-synonyms, testing precise understanding",
            "blanks_per_question": 3,
            "builder_words": "14-22 words",
            "vocab_level": "C2 near-native vocabulary",
            "scoring_leniency": "Very strict (30-75 typical range)"
        }
    },
    
    "C1-C2": {
        "label": "C1-C2 (Upper-Int. - Advanced)",
        "vocabulary": {
            "description": "Sophisticated to near-native vocabulary, full range of expression",
            "word_count_range": "6500-8000+ words known",
            "examples": "eloquent, meticulous, paradox, alleviate, exacerbate, nuance",
            "restrictions": "None"
        },
        "grammar": {
            "tenses": "All tenses with full aspect control",
            "structures": "Inversion, cleft sentences, mixed conditionals, ellipsis, fronting, all complexities",
            "connectors": "Full academic and literary range",
            "restrictions": "None"
        },
        "sentence_length": {
            "words_per_sentence": "13-24 words",
            "min": 13,
            "max": 24
        },
        "text_length_multiplier": 1.25,
        "content": {
            "topics": "Academic, professional, literary, philosophical, any domain",
            "complexity": "Highest complexity, implicit meanings, sophisticated arguments",
            "style": "Full stylistic range, academic and literary excellence"
        },
        "conversation": {
            "response_length": "3-5 sentences",
            "pace": "Fast natural native-like pace",
            "exchanges_short": "7-10",
            "exchanges_medium": "13-17",
            "exchanges_long": "19-28"
        },
        "assessment": {
            "question_style": "Critical analysis, evaluation, synthesis, stylistic analysis",
            "distractors": "Extremely sophisticated, testing precise nuanced understanding",
            "blanks_per_question": 3,
            "builder_words": "13-20 words",
            "vocab_level": "C1-C2 sophisticated vocabulary",
            "scoring_leniency": "Very strict (35-78)"
        }
    },
}


def get_cefr_spec(level: str) -> Dict[str, Any]:
    """
    Get the full CEFR specification for a given level.
    
    Args:
        level: CEFR level string (e.g., "A1", "B1-B2", "C2")
        
    Returns:
        Dictionary with all specifications for the level.
    """
    level = level.upper().strip()
    if level not in CEFR_SPECS:
        raise ValueError(f"Invalid CEFR level: {level}. Valid levels: {', '.join(CEFR_SPECS.keys())}")
    return CEFR_SPECS[level]


def get_difficulty_prompt(level: str) -> str:
    """
    Generate a standardized difficulty instruction block for LLM prompts.
    Used by all content generators to ensure consistent CEFR-based content.
    
    Args:
        level: CEFR level string
        
    Returns:
        Formatted string with vocabulary, grammar, and style instructions.
    """
    spec = get_cefr_spec(level)
    
    vocab = spec["vocabulary"]
    grammar = spec["grammar"]
    sent = spec["sentence_length"]
    content = spec["content"]
    
    return f"""CEFR Level: {level} - {spec['label']}

VOCABULARY REQUIREMENTS:
- Level: {vocab['description']}
- Known vocabulary range: {vocab['word_count_range']}
- Example words appropriate for this level: {vocab['examples']}
- Restrictions: {vocab['restrictions']}

GRAMMAR REQUIREMENTS:
- Allowed tenses: {grammar['tenses']}
- Allowed structures: {grammar['structures']}
- Connectors to use: {grammar['connectors']}
- Grammar restrictions: {grammar['restrictions']}

SENTENCE LENGTH:
- Target: {sent['words_per_sentence']} per sentence
- Minimum: {sent['min']} words, Maximum: {sent['max']} words

CONTENT STYLE:
- Appropriate topics: {content['topics']}
- Complexity level: {content['complexity']}
- Writing style: {content['style']}"""


def get_conversation_prompt(level: str) -> str:
    """
    Generate conversation-specific difficulty instructions.
    Used by Practice and Listening modules.
    
    Args:
        level: CEFR level string
        
    Returns:
        Formatted string with conversation parameters.
    """
    spec = get_cefr_spec(level)
    conv = spec["conversation"]
    vocab = spec["vocabulary"]
    grammar = spec["grammar"]
    sent = spec["sentence_length"]
    
    return f"""CEFR Level: {level} - {spec['label']}

CONVERSATION STYLE:
- Response length: {conv['response_length']}
- Pace: {conv['pace']}

VOCABULARY:
- Level: {vocab['description']}
- Restrictions: {vocab['restrictions']}

GRAMMAR:
- Allowed tenses: {grammar['tenses']}
- Structures: {grammar['structures']}
- Restrictions: {grammar['restrictions']}

SENTENCE LENGTH: {sent['words_per_sentence']} per sentence"""


def get_assessment_prompt(level: str) -> str:
    """
    Generate assessment-specific difficulty instructions.
    Used by question generators and writing analyzer.
    
    Args:
        level: CEFR level string
        
    Returns:
        Formatted string with assessment parameters.
    """
    spec = get_cefr_spec(level)
    assess = spec["assessment"]
    
    return f"""CEFR Level: {level} - {spec['label']}

QUESTION DESIGN:
- Question style: {assess['question_style']}
- Distractor quality: {assess['distractors']}
- Fill-in-blank: {assess['blanks_per_question']} blank(s) per question
- Sentence builder: {assess['builder_words']}
- Vocabulary level: {assess['vocab_level']}

SCORING:
- Leniency: {assess['scoring_leniency']}"""


def get_label_from_value(value: str) -> str:
    """Get the human-readable label for a CEFR value."""
    return CEFR_LABELS.get(value, value)


def get_value_from_label(label: str) -> str:
    """Get the CEFR value from a human-readable label."""
    for value, lbl in CEFR_LABELS.items():
        if lbl == label:
            return value
    return label
