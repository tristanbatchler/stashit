const API_URL = "http://127.0.0.1:8000/api/v1"

//#region Model interfaces (for now just a copy-paste of api/db/models.py)
export interface Stash {
	id_: number
    is_binary: boolean
    slug: string
    added: string
}

export interface StashesTextContent{
    stash_id: number
    content: string
}
//#endregion

export async function getStashes(): Promise<Stash[]> {
    const response = await fetch(`${API_URL}/stashes/`)

    if (!response.ok) {
        throw new Error(`Failed to fetch stashes: ${response.status} ('${response.statusText}')`);
    }

    return await response.json();
}

export async function getTextStash(slug: String): Promise<StashesTextContent> {
    const response = await fetch(`${API_URL}/stashes/${slug}`)

    if (!response.ok) {
        throw new Error(`Failed to fetch stashes: ${response.status} ('${response.statusText}')`);
    }

    return await response.json();
}