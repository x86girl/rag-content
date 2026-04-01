# RAG Content

RAG Content provides a shared codebase for generating vector databases.
It serves as the core framework for Lightspeed-related projects (e.g., OpenShift
Lightspeed, OpenStack Lightspeed, etc.) to generate their own vector databases
that can be used for RAG.

## Quick Start with CLI

The easiest way to use RAG Content is through the `lightspeed-rag` CLI tool, which provides a simple interface for creating vector stores from JSON and Markdown files.

### Installation

#### Via uv (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/lightspeed-core/rag-content.git
cd rag-content

# Install dependencies
uv sync

# Test the CLI
uv run lightspeed-rag --help
```

#### Via Container Image (Recommended for Production)

Pull a prebuilt image:

```bash
# CPU variant (size ~3.7 GB)
podman pull quay.io/lightspeed-core/rag-content-cpu:latest

# GPU variant with CUDA support (size ~12 GB)
podman pull quay.io/lightspeed-core/rag-content-gpu:latest

# Run the CLI from the container
podman run --rm quay.io/lightspeed-core/rag-content-cpu:latest --help
```

Official Red Hat image:

```bash
# Login to Red Hat registry
podman login registry.redhat.io

# Pull the official image
podman pull registry.redhat.io/lightspeed-core/rag-tool-rhel9

# Run the CLI
podman run --rm registry.redhat.io/lightspeed-core/rag-tool-rhel9 --help
```

### Basic Usage

#### Create Vector Store from Markdown Files

```bash
lightspeed-rag \
    --input ./docs \
    --output ./vector_store \
    --index-id my-docs \
    --model sentence-transformers/all-mpnet-base-v2
```

#### Create Vector Store from JSON File

```bash
lightspeed-rag \
    --input ./documents.json \
    --input-format json \
    --output ./vector_store \
    --index-id my-docs \
    --model sentence-transformers/all-mpnet-base-v2
```

#### Using the Container Image

```bash
# Prepare your documents
mkdir -p ./custom_docs/0.1
echo "Vector Database is an efficient way to provide information to LLM" > ./custom_docs/0.1/info.txt

# Run the CLI from the container
podman run --rm \
    -v ./custom_docs:/input:Z \
    -v ./vector_store:/output:Z \
    quay.io/lightspeed-core/rag-content-cpu:latest \
    --input /input/0.1 \
    --output /output \
    --index-id custom-docs-0_1 \
    --model sentence-transformers/all-mpnet-base-v2
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i, --input` | Input directory (markdown) or file (JSON) | Required |
| `-o, --output` | Output directory for vector store | Required |
| `--index-id` | Unique identifier for the vector store | Required |
| `-m, --model` | Embedding model name (HuggingFace repo ID) | Required |
| `--input-format` | Input format: `markdown` or `json` | `markdown` |
| `--model-dir` | Directory containing embedding model | `embeddings_model` |
| `--chunk-size` | Chunk size for text splitting | `512` |
| `--chunk-overlap` | Overlap between chunks | `128` |
| `--workers` | Number of parallel workers | `4` |
| `--vector-store-type` | Vector store type (faiss, postgres, llamastack-*) | `faiss` |
| `--base-url` | Base URL for document links | `https://docs.redhat.com` |
| `--hermetic` | Disable URL reachability checks | `false` |
| `-v, --verbose` | Enable verbose output | `false` |

For more detailed CLI documentation, see [CLI_README.md](CLI_README.md).

## JSON Input Format

The CLI accepts JSON files with document arrays:

```json
[
  {
    "title": "Document 1",
    "content": "Document content here...",
    "url": "https://example.com/doc1"
  }
]
```

Supported keys:
- **Content**: `content`, `text`, `body`
- **Title**: `title`, `name`
- **URL**: `url`, `link`

## Advanced Usage

### Custom Python Scripts

For advanced use cases requiring custom metadata processing or complex workflows, you can use the Python library directly.

#### Installing the Python Library

The `lightspeed_rag_content` library can be installed:
- In the [container image](#via-container-image) or
- Via [uv](#via-uv)

#### Via uv

```bash
uv sync
uv run python -c "import lightspeed_rag_content; print(lightspeed_rag_content.__name__)"
```

#### Custom Script Example

Create a custom processor (`./custom_processor.py`):

```python
from lightspeed_rag_content.metadata_processor import MetadataProcessor
from lightspeed_rag_content.document_processor import DocumentProcessor
from lightspeed_rag_content import utils

class CustomMetadataProcessor(MetadataProcessor):

    def __init__(self, url, hermetic_build=False):
        super().__init__(hermetic_build=hermetic_build)
        self.url = url

    def url_function(self, file_path: str) -> str:
        # Return a URL for the file
        return self.url

if __name__ == "__main__":
    parser = utils.get_common_arg_parser()
    args = parser.parse_args()

    # Instantiate custom Metadata Processor
    metadata_processor = CustomMetadataProcessor("https://www.redhat.com")

    # Instantiate Document Processor
    document_processor = DocumentProcessor(
        chunk_size=args.chunk,
        chunk_overlap=args.overlap,
        model_name=args.model_name,
        embeddings_model_dir=args.model_dir,
        num_workers=args.workers,
        vector_store_type=args.vector_store_type,
    )

    # Load and embed the documents
    document_processor.process(args.folder, metadata=metadata_processor)

    # Save the vector database
    document_processor.save(args.index, args.output)
```

Run the custom script:

```bash
uv run ./custom_processor.py -o ./vector_db -f ./docs -md embeddings_model/ \
    -mn sentence-transformers/all-mpnet-base-v2 -i my-index
```

### YAML Frontmatter Support

Markdown files can include YAML frontmatter for per-document metadata:

```markdown
---
title: My Custom Page Title
url: https://docs.example.com/my-page
---

# Content heading

Document content...
```

Supported frontmatter fields:
- `title`: Document title (overrides extraction from first heading)
- `url`: Document URL (takes priority over `url_function`)

### Hermetic Builds

For offline/air-gapped environments, use the `--hermetic` flag to disable URL reachability checks:

```bash
lightspeed-rag --input ./docs --output ./output --index-id my-index \
    --model sentence-transformers/all-mpnet-base-v2 --hermetic
```

Or in Python:

```python
metadata_processor = CustomMetadataProcessor(hermetic_build=True)
```

## Vector Store Types

### Llama-Index Faiss Vector Store

```bash
lightspeed-rag --input ./docs --output ./vector_db --index-id my-index \
    --model sentence-transformers/all-mpnet-base-v2 --vector-store-type faiss
```

### Llama-Index Postgres (PGVector) Vector Store

Start PostgreSQL with pgvector:

```bash
make start-postgres
```

Generate the vector store:

```bash
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=somesecret \
POSTGRES_HOST=localhost \
POSTGRES_PORT=15432 \
POSTGRES_DATABASE=postgres \
lightspeed-rag --input ./docs --output ./output --index-id my-index \
    --model sentence-transformers/all-mpnet-base-v2 --vector-store-type postgres
```

### Llama-Stack Faiss

```bash
lightspeed-rag --input ./docs --output ./vector_db --index-id my-index \
    --model sentence-transformers/all-mpnet-base-v2 --vector-store-type llamastack-faiss
```

Output structure:
```
vector_db/
└── faiss_store.db       # Vector store + registry metadata
└── llama-stack.yaml     # Reference configuration
```

Query the database:

```bash
python scripts/query_rag.py -p vector_db -x my-index -m embeddings_model \
    -k 5 -q "your query here"
```

### Llama-Stack SQLite-vec

```bash
lightspeed-rag --input ./docs --output ./vector_db --index-id my-index \
    --model sentence-transformers/all-mpnet-base-v2 --vector-store-type llamastack-sqlite-vec
```

### Llama-Stack Postgres (PGVector)

```bash
make start-postgres

POSTGRES_USER=postgres \
POSTGRES_PASSWORD=somesecret \
POSTGRES_HOST=localhost \
POSTGRES_PORT=15432 \
POSTGRES_DATABASE=postgres \
lightspeed-rag --input ./docs --output ./output --index-id my-index \
    --model sentence-transformers/all-mpnet-base-v2 --vector-store-type llamastack-pgvector
```

### Important: Embedding Model Path Portability

When using Llama-Stack vector stores, the embedding model path is written to the configuration as an absolute path. The model must be available at the same path when llama-stack consumes the database.

**Recommendations:**
- Use absolute paths: `-m /app/embeddings`
- Or use HuggingFace IDs: `--model-dir "" -m sentence-transformers/all-mpnet-base-v2`

## Building Container Images Locally

Build the CPU variant:

```bash
podman build -t localhost/lightspeed-rag-content-cpu:latest -f Containerfile .
```

Build the GPU variant:

```bash
podman build -t localhost/lightspeed-rag-content-gpu:latest -f Containerfile-gpu .
```

Test the built image:

```bash
podman run --rm localhost/lightspeed-rag-content-cpu:latest --help
```

## Development

### Running Tests

```bash
make test-unit
```

### Code Quality

```bash
make check-format
make check-types
make check-code-metrics
```

### Updating Dependencies

Update lock file when dependencies change:

```bash
uv lock --upgrade
uv sync
```

For hermetic builds (Konflux):

```bash
# Update Python dependencies
make konflux-requirements

# Update RPM dependencies
make konflux-rpm-lock
```

## Legacy Scripts

The repository includes legacy scripts in `scripts/` for backward compatibility:

- `scripts/generate_embeddings.py` - Original embedding generation script
- `scripts/query_rag.py` - Query vector stores
- `scripts/download_embeddings_model.py` - Download embedding models

These scripts are maintained for compatibility but **the CLI is the recommended approach** for new projects.

## License

Apache License 2.0 - See LICENSE file for details

## Support

- **Issues**: https://github.com/lightspeed-core/rag-content/issues
- **Documentation**: https://github.com/lightspeed-core/rag-content
