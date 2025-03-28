"""
DynamoDB Client Module: Handles storage and retrieval of quiz results.
Provides methods for tracking progress and analyzing performance.
"""

import logging
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class DynamoDBClient:
    """
    Handles interaction with DynamoDB for storing and retrieving quiz results.
    """
    
    def __init__(self, table_name, region="us-east-1"):
        """
        Initialize the DynamoDB client.
        
        Args:
            table_name (str): DynamoDB table name
            region (str): AWS region
        """
        self.table_name = table_name
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        self._ensure_table_exists()
        
    def _ensure_table_exists(self):
        """
        Ensure the DynamoDB table exists, create it if it doesn't.
        """
        try:
            self.table.table_status
            logger.info(f"DynamoDB table {self.table_name} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"Creating DynamoDB table {self.table_name}")
                self._create_table()
            else:
                logger.error(f"Error checking DynamoDB table: {e}")
                raise
                
    def _create_table(self):
        """
        Create the DynamoDB table for storing quiz results.
        """
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'RANGE'  # Sort key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'topic',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'TopicIndex',
                        'KeySchema': [
                            {
                                'AttributeName': 'user_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'topic',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            # Wait for table creation
            table.meta.client.get_waiter('table_exists').wait(TableName=self.table_name)
            logger.info(f"DynamoDB table {self.table_name} created successfully")
            
        except ClientError as e:
            logger.error(f"Error creating DynamoDB table: {e}")
            raise
            
    def save_quiz_result(self, user_id, topic, score, num_questions, difficulty):
        """
        Save a quiz result to DynamoDB.
        
        Args:
            user_id (str): Unique user identifier
            topic (str): Quiz topic
            score (float): Quiz score as percentage
            num_questions (int): Number of questions in the quiz
            difficulty (str): Quiz difficulty level
        """
        logger.info(f"Saving quiz result for user {user_id}, topic {topic}")
        
        timestamp = datetime.utcnow().isoformat()
        
        try:
            self.table.put_item(
                Item={
                    'user_id': user_id,
                    'timestamp': timestamp,
                    'topic': topic,
                    'score': Decimal(str(score)),  # Convert float to Decimal
                    'num_questions': num_questions,
                    'difficulty': difficulty
                }
            )
            
            logger.info("Quiz result saved successfully")
            
        except ClientError as e:
            logger.error(f"Error saving quiz result: {e}")
            raise
            
    def get_user_results(self, user_id, limit=10):
        """
        Get quiz results for a specific user.
        
        Args:
            user_id (str): Unique user identifier
            limit (int): Maximum number of results to return
            
        Returns:
            list: Quiz results
        """
        logger.info(f"Getting quiz results for user {user_id}")
        
        try:
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id),
                ScanIndexForward=False,  # Sort in descending order (newest first)
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            logger.error(f"Error getting user results: {e}")
            raise
            
    def get_topic_statistics(self, user_id, topic):
        """
        Get statistics for a specific topic.
        
        Args:
            user_id (str): Unique user identifier
            topic (str): Topic to analyze
            
        Returns:
            dict: Topic statistics
        """
        logger.info(f"Getting statistics for user {user_id}, topic {topic}")
        
        try:
            response = self.table.query(
                IndexName='TopicIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id) & 
                                      boto3.dynamodb.conditions.Key('topic').eq(topic)
            )
            
            results = response.get('Items', [])
            
            if not results:
                return {
                    'attempts': 0,
                    'average_score': 0,
                    'highest_score': 0,
                    'lowest_score': 0,
                    'total_questions': 0
                }
                
            # Calculate statistics
            scores = [float(result['score']) for result in results]
            total_questions = sum(int(result['num_questions']) for result in results)
            
            stats = {
                'attempts': len(results),
                'average_score': Decimal(str(sum(scores) / len(scores))),
                'highest_score': Decimal(str(max(scores))),
                'lowest_score': Decimal(str(min(scores))),
                'total_questions': total_questions
            }
            
            return stats
            
        except ClientError as e:
            logger.error(f"Error getting topic statistics: {e}")
            raise
