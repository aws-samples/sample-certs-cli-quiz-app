#!/usr/bin/env python3
"""
CLI Study Buddy: An AI-powered quiz application for certification exam preparation.
Uses Bedrock Knowledge Base for intelligent question generation and DynamoDB for progress tracking.

Key Components:
- BedrockKnowledgeBase: Handles interaction with your study materials
- QuizGenerator: Creates personalized quiz questions
- DynamoDBClient: Stores and retrieves your progress
"""

import os
import sys
import argparse
import logging
import uuid
import json
from pathlib import Path
from datetime import datetime

# Add src directory to path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from rag_handler.knowledge_base import BedrockKnowledgeBase
from quiz_engine.generator import QuizGenerator
from data_store.dynamo_client import DynamoDBClient
from config_helper import get_kb_id

# Set up logging to track application behavior
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default configuration settings
DEFAULT_REGION = "us-east-1"
DEFAULT_MODEL_ID = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"  # Claude 3 Sonnet 
DEFAULT_TABLE_NAME = "certification_quiz_results"  # DynamoDB table for storing results
DEFAULT_NUM_QUESTIONS = 5
DEFAULT_DIFFICULTY = "medium"

class CertQuizApp:
    """
    Main application class that coordinates between Knowledge Base, Quiz Generator, and DynamoDB.
    Handles user interaction and manages quiz sessions.
    """
    
    def __init__(self, region=DEFAULT_REGION):
        """
        Initialize the application with AWS region and set up components
        
        Args:
            region (str): AWS region for all services
        """
        self.region = region
        self.kb = None  # Knowledge Base client
        self.quiz_generator = None  # Quiz generation engine
        self.db_client = None  # DynamoDB client
        self.user_id = self._get_or_create_user_id()  # Unique user identifier
        
    def _get_or_create_user_id(self):
        """
        Manage user identification by either retrieving existing ID or creating new one.
        Stores user ID in local config file for persistence.
        
        Returns:
            str: Unique user identifier
        """
        config_dir = os.path.expanduser("~/.cert_quiz")
        config_file = os.path.join(config_dir, "config.json")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Load existing user ID if available
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
                return config.get("user_id", str(uuid.uuid4()))
        
        # Create new user ID if none exists
        user_id = str(uuid.uuid4())
        with open(config_file, "w") as f:
            json.dump({"user_id": user_id}, f)
            
        return user_id
        
    def initialize(self, kb_id):
        """
        Set up all components needed for the quiz application
        
        Args:
            kb_id (str): Identifier for your Knowledge Base
        """
        logger.info("Initializing app components")
        
        # Set up connection to your study materials
        # Create model ARN with proper region
        model_arn = DEFAULT_MODEL_ID.replace("us-east-1", self.region)
        self.kb = BedrockKnowledgeBase(kb_id=kb_id, region=self.region, model_id=model_arn)
        
        # Initialize the quiz generation engine
        self.quiz_generator = QuizGenerator(
            knowledge_base=self.kb
        )
        
        # Set up progress tracking
        self.db_client = DynamoDBClient(
            table_name=DEFAULT_TABLE_NAME,
            region=self.region
        )
        
    def run_quiz(self, topic, difficulty=DEFAULT_DIFFICULTY, num_questions=DEFAULT_NUM_QUESTIONS):
        """
        Execute a complete quiz session including question generation, user interaction,
        and result storage
        
        Args:
            topic (str): The subject to be tested
            difficulty (str): Quiz difficulty level (easy/medium/hard)
            num_questions (int): Number of questions to generate
            
        Returns:
            float: Quiz score as a percentage
        """
        if not self.quiz_generator:
            raise ValueError("Quiz generator not initialized")
            
        logger.info(f"Starting quiz on {topic} ({difficulty}, {num_questions} questions)")
        
        # Color coding for better user experience
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"
        END = "\033[0m"
        
        # Get questions from the Knowledge Base
        questions = self.quiz_generator.create_quiz(
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions
        )
        
        # Track correct answers for scoring
        correct_answers = 0
        
        # Display quiz header
        print(f"\n{BOLD}{UNDERLINE}===== QUIZ: {topic.upper()} ====={END}")
        print(f"{BLUE}Difficulty: {difficulty.capitalize()}{END}")
        print(f"{BLUE}Number of questions: {num_questions}{END}")
        print(f"{YELLOW}Answer each question by entering A, B, C, or D.{END}\n")
        
        # Process each question
        for i, q in enumerate(questions):
            print(f"\n{BOLD}Question {i+1}: {q['question']}{END}")
            
            # Display answer options
            for letter, option_text in q['options'].items():
                print(f"  {letter}. {option_text}")
                
            # Get and validate user input
            while True:
                user_answer = input(f"\n{YELLOW}Your answer: {END}").strip().upper()
                if user_answer in ['A', 'B', 'C', 'D']:
                    break
                print(f"{RED}Invalid input. Please enter A, B, C, or D.{END}")
                
            # Check answer and provide feedback
            is_correct = user_answer == q['answer']
            if is_correct:
                correct_answers += 1
                print(f"\n{GREEN}✓ Correct!{END}")
            else:
                print(f"\n{RED}✗ Incorrect. The correct answer is {q['answer']}.{END}")
                
            # Show explanation for learning
            print(f"{BLUE}Explanation: {q['explanation']}{END}")
            
        # Calculate and display final score
        score = (correct_answers / len(questions)) * 100
        
        print(f"\n{BOLD}{UNDERLINE}===== QUIZ COMPLETE ====={END}")
        if score >= 80:
            print(f"{GREEN}{BOLD}Score: {score:.1f}% ({correct_answers}/{len(questions)} correct){END}")
        elif score >= 60:
            print(f"{YELLOW}{BOLD}Score: {score:.1f}% ({correct_answers}/{len(questions)} correct){END}")
        else:
            print(f"{RED}{BOLD}Score: {score:.1f}% ({correct_answers}/{len(questions)} correct){END}")
        
        # Store quiz results for progress tracking
        if self.db_client:
            self.db_client.save_quiz_result(
                user_id=self.user_id,
                topic=topic,
                score=score,
                num_questions=num_questions,
                difficulty=difficulty
            )
            
        return score
        
    def show_history(self, limit=10):
        """
        Display previous quiz results
        
        Args:
            limit (int): Maximum number of historical results to show
        """
        if not self.db_client:
            raise ValueError("DynamoDB client not initialized")
            
        # Color coding for visual feedback
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"
        END = "\033[0m"
            
        # Retrieve quiz history from DynamoDB
        results = self.db_client.get_user_results(self.user_id, limit=limit)
        
        if not results:
            print(f"\n{YELLOW}No quiz history found.{END}")
            return
            
        # Display history header
        print(f"\n{BOLD}{UNDERLINE}===== QUIZ HISTORY (Last {min(limit, len(results))}) ====={END}")
        print(f"{BOLD}{'Date':<20} {'Topic':<30} {'Score':<10} {'Difficulty':<10}{END}")
        print(f"{BLUE}{'-' * 70}{END}")
        
        # Display each historical result
        for result in results:
            # Format the timestamp
            timestamp = datetime.fromisoformat(result['timestamp'])
            date_str = timestamp.strftime("%Y-%m-%d %H:%M")
            
            # Color-code score based on performance
            score = float(result['score'])
            if score >= 80:
                score_str = f"{GREEN}{score:<10.1f}{END}"
            elif score >= 60:
                score_str = f"{YELLOW}{score:<10.1f}{END}"
            else:
                score_str = f"{RED}{score:<10.1f}{END}"
                
            print(f"{date_str:<20} {result['topic']:<30} {score_str} {result['difficulty']:<10}")
            
    def show_topic_stats(self, topic):
        """
        Display performance statistics for a specific topic
        
        Args:
            topic (str): Topic to analyze
        """
        if not self.db_client:
            raise ValueError("DynamoDB client not initialized")
            
        # Color coding for visual feedback
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"
        END = "\033[0m"
            
        # Get topic statistics from DynamoDB
        stats = self.db_client.get_topic_statistics(self.user_id, topic)
        
        print(f"\n{BOLD}{UNDERLINE}===== TOPIC STATISTICS: {topic.upper()} ====={END}")
        
        if stats['attempts'] == 0:
            print(f"{YELLOW}No quiz attempts found for this topic.{END}")
            return
            
        # Display comprehensive statistics
        print(f"{BLUE}Attempts: {stats['attempts']}{END}")
        
        # Color-code average score based on performance
        avg_score = float(stats['average_score'])
        if avg_score >= 80:
            print(f"{GREEN}Average Score: {avg_score:.1f}%{END}")
        elif avg_score >= 60:
            print(f"{YELLOW}Average Score: {avg_score:.1f}%{END}")
        else:
            print(f"{RED}Average Score: {avg_score:.1f}%{END}")
            
        print(f"{GREEN}Highest Score: {float(stats['highest_score']):.1f}%{END}")
        print(f"{RED}Lowest Score: {float(stats['lowest_score']):.1f}%{END}")
        print(f"{BLUE}Total Questions Answered: {stats['total_questions']}{END}")
        
    def show_kb_info(self):
        """
        Display information about the Knowledge Base and its data sources
        """
        if not self.kb:
            raise ValueError("Knowledge Base not initialized")
            
        # Color coding for visual feedback
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"
        END = "\033[0m"
            
        # Get Knowledge Base details
        kb_info = self.kb.get_knowledge_base_info()
        
        # Display Knowledge Base information
        print(f"\n{BOLD}{UNDERLINE}===== KNOWLEDGE BASE INFORMATION ====={END}")
        print(f"{BLUE}ID: {kb_info.get('knowledgeBaseId')}{END}")
        print(f"{BLUE}Name: {kb_info.get('name')}{END}")
        print(f"{BLUE}Description: {kb_info.get('description')}{END}")
        print(f"{GREEN}Status: {kb_info.get('status')}{END}")
        print(f"{BLUE}Created: {kb_info.get('createdAt')}{END}")
        print(f"{BLUE}Last Modified: {kb_info.get('updatedAt')}{END}")
        
        # List connected data sources
        data_sources = self.kb.list_data_sources()
        print(f"\n{BOLD}Data Sources ({len(data_sources)}):{END}")
        for ds in data_sources:
            print(f"  {GREEN}- {ds.get('name')}: {ds.get('dataSourceId')} ({ds.get('status')}){END}")

def main():
    """
    CLI entry point with argument parsing and command routing
    """
    parser = argparse.ArgumentParser(
        description="CLI Study Buddy: Your AI-powered certification exam preparation assistant"
    )
    
    # Set up command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Knowledge Base info command
    info_parser = subparsers.add_parser("info", help="Show Knowledge Base information")
    info_parser.add_argument("--kb-id", help="Knowledge Base ID (optional if set in .env)")
    
    # Quiz command
    quiz_parser = subparsers.add_parser("quiz", help="Start a quiz session")
    quiz_parser.add_argument("--kb-id", help="Knowledge Base ID (optional if set in .env)")
    quiz_parser.add_argument("--topic", help="Topic to be tested (optional, will prompt if not provided)")
    quiz_parser.add_argument("--general", action="store_true", help="Generate a general quiz across all topics")
    quiz_parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default=DEFAULT_DIFFICULTY,
        help="Quiz difficulty level"
    )
    quiz_parser.add_argument(
        "--questions",
        type=int,
        default=DEFAULT_NUM_QUESTIONS,
        help="Number of questions to generate"
    )
    quiz_parser.add_argument(
        "--model",
        help="Bedrock model ID to use (defaults to Claude 3 Sonnet)"
    )
    
    # History command
    history_parser = subparsers.add_parser("history", help="View your quiz history")
    history_parser.add_argument("--kb-id", help="Knowledge Base ID (optional if set in .env)")
    history_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results to show"
    )
    
    # Statistics command
    stats_parser = subparsers.add_parser("stats", help="View topic statistics")
    stats_parser.add_argument("--kb-id", help="Knowledge Base ID (optional if set in .env)")
    stats_parser.add_argument("--topic", required=True, help="Topic to analyze")
    
    # Global options
    parser.add_argument("--region", default=DEFAULT_REGION, help="AWS region")
    
    # Parse and process arguments
    args = parser.parse_args()
    
    # Get Knowledge Base ID from args or config
    kb_id = get_kb_id(args)
    if not kb_id and args.command != None:
        print("Error: Knowledge Base ID is required. Please provide it with --kb-id or set it in .env file.")
        sys.exit(1)
    
    # Initialize application
    app = CertQuizApp(region=args.region)
    
    # Route to appropriate command handler
    if args.command == "info":
        app.initialize(kb_id=kb_id)
        app.show_kb_info()
        
    elif args.command == "quiz":
        app.initialize(kb_id=kb_id)
        
        # Override default model if specified
        if hasattr(args, 'model') and args.model:
            app.kb.model_id = args.model
        
        # Handle general quiz option
        if hasattr(args, 'general') and args.general:
            topic = "General Knowledge"
        else:
            # If topic is not provided, prompt the user
            topic = args.topic
            if not topic:
                topic = input("Enter a topic for your quiz: ")
            
        app.run_quiz(topic, args.difficulty, args.questions)
        
    elif args.command == "history":
        app.initialize(kb_id=kb_id)
        app.show_history(args.limit)
        
    elif args.command == "stats":
        app.initialize(kb_id=kb_id)
        app.show_topic_stats(args.topic)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
