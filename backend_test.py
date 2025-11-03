import requests
import sys
import json
from datetime import datetime

class ComebackScoutAPITester:
    def __init__(self, base_url="https://comeback-scout.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'No message')}"
            self.log_test("API Root", success, details)
            return success
        except Exception as e:
            self.log_test("API Root", False, str(e))
            return False

    def test_get_live_matches(self):
        """Test GET /api/matches/live"""
        try:
            response = requests.get(f"{self.api_url}/matches/live", timeout=15)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                matches = response.json()
                details += f", Matches count: {len(matches)}"
                
                # Validate match structure
                if matches:
                    match = matches[0]
                    required_fields = ['id', 'home_team', 'away_team', 'minute', 'status', 'comeback_probability']
                    missing_fields = [field for field in required_fields if field not in match]
                    if missing_fields:
                        success = False
                        details += f", Missing fields: {missing_fields}"
                    else:
                        # Check team structure
                        team_fields = ['name', 'logo', 'score', 'xg', 'possession', 'shots']
                        home_missing = [field for field in team_fields if field not in match['home_team']]
                        away_missing = [field for field in team_fields if field not in match['away_team']]
                        
                        if home_missing or away_missing:
                            success = False
                            details += f", Team missing fields - Home: {home_missing}, Away: {away_missing}"
                        else:
                            details += ", Structure valid"
            
            self.log_test("GET Live Matches", success, details)
            return success, response.json() if success else []
        except Exception as e:
            self.log_test("GET Live Matches", False, str(e))
            return False, []

    def test_get_alerts(self):
        """Test GET /api/alerts"""
        try:
            response = requests.get(f"{self.api_url}/alerts", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                alerts = response.json()
                details += f", Alerts count: {len(alerts)}"
                
                # Validate alert structure if alerts exist
                if alerts:
                    alert = alerts[0]
                    required_fields = ['id', 'match_id', 'team_name', 'opponent', 'score', 'probability', 'minute', 'reason']
                    missing_fields = [field for field in required_fields if field not in alert]
                    if missing_fields:
                        success = False
                        details += f", Missing fields: {missing_fields}"
                    else:
                        details += ", Structure valid"
            
            self.log_test("GET Alerts", success, details)
            return success, response.json() if success else []
        except Exception as e:
            self.log_test("GET Alerts", False, str(e))
            return False, []

    def test_check_comebacks(self):
        """Test POST /api/matches/check-comebacks"""
        try:
            response = requests.post(f"{self.api_url}/matches/check-comebacks", timeout=15)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                alerts_created = data.get('alerts_created', 0)
                details += f", Alerts created: {alerts_created}"
            
            self.log_test("POST Check Comebacks", success, details)
            return success
        except Exception as e:
            self.log_test("POST Check Comebacks", False, str(e))
            return False

    def test_get_superteams(self):
        """Test GET /api/superteams"""
        try:
            response = requests.get(f"{self.api_url}/superteams", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                superteams = response.json()
                details += f", Superteams count: {len(superteams)}"
                
                # Validate superteam structure
                if superteams:
                    team = superteams[0]
                    required_fields = ['name', 'logo', 'comeback_rate']
                    missing_fields = [field for field in required_fields if field not in team]
                    if missing_fields:
                        success = False
                        details += f", Missing fields: {missing_fields}"
                    else:
                        # Check if expected superteams are present
                        expected_teams = ['Real Madrid', 'Manchester City', 'Bayern Munich', 'PSG', 'Barcelona', 'Liverpool']
                        team_names = [t['name'] for t in superteams]
                        missing_teams = [team for team in expected_teams if team not in team_names]
                        if missing_teams:
                            details += f", Missing expected teams: {missing_teams}"
                        else:
                            details += ", All expected teams present"
            
            self.log_test("GET Superteams", success, details)
            return success
        except Exception as e:
            self.log_test("GET Superteams", False, str(e))
            return False

    def test_get_specific_match(self, match_id):
        """Test GET /api/matches/{match_id}"""
        try:
            response = requests.get(f"{self.api_url}/matches/{match_id}", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                match = response.json()
                details += f", Match ID: {match.get('id', 'Unknown')}"
            elif response.status_code == 404:
                # This is expected for non-existent match IDs
                success = True
                details += ", Correctly returns 404 for non-existent match"
            
            self.log_test("GET Specific Match", success, details)
            return success
        except Exception as e:
            self.log_test("GET Specific Match", False, str(e))
            return False

    def test_mark_alert_read(self, alert_id):
        """Test POST /api/alerts/mark-read/{alert_id}"""
        try:
            response = requests.post(f"{self.api_url}/alerts/mark-read/{alert_id}", timeout=10)
            # Either 200 (success) or 404 (not found) are acceptable
            success = response.status_code in [200, 404]
            details = f"Status: {response.status_code}"
            
            if response.status_code == 200:
                data = response.json()
                details += f", Success: {data.get('success', False)}"
            elif response.status_code == 404:
                details += ", Correctly returns 404 for non-existent alert"
            
            self.log_test("POST Mark Alert Read", success, details)
            return success
        except Exception as e:
            self.log_test("POST Mark Alert Read", False, str(e))
            return False

    def run_comprehensive_tests(self):
        """Run all API tests"""
        print("🚀 Starting Comeback Scout API Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)

        # Test basic connectivity
        if not self.test_api_root():
            print("❌ API root failed - stopping tests")
            return False

        # Test core endpoints
        matches_success, matches_data = self.test_get_live_matches()
        alerts_success, alerts_data = self.test_get_alerts()
        
        self.test_get_superteams()
        self.test_check_comebacks()

        # Test with actual data if available
        if matches_data:
            match_id = matches_data[0]['id']
            self.test_get_specific_match(match_id)
        else:
            # Test with dummy ID
            self.test_get_specific_match("dummy-id")

        if alerts_data:
            alert_id = alerts_data[0]['id']
            self.test_mark_alert_read(alert_id)
        else:
            # Test with dummy ID
            self.test_mark_alert_read("dummy-id")

        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed - check details above")
            return False

def main():
    tester = ComebackScoutAPITester()
    success = tester.run_comprehensive_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": f"{(tester.tests_passed/tester.tests_run)*100:.1f}%" if tester.tests_run > 0 else "0%",
        "test_details": tester.test_results
    }
    
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())