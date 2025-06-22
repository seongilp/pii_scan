# pii_scan
# 개인정보 스캔 도구 (PII Scanner)

MySQL 및 Oracle 데이터베이스에서 개인정보 패턴을 스캔하고 분석하는 도구입니다.

## 🔄 프론트엔드 업데이트

Django 프론트엔드에서 Next.js 프론트엔드로 마이그레이션되었습니다. 새로운 프론트엔드는 다음과 같은 개선 사항을 제공합니다:

- 사이드바 레이아웃을 사용한 모던 UI
- 라이트 모드와 다크 모드 지원
- 모바일 및 데스크톱을 위한 반응형 디자인
- 스캔 진행 상황에 대한 실시간 업데이트
- 클라이언트 사이드 렌더링을 통한 향상된 사용자 경험

### Next.js 프론트엔드 실행

```bash
# Next.js 프론트엔드 디렉토리로 이동
cd nextjs_frontend

# 의존성 설치
npm install
# 또는
yarn install

# 개발 서버 실행
npm run dev
# 또는
yarn dev
```

자세한 내용은 [Next.js 프론트엔드 README](nextjs_frontend/README.md)를 참조하세요.

## 🚀 빠른 시작

### 1. uv를 사용한 환경 설정

#### uv 설치 (아직 설치하지 않은 경우)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 프로젝트 의존성 설치
```bash
# 프로젝트 디렉토리로 이동
cd piiscan

# 가상환경 생성 및 의존성 설치
uv sync

# 또는 개발 의존성까지 포함하여 설치
uv sync --dev
```

#### 가상환경 활성화
```bash
# 가상환경 활성화
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate     # Windows

# 또는 uv run을 사용하여 가상환경 없이 실행
uv run python your_script.py
```

#### 추가 패키지 설치
```bash
# 새 패키지 추가
uv add package_name

# 개발 의존성으로 추가
uv add --dev package_name

# 특정 버전으로 추가
uv add package_name==1.2.3
```

### 2. 프로젝트 실행

```bash
# FastAPI 백엔드 실행
uv run python fastapi_privacy_scanner_backend.py
# 또는
uvicorn fastapi_privacy_scanner_backend:app --reload

# Django 프론트엔드 실행 (레거시)
cd django_frontend
uv run python manage.py runserver

# Next.js 프론트엔드 실행 (새로운 버전)
cd nextjs_frontend
npm run dev
# 또는
yarn dev

# MySQL 스캔 실행
uv run python mysql_scan.py

# Oracle 스캔 실행
uv run python oracle_scan.py
```

### 3. Git 관리 및 배포

#### 초기 Git 설정 (처음 한 번만)
```bash
# Git 저장소 초기화
git init

# 원격 저장소 추가 (GitHub/GitLab 등)
git remote add origin https://github.com/username/piiscan.git

# 또는 SSH 사용시
git remote add origin git@github.com:username/piiscan.git
```

#### 코드 변경사항 커밋 및 푸시
```bash
# 변경사항 확인
git status

# 모든 변경사항 스테이징
git add .

# 또는 특정 파일만 스테이징
git add README.md pyproject.toml

# 커밋 생성
git commit -m "Add uv package management and deployment guide"

# 원격 저장소에 푸시
git push origin main

# 또는 브랜치가 master인 경우
git push origin master
```

#### 브랜치 관리
```bash
# 새 브랜치 생성 및 전환
git checkout -b feature/new-feature

# 브랜치 전환
git checkout main

# 브랜치 병합
git merge feature/new-feature

# 브랜치 삭제
git branch -d feature/new-feature
```

#### 태그 생성 및 배포
```bash
# 버전 태그 생성
git tag v1.0.0

# 태그 푸시
git push origin v1.0.0

# 모든 태그 푸시
git push origin --tags
```

## 📦 주요 의존성

### 백엔드
- **FastAPI**: 웹 API 프레임워크
- **MySQL Connector**: MySQL 데이터베이스 연결
- **cx-Oracle**: Oracle 데이터베이스 연결
- **Pandas**: 데이터 처리 및 분석
- **Plotly**: 인터랙티브 차트
- **Matplotlib/Seaborn**: 데이터 시각화

### 프론트엔드
- **Next.js**: React 프레임워크
- **Tailwind CSS**: 유틸리티 우선 CSS 프레임워크
- **shadcn/ui**: UI 컴포넌트
- **TypeScript**: 타입 안전한 JavaScript

## 🔧 개발 환경

- Python 3.13+
- uv 패키지 매니저
- MySQL/Oracle 데이터베이스 연결 설정 필요

## 📝 개발 워크플로우

1. **코드 수정**: 기능 개발 또는 버그 수정
2. **테스트**: 로컬에서 기능 테스트
3. **커밋**: `git add .` → `git commit -m "설명"`
4. **푸시**: `git push origin main`
5. **배포**: 필요시 태그 생성 및 배포

## 📝 주의사항

- `.env` 파일은 민감한 정보를 포함하므로 `.gitignore`에 추가
- 데이터베이스 연결 정보는 환경변수로 관리
- 프로덕션 배포 전 충분한 테스트 수행
