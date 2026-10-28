# Web release — 2026-10-28

Publishes the latest web/backend improvements on top of the current Yandex ID release:

- Minimal chat header and settings dialog; saved answers, guest examples and audio controls alongside memories.
- Owner-scoped exact-question answer/audio cache, preview and explicit acceptance/discard of new speech takes.
- Account ZIP export with owned media and optional browser chat history; temporary OAuth transactions excluded.
- Consistent annual plan catalogue on the app home; pricing remains interest registration without payment, and billing quotas have not been migrated to the proposed catalogue.
- Generated speech uses the attached Railway volume when present, with legacy local-file reads preserved across the transition.
- PostgreSQL row-level security enabled for OAuth transaction tables; existing Google links and memorial data are retained.
- Correct app-basename links for pricing, memorial creation and demo navigation.

Validation: full backend suite 409 passed / 9 skipped; 35 focused tests after persistence/security changes; 14 frontend tests; production build and targeted ESLint passed. Paid AI generation was mocked during tests. Production smoke/UI checks follow deployment.

Local preview launchers, databases, uploads, emotion-test fixtures and credentials are not part of this release. Native mobile source changes require a separate device build/release.
