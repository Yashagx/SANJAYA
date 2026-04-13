#!/bin/bash
cd /home/ec2-user/sanjaya
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
