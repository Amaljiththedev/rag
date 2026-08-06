-- Evidence is shown as a section name and a page reference, so the page range a
-- chunk spans has to survive ingestion. The chunker already computes these; they
-- previously had nowhere to go.
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS page_start INTEGER;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS page_end INTEGER;

-- Document-level metadata for the workspace list (page count, created date).
CREATE TABLE IF NOT EXISTS document_sets (
    document_set_id TEXT PRIMARY KEY,
    filename        TEXT NOT NULL,
    file_type       TEXT,
    page_count      INTEGER,
    chunk_count     INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
