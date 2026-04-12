from app.llm.classifier import LLMClassifier

classifier = LLMClassifier()

tests = [
    "bonjour tout est normal dans la zone",
    "urgence dans le secteur",
    "attaque critique dans la zone"
]

for text in tests:
    result = classifier.classify(text)
    print(f"\nTexte : {text}")
    print(result)