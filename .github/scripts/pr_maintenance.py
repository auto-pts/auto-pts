#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Codecoup.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

"""Periodic maintenance of open pull requests.

Run by scheduled workflow on master. Pull request code is never checked
out or executed, everything is done through GitHub API using gh tool.

- Pull requests are reported for path based labeling, which is done by
  actions/labeler in the workflow.

Path labels are updated only for pull requests changed since previous
successful run, unless .github of their base branch changed too (e.g.
labeler configuration was modified). Labels can't change otherwise.
"""

import json
import os
import subprocess
import sys

# .github trees are queried with object() which returns null if path
# doesn't exist, Commit.file() fails whole query instead
TREES_PER_QUERY: int = 100

#: Repository in owner/name format, set by GitHub Actions
REPO: str = os.environ.get("GITHUB_REPOSITORY", "")
#: Branch the workflow runs on
BRANCH: str = os.environ.get("GITHUB_REF_NAME", "master")
#: Workflow file name, used to find previous runs
WORKFLOW: str = os.environ.get("GITHUB_WORKFLOW_REF",
                               "pr_maintenance.yml").split("@")[0].split("/")[-1]

PULLS_QUERY: str = """
query (
  $owner: String!
  $repo: String!
  $endCursor: String
) {
  repository(owner: $owner, name: $repo) {
    pullRequests(
      states: OPEN
      first: 50
      after: $endCursor
      orderBy: { field: UPDATED_AT, direction: DESC }
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        updatedAt
        baseRefName
        baseRef {
          target {
            oid
          }
        }
      }
    }
  }
}
"""

TREES_QUERY: str = """
query ($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
%s
  }
}
"""

TREE_FIELD: str = 'c%d: object(expression: "%s:.github") { oid }'


def gh(*args: str) -> str:
    """Run gh command.

    :param args: gh command line arguments
    :return: standard output of the command
    :raises subprocess.CalledProcessError: if the command fails
    """
    return subprocess.run(["gh", *args], check=True, capture_output=True,
                          text=True).stdout


def github_trees(commits: list[str]) -> dict[str, str | None]:
    """Get .github tree of commits.

    :param commits: commit SHAs, duplicates are allowed
    :return: dict of commit SHA to its .github tree SHA, or None if the
             commit has no .github directory
    """
    owner, repo = REPO.split("/")
    commits = sorted(set(commits))
    trees = {}

    for i in range(0, len(commits), TREES_PER_QUERY):
        chunk = commits[i:i + TREES_PER_QUERY]
        fields = "\n".join(TREE_FIELD % (n, c) for n, c in enumerate(chunk))
        data = json.loads(gh("api", "graphql",
                             "-f", f"query={TREES_QUERY % fields}",
                             "-f", f"owner={owner}", "-f", f"repo={repo}"))
        result = data["data"]["repository"]
        for n, c in enumerate(chunk):
            trees[c] = (result[f"c{n}"] or {}).get("oid")

    return trees


def previous_run() -> dict | None:
    """Get previous successful run of this workflow.

    :return: workflow run as returned by GitHub REST API, or None if
             there is no successful run or it can't be fetched
    """
    try:
        runs = json.loads(gh("api", f"repos/{REPO}/actions/workflows/"
                             f"{WORKFLOW}/runs?branch={BRANCH}"
                             f"&status=success&per_page=1"))
    except subprocess.CalledProcessError as e:
        print(f"Failed to get previous run: {e.stderr.strip()}")
        return None

    # No successful run yet, e.g. right after workflow was added
    if not runs["workflow_runs"]:
        print("No previous successful run")
        return None

    return runs["workflow_runs"][0]


def list_pulls() -> list[dict]:
    """List open pull requests.

    :return: pull requests as dicts with keys: number (int), updated
             (ISO 8601 str), base_name (str), base_head (str or None) and
             changed (bool, True if labels may be out of date)
    """
    owner, repo = REPO.split("/")
    pages = json.loads(gh("api", "graphql", "--paginate", "--slurp",
                          "-f", f"query={PULLS_QUERY}",
                          "-f", f"owner={owner}", "-f", f"repo={repo}"))
    pulls = []

    for page in pages:
        for node in page["data"]["repository"]["pullRequests"]["nodes"]:
            base = (node["baseRef"] or {}).get("target") or {}
            pulls.append({
                "number": node["number"],
                "updated": node["updatedAt"],
                "base_name": node["baseRefName"],
                "base_head": base.get("oid"),
            })

    previous = previous_run()
    if previous:
        print(f"Previous run started {previous['created_at']} on "
              f"{previous['head_sha']}")

    trees = github_trees([p["base_head"] for p in pulls if p["base_head"]] +
                         ([previous["head_sha"]] if previous else []))

    for pull in pulls:
        # Previous run started before last update of pull request (any
        # push or base change updates it) or before .github of base
        # branch changed, so its labels may be out of date
        pull["changed"] = not previous or \
            pull["updated"] >= previous["created_at"] or \
            pull["base_name"] != previous["head_branch"] or \
            trees.get(pull["base_head"]) != trees[previous["head_sha"]]

    return pulls


def write_outputs(outputs: dict[str, str]) -> None:
    """Write step outputs.

    :param outputs: dict of output name to value, value may be multiline
    """
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        for key, value in outputs.items():
            if "\n" in value:
                f.write(f"{key}<<EOF\n{value}\nEOF\n")
            else:
                f.write(f"{key}={value}\n")


def main() -> None:
    """Find pull requests to update and write step outputs.

    Outputs:
    pr-numbers - newline separated pull requests for path based labeling
    """
    try:
        pulls = list_pulls()
    except subprocess.CalledProcessError as e:
        sys.exit(f"Failed to list pull requests: {e.stderr.strip()}")

    changed = [p for p in pulls if p["changed"]]
    print(f"{len(pulls)} open pull requests, {len(changed)} changed")
    write_outputs({"pr-numbers": "\n".join(str(p["number"])
                                           for p in changed)})


if __name__ == "__main__":
    main()
