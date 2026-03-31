#!/usr/bin/env python3
"""
매일 오전 8시(KST) 알레르기 식단 알림 스케줄러
실행: python3 /opt/app/project/main/scripts/scheduler.py
백그라운드: nohup python3 /opt/app/project/main/scripts/scheduler.py >> /var/log/wiz/scheduler.log 2>&1 &
"""
import os
import schedule
import time
import urllib.request
import urllib.error
import logging

# KST 기준으로 스케줄 실행
os.environ['TZ'] = 'Asia/Seoul'
time.tzset()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SCHEDULER_URL = "http://localhost:3000/api/scheduler/allergy-check?key=childnote-scheduler-2026"
CLEANUP_URL = "http://localhost:3000/api/scheduler/cleanup-meal-files?key=childnote-scheduler-2026"

def run_allergy_check():
    logging.info("알레르기 식단 체크 시작...")
    try:
        req = urllib.request.Request(SCHEDULER_URL)
        req.add_header('Cookie', 'season-wiz-project=main')
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            logging.info(f"알레르기 체크 완료: {body}")
    except urllib.error.URLError as e:
        logging.error(f"알레르기 체크 실패: {e}")
    except Exception as e:
        logging.error(f"알레르기 체크 오류: {e}")

def run_meal_file_cleanup():
    logging.info("전월 식단 파일 정리 시작...")
    try:
        req = urllib.request.Request(CLEANUP_URL)
        req.add_header('Cookie', 'season-wiz-project=main')
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            logging.info(f"파일 정리 완료: {body}")
    except urllib.error.URLError as e:
        logging.error(f"파일 정리 실패: {e}")
    except Exception as e:
        logging.error(f"파일 정리 오류: {e}")

# 매일 오전 8시(KST) 실행
schedule.every().day.at("08:00").do(run_allergy_check)
# 매월 1일 자정(KST) 실행 (매일 체크, 1일인 경우만 실행)
import datetime as _dt
def _monthly_cleanup():
    if _dt.date.today().day == 1:
        run_meal_file_cleanup()
schedule.every().day.at("00:05").do(_monthly_cleanup)

logging.info("스케줄러 시작 (KST) - 매일 08:00 알레르기 알림, 매월 1일 00:05 파일 정리")

while True:
    schedule.run_pending()
    next_run = schedule.idle_seconds()
    if next_run is not None:
        hrs = int(next_run // 3600)
        mins = int((next_run % 3600) // 60)
        logging.debug(f"다음 작업까지 {hrs}시간 {mins}분")
    time.sleep(60)
