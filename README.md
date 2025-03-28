# AI-powered CLI Study Buddy Quiz App

Your command-line companion for certification exam preparation! Ask questions about any topic in your study materials and get intelligent, personalized quizzes to test your knowledge.

## What is CLI Study Buddy?

CLI Study Buddy uses [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html?trk=861fe434-89a6-4c2a-ac1f-9a898d3f87f7&sc_channel=el) to help you study smarter, not harder. Feed it your study materials, and it will:
- Generate relevant practice questions
- Test your knowledge at different difficulty levels
- Track your progress over time
- Help you focus on areas that need more attention

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐
│ Study Materials │     │CLI Quiz         │
│ (PDFs, DOCs)    │     │Application      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│                 │     │User Query       │
│   S3 Bucket     │     │(Topic)          │
│                 │     └────────┬────────┘
└────────┬────────┘              │
         │                       ▼
         │         ┌───────────────────────┐
         │         │   Bedrock Services    │
         └────────►├───────────────────────┤
                   │┌─────┐ ┌─────┐ ┌────┐ │
                   ││KB   │ │Model│ │RAG │ │
                   │└──┬──┘ └──┬──┘ └─┬──┘ │
                   │   └───────┼──────┘    │
                   └───────────┼───────────┘
                               │
                               ▼
                   ┌─────────────────────┐
                   │  Generated Quiz     │
                   │  Questions          │
                   └────────┬────────────┘
                            │
                            ▼
                   ┌─────────────────────┐
                   │  User Quiz Session  │
                   └────────┬────────────┘
                            │
                            ▼
                   ┌─────────────────────┐
                   │      DynamoDB       │
                   │   (Score Storage)   │
                   └────────┬────────────┘
                            │
                            ▼
                   ┌─────────────────────┐
                   │  Progress Reports   │
                   │    & Analytics      │
                   └─────────────────────┘
```

## Features

- **Smart Quizzes**: Generates questions based on your study materials
- **Flexible Learning**: Choose your topic and difficulty level
- **Progress Tracking**: Monitor your improvement over time
- **Quick Access**: Everything right in your terminal
- **Study Your Way**: Works with any certification materials you provide

## Getting Started

### Prerequisites

- **Python 3.10+**
- **AWS Account with Bedrock access**
- **AWS CLI configured with credentials**
- **A Bedrock Knowledge Base** with your study materials

### Quick Setup

1. **Install your study buddy**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Make it executable**:
   ```bash
   chmod +x main.py
   ```

### Basic Commands

1. **Check your knowledge base**:
   ```bash
   python main.py info --kb-id YOUR_KB_ID
   ```

2. **Take a quiz**:
   ```bash
   python main.py quiz --topic "Your Topic" --difficulty medium --questions 5
   ```
   If you don't specify a topic, you'll be prompted to enter one.
   
   For a general quiz across all topics:
   ```bash
   python main.py quiz --general --difficulty medium --questions 5
   ```

3. **See your progress**:
   ```bash
   python main.py history --limit 10
   ```

4. **Check topic stats**:
   ```bash
   python main.py stats --topic "Your Topic"
   ```

If you've set up your Knowledge Base ID in the `.env` file, you don't need to include `--kb-id` in the commands.

## Setting Up Your Study Materials

To get the most out of your Study Buddy, you'll need to create a Knowledge Base with your study materials:

1. **Prepare your documents**:
   - Upload your study materials to an S3 bucket
   - Supported formats include PDF, TXT, DOC, DOCX, and HTML

2. **Create a Knowledge Base**:
   - Sign in to the AWS Management Console
   - Navigate to Amazon Bedrock
   - In the left navigation pane, choose Knowledge bases
   - Choose "Create knowledge base"

3. **Configure your Knowledge Base**:
   - **Basic details**: Enter a name and optional description
   - **Vector store**: Select a vector store (for this use case, Pinecone offers a free tier option)
   - **Data source**: Connect to your S3 bucket containing study materials
   - **Embedding model**: Select a model (typically Amazon Titan Embeddings)
   - **IAM permissions**: Configure service role permissions

4. **Wait for creation and ingestion**:
   - Knowledge Base creation takes a few minutes
   - Document ingestion time depends on the size of your materials

Once created, note your Knowledge Base ID to use with the CLI Study Buddy commands.

For detailed instructions, refer to the [official Amazon Bedrock documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html?trk=861fe434-89a6-4c2a-ac1f-9a898d3f87f7&sc_channel=el).

## Under the Hood

- **Bedrock**: Provides foundation models for question generation (using Claude 3.7)
- **Bedrock Knowledge Base**: Enables semantic search and vector storage of your study materials
- **DynamoDB**: Stores quiz results and performance metrics
- **AWS IAM**: Manages access permissions to AWS resources

## Project Structure

```
/
├── src/                    # Source code
│   ├── quiz_engine/       # Quiz generation
│   ├── rag_handler/       # Study material processing
│   └── data_store/        # Progress tracking
├── main.py                # Your Study Buddy CLI
├── requirements.txt       # Dependencies
└── README.md              # This guide
```

## Tracking Your Progress

- Quiz results are automatically saved to DynamoDB
- Check your progress history with the history command
- Review topics that need more attention using the stats command
- Track your improvement over time with score trends

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
