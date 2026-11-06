EISENHOWER DAILY - RUN IT ON YOUR OWN COMPUTER

1. Unzip this folder somewhere permanent, e.g. Documents\Eisenhower Daily.
2. Start it:
   - Windows: double-click "Start Planner (Windows).bat"
   - Mac: right-click "Start Planner (Mac).command" > Open (first time only)
   - Or in a terminal:  python run_planner.py
   Your browser opens http://localhost:8765. Keep the small black window open while you work.
3. Connect Jira: Rules & settings > Jira > enter your site (yourcompany.atlassian.net),
   your Jira email and an API token from
   https://id.atlassian.com/manage-profile/security/api-tokens  > Save and sync.

Where things are kept (all in this folder):
- planner-data.json   your tasks, rules and Jira choices. Back this file up to keep your history.
- jira-config.json    your Jira site, email and API token (plain text: don't share this file).

Needs Python 3.8+ (Windows: install from python.org and tick "Add Python to PATH").
