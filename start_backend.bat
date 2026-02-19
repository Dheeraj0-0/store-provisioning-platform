@echo off
cd backend
venv\Scripts\uvicorn main:app --reload
pause
