# Retrieval-Augmented Generation (RAG)

## What is RAG?

Retrieval-Augmented Generation (RAG) is an AI architecture pattern that enhances large language model (LLM) responses by grounding them in externally retrieved information. Rather than relying solely on the model's pre-trained knowledge, RAG systems retrieve relevant documents or passages from a knowledge base and include them as context when generating answers.

## Why RAG Matters

Traditional LLMs have several limitations that RAG addresses:

1. **Knowledge cutoff**: LLMs only know information from their training data. RAG allows them to access current, domain-specific information.
2. **Hallucination**: LLMs can generate plausible-sounding but incorrect information. RAG grounds responses in actual source documents.
3. **Verifiability**: With RAG, answers can cite specific sources, making it possible to verify the information.
4. **Domain specificity**: Organizations can build RAG systems over their own private documents without retraining the entire model.

## How RAG Works

The RAG pipeline consists of two main phases:

### Indexing Phase (Offline)
1. **Document Collection**: Gather the documents that form the knowledge base.
2. **Text Extraction**: Parse documents (PDF, Markdown, TXT) into plain text.
3. **Chunking**: Split documents into smaller passages, typically 200-1000 characters.
4. **Embedding**: Convert each chunk into a numerical vector using an embedding model.
5. **Storage**: Store chunks and their embeddings in a database (e.g., SQLite with vector storage).

### Query Phase (Online)
1. **Query Embedding**: Convert the user's question into a vector using the same embedding model.
2. **Retrieval**: Find the most similar chunks by comparing the query vector to stored vectors.
3. **Ranking**: Score and rank the retrieved chunks by relevance.
4. **Context Assembly**: Combine the top-K most relevant chunks into a context block.
5. **Generation**: Send the context plus the user's question to the LLM.
6. **Response**: The LLM generates an answer grounded in the retrieved context.

## Key Concepts in RAG

### Embeddings
Embeddings are dense numerical vector representations of text. Semantically similar texts produce vectors that are close together in the embedding space. For example, "What is machine learning?" and "Explain ML" would have similar embedding vectors even though the words are different.

### Cosine Similarity
The standard metric for comparing embedding vectors. It measures the angle between two vectors:

    similarity(A, B) = (A · B) / (||A|| × ||B||)

Values range from -1 (opposite) to 1 (identical direction). For text similarity, values above 0.7 typically indicate strong relevance.

### Top-K Retrieval
The process of selecting the K most similar chunks from the knowledge base. Common values are K=3 or K=5. Using too many chunks can overwhelm the LLM's context window; too few may miss relevant information.

### Context Window
The maximum amount of text an LLM can process in a single request. RAG systems must manage a "context budget" to ensure the retrieved chunks plus the prompt fit within this limit.

## RAG vs. Fine-Tuning

| Aspect | RAG | Fine-Tuning |
|--------|-----|-------------|
| Data freshness | Can use latest documents | Frozen at training time |
| Cost | Lower (no retraining) | Higher (GPU compute needed) |
| Transparency | Cites sources | No source attribution |
| Setup complexity | Moderate | High |
| Domain adaptation | Fast (add documents) | Slow (retrain model) |

## Challenges in RAG

1. **Chunk size tuning**: Too small chunks lose context; too large chunks reduce precision.
2. **Retrieval quality**: The answer is only as good as the retrieved context.
3. **Embedding model selection**: Different models produce different quality embeddings.
4. **Prompt engineering**: The LLM must be instructed to use (and only use) the provided context.
5. **Handling unanswerable questions**: The system must recognize when the knowledge base lacks sufficient information.

## Best Practices

- Use overlap between chunks to maintain context continuity.
- Implement similarity thresholds to avoid returning irrelevant results.
- Include source metadata (filename, page number) with each chunk.
- Test with both answerable and unanswerable questions.
- Measure retrieval accuracy separately from generation quality.
- Cache embeddings to avoid regenerating them unnecessarily.
