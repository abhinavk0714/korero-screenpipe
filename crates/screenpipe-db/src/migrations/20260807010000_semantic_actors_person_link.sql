-- Demote semantic_actors from an identity system to a per-app label cache.
--
-- `semantic_actors` grew its own identity semantics: a name, aliases, and a
-- merge that DELETED the losing row. That gave screenpipe two merge paths with
-- different guarantees — the actor merge was destructive and irreversible,
-- while people merges are soft and auditable. Two merge semantics for "these
-- are the same human" is worse than either alone.
--
-- After this, an actor is what it always actually was: the label a specific app
-- showed for someone, in a specific conversation. Identity lives in `people`.
-- `person_id` is the pointer, and it stays NULL until something with an exact
-- handle claims the actor.
--
-- Existing rows are deliberately NOT backfilled. The actors on a real machine
-- are `[user]`, `[contact]`, `ChatGPT` and `Claude`: directional markers and
-- assistant names. None of them is a person, and none carries a handle, so
-- inventing people for them would be exactly the fabricated identity this
-- design refuses.

ALTER TABLE semantic_actors ADD COLUMN person_id INTEGER
    REFERENCES people(id) ON DELETE SET NULL;

CREATE INDEX idx_semantic_actors_person
    ON semantic_actors(person_id)
    WHERE person_id IS NOT NULL;
