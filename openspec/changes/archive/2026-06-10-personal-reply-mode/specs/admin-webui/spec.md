## ADDED Requirements

### Requirement: Personal assistant page

The Web UI SHALL provide a personal assistant page showing OAuth authorization status, polling status, and usage statistics. Users SHALL be able to initiate or re-authorize from this page.

#### Scenario: View authorization status when authorized

- **WHEN** user navigates to the personal assistant page and a valid user token exists
- **THEN** the UI SHALL display "已授权" with the authorized user's open_id, token expiry time, and a "重新授权" button

#### Scenario: View authorization status when not authorized

- **WHEN** user navigates to the personal assistant page and no valid token exists
- **THEN** the UI SHALL display "未授权" with a "授权" button that links to `/api/oauth/login`

#### Scenario: View polling status

- **WHEN** user navigates to the personal assistant page
- **THEN** the UI SHALL display the polling service status (running/stopped), last poll time, number of monitored conversations, and today's reply count
