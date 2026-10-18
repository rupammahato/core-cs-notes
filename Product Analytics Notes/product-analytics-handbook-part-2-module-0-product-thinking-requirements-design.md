# Product and Analytics Placement Handbook — Part 2
# P0: Product Thinking, Requirements and Design Communication

**P0 · 3–4 hours plus manual exercises · Tier 1 for product interviews · Requires: no product-tool experience**

---

## Why this module matters

“I built a candidate portal” invites questions beyond the technology stack. Who needed it? What problem did you prioritize? Why this scope? What counted as success? What happened when a candidate was interrupted? How did the team know the feature met the requirement?

Product thinking connects those answers. It means reasoning from a person's problem and the organization's constraints to a choice that can be explained and assessed.

> **Keep a visible chain: user problem → evidence or assumption → decision → requirement → flow → verification → outcome.**

This chapter prepares you to clarify a product case, write a small BRD/PRD, prioritize a backlog, specify acceptance criteria, explain a wireframe and use Figma/Notion vocabulary accurately.

**Verification:** **53 local checks passed** on Python 3.13.15 for the offline worksheet in examples/product-analytics/module-0-product-thinking/. They verify arithmetic, ranking, input rejection, traceability and change impact. The candidate journey and its reported check states are synthetic. No real product behavior, user study, Figma prototype or Notion account was verified.

## 0.1 What is product thinking?

A product is a means for a person or organization to accomplish something repeatedly. A feature is one capability within that experience. A project organizes work toward a result; a product usually continues to evolve after one project ends.

Product thinking asks what outcome is valuable, what prevents it today, which intervention is worth trying, and how to decide whether that intervention helped.

| Term | Teaching example | Question it answers |
| --- | --- | --- |
| User | Candidate completing an invited application | Who is trying to do something? |
| Customer/buyer | Employer paying for the hiring tool | Who chooses or funds the purchase? |
| Stakeholder | Recruiter, candidate, hiring manager, support, engineering | Who affects or is affected by the decision? |
| Problem | A candidate loses progress after an interruption | What prevents the desired outcome? |
| Feature | Save and restore a draft | What capability might address it? |
| Output | A draft-saving release shipped | What work was delivered? |
| Outcome | More eligible candidates complete usable applications | What changed for people or the business? |
| Guardrail | No cross-candidate disclosure or duplicate submission effects | What must not deteriorate while pursuing the outcome? |

An output can be completed while its hoped-for outcome fails. A draft button can exist but be confusing, lose data or solve a rare problem while the real obstacle is a long eligibility form.

**Interview line:** “I start with the user and the blocked outcome, identify what we know versus assume, choose a constrained intervention, and define how we will verify the behavior and assess the result.”

### Product work and engineering work connect

```text
Candidate cannot finish after an interruption
          |
          v
Product: investigate frequency, impact and alternatives
          |
          v
Requirement: restore the latest acknowledged draft
          |
          v
Design: saved, saving, failed-save and resume states
          |
          v
Engineering: identity, authorization, versioning and storage
          |
          v
Verification: restoration and rejection cases
          |
          v
Outcome review: completion, lost-work reports and guardrails
```

The product requirement does not need to dictate a database. Engineering still needs enough precision to decide who owns a draft, which version wins and what a successful acknowledgement promises.

## 0.2 Frame the problem before proposing the feature

“Add AI screening” is a solution proposal. “Recruiters cannot review applications before the hiring deadline” describes a possible problem, but still needs evidence and boundaries.

A useful problem statement includes **a specific group, context, obstacle, consequence and evidence status**.

**Teaching problem statement:** “Invited candidates using a mobile browser may leave a multi-step application unfinished after an interruption. We need to establish whether lost progress is a material cause and whether draft recovery improves completion without lowering application quality.”

The words “may” and “need to establish” matter. They prevent a plausible story from becoming a claimed discovery result.

### Five clarification questions for an interview case

1. Who is the target user, and which segment or journey are we considering?
2. What are they trying to finish, and what happens today?
3. What evidence indicates the obstacle and its severity?
4. What business objective and constraints shape the choice?
5. What outcome and guardrails would make the intervention worthwhile?

For “improve our hiring portal,” ask whether the target is candidates finishing applications, recruiters reviewing them, or employers configuring vacancies. Those are connected but different jobs.

### User need versus implementation preference

| Starting request | Need to investigate | One possible solution |
| --- | --- | --- |
| Add an email reminder | Remember an unfinished task before a deadline | Reminder with frequency limits |
| Add a dashboard | Know which action needs attention | A concise task list |
| Add a chatbot | Resolve uncertainty while completing a task | Clear inline guidance |
| Add autosave | Avoid losing work after interruption | Explicit save, autosave or a shorter form |

GOV.UK's user-needs guidance recommends grounding needs in research and expressing the goal without prematurely committing to a delivery mechanism. [Learning about users and their needs](https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs).

## 0.3 Discovery: turn assumptions into questions

Discovery reduces uncertainty about the problem and possible approaches. It can lead to a decision to build, change scope, investigate more, or stop. It is not a ceremony that proves the first feature request was correct. [GOV.UK discovery guidance](https://www.gov.uk/service-manual/agile-delivery/how-the-discovery-phase-works).

For the teaching case, write a small assumption register:

| ID | Assumption | What would investigate it? | Decision affected |
| --- | --- | --- | --- |
| H01 | Interruption causes meaningful loss of progress | Observe recent tasks; examine saved-state incidents | Whether draft recovery matters |
| H02 | Candidates understand “save” versus “submit” | Task-based prototype session | Copy and confirmation states |
| H03 | The form requires every current field | Review field usage with recruiters | Shorten versus persist the form |
| H04 | Recruiters receive usable applications after recovery | Review completeness and downstream rework | Quality guardrail |
| H05 | Existing identity can authorize draft access | Engineering feasibility review | Security and scope |

### Research questions that do not lead the participant

“Would you like our new autosave feature?” encourages agreement with the proposed solution.

Try: “Tell me about the last time you started an application and could not finish it immediately. What happened next? What did you do to recover?” Ask to observe the current task when appropriate, with consent and suitable handling of personal data.

Learn the sequence and consequences before asking for opinions about a new screen. Recruit beyond the people who successfully completed the flow; otherwise the people facing the most important obstacle may be absent.

The research plan should state the question, participant group, method, owner and decision it informs. That structure follows the intent of the [GOV.UK research-planning guidance](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service); the hiring example here is original teaching material.

### Qualitative and quantitative evidence

| Evidence | Useful for | Important limitation |
| --- | --- | --- |
| Observation/interview | Discovering context and mechanisms | A small selected sample does not estimate population prevalence |
| Event data | Locating patterns and segment differences | An event gap can reflect instrumentation problems |
| Support cases | Finding painful failure modes | People who contact support are a selected subset |
| Prototype task | Testing whether a design can be understood | Task success does not establish commercial demand |
| Experiment | Estimating an intervention's causal effect under its design | Assignment, exposure, sample size and interference need care |

If three interviewees describe lost work, record three descriptions in that recruited sample. Do not turn that into “most candidates lose their progress.” P2 will develop denominators and causal reasoning.

## 0.4 Stakeholders, constraints and decisions

Stakeholders can disagree while each points to a real concern. A recruiter wants richer information; a candidate wants a shorter form; support wants recoverable failures; engineering needs a manageable release.

Create a decision table rather than collecting an unranked wish list:

| Stakeholder | Concern | Decision or boundary |
| --- | --- | --- |
| Candidate | Progress and clarity | Separate save from final submission; show acknowledgements |
| Recruiter | Complete, usable records | Validate final submission and define incomplete drafts |
| Employer/admin | Access and hiring deadlines | Scope access and define expiry behavior |
| Support | Explain what happened | Stable references and an appropriate recovery route |
| Engineering | Correctness and feasibility | Verify state transitions, ownership and retry behavior |
| Product owner | Valuable scope under a time budget | Compare options and record the decision |

Accountability is an explicit agreement. In a small team, one person may hold several responsibilities; that does not remove the need to identify who decides a trade-off and who supplies evidence.

**Disagreement example:** a stakeholder requests an AI summary before launch. Explain the objective it serves, compare it with draft recovery, identify required access protections, and offer a smaller discovery task if its value or data quality is uncertain. Record the choice and revisit condition.

## 0.5 Prioritization: a transparent aid to judgment

Prioritization allocates scarce time and attention. First identify mandatory protections, dependencies and commitments. Compare discretionary work only after establishing those boundaries.

### RICE

The original Intercom framework combines **reach, impact, confidence and effort**:

```text
RICE = reach × impact × confidence / effort

reach: estimated affected users/events in a consistent period
impact: agreed relative impact score for the chosen objective
confidence: an evidence-strength adjustment expressed here from 0 to 1
effort: estimated total person-time in a consistent unit
```

Confidence is a judgment about the estimates, not an experimentally calibrated probability that a launch will succeed. Effort includes the relevant functions, rather than only coding time. [Intercom's RICE explanation](https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers).

The following **synthetic** backlog uses candidates per month and person-months. The estimates are not taken from any resume project.

| Feature | Reach | Impact | Confidence | Effort | Computed score | Decision constraint |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Secure entry | 120 | 1 | 1.0 | 1 | 120.0 | Mandatory protection |
| Resume draft | 120 | 2 | 0.8 | 2 | 96.0 | Discretionary |
| Status page | 120 | 1 | 0.8 | 1 | 96.0 | Discretionary |
| AI summary | 80 | 2 | 0.5 | 4 | 20.0 | Discretionary |

Run from the repository root:

```powershell
python -X utf8 examples/product-analytics/module-0-product-thinking/workshop.py
python -X utf8 examples/product-analytics/module-0-product-thinking/verify.py
```

The actual worksheet output includes:

```json
{
  "mandatory": [
    {"id": "secure-entry", "score": "120.0", "mandatory": true}
  ],
  "discretionary": [
    {"id": "resume-draft", "score": "96.0", "mandatory": false},
    {"id": "status-page", "score": "96.0", "mandatory": false},
    {"id": "ai-summary", "score": "20.0", "mandatory": false}
  ]
}
```

The tied scores do not tell you which feature matters more. The program uses the feature ID for deterministic display, not a product recommendation. Compare confidence, dependencies, urgency and learning value to decide the tie.

### Sensitivity beats false precision

If the draft confidence changes from 0.8 to 0.5, its score becomes **60**, below the status page's **96**. If its effort doubles to four person-months, its score becomes **48**.

Those calculations are checked locally. They show which assumptions could change the order; they do not show which estimates are true.

Never compare monthly reach in one row with quarterly reach in another. Do not enter confidence=80 when the formula expects 0.8. Zero effort is invalid rather than an infinite-priority opportunity.

### Alternatives and limits

| Approach | Useful when | Watch for |
| --- | --- | --- |
| Impact/effort discussion | Early comparisons with little evidence | Vague scales and dominant voices |
| RICE | Comparable estimates and a shared objective exist | Manufactured precision and inconsistent units |
| Must/should/could/won't-for-now | A release needs explicit scope negotiation | Calling everything a must |
| Risk-first learning | A critical assumption could invalidate the plan | Running studies without a decision they can change |

The worksheet keeps secure entry mandatory even when its reach is changed to zero. That is a policy constraint in the teaching example. The arithmetic cannot decide whether access protection is optional.

## 0.6 Minimum scope: deliver a coherent journey

A minimum viable product is a small coherent product approach for testing a value assumption with actual users. A prototype may test understanding earlier; a production release must still meet its applicable protections and quality requirements.

For this case, a candidate must be able to enter safely, complete or save work, recover from errors, submit, and know the result. Shipping only a beautiful form with no understandable submission outcome is not a coherent journey.

### Teaching release boundary

**In scope:** invited candidate access, explicit draft saving/restoration, required-field validation, one final application effect, clear confirmation and an accessible basic journey.

**Out of scope:** AI screening, public job discovery, candidate ranking, interview scheduling and recruiter collaboration. A status page is a discretionary alternative, not silently part of the draft-saving scope.

**Open decisions:** invitation lifetime, reissue ownership, retention policy, whether submitted applications can be edited, and handling conflicting draft edits. Assign owners and dates; do not hide them behind “TBD.”

An effective scope boundary states the excluded work and the condition that would justify reconsidering it. It prevents a different stakeholder from assuming the entire hiring platform is included.

## 0.7 BRD, PRD, stories and acceptance criteria

Document names vary across teams. Ask what decision the document supports and who will use it.

| Artifact | Main purpose in this chapter | Teaching example |
| --- | --- | --- |
| Business requirements document, BRD | State the business problem, objectives, scope and constraints | Reduce avoidable application loss while preserving usable submissions |
| Product requirements document, PRD | Specify intended product behavior and experience | Save/restore rules, submission behavior and flow states |
| User story | Express one user's goal and benefit | As an invited candidate, resume saved work so an interruption does not force re-entry |
| Acceptance criterion | State an observable condition for accepting the behavior | An acknowledged draft is restored after an authorized return |
| Test case | Define inputs, steps and an expected result | Save specified values, reopen through valid access and compare restored values |
| Design artifact | Communicate structure and interactions | Draft form, saved acknowledgement and recovery screen |

The distinction between business intent and product behavior is useful even if a small team combines both in one page. [Atlassian BRD guidance](https://www.atlassian.com/software/confluence/resources/guides/how-to/business-requirements), [Atlassian PRD guidance](https://www.atlassian.com/agile/product-management/requirements/).

### A small BRD for the teaching case

```text
Title: Recoverable invited application
Problem: interrupted candidates may lose work; prevalence is unconfirmed
Users: invited candidates; downstream recruiters and support
Objective: increase usable completion among eligible invited candidates
Scope: safe entry, saved draft, final submission and clear outcomes
Constraints: existing hiring deadline, access boundaries, team capacity
Primary metric: eligible completion within a defined observation window
Guardrails: application quality, duplicate effects, inappropriate access
Assumptions: interruption is material; required fields are justified
Decision owners: product scope, engineering feasibility, domain policy
```

This is a proposal template, not evidence that an actual employer approved these terms.

### Turn the brief into a behavior contract

| Requirement | Observable behavior | Important boundary |
| --- | --- | --- |
| R01 Secure entry | Valid access opens the intended application | Expired/revoked access does not disclose its data |
| R02 Draft recovery | Latest acknowledged draft can be restored | Failed saves cannot be labelled saved |
| R03 Final submission | A complete application produces one final effect | Incomplete input does not change final state |
| R04 Usable flow | Candidate can understand and operate key actions | Keyboard and comprehension checks remain necessary |

### Given/when/then is a writing aid

```text
AC04 — Draft restoration
Given the candidate has saved draft version 3 and received acknowledgement,
and still has authorized access to that application,
when they return to the application,
then the saved fields from version 3 are restored,
and the interface distinguishes draft state from final submission.
```

“Easy to use” is not an acceptance criterion by itself. Name the task and observable behavior. A usability task can require qualitative assessment; not every useful criterion must be reduced to a single automated assertion.

### Functional requirements and quality requirements

“Restore the saved draft” is functional behavior. “Under the agreed concurrent workload, draft-save response p95 is within the chosen budget” is a performance requirement.

Specify the budget, workload, payload, measurement boundary and observation period before treating such a statement as testable. This chapter does not invent a measured latency result.

### Acceptance criteria versus Definition of Done

Acceptance criteria concern the particular behavior being accepted. A team's Definition of Done sets a shared quality standard for an increment. In Scrum, Done has a specific meaning; merely merging code does not establish it. [The Scrum Guide](https://scrumguides.org/scrum-guide.html).

For this case, a team's general standard might include review, relevant tests and release documentation. AC04 still needs its own draft-restoration condition. Neither substitutes for evaluating whether the feature helps candidates.

## 0.8 Requirements traceability and change impact

Traceability connects an identified need or decision to requirements, criteria, designs and verification evidence. Stable IDs let the team find what a change affects.

The worksheet uses this **synthetic** matrix:

| Requirement | Criterion | Proposed check | Supplied state |
| --- | --- | --- | --- |
| R01 Secure entry | AC01 Valid access opens the intended application | T01 Automated contract check | Passed |
| R01 Secure entry | AC02 Expired/revoked access is rejected without data disclosure | T02 Automated rejection cases | Passed |
| R02 Draft recovery | AC03 Acknowledged save retains the intended fields | T03 Automated save check | Passed |
| R02 Draft recovery | AC04 Authorized return restores the saved draft | T04 Automated restoration check | Passed |
| R03 Final submission | AC05 Valid repeated submission produces one final effect | T05 Automated idempotency check | Passed |
| R03 Final submission | AC06 Missing required input has no final-submission effect | T06 Automated invalid-input check | Pending |
| R04 Usable flow | AC07 Key actions and errors can be operated by keyboard | T07 Manual keyboard walkthrough | Pending |
| R04 Usable flow | AC08 A candidate distinguishes save from submit without prompting | T08 Manual task-based session | Pending |

**Every state in this matrix is a scenario input.** T01–T05 were not executed against a real portal. The actual executable tests exercise the worksheet that processes the matrix.

The actual worksheet summary is:

```json
{
  "criteria": 8,
  "supplied_passes": 5,
  "passed_fraction": "0.625",
  "unresolved": ["AC06", "AC07", "AC08"],
  "worksheet_ready": false,
  "scope": "Supplied synthetic evidence states; no application was tested or approved."
}
```

**Five of eight supplied states are passed: 62.5%.** All eight criteria have check links, so linkage coverage is complete, while the supplied pass fraction is not. Neither percentage establishes real product readiness or learner mastery.

### Why count criteria rather than test files?

One test suite may cover several criteria, and several tests may support one criterion. A large count of unrelated passing tests must not conceal an unverified requirement. The helper rejects unresolved links, duplicate IDs and unreferenced check records.

For simplicity, every criterion must be passed for this worksheet's `worksheet_ready` flag to become true. A real release process may have explicit risk exceptions and independent approvals. Its evidence also needs run/version provenance, owners and freshness; this small helper does not establish those.

### A changed requirement should produce a review list

Suppose R02 changes from explicit save to autosave. The program returns:

```json
{
  "requirement": "R02",
  "criteria": ["AC03", "AC04"],
  "checks": ["T03", "T04"],
  "frames": ["F03-draft", "F04-saved"],
  "metrics": ["draft_restore_success"]
}
```

That is the impact of **declared links**, not a discovery of every real dependency. A reviewer must also consider save frequency, conflicting tabs, error recovery, acknowledgement copy and server load. The matrix can be incomplete.

## 0.9 User flows: decisions and failures before pixels

A user flow maps the states and choices involved in completing a task. It should include meaningful failures and recovery, rather than only the happy path.

```text
F01 Open invite
  |
  +-- unavailable/expired/revoked --> F02 Explain safe next step
  |
  +-- eligible --> F03 Draft form
                    |
                    +-- Save --> pending --> F04 Saved acknowledgement
                    |              |
                    |              +-- failure --> explain; retain entered values
                    |
                    +-- Return later --> verify access --> restore acknowledged draft
                    |
                    +-- Review --> F05 Review
                                      |
                                      +-- invalid --> F07 Errors --> F03
                                      |
                                      +-- submit --> pending --> F06 Confirmation
                                                        |
                                                        +-- ambiguous outcome --> recover result
```

The “ambiguous outcome” path matters: the browser can lose a response after the server commits. A product flow should explain what the candidate sees while engineering defines idempotency and outcome recovery. See [M9: reliable integrations](/docs/resume-skills/webhooks-payments-reliable-integrations).

### Questions to ask on every transition

- What action causes the transition?
- Which state is authoritative, and what data must be retained?
- What does the user see while waiting?
- What is different after success, failure or a retry?
- What is the recovery path if they close the page or return later?

This is also where product and security meet. “Hide the submit button after expiry” cannot replace a server-side rule rejecting access or submission.

## 0.10 Wireframes, mockups and prototypes

| Artifact | What it communicates | What it does not prove |
| --- | --- | --- |
| User flow | Sequence, decisions, branches and outcomes | Visual hierarchy or final implementation |
| Wireframe | Structure, information hierarchy and controls | Final visual styling |
| Mockup | A more finished visual appearance | Working interactions or backend behavior |
| Prototype | A simulation of interactions at chosen fidelity | Production persistence, authorization or market demand |

Terms can overlap in practice. Describe the artifact's purpose and fidelity rather than arguing over its label.

### One low-fidelity draft screen

```text
+---------------------------------------------------+
| Your application                                  |
| Draft — not submitted                             |
|                                                   |
| Full name *                                       |
| [                                               ] |
|                                                   |
| Relevant experience                               |
| [                                               ] |
|                                                   |
| Save draft             Review application         |
| Last saved: [acknowledged time, or no saved draft] |
+---------------------------------------------------+
```

Annotate loading, save failure, stale data, validation and confirmation states. A screenshot of the normal screen cannot communicate all of them.

### Accessibility belongs in the behavior

Use clear labels, distinguish draft/save/submit actions, associate errors with the affected fields, preserve useful entered values and communicate outcomes. W3C's form-notification guidance explains how clear feedback supports both successful and failed submissions. [W3C WAI: user notifications](https://www.w3.org/WAI/tutorials/forms/notifications/).

A pleasant color palette does not establish keyboard operation or understandable error recovery. AC07/AC08 remain manual exercises here; no accessibility conformance assessment has been performed.

## 0.11 What is Figma, and how is it used here?

Figma is a collaborative interface-design tool. A team can organize screens, reuse design elements, annotate states and connect interactions into a prototype.

For this chapter's manual exercise, create frames corresponding to F01–F07, connect the candidate's main actions, set a flow starting point and preview the journey. Figma's documentation describes prototype flows beginning on top-level frames and navigation through connected interactions. [Figma: create and manage prototype flows](https://help.figma.com/hc/en-us/articles/360039823894-Create-and-manage-prototype-flows).

Do not depend on memorizing a toolbar's exact position; product interfaces change. Explain the concepts of a screen/frame, reusable component, interaction and flow starting point.

### Manual prototype exercise

1. Create the draft, saved, review, error and confirmation states.
2. Include a failure branch rather than connecting every action to success.
3. Ask a participant to save and later submit an application without explaining the buttons first.
4. Observe actions, misunderstandings and requests for help; distinguish observation from interpretation.
5. Revise a specific ambiguity and describe what a later session should examine.

This is an exercise to perform in your own file. No Figma account was opened or modified while authoring the notes. Paper screens can be used for the initial flow discussion.

**Likely follow-up:** “Does a working prototype mean the product is ready?” No. The prototype can support design learning; it does not verify the server-side access, persistence and final-submission contract.

## 0.12 What is Notion, and how can documentation stay useful?

Notion combines documents and structured databases. For the teaching workflow, use pages for the problem brief and decision log, and records for requirements and checks.

Relations can link records across databases; rollups can summarize properties through those relations. These are documented Notion concepts, not evidence that the proposed workspace already exists. [Notion: relations and rollups](https://www.notion.com/help/relations-and-rollups).

### Suggested manual structure

| Record/page | Useful fields | Link |
| --- | --- | --- |
| Problem brief | User, context, obstacle, evidence status, owner | Requirements |
| Requirement | Stable ID, behavior, owner, version, status | Criteria and design |
| Check | ID, method, expected result, actual evidence, run/version | Criterion |
| Decision | Alternatives, rationale, owner, date, revisit condition | Affected requirement |
| Research note | Question, method, participant segment, observation | Assumption |

A filtered “ready” view is only as good as the underlying data and permissions. A manually selected status does not execute a test, and a documentation database is not a substitute for the application's authoritative data store.

**Decision-log example:** “Choose explicit save for the initial release because acknowledgement and recovery are easier to communicate within the current scope. Revisit autosave if observed interruptions during unsaved editing remain a material issue.” This is an illustrative decision, not a claim about your historical implementation.

## 0.13 Success criteria: delivery, behavior and outcomes

Keep three questions separate:

| Layer | Question | Teaching evidence |
| --- | --- | --- |
| Delivery | Did the team produce the agreed scope? | Release version and requirement links |
| Behavior | Does the system and journey meet its criteria? | Contract checks, manual sessions and relevant quality checks |
| Outcome | Did the intervention help the intended users? | Defined metrics, research and an appropriate evaluation design |

For this case, propose the following measurement contract before collecting results:

```text
Primary: eligible completion within seven days of invitation
Unit: one eligible candidate-application invitation
Numerator: units producing a valid final submission within that window
Denominator: eligible invitations with the full observation window elapsed
Exclusions: internal/test invitations under a documented rule
Segments: device class and new/returning candidate, when reliably available
Guardrails: usable application quality, duplicate effects, access incidents
```

The seven-day window is a **teaching policy choice**, not a universal conversion definition. Product and domain owners must decide what happens when invitations expire earlier, are reissued or refer to several vacancies.

Count candidate-application invitations consistently; do not use unique people in the numerator and raw invitation emails in the denominator. Do not treat unfinished observation windows as final non-completions without an explicit analysis rule.

Draft restoration is a diagnostic behavior metric. Total saves is an activity count and can rise because candidates struggle. Neither alone establishes a better product outcome.

No outcome percentage or uplift is claimed in this chapter. P2 will explain how to distinguish an observed change from the intervention's causal effect.

## 0.14 Connect the case to your resume honestly

The earlier [resume deep-dives](/docs/resume-skills/resume-project-experience-deep-dives) record hiring-module and candidate-portal responsibilities as resume-reported scope. That makes this a useful practice domain; it does not establish that the synthetic draft feature, prioritization scores or research sessions occurred in your project.

Prepare one actual example using this structure:

1. **Context:** who had the problem and what task was blocked?
2. **Evidence:** what did you observe, inspect or receive from a stakeholder?
3. **Contribution:** which requirement, design, analysis or implementation did you own?
4. **Choice:** what alternative did you consider and why did you choose this scope?
5. **Verification:** what demonstrated the expected behavior, and what remained untested?
6. **Result:** what changed, with a defensible measurement boundary or an explicit absence of impact data?

If you audited behavior against a BRD, explain one requirement-to-test link and a real discrepancy. Do not invent an approved legal/payroll rule or a numerical growth result to make the story sound stronger.

### Thirty-second answer skeleton

“The user was [group] trying to [task]. We had [evidence] that [obstacle] mattered. I owned [specific contribution]. We chose [scope] over [alternative] because [constraint or evidence]. We checked [behavior] using [evidence]. The measured result was [defined result], or the confirmed result was delivery/correctness and we did not establish causal impact.”

This is a prompt for your own facts, not a script with fabricated achievements.

## 0.15 Common wrong answers

| Wrong answer | Better reasoning |
| --- | --- |
| “Product thinking means deciding which features to add.” | Begin with user outcomes, evidence, constraints and alternatives, including not building |
| “The customer requested it, so the need is validated.” | A request is evidence to investigate; clarify the underlying task and segment |
| “Three people said it, so 60% of users want it.” | A small recruited sample does not establish population prevalence |
| “The highest RICE score must ship first.” | Estimates, mandatory constraints, dependencies and uncertainty still matter |
| “Confidence 80 means 80 in the formula.” | This worksheet expects 0.8; units and scales must be consistent |
| “MVP means skip error states and security.” | Minimum scope still needs a coherent, appropriately protected journey |
| “BRD, PRD and test case are interchangeable.” | Business intent, product behavior and verification steps serve different decisions |
| “Every requirement has a test link, so we are ready.” | A linked check can be pending, failed, stale or irrelevant |
| “A Figma prototype proves the feature works.” | It can simulate interaction without implementing the product contract |
| “The Notion status says Done, so the test passed.” | A status is a record; inspect the underlying evidence and version |
| “More draft saves prove better completion.” | Activity can rise while outcomes stay flat or deteriorate |
| “Our completion improved after release, so the feature caused it.” | Timing alone does not exclude other changes or selection effects |

## 0.16 Must remember

- A solution request is a starting point for discovery, not the finished problem definition.
- Evidence, assumption and decision are different records.
- Candidate, recruiter and buyer goals can differ.
- A framework makes assumptions visible; it does not remove judgment.
- Scope includes failure and recovery behavior.
- Acceptance criteria need observable conditions and relevant evidence.
- Traceability supports change review but can itself be incomplete.
- Prototype task success, contract correctness and business impact answer different questions.
- Metrics need a unit, population, denominator and time window.
- Resume examples must use your actual contribution and defensible results.

## 0.17 Interview questions and answers

### Q1. What is product thinking?

Reasoning from a user's desired outcome and the organization's constraints to a choice that can be evaluated. In this case, investigate interrupted applications before assuming autosave is the best intervention.

**Follow-up:** What would make you stop? Evidence that the obstacle is immaterial, another approach addresses it better, or costs and constraints outweigh the value.

### Q2. How do you distinguish a user from a customer?

A user performs the task; a customer may select or pay for the product. Candidates and employer buyers can have different needs, so define both before optimizing the journey.

**Follow-up:** Who takes priority? Explain the product objective, user protections and the particular decision rather than applying a universal hierarchy.

### Q3. What is an outcome versus an output?

A draft-saving screen is an output. More eligible candidates finishing usable applications is an intended outcome. Shipping establishes delivery, not the outcome by itself.

**Follow-up:** Can a feature meet its criteria and fail commercially? Yes; the behavior can work while solving a low-value problem.

### Q4. How do you clarify “improve the hiring portal”?

Identify the user segment and task, understand the current obstacle and evidence, state constraints, then choose an outcome and guardrails. Candidate completion and recruiter review are different starting points.

**Follow-up:** What if there is no data? State the assumptions and propose a focused investigation.

### Q5. What makes a useful research question?

It addresses uncertainty that can change a decision. “What happens when candidates leave before submission?” is more useful than asking whether they like our proposed feature.

**Follow-up:** How do you avoid leading? Ask about recent behavior and observe tasks before suggesting solutions.

### Q6. Can interviews tell you how common a problem is?

They can reveal contexts and possible mechanisms. A small selected interview sample generally cannot establish population prevalence without a suitable sampling design.

**Follow-up:** What would you combine with it? Reliable event data, incident/support evidence and appropriately designed broader research.

### Q7. How do you prioritize conflicting requests?

Agree on the objective, constraints and mandatory work, then compare expected impact, evidence, effort and dependencies. Record the rationale and what would change it.

**Follow-up:** What if a senior stakeholder disagrees? Make the trade-off and decision ownership explicit, then seek alignment on the objective and evidence.

### Q8. Explain RICE and its limitations.

It combines reach, impact and confidence relative to effort. In the worksheet, draft recovery scores 96.0, but an equal score for the status page still requires judgment.

**Follow-up:** What is confidence? An evidence-strength adjustment under the agreed scale, not a guaranteed success probability.

### Q9. Why can a low-score feature be mandatory?

Access protection is a constraint on a valid release in this case. A discretionary benefit score cannot make disclosure acceptable.

**Follow-up:** Does mandatory mean unlimited scope? No; define the actual protection and the smallest adequate implementation.

### Q10. How do you handle uncertain effort estimates?

Use rough ranges, identify the major unknowns and see whether plausible changes alter the decision. Doubling draft effort changes the score from 96 to 48 in this worksheet.

**Follow-up:** When do you investigate first? When resolving an uncertainty could materially change scope or priority.

### Q11. What is an MVP here?

A small coherent journey capable of testing value with real users: safe entry, save/restore, valid submission and understandable outcomes. AI ranking is outside this initial scope.

**Follow-up:** Is a prototype an MVP? Explain what assumption it can test; simulated interaction does not establish real product value or operational behavior.

### Q12. BRD versus PRD?

The BRD frames the business problem and constraints; the PRD describes intended product behavior. For this exercise, one explains why recovery matters and the other defines what restoring a draft means.

**Follow-up:** Must they be separate files? No; preserve clarity and ownership even when combined.

### Q13. What makes an acceptance criterion testable?

It states a relevant condition and observable expected behavior. AC04 identifies authorized return and restoration of the acknowledged draft, rather than saying “the experience is good.”

**Follow-up:** Must it be automated? No; some usability conditions require manual observation.

### Q14. Acceptance criterion versus test case?

The criterion defines the condition to accept. A test case supplies specific data and steps to gather evidence about it.

**Follow-up:** Can several cases support one criterion? Yes; expired and revoked access are separate rejection cases supporting AC02 here.

### Q15. Acceptance criteria versus Definition of Done?

Specific criteria describe the behavior being accepted; a shared Done standard addresses increment quality. Both must be understood in the team's delivery process.

**Follow-up:** Does a merged pull request satisfy both? Only if the relevant conditions and evidence actually support that conclusion.

### Q16. Why use requirement IDs?

They let a behavior stay identifiable across edits, designs and checks. A changed R02 can produce a concrete review list instead of a search for inconsistent names.

**Follow-up:** Does an ID prove the requirement is correct? No; identifiers support organization, not validation of the underlying need.

### Q17. What does traceability coverage prove?

It can show that declared requirements have links to declared checks. It does not show that those checks passed or that they reflect the right user need.

**Follow-up:** What is the worksheet result? Eight linked criteria, five supplied passes, three pending, and no real product validation.

### Q18. What happens when a requirement changes?

Review linked criteria, checks, frames, metrics and related decisions. Then inspect for dependencies missing from the matrix.

**Follow-up:** What does the autosave change affect? Acknowledgement, failure recovery, save frequency, conflicting edits and load may all need review.

### Q19. User flow versus wireframe?

A flow describes sequence and branches; a wireframe describes the structure of a screen. The candidate may need several states even when the central form has one wireframe.

**Follow-up:** Which comes first? Clarify the task and main decisions early, then refine screens and flow together.

### Q20. Mockup versus prototype?

A mockup communicates appearance; a prototype simulates selected interactions. Neither automatically implements persistence or authorization.

**Follow-up:** How much fidelity is enough? Enough to investigate the current uncertainty without unnecessary work.

### Q21. How would you use Figma for this case?

Represent the key screens and states as frames, connect actions into a flow and observe a participant attempting the task. Include saved, failed and submitted states.

**Follow-up:** What did these notes test in Figma? Nothing account-specific; the exercise remains manual.

### Q22. How would you organize requirements in Notion?

Use stable requirement records linked to criteria, decisions and evidence, with owners and versions. Summaries should preserve pending and failed states.

**Follow-up:** Does a relation enforce product behavior? No; it connects documentation records.

### Q23. What should an error state communicate?

What went wrong, which action or field needs attention, what was retained and how to recover. “Something went wrong” is often insufficient for a failed save.

**Follow-up:** Can an error reveal too much? Yes; entry failures should avoid disclosing unauthorized application information.

### Q24. How do you define success for draft recovery?

Define eligible completion with a clear unit and observation window, and inspect restoration success as a diagnostic. Include quality, duplicate-effect and access guardrails.

**Follow-up:** Why not count total saves? Repeated saves can reflect friction and do not establish completion.

### Q25. What if completion rises after launch?

Check the population, observation windows, tracking quality and concurrent changes before attributing the increase to the feature.

**Follow-up:** How do you strengthen the causal claim? Use an appropriate experimental or defensible evaluation design; P2 develops this.

### Q26. What is a guardrail metric?

A measure of an important condition that should not deteriorate while pursuing the primary objective. More submissions are not a sufficient success if duplicate effects or unusable records rise.

**Follow-up:** Does every guardrail allow averaging? No; some correctness or access incidents demand direct investigation.

### Q27. How do you explain technical feasibility in a product discussion?

Describe the user-visible consequence and constraint. For example, draft ownership and acknowledgement must be defined before promising recovery across devices.

**Follow-up:** Must the product owner choose the database? No; collaborate on the contract while engineering evaluates the mechanism.

### Q28. What if the stakeholder wants every feature in the first release?

Walk through the coherent minimum journey, trade-offs, dependencies and excluded scope. Agree on the next decision rather than leaving conflicting expectations implicit.

**Follow-up:** What should the decision log contain? Choice, alternatives, rationale, owner and revisit condition.

### Q29. How would you defend a BRD-audit claim on your resume?

Show one real requirement, the expected behavior, the observed discrepancy, your contribution and regression evidence. Keep domain-owner approval distinct from your own assumptions.

**Follow-up:** Can this synthetic case be presented as that project? No; use it to practice the structure, then substitute actual facts.

### Q30. What did the executable worksheet establish?

Fifty-three checks established local worksheet behavior for the supplied cases, including arithmetic and evidence-link handling. They did not validate candidate-portal functionality, research findings or business impact.

**Follow-up:** Why is `worksheet_ready=false` despite all 53 checks passing? The tests correctly preserve three pending criterion states in the synthetic product scenario.

## 0.18 A 30-minute mock

**Prompt:** “Improve completion of an invited candidate application without increasing recruiter rework. You have one small release to propose.”

| Minutes | Task | A useful result |
| --- | --- | --- |
| 0–4 | Clarify user, task, scope and evidence | Specific candidate segment and unresolved assumptions |
| 4–9 | Identify possible causes and investigation | Lost progress is a hypothesis alongside form length and unclear eligibility |
| 9–14 | Compare interventions and choose scope | Explicit constraints, rough estimates and alternatives |
| 14–20 | Define the behavior and flow | Save/restore, failure, review and submission outcomes |
| 20–25 | Write criteria and verification | One positive, one negative and one manual task |
| 25–30 | Define outcome, guardrails and open decisions | Stable metric unit/window; ownership and revisit conditions |

### Answer skeleton

“I would first isolate the candidate journey and the evidence for abandonment. If interrupted work is material, I would compare shortening the form with draft recovery, keeping access and submission correctness mandatory. The initial flow needs acknowledged saves, authorized restoration and understandable failure/confirmation states. I would link those requirements to automated contract cases and manual keyboard/comprehension sessions. For outcomes I would define eligible completion over a fixed observation window and monitor application quality and correctness. I would avoid claiming improvement until the measurement supports it.”

This is an example answer structure. Its quality depends on the candidate's clarification, evidence and reasoning; the worksheet does not grade the interview.

## 0.19 Practice tasks and answer checkpoints

1. **Reframe a request.** Turn “add a chatbot to the form” into a user problem, two hypotheses and one research question.
2. **Avoid leading.** Rewrite “Would autosave make you more likely to apply?” as a question about a recent experience.
3. **Predict scores.** Compute the draft score at confidence 0.5 and at effort 4 before running the verifier.
4. **Handle a tie.** Explain why the two 96-point features still need a product decision.
5. **Define minimum scope.** Remove the AI summary and status-page proposal, then show the remaining coherent candidate journey.
6. **Write criteria.** Add a positive and negative criterion for an invitation reissue policy; state the policy first.
7. **Audit the matrix.** Remove T08 from a copy of case.json and explain why the helper rejects it instead of silently dropping AC08.
8. **Read the percentages.** Explain why all criteria linked and 62.5% supplied passed are different statements.
9. **Prototype a failure.** Draw a failed-save state retaining entered values and an ambiguous-submit recovery path.
10. **Perform a manual task.** Walk the prototype by keyboard and observe an unprompted save/submit task. Record what you actually did; do not copy the synthetic states as evidence.
11. **Review change impact.** Change explicit save to autosave on paper and list dependencies beyond the declared R02 links.
12. **Prepare your own story.** Use a genuine resume example, identify your contribution and distinguish delivery/correctness evidence from causal impact.

### Answer checkpoints

- **1/2:** investigate a concrete obstacle without embedding the chatbot/autosave as the required answer.
- **3:** the locally verified scores are 60 and 48 respectively.
- **4:** assumptions, dependencies, urgency and learning value can resolve a tie; lexical order is only display behavior.
- **5:** safe entry, recovery, valid submission and understandable outcomes still need an end-to-end path.
- **6:** define whether reissue revokes old access, who may reissue and what happens to existing draft ownership; then derive cases.
- **7:** AC08 references a check that no longer exists; missing evidence cannot become an implicit pass.
- **8:** linkage concerns structure; pass state concerns supplied outcomes. Neither is real validation here.
- **9/11:** distinguish local edits, acknowledged state and final state; consider retries and conflicting tabs.
- **10/12:** preserve genuine observations and evidence boundaries even when they make the story less tidy.

## 0.20 Exit checklist

- [ ] I can frame a user problem before choosing a feature.
- [ ] I can separate a user, buyer and other stakeholder.
- [ ] I can distinguish evidence, assumption, output and outcome.
- [ ] I can ask a research question that does not lead toward my solution.
- [ ] I can explain RICE units, sensitivity, ties and mandatory constraints.
- [ ] I can define a coherent minimum journey and explicit exclusions.
- [ ] I can distinguish a BRD, PRD, story, criterion and test case.
- [ ] I can write observable positive and rejection criteria.
- [ ] I can read the worksheet without confusing supplied states with executed product tests.
- [ ] I can trace a change through criteria, checks, frames and metrics.
- [ ] I can explain flows, wireframes, mockups and prototypes.
- [ ] I can describe Figma and Notion's roles without claiming unperformed account work.
- [ ] I can define a metric's unit, population, denominator and time window.
- [ ] I can give a factual resume story and identify what its evidence does not establish.

## 0.21 Sources, reproducibility and next

Public primary sources were checked on **18 October 2026**. Links appear next to their relevant concepts; exact account controls and plan entitlements should be checked when performing manual exercises.

Preserved artifacts: workshop.py, case.json, verify.py, worksheet-output.json, verification-results.json and README.md under examples/product-analytics/module-0-product-thinking/. The JSON evidence records runtime and scope. The worksheet starts no server and calls no external service.

Return to the [Product and Analytics roadmap](/docs/product-analytics). Continue with [P1: Pricing and Unit Economics](/docs/product-analytics/pricing-unit-economics)—value, credits, usage, provider cost, failed/retried work and the Zyke case.
