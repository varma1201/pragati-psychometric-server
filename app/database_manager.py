"""
Minimal MongoDB Database Manager for Pragati Psychometric Service

Handles psychometric assessments, evaluations, and user profiles
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB operations for psychometric data only"""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongodb_url = os.getenv("MONGODB_URL")
        self.database_name = os.getenv("DATABASE_NAME", "pragati_psychometric")

        if not self.mongodb_url:
            raise ValueError("MONGODB_URL environment variable is required")

        self.client = None
        self.db = None
        self._connect()

    def _connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(self.mongodb_url, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            logger.info(f"Connected to MongoDB: {self.database_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def save_assessment(
        self,
        user_id: str,
        assessment_data: Dict[str, Any]
    ) -> str:
        """
        Save a psychometric assessment (questions) to database

        Args:
            user_id: User identifier
            assessment_data: Assessment questions and metadata

        Returns:
            Assessment ID (MongoDB ObjectId as string)
        """
        try:
            assessment_doc = {
                "_id": ObjectId(),
                "user_id": user_id,
                "assessment_id": assessment_data.get("assessment_id"),
                "title": assessment_data.get("title", "Assessment"),
                "total_questions": assessment_data.get("total_questions", 0),
                "questions": assessment_data.get("questions", []),
                "created_at": datetime.now(timezone.utc),
                "status": "pending",
                "evaluation_id": None
            }

            collection = self.db.psychometric_assessments
            result = collection.insert_one(assessment_doc)
            assessment_id = str(result.inserted_id)
            logger.info(f"Saved assessment: {assessment_id} for user: {user_id}")
            return assessment_id

        except Exception as e:
            logger.error(f"Failed to save assessment: {e}")
            raise

    def save_evaluation(
        self,
        user_id: str,
        user_name: str,
        assessment_id: str,
        evaluation_result: Dict[str, Any]
    ) -> str:
        """
        Save a psychometric evaluation (responses + analysis) to database

        Args:
            user_id: User identifier
            user_name: User's name
            assessment_id: Related assessment ID
            evaluation_result: Complete evaluation result with scores and analysis

        Returns:
            Evaluation ID (MongoDB ObjectId as string)
        """
        try:
            evaluation_doc = {
                "_id": ObjectId(),
                "user_id": user_id,
                "user_name": user_name,
                "assessment_id": assessment_id,
                "overall_score": evaluation_result.get("overall_score", 0),
                "dimension_scores": evaluation_result.get("dimension_scores", {}),
                "strengths": evaluation_result.get("strengths", []),
                "areas_for_development": evaluation_result.get("areas_for_development", []),
                "personality_profile": evaluation_result.get("personality_profile", ""),
                "entrepreneurial_fit": evaluation_result.get("entrepreneurial_fit", {}),
                "recommendations": evaluation_result.get("recommendations", []),
                "completion_rate": evaluation_result.get("completion_rate", 0),
                "questions_answered": evaluation_result.get("questions_answered", 0),
                "created_at": datetime.now(timezone.utc),
                "status": "completed"
            }

            collection = self.db.psychometric_evaluations
            result = collection.insert_one(evaluation_doc)
            evaluation_id = str(result.inserted_id)
            logger.info(f"Saved evaluation: {evaluation_id} for user: {user_id}")
            return evaluation_id

        except Exception as e:
            logger.error(f"Failed to save evaluation: {e}")
            raise

    def save_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> bool:
        """
        Save or update user profile from psychometric evaluation

        Args:
            user_id: User identifier
            profile_data: User profile data

        Returns:
            True if successful
        """
        try:
            profile_doc = {
                "user_id": user_id,
                "user_name": profile_data.get("user_name", "Unknown"),
                "psychometric_scores": profile_data.get("psychometric_scores", {}),
                "overall_score": profile_data.get("overall_psychometric_score", 0),
                "entrepreneurial_fit": profile_data.get("entrepreneurial_fit", "Medium"),
                "fit_score": profile_data.get("fit_score", 50),
                "top_strengths": profile_data.get("top_strengths", []),
                "development_areas": profile_data.get("development_areas", []),
                "personality_profile": profile_data.get("personality_profile", ""),
                "created_at": profile_data.get("created_at"),
                "last_updated": datetime.now(timezone.utc),
                "profile_completeness": profile_data.get("profile_completeness", 0)
            }

            collection = self.db.user_profiles
            result = collection.update_one(
                {"user_id": user_id},
                {"$set": profile_doc},
                upsert=True
            )
            logger.info(f"Saved/updated profile for user: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")
            return False

    def get_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Get a psychometric assessment by ID"""
        try:
            collection = self.db.psychometric_assessments
            doc = collection.find_one({"_id": ObjectId(assessment_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            logger.error(f"Failed to get assessment: {e}")
            return None

    def get_evaluation(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Get a psychometric evaluation by ID"""
        try:
            collection = self.db.psychometric_evaluations
            doc = collection.find_one({"_id": ObjectId(evaluation_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            logger.error(f"Failed to get evaluation: {e}")
            return None

    def get_user_evaluations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all evaluations for a user"""
        try:
            collection = self.db.psychometric_evaluations
            docs = list(
                collection.find({"user_id": user_id})
                .sort("created_at", -1)
                .limit(limit)
            )
            for doc in docs:
                doc["_id"] = str(doc["_id"])
            return docs
        except Exception as e:
            logger.error(f"Failed to get user evaluations: {e}")
            return []

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            collection = self.db.user_profiles
            doc = collection.find_one({"user_id": user_id})
            if doc and "_id" in doc:
                doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None

    def update_assessment_status(
        self,
        assessment_id: str,
        user_id: str,
        evaluation_id: str
    ) -> bool:
        """Update assessment status after evaluation"""
        try:
            collection = self.db.psychometric_assessments
            collection.update_one(
                {"_id": ObjectId(assessment_id), "user_id": user_id},
                {"$set": {"status": "completed", "evaluation_id": evaluation_id}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update assessment status: {e}")
            return False

    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get or create global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
