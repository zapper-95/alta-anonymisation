import json
def _fact_string(entry):
    if isinstance(entry, dict):
        return entry.get("fact") or ""
    return entry or ""


def _is_deleted(entry):
    if isinstance(entry, dict):
        return entry.get("fact") in (None, "", "[DELETED]")
    return entry in (None, "", "[DELETED]")


def _parent_index(history, idx):
    """Index of the entry `idx` was derived from. Defensive against missing or
    malformed parent_iter: falls back to the previous index."""
    if idx <= 0:
        return 0
    entry = history[idx]
    parent = entry.get("parent_iter") if isinstance(entry, dict) else None
    if not isinstance(parent, int) or parent < 0 or parent >= idx:
        parent = idx - 1
    return parent


def _walk_back(history, n, start=None):
    """Step back n generations along the parent chain. Returns an index."""
    idx = (len(history) - 1) if start is None else start
    for _ in range(max(0, n)):
        if idx <= 0:
            return 0
        idx = _parent_index(history, idx)
    return idx


def _lineage_indices(history, start=None):
    """Indices from the original to `start`, following parent_iter."""
    idx = (len(history) - 1) if start is None else start
    chain, seen = [idx], {idx}
    while idx > 0:
        parent = _parent_index(history, idx)
        if parent in seen:
            break
        chain.append(parent)
        seen.add(parent)
        idx = parent
    return list(reversed(chain))


def _lineage_values(history, start=None, collapse=True):
    """Values along the lineage, oldest first. Consecutive repeats (from
    identity) are collapsed so the chain stays short."""
    values = []
    for i in _lineage_indices(history, start):
        value = "(deleted)" if _is_deleted(history[i]) else _fact_string(history[i])
        if collapse and values and values[-1] == value:
            continue
        values.append(value)
    return values


def _format_lineage(values, max_items=5):
    """'a' -> 'b' -> 'c', eliding the middle when the chain is long."""
    if len(values) > max_items:
        values = values[:1] + ["..."] + values[-(max_items - 2):]
    return " -> ".join(v if v == "..." else f'"{v}"' for v in values)


def _facts_with_lineage_block(facts, ids, fact_history, max_items=5):
    """
    Numbered current facts, each followed by the values it passed through.
    This replaces the separate history block: the trajectory sits next to the
    fact it belongs to, which is where it is needed.
    """
    lines = []
    for fid, fact in zip(ids, facts):
        lines.append(f"{fid}. {fact}")
        history = fact_history.get(fid) if fact_history else None
        if history and len(history) > 1:
            previous = _lineage_values(history)[:-1]   # drop the current value
            if previous:
                lines.append(f"   previously: {_format_lineage(previous, max_items)}")
    return "\n".join(lines)


def _fact_history_to_block(fact_history, max_items=6):
    """Compact per-fact lineage, oldest to current."""
    if not fact_history:
        return "unknown"
    lines = []
    for fact_id, history in sorted(fact_history.items()):
        chain = _format_lineage(_lineage_values(history), max_items)
        lines.append(f"{fact_id}. {chain}")
    return "\n".join(lines)


def _facts_to_numbered_block(facts, ids=None):
    """
    Number facts by their real (zero-based) fact_id rather than their position,
    so the ids the model sees match the ids the parser expects.
    """
    ids = range(len(facts)) if ids is None else ids
    return "\n".join(f"{fid}. {fact}" for fid, fact in zip(ids, facts))


def _parse_transformation_list(raw, current_facts, current_fact_ids, valid_set,
                               valid_strengths=("low", "medium", "high", "none")):
    """
    Align returned transformations to current_facts and tag each with its
    fact_id, so downstream consumers never have to infer the mapping from
    position.
    """
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, list):
        raw = []

    by_fact = {}
    for item in raw:
        if isinstance(item, dict):
            key = str(item.get("fact", "")).strip()
            if key:
                by_fact[key] = item

    assigned = []
    for i, fact in enumerate(current_facts):
        positional = raw[i] if i < len(raw) and isinstance(raw[i], dict) else None

        # prefer the positional entry when its text agrees, then a text lookup,
        # then the positional entry regardless
        match = None
        if positional is not None and str(positional.get("fact", "")).strip() == fact.strip():
            match = positional
        if match is None:
            match = by_fact.get(fact.strip())
        if match is None:
            match = positional

        transformation = "identity"
        strength = "none"
        if match is not None:
            t = str(match.get("transformation", "")).strip().lower()
            if t in valid_set:
                transformation = t
            s = str(match.get("strength", "")).strip().lower()
            if s in valid_strengths:
                strength = s
        # coherence: identity/delete carry no strength
        if transformation in ("identity", "delete"):
            strength = "none"

        assigned.append({
            "fact_id": current_fact_ids[i],
            "fact": fact,
            "transformation": transformation,
            "strength": strength,
        })
    return assigned


def _parse_distorted_fact_list(raw):
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, list):
        return []
    return [str(f).strip() for f in raw if str(f).strip()]



def _parse_utility_transformation_list(raw, original_facts, valid_set):
    """
    Align returned utility-mode transformations to original_facts by fact_id.

    Expected shape per item: {"fact_id": int, "transformation": str, "n": int}.
    fact_id is zero-based, matching the numbering produced by
    _facts_to_numbered_block. Missing/invalid fact_ids default to identity.
    """
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, list):
        raw = []

    by_id = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        fid = item.get("fact_id")
        try:
            fid = int(fid)
        except (TypeError, ValueError):
            continue
        by_id[fid] = item

    assigned = []
    for fact_id in range(len(original_facts)):
        item = by_id.get(fact_id)
        transformation = "identity"
        n = 1
        if item is not None:
            t = str(item.get("transformation", "")).strip().lower()
            if t in valid_set:
                transformation = t
            try:
                n = int(item.get("n", 1))
            except (TypeError, ValueError):
                n = 1
        assigned.append({
            "fact_id": fact_id,
            "transformation": transformation,
            "n": n,
        })
    return assigned