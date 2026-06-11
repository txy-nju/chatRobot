## MODIFIED

### Requirement: Message polling service

The system SHALL run a background polling task that discovers the user's P2P (private) conversations via the Feishu chat search API, verifies each chat's mode, and processes new text messages through the bot engine for automatic reply as the user.

#### Scenario: P2P chats discovered via search endpoint

- **WHEN** the polling service runs
- **THEN** the system SHALL call `GET /im/v1/chats/search` with a non-empty query to discover all visible chats
- **AND** for each returned chat, call `GET /im/v1/chats/{chat_id}` to verify `chat_mode == "p2p"`
- **AND** only process messages from verified P2P chats

> **Delta**: Changed chat discovery from `GET /im/v1/chats` (list endpoint, which excludes P2P) to `GET /im/v1/chats/search` (search endpoint) plus per-chat `chat_mode` verification via `GET /im/v1/chats/{chat_id}`.

#### Scenario: New message detected and replied

- **WHEN** a new text message is found in a verified P2P conversation that was sent by someone other than the authorized user
- **THEN** the system SHALL pass the message to the bot engine for processing and send the generated reply using the user_access_token, with `receive_id_type: "open_id"` and `receive_id` set to the sender's open_id

> **Delta**: Changed reply delivery from `receive_id_type: "chat_id"` to `receive_id_type: "open_id"` so the reply appears in the user-sender P2P chat rather than within the context of the search result.

#### Scenario: Group chats skipped in personal mode

- **WHEN** a chat from search results has `chat_mode != "p2p"`
- **THEN** the system SHALL skip it — group chats are handled by the Bot mode via event subscription
