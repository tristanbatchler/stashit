import tomllib
from random import choice
from string import capwords
from typing import Literal, cast

from lemminflect import (  # pyright: ignore[reportMissingTypeStubs]
    getInflection,  # pyright: ignore[reportUnknownVariableType]
)

type WorkTypeKey = Literal["nouns", "verbs", "adjectives", "adverbs"]

with open("slug_config.toml", "rb") as f:
    data = cast(dict[WorkTypeKey, list[str]], tomllib.load(f))


def new_slug() -> str:
    noun = choice(data["nouns"])
    verb = choice(data["verbs"])

    # VBZ = 3rd person singular present (sprints, sings)
    # VBD = past tense (sprinted, sang)
    tag = choice(("VBZ", "VBD"))

    inflections = getInflection(verb, tag=tag)  # pyright: ignore[reportUnknownVariableType]
    if inflections:
        verb = cast(str, inflections[0])

    adjective = choice(data["adjectives"])
    adverb = choice(data["adverbs"])
    return capwords(f"{adjective} {noun} {verb} {adverb}").replace(" ", "")


if __name__ == "__main__":
    print(new_slug())
