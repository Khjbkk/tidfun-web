@echo off
REM Windows: double-click start.bat
cd /d %~dp0
where node >nul 2>nul || (echo Install Node.js 18+ from https://nodejs.org & pause & exit /b)
if not exist .env (copy .env.example .env >nul & echo Created .env - fill it in, then run start.bat again & pause & exit /b)
start "chatfarang-bot" cmd /k node local\server.mjs
echo Look for https://xxxx.trycloudflare.com below, put it in PUBLIC_URL (.env) and the Meta webhook Callback URL
npx --yes cloudflared tunnel --url http://localhost:8787
