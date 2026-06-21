import enum

class SeverityLevel(str, enum.Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"
    SEV4 = "SEV4"

class IncidentStatus(str, enum.Enum):
    DETECTED = "detected"
    TRIAGING = "triaging"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"

VALID_TRANSITIONS: dict[IncidentStatus, list[IncidentStatus]] = {
    IncidentStatus.DETECTED: [IncidentStatus.TRIAGING],
    IncidentStatus.TRIAGING: [IncidentStatus.INVESTIGATING],
    IncidentStatus.INVESTIGATING: [IncidentStatus.MITIGATING],
    IncidentStatus.MITIGATING: [IncidentStatus.RESOLVED],
    IncidentStatus.RESOLVED: [IncidentStatus.CLOSED],
    IncidentStatus.CLOSED: [],
}

def validate_transition(current: IncidentStatus, target: IncidentStatus) -> None:
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise InvalidStateTransition(
            f"Cannot transition from '{current.value}' to '{target.value}'. "
            f"Allowed transitions: {[s.value for s in allowed]}"
        )

class InvalidStateTransition(Exception):
    pass
