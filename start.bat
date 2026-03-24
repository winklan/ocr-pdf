@echo off
title OCR - Conversor de PDF
cd /d C:\Users\Henrique\ocr-pdf
call venv\Scripts\activate
echo.
echo ============================================
echo  OCR - Conversor de PDF Digitalizado
echo  Acesse: http://localhost:5000
echo  Pressione Ctrl+C para parar o servidor
echo ============================================
echo.
python app.py
pause
