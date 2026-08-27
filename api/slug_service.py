import secrets
import tomllib
from enum import StrEnum
from pathlib import Path
from typing import cast

from inflect import engine
from lemminflect import (  # pyright: ignore[reportMissingTypeStubs]
    getInflection,  # pyright: ignore[reportUnknownVariableType]
)

p = engine()

class WordType(StrEnum):
    PROPER_NOUNS = "proper_nouns"
    COMMON_NOUNS = "common_nouns"
    VERBS = "verbs"
    ADJECTIVES = "adjectives"
    ADVERBS = "adverbs"
    ARTICLES = "articles"
    CONJUNCTIONS = "conjunctions"


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

wt = WordType
templates = (
    # john ate swiftly
    # (wt.PROPER_NOUNS, wt.VERBS, wt.ADVERBS),
    # john will eat paul
    # (wt.PROPER_NOUNS, wt.VERBS, wt.PROPER_NOUNS),
    # john kicked lazy paul
    (wt.PROPER_NOUNS, wt.VERBS, wt.ADJECTIVES, wt.PROPER_NOUNS),
    # john has eaten so paul ate
    (wt.PROPER_NOUNS, wt.VERBS, wt.CONJUNCTIONS, wt.PROPER_NOUNS, wt.VERBS),
    # lazy john ate early
    (wt.ADJECTIVES, wt.PROPER_NOUNS, wt.VERBS, wt.ADVERBS),
    # john the lazy will eat early
    (wt.PROPER_NOUNS, "the", wt.ADJECTIVES, wt.VERBS, wt.ADVERBS),
    # john and paul eat roy
    (wt.PROPER_NOUNS, "and", wt.PROPER_NOUNS, wt.VERBS, wt.PROPER_NOUNS),
    # john eats paul and roy
    (wt.PROPER_NOUNS, wt.VERBS, wt.PROPER_NOUNS, "and", wt.PROPER_NOUNS),
    # john eats paul with roy
    (wt.PROPER_NOUNS, wt.VERBS, wt.PROPER_NOUNS, "with", wt.PROPER_NOUNS),
    # john ate a rat early
    (wt.PROPER_NOUNS, wt.VERBS, wt.ARTICLES, wt.COMMON_NOUNS, wt.ADVERBS),
    # lazy john ate a rat
    (wt.ADJECTIVES, wt.PROPER_NOUNS, wt.VERBS, wt.ARTICLES, wt.COMMON_NOUNS),
    # a lazy rat ate early
    (wt.ARTICLES, wt.ADJECTIVES, wt.COMMON_NOUNS, wt.VERBS, wt.ADVERBS),
    # the rat ate a lazy bird
    (wt.ARTICLES, wt.COMMON_NOUNS, wt.VERBS, wt.ARTICLES, wt.ADJECTIVES, wt.COMMON_NOUNS),
    # the rat will eat lazy john
    (wt.ARTICLES, wt.COMMON_NOUNS, wt.VERBS, wt.ADJECTIVES, wt.PROPER_NOUNS),
)

def new_slug() -> str:
    template = secrets.choice(templates)

    words: list[str] = []

    # First generate all actual words.
    for token in template:
        if token in WordType and token is not WordType.ARTICLES:
            word = choose(WordType(token))

            if token is WordType.VERBS:
                word = randomly_inflect_and_prepend_verb(word)

            words.append(word)

        elif token is WordType.ARTICLES:
            words.append("")

        else:
            words.append(token)

    # Resolve articles after the surrounding words exist.
    for i, token in enumerate(template):
        if token is not WordType.ARTICLES:
            continue

        noun_index = i + 1

        # Skip adjectives between the article and noun.
        while (
            noun_index < len(template)
            and template[noun_index] is WordType.ADJECTIVES
        ):
            noun_index += 1

        if noun_index >= len(template):
            raise ValueError("ARTICLE has no following noun")

        noun_token = template[noun_index]

        if noun_token not in (
            WordType.COMMON_NOUNS,
            WordType.PROPER_NOUNS,
        ):
            raise ValueError(
                f"ARTICLE must eventually be followed by a noun, got {noun_token!r}"
            )

        # Choose the article from the configured article list.
        article = choose(WordType.ARTICLES)

        # Only "a" needs grammatical adjustment to "an".
        if article == "a":
            phrase = " ".join(words[i + 1 : noun_index + 1])
            article = p.a(phrase).split()[0]  # pyright: ignore[reportArgumentType]

        words[i] = article

    return "".join(
        word.title().replace(" ", "")
        for word in words
    )

def preview_generations():
    for _ in range(1000):
        print(new_slug())

if __name__ == "__main__":
    preview_generations()
