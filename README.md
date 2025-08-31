# LLean
Testing and understanding LLM reasoning capabilities by trying to prove theorems in Lean

## Setup
1. We use `uv` so you can just use:
```uv sync```
to install dependencies

2. You will need to clone the [https://github.com/leanprover-community/NNG4.git](Natural Number Game repo)
3. Create a `.env` file by copying the `.env.example` file, and replace the defaults with the true values

## Tools
We use [LeanInteract](https://github.com/augustepoiroux/LeanInteract?tab=readme-ov-file#installation-and-setup) to drive the LEAN proving

## Problems
Currently we use the [Lean Natural Number Game](https://github.com/leanprover-community/NNG4/tree/main)