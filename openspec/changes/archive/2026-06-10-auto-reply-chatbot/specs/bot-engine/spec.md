## ADDED Requirements

### Requirement: Core message processing pipeline

The bot engine SHALL process incoming messages through a fixed pipeline: receive message → load active skill → build conversation context → call LLM → send reply.

#### Scenario: Successful reply generation

- **WHEN** an incoming text message is received from a connected platform
- **THEN** the bot engine SHALL load the active skill, construct a system prompt from it, include relevant conversation history, call the LLM, and send the generated reply back to the platform

#### Scenario: LLM call fails

- **WHEN** the LLM call fails (timeout, API error, etc.)
- **THEN** the bot engine SHALL log the error and NOT send a reply (silent failure to avoid spam)

### Requirement: Sliding window conversation memory

The system SHALL maintain a per-channel conversation history using a sliding window with a configurable maximum size, stored entirely in memory.

#### Scenario: Conversation within window limit

- **WHEN** a channel has fewer messages than the `window_size` limit (default 20)
- **THEN** all messages in the channel SHALL be included in the LLM context

#### Scenario: Conversation exceeds window limit

- **WHEN** a channel has more messages than the `window_size` limit
- **THEN** only the most recent `window_size` messages SHALL be included, with the oldest messages dropped

#### Scenario: New channel starts with empty history

- **WHEN** the first message arrives in a channel after bot startup
- **THEN** the system SHALL create a new empty conversation history for that channel

#### Scenario: Bot restart clears all history

- **WHEN** the bot process restarts
- **THEN** all in-memory conversation histories SHALL be cleared

### Requirement: Trigger mode configuration

The system SHALL support configurable reply trigger modes: reply to all messages, or only reply when @mentioned.

#### Scenario: Reply to all messages

- **WHEN** trigger mode is set to "all messages"
- **THEN** the bot SHALL attempt to reply to every incoming text message

#### Scenario: Reply only when @mentioned

- **WHEN** trigger mode is set to "@bot only"
- **THEN** the bot SHALL only reply to messages that explicitly @mention the bot

### Requirement: Reply behavior configuration

The system SHALL allow configuring maximum reply length, response delay, welcome message, and message blacklist.

#### Scenario: Reply truncated to max length

- **WHEN** the LLM generates a reply longer than `max_reply_length`
- **THEN** the system SHALL truncate the reply to the configured limit

#### Scenario: Welcome message on first interaction

- **WHEN** a new user joins a group or sends their first message, and a welcome message is configured
- **THEN** the system MAY send the configured welcome message

#### Scenario: Blacklisted keywords filtered

- **WHEN** an incoming message contains any keyword from the blacklist
- **THEN** the system SHALL ignore the message and not generate a reply
