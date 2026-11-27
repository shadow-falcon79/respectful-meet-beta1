# Respectful Meet — Owner Decisions / Beta Overrides

These decisions are explicit product decisions made after the original cahier/spec and therefore override conflicting draft values for this beta.

1. **VIP/profile capacity: 500**, not 100.
2. **E2EE is prioritized** for private text messaging when the off-platform sharing protection can be enforced before encryption on the client.
3. During the restricted period, the client blocks messages containing phone numbers, email addresses, links, external-platform handles/names and requests to move the conversation to another platform.
4. External contact sharing is eligible for **Premium immediately** or after **20 days** for that conversation. The entitlement is computed by the backend; plaintext remains unavailable to the backend under E2EE.
5. The beta includes **real audio and video calls** using WebRTC signalling. Media is peer-to-peer/TURN and is not recorded by the server.
6. A real beta must not present mock records or fake successful payments as real functionality. When a backend integration is unavailable, the UI must state that it is unavailable rather than fabricate data.

These overrides do not silently change other values from the original specification.
