# Coding Standards and Conventions

This document defines the coding standards used across my projects. The goal is to write code that is **clear**, **consistent**, and **easy to maintain**.

> **Clarity is more important than cleverness.**

---

## 1. General Rules

- Write code easy for humans to understand. 
- Prefer readable over concise.
- Avoid unnecessary abstraction.
- Keep functions small and focused.
- Use helpers for complicated functions.
- Minimize hidden side effects.
- Be consistent across the entire project.
- If code is hard to understand, rewrite it. 

---

## 2. Formatting

### Indentation

- **Java, JavaScript, TypeScript:** 2 spaces
- **Python:** 4 spaces
- **Never** use tabs.

### Braces

- Opening brace on the same line.
- Always use braces, even for single-line blocks.

```java
if (condition) {
  doSomething();
} else {
  doSomethingElse();
}
```

### Line Length

- **Maximum:** 100 characters
- **Exceptions:** Certain cases like URLs

### Whitespace

- One space after keywords: `if (x)`
- One space around binary operators
- No trailing whitespace
- No more than one blank line in a row
- One blank line between class members

### One Statement Per Line

Do not place multiple statements on one line.

---

## 3. Naming Conventions

### General Rules

- Use descriptive names.
- No prefixes like `mValue`, `_value`, or `kConstant`.
- ASCII letters and numbers only.

### Classes

- **Style:** `UpperCamelCase`
- **Use:** Nouns

**Example:** `UserService`, `ImageClassifier`

### Methods / Functions

- **Style:** `lowerCamelCase`
- **Use:** Verb-based names

**Examples:** `computeLoss()`, `validateInput()`, `sendEmail()`

### Variables

- **Style:** `lowerCamelCase`
- **Use:** Meaningful but concise

| Avoid | Prefer |
|-------|--------|
| `data` | `userSession` |
| `temp` | `retryCount` |
| `val` | `totalScore` |

### Constants

- **Style:** `UPPER_SNAKE_CASE`
- **Use:** Only for deeply immutable values

**Example:** `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT_MS`

---

## 4. File and Project Structure

**Typical structure:**

```
project/
├── src/
├── tests/
├── docs/
├── README.md
└── style.md
```

- One top-level class per file (Java).
- Tests mirror the structure of `src/`.
- Avoid circular dependencies.

---

## 5. Comments and Documentation

### Comments

- Explain **why**, not **what**.
- Avoid obvious comments.

**Bad:**

```java
// increment counter
counter++;
```

**Good:**

```java
// Skip sentinel node
counter++;
```

### TODO Format

```
TODO(issue-link): Short explanation
```

**Example:**

```java
// TODO(#142): Remove legacy auth after migration.
```

### Documentation

- Public classes and functions **must** have documentation.
- **Java:** Use Javadoc.
- **Python:** Use docstrings (Google style).

---

## 6. Programming Practices

### Error Handling

- Never ignore exceptions.
- Fail fast for invalid inputs.
- Validate inputs at system boundaries.

### Immutability

- Prefer immutable objects.
- Use `final` where possible (Java).
- Avoid shared mutable state.

### Static Members (Java)

Access static members using the class name, not an instance.

### Logging

- Do not log information that shouldn't be shared.
- Include useful context in error logs.
- Avoid excessive debug logs in production.

---

## 7. Testing

- Tests mirror source structure.
- One logical behavior per test.
- Tests must be deterministic.
- Use descriptive test names:

  - **Class:** `UserServiceTest`
  - **Method:** `testComputeLoss_handlesZeroDivision`

---

## 8. Version Control

- One logical change per commit.
- Write clear commit messages:

  ```
  feat: add gradient normalization
  fix: handle null user input
  refactor: simplify validation logic
  ```

- **Never** commit:
  - Secrets
  - Large generated files
  - Temporary debug code

---
