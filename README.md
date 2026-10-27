# Muaz CSE Courses

Coursework, programming labs, assignments, and Google Colab notebooks organized by course.

## Repository structure

Each course has its own folder:

```text
CSE321/
CSE331/
CSE340/
...
CSE428/
CST309/
MAT215/
Unclassified/
```

The `Unclassified` folder contains Colab notebooks whose filenames did not include a recognizable course code. Rename and move these notebooks when their course is known.

## Working with the notebooks

The notebooks were exported from Google Colab and may depend on:

- Google Drive files or datasets that are not included here
- Colab-only paths such as `/content`
- Packages installed during a notebook session
- API keys or other private configuration

Do not commit passwords, API keys, access tokens, private datasets, or personal credentials. Use environment variables or a local `.env` file instead. The `.env` file is ignored by Git.

## Important publishing checks

Before making this repository public:

1. Review notebooks for personal information, student IDs, credentials, and private links.
2. Remove outputs or datasets that you do not have permission to redistribute.
3. Check assignment and course-material copyright restrictions.
4. Run `git diff --cached` and inspect the staged files before the first push.

## Suggested notebook workflow

Open a notebook in VS Code with the Jupyter extension, or upload it back to Google Colab. Update paths and install required packages in the first code cell so another user can reproduce the work.
