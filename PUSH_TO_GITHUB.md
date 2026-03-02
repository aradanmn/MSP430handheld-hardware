# How to Push This Repo to GitHub

Run these commands once in your terminal to create the GitHub repo and push everything:

```bash
# 1. Navigate to this folder
cd ~/Documents/msp430-dev-vm/handheld-msp430

# 2. Create the repo on GitHub and push (requires gh CLI)
gh repo create Handheld-MSP430 --public --source=. --remote=origin --push

# --- OR, if you prefer plain git: ---

# 2a. Create the repo on GitHub manually at https://github.com/new
#     Name: Handheld-MSP430   Visibility: Public   Do NOT add README/gitignore

# 2b. Then push:
git remote add origin https://github.com/YOUR_USERNAME/Handheld-MSP430.git
git push -u origin main
```

## After that — syncing future changes

After each Claude session I'll commit new files locally. To sync with GitHub:

```bash
cd ~/Documents/msp430-dev-vm/handheld-msp430
git push
```

That's it — one command after each session.
