# personal-reply

## Purpose

Personal assistant reply mode. Allows the bot to act on behalf of a user's personal Feishu account — automatically replying to private messages sent to the user. Uses OAuth authorization to obtain a user_access_token, then polls for new messages on an interval and replies as the user.

## Requirements

### Requirement: OAuth authorization flow

The system SHALL provide an OAuth endpoint that redirects the user to Feishu's authorization page, and a callback endpoint that exchanges the authorization code for a user_access_token and refresh_token.

#### Scenario: User initiates authorization

- **WHEN** user visits `/api/oauth/login` in a browser
- **THEN** the system SHALL redirect to Feishu's OAuth authorization page requesting `im:message`, `im:message.send_as_user`, `im:message.p2p_msg:get_as_user`, `im:message.group_msg:get_as_user`, and `im:chat:readonly` scopes

#### Scenario: OAuth callback stores tokens

- **WHEN** Feishu redirects back to `/api/oauth/callback` with a valid authorization code
- **THEN** the system SHALL exchange the code for user_access_token and refresh_token, and persist them to the database

#### Scenario: OAuth callback with invalid code

- **WHEN** Feishu redirects back with an invalid or expired code
- **THEN** the system SHALL return an error message and instruct the user to retry authorization

### Requirement: Token management and auto-refresh

The system SHALL store user tokens in the database and automatically refresh the user_access_token before it expires.

#### Scenario: Token refresh before expiry

- **WHEN** the access_token is within 5 minutes of expiry
- **THEN** the system SHALL use the refresh_token to obtain a new access_token and update the database

#### Scenario: Refresh token expired

- **WHEN** the refresh_token has expired (~30 days)
- **THEN** the system SHALL log a warning and stop the polling service until the user re-authorizes

### Requirement: Message polling service

The system SHALL run a background polling task every 10 seconds that discovers the user's P2P (private) conversations via the Feishu chat search API, verifies each chat's mode, and processes new text messages through the bot engine for automatic reply as the user.

#### Scenario: P2P chats discovered via search endpoint

- **WHEN** the polling service runs
- **THEN** the system SHALL call `GET /im/v1/chats/search` to discover all visible chats (which includes P2P chats unlike the list endpoint)
- **AND** for each returned chat, call `GET /im/v1/chats/{chat_id}` to verify `chat_mode == "p2p"`
- **AND** only process messages from verified P2P chats

#### Scenario: Group chats skipped in personal mode

- **WHEN** a chat from search results has `chat_mode != "p2p"` (e.g., group or topic)
- **THEN** the system SHALL skip it — group chats are handled by the Bot mode via event subscription

#### Scenario: New message detected and replied

- **WHEN** a new text message is found in a verified P2P conversation that was sent by someone other than the authorized user
- **THEN** the system SHALL pass the message to the bot engine for processing
- **AND** send the generated reply using the user_access_token with `receive_id_type: "open_id"` and `receive_id` set to the sender's open_id, so the reply appears in the user-sender P2P chat

#### Scenario: Self-sent messages are skipped

- **WHEN** a new message is found that was sent by the authorized user themselves
- **THEN** the system SHALL skip it and not generate a reply

#### Scenario: Already-processed messages are skipped

- **WHEN** a message with a previously seen message_id is encountered
- **THEN** the system SHALL skip it to avoid duplicate replies

#### Scenario: Polling when not authorized

- **WHEN** the polling service runs but no valid user token exists
- **THEN** the system SHALL skip the polling cycle without error

### Requirement: Personal reply sending

The system SHALL send replies using the user_access_token so that messages appear to come from the authorized user, not the bot application. Replies to P2P messages SHALL use `receive_id_type: "open_id"` targeting the sender's open_id, ensuring the reply appears in the user-sender P2P conversation.

#### Scenario: Reply sent as user

- **WHEN** the bot engine generates a reply for a personal message
- **THEN** the reply SHALL be sent via the Feishu message API with the user_access_token in the Authorization header
- **AND** use `receive_id_type: "open_id"` with the sender's open_id, making the reply appear in the user-sender P2P chat as if the user sent it directly
