# skill-system

## Purpose

Bot personality customization system. Users define the bot's role, tone, reply rules, and knowledge base FAQ. Skills are stored as Markdown files and support dual-mode editing: structured form (A) and raw Markdown (B), with seamless switching between modes.

## Requirements

### Requirement: Skill storage as Markdown files

Each bot personality skill SHALL be stored as a Markdown file with defined sections: `## 角色`, `## 口吻`, `## 回复规则`, and `## 知识库`.

#### Scenario: Create a new skill

- **WHEN** user creates a new skill named "客服小助手" via the Web UI
- **THEN** the system SHALL create a Markdown file with the skill name as title and empty section templates

#### Scenario: Load skill for LLM injection

- **WHEN** the bot engine needs to generate a system prompt
- **THEN** the system SHALL load the active skill's Markdown content and inject it as the system message

### Requirement: Dual-mode skill editing (Form A + Markdown B)

The Web UI SHALL provide two editing modes for skills: structured form mode (A) and raw Markdown mode (B). Users SHALL be able to switch between modes seamlessly.

#### Scenario: Edit skill in form mode

- **WHEN** user opens a skill in form mode
- **THEN** the UI SHALL display parsed fields: role name, role description, tone selector, ordered rules list, and FAQ entries, all editable as form controls

#### Scenario: Edit skill in Markdown mode

- **WHEN** user switches to Markdown mode
- **THEN** the UI SHALL display the raw Markdown text in a text area for free editing

#### Scenario: Switch from form to Markdown

- **WHEN** user switches from form mode to Markdown mode after editing form fields
- **THEN** the system SHALL serialize the form fields back to valid Markdown and display it in the editor

#### Scenario: Switch from Markdown to form

- **WHEN** user switches from Markdown mode to form mode after editing raw Markdown
- **THEN** the system SHALL parse the Markdown into form fields; if parsing is incomplete, the system SHALL preserve unparsed content and warn the user

### Requirement: Skill CRUD operations

The system SHALL support creating, reading, updating, deleting, and listing skills.

#### Scenario: List all skills

- **WHEN** user navigates to the Skill management page
- **THEN** the system SHALL display all skills with their names and last-modified timestamps

#### Scenario: Delete a skill

- **WHEN** user deletes a non-active skill
- **THEN** the system SHALL remove the skill file and database record

#### Scenario: Cannot delete the only active skill

- **WHEN** user attempts to delete a skill that is currently active and it is the only skill
- **THEN** the system SHALL reject the operation and display an error message

### Requirement: Skill activation

Only one skill SHALL be active at a time for a bot instance. Switching the active skill SHALL take effect immediately for new messages.

#### Scenario: Activate a different skill

- **WHEN** user selects a different skill as active and saves
- **THEN** all subsequent incoming messages SHALL use the newly activated skill for reply generation
