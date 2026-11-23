import unicodedata

VOWELS = dict(zip("অআইঈউঊঋএঐওঔ", ("o","a","i","i","u","u","ri","e","oi","o","ou")))
MARKS = dict(zip("ািীুূৃেৈোৌ", ("a","i","i","u","u","ri","e","oi","o","ou")))
CONSONANTS = dict(zip(
    "কখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ",
    ("k","kh","g","gh","ng","ch","chh","j","jh","n","t","th","d","dh","n","t","th","d","dh","n","p","f","b","bh","m","j","r","l","sh","sh","s","h","r","rh","y","t"),
))
# Handle both composed and decomposed forms of the dotted letters.
CONSONANTS.update({"ড়":"r","ঢ়":"rh","য়":"y"})
CONSONANTS = {k:v for k,v in CONSONANTS.items() if k != "়"}

def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().replace("\u200c", "").replace("\u200d", "").split())

def romanize(text):
    text = normalize(text).replace("ড\u09bc","ড়").replace("ঢ\u09bc","ঢ়").replace("য\u09bc","য়")
    parts = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in CONSONANTS:
            parts.append(CONSONANTS[char])
            next_char = text[index + 1:index + 2]
            if next_char in MARKS or next_char == "্":
                parts.append(MARKS.get(next_char, ""))
                index += 1
            elif next_char and ("\u0980" <= next_char <= "\u09ff") and next_char not in "ংঃঁ":
                parts.append("o")
        else:
            parts.append(VOWELS.get(char, {"ং":"ng","ঃ":"h","ঁ":"n"}.get(char, char)))
        index += 1
    return "".join(parts)

def embedding_input(text, language):
    # The encoder also receives the original input for Banglish at runtime.
    return normalize(text)
