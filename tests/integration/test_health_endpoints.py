import pytest
import time
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch
from src.api import v1_api_router
from src.composer import Composer
from src.downstream_controller import DownstreamController


# Create a simple test app with just the API router
def create_test_app():
    """Create a fresh test app instance"""
    app = FastAPI()
    app.include_router(v1_api_router)
    return app


@pytest.fixture
def mock_downstream_controller():
    """Create a mock downstream controller"""
    controller = Mock(spec=DownstreamController)
    controller.is_initialized.return_value = True
    controller.list_all_servers_tools.return_value = []
    return controller


@pytest.fixture
def mock_composer(mock_downstream_controller):
    """Create a mock composer with downstream controller"""
    composer = Mock(spec=Composer)
    composer.downstream_controller = mock_downstream_controller
    composer.gateway_map = {}
    
    # Configure the sync method to return empty list
    composer.list_gateways = Mock(return_value=[])
    
    return composer


@pytest.fixture
def client_with_mock_composer(mock_composer):
    """Create test client with mocked composer"""
    app = create_test_app()
    app.state.composer = mock_composer
    return TestClient(app)


class TestHealthEndpoints:
    """Test suite for health check endpoints"""

    def test_basic_health_endpoint(self):
        """Test basic health endpoint"""
        client = TestClient(create_test_app())
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_liveness_probe_success(self):
        """Test liveness probe returns success"""
        client = TestClient(create_test_app())
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "uptime" in data
        assert data["uptime"] >= 0

    def test_readiness_probe_success(self, client_with_mock_composer):
        """Test readiness probe returns success when properly initialized"""
        response = client_with_mock_composer.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "timestamp" in data
        assert "downstream_servers" in data
        assert "active_gateways" in data

    def test_readiness_probe_failure_no_composer(self):
        """Test readiness probe fails when composer is not available"""
        client = TestClient(create_test_app())
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        assert "Composer not available" in response.json()["detail"]

    def test_readiness_probe_failure_not_initialized(self, client_with_mock_composer, mock_composer):
        """Test readiness probe fails when downstream controller is not initialized"""
        mock_composer.downstream_controller.is_initialized.return_value = False
        
        response = client_with_mock_composer.get("/api/v1/health/ready")
        assert response.status_code == 503
        assert "not initialized" in response.json()["detail"]

    def test_startup_probe_success(self, client_with_mock_composer):
        """Test startup probe returns success when properly started"""
        # Mock the app start time to simulate app has been running for more than 1 second
        with patch('src.api._app_start_time', time.time() - 2.0):
            response = client_with_mock_composer.get("/api/v1/health/startup")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"
            assert "timestamp" in data
            assert "startup_duration" in data
            assert "downstream_servers_initialized" in data
            assert data["startup_duration"] > 1.0

    def test_startup_probe_failure_no_composer(self):
        """Test startup probe fails when composer is not available"""
        client = TestClient(create_test_app())
        response = client.get("/api/v1/health/startup")
        assert response.status_code == 503
        assert "still starting up" in response.json()["detail"]

    def test_startup_probe_failure_not_initialized(self, client_with_mock_composer, mock_composer):
        """Test startup probe fails when downstream controller is not initialized"""
        mock_composer.downstream_controller.is_initialized.return_value = False
        
        response = client_with_mock_composer.get("/api/v1/health/startup")
        assert response.status_code == 503
        assert "initialization in progress" in response.json()["detail"]

    def test_startup_probe_failure_too_early(self, client_with_mock_composer):
        """Test startup probe fails when called too early (< 1 second after start)"""
        # Mock the app start time to simulate app started less than 1 second ago
        with patch('src.api._app_start_time', time.time() - 0.5):
            response = client_with_mock_composer.get("/api/v1/health/startup")
            assert response.status_code == 503
            assert "startup in progress" in response.json()["detail"]

    def test_all_health_endpoints_return_json(self, client_with_mock_composer):
        """Test that all health endpoints return valid JSON"""
        endpoints = [
            "/api/v1/health",
            "/api/v1/health/live", 
            "/api/v1/health/ready",
            "/api/v1/health/startup"
        ]
        
        # Mock the app start time for startup endpoint
        with patch('src.api._app_start_time', time.time() - 2.0):
            for endpoint in endpoints:
                response = client_with_mock_composer.get(endpoint)
                assert response.status_code == 200
                # Verify it's valid JSON
                data = response.json()
                assert isinstance(data, dict)
                assert "status" in data
                assert "timestamp" in data

    def test_health_endpoints_performance(self, client_with_mock_composer):
        """Test that health endpoints respond quickly"""
        endpoints = [
            "/api/v1/health/live",
            "/api/v1/health/ready"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client_with_mock_composer.get(endpoint)
            end_time = time.time()
            
            assert response.status_code == 200
            # Health checks should be fast (< 100ms)
            assert (end_time - start_time) < 0.1

    def test_nonexistent_health_endpoint(self, client_with_mock_composer):
        """Test that non-existent health endpoints return 404"""
        response = client_with_mock_composer.get("/api/v1/health/nonexistent")
        assert response.status_code == 404
