## MODIFIED

### Requirement: OAuth authorization flow

The system SHALL provide an OAuth endpoint that redirects the user to Feishu's authorization page, and a callback endpoint that exchanges the authorization code for a user_access_token and refresh_token.

#### Scenario: User initiates authorization

- **WHEN** user visits `/api/oauth/login` in a browser
- **THEN** the system SHALL redirect to Feishu's OAuth authorization page requesting `im:message`, `im:message.send_as_user`, `im:message.p2p_msg:get_as_user`, `im:message.group_msg:get_as_user`, and `im:chat:readonly` scopes

> **Delta**: Added `im:message.send_as_user` (required by Feishu `POST /im/v1/messages` when using `user_access_token`).

#### Scenario: OAuth callback stores tokens

- **WHEN** Feishu redirects back to `/api/oauth/callback` with a valid authorization code
- **THEN** the system SHALL exchange the code for user_access_token and refresh_token, and persist them to the database

#### Scenario: OAuth callback with invalid code

- **WHEN** Feishu redirects back with an invalid or expired code
- **THEN** the system SHALL return an error message and instruct the user to retry authorization

## ADDED

### Requirement: Token auto-refresh

The system SHALL automatically refresh the user_access_token when it is within 5 minutes of expiry, using the stored refresh_token.

#### Scenario: Token refreshed before expiry

- **WHEN** the polling service checks authorization and the access_token is within 5 minutes of expiry
- **THEN** the system SHALL call the Feishu OIDC refresh_access_token endpoint, update the stored tokens in the database, and continue polling

#### Scenario: Token refresh fails

- **WHEN** the refresh_token call returns an error (e.g., refresh_token expired after ~30 days or user revoked authorization)
- **THEN** the system SHALL log a warning, mark the authorization as invalid, and stop the polling service until the user re-authorizes

### Requirement: Chat list pagination

The system SHALL traverse all pages of the Feishu chat list API to ensure no conversations are missed.

#### Scenario: Chat list spans multiple pages

- **WHEN** the user has more than 50 conversations
- **THEN** the system SHALL follow `has_more` and `page_token` to retrieve all pages

#### Scenario: Message list spans multiple pages

- **WHEN** a conversation has more than 10 unread messages between poll cycles
- **THEN** the system SHALL follow `has_more` and `page_token` to retrieve all pages
