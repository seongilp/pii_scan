import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
from datetime import datetime
import re
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="개인정보 스캔 대시보드",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .high-risk {
        border-left-color: #ff4444 !important;
        background-color: #fff5f5;
    }
    .medium-risk {
        border-left-color: #ff8800 !important;
        background-color: #fff8f0;
    }
    .low-risk {
        border-left-color: #00cc44 !important;
        background-color: #f0fff5;
    }
</style>
""", unsafe_allow_html=True)


# 데이터 마스킹 함수
def mask_sensitive_data(text):
    """민감한 데이터 마스킹"""
    if not isinstance(text, str):
        return text

    # 이메일 마스킹
    text = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                  lambda m: f"{m.group(1)[:2]}***@{m.group(2)}", text)

    # 전화번호 마스킹
    text = re.sub(r'(\d{2,3})-(\d{3,4})-(\d{4})', r'\1-***-\3', text)

    # 주민등록번호 마스킹
    text = re.sub(r'(\d{6})-([1-4])(\d{6})', r'\1-\2******', text)

    # 카드번호 마스킹
    text = re.sub(r'(\d{4})-(\d{4})-(\d{4})-(\d{4})', r'\1-****-****-\4', text)

    return text


# 위험도 색상 매핑
def get_risk_color(risk_level):
    colors = {
        'HIGH': '#ff4444',
        'MEDIUM': '#ff8800',
        'LOW': '#00cc44',
        'EMPTY': '#cccccc',
        'ERROR': '#ff0000'
    }
    return colors.get(risk_level, '#cccccc')


# 메인 헤더
st.markdown('<h1 class="main-header">🔍 개인정보 스캔 대시보드</h1>', unsafe_allow_html=True)

# 사이드바
st.sidebar.title("📁 데이터 로드")

# 파일 업로드
uploaded_file = st.sidebar.file_uploader(
    "스캔 결과 JSON 파일 업로드",
    type=['json'],
    help="Polars 개인정보 스캐너에서 생성된 JSON 파일을 업로드하세요."
)

# 샘플 데이터 로드 옵션
if st.sidebar.button("🎲 샘플 데이터 사용"):
    # 샘플 데이터 생성
    sample_data = {
        "database": "sample_db",
        "scan_time": "2024-12-21T14:30:22",
        "engine": "Polars",
        "sample_size": 100,
        "summary": {
            "total_tables": 12,
            "scanned_tables": 12,
            "high_risk_tables": 3,
            "medium_risk_tables": 4,
            "low_risk_tables": 5,
            "total_privacy_score": 89,
            "total_data_rows": 1250000,
            "total_sampled_rows": 1200
        },
        "tables": {
            "users": {
                "risk_level": "HIGH",
                "privacy_score": 32,
                "sampling_info": {
                    "total_rows": 500000,
                    "sampled_rows": 100,
                    "method": "랜덤 샘플링"
                },
                "columns": {
                    "name": {
                        "type": "Utf8",
                        "suspicious_name": True,
                        "pattern_scan": None
                    },
                    "email": {
                        "type": "Utf8",
                        "suspicious_name": True,
                        "pattern_scan": {
                            "privacy_matches": {"email": 98},
                            "privacy_ratio": 0.98,
                            "sample_values": ["ki***@test.com", "le***@gmail.com"]
                        }
                    },
                    "phone": {
                        "type": "Utf8",
                        "suspicious_name": True,
                        "pattern_scan": {
                            "privacy_matches": {"phone": 95},
                            "privacy_ratio": 0.95,
                            "sample_values": ["010-***-5678", "02-***-6543"]
                        }
                    }
                }
            },
            "orders": {
                "risk_level": "MEDIUM",
                "privacy_score": 15,
                "sampling_info": {
                    "total_rows": 300000,
                    "sampled_rows": 100,
                    "method": "랜덤 샘플링"
                },
                "columns": {
                    "customer_email": {
                        "type": "Utf8",
                        "suspicious_name": True,
                        "pattern_scan": {
                            "privacy_matches": {"email": 89},
                            "privacy_ratio": 0.89,
                            "sample_values": ["cu***@shop.com", "bu***@store.com"]
                        }
                    }
                }
            },
            "products": {
                "risk_level": "LOW",
                "privacy_score": 0,
                "sampling_info": {
                    "total_rows": 50000,
                    "sampled_rows": 50,
                    "method": "전체 데이터"
                },
                "columns": {
                    "product_name": {
                        "type": "Utf8",
                        "suspicious_name": False,
                        "pattern_scan": {
                            "privacy_matches": {},
                            "privacy_ratio": 0.0
                        }
                    }
                }
            }
        }
    }
    st.session_state.scan_data = sample_data
    st.sidebar.success("✅ 샘플 데이터 로드 완료!")
    st.rerun()  # 페이지 새로고침으로 데이터 반영

# 데이터 로드
scan_data = None
if uploaded_file is not None:
    try:
        loaded_data = json.load(uploaded_file)

        # JSON이 배열인 경우 첫 번째 요소 사용
        if isinstance(loaded_data, list) and len(loaded_data) > 0:
            scan_data = loaded_data[0]
            st.sidebar.success(f"✅ 파일 로드 완료! (배열에서 첫 번째 데이터 사용)")
        elif isinstance(loaded_data, dict):
            scan_data = loaded_data
            st.sidebar.success("✅ 파일 로드 완료!")
        else:
            st.sidebar.error("❌ 지원되지 않는 JSON 형식입니다.")
            scan_data = None

        if scan_data:
            st.session_state.scan_data = scan_data

    except json.JSONDecodeError as e:
        st.sidebar.error(f"❌ JSON 파싱 오류: {str(e)}")
    except Exception as e:
        st.sidebar.error(f"❌ 파일 로드 실패: {str(e)}")

# 세션 상태에서 데이터 가져오기
if 'scan_data' in st.session_state:
    scan_data = st.session_state.scan_data

# 데이터가 없으면 초기 화면 표시
if scan_data is None:
    st.info("👆 사이드바에서 JSON 파일을 업로드하거나 샘플 데이터를 사용해보세요.")

    # 샘플 스크린샷이나 설명 추가
    st.markdown("""
    ### 🔍 개인정보 스캔 대시보드 사용법

    1. **사이드바**에서 JSON 파일을 업로드하거나
    2. **"🎲 샘플 데이터 사용"** 버튼을 클릭하세요

    ### 📊 대시보드 기능
    - **개요**: 전체 위험도 요약 및 통계
    - **테이블 분석**: 테이블별 상세 개인정보 탐지 결과  
    - **패턴 분석**: 이메일, 전화번호 등 패턴별 분석
    - **설정**: 데이터 내보내기 및 표시 옵션
    """)

    st.stop()

# 메인 대시보드 - 데이터가 있을 때만 실행
try:
    summary = scan_data.get('summary', {})
    tables_data = scan_data.get('tables', {})

    # 데이터 유효성 검사
    if not isinstance(scan_data, dict):
        st.error("❌ 잘못된 데이터 형식입니다. 올바른 JSON 파일을 업로드해주세요.")
        st.stop()

    # 필수 키 확인 (summary는 선택사항으로 변경)
    if 'tables' not in scan_data:
        st.error("❌ 'tables' 데이터가 없습니다. Polars 스캐너에서 생성된 JSON 파일을 사용해주세요.")
        st.stop()

    # summary가 없는 경우 기본값 생성
    if not summary:
        # tables 데이터에서 summary 계산
        high_risk = sum(1 for t in tables_data.values() if t.get('risk_level') == 'HIGH')
        medium_risk = sum(1 for t in tables_data.values() if t.get('risk_level') == 'MEDIUM')
        low_risk = sum(1 for t in tables_data.values() if t.get('risk_level') == 'LOW')
        total_score = sum(t.get('privacy_score', 0) for t in tables_data.values())
        total_data_rows = sum(t.get('sampling_info', {}).get('total_rows', 0) for t in tables_data.values())
        total_sampled_rows = sum(t.get('sampling_info', {}).get('sampled_rows', 0) for t in tables_data.values())

        summary = {
            'total_tables': len(tables_data),
            'scanned_tables': len(tables_data),
            'high_risk_tables': high_risk,
            'medium_risk_tables': medium_risk,
            'low_risk_tables': low_risk,
            'total_privacy_score': total_score,
            'total_data_rows': total_data_rows,
            'total_sampled_rows': total_sampled_rows
        }

        st.info("📊 summary 데이터가 없어서 자동으로 계산했습니다.")

except AttributeError:
    st.error("❌ 잘못된 데이터 형식입니다. 올바른 JSON 파일을 업로드해주세요.")
    st.stop()
except Exception as e:
    st.error(f"❌ 데이터 처리 오류: {str(e)}")
    st.stop()

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["📊 개요", "📋 테이블 분석", "🔍 패턴 분석", "⚙️ 설정"])

with tab1:
    st.subheader("스캔 개요")

    # 기본 정보
    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(f"""
        **데이터베이스**: {scan_data.get('database', 'Unknown')}  
        **스캔 시간**: {scan_data.get('scan_time', 'Unknown')}  
        **처리 엔진**: {scan_data.get('engine', 'Unknown')}  
        **샘플 크기**: {scan_data.get('sample_size', 'Unknown')}건
        """)

    with col2:
        total_score = summary.get('total_privacy_score', 0)
        if total_score >= 50:
            score_color = "🔴"
        elif total_score >= 20:
            score_color = "🟡"
        else:
            score_color = "🟢"

        st.metric("전체 위험도", f"{score_color} {total_score}점")

    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "총 테이블",
            f"{summary.get('total_tables', 0):,}개"
        )

    with col2:
        st.metric(
            "고위험 테이블",
            f"{summary.get('high_risk_tables', 0)}개",
            delta=f"위험도 {total_score}점"
        )

    with col3:
        st.metric(
            "스캔된 행 수",
            f"{summary.get('total_sampled_rows', 0):,}행",
            delta=f"전체 {summary.get('total_data_rows', 0):,}행"
        )

    with col4:
        sampling_ratio = 0
        if summary.get('total_data_rows', 0) > 0:
            sampling_ratio = summary.get('total_sampled_rows', 0) / summary.get('total_data_rows', 0) * 100

        st.metric(
            "샘플링 비율",
            f"{sampling_ratio:.2f}%"
        )

    # 위험도 분포 차트
    st.subheader("테이블 위험도 분포")

    col1, col2 = st.columns([2, 1])

    with col1:
        # 도넛 차트
        risk_counts = [
            summary.get('high_risk_tables', 0),
            summary.get('medium_risk_tables', 0),
            summary.get('low_risk_tables', 0)
        ]
        risk_labels = ['고위험', '중간위험', '저위험']
        risk_colors = ['#ff4444', '#ff8800', '#00cc44']

        fig_donut = go.Figure(data=[go.Pie(
            labels=risk_labels,
            values=risk_counts,
            hole=0.4,
            marker_colors=risk_colors
        )])

        fig_donut.update_layout(
            title="테이블 위험도 분포",
            height=400
        )

        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        # 위험도 레벨별 정보
        st.markdown("### 위험도 레벨")

        for level, count, color in zip(risk_labels, risk_counts, risk_colors):
            if count > 0:
                st.markdown(f"""
                <div style="background-color: {color}22; padding: 0.5rem; border-radius: 0.25rem; margin-bottom: 0.5rem; border-left: 4px solid {color};">
                    <strong>{level}</strong>: {count}개
                </div>
                """, unsafe_allow_html=True)

with tab2:
    st.subheader("테이블별 상세 분석")

    # 테이블 데이터 준비
    table_list = []
    for table_name, table_info in tables_data.items():
        sampling_info = table_info.get('sampling_info', {})
        table_list.append({
            'Table': table_name,
            'Risk Level': table_info.get('risk_level', 'UNKNOWN'),
            'Privacy Score': table_info.get('privacy_score', 0),
            'Total Rows': f"{sampling_info.get('total_rows', 0):,}",
            'Sampled Rows': sampling_info.get('sampled_rows', 0),
            'Sampling Method': sampling_info.get('method', 'Unknown')
        })

    if table_list:
        # 정렬 옵션
        sort_by = st.selectbox("정렬 기준", ["Privacy Score", "Risk Level", "Total Rows"])

        df_tables = pd.DataFrame(table_list)

        if sort_by == "Privacy Score":
            df_tables = df_tables.sort_values('Privacy Score', ascending=False)

        # 테이블 표시 (위험도별 색상)
        for idx, row in df_tables.iterrows():
            risk_level = row['Risk Level']
            color = get_risk_color(risk_level)

            with st.expander(f"📋 {row['Table']} (위험도: {risk_level}, 점수: {row['Privacy Score']})"):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.write(f"**총 행 수**: {row['Total Rows']}")
                    st.write(f"**샘플링된 행 수**: {row['Sampled Rows']}")
                    st.write(f"**샘플링 방법**: {row['Sampling Method']}")

                with col2:
                    st.write(f"**위험도 레벨**: {risk_level}")
                    st.write(f"**개인정보 점수**: {row['Privacy Score']}")

                # 컬럼별 상세 정보
                table_info = tables_data[row['Table']]
                columns_info = table_info.get('columns', {})

                if columns_info:
                    st.write("**컬럼별 개인정보 탐지 결과**:")

                    col_data = []
                    for col_name, col_info in columns_info.items():
                        pattern_scan = col_info.get('pattern_scan', {})
                        privacy_matches = pattern_scan.get('privacy_matches', {}) if pattern_scan else {}
                        privacy_ratio = pattern_scan.get('privacy_ratio', 0) if pattern_scan else 0

                        col_data.append({
                            'Column': col_name,
                            'Type': col_info.get('type', 'Unknown'),
                            'Suspicious Name': '⚠️' if col_info.get('suspicious_name') else '✅',
                            'Privacy Patterns': ', '.join([f"{k}({v})" for k, v in privacy_matches.items()]) or 'None',
                            'Privacy Ratio': f"{privacy_ratio:.1%}" if privacy_ratio > 0 else '0%'
                        })

                    if col_data:
                        df_cols = pd.DataFrame(col_data)
                        st.dataframe(df_cols, use_container_width=True)

with tab3:
    st.subheader("개인정보 패턴 분석")

    # 패턴별 통계 수집
    pattern_stats = {}

    for table_name, table_info in tables_data.items():
        columns_info = table_info.get('columns', {})
        for col_name, col_info in columns_info.items():
            pattern_scan = col_info.get('pattern_scan', {})
            if pattern_scan and 'privacy_matches' in pattern_scan:
                privacy_matches = pattern_scan['privacy_matches']
                for pattern, count in privacy_matches.items():
                    if pattern not in pattern_stats:
                        pattern_stats[pattern] = []
                    pattern_stats[pattern].append({
                        'table': table_name,
                        'column': col_name,
                        'count': count,
                        'ratio': pattern_scan.get('privacy_ratio', 0)
                    })

    if pattern_stats:
        # 패턴별 요약
        pattern_summary = {}
        for pattern, occurrences in pattern_stats.items():
            total_count = sum(occ['count'] for occ in occurrences)
            avg_ratio = sum(occ['ratio'] for occ in occurrences) / len(occurrences)
            pattern_summary[pattern] = {
                'total_count': total_count,
                'avg_ratio': avg_ratio,
                'tables_affected': len(set(occ['table'] for occ in occurrences))
            }

        col1, col2 = st.columns(2)

        with col1:
            # 패턴별 발견 건수
            patterns = list(pattern_summary.keys())
            counts = [pattern_summary[p]['total_count'] for p in patterns]

            fig_bar = px.bar(
                x=patterns,
                y=counts,
                title="패턴별 개인정보 발견 건수",
                labels={'x': '패턴 타입', 'y': '발견 건수'}
            )
            fig_bar.update_traces(marker_color='#1f77b4')
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            # 패턴별 평균 비율
            ratios = [pattern_summary[p]['avg_ratio'] * 100 for p in patterns]

            fig_ratio = px.bar(
                x=patterns,
                y=ratios,
                title="패턴별 평균 포함 비율",
                labels={'x': '패턴 타입', 'y': '평균 비율 (%)'}
            )
            fig_ratio.update_traces(marker_color='#ff7f0e')
            st.plotly_chart(fig_ratio, use_container_width=True)

        # 상세 패턴 정보
        st.subheader("패턴별 상세 정보")

        for pattern, info in pattern_summary.items():
            with st.expander(f"🔍 {pattern.upper()} 패턴"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("총 발견 건수", f"{info['total_count']:,}건")

                with col2:
                    st.metric("평균 포함 비율", f"{info['avg_ratio']:.1%}")

                with col3:
                    st.metric("영향받은 테이블", f"{info['tables_affected']}개")

                # 해당 패턴이 발견된 테이블/컬럼 목록
                pattern_details = pattern_stats[pattern]
                pattern_df = pd.DataFrame([
                    {
                        'Table': detail['table'],
                        'Column': detail['column'],
                        'Count': detail['count'],
                        'Ratio': f"{detail['ratio']:.1%}"
                    }
                    for detail in pattern_details
                ])

                st.dataframe(pattern_df, use_container_width=True)
    else:
        st.info("패턴 분석 데이터가 없습니다.")

with tab4:
    st.subheader("설정 및 도구")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 데이터 내보내기")

        if st.button("📥 CSV로 내보내기"):
            # 테이블 요약 데이터 CSV 생성
            if scan_data and tables_data:
                # 테이블 데이터 다시 생성 (안전하게)
                safe_table_list = []
                for table_name, table_info in tables_data.items():
                    try:
                        sampling_info = table_info.get('sampling_info', {})
                        safe_table_list.append({
                            'Table': table_name,
                            'Risk Level': table_info.get('risk_level', 'UNKNOWN'),
                            'Privacy Score': table_info.get('privacy_score', 0),
                            'Total Rows': f"{sampling_info.get('total_rows', 0):,}",
                            'Sampled Rows': sampling_info.get('sampled_rows', 0),
                            'Sampling Method': sampling_info.get('method', 'Unknown')
                        })
                    except Exception as e:
                        st.warning(f"테이블 {table_name} 처리 중 오류: {str(e)}")
                        continue

                if safe_table_list:
                    df_export = pd.DataFrame(safe_table_list)
                    csv_data = df_export.to_csv(index=False)

                    st.download_button(
                        label="다운로드 CSV",
                        data=csv_data,
                        file_name=f"privacy_scan_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("내보낼 데이터가 없습니다.")
            else:
                st.error("스캔 데이터를 먼저 로드해주세요.")

        if st.button("📄 JSON 원본 다운로드"):
            if scan_data:
                try:
                    json_data = json.dumps(scan_data, ensure_ascii=False, indent=2)

                    st.download_button(
                        label="다운로드 JSON",
                        data=json_data,
                        file_name=f"privacy_scan_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"JSON 생성 오류: {str(e)}")
            else:
                st.error("스캔 데이터를 먼저 로드해주세요.")

    with col2:
        st.markdown("### ⚙️ 표시 설정")

        show_masked = st.checkbox("민감정보 마스킹 표시", value=True)
        show_empty_tables = st.checkbox("빈 테이블 표시", value=False)

    # 설정 페이지에서도 데이터 확인
    if scan_data and isinstance(scan_data, dict):
        st.markdown("### 📈 통계")
        st.write(f"**스캔 완료 시간**: {scan_data.get('scan_time', 'Unknown')}")
        st.write(f"**처리된 데이터베이스**: 1개")
        st.write(f"**처리된 테이블**: {summary.get('scanned_tables', 0)}개")
        processing_time = scan_data.get('processing_time', 'Unknown')
        st.write(f"**처리 시간**: {processing_time}")
    else:
        st.info("스캔 데이터를 먼저 로드해주세요.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
        🔍 Polars 기반 개인정보 스캔 대시보드 | 
        Made with ❤️ using Streamlit & Plotly
    </div>
    """,
    unsafe_allow_html=True
)