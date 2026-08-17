# Text Embeddings and Vector Search

## What Are Embeddings?

Text embeddings are dense numerical vector representations of text. They encode the semantic meaning of words, phrases, sentences, or documents into fixed-length arrays of floating-point numbers. Similar texts produce vectors that are geometrically close in the embedding space.

For example, the sentences "The cat sat on the mat" and "A kitten rested on the rug" would have embedding vectors that are close together, even though they share few exact words.

## How Embeddings Are Generated

Embedding models (also called encoder models) are neural networks trained on large text corpora to produce meaningful vector representations. The process:

1. **Tokenization**: Text is split into tokens (words or subwords).
2. **Encoding**: Tokens pass through the neural network layers.
3. **Pooling**: The model's outputs are combined (typically by averaging) into a single vector.
4. **Normalization**: The vector is optionally normalized to unit length.

Common embedding dimensions include 384, 512, 768, and 1024. Larger dimensions can capture more nuanced meaning but require more storage and computation.

## Vector Similarity Metrics

### Cosine Similarity
The most common metric for comparing embeddings. It measures the cosine of the angle between two vectors:

    cos(θ) = (A · B) / (||A|| × ||B||)

- Value of 1.0: Vectors point in exactly the same direction (identical meaning).
- Value of 0.0: Vectors are orthogonal (unrelated meaning).
- Value of -1.0: Vectors point in opposite directions (opposite meaning).

For normalized vectors (unit length), cosine similarity equals the dot product.

### Euclidean Distance
Measures the straight-line distance between two vectors. Smaller distances indicate greater similarity. Less commonly used for text embeddings than cosine similarity.

### Dot Product
For normalized vectors, equivalent to cosine similarity. Faster to compute because it skips the normalization step.

## Vector Search Approaches

### Brute-Force (Exact) Search
Compare the query vector against every stored vector. This approach:
- Guarantees finding the best matches
- Works well for small datasets (up to ~100K vectors)
- Is simple to implement
- Requires no special data structures

### Approximate Nearest Neighbor (ANN) Search
For large datasets, approximate methods trade small accuracy losses for much faster search:
- **FAISS**: Facebook's library for efficient similarity search
- **HNSW**: Hierarchical Navigable Small World graphs
- **IVF**: Inverted File Index with clustering

## Embedding Models for RAG

When choosing an embedding model for a RAG system, consider:

1. **Dimension**: Higher dimensions capture more information but use more storage.
2. **Speed**: Smaller models generate embeddings faster.
3. **Quality**: Measured by retrieval accuracy on benchmark datasets.
4. **Language support**: Some models are trained on multilingual data.

Popular embedding models include:
- **qwen3-embedding-0.6b**: Small, fast, good quality (600M parameters)
- **all-MiniLM-L6-v2**: Compact model with 384 dimensions
- **text-embedding-ada-002**: OpenAI's cloud embedding model (1536 dimensions)

## Chunking Strategies for Embeddings

The quality of embeddings depends heavily on how text is chunked:

### Fixed-Size Chunking
Split text into chunks of a fixed character or token count with overlap. Simple but may break mid-sentence.

### Paragraph-Based Chunking
Split at paragraph boundaries. Preserves natural text structure but produces variable-length chunks.

### Semantic Chunking
Use NLP to identify topic boundaries and split at semantic transitions. Most sophisticated but computationally expensive.

### Recommended Settings
- **Chunk size**: 400-1000 characters (experiment to find optimal)
- **Overlap**: 50-200 characters (maintains context across boundaries)
- **Minimum chunk size**: Skip chunks shorter than 50 characters
