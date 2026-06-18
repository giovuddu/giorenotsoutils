# GIORE (not so) UTILS

This is a learning project.

After writing the firmware for some "smart" turnstiles for my company, I found
myself in love with the C programming language. Days after the software was
"finished" — so, in maintenance mode — I felt the urge to write more C.

I spent days trying to figure out what the **magnum opus** program I'd write could
be, but I quickly realized:

- good project ideas are hard to find by actively searching for them
- my C skill (low-level programming in general) is too low to even think about
  writing a chunky project from scratch in my free time (of which I don't have
  a lot)

So, while cruising through shell tools to learn them better, I stumbled upon
coreutils' `tail`. 2535 lines of tail. The obvious choice is to rewrite
coreutils in its entirety — without reading the original source code.

## Rules

- I can't read the source code of the util I'm implementing (tail is exempt — I already read it)
- I unlock the ability to read the original source only after completing the util
- A commit is mandatory upon completion
- I can use the original compiled util to test mine against it
- No AI-generated code in any form, and no AI assistance on implementation details
  (no asking an LLM "how should I structure this", no AI autocomplete/autoformat
  guiding my hand). I _can_ freely research algorithms, data structures, APIs and
  general concepts through any source — books, docs, articles, even AI used purely
  as a search/explainer for general theory. The line: theory and concepts are fair
  game; the actual implementation has to come out of my own head and hands.
- I can use every form of tool assisted programming (aka _VIBECODING_ duh) to
  write the comparison tests aganist the original coreutil. **_Here be Python_**

## Roadmap

### Tier 0

- [x] true
- [x] false
- [ ] yes
- [ ] echo
- [ ] pwd
- [ ] basename
- [ ] dirname
- [ ] whoami
- [ ] sleep

### Tier 1

- [ ] cat
- [ ] head
- [ ] tac
- [ ] nl
- [ ] tee
- [ ] wc
- [ ] cp
- [ ] mv
- [ ] rm
- [ ] touch
- [ ] mkdir
- [ ] rmdir
- [ ] ln

### Tier 2

- [ ] cut
- [ ] uniq
- [ ] tr
- [ ] seq
- [ ] fold
- [ ] expand / unexpand
- [ ] head -c / tail -c (byte mode)
- [ ] od
- [ ] split
- [ ] paste
- [ ] comm
- [ ] cksum
- [ ] base64
- [ ] env
- [ ] chmod
- [ ] tail <- the nemesis

### Tier 3

- [ ] sort
- [ ] md5sum / sha256sum
- [ ] printf
- [ ] date
- [ ] factor
- [ ] stat
- [ ] du
- [ ] df
- [ ] ls
