# Public Case Study: EPIC Cache Routing

I built the private system behind this lab while working on EPIC, a 120-page AI
graphic novel project.

The practical problem was continuity. A single generated image can look good
while a long-form sequence breaks down: characters drift, props migrate, camera
angles lose geography, and each new iteration wants to start from zero.

The workflow needed a router. For each panel request, the system had to decide
whether the right next action was exact reuse, semantic reuse, a surgical edit,
a camera or pose change, identity-locked regeneration, or a fresh generation.
The hard part was not only finding similar prior work. It was deciding when
similarity was unsafe.

This public repo is a sanitized reference harness for that decision layer. It
uses synthetic fixtures instead of private EPIC assets, but it preserves the
core product idea:

- track continuity metadata
- explain routing decisions
- prevent unsafe reuse
- cap edit-chain depth
- keep a human reviewer in the loop
- measure avoided generation without hiding risk

The broader lesson is that AI creative tooling needs workflow infrastructure,
not just better prompts. Long-form work succeeds when the system remembers what
matters, knows when not to reuse, and gives the human operator a clear reason
for every automation decision.

