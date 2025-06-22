import json
import argparse
from datetime import timedelta

def analyze_scan_preview(file_path: str):
    """
    데이터베이스 구조 분석 JSON 파일을 읽어 요약 정보를 출력하고,
    처리 비용이 높은 테이블을 식별하여 리포트를 생성합니다.

    Args:
        file_path (str): 분석할 JSON 파일의 경로
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            analyses = json.load(f)
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        print("💡 파일 경로를 다시 확인해주세요.")
        return
    except json.JSONDecodeError:
        print(f"❌ JSON 파싱 오류: {file_path} 파일이 유효한 JSON 형식이 아닙니다.")
        return

    print("=" * 80)
    print("📊 Polars 데이터베이스 구조 분석 리포트")
    print(f"📄 분석 파일: {file_path}")
    print("=" * 80)

    # 1. 전체 통계 요약
    total_db_count = len(analyses)
    db_names = [db.get('database', 'Unknown') for db in analyses]
    total_summary = {
        'tables': sum(db.get('summary', {}).get('total_tables', 0) for db in analyses),
        'rows': sum(db.get('summary', {}).get('total_rows', 0) for db in analyses),
        'columns': sum(db.get('summary', {}).get('total_columns', 0) for db in analyses),
        'scannable_tables': sum(db.get('summary', {}).get('scannable_tables', 0) for db in analyses),
        'large_tables': sum(db.get('summary', {}).get('large_tables', 0) for db in analyses),
        'est_mb': sum(db.get('summary', {}).get('estimated_total_mb', 0) for db in analyses),
        'est_time_sec': sum(db.get('summary', {}).get('estimated_total_scan_time_sec', 0) for db in analyses),
    }

    # 테이블 상태별 분류
    scannable_tables_list = []
    empty_tables_list = []
    error_tables_list = []

    for db in analyses:
        db_name = db.get('database', 'Unknown')
        for table_name, table_data in db.get('tables', {}).items():
            full_table_name = f"{db_name}.{table_name}"
            status = table_data.get('status')
            if status == 'scannable':
                scannable_tables_list.append(full_table_name)
            elif status == 'empty':
                empty_tables_list.append(full_table_name)
            elif status == 'error':
                error_msg = table_data.get('error', 'Unknown error')
                error_tables_list.append({'name': full_table_name, 'error': error_msg})

    print("📈 전체 규모 요약")
    print(f"  • 데이터베이스: {total_db_count}개 ({', '.join(db_names)})")
    print(f"  • 총 테이블: {total_summary['tables']:,}개")
    print(f"    - 🟢 스캔 가능: {len(scannable_tables_list):,}개")
    if empty_tables_list:
        print(f"    - 🟡 스캔 제외 (빈 테이블): {len(empty_tables_list):,}개")
    if error_tables_list:
        print(f"    - 🔴 스캔 오류: {len(error_tables_list):,}개")

    print(f"  • 총 행 수 (스캔 가능 테이블 기준): {total_summary['rows']:,}행")
    print(f"  • 총 컬럼 수: {total_summary['columns']:,}개")
    print(f"  • 대용량 테이블 (100만 행 이상): {total_summary['large_tables']:,}개")
    print("-" * 40)
    
    # 2. 예상 처리 비용 분석
    est_time = timedelta(seconds=int(total_summary['est_time_sec']))
    print("💾 예상 처리 비용 (Polars 엔진)")
    print(f"  • 예상 메모리 사용량 (샘플링 기반): {total_summary['est_mb']:.2f} MB")
    print(f"  • 예상 총 스캔 시간: {str(est_time)} ({total_summary['est_time_sec']:.2f}초)")
    print("-" * 80)

    # 스캔 제외 테이블 정보 출력
    if empty_tables_list or error_tables_list:
        print("ℹ️ 스캔에서 제외된 테이블 상세 정보")
        if empty_tables_list:
            print(f"  [빈 테이블] ({len(empty_tables_list)}개) - 데이터가 없어 스캔에서 제외됩니다.")
            tables_to_show = empty_tables_list[:5]
            for t in tables_to_show:
                print(f"    - {t}")
            if len(empty_tables_list) > 5:
                print(f"    ... 외 {len(empty_tables_list) - 5}개")
        
        if error_tables_list:
            print(f"\n  [분석 오류 테이블] ({len(error_tables_list)}개) - 구조 분석 중 오류가 발생했습니다.")
            tables_to_show = error_tables_list[:5]
            for t in tables_to_show:
                error_preview = t['error'].replace('\n', ' ').strip()[:70]
                print(f"    - {t['name']}: {error_preview}...")
            if len(error_tables_list) > 5:
                print(f"    ... 외 {len(error_tables_list) - 5}개")
        print("-" * 80)

    # 3. 비용 높은 테이블 식별
    high_cost_tables = []
    for db in analyses:
        db_name = db.get('database', 'Unknown')
        for table_name, table_data in db.get('tables', {}).items():
            is_large = table_data.get('total_rows', 0) >= 1000000
            is_slow = table_data.get('time_estimate', {}).get('total_estimated_sec', 0) > 30
            
            if is_large or is_slow:
                high_cost_tables.append({
                    'db': db_name,
                    'table': table_name,
                    'rows': table_data.get('total_rows', 0),
                    'cols': table_data.get('total_columns', 0),
                    'mb': table_data.get('size_estimate', {}).get('estimated_mb', 0),
                    'time_sec': table_data.get('time_estimate', {}).get('total_estimated_sec', 0),
                    'reason': "대용량" if is_large and not is_slow else "처리 시간 김" if is_slow and not is_large else "대용량 & 처리 시간 김"
                })

    if high_cost_tables:
        print("⚠️  주요 검토 대상 테이블 (상위 15개)")
        print("   (행 수가 많거나, 예상 처리 시간이 긴 테이블)")
        
        # 행 수 기준으로 정렬하여 상위 15개만 표시
        sorted_tables = sorted(high_cost_tables, key=lambda x: x['rows'], reverse=True)
        
        # 헤더 출력
        print("-" * 80)
        print(f"  {'#':<3} {'Database':<20} {'Table':<25} {'Rows':>12} {'Time (sec)':>12}")
        print("-" * 80)

        for i, t in enumerate(sorted_tables[:15], 1):
            print(f"  {i:<3} {t['db']:<20} {t['table']:<25} {t['rows']:,>12} {t['time_sec']:>12.2f}")
        
        if len(sorted_tables) > 15:
            print(f"  ... 외 {len(sorted_tables) - 15}개의 테이블이 더 있습니다.")
    else:
        print("✅ 특별히 주의가 필요한 대용량 또는 처리 시간이 긴 테이블은 없습니다.")
    print("-" * 80)
    
    # 4. 스캔 실행 권장사항
    print("💡 스캔 실행 권장사항")
    
    # 메모리 위험도 평가
    if total_summary['est_mb'] > 1024:
        print(f"  🔴 [메모리] 예상 메모리 사용량({total_summary['est_mb']:.1f}MB)이 높습니다. 서버 사양을 확인하거나 샘플 크기를 줄이세요.")
    elif total_summary['est_mb'] > 512:
        print(f"  🟡 [메모리] 예상 메모리 사용량({total_summary['est_mb']:.1f}MB)이 다소 높습니다. 실행 시 모니터링이 필요합니다.")
    else:
        print(f"  🟢 [메모리] 예상 메모리 사용량({total_summary['est_mb']:.1f}MB)은 안정적인 수준입니다.")

    # 시간 위험도 평가
    if total_summary['est_time_sec'] > 1800: # 30분
        print(f"  🔴 [시간] 예상 처리 시간({str(est_time)})이 매우 깁니다. 중요한 DB부터 나누어 실행하거나, 대용량 테이블을 제외하고 스캔하세요.")
    elif total_summary['est_time_sec'] > 600: # 10분
        print(f"  🟡 [시간] 예상 처리 시간({str(est_time)})이 다소 깁니다. 업무 영향이 적은 시간에 실행하는 것을 권장합니다.")
    else:
        print(f"  🟢 [시간] 예상 처리 시간({str(est_time)})은 양호한 수준입니다.")

    if not high_cost_tables and total_summary['est_mb'] <= 512 and total_summary['est_time_sec'] <= 600:
        print("\n✅ 전체적으로 처리 비용이 낮아 보입니다. 전체 스캔을 바로 진행해도 좋습니다.")

    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Polars DB 구조 분석(.json) 파일을 읽고 요약 리포트를 생성합니다.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="분석할 polars_db_analysis_{timestamp}.json 파일의 경로"
    )
    
    args = parser.parse_args()
    analyze_scan_preview(args.file_path) 