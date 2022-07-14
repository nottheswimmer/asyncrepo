# [asyncrepo](https://github.com/nottheswimmer/asyncrepo)

`asyncrepo` provides a unified async interface for retrieving data from a variety of sources.

## Installation

`pip install asyncrepo`

## Usage

For now, just check out the live tests for some examples:

- [AWS S3 Buckets Test](tests/live/repositories/aws/test_s3_buckets.py)
- [AWS S3 Objects Test](tests/live/repositories/aws/test_s3_objects.py)
- [Confluence Pages Test](tests/live/repositories/confluence/test_pages.py)
- [File CSV Rows Test](tests/live/repositories/file/test_csv_rows.py)
- [GitHub Repos Test](tests/live/repositories/github/test_repos.py)
- [Greenhouse Jobs Test](tests/live/repositories/greenhouse/test_jobs.py)
- [Jira Issues Test](tests/live/repositories/jira/test_issues.py)

## Motivation

To provide tooling for developers of unified and federated search platforms.

## Currently supported repositories

- `aws.s3_buckets.S3Buckets` - AWS S3 buckets belonging to the current user.
- `aws.s3_objects.S3Objects` - AWS S3 objects belonging to a bucket.
- `confluence.pages.Pages` - Confluence pages belonging to a given organization
- `file.csv_rows.CSVRows` - CSV rows within a given file specified by filepath or URL
- `github.repos.Repos` - GitHub repositories belonging to a given user or organization.
- `greenhouse.jobs.Jobs` - Greenhouse jobs belonging to a given board.
- `jira.issues.Issues` - JIRA issues belonging to a given organization.

## Supported repository operations

- `.get(id: str)`: Get an item from the repository by its ID.
- `.list()`: Get an iterator for all items in the repository.
- `.list_pages()`: Get a paginated iterator for all items in the repository.
- `.search(query: str)`: Get an iterator for all items in the repository that match the query.
- `.search_pages(query: str)`: Get a paginated iterator for all items in the repository that match the query.

## Support by repository

|        Repository        |        .get         | .list |        .search         | Non-blocking IO | Authentication                                                                        |
|:------------------------:|:-------------------:|:-----:|:----------------------:|-----------------|---------------------------------------------------------------------------------------|
| aws.s3_buckets.S3Buckets |         Yes         |  Yes  | [Naive](#naive-search) | Yes             | [AWS](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) |
| aws.s3_objects.S3Objects |         Yes         |  Yes  |          Yes           | Yes             | [AWS](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) |
|  confluence.pages.Pages  |         Yes         |  Yes  |          Yes           | Yes             | Basic                                                                                 |
|  file.csv_rows.CSVRows   | [Naive](#naive-get) |  Yes  | [Naive](#naive-search) | Yes             | None                                                                                  |
|    github.repos.Repos    |         Yes         |  Yes  |          Yes           | Yes             | Token                                                                                 |
|   greenhouse.jobs.Jobs   |         Yes         |  Yes  | [Naive](#naive-search) | Yes             | None                                                                                  |
|    jira.issues.Issues    |         Yes         |  Yes  |          Yes           | Yes             | Basic                                                                                 |

## Caveats by repository

†: On the roadmap of things to be addressed.

- `aws.s3_buckets.S3Buckets`
    - † Only basic metadata is available about buckets.
    - † Currently implemented as a [single page repository](#single-page-repositories).
- `aws.s3_objects.S3Objects`
    - † No options to get the contents of an object.
    - † Only basic metadata is available about objects.
    - Search is implemented using the prefix search API.
- `confluence.pages.Pages`
    - † No options to limit the repository scope to a specific space.
    - The search API seems to occasionally return an empty result set for a query
      that should have results. This results in fragile live tests for the repository.
      This may only happen under high concurrency.
    - Similar to the above, the API will occasionally return a 500 error when querying
      under high concurrency.
    - † There is a simple retry system in place to address the aforementioned 500 error
      But it should be abstracted out into a more general retry system that can be applied
      to other repositories.
- `file.csv_rows.CSVRows`
  - † There is no options for caching the file. If a URL is used, that means every time the
    file is queried, it will be downloaded (e.g. every get, search, or list operation). In the
    future, it would be nice to be able to cache the file either in memory or on disk with some
    sort of TTL.
  - Because CSVs have no natural pages, there is a page_size option that can be used to limit
    the number of rows returned per page. The default is 20. This allows you to load in some data
    without loading the entire file into memory.
  - Because CSV rows have no natural primary key, the identifier defaults to the row index. You can
    change this by passing an identifier to the repository, which expects either the name of a column
    or a tuple of column names.
- `github.repos.Repos`
    - † May need additional work to mitigate rate limiting issues.
    - ~~† Uses PyGithub, which is not async.~~
    - † Patches PyGithub to support async (should consider using a different library like Gidgethub).
    - † The `get` operation can retrieve repositories which are out of scope for the user/organization.
- `greenhouse.jobs.Jobs`
    - It is a [single page repository](#single-page-repositories).
- `jira.issues.Issues`
    - † No options to limit the repository scope to a specific project.
    - The .get method accepts either keys or IDs, but the .identifier for items is always the ID.
      This is because the ID doesn't change, whereas the key could change by moving the issue to
      a different project.

## Repository quirks

Because this library provides a unified interface for very different sources, all repositories will
have some quirks. Here are some of them.

### Naive search

Search is not natively supported by all sources. As a workaround, some sources fall back to an
implementation that performs a text search on the raw data for each item in the repository.

### Naive get

Get is not natively supported by all sources. As a workaround, some sources fall back to an
implementation that performs a scan of the entire repository to find the item with the given ID.

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
- Support for non-default orderings.
- Stop subclassing ClientSession from aiohttp because it makes the developer sad.
- More enterprise-friendly implementations. Testing is done on cloud-hosted services
  and those APIs are often different from the on-premise ones. Submit a ticket or a
  pull request if you want to help.
- Split dependencies into separate packages depending on which repositories are desired.

### Potential Repositories

- [ ] `jira.projects.Projects`
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
- [ ] `google.drive.Files`
- [ ] `google.mail.Mail`
- [ ] `google.calendar.Events`
- [ ] `github.code.Code`

## Contribution Guidelines

Please submit a ticket if you have an idea for a new feature or you've found a bug. 
You can also submit a pull request if you have a solution to the problem!

And hey, don't feel anxious about contributing. If you're interested in helping improve
this library by submitting a pull request, I'd be extremely happy to hear from you.

### Bug fixes

- [ ] Create a test which fails because of the identified bug
- [ ] Fix the bug
- [ ] Ensure the test passes
- [ ] Submit a pull request

### New features

- [ ] Create a test which fails because the new feature is not implemented
- [ ] Implement the new feature
- [ ] Ensure the test passes
- [ ] Submit a pull request

### New repository checklist

- [ ] Add your new repository to the `asyncrepo.repositories` module.
- [ ] At minimum, your repository should support getting and listing.
  Fallback to naive search is OK if there isn't a better way.
- [ ] Add live tests for your repository. If credentials are required
  and you have to set up the tests against a private server, outline
  what credentials are required in the env.dist file and make it clear
  what data is expected to exist in the test environment.
- [ ] Ensure the tests pass
- [ ] Document your repository in this file.
- [ ] Submit a pull request.
