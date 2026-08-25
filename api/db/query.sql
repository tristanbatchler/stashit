-- name: GetStash :one
SELECT is_binary, slug, added
FROM stashes
WHERE id = $1;

-- name: GetStashBySlug :one
SELECT id, is_binary, added
FROM stashes
WHERE slug = $1;

-- name: ListStashes :many
SELECT id, is_binary, slug, added
FROM stashes
ORDER BY added DESC, id DESC
LIMIT $1 OFFSET $2;

-- name: GetStashTextContent :one
SELECT content
FROM stashes_text_content
WHERE stash_id = $1;

-- name: GetStashBinaryPath :one
SELECT file_path
FROM stashes_binary_paths
WHERE stash_id = $1;

-- name: CreateStash :one
INSERT INTO stashes (is_binary, slug)
VALUES ($1, $2)
RETURNING id, is_binary, slug, added;

-- name: CreateStashTextContent :exec
INSERT INTO stashes_text_content (stash_id, content)
VALUES ($1, $2);

-- name: CreateStashBinaryPath :exec
INSERT INTO stashes_binary_paths (stash_id, file_path)
VALUES ($1, $2);

-- name: CheckSlugExists :one
SELECT EXISTS (
    SELECT 1
    FROM stashes
    WHERE slug = $1
);