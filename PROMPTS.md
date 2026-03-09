# PROMPTS.md — Prompt Engineering Design Decisions

## 1. Chatbot Persona

**Name:** Veri  
**Role:** Research Assistant for Verité Research

I chose the name "Veri" as a natural shortening of "Verité" — it's memorable, friendly, and clearly branded to the organisation.

**Tone decision:** Professional but approachable. Verité's audience spans policymakers, academics, civil society, and the general public. A robotic or overly formal tone would alienate non-specialist users, while a casual tone would undermine credibility on serious topics like labour rights and economic policy.

---

## 2. Routing Logic

The most important design decision in this chatbot is **when NOT to call the search tool**. Unnecessary vector searches add latency, cost tokens, and can introduce hallucinated citations. Claude is prompted with explicit routing rules:

| Message type | Action | Reasoning |
|---|---|---|
| Greeting / small talk | Respond directly | No retrieval needed — wastes tokens and looks robotic |
| Follow-up already in context | Respond from history | Claude already has the answer in its context window |
| Verité content question | Call `search_documents` | Grounded answer with citations |
| Borderline / domain-adjacent | Call `search_documents` | See §3 below |
| Out-of-scope | Politely decline | Maintain focus and trust |

The routing logic is embedded entirely in the **system prompt** rather than hard-coded programmatic routing. This is a deliberate choice: Claude's natural language understanding handles edge cases (mixed-intent messages, ambiguous phrasing) far better than regex or keyword matching would.

---

## 3. Borderline Question Handling

**Example:** *"What is forced labour?"*

This question is genuinely ambiguous:
- It could be casual curiosity → a Wikipedia answer would suffice
- It could be the user contextualising a Verité-specific question → they want Verité's lens

**My decision: treat it as in-scope and search.**

**Reasoning:**  
Verité's core research areas — labour rights, trafficking, supply chains — make "forced labour" a domain-central concept. Searching the knowledge base for this term will almost certainly return relevant, Verité-specific content that is **more valuable** than a generic definition. The worst case is we return a slightly over-specific answer; the best case is the user gets exactly the Verité perspective they were looking for.

The boundary I draw is: **if a general term is a direct subject of Verité's published work, search**. If the term has no plausible connection to Verité's research areas (e.g., "What is photosynthesis?"), it is out-of-scope and Claude declines.

---

## 4. Tool Definition

```json
{
  "name": "search_documents",
  "description": "Search the Verité Research knowledge base using hybrid vector + keyword search.
  Call this tool ONLY when the user's question requires information from Verité's
  publications that is not already present in the conversation.
  Do NOT call this for greetings, small talk, or questions already answered in context."
}
```

**Key design choices in the tool description:**
- The word **ONLY** is capitalised to strongly discourage unnecessary calls
- Explicit negative examples ("greetings, small talk") mirror the routing rules
- The description matches the system prompt's language for consistency — Claude sees both and they reinforce each other

---

## 5. Citation Format

Citations appear inline at the point of use:  
`[Source: <filename>, p.<page>]`

**Why inline rather than footnotes?** Inline citations let the reader immediately verify the claim without scrolling. For a research assistant, this transparency is critical — it allows users to pull up the original document and read the full context.

Claude is explicitly told:
> *Never fabricate citations. Only cite what was actually retrieved.*

This instruction is important because Claude is prone to confabulating plausible-sounding citations. The injunction is short and categorical — hedging language ("try to avoid") is weaker and less reliable.

---

## 6. Long-Term Memory Strategy

At the start of each new session, the **last 6 messages from the most recent previous session** are prepended to the conversation history. This is a deliberate compromise:

- **Loading the full history** risks context overflow and increases cost significantly
- **Loading nothing** makes Veri feel amnesiac across sessions
- **Loading 6 messages (3 turns)** gives Claude enough context to say "as I mentioned last time…" without cost explosion

The summary approach (compressing prior sessions into a single bullet list) was considered and rejected — it loses nuance and introduces the risk of compression errors.

---

## 7. Out-of-Scope Response

The decline message is templated in the system prompt:

> *"I'm Veri, Verité Research's assistant. I can only help with questions related to Verité's publications and research areas. Is there something about their work I can help you with?"*

**Design choices:**
- Identifies itself by name (reasserts persona)
- Does not apologise (apologies for normal operating boundaries erode user trust)
- Ends with a redirect question (keeps the conversation going rather than dead-ending it)
