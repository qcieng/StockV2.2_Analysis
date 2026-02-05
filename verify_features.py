import unittest
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import db_manager
import data_fetcher
import config
import llm_analyzer

class TestStockFeatures(unittest.TestCase):
    def setUp(self):
        # Use a test DB
        self.original_db_name = db_manager.DB_NAME
        db_manager.DB_NAME = "test_predictions.db"
        db_manager.init_db()

    def tearDown(self):
        # Clean up test DB
        if os.path.exists("test_predictions.db"):
            os.remove("test_predictions.db")
        db_manager.DB_NAME = self.original_db_name

    def test_01_db_initialization(self):
        """Test if database and tables are created correctly."""
        print("\nTesting Database Initialization...")
        conn = sqlite3.connect(db_manager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
        table = cursor.fetchone()
        self.assertIsNotNone(table, "Table 'predictions' should exist")
        conn.close()
        print("✅ Database table 'predictions' exists.")

    def test_02_data_fetcher_name(self):
        """Test fetching stock name (Chinese)."""
        print("\nTesting Stock Name Fetching...")
        symbol = "sh600519"
        name = data_fetcher.get_stock_name(symbol)
        print(f"Fetched name for {symbol}: {name}")
        self.assertIn("茅台", name, "Should return Chinese name containing '茅台'")
        print("✅ Stock name fetching successful.")

    def test_03_prediction_workflow(self):
        """Test adding and retrieving predictions."""
        print("\nTesting Prediction Storage Workflow...")
        # Add prediction
        db_manager.add_prediction(
            stock_code="sh600519",
            stock_name="贵州茅台",
            horizon="30m",
            predicted_pct=1.5,
            basis="Test Basis"
        )
        
        # Verify it's pending
        pending = db_manager.get_pending_predictions("sh600519")
        self.assertTrue(len(pending) > 0, "Should have pending predictions")
        pred_id = pending[0][0]
        
        # Update result
        db_manager.update_prediction_result(pred_id, 1.0)
        
        # Verify it's no longer pending or status updated
        # (get_pending_predictions only returns pending, so it should be empty now for this id)
        # Let's check DB directly
        conn = sqlite3.connect(db_manager.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT status, actual_pct, error_pct FROM predictions WHERE id=?", (pred_id,))
        row = c.fetchone()
        conn.close()
        
        self.assertEqual(row[0], 'verified', "Status should be 'verified'")
        self.assertEqual(row[1], 1.0, "Actual pct should be 1.0")
        # Error: |1.5 - 1.0| = 0.5
        self.assertAlmostEqual(row[2], 0.5, delta=0.01, msg="Error pct should be 0.5")
        print("✅ Prediction storage and verification workflow successful.")

    def test_04_api_validation(self):
        """Test API Key validation logic (Mock or Real if key exists)."""
        print("\nTesting API Validation Logic...")
        # We won't test actual API call to save cost/time, but check the validation function structure
        # If config has a key, we can try it, but better to mock or just check if function runs
        # Let's just check if the function exists and handles bad input
        is_valid, msg = llm_analyzer.validate_api_key("openai", "sk-invalid-key")
        self.assertFalse(is_valid, "Should fail with invalid key")
        print("✅ API validation logic (negative test) successful.")

if __name__ == '__main__':
    unittest.main()
