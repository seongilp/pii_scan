import random
import string
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import csv
import sqlite3
import mysql.connector
import cx_Oracle
from pathlib import Path

class DummyDataGenerator:
    def __init__(self):
        self.first_names = [
            "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
            "한", "오", "서", "신", "권", "황", "안", "송", "류", "전",
            "고", "문", "양", "손", "배", "조", "백", "허", "유", "남",
            "심", "노", "정", "하", "곽", "성", "차", "주", "우", "구",
            "신", "임", "나", "전", "민", "유", "진", "지", "엄", "채"
        ]
        
        self.last_names = [
            "민준", "서준", "도윤", "예준", "시우", "주원", "하준", "지호", "지후", "준서",
            "준우", "현우", "도현", "우진", "민재", "건우", "서진", "현준", "동현", "지훈",
            "준혁", "도훈", "우현", "민석", "재현", "준영", "현석", "재원", "민호", "재민",
            "지원", "재준", "현진", "민수", "재훈", "준호", "현수", "재영", "민영", "재호",
            "지영", "민지", "서연", "지우", "서현", "민서", "지은", "하은", "예은", "윤서"
        ]
        
        self.domains = ["gmail.com", "naver.com", "daum.net", "hanmail.net", "hotmail.com", "yahoo.com"]
        self.banks = ["신한은행", "KB국민은행", "우리은행", "하나은행", "NH농협은행", "기업은행", "새마을금고"]
        
    def generate_email(self) -> str:
        """무작위 이메일 생성"""
        name = random.choice(self.first_names) + random.choice(self.last_names)
        numbers = ''.join(random.choices(string.digits, k=random.randint(1, 4)))
        domain = random.choice(self.domains)
        return f"{name}{numbers}@{domain}"
    
    def generate_phone(self) -> str:
        """무작위 전화번호 생성"""
        prefixes = ["010", "011", "016", "017", "018", "019"]
        prefix = random.choice(prefixes)
        middle = ''.join(random.choices(string.digits, k=4))
        last = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}-{middle}-{last}"
    
    def generate_ssn(self) -> str:
        """무작위 주민등록번호 생성"""
        # 생년월일 (1900-2020년)
        year = random.randint(1900, 2020)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # 간단히 28일로 제한
        
        # 성별 (1-4: 남성, 5-8: 여성)
        gender = random.randint(1, 8)
        
        # 지역코드
        region = ''.join(random.choices(string.digits, k=4))
        
        # 체크섬 (간단한 랜덤)
        checksum = random.randint(0, 9)
        
        return f"{year:04d}{month:02d}{day:02d}-{gender}{region}{checksum}"
    
    def generate_credit_card(self) -> str:
        """무작위 신용카드번호 생성 - 5327로 시작하는 16자리"""
        # 5327로 시작하는 카드번호 생성
        start_digits = "5327"
        remaining = ''.join(random.choices(string.digits, k=12))
        card_number = start_digits + remaining
        
        # 4자리씩 그룹화
        groups = [card_number[i:i+4] for i in range(0, len(card_number), 4)]
        return '-'.join(groups)
    
    def generate_account_number(self) -> str:
        """무작위 계좌번호 생성 - 1000으로 시작하는 12자리"""
        bank = random.choice(self.banks)
        # 1000으로 시작하는 12자리 계좌번호
        start_digits = "1000"
        remaining = ''.join(random.choices(string.digits, k=8))
        account_num = start_digits + remaining
        return f"{bank}-{account_num}"
    
    def generate_address(self) -> str:
        """무작위 주소 생성"""
        cities = ["서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시", "울산광역시"]
        districts = ["강남구", "서초구", "마포구", "종로구", "중구", "용산구", "성동구", "광진구"]
        streets = ["테헤란로", "강남대로", "영동대로", "삼성로", "역삼로", "논현로", "신사동길"]
        
        city = random.choice(cities)
        district = random.choice(districts)
        street = random.choice(streets)
        number = random.randint(1, 999)
        
        return f"{city} {district} {street} {number}"
    
    def generate_birth_date(self) -> str:
        """무작위 생년월일 생성"""
        start_date = datetime(1960, 1, 1)
        end_date = datetime(2005, 12, 31)
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        random_date = start_date + timedelta(days=random_number_of_days)
        return random_date.strftime("%Y-%m-%d")
    
    def generate_single_record(self) -> Dict[str, Any]:
        """단일 레코드 생성"""
        return {
            "id": random.randint(10000, 99999),
            "name": random.choice(self.first_names) + random.choice(self.last_names),
            "email": self.generate_email(),
            "phone": self.generate_phone(),
            "ssn": self.generate_ssn(),
            "credit_card": self.generate_credit_card(),
            "account_number": self.generate_account_number(),
            "address": self.generate_address(),
            "birth_date": self.generate_birth_date(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def generate_batch(self, count: int = 100) -> List[Dict[str, Any]]:
        """배치 데이터 생성"""
        records = []
        for i in range(count):
            record = self.generate_single_record()
            record["id"] = i + 1  # 순차적 ID
            records.append(record)
        return records
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str = None):
        """JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dummy_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"데이터가 {filename}에 저장되었습니다.")
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None):
        """CSV 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dummy_data_{timestamp}.csv"
        
        if data:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        print(f"데이터가 {filename}에 저장되었습니다.")
    
    def save_to_sqlite(self, data: List[Dict[str, Any]], db_path: str = "dummy_data.db"):
        """SQLite 데이터베이스에 저장"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dummy_data (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                ssn TEXT,
                credit_card TEXT,
                account_number TEXT,
                address TEXT,
                birth_date TEXT,
                created_at TEXT
            )
        ''')
        
        # 데이터 삽입
        for record in data:
            cursor.execute('''
                INSERT INTO dummy_data 
                (id, name, email, phone, ssn, credit_card, account_number, address, birth_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record['id'], record['name'], record['email'], record['phone'],
                record['ssn'], record['credit_card'], record['account_number'],
                record['address'], record['birth_date'], record['created_at']
            ))
        
        conn.commit()
        conn.close()
        print(f"데이터가 SQLite 데이터베이스 {db_path}에 저장되었습니다.")
    
    def save_to_mysql(self, data: List[Dict[str, Any]], config: Dict[str, Any]):
        """MySQL 데이터베이스에 저장"""
        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            
            # 테이블이 존재하면 삭제하고 새로 생성
            cursor.execute("DROP TABLE IF EXISTS dummy_data")
            
            # 테이블 생성 - 가장 기본적인 문법으로 수정
            create_table_sql = """
                CREATE TABLE dummy_data (
                    id INT,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    phone VARCHAR(20),
                    ssn VARCHAR(20),
                    credit_card VARCHAR(30),
                    account_number VARCHAR(50),
                    address TEXT,
                    birth_date DATE,
                    created_at DATETIME
                )
            """
            
            cursor.execute(create_table_sql)
            
            # 데이터 삽입
            for record in data:
                insert_sql = """
                    INSERT INTO dummy_data 
                    (id, name, email, phone, ssn, credit_card, account_number, address, birth_date, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (
                    record['id'], record['name'], record['email'], record['phone'],
                    record['ssn'], record['credit_card'], record['account_number'],
                    record['address'], record['birth_date'], record['created_at']
                ))
            
            conn.commit()
            conn.close()
            print("데이터가 MySQL 데이터베이스에 저장되었습니다.")
            
        except Exception as e:
            print(f"MySQL 저장 중 오류 발생: {e}")
            # 더 자세한 오류 정보 출력
            import traceback
            print("상세 오류 정보:")
            print(traceback.format_exc())
    
    def save_to_oracle(self, data: List[Dict[str, Any]], config: Dict[str, Any]):
        """Oracle 데이터베이스에 저장"""
        try:
            conn = cx_Oracle.connect(**config)
            cursor = conn.cursor()
            
            # 테이블 생성
            cursor.execute('''
                CREATE TABLE dummy_data (
                    id NUMBER PRIMARY KEY,
                    name VARCHAR2(100),
                    email VARCHAR2(100),
                    phone VARCHAR2(20),
                    ssn VARCHAR2(20),
                    credit_card VARCHAR2(30),
                    account_number VARCHAR2(50),
                    address CLOB,
                    birth_date DATE,
                    created_at TIMESTAMP
                )
            ''')
            
            # 데이터 삽입
            for record in data:
                cursor.execute('''
                    INSERT INTO dummy_data 
                    (id, name, email, phone, ssn, credit_card, account_number, address, birth_date, created_at)
                    VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
                ''', (
                    record['id'], record['name'], record['email'], record['phone'],
                    record['ssn'], record['credit_card'], record['account_number'],
                    record['address'], record['birth_date'], record['created_at']
                ))
            
            conn.commit()
            conn.close()
            print("데이터가 Oracle 데이터베이스에 저장되었습니다.")
            
        except Exception as e:
            print(f"Oracle 저장 중 오류 발생: {e}")


def get_database_config(db_type: str) -> Dict[str, Any]:
    """데이터베이스 설정 정보 입력받기"""
    config = {}
    
    if db_type == "mysql":
        print("\n=== MySQL 연결 설정 ===")
        config["host"] = input("호스트 (기본값: localhost): ") or "localhost"
        config["port"] = int(input("포트 (기본값: 3306): ") or "3306")
        config["user"] = input("사용자명: ")
        config["password"] = input("비밀번호: ")
        config["database"] = input("데이터베이스명: ")
        
    elif db_type == "oracle":
        print("\n=== Oracle 연결 설정 ===")
        config["user"] = input("사용자명: ")
        config["password"] = input("비밀번호: ")
        host = input("호스트 (기본값: localhost): ") or "localhost"
        port = input("포트 (기본값: 1521): ") or "1521"
        service_name = input("서비스명 (기본값: XE): ") or "XE"
        config["dsn"] = f"{host}:{port}/{service_name}"
    
    return config


def main():
    """메인 실행 함수"""
    generator = DummyDataGenerator()
    
    print("=== 더미데이터 생성 프로그램 ===")
    print("1. JSON 파일로 저장")
    print("2. CSV 파일로 저장")
    print("3. SQLite 데이터베이스로 저장")
    print("4. MySQL 데이터베이스로 저장")
    print("5. Oracle 데이터베이스로 저장")
    print("6. 모든 형식으로 저장")
    
    choice = input("선택하세요 (1-6): ")
    count = int(input("생성할 레코드 수를 입력하세요 (기본값: 100): ") or "100")
    
    # 데이터 생성
    print(f"\n{count}개의 더미데이터를 생성 중...")
    data = generator.generate_batch(count)
    print("데이터 생성 완료!")
    
    # 선택에 따른 저장
    if choice == "1":
        generator.save_to_json(data)
    elif choice == "2":
        generator.save_to_csv(data)
    elif choice == "3":
        generator.save_to_sqlite(data)
    elif choice == "4":
        mysql_config = get_database_config("mysql")
        generator.save_to_mysql(data, mysql_config)
    elif choice == "5":
        oracle_config = get_database_config("oracle")
        generator.save_to_oracle(data, oracle_config)
    elif choice == "6":
        generator.save_to_json(data)
        generator.save_to_csv(data)
        generator.save_to_sqlite(data)
        
        # MySQL과 Oracle 설정도 입력받기
        print("\n" + "="*50)
        print("MySQL 설정을 입력하세요:")
        mysql_config = get_database_config("mysql")
        generator.save_to_mysql(data, mysql_config)
        
        print("\n" + "="*50)
        print("Oracle 설정을 입력하세요:")
        oracle_config = get_database_config("oracle")
        generator.save_to_oracle(data, oracle_config)
        
        print("\n모든 형식으로 저장 완료!")
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main() 