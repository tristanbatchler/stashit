import secrets
import tomllib
from enum import StrEnum
from typing import Literal, cast

from lemminflect import (  # pyright: ignore[reportMissingTypeStubs]
    getInflection,  # pyright: ignore[reportUnknownVariableType]
)


class WordType(StrEnum):
    NOUNS = "nouns"
    VERBS = "verbs"
    ADJECTIVES = "adjectives"
    ADVERBS = "adverbs"


with open("slug_config.toml", "rb") as f:
    data = cast(dict[WordType, list[str]], tomllib.load(f))


def choose(key: WordType) -> str:
    return secrets.choice(data[key])


def inflect_verb(verb: str, tag: Literal["VBZ", "VBD"]) -> str:
    inflections = getInflection(verb, tag=tag)  # pyright: ignore[reportUnknownVariableType]
    if inflections:
        return cast(str, inflections[0])
    return verb


def new_slug() -> str:
    noun = choose(WordType.NOUNS)
    adjective = choose(WordType.ADJECTIVES)
    adverb = choose(WordType.ADVERBS)
    verb = choose(WordType.VERBS)

    templates = (
        # Adverb + adjective + noun + verb
        lambda: (
            adverb,
            adjective,
            noun,
            inflect_verb(verb, "VBZ"),
        ),
        # Adjective + noun + verb + adverb
        lambda: (
            adjective,
            noun,
            inflect_verb(verb, "VBZ"),
            adverb,
        ),
        # Adjective + noun + verb + noun
        lambda: (
            adjective,
            noun,
            inflect_verb(verb, "VBZ"),
            choose(WordType.NOUNS),
        ),
        # Adverb + adjective + noun + verb + adverb
        lambda: (
            adverb,
            adjective,
            noun,
            inflect_verb(verb, "VBZ"),
            choose(WordType.ADVERBS),
        ),
        # Adverb + adjective + noun + verb + noun
        lambda: (
            adverb,
            adjective,
            noun,
            inflect_verb(verb, "VBZ"),
            choose(WordType.NOUNS),
        ),
        # Adjective + noun + past verb + adverb
        lambda: (
            adjective,
            noun,
            inflect_verb(verb, "VBD"),
            adverb,
        ),
        # Adjective + noun + past verb + noun
        lambda: (
            adjective,
            noun,
            inflect_verb(verb, "VBD"),
            choose(WordType.NOUNS),
        ),
    )

    words = secrets.choice(templates)()
    return "".join(word.capitalize() for word in words)


if __name__ == "__main__":
    for key, words in data.items():
        print(f"{key}: {len(words)} words")

    seen: set[str] = set()

    for _ in range(100_000):
        seen.add(new_slug())

    print(f"Unique: {len(seen):,}")
    print(f"Collisions: {100_000 - len(seen):,}")
