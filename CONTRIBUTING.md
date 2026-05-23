# Adaptive Learning Platform - Contribution Guide

Welcome! This guide will help you get started with contributing to the project.

## Prerequisites
- Python 3.10+
- Node.js 18+
- `.env` file (see `backend/.env.example`)

## Project Setup
1. **Backend**:
   - `cd backend`
   - `python -m venv venv`
   - `source venv/bin/activate` (or `venv\Scripts\activate`)
   - `pip install -r requirements.txt`
   - `python server.py`

2. **Frontend**:
   - `cd frontend`
   - `npm install`
   - `npm run dev`

## Storage Structure
The project uses `backend/storage/` to manage chat history, flashcards, and quizzes. Do not store binary files in these directories.

## Contributing
- Open an issue for bugs or feature requests.
- Create a new branch for your changes.
- Ensure your changes follow the existing codebase style.
