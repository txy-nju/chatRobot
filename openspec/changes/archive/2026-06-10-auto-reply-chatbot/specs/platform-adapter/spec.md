## ADDED Requirements

### Requirement: Unified message model

The system SHALL define a platform-independent message model that normalizes all incoming messages into a common structure.

#### Scenario: Incoming text message normalization

- **WHEN** a message arrives from any supported platform
- **THEN** the system SHALL convert it to an `IncomingMessage` with fields: `platform`, `channel_id`, `user_id`, `content` (plain text), `message_type`, and `raw` (original payload)

#### Scenario: Outgoing reply message

- **WHEN** the bot engine generates a reply
- **THEN** the system SHALL wrap it in an `OutgoingMessage` with `content` and `reply_to` (reference to the original IncomingMessage)

### Requirement: Platform adapter abstract interface

All platform adapters SHALL implement the `BasePlatform` interface with methods: `verify()`, `parse_message()`, and `send_message()`.

#### Scenario: New platform adapter registration

- **WHEN** a new platform adapter class implements `BasePlatform`
- **THEN** it SHALL be discoverable and usable by the bot engine without changes to core logic

### Requirement: Feishu URL verification

The system SHALL handle Feishu's event subscription URL verification by returning the challenge token when receiving a verification request.

#### Scenario: Feishu challenge verification

- **WHEN** Feishu sends a POST with `{"challenge": "abc123", "token": "xxx", "type": "url_verification"}`
- **THEN** the system SHALL respond with `{"challenge": "abc123"}`

### Requirement: Feishu message receiving

The system SHALL receive and parse text messages from Feishu, extracting user ID, chat ID, and message content.

#### Scenario: Receive text message from Feishu group

- **WHEN** Feishu sends a message event to the webhook endpoint with a text message body
- **THEN** the system SHALL extract the content, sender ID, and chat ID, and pass a normalized `IncomingMessage` to the bot engine

### Requirement: Feishu message sending

The system SHALL send text replies back to Feishu via the Feishu Open API.

#### Scenario: Send reply to group chat

- **WHEN** the bot engine provides an `OutgoingMessage` with content and a Feishu channel ID
- **THEN** the system SHALL call the Feishu API to send the message to the correct chat

### Requirement: Platform configuration via Web UI

The system SHALL allow users to configure platform connection parameters (App ID, App Secret, verification token) through the Web admin UI.

#### Scenario: Configure Feishu connection

- **WHEN** user enters Feishu App ID, App Secret, and verification token in the Web UI and saves
- **THEN** the system SHALL persist the configuration and display the webhook URL for the user to copy into Feishu's developer console
