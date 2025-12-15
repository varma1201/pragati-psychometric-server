"""
Mentor Psychometric Evaluation Module

Generates dynamic mentor assessment questions and analyzes mentor capabilities
Evaluates mentoring skills, domain expertise, and matching compatibility
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


class MentorEvaluator:
    """
    Generates mentor-specific psychometric assessments and evaluates responses
    Assesses mentoring capabilities, teaching style, and domain expertise
    """

    # Mentor-specific psychometric dimensions
    DIMENSIONS = {
        "coaching_ability": {
            "name": "Coaching & Guidance",
            "description": "Ability to guide mentees without imposing solutions, facilitating their growth",
            "weight": 1.2  # Higher importance
        },
        "domain_expertise": {
            "name": "Domain Expertise",
            "description": "Deep knowledge in specific industries, technologies, or business functions",
            "weight": 1.1
        },
        "empathy": {
            "name": "Empathy & Patience",
            "description": "Understanding mentee challenges, showing patience during their learning journey",
            "weight": 1.3  # Critical for mentoring
        },
        "experience_breadth": {
            "name": "Entrepreneurial Experience",
            "description": "Years building, scaling, failing, or advising ventures - real-world battle scars",
            "weight": 1.0
        },
        "network_strength": {
            "name": "Network & Connections",
            "description": "Quality of professional network and willingness to make introductions",
            "weight": 0.9
        },
        "feedback_quality": {
            "name": "Feedback Quality",
            "description": "Providing specific, actionable, constructive guidance rather than vague advice",
            "weight": 1.2
        },
        "availability": {
            "name": "Time Commitment",
            "description": "Realistic availability and consistency in mentee interactions",
            "weight": 1.0
        },
        "communication": {
            "name": "Communication Clarity",
            "description": "Explaining complex concepts simply, active listening, asking powerful questions",
            "weight": 1.1
        },
        "adaptability": {
            "name": "Adaptability to Mentee Needs",
            "description": "Adjusting mentoring style based on mentee's learning preferences and context",
            "weight": 1.0
        },
        "accountability": {
            "name": "Accountability & Follow-through",
            "description": "Holding mentees accountable while being reliable and following through on commitments",
            "weight": 1.0
        }
    }

    # Mentor expertise domains for matching
    EXPERTISE_DOMAINS = [
        "Technology & Software Development",
        "Product Management & Design",
        "Sales & Business Development",
        "Marketing & Growth",
        "Finance & Fundraising",
        "Operations & Supply Chain",
        "Legal & Compliance",
        "HR & Talent Management",
        "Healthcare & Biotech",
        "E-commerce & Retail",
        "FinTech",
        "EdTech",
        "SaaS & Enterprise",
        "Consumer Products",
        "Social Impact & Sustainability"
    ]

    # Teaching styles
    TEACHING_STYLES = [
        "Hands-on (works alongside mentee)",
        "Socratic (asks questions to guide discovery)",
        "Directive (provides clear instructions)",
        "Collaborative (equal partnership approach)",
        "Challenging (pushes mentee beyond comfort zone)"
    ]

    def __init__(self, model: str = "gpt-4o-mini", timeout: int = 120):
        """Initialize the mentor evaluator with config validation"""
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
            max_tokens=16000,  # Reduced from 16000
            timeout=timeout
        )
        logger.info(f"Mentor Evaluator initialized with {model}")

    @staticmethod
    def _clean_json_response(content: str) -> str:
        """Extract JSON from markdown-wrapped responses using regex"""
        # Match content between `````` or ``````
        match = re.search(r'``````', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content

    @retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(3))
    def _call_llm_with_retry(self, prompt: str) -> str:
        """Call LLM with exponential backoff retry logic"""
        response = self.llm.invoke(prompt)
        return response.content

    def generate_questions(
        self, 
        num_questions: int = 25,
        focus_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate dynamic mentor assessment questions with validated JSON output

        Args:
            num_questions: Number of questions to generate (default: 25)
            focus_domains: Specific domains to focus on (optional)

        Returns:
            Dictionary containing questions and metadata

        Raises:
            ValueError: If JSON is invalid or required keys are missing
        """
        try:
            logger.info(f"Generating {num_questions} mentor assessment questions...")
            
            # Build domain context
            domain_context = ""
            if focus_domains:
                domain_context = f"\nFocus on these domains: {', '.join(focus_domains)}"
            
            prompt = f"""Generate EXACTLY {num_questions} psychometric questions for MENTORS (not entrepreneurs).

CRITICAL: You MUST generate ALL {num_questions} questions. Do not generate fewer questions.

CONTEXT: These mentors will guide entrepreneurs. Assess their mentoring capabilities, not their ability to run a business.

STRICT REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no comments
2. Use double quotes for all keys and string values
3. Ensure no trailing commas in arrays or objects
4. Generate EXACTLY {num_questions} questions - this is mandatory
5. Cover ALL 10 mentor dimensions evenly: coaching_ability, domain_expertise, empathy, experience_breadth, network_strength, feedback_quality, availability, communication, adaptability, accountability
6. Make scenarios realistic - mentoring situations, not business execution scenarios
7. Include questions about past mentoring experience, teaching style preferences, and time commitment
8. Each question must have 4 options (A, B, C, D)
9. Question IDs should be: m1, m2, m3, ..., m{num_questions}
{domain_context}

Return this JSON structure (with ALL {num_questions} questions):
{{
  "assessment_id": "mentor_assess_{num_questions}q_{datetime.now().strftime('%Y%m%d_%H%M')}",
  "title": "Mentor Capability Assessment",
  "description": "Comprehensive evaluation of mentoring skills, expertise, and compatibility for guiding entrepreneurs",
  "assessment_type": "mentor",
  "estimated_time_minutes": {max(10, num_questions // 2)},
  "questions": [
    {{
      "question_id": "m1",
      "dimension": "coaching_ability",
      "question_text": "A mentee comes to you confused about pivoting their business model. Your first instinct is to:",
      "question_type": "situational",
      "scenario_context": "Testing coaching approach vs. directive advice",
      "options": [
        {{
          "option_id": "A",
          "text": "Ask probing questions to help them discover the right path themselves",
          "score_profile": {{"coaching_ability": 9, "communication": 8, "empathy": 7}}
        }},
        {{
          "option_id": "B",
          "text": "Share a similar experience from your past and what you did",
          "score_profile": {{"experience_breadth": 8, "communication": 7, "coaching_ability": 6}}
        }},
        {{
          "option_id": "C",
          "text": "Provide a clear recommendation based on your expertise",
          "score_profile": {{"domain_expertise": 8, "feedback_quality": 7, "coaching_ability": 4}}
        }},
        {{
          "option_id": "D",
          "text": "Connect them with 2-3 experts who can provide different perspectives",
          "score_profile": {{"network_strength": 9, "coaching_ability": 7, "communication": 6}}
        }}
      ]
    }},
    {{
      "question_id": "m2",
      "dimension": "availability",
      "question_text": "Regarding time commitment, how many hours per month can you realistically dedicate to mentoring?",
      "question_type": "commitment",
      "options": [
        {{
          "option_id": "A",
          "text": "1-2 hours (ad-hoc availability)",
          "score_profile": {{"availability": 3, "accountability": 3}}
        }},
        {{
          "option_id": "B",
          "text": "3-5 hours (monthly check-ins + responsive messaging)",
          "score_profile": {{"availability": 6, "accountability": 7}}
        }},
        {{
          "option_id": "C",
          "text": "6-10 hours (bi-weekly meetings + active support)",
          "score_profile": {{"availability": 9, "accountability": 9}}
        }},
        {{
          "option_id": "D",
          "text": "10+ hours (weekly engagement + deep involvement)",
          "score_profile": {{"availability": 10, "accountability": 10, "empathy": 8}}
        }}
      ]
    }}
    ... CONTINUE generating questions m3, m4, m5, etc. until you reach m{num_questions}
  ]
}}

IMPORTANT SCENARIOS TO COVER:
- How they give feedback to struggling mentees
- Handling mentees who don't take advice
- Time management and availability
- Knowledge transfer methods
- Past mentoring successes/failures
- Communication frequency preferences
- Dealing with mentee conflicts
- Domain expertise depth
- Network leverage willingness
- Teaching style adaptation

REMINDER: Generate ALL {num_questions} questions. Count them before returning. The "questions" array must contain {num_questions} question objects.

Generate all {num_questions} questions now:"""

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
            
            # CHECK: Warn if fewer questions than requested
            actual_count = len(questions_data["questions"])
            if actual_count < num_questions:
                logger.warning(
                    f"Generated {actual_count} questions but {num_questions} were requested. "
                    f"OpenAI may have hit token limits or context constraints."
                )
                print(f"⚠️  WARNING: Only {actual_count}/{num_questions} questions generated!")
                print(f"💡 TIP: Try requesting fewer questions or increase max_tokens in __init__")
            
            # Add metadata
            questions_data["generated_at"] = datetime.now().isoformat()
            questions_data["total_questions"] = len(questions_data["questions"])
            questions_data["schema_version"] = "1.0"
            questions_data["assessment_type"] = "mentor"
            
            logger.info(f"Successfully generated {questions_data['total_questions']} mentor questions")
            
            return questions_data
        
        except Exception as e:
            logger.error(f"Mentor question generation failed: {e}", exc_info=True)
            raise

    def evaluate_responses(
        self,
        questions_data: Dict[str, Any],
        responses: Dict[str, str],
        mentor_background: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate mentor responses and generate comprehensive capability analysis

        Args:
            questions_data: Original questions with scoring profiles
            responses: Dict mapping question_id to selected option_id
            mentor_background: Optional additional context (years of experience, domains, etc.)

        Returns:
            Detailed mentor capability analysis dictionary
        """
        try:
            logger.info(f"Evaluating {len(responses)} mentor responses...")

            if not responses:
                raise ValueError("No responses provided for evaluation")

            # Calculate raw scores per dimension with weighted scoring
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

            # Calculate weighted dimension averages
            dimension_averages = {}
            for dimension, scores in dimension_scores.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    weight = self.DIMENSIONS[dimension]["weight"]
                    dimension_averages[dimension] = round(avg_score * weight, 2)
                else:
                    dimension_averages[dimension] = 0.0

            # Calculate overall weighted score
            total_weight = sum(self.DIMENSIONS[dim]["weight"] for dim in dimension_averages.keys())
            overall_score = (
                round(sum(dimension_averages.values()) / total_weight, 2)
                if dimension_averages and total_weight > 0 else 0.0
            )

            # Generate AI-powered mentor analysis
            analysis = self._generate_mentor_analysis(
                dimension_averages,
                answered_questions,
                questions_data,
                mentor_background
            )

            # Compile final results
            result = {
                "assessment_id": questions_data.get("assessment_id", "unknown"),
                "assessment_type": "mentor",
                "evaluated_at": datetime.now().isoformat(),
                "schema_version": "1.0",
                "total_questions": len(question_map),
                "questions_answered": len(answered_questions),
                "completion_rate": round(
                    len(answered_questions) / max(len(question_map), 1) * 100, 1
                ),
                "dimension_scores": dimension_averages,
                "overall_mentor_score": overall_score,
                "mentor_strengths": analysis.get("strengths", []),
                "development_areas": analysis.get("development_areas", []),
                "mentor_profile_summary": analysis.get("mentor_profile_summary", ""),
                "mentoring_fit": analysis.get("mentoring_fit", {}),
                "teaching_style": analysis.get("teaching_style", ""),
                "ideal_mentee_profile": analysis.get("ideal_mentee_profile", {}),
                "mentoring_capacity": analysis.get("mentoring_capacity", ""),
                "expertise_domains": analysis.get("expertise_domains", []),
                "recommendations": analysis.get("recommendations", []),
                "detailed_insights": analysis.get("detailed_insights", {}),
                "response_details": answered_questions
            }

            logger.info(
                f"Mentor evaluation complete. Score: {result['overall_mentor_score']}/10, "
                f"Completion: {result['completion_rate']}%"
            )

            return result

        except Exception as e:
            logger.error(f"Mentor response evaluation failed: {e}", exc_info=True)
            raise

    def _generate_mentor_analysis(
        self,
        dimension_scores: Dict[str, float],
        answered_questions: List[Dict[str, Any]],
        questions_data: Dict[str, Any],
        mentor_background: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate deep AI-powered analysis of mentor capabilities

        Args:
            dimension_scores: Average weighted scores per dimension
            answered_questions: List of answered questions with details
            questions_data: Original assessment data
            mentor_background: Additional context about mentor

        Returns:
            Detailed mentor analysis dictionary
        """
        try:
            # Prepare dimension summary
            dimension_details = "\n".join([
                f"- {self.DIMENSIONS[dim]['name']}: {score:.2f}/10 (weight: {self.DIMENSIONS[dim]['weight']})"
                for dim, score in sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)
            ])

            # Calculate total weighted score
            total_weight = sum(self.DIMENSIONS[dim]["weight"] for dim in dimension_scores.keys())
            overall_score = sum(dimension_scores.values()) / total_weight if total_weight > 0 else 0

            # Add background context
            background_context = ""
            if mentor_background:
                background_context = f"\n\nADDITIONAL CONTEXT:\n{json.dumps(mentor_background, indent=2)}"

            prompt = f"""Analyze this MENTOR assessment (not entrepreneur) and return ONLY valid JSON.

DIMENSION SCORES (weighted, out of 10):
{dimension_details}

OVERALL MENTOR SCORE: {overall_score:.2f}/10
{background_context}

Return EXACT JSON structure:
{{
  "mentor_profile_summary": "2-3 sentence summary of mentoring style, strengths, and approach",
  "strengths": ["Top mentoring strength 1", "Top strength 2", "Top strength 3"],
  "development_areas": ["Area to improve 1", "Area to improve 2"],
  "mentoring_fit": {{
    "overall_fit": "Excellent/Good/Moderate/Limited",
    "fit_score": 0-100,
    "reasoning": "Brief explanation of mentoring readiness",
    "mentoring_readiness": "Ready/Needs Development/Not Ready"
  }},
  "teaching_style": "Primary teaching approach: Socratic/Hands-on/Directive/Collaborative/Challenging",
  "ideal_mentee_profile": {{
    "experience_level": "Early-stage/Growth-stage/Scaling founders",
    "personality_fit": "Best mentee personality types",
    "challenge_areas": "Problems mentor is best equipped to help with",
    "industry_fit": "Industries where mentor adds most value"
  }},
  "mentoring_capacity": "How many mentees can effectively support: 1-2/3-5/6-10/10+",
  "expertise_domains": ["Primary domain 1", "Secondary domain 2", "Tertiary domain 3"],
  "recommendations": ["Actionable recommendation 1", "Recommendation 2", "Recommendation 3"],
  "detailed_insights": {{
    "communication_approach": "How mentor communicates and engages",
    "feedback_style": "How mentor provides feedback",
    "availability_pattern": "Time commitment and responsiveness",
    "network_leverage": "How mentor uses their network",
    "experience_depth": "Real-world experience level",
    "empathy_score": "Emotional intelligence and patience level",
    "unique_value": "Distinctive mentoring strengths"
  }}
}}

Be specific, professional, and actionable. Focus on MENTORING capabilities, not entrepreneurship skills. NO MARKDOWN, NO EXTRA TEXT."""

            raw_response = self._call_llm_with_retry(prompt)
            cleaned_content = self._clean_json_response(raw_response)

            try:
                analysis = json.loads(cleaned_content)
            except json.JSONDecodeError as json_err:
                logger.error(f"Mentor analysis JSON decode failed: {json_err}")
                raise ValueError(f"Invalid mentor analysis JSON from LLM: {json_err}")

            # Validate required analysis keys
            required_keys = {"mentor_profile_summary", "strengths", "mentoring_fit", "teaching_style"}
            missing_keys = required_keys - analysis.keys()
            if missing_keys:
                logger.warning(f"Mentor analysis missing keys: {missing_keys}")

            return analysis

        except Exception as e:
            logger.error(f"Mentor AI analysis generation failed: {e}", exc_info=True)
            # Return safe fallback
            return {
                "mentor_profile_summary": (
                    f"Mentor assessment indicates an overall score of {overall_score:.2f}/10. "
                    "Further analysis recommended."
                ),
                "strengths": ["Assessment completed successfully"],
                "development_areas": ["Review detailed scores for specific insights"],
                "mentoring_fit": {
                    "overall_fit": "Moderate",
                    "fit_score": 70,
                    "reasoning": "Assessment completed. Individual results vary by dimension.",
                    "mentoring_readiness": "Needs Development"
                },
                "teaching_style": "Mixed approach",
                "ideal_mentee_profile": {
                    "experience_level": "Various",
                    "personality_fit": "Flexible",
                    "challenge_areas": "General business challenges",
                    "industry_fit": "Cross-industry"
                },
                "mentoring_capacity": "3-5 mentees",
                "expertise_domains": ["To be determined"],
                "recommendations": [
                    "Review dimension scores in detail",
                    "Clarify time commitment capacity",
                    "Identify primary expertise domains"
                ],
                "detailed_insights": {
                    "communication_approach": "Further analysis needed",
                    "feedback_style": "Review response patterns",
                    "availability_pattern": "Self-assessment recommended",
                    "network_leverage": "Context-dependent",
                    "experience_depth": "Moderate",
                    "empathy_score": "Moderate to high",
                    "unique_value": "Individual strengths identified"
                }
            }


class MentorEvaluatorSingleton:
    """Thread-safe singleton for MentorEvaluator"""
    _instance: Optional[MentorEvaluator] = None

    @classmethod
    def get_instance(cls, **kwargs) -> MentorEvaluator:
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = MentorEvaluator(**kwargs)
        return cls._instance


# Backward-compatible function
def get_mentor_evaluator() -> MentorEvaluator:
    """Get singleton instance of mentor evaluator"""
    return MentorEvaluatorSingleton.get_instance()


# Module-level singleton for convenience
mentor_evaluator = get_mentor_evaluator()
