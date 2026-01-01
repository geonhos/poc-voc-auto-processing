"""
Performance Tests
성능 테스트 - 응답 시간 측정
"""

import pytest
import time
import asyncio
from datetime import datetime
from httpx import AsyncClient

from app.models.ticket import Channel

# Performance thresholds (in seconds)
API_RESPONSE_THRESHOLD = 1.0  # 1초 이내
AGENT_TIMEOUT_THRESHOLD = 60.0  # 60초 이내


class TestAPIPerformance:
    """API 응답 시간 테스트"""

    @pytest.mark.asyncio
    async def test_health_check_response_time(self, client: AsyncClient):
        """
        헬스체크 응답 시간 (목표: 100ms 이내)
        """
        start_time = time.time()
        response = await client.get("/health")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 0.1, f"Health check took {elapsed_time:.3f}s (threshold: 0.1s)"
        print(f"Health check response time: {elapsed_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_ticket_list_response_time(self, client: AsyncClient):
        """
        티켓 목록 조회 응답 시간 (목표: 1초 이내)
        """
        # 먼저 몇 개의 티켓 생성
        for i in range(5):
            voc_data = {
                "raw_voc": f"성능 테스트용 VOC {i+1}",
                "customer_name": f"테스트{i+1}",
                "channel": Channel.EMAIL.value,
                "received_at": datetime.now().isoformat(),
            }
            await client.post("/api/v1/voc", json=voc_data)

        # 목록 조회 시간 측정
        start_time = time.time()
        response = await client.get("/api/v1/tickets")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < API_RESPONSE_THRESHOLD, \
            f"Ticket list took {elapsed_time:.3f}s (threshold: {API_RESPONSE_THRESHOLD}s)"
        print(f"Ticket list response time: {elapsed_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_ticket_detail_response_time(self, client: AsyncClient):
        """
        티켓 상세 조회 응답 시간 (목표: 1초 이내)
        """
        # 티켓 생성
        voc_data = {
            "raw_voc": "성능 테스트용 상세 조회 VOC",
            "customer_name": "테스트",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }
        response = await client.post("/api/v1/voc", json=voc_data)
        ticket_id = response.json()["ticket_id"]

        # 상세 조회 시간 측정
        start_time = time.time()
        response = await client.get(f"/api/v1/tickets/{ticket_id}")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < API_RESPONSE_THRESHOLD, \
            f"Ticket detail took {elapsed_time:.3f}s (threshold: {API_RESPONSE_THRESHOLD}s)"
        print(f"Ticket detail response time: {elapsed_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_voc_creation_response_time(self, client: AsyncClient):
        """
        VOC 생성 응답 시간 (목표: 1초 이내)
        - 백그라운드 분석 제외, 티켓 생성만 측정
        """
        voc_data = {
            "raw_voc": "성능 테스트용 VOC 생성",
            "customer_name": "테스트",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }

        start_time = time.time()
        response = await client.post("/api/v1/voc", json=voc_data)
        elapsed_time = time.time() - start_time

        assert response.status_code == 201
        assert elapsed_time < API_RESPONSE_THRESHOLD, \
            f"VOC creation took {elapsed_time:.3f}s (threshold: {API_RESPONSE_THRESHOLD}s)"
        print(f"VOC creation response time: {elapsed_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_filtered_ticket_list_response_time(self, client: AsyncClient):
        """
        필터링된 티켓 목록 조회 응답 시간 (목표: 1초 이내)
        """
        start_time = time.time()
        response = await client.get("/api/v1/tickets?status=OPEN&urgency=high&page=1&limit=10")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < API_RESPONSE_THRESHOLD, \
            f"Filtered ticket list took {elapsed_time:.3f}s (threshold: {API_RESPONSE_THRESHOLD}s)"
        print(f"Filtered ticket list response time: {elapsed_time*1000:.2f}ms")


class TestConcurrentPerformance:
    """동시 요청 성능 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_ticket_list_requests(self, client: AsyncClient):
        """
        동시 티켓 목록 요청 (5개 동시 요청)
        """
        async def make_request():
            start = time.time()
            response = await client.get("/api/v1/tickets")
            elapsed = time.time() - start
            return response.status_code, elapsed

        # 5개 동시 요청
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # 모든 요청 성공 확인
        for status_code, elapsed in results:
            assert status_code == 200
            assert elapsed < API_RESPONSE_THRESHOLD

        avg_time = sum(elapsed for _, elapsed in results) / len(results)
        max_time = max(elapsed for _, elapsed in results)
        print(f"Concurrent requests - Avg: {avg_time*1000:.2f}ms, Max: {max_time*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_sequential_voc_creation(self, client: AsyncClient):
        """
        순차 VOC 생성 (3개 순차 요청)
        """
        results = []
        for idx in range(3):
            voc_data = {
                "raw_voc": f"순차 생성 테스트 VOC {idx}",
                "customer_name": f"테스트{idx}",
                "channel": Channel.EMAIL.value,
                "received_at": datetime.now().isoformat(),
            }
            start = time.time()
            response = await client.post("/api/v1/voc", json=voc_data)
            elapsed = time.time() - start
            results.append((response.status_code, elapsed))

        # 모든 요청 성공 확인
        for status_code, elapsed in results:
            assert status_code == 201
            assert elapsed < API_RESPONSE_THRESHOLD

        avg_time = sum(elapsed for _, elapsed in results) / len(results)
        print(f"Sequential VOC creation - Avg: {avg_time*1000:.2f}ms")


class TestLoadPerformance:
    """부하(가중치) 테스트"""

    @pytest.mark.asyncio
    async def test_weighted_load_test(self, client: AsyncClient):
        """
        가중치 부하 테스트
        - 다양한 요청 유형에 가중치를 적용하여 성능 측정
        - 실제 사용 패턴 시뮬레이션
        """
        # 가중치 정의 (실제 사용 패턴 기반)
        # - 목록 조회: 50% (가장 빈번)
        # - 상세 조회: 30%
        # - VOC 생성: 15%
        # - 헬스체크: 5%

        total_requests = 20
        weights = {
            "list": 10,      # 50%
            "detail": 6,     # 30%
            "create": 3,     # 15%
            "health": 1,     # 5%
        }

        results = {
            "list": [],
            "detail": [],
            "create": [],
            "health": [],
        }

        # 테스트용 티켓 생성
        voc_data = {
            "raw_voc": "부하 테스트용 VOC",
            "customer_name": "테스트",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }
        response = await client.post("/api/v1/voc", json=voc_data)
        ticket_id = response.json()["ticket_id"]

        # 목록 조회 (10회)
        for _ in range(weights["list"]):
            start = time.time()
            await client.get("/api/v1/tickets")
            results["list"].append(time.time() - start)

        # 상세 조회 (6회)
        for _ in range(weights["detail"]):
            start = time.time()
            await client.get(f"/api/v1/tickets/{ticket_id}")
            results["detail"].append(time.time() - start)

        # VOC 생성 (3회)
        for i in range(weights["create"]):
            voc_data["raw_voc"] = f"부하 테스트 VOC {i}"
            start = time.time()
            await client.post("/api/v1/voc", json=voc_data)
            results["create"].append(time.time() - start)

        # 헬스체크 (1회)
        for _ in range(weights["health"]):
            start = time.time()
            await client.get("/health")
            results["health"].append(time.time() - start)

        # 결과 분석
        print("\n" + "="*60)
        print("Weighted Load Test Results")
        print("="*60)

        weighted_total = 0
        for req_type, times in results.items():
            if times:
                avg = sum(times) / len(times)
                weight = weights[req_type]
                weighted_avg = avg * weight
                weighted_total += weighted_avg
                print(f"  {req_type:10} ({weight:2} reqs): Avg {avg*1000:6.2f}ms")
                assert avg < API_RESPONSE_THRESHOLD, f"{req_type} avg exceeded threshold"

        weighted_avg_total = weighted_total / total_requests
        print("-"*60)
        print(f"  Weighted Average: {weighted_avg_total*1000:.2f}ms")
        print("="*60)

        assert weighted_avg_total < API_RESPONSE_THRESHOLD, \
            f"Weighted average {weighted_avg_total:.3f}s exceeded threshold"

    @pytest.mark.asyncio
    async def test_burst_load_test(self, client: AsyncClient):
        """
        버스트 부하 테스트
        - 짧은 시간에 많은 요청 처리 능력 측정
        """
        burst_count = 10
        results = []

        start_total = time.time()

        for i in range(burst_count):
            start = time.time()
            response = await client.get("/api/v1/tickets")
            elapsed = time.time() - start
            results.append((response.status_code, elapsed))

        total_time = time.time() - start_total

        # 검증
        success_count = sum(1 for status, _ in results if status == 200)
        avg_time = sum(elapsed for _, elapsed in results) / len(results)
        max_time = max(elapsed for _, elapsed in results)

        print(f"\nBurst test ({burst_count} requests):")
        print(f"  Total time: {total_time*1000:.2f}ms")
        print(f"  Avg response: {avg_time*1000:.2f}ms")
        print(f"  Max response: {max_time*1000:.2f}ms")
        print(f"  Success rate: {success_count}/{burst_count}")

        assert success_count == burst_count, "Some requests failed"
        assert max_time < API_RESPONSE_THRESHOLD, "Max response time exceeded"

    @pytest.mark.asyncio
    async def test_stress_test_ticket_list(self, client: AsyncClient):
        """
        스트레스 테스트 - Ticket 목록
        - 반복 요청으로 응답 시간 안정성 확인
        """
        iterations = 15
        results = []

        for i in range(iterations):
            start = time.time()
            response = await client.get("/api/v1/tickets")
            elapsed = time.time() - start
            results.append(elapsed)
            assert response.status_code == 200

        avg_time = sum(results) / len(results)
        max_time = max(results)
        min_time = min(results)
        variance = sum((t - avg_time) ** 2 for t in results) / len(results)
        std_dev = variance ** 0.5

        print(f"\nStress test ({iterations} iterations):")
        print(f"  Min: {min_time*1000:.2f}ms")
        print(f"  Max: {max_time*1000:.2f}ms")
        print(f"  Avg: {avg_time*1000:.2f}ms")
        print(f"  Std Dev: {std_dev*1000:.2f}ms")

        # 응답 시간 안정성 검증 (표준편차가 평균의 50% 이하)
        assert std_dev < avg_time * 0.5, \
            f"Response time unstable: std_dev {std_dev:.3f}s > avg * 0.5 = {avg_time * 0.5:.3f}s"


class TestPerformanceSummary:
    """성능 테스트 요약"""

    @pytest.mark.asyncio
    async def test_performance_summary(self, client: AsyncClient):
        """
        전체 성능 요약
        """
        results = {}

        # 1. Health check
        start = time.time()
        await client.get("/health")
        results["health_check"] = time.time() - start

        # 2. VOC creation
        voc_data = {
            "raw_voc": "성능 요약 테스트용 VOC",
            "customer_name": "테스트",
            "channel": Channel.EMAIL.value,
            "received_at": datetime.now().isoformat(),
        }
        start = time.time()
        response = await client.post("/api/v1/voc", json=voc_data)
        results["voc_creation"] = time.time() - start
        ticket_id = response.json()["ticket_id"]

        # 3. Ticket list
        start = time.time()
        await client.get("/api/v1/tickets")
        results["ticket_list"] = time.time() - start

        # 4. Ticket detail
        start = time.time()
        await client.get(f"/api/v1/tickets/{ticket_id}")
        results["ticket_detail"] = time.time() - start

        # 출력
        print("\n" + "="*50)
        print("Performance Summary")
        print("="*50)
        for name, elapsed in results.items():
            status = "PASS" if elapsed < API_RESPONSE_THRESHOLD else "FAIL"
            print(f"  {name}: {elapsed*1000:.2f}ms [{status}]")
        print("="*50)

        # 검증
        for name, elapsed in results.items():
            assert elapsed < API_RESPONSE_THRESHOLD, \
                f"{name} exceeded threshold: {elapsed:.3f}s"
