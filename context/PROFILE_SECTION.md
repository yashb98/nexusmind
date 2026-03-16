# PROFILE_SECTION.md — Step 6
# Add a full Profile page. New page, new routes, new endpoints.
# Does not modify any existing pages or components.

## Navigation Change
Add user avatar icon to the header bar that links to /profile:
```
NexusMind  7 agents                              [🔔] [👤 Profile]
```

## Backend Endpoints (NEW)

```python
# src/routes/profile.py (NEW FILE)

GET  /api/v1/users/me
     → Returns: {user: {id, email, display_name}, agent: {full agent object}}

PATCH /api/v1/users/me
     → Body: {display_name?, password?}
     → Updates user account info

PATCH /api/v1/agents/{id}/profile
     → Body: {display_name?, interests?, avatar_image_url?, 
              default_privacy_level?, default_trust_for_strangers?,
              tutor_voice?, tutor_avatar?, tutor_mode_preference?}
     → Updates agent settings. Re-syncs to Neo4j if name/interests change.

POST /api/v1/agents/{id}/retake-quiz
     → Clears personality scores, redirects to onboarding Step 3 (scenarios only)
     → After completion, updates Big Five + domain modifiers + archetype

GET  /api/v1/learner/{user_id}/progress
     → Returns: {topics: [{topic, bloom_level, confidence, last_assessed}], 
                 total_sessions, average_bloom}

GET  /api/v1/agents/{id}/connections-detail
     → Returns: [{agent, trust_level, trust_label, auto_permission, 
                  manual_override, conversation_count, last_interaction}]

PATCH /api/v1/agents/{id}/connections/{target_id}
     → Body: {manual_permission_override?}
     → Set manual permission override for specific connection

DELETE /api/v1/agents/{id}
     → Soft delete agent (mark inactive, remove from graph)

DELETE /api/v1/users/me
     → Delete account + all data (hard delete, with confirmation)
```

## Database Changes
```sql
-- Add to agents table:
ALTER TABLE agents ADD COLUMN tutor_voice VARCHAR(100) DEFAULT 'en-GB-SoniaNeural';
ALTER TABLE agents ADD COLUMN tutor_avatar_url VARCHAR(500);
ALTER TABLE agents ADD COLUMN tutor_mode_preference VARCHAR(20) DEFAULT 'active'
  CHECK (tutor_mode_preference IN ('active', 'passive', 'off'));

-- Add notification preferences table:
CREATE TABLE notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    new_insights BOOLEAN DEFAULT true,
    connection_requests BOOLEAN DEFAULT true,
    community_alerts BOOLEAN DEFAULT true,
    daily_summaries BOOLEAN DEFAULT false,
    weekly_reports BOOLEAN DEFAULT false
);
```

## Frontend: /profile page

```
frontend/src/app/profile/page.tsx

Sections (scrollable page, not tabs):

1. ACCOUNT SETTINGS
   - Display Name (editable text input + Save button)
   - Email (read-only, shown for reference)
   - [Change Password] button → reveals old/new/confirm fields

2. AGENT SETTINGS
   - Agent Name (editable)
   - Avatar (current shown, [Change] button → preset grid or upload)
   - Archetype: shown as badge (derived, not editable)
   - Communication Style: shown (derived)
   
   PERSONALITY (visual):
   - Radar chart (same as onboarding result)
   - Per-trait breakdown bars with values
   - [Retake Personality Quiz] button
   - Confidence score: "88% — answer more questions to improve"
   
   DOMAIN INSIGHTS:
   - Per-domain personality modifiers displayed as pills:
     "In AI: more direct (+0.1 openness)" 
     "In Philosophy: more open (+0.05 agreeableness)"
   
   INTERESTS (editable):
   - Current interests as removable tags [AI ×] [Philosophy ×]
   - [+ Add Interest] button → search/select from taxonomy

3. PRIVACY & TRUST SETTINGS
   - Default Privacy Level: dropdown (Level 1/2/4)
   - Default Trust for New Connections: slider (0.1 - 0.5)
   
   PER-CONNECTION OVERRIDES (table):
   | Agent Name | Trust | Auto Permission | Override | Actions |
   | Dr. Aria   | 0.35  | Level 1        | —        | [Set Override ▼] |
   | Priya      | 0.52  | Level 2        | —        | [Set Override ▼] |
   
   Clicking [Set Override] opens a dropdown to manually set permission level.

4. TUTOR SETTINGS
   - Voice: dropdown of Edge TTS voices (preview button to hear sample)
   - Avatar: select from presets or upload
   - Mode during conversations:
     ● Active (explains + asks questions)
     ○ Passive (brief notes only)
     ○ Off (no tutor during live debates)

5. NOTIFICATION PREFERENCES
   - Checkboxes for each notification type
   - All checked by default except daily summaries and weekly reports

6. LEARNING PROGRESS
   - Topics Learned: count
   - Total Teach-Back Sessions: count
   - Average Bloom Level: number
   - [View Knowledge Map] → expandable table of topics with Bloom bars:
     AI Safety      ████░░ Level 4
     Carbon Scheduling ██░░░░ Level 2
     Free Will      ███░░░ Level 3

7. DANGER ZONE (red border)
   - [Delete Agent] — confirmation dialog → soft delete
   - [Delete Account] — double confirmation → hard delete everything
```

## Styling
Same dark theme as rest of app. Use shadcn/ui components for forms.
Page is a single scrollable column, max-width 768px, centered.
Each section is a card with clear heading.
