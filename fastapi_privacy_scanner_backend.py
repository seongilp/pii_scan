from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import asyncio
import uuid
from datetime import datetime
import json
import os
from enum import Enum
import logging
import sqlite3
import requests
import pymysql
import cx_Oracle
import psycopg2
from contextlib import contextmanager

# 기존 스캐너 import (실제 구현시 분리된 모듈에서 import)
# from polars_privacy_scanner import PolarsPrivacyScanner
# from oracle_privacy_scanner import OraclePrivacyScanner
# from privacy_executive_summary import PrivacyExecutiveSummary

# FastAPI 앱 생성
app = FastAPI(
    title="개인정보 스캔 API",
    description="MySQL, Oracle 데이터베이스 개인정보 패턴 스캔 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 설정
security = HTTPBearer()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 함수 (여기로 이동)
def get_db():
    # check_same_thread=False allows SQLite connections to be used across different threads
    # This is needed because FastAPI runs in a multi-threaded environment
    conn = sqlite3.connect('database_configs.db', check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

# Enum 정의
class DatabaseType(str, Enum):
    mysql = "mysql"
    oracle = "oracle"


class ScanStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class RiskLevel(str, Enum):
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"
    empty = "EMPTY"


# Pydantic 모델들
class DatabaseConfig(BaseModel):
    db_type: DatabaseType
    host: str
    port: int = Field(default=3306, description="데이터베이스 포트")
    database: Optional[str] = Field(None, description="MySQL 데이터베이스명")
    service_name: Optional[str] = Field(None, description="Oracle 서비스명")
    user: str
    password: str
    sample_size: int = Field(default=100, ge=10, le=1000, description="샘플링 크기")


class ScanRequest(BaseModel):
    config: DatabaseConfig
    scan_name: Optional[str] = Field(None, description="스캔 작업명")
    include_structure_analysis: bool = Field(default=True, description="구조 분석 포함 여부")
    include_privacy_scan: bool = Field(default=True, description="개인정보 스캔 포함 여부")
    include_executive_summary: bool = Field(default=True, description="Executive Summary 포함 여부")


class ScanJobInfo(BaseModel):
    job_id: str
    scan_name: Optional[str]
    status: ScanStatus
    db_type: DatabaseType
    host: str
    database: Optional[str]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = Field(default=0, description="진행률 (0-100)")
    current_step: str = Field(default="", description="현재 진행 단계")
    error_message: Optional[str] = None


class ScanResult(BaseModel):
    job_id: str
    status: ScanStatus
    structure_analysis: Optional[Dict[str, Any]] = None
    privacy_scan_results: Optional[List[Dict[str, Any]]] = None
    executive_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time: Optional[str] = None


class ScanSummary(BaseModel):
    total_databases: int
    total_tables: int
    total_columns: int
    total_data_rows: int
    high_risk_tables: int
    medium_risk_tables: int
    low_risk_tables: int
    privacy_patterns_found: Dict[str, int]
    top_risk_tables: List[Dict[str, Any]]


# 메모리 저장소 (실제 운영시에는 Redis나 DB 사용)
scan_jobs: Dict[str, ScanJobInfo] = {}
scan_results: Dict[str, ScanResult] = {}


# 인증 함수 (간단한 예시)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # 실제 구현시에는 JWT 토큰 검증 등
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return {"user_id": "admin"}


# 스캔 작업 실행 함수들
@app.post("/scan/database-config/{config_id}", response_model=Dict[str, str])
async def start_scan_with_config(
    config_id: int,
    background_tasks: BackgroundTasks,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """데이터베이스 설정 ID로 MySQL 스캔 작업 시작"""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM database_configs WHERE id = ?', (config_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="데이터베이스 설정을 찾을 수 없습니다")

        # Ensure the db_type is MySQL
        db_type = result[2]
        if db_type != DatabaseType.mysql.value:
            raise HTTPException(status_code=400, detail="MySQL 데이터베이스 설정만 지원됩니다")

        # Parse the database configuration
        database_config = DatabaseConfig(
            db_type=db_type,
            host=result[3],
            port=result[4],
            database=result[5],
            service_name=result[6],
            user=result[7],
            password=result[8],
            sample_size=result[9]
        )

        # Create a new scan job
        job_id = str(uuid.uuid4())
        job_info = ScanJobInfo(
            job_id=job_id,
            scan_name=f"MySQL Scan for Config {config_id}",
            status=ScanStatus.pending,
            db_type=DatabaseType.mysql,
            host=database_config.host,
            database=database_config.database,
            created_at=datetime.now()
        )
        scan_jobs[job_id] = job_info

        # Start the scan in the background
        background_tasks.add_task(run_mysql_scan, job_id, database_config)

        # Update job status
        scan_jobs[job_id].status = ScanStatus.running
        scan_jobs[job_id].started_at = datetime.now()

        logger.info(f"MySQL 스캔 작업 시작: {job_id}, Config ID: {config_id}")

        return {
            "job_id": job_id,
            "message": "스캔 작업이 시작되었습니다.",
            "status_url": f"/jobs/{job_id}",
            "results_url": f"/results/{job_id}"
        }

    except (sqlite3.Error, ValueError) as e:
        logger.error(f"Error starting scan with config ID {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"스캔 작업 시작 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다")


async def run_mysql_scan(job_id: str, config: DatabaseConfig):
    """MySQL 스캔 실행"""
    try:
        # 실제 스캐너 초기화
        # scanner = PolarsPrivacyScanner(
        #     host=config.host,
        #     user=config.user,
        #     password=config.password,
        #     database=config.database,
        #     sample_size=config.sample_size
        # )

        # 진행상황 업데이트
        scan_jobs[job_id].current_step = "데이터베이스 연결 중..."
        scan_jobs[job_id].progress = 10

        await asyncio.sleep(1)  # 시뮬레이션

        # 구조 분석
        scan_jobs[job_id].current_step = "구조 분석 중..."
        scan_jobs[job_id].progress = 30

        # structure_analysis = scanner.preview_all_databases()
        structure_analysis = {"simulated": "structure_data"}  # 시뮬레이션

        await asyncio.sleep(2)

        # 개인정보 스캔
        scan_jobs[job_id].current_step = "개인정보 패턴 스캔 중..."
        scan_jobs[job_id].progress = 70

        # privacy_results = scanner.scan_all_databases()
        privacy_results = [{"simulated": "privacy_data"}]  # 시뮬레이션

        await asyncio.sleep(2)

        # Executive Summary 생성
        scan_jobs[job_id].current_step = "Executive Summary 생성 중..."
        scan_jobs[job_id].progress = 90

        executive_summary = {"simulated": "executive_summary"}  # 시뮬레이션

        # 결과 저장
        scan_results[job_id] = ScanResult(
            job_id=job_id,
            status=ScanStatus.completed,
            structure_analysis=structure_analysis,
            privacy_scan_results=privacy_results,
            executive_summary=executive_summary,
            created_at=scan_jobs[job_id].created_at,
            completed_at=datetime.now(),
            processing_time="00:00:05"  # 시뮬레이션
        )

        # 작업 완료 처리
        scan_jobs[job_id].status = ScanStatus.completed
        scan_jobs[job_id].completed_at = datetime.now()
        scan_jobs[job_id].progress = 100
        scan_jobs[job_id].current_step = "완료"

        logger.info(f"MySQL 스캔 완료: {job_id}")

    except Exception as e:
        logger.error(f"MySQL 스캔 실패: {job_id}, 오류: {str(e)}")
        scan_jobs[job_id].status = ScanStatus.failed
        scan_jobs[job_id].error_message = str(e)


async def run_oracle_scan(job_id: str, config: DatabaseConfig):
    """Oracle 스캔 실행"""
    try:
        # 실제 스캐너 초기화
        # scanner = OraclePrivacyScanner(
        #     host=config.host,
        #     port=config.port,
        #     service_name=config.service_name,
        #     user=config.user,
        #     password=config.password,
        #     sample_size=config.sample_size
        # )

        scan_jobs[job_id].current_step = "Oracle 서버 연결 중..."
        scan_jobs[job_id].progress = 10

        await asyncio.sleep(1)

        # 구조 분석
        scan_jobs[job_id].current_step = "스키마 구조 분석 중..."
        scan_jobs[job_id].progress = 30

        structure_analysis = {"simulated": "oracle_structure_data"}

        await asyncio.sleep(3)

        # 개인정보 스캔
        scan_jobs[job_id].current_step = "스키마별 개인정보 스캔 중..."
        scan_jobs[job_id].progress = 70

        privacy_results = [{"simulated": "oracle_privacy_data"}]

        await asyncio.sleep(3)

        # Executive Summary
        scan_jobs[job_id].current_step = "Executive Summary 생성 중..."
        scan_jobs[job_id].progress = 90

        executive_summary = {"simulated": "oracle_executive_summary"}

        # 결과 저장
        scan_results[job_id] = ScanResult(
            job_id=job_id,
            status=ScanStatus.completed,
            structure_analysis=structure_analysis,
            privacy_scan_results=privacy_results,
            executive_summary=executive_summary,
            created_at=scan_jobs[job_id].created_at,
            completed_at=datetime.now(),
            processing_time="00:00:07"
        )

        scan_jobs[job_id].status = ScanStatus.completed
        scan_jobs[job_id].completed_at = datetime.now()
        scan_jobs[job_id].progress = 100
        scan_jobs[job_id].current_step = "완료"

        logger.info(f"Oracle 스캔 완료: {job_id}")

    except Exception as e:
        logger.error(f"Oracle 스캔 실패: {job_id}, 오류: {str(e)}")
        scan_jobs[job_id].status = ScanStatus.failed
        scan_jobs[job_id].error_message = str(e)


# 애플리케이션 시작 시 DB 초기화
def init_db():
    conn = sqlite3.connect('database_configs.db')
    c = conn.cursor()

    # 데이터베이스 설정 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS database_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            db_type TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            database TEXT,
            service_name TEXT,
            user TEXT NOT NULL,
            password TEXT NOT NULL,
            sample_size INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# 애플리케이션 시작 시 DB 초기화
init_db()

# Pydantic 모델 수정
class DatabaseConfigCreate(DatabaseConfig):
    name: str = Field(..., description="설정 이름")

class DatabaseConfigResponse(DatabaseConfigCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# API 엔드포인트들

@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "message": "개인정보 스캔 API 서비스",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "scan": "/scan",
            "jobs": "/jobs",
            "results": "/results"
        }
    }


@app.post("/scan", response_model=Dict[str, str])
async def start_scan(
        request: ScanRequest,
        background_tasks: BackgroundTasks,
        current_user: dict = Depends(get_current_user)
):
    """개인정보 스캔 작업 시작"""
    job_id = str(uuid.uuid4())

    # 작업 정보 생성
    job_info = ScanJobInfo(
        job_id=job_id,
        scan_name=request.scan_name,
        status=ScanStatus.pending,
        db_type=request.config.db_type,
        host=request.config.host,
        database=request.config.database or request.config.service_name,
        created_at=datetime.now()
    )

    scan_jobs[job_id] = job_info

    # 백그라운드 작업 시작
    if request.config.db_type == DatabaseType.mysql:
        background_tasks.add_task(run_mysql_scan, job_id, request.config)
    elif request.config.db_type == DatabaseType.oracle:
        background_tasks.add_task(run_oracle_scan, job_id, request.config)

    # 작업 시작 시간 업데이트
    scan_jobs[job_id].status = ScanStatus.running
    scan_jobs[job_id].started_at = datetime.now()

    logger.info(f"스캔 작업 시작: {job_id}, DB: {request.config.db_type}, Host: {request.config.host}")

    return {
        "job_id": job_id,
        "message": "스캔 작업이 시작되었습니다.",
        "status_url": f"/jobs/{job_id}",
        "results_url": f"/results/{job_id}"
    }


@app.get("/jobs", response_model=List[ScanJobInfo])
async def list_jobs(current_user: dict = Depends(get_current_user)):
    """모든 스캔 작업 목록 조회"""
    return list(scan_jobs.values())


@app.get("/jobs/{job_id}", response_model=ScanJobInfo)
async def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """특정 스캔 작업 상태 조회"""
    if job_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    return scan_jobs[job_id]


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, current_user: dict = Depends(get_current_user)):
    """스캔 작업 취소 (실행 중인 경우만)"""
    if job_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    job = scan_jobs[job_id]
    if job.status == ScanStatus.running:
        job.status = ScanStatus.failed
        job.error_message = "사용자에 의해 취소됨"
        return {"message": "작업이 취소되었습니다."}

    return {"message": "취소할 수 없는 상태입니다.", "status": job.status}


@app.get("/results/{job_id}", response_model=ScanResult)
async def get_scan_results(job_id: str, current_user: dict = Depends(get_current_user)):
    """스캔 결과 조회"""
    if job_id not in scan_results:
        if job_id in scan_jobs:
            job = scan_jobs[job_id]
            if job.status == ScanStatus.running:
                raise HTTPException(status_code=202, detail="스캔이 진행 중입니다.")
            elif job.status == ScanStatus.failed:
                raise HTTPException(status_code=400, detail=f"스캔 실패: {job.error_message}")
            else:
                raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")
        else:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    return scan_results[job_id]


@app.get("/results/{job_id}/summary", response_model=ScanSummary)
async def get_scan_summary(job_id: str, current_user: dict = Depends(get_current_user)):
    """스캔 결과 요약 조회"""
    if job_id not in scan_results:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")

    result = scan_results[job_id]

    # 실제 구현시에는 결과 데이터에서 요약 생성
    summary = ScanSummary(
        total_databases=1,
        total_tables=72,
        total_columns=245,
        total_data_rows=4078,
        high_risk_tables=1,
        medium_risk_tables=2,
        low_risk_tables=15,
        privacy_patterns_found={
            "email": 23,
            "phone": 99,
            "ssn": 1,
            "card_number": 5,
            "account_number": 12
        },
        top_risk_tables=[
            {
                "table": "T2_USERS",
                "risk_level": "HIGH",
                "privacy_score": 15,
                "patterns": ["email", "ssn"]
            }
        ]
    )

    return summary


@app.get("/results/{job_id}/download")
async def download_results(
        job_id: str,
        format: str = "json",
        current_user: dict = Depends(get_current_user)
):
    """스캔 결과 파일 다운로드"""
    if job_id not in scan_results:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")

    result = scan_results[job_id]

    if format == "json":
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=result.dict(),
            headers={"Content-Disposition": f"attachment; filename=scan_results_{job_id}.json"}
        )
    elif format == "txt":
        # Executive Summary 텍스트 형태
        from fastapi.responses import PlainTextResponse
        summary_text = "개인정보 스캔 결과 요약\n" + "=" * 50 + "\n..."
        return PlainTextResponse(
            content=summary_text,
            headers={"Content-Disposition": f"attachment; filename=executive_summary_{job_id}.txt"}
        )
    else:
        raise HTTPException(status_code=400, detail="지원되지 않는 형식입니다. (json, txt)")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len([j for j in scan_jobs.values() if j.status == ScanStatus.running]),
        "total_jobs": len(scan_jobs),
        "completed_jobs": len([j for j in scan_jobs.values() if j.status == ScanStatus.completed])
    }


@app.get("/stats")
async def get_statistics(current_user: dict = Depends(get_current_user)):
    """전체 통계"""
    total_jobs = len(scan_jobs)
    completed_jobs = len([j for j in scan_jobs.values() if j.status == ScanStatus.completed])
    failed_jobs = len([j for j in scan_jobs.values() if j.status == ScanStatus.failed])
    running_jobs = len([j for j in scan_jobs.values() if j.status == ScanStatus.running])

    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "running_jobs": running_jobs,
        "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
        "database_types": {
            "mysql": len([j for j in scan_jobs.values() if j.db_type == DatabaseType.mysql]),
            "oracle": len([j for j in scan_jobs.values() if j.db_type == DatabaseType.oracle])
        }
    }


# API 엔드포인트 추가
@app.post("/database-configs", response_model=DatabaseConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_database_config(
    config: DatabaseConfigCreate,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """데이터베이스 설정 저장"""
    try:
        cursor = conn.cursor()

        # Ensure db_type is a valid enum value
        if config.db_type not in [e.value for e in DatabaseType]:
            raise ValueError(f"Invalid database type: {config.db_type}")

        # 설정 저장
        cursor.execute('''
            INSERT INTO database_configs 
            (name, db_type, host, port, database, service_name, user, password, sample_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            config.name,
            config.db_type,
            config.host,
            config.port,
            config.database,
            config.service_name,
            config.user,
            config.password,
            config.sample_size
        ))

        conn.commit()
        config_id = cursor.lastrowid

        # 저장된 설정 조회
        cursor.execute('''
            SELECT * FROM database_configs WHERE id = ?
        ''', (config_id,))

        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="생성된 설정을 찾을 수 없습니다")

        # Handle potential None values for optional fields
        database = result[5] if result[5] is not None else None
        service_name = result[6] if result[6] is not None else None

        # Parse datetime strings safely
        try:
            created_at = datetime.strptime(result[10], '%Y-%m-%d %H:%M:%S')
            updated_at = datetime.strptime(result[11], '%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            logger.error(f"Error parsing datetime: {e}")
            raise ValueError(f"Invalid datetime format: {e}")

        return DatabaseConfigResponse(
            id=result[0],
            name=result[1],
            db_type=result[2],
            host=result[3],
            port=result[4],
            database=database,
            service_name=service_name,
            user=result[7],
            password=result[8],
            sample_size=result[9],
            created_at=created_at,
            updated_at=updated_at
        )
    except (sqlite3.Error, ValueError, TypeError, IndexError) as e:
        logger.error(f"Error creating database config: {e}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 설정 생성 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다")

@app.get("/database-configs", response_model=List[DatabaseConfigResponse])
async def list_database_configs(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """저장된 데이터베이스 설정 목록 조회"""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM database_configs ORDER BY created_at DESC')

        configs = []
        for row in cursor.fetchall():
            # Ensure db_type is a valid enum value
            db_type = row[2]
            if db_type not in [e.value for e in DatabaseType]:
                logger.warning(f"Skipping config with invalid database type: {db_type}")
                continue

            # Handle potential None values for optional fields
            database = row[5] if row[5] is not None else None
            service_name = row[6] if row[6] is not None else None

            # Parse datetime strings safely
            try:
                created_at = datetime.strptime(row[10], '%Y-%m-%d %H:%M:%S')
                updated_at = datetime.strptime(row[11], '%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                logger.warning(f"Skipping config with invalid datetime format: {e}")
                continue

            configs.append(DatabaseConfigResponse(
                id=row[0],
                name=row[1],
                db_type=db_type,
                host=row[3],
                port=row[4],
                database=database,
                service_name=service_name,
                user=row[7],
                password=row[8],
                sample_size=row[9],
                created_at=created_at,
                updated_at=updated_at
            ))

        return configs
    except sqlite3.Error as e:
        logger.error(f"Error listing database configs: {e}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 설정 목록 조회 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다")

@app.get("/database-configs/{config_id}", response_model=DatabaseConfigResponse)
async def get_database_config(
    config_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """특정 데이터베이스 설정 조회"""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM database_configs WHERE id = ?', (config_id,))

        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다")

        # Ensure db_type is a valid enum value
        db_type = result[2]
        if db_type not in [e.value for e in DatabaseType]:
            raise ValueError(f"Invalid database type: {db_type}")

        # Handle potential None values for optional fields
        database = result[5] if result[5] is not None else None
        service_name = result[6] if result[6] is not None else None

        # Parse datetime strings safely
        try:
            created_at = datetime.strptime(result[10], '%Y-%m-%d %H:%M:%S')
            updated_at = datetime.strptime(result[11], '%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            logger.error(f"Error parsing datetime: {e}")
            raise ValueError(f"Invalid datetime format: {e}")

        return DatabaseConfigResponse(
            id=result[0],
            name=result[1],
            db_type=db_type,
            host=result[3],
            port=result[4],
            database=database,
            service_name=service_name,
            user=result[7],
            password=result[8],
            sample_size=result[9],
            created_at=created_at,
            updated_at=updated_at
        )
    except (sqlite3.Error, ValueError, TypeError, IndexError) as e:
        logger.error(f"Error retrieving database config: {e}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 설정 조회 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다")

@app.put("/database-configs/{config_id}", response_model=DatabaseConfigResponse)
async def update_database_config(
    config_id: int,
    config: DatabaseConfigCreate,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """데이터베이스 설정 수정"""
    try:
        cursor = conn.cursor()

        # 설정 존재 확인
        cursor.execute('SELECT id FROM database_configs WHERE id = ?', (config_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다")

        # Ensure db_type is a valid enum value
        if config.db_type not in [e.value for e in DatabaseType]:
            raise ValueError(f"Invalid database type: {config.db_type}")

        # 설정 업데이트
        cursor.execute('''
            UPDATE database_configs 
            SET name = ?, db_type = ?, host = ?, port = ?, database = ?, 
                service_name = ?, user = ?, password = ?, sample_size = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            config.name,
            config.db_type,
            config.host,
            config.port,
            config.database,
            config.service_name,
            config.user,
            config.password,
            config.sample_size,
            config_id
        ))

        conn.commit()

        # 업데이트된 설정 조회
        cursor.execute('SELECT * FROM database_configs WHERE id = ?', (config_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="업데이트된 설정을 찾을 수 없습니다")

        # Handle potential None values for optional fields
        database = result[5] if result[5] is not None else None
        service_name = result[6] if result[6] is not None else None

        # Parse datetime strings safely
        try:
            created_at = datetime.strptime(result[10], '%Y-%m-%d %H:%M:%S')
            updated_at = datetime.strptime(result[11], '%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            logger.error(f"Error parsing datetime: {e}")
            raise ValueError(f"Invalid datetime format: {e}")

        return DatabaseConfigResponse(
            id=result[0],
            name=result[1],
            db_type=result[2],
            host=result[3],
            port=result[4],
            database=database,
            service_name=service_name,
            user=result[7],
            password=result[8],
            sample_size=result[9],
            created_at=created_at,
            updated_at=updated_at
        )
    except (sqlite3.Error, ValueError, TypeError, IndexError) as e:
        logger.error(f"Error updating database config: {e}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 설정 수정 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다")

@app.delete("/database-configs/{config_id}")
async def delete_database_config(
    config_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """데이터베이스 설정 삭제"""
    try:
        cursor = conn.cursor()

        # 설정 존재 확인
        cursor.execute('SELECT id FROM database_configs WHERE id = ?', (config_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다")

        # 설정 삭제
        cursor.execute('DELETE FROM database_configs WHERE id = ?', (config_id,))
        conn.commit()

        return {"message": "설정이 삭제되었습니다"}
    except sqlite3.Error as e:
        logger.error(f"Error deleting database config: {e}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 설정 삭제 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다")


# 새로운 API 엔드포인트들 추가

# 데이터베이스 연결 테스트 API
@app.post("/test-connection")
async def test_database_connection(
    config: DatabaseConfig,
    current_user: dict = Depends(get_current_user)
):
    """데이터베이스 연결 테스트"""
    try:
        if config.db_type == DatabaseType.mysql:
            return await test_mysql_connection(config)
        elif config.db_type == DatabaseType.oracle:
            return await test_oracle_connection(config)
        else:
            raise HTTPException(status_code=400, detail="지원되지 않는 데이터베이스 유형입니다")
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "message": f"연결 실패: {str(e)}",
            "details": str(e)
        }

async def test_mysql_connection(config: DatabaseConfig):
    """MySQL 연결 테스트"""
    try:
        import pymysql
        
        connection = pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            connect_timeout=10
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            
        connection.close()
        
        return {
            "success": True,
            "message": "MySQL 연결 성공",
            "database_info": {
                "version": version[0] if version else "Unknown",
                "host": config.host,
                "port": config.port,
                "database": config.database
            }
        }
    except Exception as e:
        raise Exception(f"MySQL 연결 실패: {str(e)}")

async def test_oracle_connection(config: DatabaseConfig):
    """Oracle 연결 테스트"""
    try:
        import cx_Oracle
        
        dsn = cx_Oracle.makedsn(config.host, config.port, service_name=config.service_name)
        connection = cx_Oracle.connect(
            user=config.user,
            password=config.password,
            dsn=dsn
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM v$version WHERE ROWNUM = 1")
            version = cursor.fetchone()
            
        connection.close()
        
        return {
            "success": True,
            "message": "Oracle 연결 성공",
            "database_info": {
                "version": version[0] if version else "Unknown",
                "host": config.host,
                "port": config.port,
                "service_name": config.service_name
            }
        }
    except Exception as e:
        raise Exception(f"Oracle 연결 실패: {str(e)}")

# 개인정보 패턴 관리 API
class PrivacyPattern(BaseModel):
    id: Optional[int] = None
    name: str
    category: str
    pattern: str
    risk_level: RiskLevel
    description: str
    examples: List[str]
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# 메모리 저장소 (실제로는 DB 사용)
privacy_patterns: Dict[int, PrivacyPattern] = {}
pattern_counter = 1

@app.get("/patterns", response_model=List[PrivacyPattern])
async def list_privacy_patterns(
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """개인정보 패턴 목록 조회"""
    patterns = list(privacy_patterns.values())
    
    # 필터링
    if category and category != "전체":
        patterns = [p for p in patterns if p.category == category]
    
    if risk_level and risk_level != "전체":
        patterns = [p for p in patterns if p.risk_level.value == risk_level]
    
    if search:
        patterns = [p for p in patterns if search.lower() in p.name.lower() or search.lower() in p.description.lower()]
    
    return patterns

@app.post("/patterns", response_model=PrivacyPattern)
async def create_privacy_pattern(
    pattern: PrivacyPattern,
    current_user: dict = Depends(get_current_user)
):
    """개인정보 패턴 생성"""
    global pattern_counter
    
    pattern.id = pattern_counter
    pattern.created_at = datetime.now()
    pattern.updated_at = datetime.now()
    
    privacy_patterns[pattern_counter] = pattern
    pattern_counter += 1
    
    return pattern

@app.put("/patterns/{pattern_id}", response_model=PrivacyPattern)
async def update_privacy_pattern(
    pattern_id: int,
    pattern: PrivacyPattern,
    current_user: dict = Depends(get_current_user)
):
    """개인정보 패턴 수정"""
    if pattern_id not in privacy_patterns:
        raise HTTPException(status_code=404, detail="패턴을 찾을 수 없습니다")
    
    pattern.id = pattern_id
    pattern.updated_at = datetime.now()
    privacy_patterns[pattern_id] = pattern
    
    return pattern

@app.delete("/patterns/{pattern_id}")
async def delete_privacy_pattern(
    pattern_id: int,
    current_user: dict = Depends(get_current_user)
):
    """개인정보 패턴 삭제"""
    if pattern_id not in privacy_patterns:
        raise HTTPException(status_code=404, detail="패턴을 찾을 수 없습니다")
    
    del privacy_patterns[pattern_id]
    return {"message": "패턴이 삭제되었습니다"}

# 기본 패턴 초기화
def init_default_patterns():
    """기본 개인정보 패턴 초기화"""
    default_patterns = [
        PrivacyPattern(
            name="이메일 주소",
            category="연락처",
            pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            risk_level=RiskLevel.medium,
            description="일반적인 이메일 주소 형식을 감지합니다",
            examples=["user@example.com", "test.email@domain.co.kr"],
            created_at=datetime.now()
        ),
        PrivacyPattern(
            name="전화번호",
            category="연락처",
            pattern=r"(\+82|0)[0-9]{1,2}-?[0-9]{3,4}-?[0-9]{4}",
            risk_level=RiskLevel.medium,
            description="한국 전화번호 형식을 감지합니다",
            examples=["010-1234-5678", "+82-10-1234-5678"],
            created_at=datetime.now()
        ),
        PrivacyPattern(
            name="주민등록번호",
            category="신원정보",
            pattern=r"[0-9]{6}-[1-4][0-9]{6}",
            risk_level=RiskLevel.high,
            description="한국 주민등록번호 형식을 감지합니다",
            examples=["123456-1234567", "123456-2345678"],
            created_at=datetime.now()
        ),
        PrivacyPattern(
            name="신용카드번호",
            category="금융정보",
            pattern=r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
            risk_level=RiskLevel.high,
            description="Visa, MasterCard, American Express 등 신용카드 번호를 감지합니다",
            examples=["4111-1111-1111-1111", "5555-5555-5555-4444"],
            created_at=datetime.now()
        ),
        PrivacyPattern(
            name="계좌번호",
            category="금융정보",
            pattern=r"\b[0-9]{10,14}\b",
            risk_level=RiskLevel.medium,
            description="은행 계좌번호 형식을 감지합니다",
            examples=["123-456789-01-234", "123456789012"],
            created_at=datetime.now()
        )
    ]
    
    for i, pattern in enumerate(default_patterns, 1):
        pattern.id = i
        privacy_patterns[i] = pattern

# 통계 분석 API
@app.get("/analytics/overview")
async def get_analytics_overview(current_user: dict = Depends(get_current_user)):
    """전체 통계 개요"""
    total_jobs = len(scan_jobs)
    completed_jobs = len([j for j in scan_jobs.values() if j.status == ScanStatus.completed])
    failed_jobs = len([j for j in scan_jobs.values() if j.status == ScanStatus.failed])
    running_jobs = len([j for j in scan_jobs.values() if j.status == ScanStatus.running])
    
    # 데이터베이스 유형별 통계
    db_stats = {}
    for job in scan_jobs.values():
        db_type = job.db_type.value
        if db_type not in db_stats:
            db_stats[db_type] = {"total": 0, "completed": 0, "failed": 0}
        db_stats[db_type]["total"] += 1
        if job.status == ScanStatus.completed:
            db_stats[db_type]["completed"] += 1
        elif job.status == ScanStatus.failed:
            db_stats[db_type]["failed"] += 1
    
    # 월별 통계 (최근 6개월)
    monthly_stats = {}
    for job in scan_jobs.values():
        month_key = job.created_at.strftime("%Y-%m")
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {"total": 0, "completed": 0, "failed": 0}
        monthly_stats[month_key]["total"] += 1
        if job.status == ScanStatus.completed:
            monthly_stats[month_key]["completed"] += 1
        elif job.status == ScanStatus.failed:
            monthly_stats[month_key]["failed"] += 1
    
    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "running_jobs": running_jobs,
        "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
        "database_stats": db_stats,
        "monthly_stats": monthly_stats,
        "active_patterns": len([p for p in privacy_patterns.values() if p.is_active]),
        "total_patterns": len(privacy_patterns)
    }

@app.get("/analytics/patterns")
async def get_pattern_analytics(current_user: dict = Depends(get_current_user)):
    """패턴별 통계"""
    pattern_stats = {}
    
    # 각 패턴별 감지 횟수 계산 (실제로는 스캔 결과에서 계산)
    for pattern in privacy_patterns.values():
        pattern_stats[pattern.name] = {
            "category": pattern.category,
            "risk_level": pattern.risk_level.value,
            "detection_count": 0,  # 실제 구현시 스캔 결과에서 계산
            "is_active": pattern.is_active
        }
    
    return {
        "patterns": pattern_stats,
        "categories": list(set(p.category for p in privacy_patterns.values())),
        "risk_levels": [level.value for level in RiskLevel]
    }

# 설정 관리 API
class AppSettings(BaseModel):
    backend_url: str = "http://localhost:8000"
    api_version: str = "v1"
    api_token: str = "your-secret-token"
    connection_timeout: int = 30
    auto_reconnect: bool = True
    scan_endpoint: str = "/scan"
    jobs_endpoint: str = "/jobs"
    results_endpoint: str = "/results"
    config_endpoint: str = "/database-configs"
    health_endpoint: str = "/health"

# 메모리 저장소 (실제로는 DB 사용)
app_settings = AppSettings()

@app.get("/settings")
async def get_app_settings(current_user: dict = Depends(get_current_user)):
    """앱 설정 조회"""
    return app_settings

@app.put("/settings")
async def update_app_settings(
    settings: AppSettings,
    current_user: dict = Depends(get_current_user)
):
    """앱 설정 업데이트"""
    global app_settings
    app_settings = settings
    return {"message": "설정이 업데이트되었습니다"}

# 대시보드 API
@app.get("/dashboard")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """대시보드 데이터"""
    total_jobs = len(scan_jobs)
    completed_jobs = len([j for j in scan_jobs.values() if j.status == ScanStatus.completed])
    running_jobs = len([j for j in scan_jobs.values() if j.status == ScanStatus.running])
    
    # 최근 스캔 작업 (최근 5개)
    recent_jobs = []
    for job in sorted(scan_jobs.values(), key=lambda x: x.created_at, reverse=True)[:5]:
        recent_jobs.append({
            "id": job.job_id,
            "name": job.scan_name or f"{job.db_type.value} Scan",
            "status": job.status.value,
            "database": job.db_type.value,
            "host": job.host,
            "created_at": job.created_at.isoformat(),
            "progress": job.progress
        })
    
    # 개인정보 패턴 분포 (더미 데이터)
    pattern_distribution = {
        "이메일 주소": 156,
        "전화번호": 89,
        "주민등록번호": 23,
        "신용카드번호": 12,
        "계좌번호": 67
    }
    
    return {
        "stats": {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "running_jobs": running_jobs,
            "high_risk_patterns": 12
        },
        "recent_jobs": recent_jobs,
        "pattern_distribution": pattern_distribution
    }

# 스캔 작업 일괄 관리 API
@app.post("/jobs/batch")
async def batch_job_operations(
    job_ids: List[str],
    operation: str,  # "cancel", "delete", "retry"
    current_user: dict = Depends(get_current_user)
):
    """스캔 작업 일괄 관리"""
    results = []
    
    for job_id in job_ids:
        if job_id not in scan_jobs:
            results.append({"job_id": job_id, "success": False, "message": "작업을 찾을 수 없습니다"})
            continue
        
        try:
            if operation == "cancel":
                job = scan_jobs[job_id]
                if job.status == ScanStatus.running:
                    job.status = ScanStatus.failed
                    job.error_message = "사용자에 의해 취소됨"
                    results.append({"job_id": job_id, "success": True, "message": "작업이 취소되었습니다"})
                else:
                    results.append({"job_id": job_id, "success": False, "message": "취소할 수 없는 상태입니다"})
            
            elif operation == "delete":
                del scan_jobs[job_id]
                if job_id in scan_results:
                    del scan_results[job_id]
                results.append({"job_id": job_id, "success": True, "message": "작업이 삭제되었습니다"})
            
            elif operation == "retry":
                # 재시도 로직 (실제 구현 필요)
                results.append({"job_id": job_id, "success": True, "message": "재시도 요청이 등록되었습니다"})
            
        except Exception as e:
            results.append({"job_id": job_id, "success": False, "message": str(e)})
    
    return {"results": results}

# 초기화 함수 호출
init_default_patterns()

# 실행 설정
if __name__ == "__main__":
    import uvicorn

    # 개발 환경에서 실행
    uvicorn.run(
        "fastapi_privacy_scanner_backend:app",
        host="0.0.0.0",
        port=18000,
        reload=True,
        log_level="debug"
    )
else:
    # 프로덕션 환경에서 실행 (uvicorn이 자동으로 처리)
    pass
