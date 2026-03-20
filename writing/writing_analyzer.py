"""
Writing Analyzer
Analyzes user's written responses and provides detailed feedback.
"""

import json
import os
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from together import Together

from cefr_config import get_cefr_spec, get_difficulty_prompt


@dataclass
class ErrorDetail:
    """Details about a single error."""
    original_sentence: str
    corrected_sentence: str
    error_type: str
    note: str


@dataclass
class Scores:
    """Scores for different aspects."""
    grammar: int
    fluency: int
    vocabulary: int
    structure: int
    task_completion: int
    overall: int


@dataclass 
class AnalysisResult:
    """Complete analysis result."""
    errors: List[ErrorDetail]
    scores: Scores
    strengths: List[str]
    areas_for_improvement: List[str]
    tips_feedback: Optional[List[str]] = None


class WritingAnalyzer:
    """
    Analyzes written responses using Together AI.
    Provides detailed feedback on grammar, vocabulary, style, and structure.
    """
    
    MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer with API key."""
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY is required")
        self.client = Together(api_key=self.api_key)
    
    def _build_analysis_prompt(
        self,
        task_instruction: str,
        user_response: str,
        target_tense: Optional[str] = None,
        target_vocabulary: Optional[List[str]] = None,
        target_grammar: Optional[List[str]] = None,
        additional_details: Optional[str] = None,
        difficulty: str = "B1",
        tips: Optional[List[str]] = None,
        rag_context: Optional[str] = None
    ) -> str:
        """Build the prompt for analysis."""
        
        # Get CEFR-specific evaluation criteria
        spec = get_cefr_spec(difficulty)
        scoring_leniency = spec.get("assessment", {}).get("scoring_leniency", "balanced")
        
        leniency_map = {
            "very lenient": "Be VERY LENIENT in your evaluation. Focus on basic communication. Even significant grammar mistakes are acceptable if the meaning is clear. Score very generously (80-100 for decent attempts).",
            "lenient": "Be LENIENT in your evaluation. Focus on communication over accuracy. Minor grammar mistakes are acceptable if the meaning is clear. Score generously (70-100 for decent attempts).",
            "moderate": "Be MODERATE in your evaluation. Expect reasonable grammar and vocabulary usage. Some errors are acceptable but should be noted. Score in the 60-90 range typically.",
            "balanced": "Be BALANCED in your evaluation. Expect good grammar and vocabulary usage. Errors should be noted and affect scoring. Score in the 50-85 range typically.",
            "moderately strict": "Be MODERATELY STRICT in your evaluation. Expect strong grammar, good vocabulary range, and proper style. Most errors should be noted. Score in the 40-80 range typically.",
            "strict": "Be STRICT in your evaluation. Expect excellent grammar, sophisticated vocabulary, and proper style. Even minor errors should be noted. Score in the 30-75 range typically.",
            "very strict": "Be VERY STRICT in your evaluation. Expect near-native level grammar, advanced vocabulary, nuanced style, and complex structures. All errors must be noted. Score in the 20-70 range typically."
        }
        
        eval_criteria = leniency_map.get(scoring_leniency, leniency_map["balanced"])
        cefr_instructions = get_difficulty_prompt(difficulty)
        
        prompt = f"""You are an expert English writing teacher analyzing a student's writing.

CEFR LEVEL: {difficulty}
{cefr_instructions}

EVALUATION CRITERIA: {eval_criteria}

WRITING TASK:
{task_instruction}

STUDENT'S RESPONSE:
{user_response}

"""
        if target_tense:
            prompt += f"TARGET TENSE TO PRACTICE: {target_tense}\n"
        
        if target_vocabulary:
            prompt += f"""⚠️ MANDATORY VOCABULARY CHECK: {', '.join(target_vocabulary)}
CRITICAL: Check whether the student used these vocabulary words. At least 70-80% of them MUST be present in the writing. List which words were used and which were missing. Deduct points if too many are missing.
"""
        
        if target_grammar:
            prompt += f"""⚠️ MANDATORY GRAMMAR CHECK: {', '.join(target_grammar)}
CRITICAL: Check whether the student used ALL of these grammar structures. EVERY grammar pattern must appear at least once. List which structures were used correctly, which were used incorrectly, and which were completely missing. Deduct points for missing grammar structures.
"""
        
        if additional_details:
            prompt += f"ADDITIONAL REQUIREMENTS: {additional_details}\n"
        
        if tips:
            prompt += f"TIPS GIVEN TO STUDENT: {'; '.join(tips)}\n"
        
        prompt += """
Analyze the student's writing and provide feedback in the following JSON format:

{
    "errors": [
        {
            "original_sentence": "The COMPLETE original sentence. Mark ONLY the exact wrong word(s) as [wrong]word[wrong]",
            "corrected_sentence": "The COMPLETE corrected sentence. Mark ONLY the exact replacement word(s) as [correct]word[correct]",
            "error_type": "grammar|vocabulary|style|punctuation|spelling|word_order|tense|article|preposition",
            "note": "Brief explanation in English of why this was wrong and how to fix it"
        }
    ],
    "scores": {
        "grammar": 85,
        "fluency": 80,
        "vocabulary": 75,
        "structure": 90,
        "task_completion": 85,
        "overall": 83
    },
    "strengths": [
        "Strength 1",
        "Strength 2"
    ],
    "areas_for_improvement": [
        "Area 1",
        "Area 2"
    ],
    "tips_feedback": [
        "Feedback on tip 1: followed/not followed and why",
        "Feedback on tip 2: followed/not followed and why"
    ]
}

ABSOLUTELY CRITICAL ERROR MARKING RULES:

1. ONLY report errors where there is an ACTUAL CHANGE between original and corrected
2. DO NOT include "errors" where the corrected_sentence is identical to original_sentence
3. DO NOT include style suggestions or "could be better" feedback as errors - only ACTUAL mistakes

4. Mark [wrong] and [correct] PRECISELY around ONLY the changed word(s):
   - WRONG: "I have [wrong]work[wrong] at my company for 5 years."
   - CORRECT: "I have [correct]worked[correct] at my company for 5 years."
   
5. The [wrong] and [correct] tags must wrap ONLY the minimal changed portion:
   - If only one word changes: [wrong]word[wrong] → [correct]newword[correct]
   - If a phrase changes: [wrong]old phrase[wrong] → [correct]new phrase[correct]

6. GOOD EXAMPLES:
   Original: "I [wrong]am work[wrong] here for 5 years."
   Corrected: "I [correct]have worked[correct] here for 5 years."
   
   Original: "She [wrong]go[wrong] to school yesterday."
   Corrected: "She [correct]went[correct] to school yesterday."
   
   Original: "I am interested [wrong]to[wrong] this job."
   Corrected: "I am interested [correct]in[correct] this job."

7. BAD EXAMPLES (DO NOT DO THIS):
   - DO NOT mark entire sentences when only a word is wrong
   - DO NOT include errors where original and corrected are the same
   - DO NOT suggest alternatives without marking actual errors
   - DO NOT report "style" improvements unless there's a concrete error

8. If a sentence is wordy but grammatically correct, DO NOT include it as an error
9. If you would suggest a different word but the original is acceptable, DO NOT include it
10. ONLY include entries in "errors" array where corrected_sentence is DIFFERENT from original_sentence

11. error_type must be one of: grammar, vocabulary, style, punctuation, spelling, word_order, tense, article, preposition
12. Adjust scores based on CEFR level:
    - A1/A2: be very generous (70-100 for decent attempts)
    - B1: balanced scoring (60-90 typical range)
    - B2/C1: moderately strict (40-80 typical range)
    - C2: strict scoring (lower scores for any errors)
13. Provide 1-5 strengths and 1-5 areas for improvement
14. If tips were provided, evaluate whether each tip was followed in tips_feedback
15. Write all notes and feedback in English

Return ONLY valid JSON, no additional text or explanation outside the JSON.
"""

        if rag_context:
            prompt += rag_context + "\n"

        return prompt
    
    def analyze(
        self,
        task_instruction: str,
        user_response: str,
        target_tense: Optional[str] = None,
        target_vocabulary: Optional[List[str]] = None,
        target_grammar: Optional[List[str]] = None,
        additional_details: Optional[str] = None,
        difficulty: str = "B1",
        tips: Optional[List[str]] = None,
        rag_context: Optional[str] = None
    ) -> AnalysisResult:
        """Analyze a user's written response."""
        
        prompt = self._build_analysis_prompt(
            task_instruction=task_instruction,
            user_response=user_response,
            target_tense=target_tense,
            target_vocabulary=target_vocabulary,
            target_grammar=target_grammar,
            additional_details=additional_details,
            difficulty=difficulty,
            tips=tips,
            rag_context=rag_context
        )
        
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert English writing teacher. Analyze student writing carefully and provide detailed, constructive feedback. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=3000,
            temperature=0.3  # Lower temperature for more consistent analysis
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Response text: {response_text}")
            # Return a default result if parsing fails
            return self._default_result()
        
        # Parse errors
        errors = []
        for err in result.get("errors", []):
            errors.append(ErrorDetail(
                original_sentence=err.get("original_sentence", ""),
                corrected_sentence=err.get("corrected_sentence", ""),
                error_type=err.get("error_type", "grammar"),
                note=err.get("note", "")
            ))
        
        # Parse scores
        scores_data = result.get("scores", {})
        scores = Scores(
            grammar=scores_data.get("grammar", 70),
            fluency=scores_data.get("fluency", 70),
            vocabulary=scores_data.get("vocabulary", 70),
            structure=scores_data.get("structure", 70),
            task_completion=scores_data.get("task_completion", 70),
            overall=scores_data.get("overall", 70)
        )
        
        # Get strengths and areas for improvement
        strengths = result.get("strengths", ["Good effort"])
        areas_for_improvement = result.get("areas_for_improvement", ["Continue practicing"])
        
        # Tips feedback
        tips_feedback = result.get("tips_feedback")
        
        return AnalysisResult(
            errors=errors,
            scores=scores,
            strengths=strengths[:5],  # Limit to 5
            areas_for_improvement=areas_for_improvement[:5],  # Limit to 5
            tips_feedback=tips_feedback
        )
    
    def _default_result(self) -> AnalysisResult:
        """Return a default result when analysis fails."""
        return AnalysisResult(
            errors=[],
            scores=Scores(
                grammar=70,
                fluency=70,
                vocabulary=70,
                structure=70,
                task_completion=70,
                overall=70
            ),
            strengths=["Unable to fully analyze the text"],
            areas_for_improvement=["Please try again with a different text"],
            tips_feedback=None
        )
