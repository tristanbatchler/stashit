-- name: GetStash :one
SELECT * FROM stashes WHERE id = ?;

-- name: GetStashBySlug :one
SELECT * FROM stashes WHERE slug = ?;

-- name: ListStashes :many
SELECT *
FROM stashes
ORDER BY added DESC, id DESC
LIMIT ? OFFSET ?;

-- name: GetStashTextContent :one
SELECT * FROM stashes_text_content WHERE stash_id = ?;

-- name: GetStashBinaryPath :one
SELECT * FROM stashes_binary_paths WHERE stash_id = ?;

-- name: CreateStash :one
INSERT INTO stashes (is_binary, slug) VALUES (?, ?)
RETURNING id, is_binary, slug, added;

-- name: CreateStashTextContent :exec
INSERT INTO stashes_text_content (stash_id, content) VALUES (?, ?);

-- name: CreateStashBinaryPath :exec
INSERT INTO stashes_binary_paths (stash_id, path) VALUES (?, ?);

-- name: CheckSlugExists :one
SELECT EXISTS(
    SELECT NULL FROM stashes WHERE slug = ?
    LIMIT 1
);