@echo off
setlocal EnableDelayedExpansion

REM Script pour build et lancer le dashboard automatiquement
REM Placez ce fichier à la racine du dossier Projet/

set COMPOSE_FILE=docker-compose.yml
set WEB_URL=http://localhost:5000

REM Demande à l'utilisateur s'il faut rebuild les images
set /p BUILD="Faut-il (re)build les images Docker ? (o/n) : "

cd /d "%~dp0"

if /i "%BUILD%"=="o" (
    echo Build et lancement des services...
    docker-compose -f %COMPOSE_FILE% up --build -d
) else (
    echo Lancement des services sans rebuild...
    docker-compose -f %COMPOSE_FILE% up -d
)

REM Attente que le site web soit disponible
:waitloop
ping -n 2 127.0.0.1 >nul
curl -s %WEB_URL% >nul 2>&1
if errorlevel 1 (
    goto waitloop
)

REM Ouvre le site web automatiquement
start %WEB_URL%

echo Dashboard lancé !
endlocal
