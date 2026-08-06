-- Session isolation: every chunk is tagged with the upload session that created it.
-- All retrieval queries filter on this column, so it needs an index.
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS document_set_id TEXT;
CREATE INDEX IF NOT EXISTS idx_chunks_document_set_id ON chunks (document_set_id);

-- The pre-existing seeded SEC corpus predates this column. Retrieval now always
-- filters by set, so name that corpus rather than leaving it unreachable.
UPDATE chunks SET document_set_id = 'legacy_sec_corpus' WHERE document_set_id IS NULL;
