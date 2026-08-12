-- Give stranded transcript rows their speaker back.
--
-- Deleting a speaker while rows still pointed at it left transcript lines
-- referencing an id that no longer exists. The join then yields no name and
-- the UI falls back to a generic "speaker", with no way to rename it — the
-- rows are unreachable from every speaker surface.
--
-- 20260210100000 already tried to clean this up by setting speaker_id to
-- NULL, but it only covered audio_transcriptions (leaving meeting segments
-- broken) and NULL throws away the grouping: which lines belong to the same
-- voice. Recreating the missing rows keeps that grouping intact, so one
-- rename in the transcript can still relabel the whole voice.
--
-- The recreated speaker is nameless, exactly as it was before deletion. Ids
-- are safe to reuse here by definition: an id only appears below because no
-- speakers row holds it, so nothing else can have claimed it.
INSERT INTO speakers (id, name)
SELECT DISTINCT speaker_id, ''
FROM (
    SELECT speaker_id FROM audio_transcriptions
    WHERE speaker_id IS NOT NULL
    UNION
    SELECT speaker_id FROM meeting_transcript_segments
    WHERE speaker_id IS NOT NULL
    UNION
    SELECT speaker_id FROM speaker_embeddings
    WHERE speaker_id IS NOT NULL
    UNION
    SELECT speaker_id FROM diarization_segments
    WHERE speaker_id IS NOT NULL
    UNION
    SELECT speaker_id FROM speaker_identity_evidence
    WHERE speaker_id IS NOT NULL
)
WHERE speaker_id NOT IN (SELECT id FROM speakers);
