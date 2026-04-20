# Lab Codex Skills

Shared Codex skill folders for lab workflows.

## Install From Scratch

Run these commands in a terminal if you have SSH access configured for GitHub:

```bash
mkdir -p ~/code
git clone git@github.com:ransona/lab_codex_skills.git ~/code/lab_codex_skills
cd ~/code/lab_codex_skills
./install_skills.sh
```

If you do not have SSH access configured for GitHub, use HTTPS instead:

```bash
mkdir -p ~/code
git clone https://github.com/ransona/lab_codex_skills.git ~/code/lab_codex_skills
cd ~/code/lab_codex_skills
./install_skills.sh
```

The installer copies each top-level skill folder from this repository into:

```bash
~/.codex/skills
```

If a skill folder already exists there, the script asks whether to overwrite it.

## Manual Install

To install a skill manually, copy the whole skill folder into the Codex skills folder:

```bash
mkdir -p ~/.codex/skills
cp -a ~/code/lab_codex_skills/lab-data-access ~/.codex/skills/
```

Restart Codex after installing or updating skills so the new skill list is loaded.
