# Lightspeed RAG CLI

Simple command-line interface for creating vector stores from JSON and Markdown files for Lightspeed Stack.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/lightspeed-core/rag-content.git
cd rag-content

# Switch to the CLI branch
git checkout feature/simple-cli

# Install dependencies
uv sync
```

### Basic Usage

```bash
# Using the standalone script
./lightspeed-rag --help

# Or using Python module
python -m lightspeed_rag_content.cli --help

# Or with uv
uv run ./lightspeed-rag --help
```

## Examples

### 1. Create Vector Store from Markdown Files

```bash
./lightspeed-rag \
    --input ./rhel_docs_markdown \
    --output ./rhel_vector_store \
    --index-id rhel-docs \
    --model sentence-transformers/all-mpnet-base-v2
```

### 2. Create Vector Store from JSON File

```bash
./lightspeed-rag \
    --input ./documents.json \
    --input-format json \
    --output ./vector_store \
    --index-id my-docs \
    --model sentence-transformers/all-mpnet-base-v2
```

### 3. Custom Configuration

```bash
./lightspeed-rag \
    --input ./docs \
    --output ./vector_db \
    --index-id my-index \
    --model sentence-transformers/all-mpnet-base-v2 \
    --chunk-size 512 \
    --chunk-overlap 128 \
    --workers 4 \
    --vector-store-type faiss \
    --hermetic
```

## Command-Line Options

### Required Arguments

| Option | Description |
|--------|-------------|
| `-i, --input` | Input directory (markdown) or file (JSON) |
| `-o, --output` | Output directory for vector store |
| `--index-id` | Unique identifier for the vector store |
| `-m, --model` | Embedding model name (HuggingFace repo ID) |

### Optional Arguments

| Option | Default | Description |
|--------|---------|-------------|
| `--input-format` | `markdown` | Input format: `markdown` or `json` |
| `--model-dir` | `embeddings_model` | Directory containing embedding model |
| `--chunk-size` | `512` | Chunk size for text splitting |
| `--chunk-overlap` | `128` | Overlap between chunks |
| `--workers` | `4` | Number of parallel workers |
| `--vector-store-type` | `faiss` | Vector store type (`faiss`, `postgres`, etc.) |
| `--base-url` | `https://docs.redhat.com` | Base URL for document links |
| `--hermetic` | `false` | Disable URL reachability checks |
| `-v, --verbose` | `false` | Enable verbose output |
| `-h, --help` | - | Show help message |

## JSON Input Format

The CLI accepts JSON files in multiple formats:

### Array of Documents

```json
[
  {
    "title": "Document 1",
    "content": "Document content here...",
    "url": "https://example.com/doc1"
  },
  {
    "title": "Document 2",
    "content": "More content...",
    "url": "https://example.com/doc2"
  }
]
```

### Object with Documents Array

```json
{
  "documents": [
    {
      "title": "Document 1",
      "content": "Content here..."
    }
  ]
}
```

### Supported Keys

The CLI recognizes these common keys:

- **Content**: `content`, `text`, `body`
- **Title**: `title`, `name`
- **URL**: `url`, `link`
- **Document list**: `documents`, `items`, `data`, `content`

## Output

The CLI creates a vector store compatible with Lightspeed Stack:

```
output_directory/
├── index_id/
│   ├── vector_store files...
│   └── metadata files...
```

## Integration with Lightspeed Stack

### 1. Copy to Container

```bash
podman cp ./rhel_vector_store/. \
    llama-stack-vertexai:/opt/app-root/src/.llama/storage/vector_stores/rhel-docs/
```

### 2. Register in Llama Stack

**Method A: Via API**
```bash
curl -X POST http://127.0.0.1:8321/v1/vector_stores/register \
    -H "Content-Type: application/json" \
    -d '{
        "vector_store_id": "rhel-docs",
        "provider_id": "faiss",
        "vector_db_config": {
            "type": "faiss",
            "dimension": 768
        }
    }'
```

**Method B: Via Config File** (Recommended)

Edit `vertexai-custom-run.yaml`:
```yaml
vector_stores:
  - vector_store_id: rhel-docs
    provider_id: faiss
    vector_db_config:
      type: faiss
      dimension: 768
```

### 3. Test Query

```bash
curl -X POST http://127.0.0.1:8321/v1/vector_stores/rhel-docs/query \
    -H "Content-Type: application/json" \
    -d '{
        "query": "How do I install RHEL?",
        "top_k": 5
    }'
```

## Error Handling

The CLI includes comprehensive error handling:

- **Invalid input paths**: Checks if files/directories exist
- **JSON parsing errors**: Validates JSON structure
- **Argument validation**: Ensures chunk size, overlap, workers are valid
- **Process errors**: Catches and reports processing failures

Use `--verbose` flag for detailed error messages and stack traces.

## Comparison with Custom Scripts

### Before (Custom Script Approach)

```python
# create_custom_processor.py
import sys
sys.path.insert(0, '/path/to/rag-content/src')

from lightspeed_rag_content.metadata_processor import MetadataProcessor
from lightspeed_rag_content.document_processor import DocumentProcessor
from lightspeed_rag_content import utils

class CustomMetadataProcessor(MetadataProcessor):
    # ... custom code ...

if __name__ == "__main__":
    parser = utils.get_common_arg_parser()
    args = parser.parse_args()
    # ... more code ...
```

```bash
uv run --directory /path/to/rag-content python create_custom_processor.py \
    -f ./docs -o ./output -md ./model -mn model-name -i index-id
```

### After (Simple CLI)

```bash
./lightspeed-rag \
    --input ./docs \
    --output ./output \
    --index-id index-id \
    --model model-name
```

## Advanced Features

### Hermetic Builds

For offline/air-gapped environments:

```bash
./lightspeed-rag \
    --input ./docs \
    --output ./output \
    --index-id my-index \
    --model sentence-transformers/all-mpnet-base-v2 \
    --hermetic
```

### Performance Tuning

For large document sets:

```bash
./lightspeed-rag \
    --input ./large_docs \
    --output ./vector_db \
    --index-id large-index \
    --model sentence-transformers/all-mpnet-base-v2 \
    --chunk-size 512 \
    --chunk-overlap 128 \
    --workers 8
```

### Different Vector Store Types

```bash
# PostgreSQL vector store
./lightspeed-rag \
    --input ./docs \
    --output ./output \
    --index-id pg-index \
    --model sentence-transformers/all-mpnet-base-v2 \
    --vector-store-type postgres

# Llama Stack FAISS
./lightspeed-rag \
    --input ./docs \
    --output ./output \
    --index-id ls-index \
    --model sentence-transformers/all-mpnet-base-v2 \
    --vector-store-type llamastack-faiss
```

## Troubleshooting

### "Input path does not exist"
- Check that the path is correct
- Use absolute paths if relative paths don't work

### "Invalid JSON file"
- Validate JSON syntax with `jq . < file.json`
- Check that the JSON structure matches expected format

### "Failed to create vector store"
- Ensure embedding model is downloaded to `--model-dir`
- Check that output directory is writable
- Use `--verbose` for detailed error information

### "Chunk overlap must be less than chunk size"
- Ensure `--chunk-overlap` < `--chunk-size`
- Typical values: chunk size 512, overlap 128

## Development

### Running Tests

```bash
# Run tests (if test suite exists)
uv run pytest

# Test the CLI
./lightspeed-rag --help
```

### Contributing

1. Create a feature branch from `feature/simple-cli`
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

Apache License 2.0 - See LICENSE file for details

## Support

- **Issues**: https://github.com/lightspeed-core/rag-content/issues
- **Documentation**: https://github.com/lightspeed-core/rag-content
- **Lightspeed Stack**: https://github.com/lightspeed-core/lightspeed-stack
