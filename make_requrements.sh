#!/bin/bash

# 패키지 목록
packages=(
    python
    pydantic
    playwright
    feedparser
    newspaper3k
    yfinance
    pandas
    matplotlib
    numpy
    psycopg2-binary
)

# requirements.txt 초기화
echo "# Automatically generated requirements.txt" > requirements.txt

# 각 패키지의 버전을 확인하고 requirements.txt에 추가
for package in "${packages[@]}"
do
    # 패키지 버전 확인
    version=$(python -m pip show $package 2>/dev/null | grep -i 'Version:' | awk '{print $2}')
    
    # 결과 처리
    if [ -n "$version" ]; then
        echo "$package==$version" >> requirements.txt
    else
        echo "# $package is not installed or version cannot be determined" >> requirements.txt
    fi
done

# 완료 메시지
echo "requirements.txt 파일이 생성되었습니다."

