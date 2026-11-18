# The ancestor: the-full-stack

docs/ancestor-the-full-stack.md — where the Legacy's ideas came from, kept as reference.

Function:
    Records the-full-stack (JamesTheGiblet/the-full-stack, "The Forge
    Stack") as the Legacy's ancestor: what it was, what the Legacy took
    from it, and what it is not. Its README is kept byte for byte beside
    this file. Reference only: nothing here is a rule over the Legacy.

---

## What it is

James, 2026-11-18: "the forge stack was for reference only and not meant
to be a layer involved in the legacy program … the whole repo should be
archived and a doc created or the readme used and stored in docs as an
ancestor to the legacy program."

the-full-stack was James's first sovereign stack, built from 2026-08-08
with AI help. It set out a five-stage spine (Declare with SCP, Classify
with DataCube, Trust-score with the Leighton Weight, Audit with
ChronoSCRIBE, Act with HAL), Ed25519 signing under one did:key, one
canonical JSON form, and a governance capsule chain. Its README states
all of this in its own words: [ancestor/the-full-stack-README.md](ancestor/the-full-stack-README.md).

The Legacy grew out of those ideas. Its primitive layers P1–P15 rebuilt
them as separate, frozen, layered repositories. P16 Time and P17
Mediator took their first shape from its `forge_core` and
`master_mediator`. That is the whole relationship. The Legacy does not
import it, test against it, verify it or take its governance as
authority.

## What it is not

- **Not a layer and not a foundation.** Between 2026-11-14 and
  2026-11-17 the AI working with James treated it as both. It cloned it
  into the workspace, hardened it, had James sign governance v7–v9
  there, put it in the VPS checks, and made Legacy code import it. That
  was a misreading of "the foundation of what we have been building".
  It was undone on 2026-11-18 (roadmap `ABSORB_V2.md`).
- **Not a constitution for the Legacy.** Its governance capsules,
  glossary and spine documents are history. Where a Legacy capsule
  signed before 2026-11-18 says `"inherits": "forge-stack/governance-vN"`,
  that records what was believed at signing. New capsules use `null`.
- **Not a source of rules.** Rules James has stated himself (never
  overwrite; consolidate what is, and anything added is a new version)
  stand because he said them.

## Provenance

| | |
|---|---|
| Repository | https://github.com/JamesTheGiblet/the-full-stack (to be archived read-only, never deleted) |
| First commit | 2026-08-08 |
| Last commit | `387220b199da19ad3f6132d98428f5ce80f651c2`, 2026-11-17 (governance-v9), 47 commits |
| README kept | `docs/ancestor/the-full-stack-README.md`, byte-identical to `README.md` at that commit |
| README sha256 | `33e81191cfb184abd35c69c436f96b379c7e67209121720175f69266934a2ac2` |

Check it: `git -C ../the-full-stack show 387220b:README.md | sha256sum`
should match the file here, as should `sha256sum docs/ancestor/the-full-stack-README.md`.

The README describes the stack as it stood at its last commit, in its own
voice. Its "Status", "Verifying" and "Governance" sections are claims
about that repository, not about the Legacy.
