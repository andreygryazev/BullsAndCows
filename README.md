# 🐂 Bulls & Cows - Telegram Bot

A Telegram bot for playing the classic **Bulls and Cows** number-guessing game, with user registration and game statistics.

> **Note:** The bot interface is entirely in **Russian** (Русский).

**Bot:** [@LetovoBullsCows_bot](https://t.me/LetovoBullsCows_bot)

## About the Game

The computer picks a 4-digit number with all unique digits (leading zero is allowed). The player tries to guess it within a limited number of attempts. After each guess the bot reports:
- **Bulls** 🐂 — correct digit in the correct position
- **Cows** 🐄 — correct digit in the wrong position

## Features

- 🔐 Registration & login with persistent sessions (no need to log in every time)
- 👤 Player profile with game statistics
- 📖 In-bot rules explanation
- 🎯 4 difficulty levels (20 / 15 / 12 / 8 attempts)
- 🏳️ Surrender option during a game
- 🗄️ SQLite3 database for data persistence

## Difficulty Levels

| Level              | Attempts |
|--------------------|----------|
| 🟢 Новичок (Beginner)       | 20       |
| 🟡 Любитель (Amateur)       | 15       |
| 🟠 Профессионал (Professional) | 12       |
| 🔴 Бог игры (God Mode)      | 8        |

## Getting Started

```bash
pip install -r requirements.txt
python bot.py
```

## Tech Stack

- Python 3.10+
- python-telegram-bot 22.x
- SQLite3

---

*Project recreated in 2026 (original — autumn 2020).*
