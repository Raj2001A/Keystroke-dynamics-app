@echo off
setlocal
set "REMOTE=P126033005@172.16.13.100:~/repo"

echo Downloading results from DGX (172.16.13.100)...
if not exist model mkdir model
if not exist results_hardened mkdir results_hardened
if not exist results_continuous mkdir results_continuous

scp -r %REMOTE%/results_hardened/* ./results_hardened/
scp -r %REMOTE%/results_continuous/* ./results_continuous/
scp -r %REMOTE%/model/* ./model/
scp %REMOTE%/LOSS.png .
scp %REMOTE%/paper_results_manifest.json .
scp %REMOTE%/pipeline_*.log .

echo.
echo If any file was missing on the server, scp may show a warning for that file only.
echo.
echo Download complete! Check the 'results_hardened', 'results_continuous', and 'model' folders.
echo.
pause
