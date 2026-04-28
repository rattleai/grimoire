# acme — tenant preferences

## Style
- Product names: keep exact wording from the source pricelist
- Area naming: `"<SKU> — <Section>"` with em-dash separator
- Language for option / group descriptions: `de`

## Preferences
- **custom-keys**: never
- **option-standard-variant**: always present, price 0, recommended=true
- **language**: de
- **decimal-separator**: comma

## Offer documents
- doc_type: `offer`
- Required chapters: Product Overview (static content block) + Configuration (dynamic:document_configuration) + Pricing (dynamic:document_line_items)
- Hero image: `acme-logo.png` from `/files/`

## Suppressions
- Suppress audit finding: `options-with-custom-keys` is opt-in via `custom-keys: never` above; do not suppress otherwise.

## Notes for the consultant
- We migrated from an offer-sections-based template in 2025; do not re-introduce offer-sections.
- New product lines start as draft (`is_published: false`) until the customer signs off the offer template.
