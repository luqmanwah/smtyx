# Protocol Guide

## Example: document review

Request:
```json
{
  "protocol": "SMTYX",
  "protocol_version": "0.2",
  "state_id": "st_req_1",
  "parent_state_id": null,
  "trace_id": "tr_doc_1",
  "source": {"kind": "human", "id": "user"},
  "destination": {"kind": "agent", "id": "reviewer"},
  "intent": "ANALYZE",
  "object": "DOCUMENT",
  "status": "PROPOSED",
  "confidence": 1.0,
  "payload": {"goal": "find structural inconsistencies"},
  "evidence": [],
  "permissions": ["document.read"],
  "ack": ["ACK_RECEIVED"]
}
```

Verified finding:
```json
{
  "protocol": "SMTYX",
  "protocol_version": "0.2",
  "state_id": "st_find_1",
  "parent_state_id": "st_req_1",
  "trace_id": "tr_doc_1",
  "source": {"kind": "agent", "id": "reviewer"},
  "destination": {"kind": "orchestrator", "id": "nara"},
  "intent": "REPORT",
  "object": "DOCUMENT_FINDING",
  "status": "VERIFIED",
  "confidence": 0.94,
  "payload": {"finding": "TABLE_NUMBER_SEQUENCE_GAP"},
  "evidence": [{"ref": "document://table/7"}],
  "permissions": [],
  "ack": ["ACK_RECEIVED", "ACK_PARSED", "ACK_SEMANTIC", "ACK_VERIFIED"]
}
```

## Conflict
If two agents disagree, create a new `CONFLICT` state referencing both findings in `payload.conflicting_state_ids`. Do not overwrite either source state.
