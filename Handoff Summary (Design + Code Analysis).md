Handoff Summary (Design + Code Analysis)

You asked for architectural analysis of the GitHub repo smartbutnot/flightportal and modernization suggestions.

What was done

Cloned the repo locally and analyzed its source.
Reviewed project structure and key files:
flightportal/README.md
flightportal/code.py
flightportal/secrets.py
Moved the repo to:
OneDrive - Cetera Financial Group, Inc/Documents/GitHub/flightportal
Design analysis already completed

Architecture style:
Single-file embedded CircuitPython app centered in flightportal/code.py.
Function-oriented, global-state, polling-loop design for constrained hardware.
Main runtime flow:
Boot + hardware/network/display setup.
Poll FR24 search endpoint for nearby flight IDs.
Fetch details for selected flight.
Parse/map fields to 3 display rows.
Animate plane + scroll text.
Repeat with watchdog feeding and periodic GC.
Key design choices:
Preallocated fixed JSON byte buffer to avoid dynamic memory pressure.
Chunked HTTP response handling and early truncation at trail marker to fit RAM.
Retry/reconnect logic for Wi-Fi failures.
Duplicate-flight suppression with last_flight tracking.
Strengths:
Practical memory strategy for MatrixPortal constraints.
Operational resilience via watchdog and reconnect handling.
Clear display pipeline from API data to rendered rows.
Risks/weak points identified:
Brittle coupling to unofficial FR24 response shape.
Manual JSON truncation logic is fragile to API changes.
Heavy global mutable state.
Transport, parsing, and rendering are tightly coupled in one file.
Limited testability and maintainability.
Improvement recommendations already provided

Hardware

Update MatrixPortal firmware/libs compatibility baseline.
Improve power stability and margin.
Improve Wi-Fi reliability (placement/enclosure).
Add ambient brightness control.
Add RTC/NTP fallback info display.
Improve serviceability (reset/USB accessibility).
Software

Modularize into network/parser/display/controller.
Replace brittle parse assumptions with defensive extraction.
Add config validation/defaults.
Add exponential backoff and clearer error states.
Add de-dup/cache smoothing for noisy flight detection.
Improve observability (structured serial logs, debug mode).
Add parser unit tests with fixture payloads.
Pin dependency versions and document tested CircuitPython version.
If you start a new chat, you can paste this summary and ask for phase-by-phase implementation planning (P0 stability, P1 refactor, P2 features).