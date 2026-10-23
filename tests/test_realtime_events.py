import pytest
import asyncio
from backend.app.simulation.events import SimulationEventBus

@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    bus = SimulationEventBus()
    exp_id = "test-exp-events-1"

    queue = await bus.subscribe(exp_id)
    assert queue.empty()

    # Publish an event
    event_payload = {
        "type": "step",
        "user_id": "u-123",
        "action_type": "CLICK",
        "action_target": "#checkout-btn"
    }
    await bus.publish(exp_id, event_payload)

    # Receive event
    received = await asyncio.wait_for(queue.get(), timeout=2.0)
    assert received["type"] == "step"
    assert received["user_id"] == "u-123"
    assert received["action_target"] == "#checkout-btn"
    assert "timestamp" in received
    assert received["experiment_id"] == exp_id

    # Unsubscribe
    await bus.unsubscribe(exp_id, queue)
    await bus.publish(exp_id, {"type": "step", "user_id": "u-999"})
    assert queue.empty()

@pytest.mark.asyncio
async def test_event_bus_buffer_overflow_protection():
    bus = SimulationEventBus()
    exp_id = "test-exp-events-2"
    queue = await bus.subscribe(exp_id)

    # Fill queue past its maxsize without reading
    for i in range(120):
        await bus.publish(exp_id, {"type": "step", "step_number": i})

    # The queue should not crash, it should have capped at 100 items
    assert queue.qsize() == 100
    await bus.unsubscribe(exp_id, queue)
