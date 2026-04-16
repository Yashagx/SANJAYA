#!/bin/bash
OTP_ROW=$(sudo docker exec sanjaya-auth-db psql -U sanjaya_auth_user -d sanjaya_auth_db -t -c "SELECT code, challenge_id FROM mfa_challenges ORDER BY created_at DESC LIMIT 1;")
echo "OTP_ROW: $OTP_ROW"
