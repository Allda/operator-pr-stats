🔍 Applying filters: Pipeline: operator-release-pipeline
╭─────────────────────────── 🔧 Pipeline Overview ───────────────────────────╮
│               Pipeline: operator-release-pipeline (Filtered)               │
│ ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Metric           ┃ Value                                               ┃ │
│ ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ Total Executions │ 535                                                 │ │
│ │ Successful       │ 481                                                 │ │
│ │ Failed           │ 49                                                  │ │
│ │ Success Rate     │ 89.9%                                               │ │
│ │ First Seen       │ 2025-07-03 15:38:19.603501                          │ │
│ │ Last Seen        │ 2025-07-03 16:14:26.219252                          │ │
│ │ Repositories     │ redhat-openshift-ecosystem/community-operators-prod │ │
│ └──────────────────┴─────────────────────────────────────────────────────┘ │
╰────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────── 📋 Task Statistics ──────────────────────────────────────╮
│                                   Task Statistics (Filtered)                                   │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓ │
│ ┃ Task Name                              ┃ Total ┃ Success ┃ Failed ┃ Skipped ┃ Success Rate ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩ │
│ │ publish-to-index                       │ 425   │ 395     │ 29     │ 0       │ 92.9%        │ │
│ │ add-bundle-to-index                    │ 356   │ 341     │ 13     │ 0       │ 95.8%        │ │
│ │ build-fragment-images                  │ 89    │ 88      │ 1      │ 0       │ 98.9%        │ │
│ │ add-bundle-to-fbc                      │ 425   │ 421     │ 4      │ 0       │ 99.1%        │ │
│ │ sign-index-image                       │ 428   │ 424     │ 2      │ 0       │ 99.1%        │ │
│ │ set-github-started-label               │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ set-github-status-pending              │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ set-env                                │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ clone-repository-base                  │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ clone-repository                       │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ detect-changes                         │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ read-config                            │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ resolve-pr-type                        │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ content-hash                           │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ certification-project-check            │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ get-organization                       │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ get-pyxis-certification-data           │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ copy-bundle-image-to-released-registry │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ get-supported-versions                 │ 535   │ 535     │ 0      │ 0       │ 100.0%       │ │
│ │ acquire-lease                          │ 534   │ 534     │ 0      │ 0       │ 100.0%       │ │
│ │ build-fbc-index-images                 │ 88    │ 88      │ 0      │ 0       │ 100.0%       │ │
│ │ decide-index-paths                     │ 1     │ 1       │ 0      │ 0       │ 100.0%       │ │
│ │ get-manifest-digests                   │ 1     │ 1       │ 0      │ 0       │ 100.0%       │ │
│ │ request-signature                      │ 1     │ 1       │ 0      │ 0       │ 100.0%       │ │
│ │ upload-signature                       │ 1     │ 1       │ 0      │ 0       │ 100.0%       │ │
│ └────────────────────────────────────────┴───────┴─────────┴────────┴─────────┴──────────────┘ │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
