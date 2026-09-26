# How TRIPWIRE works (the intuitive version)

This is the plain-language introduction to the chip. Read it first, before `docs/design/OVERVIEW_TRIPWIRE.md` and `docs/design/ARCHITECTURE.md`, which say the same things with the real names, numbers and exact rules. It describes the design as frozen at the end of phase 1 (spec v1.0, DECISIONS D-037).

---

## The job

The outside world (other chips) talks to us through wires. Every protocol (UART, I2C, SPI…) is like a different language, with strict rules about *timing*: when to speak, when to listen, how fast. TRIPWIRE is one chip that can be programmed to speak many of these languages.

## The kitchen analogy

Think of the chip as a **restaurant kitchen**.

| Chip part | Kitchen version | What it really does |
|---|---|---|
| **Pins** | The serving windows to the dining room | The physical wires connected to the outside world |
| **Pin units** | **Waiters** at the windows | Handle the *timing* of talking on the wires: "say these 8 things, one every 2 seconds", "listen and write down what the customer says" |
| **Tokens** | **Order tickets** | A small note carrying one piece of info, like "received the letter A" or "please send 8 bits" |
| **Channel fabric** | The **ticket rail** between waiters and cooks | The wiring that carries tickets from whoever writes them to whoever needs them |
| **Lanes** | **Cooks** | Make the *decisions*: "a ticket says the customer asked for X, so we do Y" |
| **Rules (reflex slots)** | Each cook's **list of 12 reflexes**, taped to the wall | "*If* a ticket says 'address 42' *then* shout back 'yes, that's me'" |
| **Routines / SRAM** | The **recipe book** on the shelf | Longer, slower tasks (like adding up a checksum) that don't fit in 12 reflexes |
| **Host** | The **manager** who comes in before opening | Another computer that loads everyone's instructions, starts and stops the kitchen, and checks for problems |

## Why split it this way?

Each part does **one kind of job**:
- **Waiters (pin units) are good at timing and bad at thinking.** They hit exact moments on the wire, down to 20 ns, but they don't decide anything.
- **Cooks (lanes) are good at deciding and don't worry about timing.** They just react to tickets.
- **Tickets on a rail (tokens on the fabric)** keep them separate. Waiters and cooks never need to know how the other works.

So a new protocol needs no new hardware. You give the waiters new timing settings and the cooks new reflex lists. That's the "firmware-programmable" part the competition asks for. It is also why we never build a protocol-specific block (an "I2C block", an "SPI block"): every part stays general (DECISIONS D-012).

## What makes our cooks special

A normal processor is like a cook reading a recipe **line by line**: step 1, step 2, step 3… If something urgent happens, it has to finish its current line before noticing.

Our cooks don't read line by line. They glance at **all 12 reflexes at once, every instant**, and whichever one matches, they do it immediately. Think of a goalkeeper, not someone reading a manual. So the reaction time is always the same: **7 clocks = 140 billionths of a second**, from a wire changing to our answer on a wire.

The recipe book (routines) is for jobs that aren't urgent. A cook works on a recipe between reflexes, and drops it instantly if a reflex fires.

## One example, start to finish (a UART echo)

1. A byte arrives on a wire. The **waiter** (pin unit) listens at the right speed and writes the byte on a **ticket** (token).
2. The ticket goes along the **rail** (fabric) to a **cook** (lane).
3. The cook's reflex says "if a ticket arrives, pass it to the waiter at the other window". It writes a new ticket.
4. The rail carries it to the second waiter, who sends the byte out on another wire at exactly the right speed.

## Our kitchen's size

- **6 waiters** (pin units), who share **19 serving windows** (pins). Two are all-rounders; the other four do the common jobs, which is all most protocols need (DECISIONS D-040)
- **3 cooks** (lanes), each with **12 reflexes**
- **1 recipe book** (512 lines of SRAM), which the cooks take turns reading
- **1 manager** (host), who talks to the chip over SPI from the Tiny Tapeout demo board

---

## The same thing, a level closer to the real chip

Once the kitchen picture makes sense, these are the details that matter.

**1. Pin units are *set up* by firmware and *told what to do* by lanes. They don't run firmware themselves.**
- Before the chip starts, the host loads each pin unit's **settings**: which pins it uses, what speed, and which mode (plain serial, clocked like SPI or I2C, pulses like WS2812, and so on).
- While running, lanes send it **commands** as tokens, for example "send these 8 bits" or "drive the pin low in 30 ticks".

So the protocol definition is split in two:
- the **timing** part lives in the pin unit settings;
- the **logic** part lives in the lanes' rules (and routines).

Together, those are "the firmware".

**2. A token is smaller than a packet.** A token is one small word: 16 bits of data plus a 2-bit label saying what kind it is.

| Label | Meaning | Example |
|---|---|---|
| DATA | a piece of data | a received byte |
| CTRL | a command | "send 8 bits" |
| EVENT | something happened | "I2C START just happened" |
| ERR | an error | "framing error" |

A whole protocol packet, like a CAN frame, is **many tokens**.

**3. The fabric connects everything, not just pin units to lanes.** Tokens can go:
- pin unit → lane (a received byte);
- lane → pin unit (data or a command);
- lane → lane (two cooks working together, as CAN does);
- host ↔ anything (the host can send and receive tokens too).

The connections are chosen by the host before starting and stay fixed while running. One token can also go to **several places at once**.

**4. Rules react to more than just the token.** A rule's "when" can check:
- whether a token is waiting, and what's in it;
- the lane's current **state** (e.g. "I'm waiting for the address byte");
- its **flags** (e.g. "the last compare matched").

Each rule does **one small action**, like a compare, an add, or sending one token. Anything longer, like computing a checksum, goes to a **routine** in the SRAM, which runs in the background.

**5. The output often goes back to the *same* pin unit.** In the I2C example, the unit that received the address byte on SDA is also the one that sends the ACK on SDA. A "different pin unit" is common too (UART echo, SPI). Both work.

## The whole flow in one paragraph

> The host loads **settings** into the pin units, **rules** into the lanes, and **routines** into the SRAM, and wires up the fabric. Then it presses run.
> A pin unit hears something on its wires and turns it into a **token** (a small labelled word).
> The **fabric** carries the token to whoever is subscribed, usually a lane.
> In the lane, the first rule whose condition matches (token + state + flags) fires, doing one small action, or starting a longer routine.
> If it needs to respond, it sends a token (data or a command) through the fabric to a pin unit, **often the same one**, which drives the wires at exactly the right time.

---

## Will it survive being built? (the hardware assumptions)

Our software copy of the chip shows the *design* works. But it assumes the real silicon can do certain things. In phase 1 we checked the three riskiest ones with the real chip-building tools:
- **R1:** can a cook really glance at all 12 reflexes in one instant (20 ns)? **Yes, it takes about 6 ns** on a slow chip (D-030).
- **R2:** can we write the reflex lists on cheap, compact "sticky notes" (latches) instead of bulky "whiteboards" (flip-flops), and still build the kitchen? **Yes**, and after the real wiring was laid out, there were still 6.94 ns to spare (D-032, D-034).
- **R3:** does the recipe book (the SRAM block) fit into the kitchen's construction process? **Yes**, so we keep it (D-031).

Still open:
- **The kitchen is small** (6x4 tiles), and it isn't yet certain everything fits. The waiters' settings turned out bigger than expected, about 307 bits each. Checking the fit is the first job of phase 2.
- **Everything so far is simulation.** We have no real hardware yet, so every result is from simulation with ideal wires (see `docs/CLAIMS.md`).

## Word list

| Word | Meaning |
|---|---|
| **Pin** | One wire between the chip and the outside world |
| **Pin unit** (U0–U5) | A timing engine attached to up to two pins; sends and receives bits at exact times |
| **Token** | One 16-bit word plus a 2-bit label (DATA, CTRL, EVENT, ERR), passed between blocks |
| **Channel fabric** | The on-chip wiring that delivers tokens from producers to consumers |
| **Lane** (L0–L2) | A decision engine that holds 12 rules, 4 registers, a state and flags |
| **Rule / reflex slot** | "When this condition holds, do this one action"; all 12 are checked every clock |
| **State** | Where the lane is in the protocol (e.g. "waiting for the address byte"), 16 possible values |
| **Flag** | A yes/no remembered by a lane (e.g. "the address matched") |
| **Routine** | A longer program in the SRAM, run in the background between rule firings |
| **SRAM** | The chip's memory block (512 words) for routines and data |
| **Host** | The outside computer (the demo board's RP2350) that loads, starts, stops and inspects the chip |
| **Firmware** | Everything the host loads: pin unit settings, rules, routines and fabric connections |
| **Clock** | The chip's heartbeat: 50 million beats per second, one every 20 ns |
