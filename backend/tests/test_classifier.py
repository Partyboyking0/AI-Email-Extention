from backend.app.services.classifier import HeuristicEmailClassifier


def test_classifier_detects_follow_up() -> None:
    result = HeuristicEmailClassifier().classify("Gentle reminder: can you send the report today?")
    assert result.label == "follow-up"
    assert result.model_version == "heuristic-classifier-v3"


def test_classifier_detects_newsletter_by_length() -> None:
    result = HeuristicEmailClassifier().classify("Weekly digest " + ("market update " * 100))
    assert result.label == "newsletter"


def test_classifier_detects_institutional_internship_opportunity() -> None:
    result = HeuristicEmailClassifier().classify(
        "TNP Cell invites IIIT students to apply for an internship opportunity. "
        "Please fill out the form at placement@college.ac.in."
    )
    assert result.label == "opportunity"
    assert result.score > 0.7
