# Research Report

## GitLab CI Rules for Running Unit Tests After Merge

### Summary of Work

I researched how GitLab CI/CD rules determine when jobs run, especially in merge request pipelines versus default branch pipelines. I specifically investigated why retrying an old pipeline after a merge could fail, and whether it would be more reliable to run unit tests again on the default branch after merge. I reviewed GitLab documentation for job rules, predefined CI/CD variables, merge request pipelines, and general pipeline behavior to understand how these conditions are evaluated and how to redesign the test jobs more reliably.[^1] [^2] [^3] [^4]

### Motivation

I performed this research because retrying a failed pipeline after merge was not behaving the way I expected. In practice, retrying the pipeline could fail if the original source branch was deleted after merge. I wanted to understand whether this was related to how GitLab handles branch refs and pipeline sources, and whether changing the CI rules to run tests on the default branch after merge would be a better solution.[^2] [^3]

### Time Spent

~30 minutes reviewing the existing `.gitlab-ci.yml` configuration

~30 minutes reading GitLab documentation on job rules, merge request pipelines, and predefined variables

~40 minutes comparing how `CI_PIPELINE_SOURCE`, `CI_COMMIT_BRANCH`, and `CI_DEFAULT_BRANCH` affect when unit test jobs run

### Results

The most important result of this research was understanding that GitLab job execution can be controlled precisely with `rules`, and that rules are evaluated from top to bottom until the first matching rule is found.[^1] I also learned that predefined variables such as `CI_PIPELINE_SOURCE`, `CI_COMMIT_BRANCH`, and `CI_DEFAULT_BRANCH` are the key variables for deciding whether a job should run for merge requests, branch pushes, or the default branch.[^2]

GitLab’s documentation confirmed that merge request pipelines are distinct from default branch pipelines.[^3][^4] This matters because retrying an old pipeline is not the same as creating a new pipeline for the merged code. A retry still depends on the original pipeline context, while a default branch pipeline runs against the current state of the branch after merge.[^3][^4] Because of that, relying on retrying an old merge-related pipeline is less reliable than explicitly running tests again on the default branch.

Based on this research, I concluded that the most reliable solution for this project was to adjust the unit test jobs so they run on the default branch after merge, instead of relying on merge request retries. Concretely, using a rule such as `if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'` ensures that unit tests are executed on the main branch pipeline after merged changes are present there.[^1][^2] This approach better matches the project goal of validating the actual merged state of the codebase on the main branch.

For example, a backend job can be configured like this:

`rules:
  - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
  - when: never`

With this setup, unit tests run during merge request pipelines and also run again after the code has been merged into the default branch. This makes the pipeline behavior more reliable for checking both pre-merge and post-merge code states.[^1] [^2] [^3]

### Sources

- GitLab CI/CD job rules documentation[^1]
- GitLab predefined CI/CD variables reference[^2]
- GitLab merge request pipelines documentation[^3]
- GitLab CI/CD pipelines overview[^4]

[^1]: https://docs.gitlab.com/ci/jobs/job_rules/
[^2]: https://docs.gitlab.com/ci/variables/predefined_variables/
[^3]: https://docs.gitlab.com/ci/pipelines/merge_request_pipelines/
[^4]: https://docs.gitlab.com/ci/pipelines/