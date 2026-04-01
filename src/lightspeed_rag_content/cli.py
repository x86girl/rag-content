#!/usr/bin/env python3
# Copyright 2025 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""Simple CLI for creating vector stores from JSON and Markdown files."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from lightspeed_rag_content.document_processor import DocumentProcessor
from lightspeed_rag_content.metadata_processor import MetadataProcessor


class SimpleCLI:
    """Simple CLI for transforming documents into Lightspeed Stack vector stores."""

    def __init__(self):
        """Initialize the CLI."""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            prog="lightspeed-rag-cli",
            description="Transform JSON and Markdown files into vector stores for Lightspeed Stack",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Create vector store from markdown files
  python -m lightspeed_rag_content.cli \\
      --input ./rhel_docs_markdown \\
      --output ./rhel_vector_store \\
      --index-id rhel-docs \\
      --model sentence-transformers/all-mpnet-base-v2

  # Create vector store from JSON file
  python -m lightspeed_rag_content.cli \\
      --input ./data.json \\
      --input-format json \\
      --output ./vector_store \\
      --index-id my-index \\
      --model sentence-transformers/all-mpnet-base-v2

  # Use custom chunk size and overlap
  python -m lightspeed_rag_content.cli \\
      --input ./docs \\
      --output ./vector_db \\
      --index-id docs \\
      --model sentence-transformers/all-mpnet-base-v2 \\
      --chunk-size 512 \\
      --chunk-overlap 128 \\
      --workers 4

For more information, visit: https://github.com/lightspeed-core/rag-content
            """,
        )

        # Required arguments
        required = parser.add_argument_group("required arguments")
        required.add_argument(
            "-i",
            "--input",
            required=True,
            type=str,
            help="Input directory (for markdown) or file (for JSON)",
        )
        required.add_argument(
            "-o",
            "--output",
            required=True,
            type=str,
            help="Output directory for vector store",
        )
        required.add_argument(
            "--index-id",
            required=True,
            type=str,
            help="Unique identifier for the vector store index",
        )
        required.add_argument(
            "-m",
            "--model",
            required=True,
            type=str,
            help="Embedding model name (e.g., sentence-transformers/all-mpnet-base-v2)",
        )

        # Optional arguments
        optional = parser.add_argument_group("optional arguments")
        optional.add_argument(
            "--input-format",
            choices=["markdown", "json"],
            default="markdown",
            help="Input file format (default: markdown)",
        )
        optional.add_argument(
            "--model-dir",
            type=str,
            default="embeddings_model",
            help="Directory containing the embedding model (default: embeddings_model)",
        )
        optional.add_argument(
            "--chunk-size",
            type=int,
            default=512,
            help="Chunk size for text splitting (default: 512)",
        )
        optional.add_argument(
            "--chunk-overlap",
            type=int,
            default=128,
            help="Overlap between chunks (default: 128)",
        )
        optional.add_argument(
            "--workers",
            type=int,
            default=4,
            help="Number of parallel workers (default: 4)",
        )
        optional.add_argument(
            "--vector-store-type",
            choices=["faiss", "postgres", "llamastack-faiss", "llamastack-sqlite-vec", "llamastack-pgvector"],
            default="faiss",
            help="Vector store backend type (default: faiss)",
        )
        optional.add_argument(
            "--base-url",
            type=str,
            default="https://docs.redhat.com",
            help="Base URL for document links (default: https://docs.redhat.com)",
        )
        optional.add_argument(
            "--hermetic",
            action="store_true",
            help="Disable URL reachability checks (for offline/hermetic builds)",
        )
        optional.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose output",
        )

        return parser

    def validate_args(self, args: argparse.Namespace) -> None:
        """
        Validate command-line arguments.

        Args:
            args: Parsed arguments

        Raises:
            SystemExit: If validation fails
        """
        input_path = Path(args.input)

        # Check if input exists
        if not input_path.exists():
            self._error(f"Input path does not exist: {args.input}")

        # Validate input format matches input type
        if args.input_format == "json":
            if not input_path.is_file():
                self._error("For JSON input, --input must be a file, not a directory")
            if not input_path.suffix.lower() == ".json":
                self._error(f"Expected .json file, got: {input_path.suffix}")
        elif args.input_format == "markdown":
            if not input_path.is_dir():
                self._error("For markdown input, --input must be a directory")

        # Validate chunk size and overlap
        if args.chunk_size < 1:
            self._error("Chunk size must be at least 1")
        if args.chunk_overlap < 0:
            self._error("Chunk overlap cannot be negative")
        if args.chunk_overlap >= args.chunk_size:
            self._error("Chunk overlap must be less than chunk size")

        # Validate workers
        if args.workers < 1:
            self._error("Number of workers must be at least 1")

    def _error(self, message: str) -> None:
        """
        Print error message and exit.

        Args:
            message: Error message to display
        """
        print(f"Error: {message}", file=sys.stderr)
        print("\nUse -h or --help for usage information", file=sys.stderr)
        sys.exit(1)

    def _success(self, message: str) -> None:
        """
        Print success message.

        Args:
            message: Success message to display
        """
        print(f"✓ {message}")

    def _info(self, message: str) -> None:
        """
        Print info message.

        Args:
            message: Info message to display
        """
        print(f"ℹ {message}")

    def convert_json_to_markdown(self, json_path: Path, temp_dir: Path) -> Path:
        """
        Convert JSON file to markdown files for processing.

        Args:
            json_path: Path to JSON file
            temp_dir: Temporary directory for markdown files

        Returns:
            Path to directory containing markdown files

        Raises:
            SystemExit: If JSON processing fails
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self._error(f"Invalid JSON file: {e}")
        except Exception as e:
            self._error(f"Failed to read JSON file: {e}")

        # Ensure temp directory exists
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Handle different JSON structures
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try common keys for document lists
            for key in ["documents", "items", "data", "content"]:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break
            # If no list found, treat the dict as a single item
            if not items:
                items = [data]
        else:
            self._error("JSON must be an object or array")

        if not items:
            self._error("No documents found in JSON file")

        self._info(f"Converting {len(items)} JSON documents to markdown...")

        # Convert each item to markdown
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                print(f"Warning: Skipping non-object item at index {idx}", file=sys.stderr)
                continue

            # Get document content and metadata
            content = item.get("content") or item.get("text") or item.get("body") or ""
            title = item.get("title") or item.get("name") or f"Document {idx + 1}"
            url = item.get("url") or item.get("link") or ""

            # Create markdown with YAML frontmatter
            markdown_content = "---\n"
            markdown_content += f"title: {title}\n"
            if url:
                markdown_content += f"url: {url}\n"
            markdown_content += "---\n\n"
            markdown_content += f"# {title}\n\n"
            markdown_content += content

            # Save to file
            filename = f"doc_{idx:05d}.md"
            output_path = temp_dir / filename
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                f.flush()  # Ensure data is written to disk

        self._success(f"Converted {len(items)} documents to markdown")

        # Verify files were created
        md_files = list(temp_dir.glob("*.md"))
        if not md_files:
            self._error(f"Failed to create markdown files in {temp_dir}")

        return temp_dir

    def run(self, args: Optional[argparse.Namespace] = None) -> None:
        """
        Run the CLI.

        Args:
            args: Parsed arguments (if None, will parse from sys.argv)
        """
        if args is None:
            args = self.parser.parse_args()

        # Validate arguments
        self.validate_args(args)

        print("=" * 80)
        print("Lightspeed RAG Content - Vector Store Creation")
        print("=" * 80)
        print(f"Input:              {args.input}")
        print(f"Input format:       {args.input_format}")
        print(f"Output:             {args.output}")
        print(f"Index ID:           {args.index_id}")
        print(f"Embedding model:    {args.model}")
        print(f"Model directory:    {args.model_dir}")
        print(f"Vector store type:  {args.vector_store_type}")
        print(f"Chunk size:         {args.chunk_size}")
        print(f"Chunk overlap:      {args.chunk_overlap}")
        print(f"Workers:            {args.workers}")
        print("=" * 80)
        print()

        # Handle JSON conversion if needed
        input_path = Path(args.input)
        temp_dir = None

        if args.input_format == "json":
            # Note: Don't use hidden directory (starting with .) as SimpleDirectoryReader ignores them
            temp_dir = Path(args.output) / "_temp_markdown"
            input_path = self.convert_json_to_markdown(input_path, temp_dir)

        try:
            # Create metadata processor
            self._info("Initializing metadata processor...")
            metadata_processor = MetadataProcessor(hermetic_build=args.hermetic)

            # Create document processor
            self._info("Initializing document processor...")
            document_processor = DocumentProcessor(
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                model_name=args.model,
                embeddings_model_dir=args.model_dir,
                num_workers=args.workers,
                vector_store_type=args.vector_store_type,
                manual_chunking=True,  # Use manual chunking by default
                doc_type="markdown",
            )

            # Process documents
            self._info("Processing documents...")
            document_processor.process(
                input_path,
                metadata=metadata_processor,
            )

            # Save vector store
            self._info("Saving vector store...")
            document_processor.save(args.index_id, args.output)

            print()
            print("=" * 80)
            self._success("Vector store created successfully!")
            print("=" * 80)
            print(f"Output directory:   {args.output}")
            print(f"Index ID:           {args.index_id}")
            print(f"Vector store type:  {args.vector_store_type}")
            print("=" * 80)
            print()
            print("Next steps:")
            print(f"1. Copy to container:")
            print(f"   podman cp {args.output}/. llama-stack:/opt/app-root/src/.llama/storage/vector_stores/{args.index_id}/")
            print()
            print(f"2. Register in Llama Stack config or via API")
            print()
            print(f"3. Test query:")
            print(f"   curl -X POST http://127.0.0.1:8321/v1/vector_stores/{args.index_id}/query \\")
            print(f"        -d '{{\"query\": \"test query\"}}'")
            print("=" * 80)

        except Exception as e:
            if args.verbose:
                import traceback
                traceback.print_exc()
            self._error(f"Failed to create vector store: {e}")

        finally:
            # Clean up temporary markdown files created from JSON input
            if temp_dir and temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                if args.verbose:
                    self._info(f"Cleaned up temporary directory: {temp_dir}")


def main():
    """Entry point for the CLI."""
    cli = SimpleCLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
