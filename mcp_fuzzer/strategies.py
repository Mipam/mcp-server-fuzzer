from typing import Any, Dict
from hypothesis import strategies as st

Strategy = st.SearchStrategy


def make_fuzz_strategy_from_jsonschema(
    schema: Dict[str, Any], phase: str = "aggressive"
) -> Strategy[Dict[str, Any]]:
    """Create a Hypothesis strategy for the tool's arguments based on JSON Schema."""
    props = schema.get("properties", {})
    strat_dict: Dict[str, Strategy[Any]] = {}
    for arg, prop in props.items():
        typ = prop.get("type", "string")
        if phase == "realistic":
            if typ == "integer":
                strat_dict[arg] = st.integers()
            elif typ == "number":
                strat_dict[arg] = st.floats(allow_nan=False)
            elif typ == "string":
                strat_dict[arg] = st.text()
            elif typ == "boolean":
                strat_dict[arg] = st.booleans()
            elif typ == "object":
                strat_dict[arg] = st.dictionaries(st.text(), st.text())
            elif typ == "array":
                items = prop.get("items", {"type": "string"})
                item_type = items.get("type", "string")
                if item_type == "integer":
                    strat_dict[arg] = st.lists(st.integers())
                elif item_type == "number":
                    strat_dict[arg] = st.lists(st.floats(allow_nan=False))
                elif item_type == "boolean":
                    strat_dict[arg] = st.lists(st.booleans())
                else:
                    strat_dict[arg] = st.lists(st.text())
            else:
                strat_dict[arg] = st.text()
        else:  # aggressive
            strat_dict[arg] = (
                st.none() | st.text() | st.integers() | st.floats(allow_nan=False) | st.booleans()
            )

    return st.fixed_dictionaries(strat_dict)


def make_protocol_fuzz_strategy(phase: str = "aggressive") -> Strategy[Dict[str, Any]]:
    """Create a Hypothesis strategy for fuzzing the JSON-RPC protocol itself."""
    if phase == "realistic":
        return make_realistic_protocol_fuzz_strategy()
    else:
        return make_aggressive_protocol_fuzz_strategy()


def make_realistic_protocol_fuzz_strategy() -> Strategy[Dict[str, Any]]:
    """Create a Hypothesis strategy for generating valid JSON-RPC requests."""
    json_rpc_versions = st.just("2.0")
    methods = st.text(min_size=1, max_size=20)
    params = st.dictionaries(st.text(), st.text()) | st.lists(st.text())
    ids = st.integers() | st.text(min_size=1, max_size=20)

    return st.fixed_dictionaries(
        {"jsonrpc": json_rpc_versions, "method": methods, "params": params, "id": ids}
    )


def make_aggressive_protocol_fuzz_strategy() -> Strategy[Dict[str, Any]]:
    """Create a Hypothesis strategy for generating malformed JSON-RPC requests."""
    json_rpc_versions = st.just("2.0")
    methods = st.text(min_size=1, max_size=20)
    params = st.dictionaries(st.text(), st.text()) | st.lists(st.text())
    ids = st.integers() | st.text(min_size=1, max_size=20) | st.none()

    base_strategy = st.fixed_dictionaries(
        {"jsonrpc": json_rpc_versions, "method": methods, "params": params, "id": ids}
    )

    missing_fields = st.fixed_dictionaries(
        {"method": methods, "params": params, "id": ids}
    )
    invalid_version = st.fixed_dictionaries(
        {"jsonrpc": st.text(), "method": methods, "params": params, "id": ids}
    )
    invalid_method = st.fixed_dictionaries(
        {"jsonrpc": json_rpc_versions, "method": st.integers(), "params": params, "id": ids}
    )
    invalid_params = st.fixed_dictionaries(
        {"jsonrpc": json_rpc_versions, "method": methods, "params": st.text(), "id": ids}
    )

    return st.one_of(
        base_strategy,
        missing_fields,
        invalid_version,
        invalid_method,
        invalid_params,
    )
