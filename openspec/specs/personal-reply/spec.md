# personal-reply

## Purpose

Personal assistant reply mode. Allows the bot to act on behalf of a user's personal Feishu account — automatically replying to private messages sent to the user. Uses OAuth authorization to obtain a user_access_token, then polls for new messages on an interval and replies as the user.

## Requirements

### Requirement: OAuth authorization flow

The system SHALL provide an OAuth endpoint that redirects the user to Feishu's authorization page, and a callback endpoint that exchanges the authorization code for a user_access_token and refresh_token.

#### Scenario: User initiates authorization

- **WHEN** user visits `/api/oauth/login` in a browser
- **THEN** the system SHALL redirect to Feishu's OAuth authorization page requesting `im:message`, `im:message.p2p_msg:get_as_user`, and `im:message.group_msg:get_as_user` scopes

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

The system SHALL run a background polling task that checks the user's conversations for new messages every 10 seconds and processes them through the bot engine.

#### Scenario: New message detected and replied

- **WHEN** a new message is found in a user's conversation that was sent by someone else after the last poll timestamp
- **THEN** the system SHALL pass the message to the bot engine for processing and send the generated reply using the user_access_token

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

The system SHALL send replies using the user_access_token so that messages appear to come from the authorized user, not the bot application.

#### Scenario: Reply sent as user

- **WHEN** the bot engine generates a reply for a personal message
- **THEN** the reply SHALL be sent via the Feishu message API with the user_access_token in the Authorization header, making it appear as if the user sent it directly
