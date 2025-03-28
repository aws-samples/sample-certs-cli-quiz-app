"""
Knowledge Base handler for interacting with Amazon Bedrock Knowledge Bases
"""

import logging
import json
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BedrockKnowledgeBase:
    """
    Class for interacting with Amazon Bedrock Knowledge Bases
    """
    
    def __init__(self, kb_id, region="us-east-1", model_id=None):
        """
        Initialize the Knowledge Base handler
        
        Args:
            kb_id (str): Knowledge Base ID
            region (str): AWS region
            model_id (str): Bedrock model ID for generation
        """
        self.kb_id = kb_id
        self.region = region
        self.model_id = model_id
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
    def query_knowledge_base(self, query, num_results=3):
        """
        Query the Knowledge Base using the retrieve API
        
        Args:
            query (str): Query text
            num_results (int): Number of results to return
            
        Returns:
            list: List of retrieved passages
        """
        logger.info(f"Querying Knowledge Base: {query}")
        
        try:
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': num_results
                    }
                }
            )
            
            # Extract and return the retrieved passages
            retrieved_results = []
            for result in response.get('retrievalResults', []):
                content = result.get('content', {}).get('text', '')
                if content:
                    retrieved_results.append(content)
                    
            return retrieved_results
            
        except ClientError as e:
            logger.error(f"Error querying Knowledge Base: {e}")
            raise
            
    def retrieve_and_generate(self, query, prompt_template, num_results=3):
        """
        Query the Knowledge Base and generate content using the RetrieveAndGenerate API
        
        Args:
            query (str): Query text
            prompt_template (str): Template for the prompt to send to the model
            num_results (int): Number of results to return
            
        Returns:
            str: Generated content
        """
        logger.info(f"Using RetrieveAndGenerate API for query: {query}")
        
        try:
            # Create the full prompt with template
            full_prompt = f"""
            You are an expert quiz creator for certification exam preparation.
            Based on the retrieved information, please:
            
            {prompt_template}
            """

            # Use the unified RetrieveAndGenerate API
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={
                    'text': query + "\n\n" + full_prompt
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': self.model_id
                    }
                }
            )
            
            # Parse response
            generated_text = response.get('output', {}).get('text', '')
            
            return generated_text
            
        except ClientError as e:
            logger.error(f"Error with retrieve and generate: {e}")
            raise
            
    def get_knowledge_base_info(self):
        """
        Get information about the Knowledge Base
        
        Returns:
            dict: Knowledge Base information
        """
        try:
            bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
            response = bedrock_agent.get_knowledge_base(
                knowledgeBaseId=self.kb_id
            )
            return response
        except ClientError as e:
            logger.error(f"Error getting Knowledge Base info: {e}")
            raise
            
    def list_data_sources(self):
        """
        List data sources for the Knowledge Base
        
        Returns:
            list: List of data sources
        """
        try:
            bedrock_agent = boto3.client('bedrock-agent', region_name=self.region)
            response = bedrock_agent.list_data_sources(
                knowledgeBaseId=self.kb_id
            )
            return response.get('dataSourceSummaries', [])
        except ClientError as e:
            logger.error(f"Error listing data sources: {e}")
            raise
