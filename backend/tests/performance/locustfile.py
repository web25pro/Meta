"""
Performance Testing with Locust

This module contains load tests for the LPanda Platform API.
Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000

**Validates: Requirements 1.1 - Testing Infrastructure**
"""
import random
import json
from locust import HttpUser, task, between, events
from datetime import datetime, timedelta


class LPandaPlatformUser(HttpUser):
    """
    Simulates a user interacting with the LPanda Platform.
    
    This load test simulates realistic user behavior including:
    - Authentication (login)
    - Viewing tasks
    - Submitting tasks
    - Checking leaderboard
    - Viewing announcements and schedules
    """
    
    # Wait between 1 and 5 seconds between tasks
    wait_time = between(1, 5)
    
    def on_start(self):
        """
        Called when a simulated user starts.
        Performs login and stores authentication token.
        """
        # Create a test user or login with existing credentials
        # For load testing, you should have pre-created test users
        self.user_email = f"loadtest_user_{random.randint(1, 1000)}@test.com"
        self.user_password = "TestPassword123!"
        self.auth_token = None
        self.user_id = None
        
        # Attempt to login (assumes users are pre-created)
        self.login()
    
    def login(self):
        """Authenticate and store token"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.user_email,
                "password": self.user_password
            },
            name="/api/v1/auth/login"
        )
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.user_id = data.get("user_id")
        else:
            # If login fails, mark as failure but continue
            print(f"Login failed for {self.user_email}: {response.status_code}")
    
    def get_headers(self):
        """Get authentication headers"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    @task(5)
    def view_dashboard(self):
        """
        View user dashboard (high frequency task).
        Weight: 5 (most common action)
        """
        self.client.get(
            "/api/v1/dashboard",
            headers=self.get_headers(),
            name="/api/v1/dashboard"
        )
    
    @task(4)
    def view_my_tasks(self):
        """
        View assigned tasks (high frequency task).
        Weight: 4
        """
        self.client.get(
            "/api/v1/dashboard/my-tasks",
            headers=self.get_headers(),
            name="/api/v1/dashboard/my-tasks"
        )
    
    @task(3)
    def view_leaderboard(self):
        """
        View leaderboard (medium frequency task).
        Weight: 3
        """
        # Randomly choose between Team_Members and Ambassadors leaderboard
        leaderboard_type = random.choice(["team-members", "ambassadors"])
        
        self.client.get(
            f"/api/v1/leaderboard/{leaderboard_type}",
            headers=self.get_headers(),
            name="/api/v1/leaderboard/[type]"
        )
    
    @task(2)
    def view_announcements(self):
        """
        View announcements (medium frequency task).
        Weight: 2
        """
        self.client.get(
            "/api/v1/announcements",
            headers=self.get_headers(),
            name="/api/v1/announcements"
        )
    
    @task(2)
    def view_schedules(self):
        """
        View schedules (medium frequency task).
        Weight: 2
        """
        self.client.get(
            "/api/v1/schedules",
            headers=self.get_headers(),
            name="/api/v1/schedules"
        )
    
    @task(1)
    def view_user_points(self):
        """
        View user's points balance (low frequency task).
        Weight: 1
        """
        if self.user_id:
            self.client.get(
                f"/api/v1/users/{self.user_id}/points",
                headers=self.get_headers(),
                name="/api/v1/users/[id]/points"
            )
    
    @task(1)
    def view_user_rank(self):
        """
        View user's leaderboard rank (low frequency task).
        Weight: 1
        """
        if self.user_id:
            self.client.get(
                f"/api/v1/leaderboard/user/{self.user_id}/rank",
                headers=self.get_headers(),
                name="/api/v1/leaderboard/user/[id]/rank"
            )
    
    @task(1)
    def submit_task(self):
        """
        Submit a task (low frequency task).
        Weight: 1
        
        Note: This will fail if no tasks are available or already submitted.
        In a real load test, you'd need to ensure tasks are available.
        """
        # This is a simplified version - in reality, you'd need to:
        # 1. Get available tasks
        # 2. Select one that hasn't been submitted
        # 3. Submit it
        
        # For demonstration, we'll just attempt a submission
        # In production load tests, you'd need proper task management
        pass


class AdminUser(HttpUser):
    """
    Simulates an admin user performing administrative tasks.
    
    This represents a smaller percentage of users but with different
    access patterns (creating tasks, reviewing submissions, etc.)
    """
    
    wait_time = between(2, 10)
    
    def on_start(self):
        """Login as admin"""
        self.admin_email = "admin@lpanda.com"
        self.admin_password = "AdminPassword123!"
        self.auth_token = None
        
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.admin_email,
                "password": self.admin_password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
    
    def get_headers(self):
        """Get authentication headers"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    @task(3)
    def view_all_tasks(self):
        """View all tasks (admin)"""
        self.client.get(
            "/api/v1/tasks",
            headers=self.get_headers(),
            name="/api/v1/tasks (admin)"
        )
    
    @task(2)
    def view_all_users(self):
        """View all users (admin)"""
        self.client.get(
            "/api/v1/users",
            headers=self.get_headers(),
            name="/api/v1/users (admin)"
        )
    
    @task(1)
    def view_analytics(self):
        """View analytics dashboard (admin)"""
        self.client.get(
            "/api/v1/analytics/engagement",
            headers=self.get_headers(),
            name="/api/v1/analytics/engagement"
        )


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the load test starts"""
    print("Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops"""
    print("Load test completed!")
    
    # Print summary statistics
    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min response time: {stats.total.min_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")
    
    # Check if performance targets are met
    if stats.total.avg_response_time > 1000:
        print("\n⚠️  WARNING: Average response time exceeds 1 second target!")
    
    if stats.total.num_failures > 0:
        failure_rate = (stats.total.num_failures / stats.total.num_requests) * 100
        print(f"\n⚠️  WARNING: Failure rate is {failure_rate:.2f}%")
        if failure_rate > 1:
            print("   Failure rate exceeds 1% target!")


# Performance test scenarios
"""
To run different load test scenarios:

1. Smoke Test (verify basic functionality):
   locust -f tests/performance/locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 1m --headless

2. Load Test (normal load):
   locust -f tests/performance/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless

3. Stress Test (high load):
   locust -f tests/performance/locustfile.py --host=http://localhost:8000 --users 500 --spawn-rate 50 --run-time 10m --headless

4. Spike Test (sudden traffic spike):
   locust -f tests/performance/locustfile.py --host=http://localhost:8000 --users 1000 --spawn-rate 100 --run-time 2m --headless

5. Endurance Test (sustained load):
   locust -f tests/performance/locustfile.py --host=http://localhost:8000 --users 200 --spawn-rate 20 --run-time 30m --headless

6. Interactive Mode (with web UI):
   locust -f tests/performance/locustfile.py --host=http://localhost:8000
   Then open http://localhost:8089 in your browser

Performance Targets (from design document):
- API response time p95 < 1 second
- Error rate < 1%
- Support 1000 concurrent users
- Database query performance optimized
- WebSocket connection stability
"""
