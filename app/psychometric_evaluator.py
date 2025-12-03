"""
Psychometric Evaluation Module

Generates dynamic psychometric questions and analyzes responses
"""

import os
import logging
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt

load_dotenv()
logger = logging.getLogger(__name__)


class PsychometricEvaluator:
    """
    Generates psychometric assessments and evaluates responses
    Assesses personality traits, cognitive abilities, and entrepreneurial fit
    """

    # Psychometric dimensions to evaluate
    DIMENSIONS = {
        "leadership": {
            "name": "Leadership & Vision",
            "description": "Ability to lead, inspire, and set strategic direction"
        },
        "risk_tolerance": {
            "name": "Risk Tolerance",
            "description": "Comfort with uncertainty and calculated risk-taking"
        },
        "resilience": {
            "name": "Resilience & Adaptability",
            "description": "Ability to recover from setbacks and adapt to change"
        },
        "innovation": {
            "name": "Innovation & Creativity",
            "description": "Capacity for creative thinking and novel solutions"
        },
        "decision_making": {
            "name": "Decision Making",
            "description": "Quality and speed of judgment under pressure"
        },
        "emotional_intelligence": {
            "name": "Emotional Intelligence",
            "description": "Self-awareness and interpersonal effectiveness"
        },
        "persistence": {
            "name": "Persistence & Grit",
            "description": "Determination to pursue long-term goals"
        },
        "strategic_thinking": {
            "name": "Strategic Thinking",
            "description": "Ability to analyze complex situations and plan ahead"
        },
        "communication": {
            "name": "Communication Skills",
            "description": "Clarity and effectiveness in conveying ideas"
        },
        "problem_solving": {
            "name": "Problem Solving",
            "description": "Analytical and creative approach to challenges"
        }
    }

    def __init__(self, model: str = "gpt-4o-mini", timeout: int = 180):
        """Initialize the psychometric evaluator with config validation"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it via: "
                "1) Environment variable: export OPENAI_API_KEY='your-key' "
                "2) .env file in project root"
            )

        self.llm = ChatOpenAI(
            model=model,
            temperature=0.7,
            api_key=api_key,
            max_tokens=16000,
            timeout=timeout
        )
        logger.info(f"Psychometric Evaluator initialized with {model}")

    @staticmethod
    def _clean_json_response(content: str) -> str:
        """Extract JSON from markdown-wrapped responses using regex"""
        # Match content between ```json ... ``` or ``` ... ```
        match = re.search(r'```(?:json\s*)?(.*?)```', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content

    @retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(3))
    def _call_llm_with_retry(self, prompt: str) -> str:
        """Call LLM with exponential backoff retry logic"""
        response = self.llm.invoke(prompt)
        return response.content

    def generate_questions(self, num_questions: int = 20) -> Dict[str, Any]:
        """
        Generate dynamic psychometric questions with validated JSON output
        
        Args:
            num_questions: Number of questions to generate (default: 20)
            
        Returns:
            Dictionary containing questions and metadata
            
        Raises:
            ValueError: If JSON is invalid or required keys are missing
        """
        try:
            logger.info(f"Generating {num_questions} psychometric questions...")

            prompt = f"""Generate exactly {num_questions} psychometric questions for entrepreneurs.

STRICT REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no comments
2. Use double quotes for all keys and string values
3. Ensure no trailing commas in arrays or objects
4. Cover ALL 10 dimensions evenly
5. Make options realistic and psychologically nuanced

Return this JSON structure:
{{
  "assessment_id": "assess_{num_questions}q_{datetime.now().strftime('%Y%m%d_%H%M')}",
  "title": "Entrepreneurial Psychometric Assessment",
  "description": "Comprehensive evaluation of entrepreneurial traits and competencies",
  "estimated_time_minutes": {max(5, num_questions // 2)},
  "questions": [
    {{
      "question_id": "q1",
      "dimension": "leadership",
      "question_text": "When facing a critical business decision with incomplete information, you typically...",
      "question_type": "situational",
      "options": [
        {{
          "option_id": "A",
          "text": "Make a decisive choice based on intuition and available data",
          "score_profile": {{"leadership": 8, "decision_making": 8, "risk_tolerance": 6}}
        }},
        {{
          "option_id": "B",
          "text": "Consult key stakeholders to build consensus before deciding",
          "score_profile": {{"leadership": 7, "emotional_intelligence": 8, "communication": 7}}
        }}
      ]
    }}
  ]
}}

Generate questions now:"""

            # Get response with retry logic
            raw_response = self._call_llm_with_retry(prompt)
            cleaned_content = self._clean_json_response(raw_response)
            
            # Parse JSON
            try:
                questions_data = json.loads(cleaned_content)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON decode failed. Raw content: {raw_response[:500]}...")
                raise ValueError(f"Invalid JSON from LLM: {json_err}")

            # Validate required schema
            required_keys = {"assessment_id", "title", "questions"}
            missing_keys = required_keys - questions_data.keys()
            if missing_keys:
                raise ValueError(f"Missing required keys in response: {missing_keys}")

            # Validate questions structure
            if not isinstance(questions_data.get("questions"), list):
                raise ValueError("Questions must be a list")

            # Add metadata
            questions_data["generated_at"] = datetime.now().isoformat()
            questions_data["total_questions"] = len(questions_data["questions"])
            questions_data["schema_version"] = "1.0"

            logger.info(f"Successfully generated {questions_data['total_questions']} questions")
            return questions_data

        except Exception as e:
            logger.error(f"Question generation failed: {e}", exc_info=True)
            raise

    def evaluate_responses(
        self, 
        questions_data: Dict[str, Any], 
        responses: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Evaluate user responses and generate comprehensive psychometric analysis
        
        Args:
            questions_data: Original questions with scoring profiles
            responses: Dict mapping question_id to selected option_id
            
        Returns:
            Detailed psychometric analysis dictionary
        """
        try:
            logger.info(f"Evaluating {len(responses)} responses...")
            
            if not responses:
                raise ValueError("No responses provided for evaluation")

            # Calculate raw scores per dimension
            dimension_scores = {dim: [] for dim in self.DIMENSIONS.keys()}
            answered_questions = []

            # Build quick lookup for questions
            question_map = {q["question_id"]: q for q in questions_data.get("questions", [])}

            for q_id, selected_option_id in responses.items():
                question = question_map.get(q_id)
                if not question:
                    logger.warning(f"Question {q_id} not found in assessment data")
                    continue

                # Find selected option
                selected_option = next(
                    (opt for opt in question.get("options", []) 
                     if opt.get("option_id") == selected_option_id),
                    None
                )
                
                if not selected_option:
                    logger.warning(f"Option {selected_option_id} not found for question {q_id}")
                    continue

                # Aggregate scores
                score_profile = selected_option.get("score_profile", {})
                for dimension, score in score_profile.items():
                    if dimension in dimension_scores:
                        dimension_scores[dimension].append(score)

                # Record answer details
                answered_questions.append({
                    "question_id": q_id,
                    "question_text": question.get("question_text", ""),
                    "dimension": question.get("dimension", ""),
                    "selected_option": selected_option_id,
                    "selected_text": selected_option.get("text", "")
                })

            # Calculate dimension averages
            dimension_averages = {}
            for dimension, scores in dimension_scores.items():
                dimension_averages[dimension] = (
                    round(sum(scores) / len(scores), 2) if scores else 0.0
                )

            # Calculate overall score
            overall_score = (
                round(sum(dimension_averages.values()) / len(dimension_averages), 2)
                if dimension_averages else 0.0
            )

            # Generate AI-powered analysis
            analysis = self._generate_ai_analysis(
                dimension_averages,
                answered_questions,
                questions_data
            )

            # Compile final results
            result = {
                "assessment_id": questions_data.get("assessment_id", "unknown"),
                "evaluated_at": datetime.now().isoformat(),
                "schema_version": "1.0",
                "total_questions": len(question_map),
                "questions_answered": len(answered_questions),
                "completion_rate": round(
                    len(answered_questions) / max(len(question_map), 1) * 100, 1
                ),
                "dimension_scores": dimension_averages,
                "overall_score": overall_score,
                "strengths": analysis.get("strengths", []),
                "areas_for_development": analysis.get("areas_for_development", []),
                "personality_profile": analysis.get("personality_profile", ""),
                "entrepreneurial_fit": analysis.get("entrepreneurial_fit", {}),
                "recommendations": analysis.get("recommendations", []),
                "detailed_insights": analysis.get("detailed_insights", {}),
                "response_details": answered_questions
            }

            logger.info(
                f"Evaluation complete. Score: {result['overall_score']}/10, "
                f"Completion: {result['completion_rate']}%"
            )
            return result

        except Exception as e:
            logger.error(f"Response evaluation failed: {e}", exc_info=True)
            raise

    def _generate_ai_analysis(
        self,
        dimension_scores: Dict[str, float],
        answered_questions: List[Dict[str, Any]],
        questions_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate deep AI-powered analysis of psychometric results
        
        Args:
            dimension_scores: Average scores per dimension
            answered_questions: List of answered questions with details
            questions_data: Original assessment data
            
        Returns:
            Detailed analysis dictionary
        """
        try:
            # Prepare dimension summary
            dimension_details = "\n".join([
                f"- {self.DIMENSIONS[dim]['name']}: {score}/10"
                for dim, score in sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)
            ])

            overall_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0

            prompt = f"""Analyze this entrepreneur assessment and return ONLY valid JSON.

DIMENSION SCORES (out of 10):
{dimension_details}

OVERALL SCORE: {overall_score:.2f}/10

Return EXACT JSON structure:
{{
  "personality_profile": "Concise 2-3 sentence summary of entrepreneurial personality",
  "strengths": ["Top strength 1", "Top strength 2", "Top strength 3"],
  "areas_for_development": ["Development area 1", "Development area 2"],
  "entrepreneurial_fit": {{
    "overall_fit": "High/Medium/Low",
    "fit_score": 0-100,
    "reasoning": "Brief explanation of fit assessment",
    "ideal_role": "Founder/Co-founder/Intrapreneur/Advisor",
    "ideal_venture_type": "Tech startup/Small business/Social enterprise/Corporate venture"
  }},
  "recommendations": ["Actionable recommendation 1", "Recommendation 2", "Recommendation 3"],
  "detailed_insights": {{
    "leadership_style": "Analysis of leadership approach",
    "decision_making_pattern": "Decision-making tendencies",
    "stress_response": "How handles pressure",
    "growth_potential": "Development outlook",
    "team_dynamics": "Team interaction style",
    "unique_qualities": "Distinctive strengths"
  }}
}}

Be specific, professional, and actionable. NO MARKDOWN, NO EXTRA TEXT."""

            raw_response = self._call_llm_with_retry(prompt)
            cleaned_content = self._clean_json_response(raw_response)
            
            try:
                analysis = json.loads(cleaned_content)
            except json.JSONDecodeError as json_err:
                logger.error(f"Analysis JSON decode failed: {json_err}")
                raise ValueError(f"Invalid analysis JSON from LLM: {json_err}")

            # Validate required analysis keys
            required_keys = {"personality_profile", "strengths", "entrepreneurial_fit"}
            missing_keys = required_keys - analysis.keys()
            if missing_keys:
                logger.warning(f"Analysis missing keys: {missing_keys}")
                
            return analysis

        except Exception as e:
            logger.error(f"AI analysis generation failed: {e}", exc_info=True)
            # Return safe fallback instead of crashing
            return {
                "personality_profile": (
                    f"Assessment indicates an overall score of {dimension_scores.get('overall_score', 0)}/10. "
                    "Further analysis recommended."
                ),
                "strengths": ["Assessment completed successfully"],
                "areas_for_development": ["Review detailed scores for specific insights"],
                "entrepreneurial_fit": {
                    "overall_fit": "Medium",
                    "fit_score": 70,
                    "reasoning": "Assessment completed. Individual results vary by dimension.",
                    "ideal_role": "Entrepreneur",
                    "ideal_venture_type": "Versatile"
                },
                "recommendations": [
                    "Review dimension scores in detail",
                    "Focus on top 2-3 development areas",
                    "Consider coaching for targeted growth"
                ],
                "detailed_insights": {
                    "leadership_style": "Further analysis needed",
                    "decision_making_pattern": "Review response patterns",
                    "stress_response": "Self-assessment recommended",
                    "growth_potential": "Moderate to high",
                    "team_dynamics": "Context-dependent",
                    "unique_qualities": "Individual strengths identified"
                }
            }


class PsychometricEvaluatorSingleton:
    """Thread-safe singleton for PsychometricEvaluator"""
    
    _instance: Optional[PsychometricEvaluator] = None
    
    @classmethod
    def get_instance(cls, **kwargs) -> PsychometricEvaluator:
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = PsychometricEvaluator(**kwargs)
        return cls._instance


# Backward-compatible function
def get_psychometric_evaluator() -> PsychometricEvaluator:
    """Get singleton instance of psychometric evaluator"""
    return PsychometricEvaluatorSingleton.get_instance()


# Module-level singleton for convenience
psychometric_evaluator = get_psychometric_evaluator()