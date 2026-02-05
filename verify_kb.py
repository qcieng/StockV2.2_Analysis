import unittest
import os
import sys
import sqlite3
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import db_manager
import llm_analyzer

class TestKnowledgeBase(unittest.TestCase):
    def setUp(self):
        # Use a test DB
        self.original_db_name = db_manager.DB_NAME
        db_manager.DB_NAME = "test_knowledge.db"
        # Ensure clean state
        if os.path.exists(db_manager.DB_NAME):
            os.remove(db_manager.DB_NAME)
        db_manager.init_db()

    def tearDown(self):
        # Clean up test DB
        if os.path.exists(db_manager.DB_NAME):
            os.remove(db_manager.DB_NAME)
        db_manager.DB_NAME = self.original_db_name

    def test_01_add_and_search_term(self):
        """Test adding and searching knowledge terms."""
        print("\nTesting KB Add/Search...")
        term = "PMI"
        definition = "Purchasing Managers' Index"
        impact = "Leading indicator of economic health"
        category = "Macro"
        
        # Add
        success = db_manager.add_knowledge_term(term, definition, impact, category)
        self.assertTrue(success, "Should add term successfully")
        
        # Search exact
        results = db_manager.search_knowledge_terms("PMI")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "PMI")
        
        # Search partial
        results_partial = db_manager.search_knowledge_terms("Purchasing")
        self.assertEqual(len(results_partial), 1)
        
        # Search non-existent
        results_none = db_manager.search_knowledge_terms("XYZ")
        self.assertEqual(len(results_none), 0)
        print("✅ KB Add/Search passed.")

    def test_02_llm_generation_mock(self):
        """Test the LLM generation function structure (Mocked response)."""
        print("\nTesting LLM Knowledge Generation Logic...")
        # Since we can't easily mock OpenAI client here without heavy libs, 
        # we will test the JSON parsing logic if we were to extract it, 
        # but for now let's just ensure the function signature exists and handles empty input safely.
        
        # 1. Test with empty input
        # Note: This will likely fail or return empty list because no API key is provided in test env usually,
        # or it might try to call API if key is in env.
        # Let's just check if function is importable and callable.
        try:
            # We don't provide API key, so it should return [] or error handled gracefully
            res = llm_analyzer.generate_knowledge_base(["PMI"], provider="openai", api_key="invalid")
            self.assertIsInstance(res, list)
            print("✅ LLM Generation function handles invalid key gracefully.")
        except Exception as e:
            self.fail(f"LLM function raised exception: {e}")

if __name__ == '__main__':
    unittest.main()
