🔍 Applying filters: Pipeline: operator-hosted-pipeline
╭─────────────────────────── 🔧 Pipeline Overview ───────────────────────────╮
│               Pipeline: operator-hosted-pipeline (Filtered)                │
│ ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Metric           ┃ Value                                               ┃ │
│ ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ Total Executions │ 843                                                 │ │
│ │ Successful       │ 519                                                 │ │
│ │ Failed           │ 254                                                 │ │
│ │ Success Rate     │ 61.6%                                               │ │
│ │ First Seen       │ 2025-07-03 15:38:19.603313                          │ │
│ │ Last Seen        │ 2025-07-03 16:14:26.219398                          │ │
│ │ Repositories     │ redhat-openshift-ecosystem/community-operators-prod │ │
│ └──────────────────┴─────────────────────────────────────────────────────┘ │
╰────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────────────── 📋 Task Statistics ─────────────────────────────────────╮
│                                  Task Statistics (Filtered)                                  │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓ │
│ ┃ Task Name                            ┃ Total ┃ Success ┃ Failed ┃ Skipped ┃ Success Rate ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━┩ │
│ │ preflight-trigger                    │ 677   │ 583     │ 32     │ 0       │ 86.1%        │ │
│ │ add-bundle-to-index                  │ 487   │ 450     │ 37     │ 0       │ 92.4%        │ │
│ │ build-fbc-scratch-catalog            │ 105   │ 98      │ 7      │ 0       │ 93.3%        │ │
│ │ merge-pr                             │ 551   │ 519     │ 32     │ 0       │ 94.2%        │ │
│ │ evaluate-preflight-result            │ 454   │ 432     │ 22     │ 0       │ 95.2%        │ │
│ │ build-bundle                         │ 754   │ 721     │ 33     │ 0       │ 95.6%        │ │
│ │ static-tests                         │ 787   │ 754     │ 33     │ 0       │ 95.8%        │ │
│ │ detect-changes                       │ 829   │ 801     │ 21     │ 0       │ 96.6%        │ │
│ │ add-bundle-to-fbc-dryrun             │ 430   │ 420     │ 10     │ 0       │ 97.7%        │ │
│ │ build-fragment-images                │ 109   │ 107     │ 2      │ 0       │ 98.2%        │ │
│ │ acquire-lease                        │ 843   │ 830     │ 13     │ 0       │ 98.5%        │ │
│ │ yaml-lint                            │ 668   │ 658     │ 10     │ 0       │ 98.5%        │ │
│ │ check-permissions                    │ 791   │ 789     │ 2      │ 0       │ 99.7%        │ │
│ │ clone-repository                     │ 830   │ 829     │ 0      │ 0       │ 99.9%        │ │
│ │ clone-repository-base                │ 830   │ 829     │ 0      │ 0       │ 99.9%        │ │
│ │ get-pr-number                        │ 843   │ 843     │ 0      │ 0       │ 100.0%       │ │
│ │ set-github-started-label             │ 830   │ 830     │ 0      │ 0       │ 100.0%       │ │
│ │ set-github-status-pending            │ 830   │ 830     │ 0      │ 0       │ 100.0%       │ │
│ │ set-env                              │ 830   │ 830     │ 0      │ 0       │ 100.0%       │ │
│ │ set-github-pr-title                  │ 789   │ 789     │ 0      │ 0       │ 100.0%       │ │
│ │ read-config                          │ 789   │ 789     │ 0      │ 0       │ 100.0%       │ │
│ │ resolve-pr-type                      │ 789   │ 789     │ 0      │ 0       │ 100.0%       │ │
│ │ apply-test-waivers                   │ 656   │ 656     │ 0      │ 0       │ 100.0%       │ │
│ │ content-hash                         │ 787   │ 787     │ 0      │ 0       │ 100.0%       │ │
│ │ certification-project-check          │ 787   │ 787     │ 0      │ 0       │ 100.0%       │ │
│ │ get-organization                     │ 787   │ 787     │ 0      │ 0       │ 100.0%       │ │
│ │ get-pyxis-certification-data         │ 787   │ 787     │ 0      │ 0       │ 100.0%       │ │
│ │ merge-registry-credentials           │ 754   │ 754     │ 0      │ 0       │ 100.0%       │ │
│ │ digest-pinning                       │ 754   │ 754     │ 0      │ 0       │ 100.0%       │ │
│ │ verify-pinned-digest                 │ 754   │ 754     │ 0      │ 0       │ 100.0%       │ │
│ │ dockerfile-creation                  │ 754   │ 754     │ 0      │ 0       │ 100.0%       │ │
│ │ make-bundle-repo-public              │ 616   │ 616     │ 0      │ 0       │ 100.0%       │ │
│ │ get-supported-versions               │ 721   │ 721     │ 0      │ 0       │ 100.0%       │ │
│ │ make-index-repo-public               │ 572   │ 572     │ 0      │ 0       │ 100.0%       │ │
│ │ get-ci-results-attempt               │ 677   │ 677     │ 0      │ 0       │ 100.0%       │ │
│ │ get-ci-results                       │ 561   │ 561     │ 0      │ 0       │ 100.0%       │ │
│ │ link-pull-request-with-open-status   │ 561   │ 561     │ 0      │ 0       │ 100.0%       │ │
│ │ link-pull-request-with-merged-status │ 464   │ 464     │ 0      │ 0       │ 100.0%       │ │
│ │ validate-catalog-format              │ 109   │ 109     │ 0      │ 0       │ 100.0%       │ │
│ │ build-fbc-index-images               │ 105   │ 105     │ 0      │ 0       │ 100.0%       │ │
│ │ static-tests-results                 │ 2     │ 2       │ 0      │ 0       │ 100.0%       │ │
│ └──────────────────────────────────────┴───────┴─────────┴────────┴─────────┴──────────────┘ │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
