"""
Psychometric Assessment API Endpoints
Provides routes for generating and evaluating psychometric assessments
"""

import logging
from flask import jsonify, request
from .psychometric_evaluator import get_psychometric_evaluator
from .database_manager import get_database_manager
from .user_profile_manager import get_user_profile_manager
from bson import ObjectId

logger = logging.getLogger(__name__)


def register_psychometric_endpoints(app):
    """Register psychometric assessment endpoints with Flask app"""
    
    @app.route('/api/psychometric/generate', methods=['POST'])
    def generate_psychometric_assessment():
        """
        Generate a new psychometric assessment with dynamic questions
        
        Request Body (optional):
        {
            "num_questions": 20,
            "user_id": "user123",
            "context": "Optional context about the person"
        }
        
        Response:
        {
            "assessment_id": "unique_id",
            "title": "Assessment title",
            "questions": [...],
            "metadata": {...}
        }
        """
        try:
            data = request.get_json() or {}
            num_questions = data.get('num_questions', 20)
            user_id = data.get('user_id', None)
            
            # Validate number of questions
            if not isinstance(num_questions, int) or num_questions < 5 or num_questions > 50:
                return jsonify({
                    "error": "Invalid number of questions",
                    "message": "num_questions must be between 5 and 50"
                }), 400
            
            logger.info(f"Generating {num_questions} psychometric questions for user: {user_id or 'anonymous'}")
            
            evaluator = get_psychometric_evaluator()
            questions_data = evaluator.generate_questions(num_questions=num_questions)
            
            # Optionally save to database
            if user_id:
                db_manager = get_database_manager()
                if db_manager:
                    try:
                        # Store the assessment for later retrieval
                        assessment_record = {
                            "user_id": user_id,
                            "assessment_id": questions_data.get("assessment_id"),
                            "questions_data": questions_data,
                            "status": "pending",
                            "generated_at": questions_data.get("generated_at")
                        }
                        db_manager.db.psychometric_assessments.insert_one(assessment_record)
                        logger.info(f"Assessment saved to database for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to save assessment to DB: {e}")
            
            return jsonify({
                "success": True,
                "assessment_id": questions_data.get("assessment_id"),
                "title": questions_data.get("title"),
                "description": questions_data.get("description"),
                "estimated_time_minutes": questions_data.get("estimated_time_minutes"),
                "total_questions": questions_data.get("total_questions"),
                "questions": questions_data.get("questions"),
                "generated_at": questions_data.get("generated_at")
            })
            
        except Exception as e:
            logger.error(f"Failed to generate assessment: {e}")
            return jsonify({
                "error": "Failed to generate assessment",
                "details": str(e)
            }), 500
    
    @app.route('/api/psychometric/evaluate', methods=['POST'])
    def evaluate_psychometric_responses():
        """
        Evaluate psychometric assessment responses

        Request Body:
        {
            "assessment_id": "unique_id",
            "user_id": "user123",
            "user_name": "John Doe",
            "questions_data": {...},  # Original questions
            "responses": {
                "q1": "A",
                "q2": "C",
                "q3": "B",
                ...
            }
        }

        Response:
        {
            "success": true,
            "evaluation_id": "unique_id",
            "overall_score": 7.5,
            "dimension_scores": {...},
            "personality_profile": "...",
            "strengths": [...],
            "areas_for_development": [...],
            "recommendations": [...],
            ...
        }
        """
        try:
            print("\n" + "="*70)
            print("🔍 PSYCHOMETRIC EVALUATION REQUEST RECEIVED")
            print("="*70)

            # Step 1: Parse request data
            data = request.get_json()
            print(f"📥 Request data received: {data is not None}")

            if not data:
                print("❌ ERROR: Empty request body")
                return jsonify({
                    "error": "Invalid request",
                    "message": "Request body is required"
                }), 400

            # Step 2: Validate required fields
            print("\n📋 Validating required fields...")
            required_fields = ['questions_data', 'responses']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                print(f"❌ ERROR: Missing fields: {missing_fields}")
                return jsonify({
                    "error": "Missing required fields",
                    "missing": missing_fields
                }), 400

            print("✅ All required fields present")

            # Step 3: Extract data
            questions_data = data['questions_data']
            responses = data['responses']
            user_id = data.get('user_id', 'anonymous')
            user_name = data.get('user_name', 'Anonymous User')
            assessment_id = data.get('assessment_id', questions_data.get('assessment_id', 'unknown'))

            print(f"\n👤 User ID: {user_id}")
            print(f"👤 User Name: {user_name}")
            print(f"📝 Assessment ID: {assessment_id}")
            print(f"📊 Total Questions in Data: {questions_data.get('total_questions', 0)}")
            print(f"✍️  Responses Received: {len(responses)}")
            print(f"📝 Response Keys: {list(responses.keys())[:5]}..." if len(responses) > 5 else f"📝 Response Keys: {list(responses.keys())}")

            logger.info(f"Evaluating psychometric responses for user: {user_id}")
            logger.info(f"Received {len(responses)} responses out of {questions_data.get('total_questions', 0)} questions")

            # Step 4: Evaluate responses
            print(f"\n🧠 Starting evaluation process...")
            evaluator = get_psychometric_evaluator()
            print("✅ Evaluator instance obtained")

            evaluation_result = evaluator.evaluate_responses(questions_data, responses)
            print(f"✅ Evaluation completed successfully")
            print(f"📊 Overall Score: {evaluation_result.get('overall_score')}/10")
            print(f"📈 Completion Rate: {evaluation_result.get('completion_rate')}%")

            # Add user information
            evaluation_result['user_id'] = user_id
            evaluation_result['user_name'] = user_name

            # Step 5: Save to database
            print(f"\n💾 Saving evaluation to database...")
            db_manager = get_database_manager()
            evaluation_id = None

            if not db_manager:
                print("⚠️  WARNING: Database manager not available")
            else:
                print("✅ Database manager connected")

                try:
                    # 5.1: Save evaluation record
                    print("\n📝 Step 1: Saving evaluation record to psychometric_evaluations...")
                    evaluation_record = {
                        "user_id": user_id,
                        "user_name": user_name,
                        "assessment_id": assessment_id,
                        "evaluation_result": evaluation_result,
                        "questions_answered": len(responses),
                        "overall_score": evaluation_result.get('overall_score'),
                        "completion_rate": evaluation_result.get('completion_rate'),
                        "evaluated_at": evaluation_result.get('evaluated_at')
                    }

                    result = db_manager.db.psychometric_evaluations.insert_one(evaluation_record)
                    evaluation_id = str(result.inserted_id)
                    print(f"✅ Evaluation saved with ID: {evaluation_id}")
                    logger.info(f"Evaluation saved to database with ID: {evaluation_id}")

                    # 5.2: Update assessment status
                    print(f"\n📝 Step 2: Updating assessment status...")
                    assessment_update_result = db_manager.db.psychometric_assessments.update_one(
                        {"assessment_id": assessment_id, "user_id": user_id},
                        {"$set": {"status": "completed", "evaluation_id": evaluation_id}}
                    )
                    print(f"✅ Assessment status updated (matched: {assessment_update_result.matched_count}, modified: {assessment_update_result.modified_count})")

                    # 5.3: Update users collection (FIXED - Only 3 fields)
                    print(f"\n📝 Step 3: Updating users collection...")
                    from datetime import datetime, timezone

                    # Round score to 2 decimal places to match expected format
                    overall_score = round(evaluation_result.get('overall_score', 0), 2)
                    psychometric_completed_at = datetime.now(timezone.utc)

                    print(f"   - User ID: {user_id}")
                    print(f"   - Score (rounded): {overall_score}")
                    print(f"   - Completed At: {psychometric_completed_at}")

                    user_update_result = db_manager.db.users.update_one(
                        {"_id": ObjectId(user_id)},
                        {
                            "$set": {
                                "isPsychometricAnalysisDone": True,
                                "psychometricScore": overall_score,
                                "psychometricCompletedAt": psychometric_completed_at
                            }
                        }
                    )

                    if user_update_result.matched_count > 0:
                        print(f"✅ Users collection updated successfully")
                        print(f"   - Matched: {user_update_result.matched_count}")
                        print(f"   - Modified: {user_update_result.modified_count}")
                        logger.info(f"✅ Updated users collection: isPsychometricAnalysisDone=True, score={overall_score}")
                    else:
                        print(f"⚠️  WARNING: User {user_id} not found in users collection")
                        logger.warning(f"User {user_id} not found in users collection")

                    # Verify update by fetching the user
                    print(f"\n🔍 Verifying user document update...")
                    updated_user = db_manager.db.users.find_one(
                        {"_id": user_id},
                        {"_id": 1, "name": 1, "email": 1, "isPsychometricAnalysisDone": 1, 
                         "psychometricScore": 1, "psychometricCompletedAt": 1}
                    )

                    if updated_user:
                        print(f"✅ User document verified:")
                        print(f"   - _id: {updated_user.get('_id')}")
                        print(f"   - name: {updated_user.get('name')}")
                        print(f"   - email: {updated_user.get('email')}")
                        print(f"   - isPsychometricAnalysisDone: {updated_user.get('isPsychometricAnalysisDone')}")
                        print(f"   - psychometricScore: {updated_user.get('psychometricScore')}")
                        print(f"   - psychometricCompletedAt: {updated_user.get('psychometricCompletedAt')}")
                    else:
                        print(f"⚠️  Could not verify - user not found")

                except Exception as e:
                    print(f"\n❌ ERROR saving to database: {e}")
                    logger.warning(f"Failed to save evaluation to DB: {e}")
                    import traceback
                    traceback.print_exc()

            # Step 6: Create/update user profile
            print(f"\n👤 Creating/updating user profile...")
            profile_manager = get_user_profile_manager()
            user_profile = None

            try:
                user_profile = profile_manager.create_profile_from_psychometric(
                    user_id=user_id,
                    evaluation_result=evaluation_result
                )
                print(f"✅ User profile created/updated successfully")
                logger.info(f"User profile created/updated for: {user_id}")
            except Exception as e:
                print(f"⚠️  WARNING: Failed to create user profile: {e}")
                logger.warning(f"Failed to create user profile: {e}")

            # Step 7: Prepare response
            print(f"\n📤 Preparing response...")
            response_data = {
                "success": True,
                "evaluation_id": evaluation_id,
                "profile_created": user_profile is not None,
                **evaluation_result
            }

            print(f"\n✅ EVALUATION COMPLETE")
            print(f"   - Overall Score: {evaluation_result.get('overall_score')}/10")
            print(f"   - Evaluation ID: {evaluation_id}")
            print(f"   - Profile Created: {user_profile is not None}")
            print("="*70 + "\n")

            logger.info(f"Evaluation complete. Overall score: {evaluation_result.get('overall_score')}/10")

            return jsonify(response_data)

        except Exception as e:
            print(f"\n❌ FATAL ERROR in evaluate_psychometric_responses:")
            print(f"   Error Type: {type(e).__name__}")
            print(f"   Error Message: {str(e)}")
            logger.error(f"Failed to evaluate responses: {e}")

            import traceback
            print("\n📚 Full Traceback:")
            traceback.print_exc()

            return jsonify({
                "error": "Failed to evaluate responses",
                "details": str(e)
            }), 500


    @app.route('/api/psychometric/evaluations/<user_id>', methods=['GET'])
    def get_user_evaluations(user_id):
        """
        Get all psychometric evaluations for a specific user
        
        Response:
        {
            "user_id": "user123",
            "evaluations": [...],
            "count": 5
        }
        """
        try:
            db_manager = get_database_manager()
            
            if not db_manager:
                return jsonify({
                    "error": "Database not available"
                }), 503
            
            limit = request.args.get('limit', 10, type=int)
            
            # Fetch evaluations
            evaluations = list(
                db_manager.db.psychometric_evaluations
                .find({"user_id": user_id})
                .sort("evaluated_at", -1)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for evaluation in evaluations:
                evaluation['_id'] = str(evaluation['_id'])
            
            return jsonify({
                "user_id": user_id,
                "evaluations": evaluations,
                "count": len(evaluations)
            })
            
        except Exception as e:
            logger.error(f"Failed to get user evaluations: {e}")
            return jsonify({
                "error": "Failed to retrieve evaluations",
                "details": str(e)
            }), 500
    
    @app.route('/api/psychometric/evaluation/<evaluation_id>', methods=['GET'])
    def get_evaluation_by_id(evaluation_id):
        """
        Get specific psychometric evaluation by ID
        
        Response:
        {
            "evaluation_id": "...",
            "evaluation_result": {...},
            ...
        }
        """
        try:
            db_manager = get_database_manager()
            
            if not db_manager:
                return jsonify({
                    "error": "Database not available"
                }), 503
            
            from bson import ObjectId
            
            # Fetch evaluation
            evaluation = db_manager.db.psychometric_evaluations.find_one(
                {"_id": ObjectId(evaluation_id)}
            )
            
            if not evaluation:
                return jsonify({
                    "error": "Evaluation not found"
                }), 404
            
            # Convert ObjectId to string
            evaluation['_id'] = str(evaluation['_id'])
            
            return jsonify(evaluation)
            
        except Exception as e:
            logger.error(f"Failed to get evaluation: {e}")
            return jsonify({
                "error": "Failed to retrieve evaluation",
                "details": str(e)
            }), 500
    
    @app.route('/api/profile/<user_id>', methods=['GET'])
    def get_user_profile(user_id):
        """
        Get user profile created from psychometric assessment
        
        Response:
        {
            "user_id": "user123",
            "entrepreneurial_fit": "High",
            "fit_score": 85,
            "strengths": [...],
            "weak_areas": [...],
            "psychometric_scores": {...},
            ...
        }
        """
        try:
            profile_manager = get_user_profile_manager()
            profile = profile_manager.get_profile(user_id)
            
            if not profile:
                return jsonify({
                    "error": "Profile not found",
                    "message": "User needs to complete psychometric assessment first"
                }), 404
            
            return jsonify(profile)
            
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            return jsonify({
                "error": "Failed to retrieve profile",
                "details": str(e)
            }), 500
    
    @app.route('/api/profile/<user_id>/validation-context', methods=['GET'])
    def get_validation_context(user_id):
        """
        Get personalized validation context for a user
        This context is used to customize idea validation
        
        Response:
        {
            "has_profile": true,
            "strengths": [...],
            "weak_areas": [...],
            "focus_areas": [...],
            "risk_tolerance": "High",
            ...
        }
        """
        try:
            profile_manager = get_user_profile_manager()
            context = profile_manager.get_personalized_validation_context(user_id)
            
            return jsonify(context)
            
        except Exception as e:
            logger.error(f"Failed to get validation context: {e}")
            return jsonify({
                "error": "Failed to retrieve validation context",
                "details": str(e)
            }), 500
    
    logger.info("Psychometric endpoints registered")

