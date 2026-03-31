#!/bin/bash
# 알레르기 식단 알림 스케줄러 (백그라운드 프로세스)
# 실행: nohup /opt/app/project/main/scripts/allergy-cron.sh &
# 또는: python3 /opt/app/project/main/scripts/scheduler.py &

python3 /opt/app/project/main/scripts/scheduler.py
