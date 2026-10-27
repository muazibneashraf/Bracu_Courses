# Muaz CSE Courses

Coursework, programming labs, assignments, and Google Colab notebooks organized by course.

## Repository structure

Each official course has its own folder. The names and titles follow the
[BRAC University CSE course list](https://cse.bracu.ac.bd/course/list).
Folders are created even when no local material was available, so the
repository has a complete catalog structure:

```text
CSE110/  CSE111/  CSE220/  CSE221/  CSE230/
CSE250/  CSE251/  CSE260/  CSE320/  CSE321/
CSE330/  CSE331/  CSE340/  CSE341/  CSE350/
CSE360/  CSE370/  CSE400/  CSE420/  CSE421/
CSE422/  CSE423/  CSE460/  CSE461/  CSE470/
CSE471/  CSE700/  CSE705/ ... / CSE798/
```

Notebooks whose filenames did not include a course code were classified from
their content. Algorithm and data-structure notebooks are in `CSE221`,
numerical-methods notebooks are in `CSE330`, machine-learning notebooks are in
`CSE422`, graphics notebooks are in `CSE423`, and robotics notebooks are in
`CSE461`.

The current catalog does not list the local `CSE428`, `CST309`, or `MAT215`
codes. Their files are preserved under `Other-Courses/` rather than being
presented as current official CSE courses.

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
