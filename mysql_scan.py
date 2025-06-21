import mysql.connector
import polars as pl
import re
import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import warnings
import logging
import concurrent.futures
from functools import partial
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import os
from dotenv import load_dotenv

warnings.filterwarnings('ignore')


class PrivacyScannerLogger:
    def __init__(self, log_level: str = "INFO"):
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('privacy_scanner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)


class PolarsPrivacyScanner:
    def __init__(self, host: str, user: str, password: str = None, database: str = None, sample_size: int = 100, port: int = 3306):
        """
        Polars 기반 개인정보 스캐너

        Args:
            host: MySQL 서버 호스트
            user: 사용자명
            password: 비밀번호 (선택사항 - 비밀번호 없이도 접속 가능)
            database: 데이터베이스명
            sample_size: 샘플링할 행 수
            port: MySQL 포트 (기본값: 3306)
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None
        self.sample_size = sample_size

        # 시스템 스키마 제외 목록 (포괄적)
        self.system_schemas = {
            # MySQL 기본 시스템 스키마
            'information_schema',
            'performance_schema', 
            'mysql',
            'sys',
            
            # MySQL 8.0+ 추가 시스템 스키마
            'ndbinfo',
        }

        # 개인정보 패턴 정의 - 한국 형식으로 업데이트
        self.privacy_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\d{2,3}-\d{3,4}-\d{4}|\d{10,11})',
            'ssn': r'\d{6}-[1-4]\d{6}',  # 한국 주민등록번호 형식
            'card_number': r'5327-\d{4}-\d{4}-\d{4}',  # 5327로 시작하는 16자리 카드번호
            'account_number': r'1000-\d{8}',  # 1000으로 시작하는 12자리 계좌번호
        }

        # 개인정보 관련 컬럼명 키워드
        self.privacy_keywords = [
            'name', 'email', 'phone', 'mobile', 'tel', 'address', 'addr',
            'ssn', 'social', 'birth', 'birthday', 'card', 'account',
            'user_id', 'customer', '고객', 'personal', '개인'
        ]

        print(f"🚀 Polars 기반 개인정보 스캐너 초기화 (샘플: {sample_size}건)")

    def validate_config(self) -> bool:
        """설정 유효성 검사"""
        issues = []
        
        if not self.host:
            issues.append("호스트가 설정되지 않았습니다")
        
        if not self.user:
            issues.append("사용자명이 설정되지 않았습니다")
        
        # 비밀번호 검증 제거 - 비밀번호 없이도 접속 가능
        # if not self.password:
        #     issues.append("비밀번호가 설정되지 않았습니다")
        
        if self.sample_size <= 0:
            issues.append("샘플 크기는 0보다 커야 합니다")
        
        if self.port <= 0 or self.port > 65535:
            issues.append("포트 번호가 유효하지 않습니다")
        
        if issues:
            print("❌ 설정 오류:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        
        return True

    def test_connection(self) -> bool:
        """연결 테스트"""
        print(f"🔍 MySQL 연결 테스트 중... ({self.host}:{self.port})")
        
        try:
            # 연결 파라미터 구성
            connection_params = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'charset': 'utf8mb4',
                'connect_timeout': 10
            }
            
            # 비밀번호가 있는 경우에만 추가
            if self.password:
                connection_params['password'] = self.password
                print(f"   • 인증 방식: 사용자명 + 비밀번호")
            else:
                print(f"   • 인증 방식: 사용자명만 (비밀번호 없음)")
            
            # 연결 테스트
            test_connection = mysql.connector.connect(**connection_params)
            
            if test_connection.is_connected():
                cursor = test_connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                cursor.close()
                test_connection.close()
                
                print(f"✅ MySQL 연결 테스트 성공")
                print(f"   • 서버 버전: {version}")
                return True
            else:
                print("❌ MySQL 연결 테스트 실패")
                return False
                
        except mysql.connector.Error as err:
            error_code = err.errno if hasattr(err, 'errno') else 'Unknown'
            print(f"❌ MySQL 연결 테스트 실패 (에러 코드: {error_code})")
            
            if error_code == 2003:
                print("   • MySQL 서버가 실행되지 않았거나 호스트/포트가 잘못되었습니다")
                print("   • 해결방법: sudo systemctl start mysql")
            elif error_code == 1045:
                print("   • 사용자명 또는 비밀번호가 잘못되었습니다")
                if not self.password:
                    print("   • 비밀번호 없이 접속을 시도했지만 실패했습니다")
                    print("   • 해결방법: 올바른 비밀번호를 설정하거나 MySQL 사용자 권한을 확인하세요")
                else:
                    print("   • 해결방법: MySQL 사용자 계정을 확인하세요")
            elif error_code == 1049:
                print("   • 지정된 데이터베이스가 존재하지 않습니다")
            elif error_code == 2013:
                print("   • 연결 시간 초과 - 네트워크 문제일 수 있습니다")
            else:
                print(f"   • 오류 메시지: {err}")
            
            return False

    def connect(self):
        """MySQL 연결"""
        # 설정 검증
        if not self.validate_config():
            return False
        
        # 연결 테스트
        if not self.test_connection():
            return False
        
        try:
            print(f"🔗 MySQL에 연결 중... ({self.host}:{self.port})")
            
            # 연결 파라미터 구성
            connection_params = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'charset': 'utf8mb4',
                'autocommit': True,
                'connect_timeout': 30,
                'read_timeout': 60,
                'write_timeout': 60
            }
            
            # 비밀번호가 있는 경우에만 추가
            if self.password:
                connection_params['password'] = self.password
            
            # 데이터베이스가 지정된 경우 추가
            if self.database:
                connection_params['database'] = self.database
            
            self.connection = mysql.connector.connect(**connection_params)
            
            if self.connection.is_connected():
                print(f"✅ MySQL 연결 성공: {self.host}:{self.port}")
                
                # 연결 정보 출력
                cursor = self.connection.cursor()
                cursor.execute("SELECT DATABASE()")
                current_db = cursor.fetchone()[0]
                cursor.close()
                
                if current_db:
                    print(f"   • 현재 데이터베이스: {current_db}")
                else:
                    print(f"   • 데이터베이스 미선택 (전체 스캔 모드)")
                
                return True
            else:
                print("❌ MySQL 연결 실패")
                return False
                
        except mysql.connector.Error as err:
            print(f"❌ MySQL 연결 실패: {err}")
            return False
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return False

    def disconnect(self):
        """MySQL 연결 해제"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔐 MySQL 연결 해제")
        else:
            print("ℹ️  이미 연결이 해제되었습니다")

    def get_databases(self) -> List[str]:
        """모든 데이터베이스 목록 조회"""
        if not self.connection or not self.connection.is_connected():
            print("❌ MySQL 연결이 없습니다")
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            cursor.close()
            return databases
        except mysql.connector.Error as err:
            print(f"❌ 데이터베이스 목록 조회 실패: {err}")
            return []

    def get_tables(self, database: str) -> List[str]:
        """특정 데이터베이스의 테이블 목록 조회"""
        cursor = self.connection.cursor()
        cursor.execute(f"USE {database}")
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        return tables

    def get_table_info(self, database: str, table: str) -> Dict:
        """테이블 정보 조회 (행 수, 컬럼 정보)"""
        cursor = self.connection.cursor()
        cursor.execute(f"USE {database}")

        # 행 수 조회
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        total_rows = cursor.fetchone()[0]

        # 컬럼 정보 조회
        cursor.execute(f"DESCRIBE {table}")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'null': row[2],
                'key': row[3],
                'default': row[4],
                'extra': row[5]
            })

        cursor.close()
        return {
            'total_rows': total_rows,
            'columns': columns
        }

    def estimate_dataframe_size(self, columns: List[Dict], sample_rows: int) -> Dict:
        """DataFrame 예상 크기 계산"""
        size_estimates = {
            'int': 8, 'bigint': 8, 'smallint': 4, 'tinyint': 1,
            'float': 8, 'double': 8, 'decimal': 16,
            'varchar': 50, 'text': 200, 'longtext': 1000,
            'char': 20, 'date': 8, 'datetime': 8, 'timestamp': 8,
            'json': 100, 'blob': 500, 'binary': 50
        }

        total_bytes_per_row = 0
        text_columns = 0
        numeric_columns = 0
        date_columns = 0

        for col in columns:
            col_type = col['type'].lower()
            col_size = 8

            for type_key, size in size_estimates.items():
                if type_key in col_type:
                    col_size = size
                    break

            if 'varchar' in col_type or 'char' in col_type:
                import re
                match = re.search(r'\((\d+)\)', col_type)
                if match:
                    declared_length = int(match.group(1))
                    col_size = min(declared_length, 255)
                text_columns += 1
            elif any(t in col_type for t in ['text', 'blob', 'json']):
                text_columns += 1
            elif any(t in col_type for t in ['int', 'float', 'double', 'decimal']):
                numeric_columns += 1
            elif any(t in col_type for t in ['date', 'time', 'timestamp']):
                date_columns += 1

            total_bytes_per_row += col_size

        overhead_factor = 1.3
        estimated_size_bytes = total_bytes_per_row * sample_rows * overhead_factor

        return {
            'total_columns': len(columns),
            'text_columns': text_columns,
            'numeric_columns': numeric_columns,
            'date_columns': date_columns,
            'estimated_bytes_per_row': int(total_bytes_per_row),
            'estimated_total_bytes': int(estimated_size_bytes),
            'estimated_mb': round(estimated_size_bytes / (1024 * 1024), 2),
            'sample_rows': sample_rows
        }

    def estimate_scan_time(self, total_rows: int, columns: int, text_columns: int,
                           estimated_mb: float, sample_rows: int) -> Dict:
        """스캔 시간 예측 (Polars 기준)"""
        base_speed_rows_per_sec = 50000
        regex_speed_factor = 0.3
        text_factor = 1 + (text_columns * 0.1)

        effective_speed = base_speed_rows_per_sec * regex_speed_factor / text_factor

        db_query_time = max(0.1, total_rows / 1000000)
        dataframe_creation_time = max(0.05, estimated_mb / 100)
        pattern_scan_time = sample_rows / effective_speed

        total_estimated_seconds = db_query_time + dataframe_creation_time + pattern_scan_time

        return {
            'engine': 'Polars',
            'db_query_time_sec': round(db_query_time, 2),
            'dataframe_creation_time_sec': round(dataframe_creation_time, 2),
            'pattern_scan_time_sec': round(pattern_scan_time, 2),
            'total_estimated_sec': round(total_estimated_seconds, 2),
            'estimated_rows_per_sec': int(effective_speed),
            'text_columns_factor': round(text_factor, 2)
        }

    def load_table_sample(self, database: str, table: str) -> Tuple[Optional[pl.DataFrame], Dict]:
        """테이블에서 샘플 데이터를 Polars DataFrame으로 로드"""
        cursor = self.connection.cursor()
        cursor.execute(f"USE {database}")

        table_info = self.get_table_info(database, table)
        total_rows = table_info['total_rows']

        if total_rows == 0:
            print(f"    ⚠️  빈 테이블")
            return None, {'method': 'empty', 'total_rows': 0, 'sampled_rows': 0}

        if total_rows <= self.sample_size:
            query = f"SELECT * FROM {table}"
            sample_method = "전체 데이터"
        else:
            query = f"SELECT * FROM {table} ORDER BY RAND() LIMIT {self.sample_size}"
            sample_method = f"랜덤 샘플링"

        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            if not rows:
                return None, {'method': 'no_data', 'total_rows': total_rows, 'sampled_rows': 0}

            df = pl.DataFrame(rows, schema=columns)

            sampling_info = {
                'method': sample_method,
                'total_rows': total_rows,
                'sampled_rows': len(rows),
                'sampling_ratio': len(rows) / total_rows if total_rows > 0 else 0
            }

            print(f"    📊 {total_rows:,}행 → {len(rows)}행 샘플링 ({sample_method})")

            return df, sampling_info

        except Exception as e:
            print(f"    ❌ 데이터 로드 오류: {str(e)}")
            return None, {'method': 'error', 'error': str(e)}
        finally:
            cursor.close()

    def is_privacy_column(self, column_name: str) -> bool:
        """컬럼명이 개인정보 관련 컬럼인지 확인"""
        column_lower = column_name.lower()
        return any(keyword in column_lower for keyword in self.privacy_keywords)

    def scan_column_patterns(self, df: pl.DataFrame, column: str) -> Dict:
        """Polars DataFrame 컬럼에서 개인정보 패턴 스캔"""
        if df is None:
            return {'error': 'DataFrame is None'}

        try:
            if column not in df.columns:
                return {'error': f'Column {column} not found'}

            col_data = df.select(pl.col(column).filter(pl.col(column).is_not_null())).to_series()
            values = [str(val) for val in col_data.to_list()]

            if not values:
                return {'privacy_matches': {}, 'total_values': 0, 'privacy_count': 0, 'privacy_ratio': 0}

            privacy_matches = {}
            privacy_rows = set()

            for idx, value in enumerate(values):
                for pattern_name, pattern in self.privacy_patterns.items():
                    matches = re.findall(pattern, value)
                    if matches:
                        if pattern_name not in privacy_matches:
                            privacy_matches[pattern_name] = 0
                        privacy_matches[pattern_name] += len(matches)
                        privacy_rows.add(idx)

            total_values = len(values)
            privacy_count = len(privacy_rows)
            privacy_ratio = privacy_count / total_values if total_values > 0 else 0

            return {
                'privacy_matches': privacy_matches,
                'total_values': total_values,
                'privacy_count': privacy_count,
                'privacy_ratio': privacy_ratio,
                'sample_values': self.mask_sample_data(values[:5])
            }

        except Exception as e:
            return {'error': str(e)}

    def mask_sample_data(self, values: List[str]) -> List[str]:
        """샘플 데이터 마스킹"""
        masked = []
        for value in values:
            value = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                           lambda m: f"{m.group(1)[:2]}***@{m.group(2)}", value)
            value = re.sub(r'(\d{2,3})-(\d{3,4})-(\d{4})', r'\1-***-\3', value)
            value = re.sub(r'(\d{6})-([1-4])(\d{6})', r'\1-\2******', value)
            value = re.sub(r'(\d{4})-(\d{4})-(\d{4})-(\d{4})', r'\1-****-****-\4', value)

            masked.append(value[:50] + "..." if len(value) > 50 else value)

        return masked

    def analyze_dataframe(self, df: pl.DataFrame, table_name: str, sampling_info: Dict) -> Dict:
        """Polars DataFrame 전체 분석"""
        if df is None:
            return {
                'table': table_name,
                'sampling_info': sampling_info,
                'columns': {},
                'privacy_score': 0,
                'risk_level': 'EMPTY' if sampling_info.get('total_rows', 0) == 0 else 'ERROR'
            }

        print(f"    🔍 DataFrame 분석 중... (Polars)")

        result = {
            'table': table_name,
            'sampling_info': sampling_info,
            'columns': {},
            'privacy_score': 0,
            'risk_level': 'LOW'
        }

        for column in df.columns:
            column_name = str(column)
            col_type = str(df[column].dtype)
            is_suspicious = self.is_privacy_column(column_name)

            column_result = {
                'type': col_type,
                'suspicious_name': is_suspicious,
                'pattern_scan': None
            }

            if any(t in col_type.lower() for t in ['string', 'utf8', 'str']):
                pattern_result = self.scan_column_patterns(df, column_name)
                column_result['pattern_scan'] = pattern_result

                if 'privacy_matches' in pattern_result and pattern_result['privacy_matches']:
                    pattern_score = len(pattern_result['privacy_matches']) * 3
                    ratio_score = int(pattern_result.get('privacy_ratio', 0) * 10)
                    column_score = pattern_score + ratio_score
                    result['privacy_score'] += column_score

                    print(f"      🚨 {column_name}: {list(pattern_result['privacy_matches'].keys())} "
                          f"(비율: {pattern_result.get('privacy_ratio', 0):.1%})")

                elif is_suspicious:
                    result['privacy_score'] += 1
                    print(f"      ⚠️  {column_name}: 의심스러운 컬럼명")

            result['columns'][column_name] = column_result

        if result['privacy_score'] >= 15:
            result['risk_level'] = 'HIGH'
        elif result['privacy_score'] >= 5:
            result['risk_level'] = 'MEDIUM'

        return result

    def scan_table(self, database: str, table: str) -> Dict:
        """테이블 스캔 (Polars 기반)"""
        print(f"  📋 테이블 스캔: {table}")

        df, sampling_info = self.load_table_sample(database, table)
        result = self.analyze_dataframe(df, table, sampling_info)

        print(f"    ✅ 완료 (위험도: {result['risk_level']}, 점수: {result['privacy_score']})")

        return result

    def analyze_database_structure(self, database: str) -> Dict:
        """데이터베이스 구조 분석 및 처리 비용 예측"""
        print(f"🔍 데이터베이스 구조 분석 중: {database}")

        analysis = {
            'database': database,
            'analysis_time': datetime.now().isoformat(),
            'engine': 'Polars',
            'sample_size': self.sample_size,
            'tables': {},
            'summary': {
                'total_tables': 0,
                'total_rows': 0,
                'total_columns': 0,
                'total_text_columns': 0,
                'estimated_total_mb': 0,
                'estimated_total_scan_time_sec': 0,
                'scannable_tables': 0,
                'empty_tables': 0,
                'large_tables': 0
            }
        }

        try:
            tables = self.get_tables(database)
            analysis['summary']['total_tables'] = len(tables)

            print(f"  📊 발견된 테이블: {len(tables)}개")

            for table in tables:
                print(f"    📋 분석 중: {table}")

                try:
                    table_info = self.get_table_info(database, table)
                    total_rows = table_info['total_rows']
                    columns = table_info['columns']

                    sample_rows = min(total_rows, self.sample_size) if total_rows > 0 else 0
                    size_estimate = self.estimate_dataframe_size(columns, sample_rows)
                    time_estimate = self.estimate_scan_time(
                        total_rows,
                        len(columns),
                        size_estimate['text_columns'],
                        size_estimate['estimated_mb'],
                        sample_rows
                    )

                    table_analysis = {
                        'total_rows': total_rows,
                        'total_columns': len(columns),
                        'columns': columns,
                        'size_estimate': size_estimate,
                        'time_estimate': time_estimate,
                        'status': 'scannable' if total_rows > 0 else 'empty'
                    }

                    analysis['tables'][table] = table_analysis

                    analysis['summary']['total_rows'] += total_rows
                    analysis['summary']['total_columns'] += len(columns)
                    analysis['summary']['total_text_columns'] += size_estimate['text_columns']
                    analysis['summary']['estimated_total_mb'] += size_estimate['estimated_mb']
                    analysis['summary']['estimated_total_scan_time_sec'] += time_estimate['total_estimated_sec']

                    if total_rows == 0:
                        analysis['summary']['empty_tables'] += 1
                    else:
                        analysis['summary']['scannable_tables'] += 1

                    if total_rows >= 1000000:
                        analysis['summary']['large_tables'] += 1

                    print(f"      ✅ {total_rows:,}행, {len(columns)}컬럼, "
                          f"~{size_estimate['estimated_mb']}MB, "
                          f"~{time_estimate['total_estimated_sec']}초")

                except Exception as e:
                    analysis['tables'][table] = {
                        'error': str(e),
                        'status': 'error'
                    }
                    print(f"      ❌ 분석 오류: {str(e)}")

        except Exception as e:
            analysis['error'] = str(e)
            print(f"❌ 데이터베이스 분석 오류: {str(e)}")

        return analysis

    def scan_database(self, database: str) -> Dict:
        """데이터베이스 전체 스캔"""
        print(f"🔍 데이터베이스 스캔 시작: {database} (Polars 엔진)")

        scan_results = {
            'database': database,
            'scan_time': datetime.now().isoformat(),
            'engine': 'Polars',
            'sample_size': self.sample_size,
            'tables': {},
            'summary': {
                'total_tables': 0,
                'scanned_tables': 0,
                'high_risk_tables': 0,
                'medium_risk_tables': 0,
                'low_risk_tables': 0,
                'total_privacy_score': 0,
                'total_data_rows': 0,
                'total_sampled_rows': 0
            }
        }

        try:
            tables = self.get_tables(database)
            scan_results['summary']['total_tables'] = len(tables)

            for table in tables:
                table_result = self.scan_table(database, table)
                scan_results['tables'][table] = table_result

                risk_level = table_result.get('risk_level', 'LOW')
                privacy_score = table_result.get('privacy_score', 0)
                sampling_info = table_result.get('sampling_info', {})

                if risk_level == 'HIGH':
                    scan_results['summary']['high_risk_tables'] += 1
                elif risk_level == 'MEDIUM':
                    scan_results['summary']['medium_risk_tables'] += 1
                elif risk_level == 'LOW':
                    scan_results['summary']['low_risk_tables'] += 1

                scan_results['summary']['scanned_tables'] += 1
                scan_results['summary']['total_privacy_score'] += privacy_score
                scan_results['summary']['total_data_rows'] += sampling_info.get('total_rows', 0)
                scan_results['summary']['total_sampled_rows'] += sampling_info.get('sampled_rows', 0)

        except Exception as e:
            scan_results['error'] = str(e)
            print(f"❌ 데이터베이스 스캔 오류: {str(e)}")

        return scan_results

    def generate_structure_report(self, analysis: Dict) -> str:
        """데이터베이스 구조 분석 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("🏗️  데이터베이스 구조 분석 및 처리 비용 예측 (Polars)")
        report.append("=" * 80)
        report.append(f"데이터베이스: {analysis['database']}")
        report.append(f"분석 시간: {analysis['analysis_time']}")
        report.append(f"처리 엔진: Polars")
        report.append(f"샘플 크기: {analysis.get('sample_size', 'Unknown')}건")
        report.append("")

        summary = analysis.get('summary', {})

        report.append("📊 전체 요약:")
        report.append(f"  • 총 테이블 수: {summary.get('total_tables', 0):,}개")
        report.append(f"  • 스캔 가능한 테이블: {summary.get('scannable_tables', 0):,}개")
        report.append(f"  • 빈 테이블: {summary.get('empty_tables', 0):,}개")
        report.append(f"  • 대용량 테이블 (100만행+): {summary.get('large_tables', 0):,}개")
        report.append(f"  • 총 데이터 행 수: {summary.get('total_rows', 0):,}행")
        report.append(f"  • 총 컬럼 수: {summary.get('total_columns', 0):,}개")
        report.append(f"  • 텍스트 컬럼 수: {summary.get('total_text_columns', 0):,}개")
        report.append("")

        estimated_mb = summary.get('estimated_total_mb', 0)
        estimated_time = summary.get('estimated_total_scan_time_sec', 0)

        report.append("💾 예상 처리 비용 (Polars 엔진):")
        report.append(f"  • 예상 DataFrame 크기: {estimated_mb:.1f} MB")
        if estimated_mb < 10:
            report.append(f"    → 메모리 사용량: 🟢 낮음")
        elif estimated_mb < 100:
            report.append(f"    → 메모리 사용량: 🟡 보통")
        else:
            report.append(f"    → 메모리 사용량: 🔴 높음")

        report.append(f"  • 예상 스캔 시간: {estimated_time:.1f}초")
        if estimated_time < 30:
            report.append(f"    → 처리 시간: 🟢 빠름")
        elif estimated_time < 300:
            report.append(f"    → 처리 시간: 🟡 보통")
        else:
            report.append(f"    → 처리 시간: 🔴 오래 걸림")

        if estimated_time > 60:
            minutes = int(estimated_time // 60)
            seconds = int(estimated_time % 60)
            report.append(f"    → 예상 시간: {minutes}분 {seconds}초")

        report.append("")

        large_tables = []
        for table_name, table_data in analysis.get('tables', {}).items():
            if table_data.get('total_rows', 0) >= 100000:
                large_tables.append({
                    'name': table_name,
                    'rows': table_data.get('total_rows', 0),
                    'columns': table_data.get('total_columns', 0),
                    'mb': table_data.get('size_estimate', {}).get('estimated_mb', 0),
                    'time': table_data.get('time_estimate', {}).get('total_estimated_sec', 0)
                })

        large_tables.sort(key=lambda x: x['rows'], reverse=True)

        if large_tables:
            report.append("📈 대용량 테이블 상위 10개:")
            for i, table in enumerate(large_tables[:10], 1):
                report.append(f"  {i:2d}. {table['name']}")
                report.append(f"      • 행 수: {table['rows']:,}")
                report.append(f"      • 컬럼 수: {table['columns']}")
                report.append(f"      • 예상 크기: {table['mb']:.1f} MB")
                report.append(f"      • 예상 시간: {table['time']:.1f}초")

            if len(large_tables) > 10:
                report.append(f"  ... 외 {len(large_tables) - 10}개")
            report.append("")

        report.append("💡 권장사항:")

        if estimated_mb > 500:
            report.append("  • 메모리 사용량이 높습니다. 샘플 크기를 줄이는 것을 고려하세요.")

        if estimated_time > 600:
            report.append("  • 처리 시간이 깁니다. 특정 테이블만 선택적으로 스캔하는 것을 고려하세요.")

        if summary.get('large_tables', 0) > 10:
            report.append("  • 대용량 테이블이 많습니다. 배치 처리를 고려하세요.")

        if summary.get('total_text_columns', 0) > summary.get('total_columns', 1) * 0.7:
            report.append("  • 텍스트 컬럼 비율이 높습니다. 정규식 처리로 인해 시간이 더 걸릴 수 있습니다.")

        report.append("  • Polars 엔진으로 최적화된 고성능 처리가 진행됩니다.")

        return "\n".join(report)

    def generate_scan_report(self, scan_results: Dict) -> str:
        """스캔 결과 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("📊 MySQL 개인정보 스캔 리포트 (Polars 엔진)")
        report.append("=" * 80)
        report.append(f"데이터베이스: {scan_results['database']}")
        report.append(f"스캔 시간: {scan_results['scan_time']}")
        report.append(f"처리 엔진: Polars")

    def generate_privacy_summary_report(self, scan_results: List[Dict]) -> str:
        """개인정보 스캔 결과 요약 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("🔍 개인정보 스캔 결과 요약 리포트")
        report.append("=" * 80)
        
        # 전체 통계
        total_databases = len(scan_results)
        total_tables = sum(r.get('summary', {}).get('total_tables', 0) for r in scan_results)
        total_high_risk = sum(r.get('summary', {}).get('high_risk_tables', 0) for r in scan_results)
        total_medium_risk = sum(r.get('summary', {}).get('medium_risk_tables', 0) for r in scan_results)
        total_score = sum(r.get('summary', {}).get('total_privacy_score', 0) for r in scan_results)
        
        report.append(f"📊 전체 스캔 통계:")
        report.append(f"  • 스캔된 데이터베이스: {total_databases}개")
        report.append(f"  • 총 테이블 수: {total_tables}개")
        report.append(f"  • 고위험 테이블: {total_high_risk}개")
        report.append(f"  • 중간위험 테이블: {total_medium_risk}개")
        report.append(f"  • 전체 위험도 점수: {total_score}")
        report.append("")
        
        # 개인정보 의심 컬럼 상세 분석
        privacy_columns_summary = {}
        suspicious_columns_summary = {}
        
        for db_result in scan_results:
            db_name = db_result.get('database', 'Unknown')
            
            for table_name, table_data in db_result.get('tables', {}).items():
                full_table_name = f"{db_name}.{table_name}"
                
                for col_name, col_data in table_data.get('columns', {}).items():
                    pattern_scan = col_data.get('pattern_scan', {})
                    
                    # 패턴 매칭된 개인정보 컬럼
                    if pattern_scan and 'privacy_matches' in pattern_scan and pattern_scan['privacy_matches']:
                        matches = pattern_scan['privacy_matches']
                        total_values = pattern_scan.get('total_values', 0)
                        privacy_count = pattern_scan.get('privacy_count', 0)
                        privacy_ratio = pattern_scan.get('privacy_ratio', 0)
                        sample_values = pattern_scan.get('sample_values', [])
                        
                        key = f"{full_table_name}.{col_name}"
                        if key not in privacy_columns_summary:
                            privacy_columns_summary[key] = {
                                'database': db_name,
                                'table': table_name,
                                'column': col_name,
                                'column_type': col_data.get('type', 'Unknown'),
                                'patterns': {},
                                'total_values': total_values,
                                'privacy_count': privacy_count,
                                'privacy_ratio': privacy_ratio,
                                'risk_score': table_data.get('privacy_score', 0),
                                'sample_values': sample_values,
                                'table_rows': table_data.get('sampling_info', {}).get('total_rows', 0)
                            }
                        
                        for pattern_type, match_count in matches.items():
                            if pattern_type not in privacy_columns_summary[key]['patterns']:
                                privacy_columns_summary[key]['patterns'][pattern_type] = 0
                            privacy_columns_summary[key]['patterns'][pattern_type] += match_count
                    
                    # 의심스러운 컬럼명
                    elif col_data.get('suspicious_name'):
                        key = f"{full_table_name}.{col_name}"
                        suspicious_columns_summary[key] = {
                            'database': db_name,
                            'table': table_name,
                            'column': col_name,
                            'column_type': col_data.get('type', 'Unknown'),
                            'reason': '의심스러운 컬럼명',
                            'risk_score': table_data.get('privacy_score', 0),
                            'table_rows': table_data.get('sampling_info', {}).get('total_rows', 0)
                        }
        
        # 개인정보 패턴이 발견된 컬럼들
        if privacy_columns_summary:
            report.append("🚨 개인정보 패턴이 발견된 컬럼들:")
            report.append("")
            
            # 위험도 순으로 정렬
            sorted_privacy_columns = sorted(
                privacy_columns_summary.items(), 
                key=lambda x: x[1]['risk_score'], 
                reverse=True
            )
            
            for i, (col_key, col_info) in enumerate(sorted_privacy_columns, 1):
                report.append(f"  {i:2d}. 📋 컬럼: {col_info['database']}.{col_info['table']}.{col_info['column']}")
                report.append(f"      📊 데이터 타입: {col_info['column_type']}")
                report.append(f"      📈 테이블 총 행수: {col_info['table_rows']:,}행")
                report.append(f"      📈 스캔된 데이터: {col_info['total_values']:,}건")
                report.append(f"      ⚠️  개인정보 발견: {col_info['privacy_count']:,}건 ({col_info['privacy_ratio']:.1%})")
                report.append(f"      🎯 위험도 점수: {col_info['risk_score']}")
                
                # 패턴별 상세
                pattern_details = []
                for pattern_type, count in col_info['patterns'].items():
                    pattern_details.append(f"{pattern_type}({count}건)")
                report.append(f"      • 발견된 패턴: {', '.join(pattern_details)}")
                
                # 샘플 데이터 표시
                if col_info['sample_values']:
                    report.append(f"      📝 샘플 데이터:")
                    for j, sample in enumerate(col_info['sample_values'][:3], 1):
                        report.append(f"         {j}. {sample}")
                    if len(col_info['sample_values']) > 3:
                        report.append(f"         ... 외 {len(col_info['sample_values']) - 3}개")
                
                report.append("")
        else:
            report.append("✅ 개인정보 패턴이 발견된 컬럼이 없습니다.")
            report.append("")
        
        # 의심스러운 컬럼명들
        if suspicious_columns_summary:
            report.append("⚠️  의심스러운 컬럼명들:")
            report.append("")
            
            sorted_suspicious = sorted(
                suspicious_columns_summary.items(),
                key=lambda x: x[1]['risk_score'],
                reverse=True
            )
            
            for i, (col_key, col_info) in enumerate(sorted_suspicious, 1):
                report.append(f"  {i:2d}. 📋 컬럼: {col_info['database']}.{col_info['table']}.{col_info['column']}")
                report.append(f"      📊 데이터 타입: {col_info['column_type']}")
                report.append(f"      📈 테이블 총 행수: {col_info['table_rows']:,}행")
                report.append(f"      🎯 위험도 점수: {col_info['risk_score']}")
                report.append(f"      ⚠️  의심 사유: {col_info['reason']}")
                report.append("")
        else:
            report.append("✅ 의심스러운 컬럼명이 없습니다.")
            report.append("")
        
        # 데이터베이스별 요약
        db_summary = {}
        for db_result in scan_results:
            db_name = db_result.get('database', 'Unknown')
            db_summary[db_name] = {
                'tables': 0,
                'high_risk_tables': 0,
                'medium_risk_tables': 0,
                'privacy_columns': 0,
                'suspicious_columns': 0,
                'total_score': 0
            }
            
            for table_name, table_data in db_result.get('tables', {}).items():
                db_summary[db_name]['tables'] += 1
                risk_level = table_data.get('risk_level', 'LOW')
                
                if risk_level == 'HIGH':
                    db_summary[db_name]['high_risk_tables'] += 1
                elif risk_level == 'MEDIUM':
                    db_summary[db_name]['medium_risk_tables'] += 1
                
                db_summary[db_name]['total_score'] += table_data.get('privacy_score', 0)
                
                for col_name, col_data in table_data.get('columns', {}).items():
                    pattern_scan = col_data.get('pattern_scan', {})
                    if pattern_scan and 'privacy_matches' in pattern_scan and pattern_scan['privacy_matches']:
                        db_summary[db_name]['privacy_columns'] += 1
                    elif col_data.get('suspicious_name'):
                        db_summary[db_name]['suspicious_columns'] += 1
        
        if len(db_summary) > 1:
            report.append("🗄️  데이터베이스별 요약:")
            report.append("")
            
            for db_name, stats in sorted(db_summary.items(), key=lambda x: x[1]['total_score'], reverse=True):
                report.append(f"  📊 {db_name}:")
                report.append(f"      • 테이블 수: {stats['tables']}개")
                report.append(f"      • 고위험 테이블: {stats['high_risk_tables']}개")
                report.append(f"      • 중간위험 테이블: {stats['medium_risk_tables']}개")
                report.append(f"      • 개인정보 컬럼: {stats['privacy_columns']}개")
                report.append(f"      • 의심 컬럼: {stats['suspicious_columns']}개")
                report.append(f"      • 총 위험도 점수: {stats['total_score']}")
                report.append("")
        
        # 패턴별 통계
        pattern_stats = {}
        for col_info in privacy_columns_summary.values():
            for pattern_type, count in col_info['patterns'].items():
                if pattern_type not in pattern_stats:
                    pattern_stats[pattern_type] = {
                        'total_matches': 0,
                        'columns_count': 0,
                        'databases': set(),
                        'tables': set()
                    }
                pattern_stats[pattern_type]['total_matches'] += count
                pattern_stats[pattern_type]['columns_count'] += 1
                pattern_stats[pattern_type]['databases'].add(col_info['database'])
                pattern_stats[pattern_type]['tables'].add(f"{col_info['database']}.{col_info['table']}")
        
        if pattern_stats:
            report.append("📈 패턴별 발견 통계:")
            report.append("")
            
            for pattern_type, stats in sorted(pattern_stats.items()):
                report.append(f"  • {pattern_type}:")
                report.append(f"      • 총 발견 건수: {stats['total_matches']:,}건")
                report.append(f"      • 발견된 컬럼 수: {stats['columns_count']}개")
                report.append(f"      • 관련 테이블 수: {len(stats['tables'])}개")
                report.append(f"      • 관련 데이터베이스: {len(stats['databases'])}개")
                report.append("")
        
        # 권장사항
        report.append("💡 권장사항:")
        
        if privacy_columns_summary:
            report.append("  • 개인정보가 발견된 컬럼들을 우선적으로 검토하세요.")
            report.append("  • 발견된 개인정보의 적절한 암호화 또는 마스킹을 고려하세요.")
            report.append("  • GDPR/개인정보보호법 준수 여부를 점검하세요.")
        
        if suspicious_columns_summary:
            report.append("  • 의심스러운 컬럼명을 가진 테이블들을 추가로 검토하세요.")
        
        if total_high_risk > 0:
            report.append("  • 고위험 테이블들에 대한 즉시 조치가 필요합니다.")
        
        report.append("  • 정기적인 개인정보 스캔을 통해 지속적인 모니터링을 수행하세요.")
        
        return "\n".join(report)

    def save_results_with_summary(self, results: List[Dict], timestamp: str) -> None:
        """결과를 JSON으로 저장하고 요약 리포트 생성"""
        # JSON 파일 저장
        scan_filename = f"polars_privacy_scan_{timestamp}.json"
        with open(scan_filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 스캔 결과가 {scan_filename}에 저장되었습니다.")
        
        # 요약 리포트 생성 및 출력
        summary_report = self.generate_privacy_summary_report(results)
        print("\n" + summary_report)
        
        # 요약 리포트도 파일로 저장
        summary_filename = f"privacy_scan_summary_{timestamp}.txt"
        with open(summary_filename, "w", encoding="utf-8") as f:
            f.write(summary_report)
        
        print(f"📄 요약 리포트가 {summary_filename}에 저장되었습니다.")

    def is_system_schema(self, database_name: str) -> bool:
        """시스템 스키마인지 확인"""
        # 정확한 매칭
        if database_name.lower() in self.system_schemas:
            return True
        
        # 패턴 매칭 (시스템 관련 접두사/접미사)
        db_lower = database_name.lower()
        
        # 시스템 관련 접두사
        system_prefixes = ['sys_', 'system_', 'mysql_', 'info_', 'perf_', 'audit_', 'log_', 'monitor_', 'temp_', 'backup_']
        for prefix in system_prefixes:
            if db_lower.startswith(prefix):
                return True
        
        # 시스템 관련 접미사
        system_suffixes = ['_sys', '_system', '_temp', '_tmp', '_backup', '_log', '_audit', '_monitor', '_test']
        for suffix in system_suffixes:
            if db_lower.endswith(suffix):
                return True
        
        # 숫자만으로 구성된 스키마 (일반적으로 시스템용)
        if database_name.isdigit():
            return True
        
        return False

    def get_user_databases(self) -> List[str]:
        """사용자 데이터베이스 목록 조회 (시스템 스키마 제외)"""
        all_databases = self.get_databases()
        user_databases = []
        system_databases = []
        
        for db in all_databases:
            if self.is_system_schema(db):
                system_databases.append(db)
            else:
                user_databases.append(db)
        
        # 제외된 시스템 스키마 정보 출력
        if system_databases:
            print(f"🔒 시스템 스키마 제외됨 ({len(system_databases)}개):")
            for i, sys_db in enumerate(sorted(system_databases), 1):
                print(f"   {i:2d}. {sys_db}")
            print("")
        
        return user_databases

    def preview_all_databases(self) -> List[Dict]:
        """모든 데이터베이스 구조 분석 및 처리 비용 예측"""
        if not self.connect():
            return []

        try:
            user_databases = self.get_user_databases()

            print(f"🎯 발견된 사용자 데이터베이스: {len(user_databases)}개")
            print(f"⚡ 분석 엔진: Polars")
            print(f"📊 샘플링 설정: 테이블당 최대 {self.sample_size}건")
            print("=" * 60)

            all_analyses = []
            total_start_time = datetime.now()

            for i, database in enumerate(user_databases, 1):
                print(f"\n[{i}/{len(user_databases)}] 데이터베이스 구조 분석 중...")

                analysis_start_time = datetime.now()
                analysis = self.analyze_database_structure(database)
                analysis_end_time = datetime.now()

                analysis['analysis_duration'] = str(analysis_end_time - analysis_start_time)
                all_analyses.append(analysis)

                print(self.generate_structure_report(analysis))
                print(f"⏱️  분석 시간: {analysis_end_time - analysis_start_time}")
                print("\n" + "=" * 80 + "\n")

            total_end_time = datetime.now()
            self.generate_total_preview_summary(all_analyses, total_end_time - total_start_time)

            return all_analyses

        finally:
            self.disconnect()

    def scan_all_databases(self) -> List[Dict]:
        """모든 데이터베이스 스캔 (실제 개인정보 탐지)"""
        if not self.connect():
            return []

        try:
            user_databases = self.get_user_databases()

            print(f"🎯 발견된 사용자 데이터베이스: {len(user_databases)}개")
            print(f"⚡ 처리 엔진: Polars")
            print(f"📊 샘플링: 테이블당 최대 {self.sample_size}건")
            print("=" * 60)

            all_results = []
            total_start_time = datetime.now()

            for i, database in enumerate(user_databases, 1):
                print(f"\n[{i}/{len(user_databases)}] 데이터베이스 처리 중...")

                db_start_time = datetime.now()
                result = self.scan_database(database)
                db_end_time = datetime.now()

                result['processing_time'] = str(db_end_time - db_start_time)
                all_results.append(result)

                print(self.generate_scan_report(result))
                print(f"⏱️  처리 시간: {db_end_time - db_start_time}")
                print("\n" + "=" * 80 + "\n")

            total_end_time = datetime.now()
            print(f"🎉 전체 스캔 완료! (Polars 엔진)")
            print(f"⏱️  총 처리 시간: {total_end_time - total_start_time}")

            return all_results

        finally:
            self.disconnect()

    def scan_all_databases_with_progress(self):
        """진행률 표시와 함께 모든 데이터베이스 스캔"""
        if not self.connect():
            return []
        
        try:
            user_databases = self.get_user_databases()
            results = []
            
            with tqdm(total=len(user_databases), desc="데이터베이스 스캔") as pbar:
                for database in user_databases:
                    result = self.scan_database(database)
                    results.append(result)
                    pbar.update(1)
                    pbar.set_postfix({'현재': database})
            
            return results
        finally:
            self.disconnect()

    def generate_total_preview_summary(self, all_analyses: List[Dict], total_time) -> None:
        """전체 데이터베이스 예측 요약"""
        print("🎯 전체 데이터베이스 처리 비용 예측 요약 (Polars)")
        print("=" * 60)

        total_tables = sum(a.get('summary', {}).get('total_tables', 0) for a in all_analyses)
        total_rows = sum(a.get('summary', {}).get('total_rows', 0) for a in all_analyses)
        total_columns = sum(a.get('summary', {}).get('total_columns', 0) for a in all_analyses)
        total_mb = sum(a.get('summary', {}).get('estimated_total_mb', 0) for a in all_analyses)
        total_scan_time = sum(a.get('summary', {}).get('estimated_total_scan_time_sec', 0) for a in all_analyses)
        scannable_tables = sum(a.get('summary', {}).get('scannable_tables', 0) for a in all_analyses)
        large_tables = sum(a.get('summary', {}).get('large_tables', 0) for a in all_analyses)

        print(f"📊 전체 규모:")
        print(f"  • 데이터베이스 수: {len(all_analyses)}개")
        print(f"  • 총 테이블 수: {total_tables:,}개")
        print(f"  • 스캔 가능한 테이블: {scannable_tables:,}개")
        print(f"  • 대용량 테이블 (100만행+): {large_tables:,}개")
        print(f"  • 총 데이터 행 수: {total_rows:,}행")
        print(f"  • 총 컬럼 수: {total_columns:,}개")

        print(f"\n💾 예상 처리 비용 (Polars 엔진):")
        print(f"  • 예상 총 메모리 사용량: {total_mb:.1f} MB")
        print(f"  • 예상 총 스캔 시간: {total_scan_time:.1f}초")

        if total_scan_time > 60:
            minutes = int(total_scan_time // 60)
            seconds = int(total_scan_time % 60)
            print(f"    → {minutes}분 {seconds}초")

        print(f"\n🚦 처리 위험도 평가:")

        memory_risk = "🟢 낮음" if total_mb < 100 else "🟡 보통" if total_mb < 500 else "🔴 높음"
        time_risk = "🟢 빠름" if total_scan_time < 60 else "🟡 보통" if total_scan_time < 600 else "🔴 오래 걸림"

        print(f"  • 메모리 위험도: {memory_risk} ({total_mb:.1f} MB)")
        print(f"  • 시간 위험도: {time_risk} ({total_scan_time:.1f}초)")

        if large_tables > 20:
            print(f"  • 대용량 테이블 위험도: 🔴 높음 ({large_tables}개)")
        elif large_tables > 5:
            print(f"  • 대용량 테이블 위험도: 🟡 보통 ({large_tables}개)")
        else:
            print(f"  • 대용량 테이블 위험도: 🟢 낮음 ({large_tables}개)")

        print(f"\n⏱️  전체 분석 시간: {total_time}")
        print(f"🚀 Polars 엔진으로 최적화된 처리 준비 완료!")

        print(f"\n💡 스캔 실행 권장사항:")

        if total_mb > 1000:
            print(f"  ⚠️  메모리 사용량이 높습니다 ({total_mb:.1f}MB)")
            print(f"     → 샘플 크기를 50으로 줄이거나 데이터베이스별로 분할 실행하세요")

        if total_scan_time > 1800:
            print(f"  ⚠️  예상 처리 시간이 깁니다 ({total_scan_time / 60:.1f}분)")
            print(f"     → 대용량 테이블을 제외하거나 배치로 나누어 실행하세요")

        if large_tables > 50:
            print(f"  ⚠️  대용량 테이블이 많습니다 ({large_tables}개)")
            print(f"     → 우선순위가 높은 테이블부터 선별적으로 스캔하세요")

        if total_tables > 1000:
            print(f"  ⚠️  테이블 수가 많습니다 ({total_tables:,}개)")
            print(f"     → 중요한 데이터베이스부터 단계적으로 스캔하세요")

        print(f"\n✅ 구조 분석 완료! 이제 실제 스캔을 실행할 수 있습니다.")
        print("=" * 60)


# 사용 예시
if __name__ == "__main__":
    # .env 파일 로드 (있는 경우)
    load_dotenv()
    
    # Polars 기반 스캐너 초기화 (비밀번호 없이도 가능)
    scanner = PolarsPrivacyScanner(
        host="localhost",
        user="root",
        # password="fosslight",  # 비밀번호 없이도 접속 가능
        port=9030,
        sample_size=100
    )

    print("🚀 Polars 기반 MySQL 개인정보 스캐너")
    print("📦 환경 설정:")
    print("   uv venv privacy-scanner")
    print("   source privacy-scanner/bin/activate  # Linux/Mac")
    print("   # privacy-scanner\\Scripts\\activate  # Windows")
    print("   uv add polars mysql-connector-python")
    print("=" * 60)
    print("자동 실행 순서: 구조 분석 → 비용 예측 → 개인정보 스캔")
    print("=" * 60)

    # 연결 정보 출력
    print(f"🔗 연결 정보:")
    print(f"   • 호스트: {scanner.host}:{scanner.port}")
    print(f"   • 사용자: {scanner.user}")
    if scanner.password:
        print(f"   • 인증: 사용자명 + 비밀번호")
    else:
        print(f"   • 인증: 사용자명만 (비밀번호 없음)")
    print(f"   • 샘플 크기: {scanner.sample_size}건")
    print("=" * 60)

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1단계: 데이터베이스 구조 분석
        print("\n🔍 1단계: 데이터베이스 구조 분석 시작...")
        analyses = scanner.preview_all_databases()

        analysis_filename = f"polars_db_analysis_{timestamp}.json"
        with open(analysis_filename, "w", encoding="utf-8") as f:
            json.dump(analyses, f, ensure_ascii=False, indent=2)

        print(f"\n💾 구조 분석 결과가 {analysis_filename}에 저장되었습니다.")

        # 2단계: 사용자 확인 (자동 진행)
        print("\n⏳ 3초 후 개인정보 스캔을 자동으로 시작합니다...")
        import time
        time.sleep(3)

        # 3단계: 개인정보 스캔 실행
        print("\n🚀 2단계: 개인정보 스캔 실행...")
        results = scanner.scan_all_databases()

        # 4단계: 결과 저장 및 요약 리포트 생성
        scanner.save_results_with_summary(results, timestamp)

        print(f"\n✅ 전체 프로세스 완료!")
        print(f"📄 구조 분석: {analysis_filename}")
        print(f"📄 스캔 결과: polars_privacy_scan_{timestamp}.json")
        print(f"📄 요약 리포트: privacy_scan_summary_{timestamp}.txt")

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")

    print("\n👋 프로그램을 종료합니다.")