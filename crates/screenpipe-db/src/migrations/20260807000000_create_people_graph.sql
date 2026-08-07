-- Canonical people, joined from the identity namespaces screenpipe already has.
--
-- Before this, screenpipe had three disconnected identity systems:
--   * `speakers` (+ embeddings)  — voice, since 2024
--   * `semantic_actors`          — screen, since 2026-07
--   * PersonResolver             — exact handles, never wired to a caller
-- Nothing joined them, so "Drew Thomas" the voice and "[contact]" the screen
-- actor could never be the same person, and neither could ever become an email
-- or a phone number.
--
-- Design rules, enforced here rather than left to callers:
--
--  1. Only exact normalized identifiers join people across sources. A display
--     name is never a join key. `person_identifiers` is UNIQUE on
--     (kind, value), so one handle cannot silently belong to two people.
--  2. Every link to a voice or screen identity is reversible. Links are
--     revoked, never deleted, so a wrong merge can be undone with its evidence
--     intact.
--  3. Confidence is explicit and ordered. A user confirmation outranks any
--     heuristic and is the only thing allowed to contradict one.
--  4. Merges are soft. `merged_into_id` redirects without destroying the
--     merged person's identifiers or links.

CREATE TABLE people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Best known human-readable name. Nullable: a person can be known by a
    -- handle long before a name is observed.
    display_name TEXT
        CHECK (display_name IS NULL OR length(trim(display_name)) BETWEEN 1 AND 256),
    -- Where display_name came from, so a weak guess never overwrites a
    -- user-confirmed name.
    display_name_confidence TEXT NOT NULL DEFAULT 'weak'
        CHECK (display_name_confidence IN ('confirmed', 'strong', 'weak')),
    -- Soft merge target. NULL means this is a live person record.
    merged_into_id INTEGER
        REFERENCES people(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    CHECK (merged_into_id IS NULL OR merged_into_id != id)
);

CREATE INDEX idx_people_display_name
    ON people(display_name COLLATE NOCASE)
    WHERE display_name IS NOT NULL;
CREATE INDEX idx_people_merged_into
    ON people(merged_into_id)
    WHERE merged_into_id IS NOT NULL;

-- Exact, normalized handles. These are the ONLY cross-source join keys.
--   email : lowercased, single '@'
--   phone : explicit E.164, leading '+', no country guessing
--   native: opaque per-source id (slack user id, imessage handle rowid, ...)
--           scoped by `source` so ids cannot collide across systems.
CREATE TABLE person_identifiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL
        REFERENCES people(id) ON DELETE CASCADE,
    kind TEXT NOT NULL
        CHECK (kind IN ('email', 'phone', 'native')),
    -- Provenance of the observation, never used as a join key by itself.
    source TEXT NOT NULL
        CHECK (length(trim(source)) BETWEEN 1 AND 64),
    value TEXT NOT NULL
        CHECK (length(trim(value)) BETWEEN 1 AND 256),
    first_seen_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_seen_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX idx_person_identifiers_person
    ON person_identifiers(person_id);

-- Uniqueness is deliberately split by kind.
--
-- Emails and phones are globally unique in the real world, so the same handle
-- seen through calendar and through Contacts must resolve to the SAME person.
-- Scoping these by source would let one address belong to two people, which is
-- exactly the silent double-identity this table exists to prevent.
CREATE UNIQUE INDEX idx_person_identifiers_global_handle
    ON person_identifiers(kind, value)
    WHERE kind IN ('email', 'phone');

-- Native ids are opaque and only meaningful inside their own system, so they
-- must be namespaced by source. Slack's "U123" and Notion's "U123" are not the
-- same person.
CREATE UNIQUE INDEX idx_person_identifiers_native_handle
    ON person_identifiers(kind, source, value)
    WHERE kind = 'native';

-- Resolution lookup: exact handle -> person, ignoring provenance.
CREATE INDEX idx_person_identifiers_lookup
    ON person_identifiers(kind, value);

-- Reversible links from a canonical person to the identity namespaces that
-- already exist. `target_kind` is closed on purpose: adding a namespace is a
-- migration, not a free-text string.
CREATE TABLE person_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL
        REFERENCES people(id) ON DELETE CASCADE,
    target_kind TEXT NOT NULL
        CHECK (target_kind IN ('speaker', 'semantic_actor')),
    target_id INTEGER NOT NULL,
    confidence TEXT NOT NULL
        CHECK (confidence IN ('confirmed', 'strong', 'weak')),
    -- Allowlisted evidence code. Never free text, never captured content.
    evidence TEXT NOT NULL
        CHECK (evidence IN (
            'user_confirmed',
            'exact_identifier',
            'calendar_attendee',
            'contacts_handle',
            'message_store_handle',
            'connection_directory',
            'single_candidate_meeting'
        )),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- Reversal, not deletion: a revoked link keeps its evidence for audit.
    revoked_at TEXT,
    revoked_reason TEXT
        CHECK (revoked_reason IS NULL OR revoked_reason IN (
            'user_rejected',
            'superseded',
            'ambiguous',
            'source_removed'
        )),
    CHECK (revoked_at IS NOT NULL OR revoked_reason IS NULL)
);

-- One live link per target. Revoked links are exempt so history accumulates.
CREATE UNIQUE INDEX idx_person_links_live_target
    ON person_links(target_kind, target_id)
    WHERE revoked_at IS NULL;
CREATE INDEX idx_person_links_person
    ON person_links(person_id, target_kind);
