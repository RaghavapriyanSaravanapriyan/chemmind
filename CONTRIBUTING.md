# Contributing to ChemMind


To keep development organized and avoid merge conflicts, every contributor should follow the workflow below.

---

## Repository

```text
https://github.com/RaghavapriyanSaravanapriyan/chemmind
```

---

## Step 1: Accept the GitHub Invitation

- Open the invitation email or GitHub notification.
- Click **Accept Invitation**.
- You should now have access to the ChemMind repository.

---

## Step 2: Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/RaghavapriyanSaravanapriyan/chemmind.git
cd chemmind
```

---

## Step 3: Checkout Your Assigned Branch

Each team member has a dedicated branch.

### Frontend

```bash
git checkout frontend
```

### Backend

```bash
git checkout backend
```

### DevOps

```bash
git checkout devops
```

### AI / RAG

```bash
git checkout rag
```

To verify that you're on the correct branch:

```bash
git branch
```

Example:

```text
main
* frontend
  backend
  rag
  devops
```

---

## Step 4: Pull the Latest Changes

Before starting any work, always update your branch.

```bash
git pull origin <your-branch>
```

Example:

```bash
git pull origin frontend
```

---

## Step 5: Develop

Work on your assigned tasks as usual.

- Write clean, readable code.
- Test your changes before committing.
- Keep commits focused on a single feature or fix whenever possible.

---

## Step 6: Commit Your Changes

Stage your changes:

```bash
git add .
```

Create a commit:

```bash
git commit -m "Short description of your changes"
```

Examples:

```bash
git commit -m "Added PDF upload component"
```

```bash
git commit -m "Implemented authentication endpoints"
```

---

## Step 7: Push Your Branch

Push your latest commits:

```bash
git push
```

Since your branch is already linked to GitHub, this is all you need.

---

## Step 8: Create a Pull Request

When your feature is complete:

1. Open the ChemMind repository on GitHub.
2. Navigate to **Pull Requests**.
3. Click **New Pull Request** (or **Compare & Pull Request**).
4. Set:
   - **Base branch:** `main`
   - **Compare branch:** your assigned branch

Example:

```text
frontend → main
```

5. Write a clear title and description.
6. Click **Create Pull Request**.

Wait for your PR to be reviewed.

> **Do not merge your own Pull Request unless explicitly instructed.**

---

## Step 9: Sync Your Branch After a Merge

Once your Pull Request has been merged, update your branch with the latest changes from `main`.

```bash
git checkout <your-branch>
git fetch origin
git merge origin/main
git push
```

Example:

```bash
git checkout frontend
git fetch origin
git merge origin/main
git push
```

---

# Project Rules

- Never commit directly to `main`.
- Always work on your assigned branch.
- All code must reach `main` through a Pull Request.
- Pull the latest changes before starting work.
- Write meaningful commit messages.
- Test your code before pushing.
- Keep Pull Requests focused and easy to review.

---

## Branch Assignments

| Branch | Responsibility |
|--------|----------------|
| `rag` | AI, RAG pipeline, LLM integration |
| `frontend` | UI, React/Next.js frontend |
| `backend` | FastAPI, APIs, database |
| `devops` | Deployment, Docker, CI/CD, infrastructure |

---

Let's build ChemMind together.