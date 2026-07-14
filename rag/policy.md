# Internal Consumer Lending Underwriting Policy

**Document owner:** Credit Risk & Underwriting
**Applies to:** All unsecured consumer loan applications processed through the automated underwriting pipeline
**Status:** Active

This document defines the underwriting rules, thresholds, and escalation criteria used by the
loan underwriting copilot and by human underwriters reviewing its recommendations. It is the
authoritative policy reference for automated decisioning; any tool or agent output that
conflicts with this document should defer to this document.

## 1. Purpose and Scope

This policy governs the evaluation of unsecured personal loan applications, including initial
risk scoring, debt-to-income (DTI) assessment, fraud screening, and the conditions under which
an application must be routed to a human underwriter rather than being auto-approved or
auto-denied. It applies to all applications submitted through the online origination channel
and processed by the underwriting copilot, regardless of requested loan amount.

The policy is intended to keep automated decisions consistent, explainable, and auditable. Every
automated approval or denial must be traceable to the specific rule or threshold in this
document that drove the decision, and the reasoning must be recorded in the audit log alongside
the model outputs that informed it.

## 2. Debt-to-Income (DTI) Thresholds

Debt-to-income ratio is calculated as total monthly debt obligations (existing debt service plus
the estimated payment on the requested loan) divided by gross monthly income.

- **DTI at or below 0.43 (43%):** Meets the standard consumer lending DTI threshold. This is
  consistent with the qualified-mortgage back-end DTI convention used industry-wide and is the
  baseline affordability bar for this institution's unsecured lending products.
- **DTI above 0.43:** Fails the standard DTI threshold. Applications in this range are not
  eligible for automatic approval, regardless of credit risk tier, and must be either declined
  or escalated to manual review per Section 6.
- **DTI above 0.55:** Considered a severe affordability concern. These applications should be
  auto-denied unless a underwriter documents a compensating factor (e.g., significant liquid
  reserves, a co-signer, or income verification that materially understates true income).

DTI alone does not determine approval; it is a gating threshold that works alongside the credit
risk tier described in Section 3.

## 3. Credit Risk Tier Rules

The credit-risk model produces a default probability for each applicant, which is mapped to one
of three risk tiers:

- **Low risk (default probability below 0.30):** Applicant demonstrates strong creditworthiness.
  Eligible for automatic approval provided the DTI threshold in Section 2 is also met and no
  red-flag conditions from Section 4 are present.
- **Medium risk (default probability between 0.30 and 0.60):** Applicant shows moderate risk
  indicators. These applications are not eligible for straight-through automatic approval. They
  may be auto-approved only at a reduced loan amount or with adjusted pricing per the pricing
  addendum, and otherwise should be routed to manual review.
- **High risk (default probability of 0.60 or above):** Applicant demonstrates significant risk
  of default. These applications should be automatically denied unless a manual underwriter
  identifies specific, documented mitigating circumstances that justify an exception. Exceptions
  at this tier require sign-off from a senior underwriter.

Risk tier and DTI status are evaluated independently; an applicant must clear both to qualify
for automatic approval. A low risk tier does not override a failing DTI ratio, and a passing DTI
ratio does not override a high risk tier.

## 4. Red-Flag Conditions

The following conditions are treated as red flags. A red flag does not automatically deny an
application, but it disqualifies the application from automatic approval and typically triggers
manual review, even if the applicant would otherwise clear the DTI and risk-tier thresholds.

- **Multiple late payments:** Three or more late payments recorded within the last 24 months. A
  pattern of recent delinquency is one of the strongest predictors of future default and should
  be weighted heavily even when the overall risk score is moderate.
- **Very short credit history:** Fewer than 3 years of recorded credit history. Thin credit files
  make the risk model's output less reliable and warrant additional scrutiny, particularly for
  larger loan amounts.
- **Very low employment tenure:** Less than 1 year at current employment. Short job tenure
  correlates with income instability and should be cross-checked against stated income and
  supporting documentation.
- **Loan amount disproportionate to income:** Requested loan amount exceeding 75% of stated
  annual income, even if the resulting DTI technically passes based on estimated payments.
- **Inconsistent or missing identity/income documentation:** Any mismatch between application
  data and submitted documentation (see Section 5) is a red flag and should halt automatic
  processing until resolved.

Multiple simultaneous red flags on a single application should be treated as a stronger signal
than any one red flag alone and generally warrant escalation regardless of the computed risk
tier.

## 5. Required Documentation Checklist

Before an application can be fully processed, the following documentation must be present and
internally consistent:

1. Government-issued photo identification confirming applicant identity and age.
2. Proof of income (recent pay stubs, tax returns, or employer verification letter) sufficient to
   corroborate the stated annual income used in the DTI and risk calculations.
3. Proof of current address (utility bill, lease agreement, or bank statement dated within the
   last 90 days).
4. Statement or disclosure of existing debt obligations used in the DTI calculation.
5. Signed applicant consent for a credit history pull and for automated decisioning.

Applications missing any of the above items are incomplete and must not be auto-approved or
auto-denied; they should be held in a pending-documentation state until the applicant supplies
the missing item, or routed to manual review if the missing item cannot reasonably be obtained.

## 6. Manual Review Escalation Criteria

The following cases must be escalated to a human underwriter and are not eligible for a fully
automated decision, even when individual thresholds above suggest a clear outcome:

- Applications with a **medium risk tier** (default probability 0.30-0.60), which are never
  eligible for straight-through automatic approval under Section 3.
- Applications with a **DTI ratio above 0.43** but below the severe-concern threshold of 0.55,
  where a compensating factor might justify approval.
- Applications with **any red flag** from Section 4, regardless of computed risk tier or DTI.
- Applications where the fraud-check tool's top contributing factors include an identity- or
  documentation-related feature, suggesting the risk score may reflect data quality issues rather
  than genuine credit risk.
- Applications requesting a loan amount above the automated approval ceiling defined in the
  pricing addendum, regardless of how favorable the risk tier and DTI are.
- Any application where the applicant has disputed a prior automated decision within the last 12
  months.
- Any case where the underwriting copilot's tool outputs are inconsistent with each other (for
  example, a low default probability from the credit-risk tool alongside a high fraud risk
  score), since this divergence itself indicates the automated signals are not reliable enough
  for a straight-through decision.

Escalated applications must include the full set of tool outputs (credit score, DTI calculation,
fraud check, and any policy citations used in reasoning) in the case file handed to the human
underwriter, so the manual review can be completed without re-running the automated pipeline.
