# asyncrepo

`asyncrepo` provides a unified async interface for retrieving data from a variety of sources.

## Installation

`pip install asyncrepo`

## Usage

For now, just check out the live tests for some examples:
- [Greenhouse Jobs Test](tests/live/repositories/greenhouse/test_jobs.py)
- [GitHub Repos Test](tests/live/repositories/github/test_repos.py)

## Motivation

To provide tooling for developers of unified and federated search platforms.

## Currently supported repositories
- `github.repos.Repos` - GitHub repositories belonging to a given user or organization.
- `greenhouse.jobs.Jobs` - Greenhouse jobs belonging to a given board.

## Supported repository operations
- `.get(id: str)`: Get an item from the repository by its ID.
- `.list()`: Get an iterator for all items in the repository.
- `.list_pages()`: Get a paginated iterator for all items in the repository.
- `.search(query: str)`: Get an iterator for all items in the repository that match the query.
- `.search_pages(query: str)`: Get a paginated iterator for all items in the repository that match the query.

## Caveats by repository
†: On the roadmap of things to be addressed.

- `github.repos.Repos`
  - † Does not handle rate limiting, so iteration may have an unrecoverable error.
  - † Uses PyGithub, which is not async.
  - † The `get` operation can retrieve repositories which are out of scope for the user/organization.
- `greenhouse.jobs.Jobs`
  - Uses [naive search](#naive-search).
  - It is a [single page repository](#single-page-repositories).

## Repository quirks
Because this library provides a unified interface for very different sources, all repositories will
have some quirks. Here are some of them.

### Naive search
Search is not natively supported by all sources. As a workaround, some sources fall back to an 
  implementation that performs a naive text search on the raw data for each item in the repository.

### Single page repositories
Some repositories are based on a flat list of items, rather than being paginated. All items from such repositories
  are returned as the first and only page.

## Items
All items are represented by an `Item` object. This object has the following attributes:
- `identifier`: A string that uniquely identifies item, which can be passed to `Repository.get` to retrieve the item.
- `raw`: A dictionary containing the raw data for the item.
- `repository`: The repository that contains the item.

## Wish list
The following is a list of things that might be worked on next.

### General improvements
- Addressing [caveats](#caveats-by-repository) as indicated (†).
- Making the live tests runnable in GitHub Actions.
- Write mock tests for the various supported repositories.
- Add common optional attributes to all items. Things like `title`, `description`, `url`, `created_at`, etc.
- Add a meta repository that can combine multiple repositories.

### Repositories
- [ ] `jira.projects.Projects`
- [ ] `jira.issues.Issues`
- [ ] `confluence.pages.Pages`
- [ ] `confluence.spaces.Spaces`
- [ ] `confluence.blogs.Blogs`
- [ ] `jenkins.jobs.Jobs`
- [ ] `jenkins.builds.Builds`
- [ ] `elastic.indexes.Indexes`
- [ ] `elastic.documents.Documents`
- [ ] `slack.channels.Channels`
- [ ] `slack.users.Users`
- [ ] `slack.messages.Messages`
- [ ] `pypi.packages.Packages`
