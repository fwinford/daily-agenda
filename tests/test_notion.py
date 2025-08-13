import unittest
import os
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
import requests

from app.notion import query_due_on, get_db_title
from datetime import date

# Load environment variables for tests
load_dotenv()

class TestNotionAPI(unittest.TestCase):
    """Test Notion API functionality"""
    
    def setUp(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.test_db_map = {
            "example-database-id-1": {
                "name": "Tasks",
                "date_property": "Due Date",
                "fields": ["Priority", "Status"]
            },
            "example-database-id-2": {
                "name": "Projects", 
                "date_property": "Deadline",
                "fields": ["Category", "Owner"]
            }
        }
    
    @unittest.skipIf(not os.getenv("NOTION_TOKEN"), "NOTION_TOKEN not set")
    def test_notion_token_exists(self):
        """Test that Notion token is available"""
        self.assertIsNotNone(self.token)
        self.assertTrue(len(self.token) > 10)
    
    @unittest.skipIf(not os.getenv("NOTION_TOKEN"), "NOTION_TOKEN not set")
    @patch('requests.get')
    @patch('requests.post')
    def test_database_access(self, mock_post, mock_get):
        """Test that we can access both databases"""
        if not self.token:
            self.skipTest("No Notion token available")
        
        # Mock successful responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"object": "database"}
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"results": []}
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        
        for db_id, config in self.test_db_map.items():
            with self.subTest(database=config["name"]):
                # This is now mocked, so it will always succeed
                resp = requests.get(f"https://api.notion.com/v1/databases/{db_id}", 
                                  headers=headers, timeout=10)
                self.assertEqual(resp.status_code, 200, 
                               f"Failed to access {config['name']} database")
                
                # Test query functionality
                payload = {"page_size": 1}
                resp2 = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query",
                                    headers=headers, json=payload, timeout=10)
                self.assertEqual(resp2.status_code, 200,
                               f"Failed to query {config['name']} database")
    
    @patch('app.notion.requests.post')
    @unittest.skipIf(not os.getenv("NOTION_TOKEN"), "NOTION_TOKEN not set")
    def test_query_due_on(self, mock_post):
        """Test querying tasks due on a specific date"""
        if not self.token:
            self.skipTest("No Notion token available")
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{
                "id": "test-page-id",
                "url": "https://notion.so/test",
                "properties": {
                    "Name": {"title": [{"plain_text": "Test Task"}]},
                    "Due Date": {"date": {"start": "2025-08-13"}},
                    "Priority": {"select": {"name": "High"}}
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
            
        today = date.today()
        results = query_due_on(self.token, self.test_db_map, today)
        
        # Should return a list
        self.assertIsInstance(results, list)
        
        # Each result should have required fields
        for item in results:
            self.assertIn("title", item)
            self.assertIn("url", item) 
            self.assertIn("db_name", item)
            self.assertIn("fields", item)
    
    def test_query_due_on_no_token(self):
        """Test query_due_on with no token returns empty list"""
        results = query_due_on("", self.test_db_map, date.today())
        self.assertEqual(results, [])
        
        results = query_due_on(None, self.test_db_map, date.today())
        self.assertEqual(results, [])
    
    def test_query_due_on_no_db_map(self):
        """Test query_due_on with no database map returns empty list"""
        results = query_due_on("fake_token", {}, date.today())
        self.assertEqual(results, [])

if __name__ == "__main__":
    unittest.main()
