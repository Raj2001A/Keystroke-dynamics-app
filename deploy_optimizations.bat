@echo off
echo ========================================================
echo  Deploying Optimized Type2Branch (Desktop) to DGX
echo ========================================================
echo.
echo 1. Uploading optimized configuration (K=40, Beta=0.05)...
scp "r:\Project papers\Type2Branch\repo\conf.py" P126033005@172.16.13.100:~/repo/

echo.
echo 2. Uploading fixed model architecture (LSTM + 512 Filters)...
scp "r:\Project papers\Type2Branch\repo\model.py" P126033005@172.16.13.100:~/repo/

echo.
echo 3. Uploading execution script...
scp "r:\Project papers\Type2Branch\repo\run_pipeline.sh" P126033005@172.16.13.100:~/repo/

echo.
echo ========================================================
echo  Deployment Complete!
echo ========================================================
echo.
echo To start training on the SASTRA Cluster, follow these exact steps:
echo 1. Login to the main gateway: ssh P126033005@172.16.13.100
echo 2. Enable base conda:        source /SASTRA-NEW-CLUSTER/apps/anaconda3/bin/activate
echo 3. Connect to the GPU node:  ssh dgx-node1
echo 4. Activate ML environment:  conda activate LABENV
echo 5. Deploy the fast run:      tmux new -s fast_run "cd ~/repo && RUN_CONTINUOUS_EVAL=0 RUN_CONTINUOUS_ABLATIONS=0 bash run_pipeline.sh 2>&1 | tee pipeline_fast_$(date +%%F_%%H-%%M-%%S).log"
echo.
pause
