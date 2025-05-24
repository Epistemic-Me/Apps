from deepdiff import DeepDiff

def diff_cards(old: dict, new: dict) -> str:
    """
    Compute JSON diff between two agent cards using deepdiff.
    """
    diff = DeepDiff(old, new, view='tree')
    return diff.pretty() 