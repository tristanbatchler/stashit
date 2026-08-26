import secrets
import tomllib
from enum import StrEnum
from pathlib import Path
from typing import cast

from lemminflect import (  # pyright: ignore[reportMissingTypeStubs]
    getInflection,  # pyright: ignore[reportUnknownVariableType]
)


class WordType(StrEnum):
    NOUNS = "nouns"
    VERBS = "verbs"
    ADJECTIVES = "adjectives"
    ADVERBS = "adverbs"


# Nerd shit
class VerbInflection(StrEnum):
    EATS = "VBZ"
    EAT = "VBP"
    EATEN = "VBN"
    EATING = "VBG"
    ATE = "VBD"


_CONFIG_PATH = Path(__file__).parent / "slug_config.toml"

with open(_CONFIG_PATH, "rb") as f:
    data = cast(dict[WordType, list[str]], tomllib.load(f))


def choose(key: WordType) -> str:
    return secrets.choice(data[key])


def inflect_verb(verb: str, tag: VerbInflection) -> str:
    inflections = getInflection(verb, tag=tag)  # pyright: ignore[reportUnknownVariableType]
    if inflections:
        return cast(str, inflections[0])
    return verb

def randomly_inflect_and_prepend_verb(verb: str) -> str:
    tag = secrets.choice(list(VerbInflection))
    new_verb = inflect_verb(verb, tag)
    
    match tag:
        case VerbInflection.ATE:
            prefix = None
        case VerbInflection.EAT:
            prefix = "will"
        case VerbInflection.EATEN:
            prefix = secrets.choice(("had", "has"))
        case VerbInflection.EATING:
            prefix = secrets.choice(("was", "is"))
        case VerbInflection.EATS:
            prefix = None
        case _:  # pyright: ignore[reportUnnecessaryComparison]
            raise NotImplementedError("Not covering all verb inflection tags")  # pyright: ignore[reportUnreachable]

    if prefix is None:
        return new_verb

    return f"{prefix} {new_verb}"

def new_slug() -> str:
    # Load some up to work with

    nouns = [choose(WordType.NOUNS) for _ in range(5)]
    adjectives = [choose(WordType.ADJECTIVES) for _ in range(5)]
    adverbs = [choose(WordType.ADVERBS) for _ in range(5)]
    verbs = [
        randomly_inflect_and_prepend_verb(choose(WordType.VERBS))
        for _ in range(5)
    ]

    templates = (
        (adverbs[0], adjectives[0], nouns[0], verbs[0]),
        (adjectives[0], nouns[0], verbs[0]),
        (nouns[0], verbs[0], adverbs[0]),
        (nouns[0], verbs[0], nouns[1]),
        (nouns[0], verbs[0], adjectives[0], nouns[1]),
        (nouns[0], verbs[0], "and", nouns[1], verbs[1]) # Removed trailing space
    )

    raw_words = secrets.choice(templates)
    
    # Process each segment: split by spaces to handle helper prefixes correctly
    slug_parts: list[str] = []
    for segment in raw_words:
        for word in segment.split():
            slug_parts.append(word.capitalize())

    return "".join(slug_parts)


if __name__ == "__main__":
    for _ in range(100):
        print(new_slug())

    # for key, words in data.items():
    #     print(f"{key}: {len(words)} words")

    # seen: set[str] = set()

    # for _ in range(100_000):
    #     seen.add(new_slug())

    # print(f"Unique: {len(seen):,}")
    # print(f"Collisions: {100_000 - len(seen):,}")
