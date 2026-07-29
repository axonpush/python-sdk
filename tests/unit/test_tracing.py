from axonpush._tracing import TraceContext


def test_w3c_trace_context_uses_valid_identifiers() -> None:
    context = TraceContext()
    span_id = context.next_span_id()

    assert len(context.w3c_trace_id()) == 32
    int(context.w3c_trace_id(), 16)
    assert len(span_id) == 16
    int(span_id, 16)
    assert context.traceparent(span_id) == f"00-{context.w3c_trace_id()}-{span_id}-01"


def test_non_w3c_trace_seed_is_deterministically_mapped() -> None:
    first = TraceContext("customer-trace")
    second = TraceContext("customer-trace")

    assert first.w3c_trace_id() == second.w3c_trace_id()
    assert first.w3c_trace_id() != "0" * 32
