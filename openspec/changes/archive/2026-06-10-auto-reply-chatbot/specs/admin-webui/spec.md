## ADDED Requirements

### Requirement: Skill editor page

The Web UI SHALL provide a skill management page with a skill list sidebar and a dual-mode editor panel.

#### Scenario: Skill list and selection

- **WHEN** user opens the admin UI
- **THEN** the left sidebar SHALL show all existing skills with the active one highlighted, and a "+" button to create new skills

#### Scenario: Toggle between form and Markdown editor

- **WHEN** user clicks the mode toggle switch
- **THEN** the editor SHALL transition between form mode and Markdown mode without losing unsaved changes

### Requirement: LLM configuration page

The Web UI SHALL provide an LLM configuration page where users can select the provider, model, enter API key and base URL, and test the connection.

#### Scenario: Provider dropdown filters available models

- **WHEN** user selects a provider from the dropdown (e.g., OpenAI)
- **THEN** the model dropdown SHALL update to show only models available from that provider

#### Scenario: Test connection feedback

- **WHEN** user clicks "Test Connection" with valid credentials
- **THEN** the UI SHALL display "Connected successfully" with the response latency

#### Scenario: Test connection failure

- **WHEN** user clicks "Test Connection" with invalid credentials
- **THEN** the UI SHALL display the specific error message from the LLM provider

### Requirement: Bot behavior configuration page

The Web UI SHALL provide a behavior configuration page with settings for trigger mode, max reply length, window size, response delay, welcome message, and keyword blacklist.

#### Scenario: Adjust sliding window size

- **WHEN** user changes the window size slider/input to 30 and saves
- **THEN** the system SHALL use 30 messages as the conversation window for subsequent replies

#### Scenario: Add keywords to blacklist

- **WHEN** user adds a keyword to the blacklist and saves
- **THEN** messages containing that keyword SHALL be ignored by the bot

### Requirement: Platform configuration page

The Web UI SHALL provide a platform configuration page showing connection status for each supported platform and configuration forms.

#### Scenario: Feishu configuration form

- **WHEN** user navigates to the platform configuration page
- **THEN** the UI SHALL display a form for Feishu with fields: App ID, App Secret, Verification Token, Encryption Key (optional), and show the webhook URL and connection status

#### Scenario: Copy webhook URL

- **WHEN** user clicks the copy button next to the webhook URL
- **THEN** the webhook URL SHALL be copied to the clipboard

### Requirement: Chat test console

The Web UI SHALL provide a chat test console where users can send test messages and see bot replies using the current skill and LLM configuration.

#### Scenario: Send test message

- **WHEN** user types a test message and presses Enter
- **THEN** the system SHALL process the message through the full pipeline (excluding actual platform delivery) and display the generated reply with metadata (word count, latency)

#### Scenario: Clear test conversation

- **WHEN** user clicks "Clear conversation"
- **THEN** the test console's message history SHALL be cleared

### Requirement: Static file serving

The admin Web UI SHALL be served by FastAPI as static files, requiring no separate frontend build step or server.

#### Scenario: Access admin UI at root path

- **WHEN** user navigates to `http://<host>/` in a browser
- **THEN** the admin Web UI SHALL load and display the skill editor page
