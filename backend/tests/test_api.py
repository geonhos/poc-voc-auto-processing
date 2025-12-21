"""
API endpoint tests
"""

import pytest
from httpx import AsyncClient
from app.models.ticket import TicketStatus


@pytest.mark.integration
class TestHealthEndpoint:
    """Health check endpoint tests"""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert data["components"]["database"] == "healthy"


@pytest.mark.integration
class TestVOCEndpoint:
    """VOC input endpoint tests"""

    async def test_create_voc(self, client: AsyncClient, sample_voc_data):
        """Test VOC creation"""
        response = await client.post("/api/v1/voc", json=sample_voc_data)
        assert response.status_code == 201
        data = response.json()
        assert "ticket_id" in data
        assert data["status"] == TicketStatus.OPEN.value
        assert "message" in data

    async def test_create_voc_invalid_data(self, client: AsyncClient):
        """Test VOC creation with invalid data"""
        invalid_data = {
            "raw_voc": "",  # Empty VOC
            "customer_name": "테스트",
            "channel": "email",
            "received_at": "2024-01-01T00:00:00",
        }
        response = await client.post("/api/v1/voc", json=invalid_data)
        assert response.status_code == 422  # Validation error

    async def test_create_voc_missing_fields(self, client: AsyncClient):
        """Test VOC creation with missing required fields"""
        incomplete_data = {
            "raw_voc": "테스트 VOC",
            # Missing customer_name, channel, received_at
        }
        response = await client.post("/api/v1/voc", json=incomplete_data)
        assert response.status_code == 422


@pytest.mark.integration
class TestTicketEndpoints:
    """Ticket management endpoint tests"""

    async def test_list_tickets_empty(self, client: AsyncClient):
        """Test listing tickets when none exist"""
        response = await client.get("/api/v1/tickets")
        assert response.status_code == 200
        data = response.json()
        assert data["tickets"] == []
        assert data["total_count"] == 0
        assert data["page"] == 1
        assert data["total_pages"] == 0

    async def test_list_tickets_with_data(self, client: AsyncClient, sample_voc_data):
        """Test listing tickets after creating one"""
        # Create a ticket first
        create_response = await client.post("/api/v1/voc", json=sample_voc_data)
        assert create_response.status_code == 201

        # List tickets
        response = await client.get("/api/v1/tickets")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tickets"]) == 1
        assert data["total_count"] == 1
        assert data["total_pages"] == 1

    async def test_get_ticket_by_id(self, client: AsyncClient, sample_voc_data):
        """Test getting ticket details by ID"""
        # Create a ticket
        create_response = await client.post("/api/v1/voc", json=sample_voc_data)
        ticket_id = create_response.json()["ticket_id"]

        # Get ticket details
        response = await client.get(f"/api/v1/tickets/{ticket_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == ticket_id
        assert data["status"] == TicketStatus.OPEN.value
        assert data["raw_voc"] == sample_voc_data["raw_voc"]
        assert data["customer_name"] == sample_voc_data["customer_name"]

    async def test_get_ticket_not_found(self, client: AsyncClient):
        """Test getting non-existent ticket"""
        response = await client.get("/api/v1/tickets/VOC-99999999-9999")
        assert response.status_code == 404

    async def test_list_tickets_pagination(self, client: AsyncClient, sample_voc_data):
        """Test ticket list pagination"""
        # Create multiple tickets
        for i in range(5):
            await client.post("/api/v1/voc", json=sample_voc_data)

        # Test page 1 with limit 2
        response = await client.get("/api/v1/tickets?page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tickets"]) == 2
        assert data["total_count"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2
        assert data["total_pages"] == 3

    async def test_list_tickets_filter_by_status(
        self, client: AsyncClient, sample_voc_data
    ):
        """Test filtering tickets by status"""
        # Create a ticket
        await client.post("/api/v1/voc", json=sample_voc_data)

        # Filter by OPEN status
        response = await client.get("/api/v1/tickets?status=OPEN")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tickets"]) == 1
        assert data["tickets"][0]["status"] == TicketStatus.OPEN.value

        # Filter by non-existent status
        response = await client.get("/api/v1/tickets?status=DONE")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tickets"]) == 0
