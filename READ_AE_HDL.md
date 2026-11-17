## Risk Triad Formalization

| Factor | Flight booking | Malware |
|---|---|---|
| **Autonomy** (α = 0) | `abl_no_autonomy`: `human_approval=True` in `book_flight` | `abl_no_autonomy`: `human_approval=True` in `quarantine_endpoints` |
| **Delegation** (restricted Δ) | `abl_no_delegation`: `credential_scope=[OFFICIAL_DOMAIN]` | `abl_no_delegation`: `batch_cap=1` |
| **Operative power** (Ω without WRITE) | `abl_no_operative`: `WRITE` removed, so `book_flight` is denied | `abl_no_operative`: `WRITE` removed, so `quarantine_endpoints` is denied |

The baseline is α = 1 with full Δ and Ω.

1. **Autonomy gate is simulated.** The reviewer uses oracle knowledge (`mVerified` in flight booking, `KNOWN_GOOD_HASHES` in malware). It is not a generic human gate.
2. **Delegation bounds, it does not always block.** With `batch_cap=1`, one endpoint is still quarantined, so the malware ASR ("at least one endpoint") stays high. The effect shows only in endpoints affected. Say "blocks or bounds" in the text, as drafted.
3. **CAM controls are outside the formalisation.** Corroboration, verified domain and price floor are in-code controls that intercept without a human, so they are not triad factors. Reword my sentence "reaches execution unintercepted only if α = 1" to "reaches execution without human interception only if α = 1".

### Alternative models
| Model (Ollama tag) | Parameters | Developer | Why |
|---|---|---|---|
| `granite3.3:2b` | 2B | IBM | Small and fast, and a new developer, so more variety |
| `llama3.2:3b` | 3B | Meta | Same family as your 1B, so less variety |
| `phi4-mini:3.8b` | 3.8B | Microsoft | Newer Phi, usually follows "reply only JSON" better, but similar size |
| `smollm2:1.7b` | 1.7B | Hugging Face | Very fast |
