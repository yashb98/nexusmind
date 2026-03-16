---
name: social-layer
description: Work on groups, events (hackathon/debate/research/game), connections, invite links, feed aggregation, discovery recommendations, multi-agent group conversations, or any social feature
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Social Layer (Groups, Events, Connections, Feed)

## When to use
Working on groups, events, connections, feed, discovery, invites, or any social feature.

## Groups
Types: interest, skill, project, social. Tables: groups, group_members.
Neo4j: Group node + MEMBER_OF edges. Each group has its own conversation history and insights.
Group conversations use the multi-agent engine (dynamic turn order, 3+ agents).
API: CRUD groups, join/leave, invite, start group conversation, list group insights.

## Events
Types: hackathon, debate, research, game, bookclub, workshop.
Tables: events, event_participants, event_teams. Status: upcoming→live→completed.
Events have schedules (start/end), participant limits, rules (JSONB), results (JSONB).
Event conversations use mode appropriate to type: hackathon→project, debate→socratic, game→play.
Users can spectate live events with tutor commentary.

## Connections
Real people connect via invite links. Connection requests with accept/reject.
New connections start at trust=0.2 (strangers). Trust grows from conversation quality.
Tables: connection_requests, invite_links.
5 mock agents auto-connect to every new user with pre-set trust levels.

## Feed
Activity aggregation from all systems. Table: feed_items.
Types: insight, conversation, community_formed, trust_change, event_result, group_activity, connection_request.
Frontend: reverse-chronological cards with action buttons (Teach me, Accept, View Results).
Feed items created as side effects by ConversationService, GraphService, EventService, ConnectionService.

## Discovery
Recommendations for: agents (interest overlap + compatibility + network proximity), groups (interest match + activity), events (interest match + availability).
API: GET /discover/agents, /discover/groups, /discover/events.

## Navigation
Top-level sections: Home (feed), Network (graph), Groups, Events, Learn (teach-back), Profile.
Each is a separate Next.js page. Existing dashboard content moves to /network.

## Rules
- All group/event data filtered by tenant_id
- Group admins can manage members and settings
- Events respect privacy settings of participants
- Mock agents participate in events and groups like regular agents
- Feed items respect read/unread status
