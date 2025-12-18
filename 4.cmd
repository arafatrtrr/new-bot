@echo off
title Python Bot Runner

REM Go to project directory
cd /d C:\Users\runneradmin\Documents\new-bot-main

REM Run python script and feed inputs
(
echo 2
echo 10
echo 5
echo n
echo y
echo 2
echo 4
echo 2
) | python main.py

REM Keep terminal open for further user input
cmd
