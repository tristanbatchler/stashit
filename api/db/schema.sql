CREATE TABLE IF NOT EXISTS stashes
(
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    is_binary  BOOLEAN NOT NULL,
    slug       TEXT NOT NULL UNIQUE,
    added      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stashes_added ON stashes (added);

CREATE TABLE IF NOT EXISTS stashes_text_content
(
    stash_id  BIGINT PRIMARY KEY
              REFERENCES stashes (id) ON DELETE CASCADE,
    content   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stashes_binary_paths
(
    stash_id  BIGINT PRIMARY KEY
              REFERENCES stashes (id) ON DELETE CASCADE,
    file_path TEXT NOT NULL
);