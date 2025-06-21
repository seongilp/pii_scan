import cx_Oracle
import polars as pl
import re
import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')


class OraclePrivacyScanner:
    def __init__(self, host: str, port: int, service_name: str, user: str, password: str,
                 sample_size: int = 100):
        """
        Oracle 기반 개인정보 스캐너

        Args:
            host: Oracle 서버 호스트
            port: Oracle 포트 (기본 1521)
            service_name: Oracle 서비스명 또는 SID
            user: 사용자명
            password: 비밀번호
            sample_size: 샘플링할 행 수
        """
        self.host = host
        self.port = port
        self.service_name = service_name
        self.user = user
        self.password = password
        self.connection = None
        self.sample_size = sample_size

        # Oracle 연결 문자열 생성
        self.dsn = cx_Oracle.makedsn(host, port, service_name=service_name)

        # 개인정보 패턴 정의 - 한국 형식으로 업데이트
        self.privacy_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\d{2,3}-\d{3,4}-\d{4}|\d{10,11})',
            'ssn': r'\d{6}-[1-4]\d{6}',  # 한국 주민등록번호 형식
            'card_number': r'5327-\d{4}-\d{4}-\d{4}',  # 5327로 시작하는 16자리 카드번호
            'account_number': r'1000-\d{8}',  # 1000으로 시작하는 12자리 계좌번호
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        }

        # 개인정보 관련 컬럼명 키워드
        self.privacy_keywords = [
            'name', 'email', 'phone', 'mobile', 'tel', 'address', 'addr',
            'ssn', 'social', 'birth', 'birthday', 'card', 'account',
            '이름', '성명', '전화', '휴대폰', '주소', '주민', '생년월일', '카드', '계좌',
            'user_id', 'customer', '고객', 'personal', '개인', 'emp_id', 'employee'
        ]

        print(f"🔮 Oracle 기반 개인정보 스캐너 초기화")
        print(f"   Host: {host}:{port}")
        print(f"   Service: {service_name}")
        print(f"   User: {user}")
        print(f"   샘플 크기: {sample_size}건")

    def connect(self):
        """Oracle 연결"""
        try:
            self.connection = cx_Oracle.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
                encoding="UTF-8"
            )
            print(f"✅ Oracle 연결 성공: {self.host}:{self.port}/{self.service_name}")
            return True
        except cx_Oracle.Error as err:
            print(f"❌ Oracle 연결 실패: {err}")
            return False

    def disconnect(self):
        """Oracle 연결 해제"""
        if self.connection:
            self.connection.close()
            print("🔐 Oracle 연결 해제")

    def get_schemas(self) -> List[str]:
        """모든 스키마 목록 조회 (사용자 소유)"""
        cursor = self.connection.cursor()

        # 현재 사용자가 접근 가능한 스키마 조회
        cursor.execute("""
                       SELECT DISTINCT OWNER
                       FROM ALL_TABLES
                       WHERE OWNER NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'APPQOSSYS',
                                           'WMSYS', 'EXFSYS', 'CTXSYS', 'XDB', 'ANONYMOUS',
                                           'OLAPSYS', 'MDSYS', 'ORDSYS', 'FLOWS_FILES',
                                           'APEX_030200', 'APEX_PUBLIC_USER', 'SPATIAL_CSW_ADMIN_USR',
                                           'SPATIAL_WFS_ADMIN_USR', 'PUBLIC')
                       ORDER BY OWNER
                       """)

        schemas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return schemas

    def get_tables(self, schema: str) -> List[str]:
        """특정 스키마의 테이블 목록 조회"""
        cursor = self.connection.cursor()

        cursor.execute("""
                       SELECT TABLE_NAME
                       FROM ALL_TABLES
                       WHERE OWNER = :schema
                       ORDER BY TABLE_NAME
                       """, schema=schema)

        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables

    def get_table_info(self, schema: str, table: str) -> Dict:
        """테이블 정보 조회 (행 수, 컬럼 정보)"""
        cursor = self.connection.cursor()

        # 행 수 조회
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
            total_rows = cursor.fetchone()[0]
        except Exception as e:
            print(f"    ⚠️  행 수 조회 실패: {str(e)}")
            total_rows = 0

        # 컬럼 정보 조회
        cursor.execute("""
                       SELECT COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_LENGTH, DATA_PRECISION, DATA_SCALE
                       FROM ALL_TAB_COLUMNS
                       WHERE OWNER = :schema
                         AND TABLE_NAME = :table
                       ORDER BY COLUMN_ID
                       """, schema=schema, table=table)

        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2],
                'length': row[3],
                'precision': row[4],
                'scale': row[5]
            })

        cursor.close()
        return {
            'total_rows': total_rows,
            'columns': columns
        }

    def estimate_dataframe_size(self, columns: List[Dict], sample_rows: int) -> Dict:
        """DataFrame 예상 크기 계산 (Oracle 타입 기준)"""
        size_estimates = {
            'NUMBER': 8, 'INTEGER': 8, 'FLOAT': 8,
            'VARCHAR2': 50, 'CHAR': 20, 'CLOB': 500, 'LONG': 200,
            'DATE': 8, 'TIMESTAMP': 12, 'TIMESTAMP(6)': 12,
            'RAW': 50, 'BLOB': 500, 'LONG RAW': 200
        }

        total_bytes_per_row = 0
        text_columns = 0
        numeric_columns = 0
        date_columns = 0

        for col in columns:
            col_type = col['type'].upper()
            col_size = 8  # 기본값

            # Oracle 타입별 크기 추정
            if col_type in size_estimates:
                col_size = size_estimates[col_type]
            elif col_type.startswith('VARCHAR2'):
                # VARCHAR2(n) 처리
                col_size = min(col.get('length', 50), 255)
                text_columns += 1
            elif col_type.startswith('CHAR'):
                col_size = min(col.get('length', 20), 255)
                text_columns += 1
            elif col_type in ['CLOB', 'LONG']:
                text_columns += 1
            elif col_type in ['NUMBER', 'INTEGER', 'FLOAT']:
                numeric_columns += 1
            elif col_type in ['DATE', 'TIMESTAMP'] or col_type.startswith('TIMESTAMP'):
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
        """스캔 시간 예측 (Oracle + Polars 기준)"""
        base_speed_rows_per_sec = 45000  # Oracle은 MySQL보다 약간 느림
        regex_speed_factor = 0.3
        text_factor = 1 + (text_columns * 0.1)

        effective_speed = base_speed_rows_per_sec * regex_speed_factor / text_factor

        # Oracle 쿼리는 MySQL보다 약간 느림
        db_query_time = max(0.2, total_rows / 800000)
        dataframe_creation_time = max(0.05, estimated_mb / 80)
        pattern_scan_time = sample_rows / effective_speed

        total_estimated_seconds = db_query_time + dataframe_creation_time + pattern_scan_time

        return {
            'engine': 'Oracle + Polars',
            'db_query_time_sec': round(db_query_time, 2),
            'dataframe_creation_time_sec': round(dataframe_creation_time, 2),
            'pattern_scan_time_sec': round(pattern_scan_time, 2),
            'total_estimated_sec': round(total_estimated_seconds, 2),
            'estimated_rows_per_sec': int(effective_speed),
            'text_columns_factor': round(text_factor, 2)
        }

    def load_table_sample(self, schema: str, table: str) -> Tuple[Optional[pl.DataFrame], Dict]:
        """테이블에서 샘플 데이터를 Polars DataFrame으로 로드"""
        cursor = self.connection.cursor()

        table_info = self.get_table_info(schema, table)
        total_rows = table_info['total_rows']

        if total_rows == 0:
            print(f"    ⚠️  빈 테이블")
            return None, {'method': 'empty', 'total_rows': 0, 'sampled_rows': 0}

        # Oracle 샘플링 쿼리
        if total_rows <= self.sample_size:
            query = f"SELECT * FROM {schema}.{table}"
            sample_method = "전체 데이터"
        else:
            # Oracle의 SAMPLE 사용 (더 효율적)
            sample_percent = min(50, (self.sample_size / total_rows) * 100 * 2)  # 약간 여유있게
            query = f"""
                SELECT * FROM (
                    SELECT * FROM {schema}.{table} SAMPLE({sample_percent:.2f})
                    ORDER BY DBMS_RANDOM.VALUE
                ) WHERE ROWNUM <= {self.sample_size}
            """
            sample_method = f"Oracle SAMPLE ({sample_percent:.1f}%)"

        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                return None, {'method': 'no_data', 'total_rows': total_rows, 'sampled_rows': 0}

            # 컬럼명 추출
            columns = [desc[0] for desc in cursor.description]

            # Oracle의 None을 처리하여 Polars DataFrame 생성
            processed_rows = []
            for row in rows:
                processed_row = []
                for value in row:
                    if value is None:
                        processed_row.append(None)
                    elif isinstance(value, cx_Oracle.LOB):
                        # CLOB/BLOB 처리
                        try:
                            processed_row.append(value.read())
                        except:
                            processed_row.append(str(value))
                    else:
                        processed_row.append(value)
                processed_rows.append(processed_row)

            df = pl.DataFrame(processed_rows, schema=columns)

            sampling_info = {
                'method': sample_method,
                'total_rows': total_rows,
                'sampled_rows': len(processed_rows),
                'sampling_ratio': len(processed_rows) / total_rows if total_rows > 0 else 0
            }

            print(f"    📊 {total_rows:,}행 → {len(processed_rows)}행 샘플링 ({sample_method})")

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

            # null이 아닌 데이터만 추출하고 문자열로 변환
            col_data = df.select(pl.col(column).filter(pl.col(column).is_not_null())).to_series()
            values = [str(val) for val in col_data.to_list() if val is not None]

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

    def analyze_dataframe(self, df: pl.DataFrame, schema: str, table_name: str, sampling_info: Dict) -> Dict:
        """Polars DataFrame 전체 분석"""
        if df is None:
            return {
                'schema': schema,
                'table': table_name,
                'sampling_info': sampling_info,
                'columns': {},
                'privacy_score': 0,
                'risk_level': 'EMPTY' if sampling_info.get('total_rows', 0) == 0 else 'ERROR'
            }

        print(f"    🔍 DataFrame 분석 중... (Polars)")

        result = {
            'schema': schema,
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

    def scan_table(self, schema: str, table: str) -> Dict:
        """테이블 스캔 (Oracle + Polars 기반)"""
        print(f"  📋 테이블 스캔: {schema}.{table}")

        df, sampling_info = self.load_table_sample(schema, table)
        result = self.analyze_dataframe(df, schema, table, sampling_info)

        print(f"    ✅ 완료 (위험도: {result['risk_level']}, 점수: {result['privacy_score']})")

        return result

    def analyze_schema_structure(self, schema: str) -> Dict:
        """스키마 구조 분석 및 처리 비용 예측"""
        print(f"🔍 스키마 구조 분석 중: {schema}")

        analysis = {
            'schema': schema,
            'analysis_time': datetime.now().isoformat(),
            'engine': 'Oracle + Polars',
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
            tables = self.get_tables(schema)
            analysis['summary']['total_tables'] = len(tables)

            print(f"  📊 발견된 테이블: {len(tables)}개")

            for table in tables:
                print(f"    📋 분석 중: {table}")

                try:
                    table_info = self.get_table_info(schema, table)
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
            print(f"❌ 스키마 분석 오류: {str(e)}")

        return analysis

    def scan_schema(self, schema: str) -> Dict:
        """스키마 전체 스캔"""
        print(f"🔍 스키마 스캔 시작: {schema} (Oracle + Polars 엔진)")

        scan_results = {
            'schema': schema,
            'scan_time': datetime.now().isoformat(),
            'engine': 'Oracle + Polars',
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
            tables = self.get_tables(schema)
            scan_results['summary']['total_tables'] = len(tables)

            for table in tables:
                table_result = self.scan_table(schema, table)
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
            print(f"❌ 스키마 스캔 오류: {str(e)}")

        return scan_results

    def generate_structure_report(self, analysis: Dict) -> str:
        """스키마 구조 분석 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("🔮 Oracle 스키마 구조 분석 및 처리 비용 예측")
        report.append("=" * 80)
        report.append(f"스키마: {analysis['schema']}")
        report.append(f"분석 시간: {analysis['analysis_time']}")
        report.append(f"처리 엔진: Oracle + Polars")
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

        report.append("💾 예상 처리 비용 (Oracle + Polars 엔진):")
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
        report.append("💡 Oracle 특화 권장사항:")
        report.append("  • Oracle SAMPLE을 이용한 효율적인 샘플링")
        report.append("  • CLOB/BLOB 컬럼 자동 처리")
        report.append("  • 스키마별 독립적인 스캔 가능")

        return "\n".join(report)

    def generate_scan_report(self, scan_results: Dict) -> str:
        """스캔 결과 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("📊 Oracle 개인정보 스캔 리포트")
        report.append("=" * 80)
        report.append(f"스키마: {scan_results['schema']}")
        report.append(f"스캔 시간: {scan_results['scan_time']}")
        report.append(f"처리 엔진: Oracle + Polars")
        report.append(f"샘플 사이즈: {scan_results.get('sample_size', 'Unknown')}건")
        report.append("")

        summary = scan_results.get('summary', {})
        total_data_rows = summary.get('total_data_rows', 0)
        total_sampled_rows = summary.get('total_sampled_rows', 0)

        report.append("📋 스캔 요약:")
        report.append(f"  • 총 테이블 수: {summary.get('total_tables', 0)}")
        report.append(f"  • 스캔된 테이블 수: {summary.get('scanned_tables', 0)}")
        report.append(f"  • 고위험 테이블: {summary.get('high_risk_tables', 0)}개")
        report.append(f"  • 중간위험 테이블: {summary.get('medium_risk_tables', 0)}개")
        report.append(f"  • 저위험 테이블: {summary.get('low_risk_tables', 0)}개")
        report.append(f"  • 총 개인정보 위험도 점수: {summary.get('total_privacy_score', 0)}")
        report.append(f"  • 전체 데이터 행 수: {total_data_rows:,}")
        report.append(f"  • 샘플링된 행 수: {total_sampled_rows:,}")

        if total_data_rows > 0:
            sampling_efficiency = total_sampled_rows / total_data_rows
            report.append(f"  • 샘플링 효율: {sampling_efficiency:.1%}")

        report.append("")

        # 고위험 테이블 상세 정보
        high_risk_tables = []
        for table_name, table_data in scan_results.get('tables', {}).items():
            if table_data.get('risk_level') == 'HIGH':
                high_risk_tables.append({
                    'name': table_name,
                    'score': table_data.get('privacy_score', 0),
                    'data': table_data
                })

        high_risk_tables.sort(key=lambda x: x['score'], reverse=True)

        if high_risk_tables:
            report.append("🚨 고위험 테이블 상세:")
            for table_info in high_risk_tables:
                table_name = table_info['name']
                table_data = table_info['data']
                sampling_info = table_data.get('sampling_info', {})
                schema = table_data.get('schema', 'Unknown')

                report.append(f"  • {schema}.{table_name} (점수: {table_info['score']})")
                report.append(f"    - 총 행수: {sampling_info.get('total_rows', 0):,}")
                report.append(f"    - 샘플링: {sampling_info.get('method', 'Unknown')}")

                privacy_columns = []
                for col_name, col_data in table_data.get('columns', {}).items():
                    pattern_scan = col_data.get('pattern_scan', {})
                    if pattern_scan and 'privacy_matches' in pattern_scan and pattern_scan['privacy_matches']:
                        matches = pattern_scan['privacy_matches']
                        ratio = pattern_scan.get('privacy_ratio', 0)
                        match_details = [f"{k}({v})" for k, v in matches.items()]
                        privacy_columns.append(f"      - {col_name}: {', '.join(match_details)} [비율: {ratio:.1%}]")
                    elif col_data.get('suspicious_name'):
                        privacy_columns.append(f"      - {col_name}: 의심스러운 컬럼명")

                if privacy_columns:
                    report.extend(privacy_columns)
                report.append("")

        # Oracle 특화 성능 정보
        report.append("⚡ Oracle 특화 성능 정보:")
        report.append("  • Oracle SAMPLE 기반 고속 샘플링")
        report.append("  • CLOB/BLOB 데이터 자동 처리")
        report.append("  • Polars 벡터화 분석 엔진")
        report.append("  • 스키마별 독립적 처리")

        return "\n".join(report)

    def preview_all_schemas(self) -> List[Dict]:
        """모든 스키마 구조 분석 및 처리 비용 예측"""
        if not self.connect():
            return []

        try:
            schemas = self.get_schemas()

            print(f"🎯 발견된 사용자 스키마: {len(schemas)}개")
            print(f"⚡ 분석 엔진: Oracle + Polars")
            print(f"📊 샘플링 설정: 테이블당 최대 {self.sample_size}건")
            print("=" * 60)

            all_analyses = []
            total_start_time = datetime.now()

            for i, schema in enumerate(schemas, 1):
                print(f"\n[{i}/{len(schemas)}] 스키마 구조 분석 중...")

                analysis_start_time = datetime.now()
                analysis = self.analyze_schema_structure(schema)
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

    def generate_total_preview_summary(self, all_analyses: List[Dict], total_time) -> None:
        """전체 스키마 예측 요약"""
        print("🎯 전체 Oracle 스키마 처리 비용 예측 요약")
        print("=" * 60)

        total_tables = sum(a.get('summary', {}).get('total_tables', 0) for a in all_analyses)
        total_rows = sum(a.get('summary', {}).get('total_rows', 0) for a in all_analyses)
        total_columns = sum(a.get('summary', {}).get('total_columns', 0) for a in all_analyses)
        total_mb = sum(a.get('summary', {}).get('estimated_total_mb', 0) for a in all_analyses)
        total_scan_time = sum(a.get('summary', {}).get('estimated_total_scan_time_sec', 0) for a in all_analyses)
        scannable_tables = sum(a.get('summary', {}).get('scannable_tables', 0) for a in all_analyses)
        large_tables = sum(a.get('summary', {}).get('large_tables', 0) for a in all_analyses)

        print(f"📊 전체 규모:")
        print(f"  • 스키마 수: {len(all_analyses)}개")
        print(f"  • 총 테이블 수: {total_tables:,}개")
        print(f"  • 스캔 가능한 테이블: {scannable_tables:,}개")
        print(f"  • 대용량 테이블 (100만행+): {large_tables:,}개")
        print(f"  • 총 데이터 행 수: {total_rows:,}행")
        print(f"  • 총 컬럼 수: {total_columns:,}개")

        print(f"\n💾 예상 처리 비용 (Oracle + Polars 엔진):")
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
        print(f"🔮 Oracle + Polars 엔진으로 최적화된 처리 준비 완료!")

        print(f"\n💡 Oracle 특화 권장사항:")
        print(f"  • SAMPLE을 이용한 효율적인 대용량 테이블 처리")
        print(f"  • CLOB/BLOB 컬럼 자동 변환 처리")
        print(f"  • 스키마별 순차 처리로 메모리 효율성 확보")
        print(f"  • Oracle 시스템 스키마 자동 제외")

        print(f"\n✅ 구조 분석 완료! 이제 실제 스캔을 실행할 수 있습니다.")
        print("=" * 60)

    def scan_all_schemas(self) -> List[Dict]:
        """모든 스키마 스캔 (실제 개인정보 탐지)"""
        if not self.connect():
            return []

        try:
            schemas = self.get_schemas()

            print(f"🎯 발견된 사용자 스키마: {len(schemas)}개")
            print(f"⚡ 처리 엔진: Oracle + Polars")
            print(f"📊 샘플링: 테이블당 최대 {self.sample_size}건")
            print("=" * 60)

            all_results = []
            total_start_time = datetime.now()

            for i, schema in enumerate(schemas, 1):
                print(f"\n[{i}/{len(schemas)}] 스키마 처리 중...")

                schema_start_time = datetime.now()
                result = self.scan_schema(schema)
                schema_end_time = datetime.now()

                result['processing_time'] = str(schema_end_time - schema_start_time)
                all_results.append(result)

                print(self.generate_scan_report(result))
                print(f"⏱️  처리 시간: {schema_end_time - schema_start_time}")
                print("\n" + "=" * 80 + "\n")

            total_end_time = datetime.now()
            print(f"🎉 전체 스캔 완료! (Oracle + Polars 엔진)")
            print(f"⏱️  총 처리 시간: {total_end_time - total_start_time}")

            return all_results

        finally:
            self.disconnect()


# 사용 예시
if __name__ == "__main__":
    # Oracle 기반 스캐너 초기화
    scanner = OraclePrivacyScanner(
        host="localhost",
        port=1521,
        service_name="ORCL",  # 또는 "XE", "XEPDB1" 등
        user="your_username",
        password="your_password",
        sample_size=100
    )

    print("🔮 Oracle 기반 개인정보 스캐너")
    print("📦 환경 설정:")
    print("   uv venv oracle-privacy-scanner")
    print("   source oracle-privacy-scanner/bin/activate  # Linux/Mac")
    print("   # oracle-privacy-scanner\\Scripts\\activate  # Windows")
    print("   uv add polars cx-Oracle")
    print("=" * 60)
    print("자동 실행 순서: 구조 분석 → 비용 예측 → 개인정보 스캔")
    print("=" * 60)

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1단계: 스키마 구조 분석
        print("\n🔍 1단계: Oracle 스키마 구조 분석 시작...")
        analyses = scanner.preview_all_schemas()

        analysis_filename = f"oracle_schema_analysis_{timestamp}.json"
        with open(analysis_filename, "w", encoding="utf-8") as f:
            json.dump(analyses, f, ensure_ascii=False, indent=2)

        print(f"\n💾 구조 분석 결과가 {analysis_filename}에 저장되었습니다.")

        # 2단계: 사용자 확인 (자동 진행)
        print("\n⏳ 3초 후 개인정보 스캔을 자동으로 시작합니다...")
        import time

        time.sleep(3)

        # 3단계: 개인정보 스캔 실행
        print("\n🚀 2단계: Oracle 개인정보 스캔 실행...")
        results = scanner.scan_all_schemas()

        scan_filename = f"oracle_privacy_scan_{timestamp}.json"
        with open(scan_filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 전체 프로세스 완료!")
        print(f"📄 구조 분석: {analysis_filename}")
        print(f"📄 스캔 결과: {scan_filename}")

        # 전체 요약
        if results:
            total_tables = sum(r.get('summary', {}).get('total_tables', 0) for r in results)
            total_high_risk = sum(r.get('summary', {}).get('high_risk_tables', 0) for r in results)
            total_score = sum(r.get('summary', {}).get('total_privacy_score', 0) for r in results)
            total_data_rows = sum(r.get('summary', {}).get('total_data_rows', 0) for r in results)

            print(f"\n📊 최종 전체 요약:")
            print(f"  • 처리 엔진: Oracle + Polars")
            print(f"  • 스캔된 스키마: {len(results)}개")
            print(f"  • 총 테이블 수: {total_tables}")
            print(f"  • 총 데이터 행 수: {total_data_rows:,}")
            print(f"  • 고위험 테이블 수: {total_high_risk}")
            print(f"  • 전체 개인정보 위험도 점수: {total_score}")
            print(f"  • Oracle + Polars 기반 고성능 처리 완료! 🔮")

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        print("\n💡 확인사항:")
        print("  • Oracle 서버가 실행 중인지 확인")
        print("  • 연결 정보 (host, port, service_name) 확인")
        print("  • 사용자 권한 확인")
        print("  • cx_Oracle 라이브러리 설치 확인")

    print("\n👋 프로그램을 종료합니다.")