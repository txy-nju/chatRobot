# llm-provider

## Purpose

Multi-LLM provider abstraction layer. Provides a unified chat interface across OpenAI, Anthropic, DeepSeek, and future providers. Supports environment-variable-based auto-assembly so switching providers requires only changing an env var.

## Requirements

### Requirement: LLM Factory auto-assembles provider from environment variable

The system SHALL read the `LLM_PROVIDER` environment variable and automatically instantiate the corresponding LLM adapter with credentials from provider-specific environment variables.

#### Scenario: OpenAI provider configured

- **WHEN** `LLM_PROVIDER=openai` and `OPENAI_API_KEY` is set
- **THEN** the system SHALL create an OpenAI adapter using the configured API key and model

#### Scenario: Anthropic provider configured

- **WHEN** `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` is set
- **THEN** the system SHALL create an Anthropic adapter using the configured API key and model

#### Scenario: DeepSeek provider configured

- **WHEN** `LLM_PROVIDER=deepseek` and `DEEPSEEK_API_KEY` is set
- **THEN** the system SHALL create a DeepSeek adapter using the configured API key and model

#### Scenario: Unsupported provider

- **WHEN** `LLM_PROVIDER` is set to an unsupported value
- **THEN** the system SHALL raise a clear error listing supported providers

#### Scenario: Missing API key

- **WHEN** `LLM_PROVIDER` is set but the corresponding API key environment variable is empty
- **THEN** the system SHALL raise a clear error indicating which environment variable is missing

### Requirement: Unified LLM chat interface

All LLM adapters SHALL implement a common `BaseLLMClient` interface with a `chat` method that accepts a list of messages and returns a string response.

#### Scenario: Chat with system and user messages

- **WHEN** `chat()` is called with a system message and a user message
- **THEN** the adapter SHALL return a non-empty string response from the model

#### Scenario: Chat with conversation history

- **WHEN** `chat()` is called with multiple user/assistant message pairs plus a new user message
- **THEN** the adapter SHALL include the full message list in the request and return a contextually relevant response

### Requirement: Custom base URL support

Each LLM adapter SHALL support an optional base URL configuration for API proxy or self-hosted endpoint use.

#### Scenario: Custom OpenAI-compatible endpoint

- **WHEN** `OPENAI_BASE_URL` is set to a custom endpoint (e.g., `https://api.custom.com/v1`)
- **THEN** the OpenAI adapter SHALL send requests to that endpoint instead of the default `https://api.openai.com/v1`

### Requirement: LLM configuration modifiable via Web UI

The system SHALL allow users to view and update LLM configuration (provider, model, API key, base URL) through the Web admin UI, with changes persisted to the database.

#### Scenario: Change LLM provider via Web UI

- **WHEN** user selects a new provider and model in the Web UI and saves
- **THEN** the system SHALL update the active LLM configuration and subsequent calls SHALL use the new provider

#### Scenario: Test LLM connection via Web UI

- **WHEN** user clicks "Test Connection" in the Web UI
- **THEN** the system SHALL send a minimal test message to the configured LLM and display success or failure
