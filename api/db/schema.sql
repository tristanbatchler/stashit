PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS stashes
(
    id INTEGER PRIMARY KEY NOT NULL,
    is_binary BOOLEAN NOT NULL CHECK (is_binary IN (0, 1)),
    slug TEXT NOT NULL UNIQUE,
    added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stashes_added ON stashes (added);

CREATE TABLE IF NOT EXISTS stashes_text_content
(
    stash_id INTEGER PRIMARY KEY NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (stash_id) REFERENCES stashes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stashes_binary_paths
(
    stash_id INTEGER PRIMARY KEY NOT NULL,
    file_path TEXT NOT NULL,
    FOREIGN KEY (stash_id) REFERENCES stashes(id) ON DELETE CASCADE
);