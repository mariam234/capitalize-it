# import TextRazor NLP API
import textrazor
import re

# Untokenizer from https://github.com/commonsense/metanl/blob/master/metanl/token_utils.py with some edits
def untokenize(words):
    """
    Untokenizing a text undoes the tokenizing operation, restoring
    punctuation and spaces to the places that people expect them to be.
    Ideally, `untokenize(tokenize(text))` should be identical to `text`,
    except for line breaks.
    """
    text = ' '.join(words)
    step0= text.replace("-RRB-", ")").replace("-LRB-", "(").replace("-RSB-", "]").replace("-LSB-", "[").replace("-RCB-", "}").replace("-LCB-", "{")
    step1 = step0.replace("`` ", '"').replace(" ''", '"').replace('. . .', '...')
    step2 = step1.replace(" ( ", " (").replace(" ) ", ") ").replace(" !", "!").replace("$ ", "$").replace("' ", "'").replace(" ?", "?")
    step3 = re.sub(r' ([.,:;?!%]+)([ \'"`])', r"\1\2", step2)
    step4 = re.sub(r' ([.,:;?!%]+)$', r"\1", step3)
    step5 = step4.replace(" '", "'").replace(" n't", "n't").replace("can not", "cannot")
    step6 = step5.replace(" ` ", " '")
    return step6.strip()

# API key
textrazor.api_key = "0f442f18dc5c4a615d5efd556a31725eb6558ccde2a87ce58e5c5674"

# function for properly capitalizing text (including proper nouns and beginning of sentences)
def cap(text):
    # Analyze text for words and entities
    client = textrazor.TextRazor(extractors=["entities", "words"])
    response = client.analyze(text)

    # Add positions of first words of sentences into set
    firstWordPositions = set()
    for sentence in response.sentences():
        # Add position of first word token only, not punctuation
        firstWordPositions.add(sentence.words[next((i for i, word in enumerate(sentence.words) if word.token.isalpha()), 0)].position)

    # Tokenize text and store positions of proper nouns into set for later capitalization (NNP = proper noun singular, NNPS = proper noun plural)
    NNPPositions = set()
    tokens = []
    for word in response.words():
        tokens.append(word.token)
        if word.part_of_speech == "NNP" or word.part_of_speech == "NNPS":
            NNPPositions.add(word.position)

    # Store positions of entities that have types (higher chance it's a named entity or proper noun) into set
    # And store entity ID (formatted entity name) into dict with its position as the key
    entityPositions = set()
    ID = {}
    for entity in response.entities():
        if entity.dbpedia_types and entity.freebase_types:
            for position in entity.matched_positions:
                entityPositions.add(position)
                ID[position] = entity.id

    for position, token in enumerate(tokens):
        # Capitalize word if it's "I" or any contraction of "I"
        if token == "i" or token == "i'm" or token == "i'd" or token == "i'll" or token == "i've":
            tokens[position] = token.capitalize()

        # Capitalize word if it's the beginning of a sentence or a proper noun
        if position in firstWordPositions or position in NNPPositions:
            tokens[position] = token.capitalize()

        # Capitalize word if it's a named entity
        if position in entityPositions:

            # All caps if word has "." because it's probably an acronym
            if "." in token:
                tokens[position] = token.upper()

            # Set word to entity ID (formatted entity name) if it's uppercase and not in time format because it's probably an acronym
            elif ID[position].isupper() and not(":" in ID[position] and "-" in ID[position] and "." in ID[position]):
                # capitalize only acronym word and not words like "the"
                if token.upper() in ID[position]:
                    tokens[position] = ID[position]

            # Capitalize if the word is not numerical and is not a lowercase word in a proper noun phrase and is not "of" or "the"
            elif not ID[position].isdigit() and not(any(x.isupper() for x in ID[position]) and token in ID[position]) and token != "of" and token != "the":
                tokens[position] = token.capitalize()

    # Return untokenized text
    return untokenize(tokens)