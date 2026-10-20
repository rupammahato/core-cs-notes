# Product and analytics casebook examples

Eighteen original hypothetical cases combine a user problem, an evidence pack, metric definitions, complete fixture inputs, verified arithmetic, competing options, a conditional recommendation, engineering consequences and four interviewer follow-ups. The nine-file root Product Casebook Notes subject is the reader-facing book.

## Run from the repository root

```powershell
python examples/product-casebook/compute.py C04
python examples/product-casebook/compute.py C18
python examples/product-casebook/verify.py
python examples/product-casebook/build_book.py
python examples/product-casebook/validate_content.py
```

Python 3.13.15, standard library only. The lab reads fixture.json and performs local aggregate calculations. No real users, interviews, customer records, provider calls, experiments, databases or deployments are used. Money is invented USD cents. Raw floats are recorded in results.json; note displays use six-decimal rounding and retain significant digits for tiny probabilities.

The 41 runtime checks comprise 18 independent arithmetic reference projections, thirteen changed scenarios, eight rejected contradictory inputs and two preservation checks. References use separately written fractions, identity/count algebra, direct expected outputs and a separate Normal-tail calculation. These are scoped checks, not proof over arbitrary inputs or a production-grade metrics library. In particular, they verify neither supplied source identities/labels nor the quality of a product recommendation.

C01/C03/C07 describe conditional opportunity scenarios, not measured interventions. C04 standardizes a descriptive mixture. C05 trusts declared disjoint identity counts rather than reconstructing real source rows. C08 fixes cohort and receipt assumptions. C09/C16 provide aggregate comparisons without verifying assignment. C10/C11/C12 use selected costs and future assumptions; unavailable LTV stays null. C13's added-slot value is only a capacity upper bound. C14 is a constant-rate fluid model, not stochastic waiting-time inference. C15 assumes uniform, perfectly prevented loss for caught fraud. C17 uses supplied model labels, not an executed AI benchmark. C18's request-budget ratio is not a production multiwindow burn alert.

`cases.json` contains the authored reasoning and follow-ups. `build_book.py` replaces only marked worked-case blocks in six chapters, inserting the complete fixture and actual output. Other handbook prose is authored directly in root Markdown. `validate_content.py` checks content fidelity, links, coverage and byte preservation of the 144 earlier handbooks captured at task start. `content-validation.json` records those audits separately from runtime checks.

After the website sync and production build, run `node examples/product-casebook/site-smoke.mjs`. It checks routes, new content and subject-filtered search using its own temporary loopback preview and closes that preview. Port 3000 remains stopped unless the user separately requests it. The recorded build uses this machine's local font-response fixture for its restricted network environment; normal site font configuration is unchanged.

Primary references and research boundaries appear in research.json and inline in the notes. Selection, recommendations, mock formats and rubrics are editorial practice material; no measured company question-frequency claim is made. Learner attempts and mock feedback remain manual work.
