"""
Configuration Helper Module: Handles loading and managing configuration settings.
Provides functions for retrieving environment variables and command-line arguments.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def get_kb_id(args):
    """
    Get Knowledge Base ID from command-line arguments or environment variables.
    
    Args:
        args: Command-line arguments
        
    Returns:
        str: Knowledge Base ID or None if not found
    """
    # First check command-line arguments
    if hasattr(args, 'kb_id') and args.kb_id:
        return args.kb_id
        
    # Then check environment variables
    kb_id = os.getenv('KB_ID') or os.getenv('BEDROCK_KB_ID')
    if kb_id:
        return kb_id
        
    # Not found
    return None
