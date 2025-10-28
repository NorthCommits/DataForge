# DataForge

**Production-grade dataset creation and curation pipeline** integrating Tavily for intelligent web search and OpenAI for AI-powered content analysis, quality assessment, and enrichment.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Overview

DataForge is an AI-powered end-to-end data pipeline that transforms raw web data into high-quality, production-ready training datasets. The system combines smart web discovery with advanced content analysis to create curated datasets for machine learning applications.

### Key Features

- **🔍 Smart Web Discovery**: Tavily-powered content discovery with domain filtering and source verification
- **🤖 AI-Powered Analysis**: GPT-4 content quality assessment, summarization, and topic classification
- **💰 Cost Management**: Real-time API cost tracking with budget enforcement and rate limiting
- **📊 Quality Control**: Multi-criteria quality scoring, fact-checking, and bias detection
- **🔄 Data Processing**: Automated cleaning, deduplication, and train/val/test splitting
- **⚡ Production Ready**: Async processing, caching, retry logic, and comprehensive error handling

## 🏗️ Architecture

```
DataForge/
├── 📁 dataforge/           # Core library
│   ├── 🔌 api/             # API integrations (Tavily, OpenAI)
│   ├── 🕷️ scrapers/        # Content discovery & extraction
│   ├── 🧹 cleaners/        # Text cleaning & normalization
│   ├── 🔍 quality/         # Quality assessment & scoring
│   ├── 📈 enrichment/       # AI-powered enhancement
│   ├── 🗂️ deduplication/   # Duplicate detection & removal
│   ├── ✅ validation/      # Content validation & fact-checking
│   ├── 💾 storage/         # Caching & data persistence
│   ├── 🎛️ cli/            # Command-line interface
│   └── 📊 analytics/       # Cost & performance tracking
├── 📁 examples/            # Usage examples
├── 📁 docs/               # Documentation
└── 📁 tests/              # Test suite
```

### Core Components

- **API Layer**: Async clients for Tavily and OpenAI with rate limiting, caching, and cost tracking
- **Scrapers**: Tavily-powered content discovery with source credibility scoring
- **Processors**: Text cleaning, quality filtering, and deduplication pipelines
- **Quality Assessment**: GPT-4 powered content evaluation with multiple criteria
- **Enrichment**: AI-generated summaries, topic classification, and metadata extraction
- **CLI Tools**: Command-line interface for scraping, processing, and dataset creation

## 🛠️ Installation

### Prerequisites

- Python 3.10+
- Tavily API key
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DataForge
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Validate configuration**
   ```bash
   python -m dataforge.cli.main validate-keys
   ```

## ⚙️ Configuration

DataForge uses a YAML configuration file (`config.yaml`) with environment variable expansion:

```yaml
api:
  tavily:
    api_key: ${TAVILY_API_KEY}
    max_results: 10
    search_depth: "advanced"
    
  openai:
    api_key: ${OPENAI_API_KEY}
    model: "gpt-4-turbo-preview"
    temperature: 0.3
    
  rate_limiting:
    tavily_rpm: 60
    openai_rpm: 3500
    
  cost_limits:
    daily_budget: 10.00
    per_request_max: 0.50
```

## 🎯 Quick Start

### 1. Scrape Content

```bash
# Scrape AI research articles
python -m dataforge.cli.main scrape-tavily --topic "AI research" --limit 20

# Output: ✓ Saved 20 documents to ./data/raw/tavily_ai_research_2025-10-28.jsonl
```

### 2. Process Dataset

```bash
# Clean, deduplicate, and split into train/val/test
python -m dataforge.cli.main process \
  --input ./data/raw/tavily_ai_research_2025-10-28.jsonl \
  --output ./datasets/ai_research

# Output: Processed: total=20 removed=3 final=17
```

### 3. View Results

```bash
# Check dataset structure
ls ./datasets/ai_research/
# train.jsonl  val.jsonl  test.jsonl  dataset_card.json

# View dataset statistics
cat ./datasets/ai_research/dataset_card.json
```

## 📋 CLI Commands

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `validate-keys` | Check API key configuration | `python -m dataforge.cli.main validate-keys` |
| `scrape-tavily` | Scrape content using Tavily | `scrape-tavily --topic "ML" --limit 50` |
| `process` | Process raw data to dataset | `process --input raw.jsonl --output dataset/` |

### Command Options

**scrape-tavily**
- `--topic`: Search topic (required)
- `--limit`: Number of documents (default: 10)
- `--config`: Config file path (default: config.yaml)

**process**
- `--input`: Input JSONL file (required)
- `--output`: Output directory (required)

## 🔧 API Integration

### Tavily Client

```python
from dataforge.api.tavily_client import TavilyClient

async with TavilyClient() as client:
    result = await client.search("machine learning", max_results=10)
    for doc in result.documents:
        print(f"{doc.title}: {doc.url}")
```

### OpenAI Client

```python
from dataforge.api.openai_client import OpenAIClient

async with OpenAIClient() as client:
    analysis = await client.analyze_text("Your content here...")
    print(f"Quality Score: {analysis.scores.factual_accuracy}")
    print(f"Summary: {analysis.summary}")
```

## 📊 Data Pipeline

### 1. Content Discovery
- **Tavily Search**: Smart web search with domain filtering
- **Source Scoring**: Credibility assessment based on domain reputation
- **Rate Limiting**: Respectful API usage with token bucket algorithm

### 2. Content Processing
- **Text Cleaning**: HTML removal, whitespace normalization
- **Quality Filtering**: Length checks, junk content detection
- **Deduplication**: Exact and fuzzy duplicate removal

### 3. Quality Assessment
- **GPT-4 Analysis**: Multi-criteria content evaluation
- **Scoring**: Factual accuracy, coherence, educational value
- **Fact-Checking**: Cross-reference verification with Tavily

### 4. Dataset Creation
- **Train/Val/Test Split**: 80/10/10 automatic splitting
- **Metadata**: Comprehensive dataset cards with statistics
- **Export Formats**: JSONL, Parquet, HuggingFace datasets

## 💰 Cost Management

DataForge includes comprehensive cost tracking and budget enforcement:

- **Real-time Tracking**: Monitor API costs across services
- **Budget Limits**: Daily and per-request cost controls
- **Rate Limiting**: Prevent API quota exhaustion
- **Caching**: Reduce redundant API calls
- **Fallback Models**: Automatic fallback to cheaper alternatives

### Cost Optimization

- File-based caching for API responses
- Batch processing where possible
- Smart model selection (GPT-4 → GPT-3.5 fallback)
- Token-efficient prompts
- Budget alerts and enforcement

## 🧪 Examples

### Basic Usage

```python
# examples/example_tavily_search.py
import asyncio
from dataforge.api.tavily_client import TavilyClient
from dataforge.api.openai_client import OpenAIClient

async def main():
    # Search for content
    async with TavilyClient() as tclient:
        result = await tclient.search("AI breakthroughs 2024", max_results=5)
        
    # Analyze content
    async with OpenAIClient() as oclient:
        for doc in result.documents:
            analysis = await oclient.analyze_text(doc.content or "")
            print(f"Topic: {doc.title}")
            print(f"Quality: {analysis.scores.factual_accuracy}")
            print(f"Summary: {analysis.summary}")

asyncio.run(main())
```

### Custom Processing

```python
from dataforge.cli.process import process_raw_to_dataset
from pathlib import Path

# Process custom dataset
stats = process_raw_to_dataset(
    Path("custom_data.jsonl"),
    Path("output_dataset")
)

print(f"Processed {stats['total']} documents")
print(f"Removed {stats['removed']} low-quality/duplicate items")
print(f"Final dataset: {stats['final']} documents")
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dataforge

# Run specific test categories
pytest tests/test_api/
pytest tests/test_scrapers/
pytest tests/integration/
```

## 📚 Documentation

- [Architecture Guide](docs/architecture.md) - System design and components
- [API Integration](docs/api_integration_guide.md) - Tavily and OpenAI integration details
- [Cost Optimization](docs/cost_optimization.md) - Minimizing API costs
- [User Guide](docs/user_guide.md) - Comprehensive usage instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black dataforge/
ruff check dataforge/
mypy dataforge/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Tavily](https://tavily.com/) for intelligent web search capabilities
- [OpenAI](https://openai.com/) for GPT-4 content analysis
- The open-source community for the excellent Python libraries

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-repo/issues)
- 💬 [Discussions](https://github.com/your-repo/discussions)

---

**DataForge** - Transform web data into high-quality datasets with AI-powered intelligence.