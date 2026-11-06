# Eisenhower Daily

A daily priority planner built on the Eisenhower Matrix (Do / Schedule / Delegate / Eliminate), with a Jira inbox. It runs on your own computer and needs no extra installs beyond Python.

## What it does
- Sorts each day's tasks into the four boxes using **Urgent** and **Important** toggles
- **Carries unfinished tasks to the next day** automatically, showing how many days late each one is
- Moves important work to **Do** if it keeps slipping, and makes tasks urgent as their due date gets close
- Drops low-value tasks that sit in **Eliminate** for too long
- Supports repeating tasks (daily, weekdays, weekly)
- **Jira inbox**: shows open tickets assigned to you, with Ignore and "never show" rules, and ticks off tasks once their ticket is Done or Deployed on Prod
- Every rule can be changed or switched off in **Rules & settings**

## Run it
1. Install Python 3.8 or newer from python.org (on Windows, tick "Add python.exe to PATH").
2. Download this repository (green **Code** button → **Download ZIP**) and unzip it.
3. Double-click `Start Planner (Windows).bat`, or `Start Planner (Mac).command` on a Mac.
4. The planner opens at http://localhost:8765. Keep the small terminal window open while you use it.

## Connect Jira (optional)
In **Rules & settings → Jira**, enter your Jira site, your Jira email and an API token from
https://id.atlassian.com/manage-profile/security/api-tokens, then press **Save and sync**.

## Your data stays on your computer
- `planner-data.json` holds your tasks and settings.
- `jira-config.json` holds your Jira API token.

Both files are created next to the launcher and are listed in `.gitignore`, so Git never uploads them.

## Files
| File | Purpose |
|---|---|
| `eisenhower-daily.html` | The planner itself |
| `run_planner.py` | Small local server: saves your data and talks to Jira |
| `Start Planner (Windows).bat` / `(Mac).command` | One-click start |
