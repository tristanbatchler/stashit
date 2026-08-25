-- name: GetStash :one
SELECT is_binary, slug, added FROM stashes WHERE id = ?;

-- name: GetStashBySlug :one
SELECT id, is_binary, added FROM stashes WHERE slug = ?;

-- name: ListStashes :many
SELECT id, is_binary, slug, added
FROM stashes
ORDER BY added DESC, id DESC
LIMIT ? OFFSET ?;

-- name: GetStashTextContent :one
SELECT content FROM stashes_text_content WHERE stash_id = ?;

-- name: GetStashBinaryPath :one
SELECT file_path FROM stashes_binary_paths WHERE stash_id = ?;

-- name: CreateStash :one
INSERT INTO stashes (is_binary, slug) VALUES (?, ?)
RETURNING id, is_binary, slug, added;

-- name: CreateStashTextContent :exec
INSERT INTO stashes_text_content (stash_id, content) VALUES (?, ?);

-- name: CreateStashBinaryPath :exec
INSERT INTO stashes_binary_paths (stash_id, file_path) VALUES (?, ?);

-- name: CheckSlugExists :one
SELECT EXISTS(
    SELECT NULL FROM stashes WHERE slug = ?
    LIMIT 1
);