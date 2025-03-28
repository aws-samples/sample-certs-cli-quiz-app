"""
Quiz generator module for creating quizzes based on Knowledge Base content
"""

import logging
import json
import re
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class QuizGenerator:
    """
    Class for generating quizzes based on Knowledge Base content
    """
    
    def __init__(self, knowledge_base):
        """
        Initialize the quiz generator
        
        Args:
            knowledge_base (BedrockKnowledgeBase): Knowledge Base handler
        """
        self.knowledge_base = knowledge_base
        
    def create_quiz(self, topic, difficulty, num_questions):
        """
        Create a quiz on a specific topic
        
        Args:
            topic (str): Topic for the quiz
            difficulty (str): Difficulty level (easy, medium, hard)
            num_questions (int): Number of questions to generate
            
        Returns:
            list: List of quiz questions
        """
        logger.info(f"Generating {num_questions} {difficulty} questions about {topic}")
        
        if topic.lower() == "general knowledge":
            return self._create_general_quiz(difficulty, num_questions)
        else:
            return self._create_topic_quiz(topic, difficulty, num_questions)
    
    def _create_topic_quiz(self, topic, difficulty, num_questions):
        """
        Create a quiz on a specific topic
        
        Args:
            topic (str): Topic for the quiz
            difficulty (str): Difficulty level (easy, medium, hard)
            num_questions (int): Number of questions to generate
            
        Returns:
            list: List of quiz questions
        """
        # Create prompt template for retrieve and generate
        prompt_template = f"""
        You are an expert quiz creator for certification exam preparation.
        
        Based on the retrieved information about "{topic}", create {num_questions} multiple-choice questions at {difficulty} difficulty level.
        
        For each question:
        1. Make sure it's at {difficulty} difficulty level
        2. Include 4 possible answers (A, B, C, D)
        3. Mark the correct answer
        4. Provide a brief explanation for why the answer is correct
        
        Format each question like this:
        
        Q1: [Question text]
        A. [Specific option text for A]
        B. [Specific option text for B]
        C. [Specific option text for C]
        D. [Specific option text for D]
        Answer: [Correct letter]
        Explanation: [Brief explanation]
        
        Make sure the questions are challenging but fair, and directly related to "{topic}".
        """
        
        try:
            # Use retrieve and generate
            generated_text = self.knowledge_base.retrieve_and_generate(
                query=f"Tell me about {topic} for a certification exam",
                prompt_template=prompt_template,
                num_results=5
            )
            
            # Parse the generated text into structured questions
            questions = self._parse_questions(generated_text)
            
            return questions
            
        except ClientError as e:
            logger.error(f"Error generating topic quiz: {e}")
            raise
    
    def _create_general_quiz(self, difficulty, num_questions):
        """
        Create a general quiz across multiple topics
        
        Args:
            difficulty (str): Difficulty level (easy, medium, hard)
            num_questions (int): Number of questions to generate
            
        Returns:
            list: List of quiz questions
        """
        logger.info(f"Generating general knowledge quiz with {num_questions} {difficulty} questions")
        
        # Create prompt template for retrieve and generate
        prompt_template = f"""
        You are an expert quiz creator for certification exam preparation.
        
        Based on the retrieved information from various topics, create {num_questions} multiple-choice questions at {difficulty} difficulty level.
        
        Important: Include questions from different topics and subject areas to create a diverse general knowledge quiz.
        
        For each question:
        1. Make sure it's at {difficulty} difficulty level
        2. Include 4 possible answers (A, B, C, D)
        3. Mark the correct answer
        4. Provide a brief explanation for why the answer is correct
        
        Format each question like this:
        
        Q1: [Question text]
        A. [Specific option text for A - not just "A"]
        B. [Specific option text for B - not just "B"]
        C. [Specific option text for C - not just "C"]
        D. [Specific option text for D - not just "D"]
        Answer: [Correct letter]
        Explanation: [Brief explanation]
        
        Make sure the questions are challenging but fair, and cover a variety of topics from the study materials.
        """
        
        try:
            # Use retrieve and generate
            generated_text = self.knowledge_base.retrieve_and_generate(
                query="Give me diverse information from different topics for a general knowledge quiz",
                prompt_template=prompt_template,
                num_results=5
            )
            
            # Parse the generated text into structured questions
            questions = self._parse_questions(generated_text)
            
            return questions
            
        except ClientError as e:
            logger.error(f"Error generating general quiz: {e}")
            raise
    
    def _parse_questions(self, text):
        """
        Parse the generated text into structured questions
        
        Args:
            text (str): Generated text containing questions
            
        Returns:
            list: List of structured questions
        """
        # Split the text into individual questions
        question_pattern = r'Q\d+:|Question \d+:'
        raw_questions = re.split(question_pattern, text)
        
        # Remove any empty strings
        raw_questions = [q.strip() for q in raw_questions if q.strip()]
        
        structured_questions = []
        
        for i, raw_q in enumerate(raw_questions):
            try:
                # Extract the question text, options, answer, and explanation
                lines = raw_q.split('\n')
                question_text = lines[0].strip()
                
                options = {}
                answer = None
                explanation = None
                correct_index = None
                
                # Process each line to extract options, answer, and explanation
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Extract options (A, B, C, D)
                    option_match = re.match(r'^([A-D])[.:]?\s+(.+)$', line)
                    if option_match:
                        letter, text = option_match.groups()
                        options[letter] = text
                    
                    # Extract answer
                    answer_match = re.match(r'^Answer:?\s+([A-D]).*$', line)
                    if answer_match:
                        answer = answer_match.group(1)
                    
                    # Extract explanation
                    if line.startswith('Explanation:'):
                        explanation = line[12:].strip()
                    elif explanation and not option_match and not answer_match and not line.startswith('Q'):
                        explanation += ' ' + line
                
                # Convert answer letter to index (A=0, B=1, etc.)
                if answer:
                    correct_index = ord(answer) - 65  # A=0, B=1, C=2, D=3
                
                # Create structured question if we have all required components
                if question_text and options and answer and explanation and len(options) == 4:
                    structured_questions.append({
                        'question': question_text,
                        'options': options,
                        'answer': answer,
                        'explanation': explanation
                    })
            except Exception as e:
                logger.error(f"Error parsing question {i+1}: {e}")
                continue
        
        return structured_questions
