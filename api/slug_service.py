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

templates = (
    (WordType.ADVERBS, WordType.ADJECTIVES, WordType.NOUNS, WordType.VERBS),
    (WordType.ADJECTIVES, WordType.NOUNS, WordType.VERBS),
    (WordType.NOUNS, WordType.VERBS, WordType.ADVERBS),
    (WordType.NOUNS, WordType.VERBS, WordType.NOUNS),
    (WordType.NOUNS, WordType.VERBS, WordType.ADJECTIVES, WordType.NOUNS),
    (WordType.NOUNS, WordType.VERBS, "and", WordType.NOUNS, WordType.VERBS),
)

def new_slug() -> str:
    template = secrets.choice(templates)

    slug_parts: list[str] = []
    for token in template:
        word: str = token
        if token in WordType:
            word = choose(WordType(token))
            if token is WordType.VERBS:
                word = randomly_inflect_and_prepend_verb(word)

        slug_parts.append(word.title().replace(" ", ""))
        
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
