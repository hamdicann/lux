# Microsoft Foundry Local

## Overview

Microsoft Foundry Local is an end-to-end local AI solution for building applications that run entirely on the user's device. It provides native SDKs for C#, JavaScript, Python, and Rust, along with a curated catalog of optimized models and automatic hardware acceleration.

## Key Features

### Lightweight Runtime
The Foundry Local runtime handles model acquisition, hardware acceleration, model management, and inference via ONNX Runtime. The entire runtime is approximately 20 MB, making it easy to distribute with applications.

### Curated Model Catalog
Foundry Local provides a catalog of high-quality models optimized for on-device use. The catalog covers:
- **Chat completions**: GPT OSS, Qwen, DeepSeek, Mistral, and Phi models
- **Audio transcription**: Whisper models
- **Embeddings**: Models for generating text embeddings

Every model undergoes extensive quantization and compression to deliver the best balance of quality and performance on consumer hardware.

### Automatic Hardware Acceleration
Foundry Local detects the available hardware on the user's device and selects the best execution provider:
- **NPU** (Neural Processing Unit): For devices with dedicated AI accelerators
- **GPU**: For NVIDIA, AMD, or Intel graphics processors
- **CPU**: Universal fallback for any system

### Smart Model Management
The full model lifecycle is handled automatically:
1. Models download on first use
2. Models are cached locally for instant subsequent launches
3. The best-performing variant is selected for the user's specific hardware
4. Models are versioned for reproducibility

### OpenAI-Compatible API
Foundry Local supports the OpenAI request and response format. If your application already uses the OpenAI SDK, you can point it to a Foundry Local endpoint with minimal code changes.

## Why Foundry Local for RAG?

Foundry Local is particularly well-suited for RAG (Retrieval-Augmented Generation) applications because:

1. **Privacy**: User data never leaves the device. All prompts, documents, and processing remain local.
2. **Offline capability**: Once models are downloaded, the application works without internet access.
3. **Zero latency**: Responses start immediately with no network round-trip.
4. **No costs**: No per-token charges, no API keys, no subscription required.
5. **No infrastructure**: No backend servers to maintain or scale.

## Using Foundry Local in Python

### Installation
For Windows with hardware acceleration:
```
pip install foundry-local-sdk-winml openai
```

For macOS/Linux:
```
pip install foundry-local-sdk openai
```

### Basic Usage Pattern
1. Initialize the FoundryLocalManager with an app name
2. Get a model from the catalog using its alias
3. Download and load the model
4. Create an OpenAI-compatible client pointing to the local endpoint
5. Use standard OpenAI API calls for chat completions or embeddings

### Model Aliases
Common model aliases include:
- `phi-3.5-mini`: Small, fast chat model (3.8B parameters)
- `qwen2.5-0.5b`: Very small chat model for resource-constrained devices
- `qwen3-embedding-0.6b`: Small embedding model for text vectorization

## Local LLM Considerations

When using local models, keep in mind:

1. **Model size vs. quality**: Smaller models (3-5B parameters) are fast but less capable than large cloud models.
2. **Context window**: Local models typically have smaller context windows (4K-8K tokens).
3. **Hardware requirements**: GPU acceleration significantly improves generation speed.
4. **Memory usage**: Models require several GB of RAM. Phi-3.5-mini needs approximately 2-4 GB.
5. **First-load time**: The initial model download can take several minutes depending on internet speed.
