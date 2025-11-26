# MORS Depression Bot

Telegram-bot for weekly monitoring of emotional state, BDI-II score, and therapy adherence for MS Center MORS.

## 🚀 Features
- Weekly scheduled questionnaire (general feeling, PITSRS adherence, antidepressant use, BDI-II)
- Data saved locally in CSV/JSON
- Clean and structured conversation flow
- APScheduler weekly broadcasts (Fridays at 13:30)
- Support for multiple users
- Ready for deployment on Selectel / any VPS

## 🧰 Tech stack
- Python 3.10+
- python-telegram-bot
- APScheduler
- python-dotenv

## ▶️ Running locally
pip install -r requirements.txt
python mors_depression_bot.py

## 🖥 Deployment on server (Selectel)

Install Python and pip

Clone the repository:
git clone https://github.com/ponevej-boop/mors-depression-bot

Create virtual environment

Install requirements

Create .env file:
BOT_TOKEN=your_token

Set up systemd service for auto-restart

## 📁 File structure
mors-depression-bot/
├── mors_depression_bot.py
├── requirements.txt
├── .gitignore
└── README.md
