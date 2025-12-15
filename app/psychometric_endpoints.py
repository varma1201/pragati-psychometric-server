"""
Unified Psychometric Assessment API Endpoints

Handles both entrepreneur and mentor assessments based on user role
Routes to appropriate evaluator and profile manager
"""

import logging
from flask import jsonify, request
from .psychometric_evaluator import get_psychometric_evaluator
from .mentor_evaluator import get_mentor_evaluator
from .database_manager import get_database_manager
from .user_profile_manager import get_user_profile_manager
from bson import ObjectId

logger = logging.getLogger(__name__)


def _determine_user_type(data: dict, user_id: str = None) -> str:
    """
    Determine if user is entrepreneur or mentor based on request data or database
    
    Args:
        data: Request JSON data
        user_id: User ID to fetch role from database if not in request
        
    Returns:
        'mentor' or 'entrepreneur'
    """
    print("\n" + "🔍" * 35)
    print("📋 DETERMINING USER TYPE FROM REQUEST DATA")
    print("🔍" * 35)
    
    # Print all incoming data for debugging
    print(f"📦 Full Request Data: {data}")
    print(f"📦 Request Keys: {list(data.keys())}")
    print(f"👤 User ID: {user_id}")
    
    # Check explicit user_type field
    user_type = data.get('user_type', '').strip().lower() if data.get('user_type') else ''
    print(f"🏷️  user_type field: '{user_type}' (type: {type(data.get('user_type'))})")
    if user_type in ['mentor', 'internal_mentor']:
        print(f"✅ ✅ ✅ MATCHED! User is MENTOR (via 'user_type' field)")
        print("🔍" * 35 + "\n")
        return 'mentor'
    
    # Check user_role field
    user_role = data.get('user_role', '').strip().lower() if data.get('user_role') else ''
    print(f"🏷️  user_role field: '{user_role}' (type: {type(data.get('user_role'))})")
    if user_role in ['mentor', 'internal_mentor']:
        print(f"✅ ✅ ✅ MATCHED! User is MENTOR (via 'user_role' field)")
        print("🔍" * 35 + "\n")
        return 'mentor'
    
    # Check role field (alternative)
    role = data.get('role', '').strip().lower() if data.get('role') else ''
    print(f"🏷️  role field: '{role}' (type: {type(data.get('role'))})")
    if role in ['mentor', 'internal_mentor']:
        print(f"✅ ✅ ✅ MATCHED! User is MENTOR (via 'role' field)")
        print("🔍" * 35 + "\n")
        return 'mentor'
    
    # Check assessment_type field (in case it's passed)
    assessment_type = data.get('assessment_type', '').strip().lower() if data.get('assessment_type') else ''
    print(f"🏷️  assessment_type field: '{assessment_type}' (type: {type(data.get('assessment_type'))})")
    if assessment_type in ['mentor', 'internal_mentor']:
        print(f"✅ ✅ ✅ MATCHED! User is MENTOR (via 'assessment_type' field)")
        print("🔍" * 35 + "\n")
        return 'mentor'
    
    # If no role in request body, fetch from database
    if user_id:
        print(f"\n🔍 No role in request body - Fetching from database...")
        try:
            db_manager = get_database_manager()
            if db_manager:
                user = db_manager.db.users.find_one(
                    {"_id": ObjectId(user_id)},
                    {"role": 1}
                )
                
                if user:
                    db_role = user.get('role', '').strip().lower()
                    print(f"✅ Found user in database!")
                    print(f"🏷️  Database role: '{db_role}'")
                    
                    if db_role in ['mentor', 'internal_mentor']:
                        print(f"✅ ✅ ✅ MATCHED! User is MENTOR (from database)")
                        print("🔍" * 35 + "\n")
                        return 'mentor'
                    else:
                        print(f"📝 Database role '{db_role}' is not mentor role - defaulting to entrepreneur")
                else:
                    print(f"⚠️  User not found in database")
            else:
                print(f"⚠️  Database manager not available")
        except Exception as e:
            print(f"⚠️  Error fetching user from database: {e}")
            logger.warning(f"Error fetching user role from database: {e}")
            import traceback
            traceback.print_exc()
    
    # Default to entrepreneur
    print(f"⚠️ ⚠️ ⚠️  NO MENTOR ROLE FOUND - Defaulting to: ENTREPRENEUR")
    print(f"💡 TIP: Either send 'user_type'/'user_role'/'role' in request OR ensure user.role in DB = 'mentor'")
    print("🔍" * 35 + "\n")
    return 'entrepreneur'


def register_psychometric_endpoints(app):
    """Register unified psychometric assessment endpoints with Flask app"""
    
    @app.route('/api/psychometric/generate', methods=['POST'])
    def generate_psychometric_assessment():
        """
        Generate psychometric assessment (entrepreneur or mentor based on role)
        
        Request Body:
        {
            "num_questions": 20,
            "user_id": "user123",
            "user_type": "entrepreneur" | "mentor" | "internal_mentor",  # Optional
            "user_role": "entrepreneur" | "mentor" | "internal_mentor",  # Optional
            "role": "entrepreneur" | "mentor" | "internal_mentor",  # Optional
            "focus_domains": ["Technology", "Marketing"]  # Optional, for mentors
        }
        
        Note: If role fields are not provided, the system will fetch the user's role 
        from the database using user_id
        """
        try:
            print("\n" + "="*70)
            print("🎯 PSYCHOMETRIC ASSESSMENT GENERATION REQUEST")
            print("="*70)
            
            data = request.get_json() or {}
            print(f"📥 Raw Request Body: {data}")
            
            num_questions = data.get('num_questions', 20)
            user_id = data.get('user_id', None)
            focus_domains = data.get('focus_domains', None)
            
            # Determine user type with detailed logging (now passes user_id)
            user_type = _determine_user_type(data, user_id=user_id)
            
            print(f"\n{'='*70}")
            print(f"🎭 FINAL DETERMINED USER TYPE: **{user_type.upper()}**")
            print(f"{'='*70}")
            print(f"👤 User ID: {user_id}")
            print(f"📊 Questions to Generate: {num_questions}")
            print(f"🎯 Focus Domains: {focus_domains}")
            
            # Validate number of questions
            if not isinstance(num_questions, int) or num_questions < 5 or num_questions > 50:
                return jsonify({
                    "error": "Invalid number of questions",
                    "message": "num_questions must be between 5 and 50"
                }), 400
            
            logger.info(
                f"Generating {num_questions} {user_type} psychometric questions "
                f"for user: {user_id or 'anonymous'}"
            )
            
            # Route to appropriate evaluator based on user type
            print(f"\n🔀 ROUTING TO EVALUATOR...")
            if user_type == 'mentor':
                print(f"✅ ✅ ✅ Routing to: MENTOR EVALUATOR")
                evaluator = get_mentor_evaluator()
                print(f"✅ Mentor evaluator instance obtained")
                questions_data = evaluator.generate_questions(
                    num_questions=num_questions,
                    focus_domains=focus_domains
                )
                print(f"✅ MENTOR questions generated successfully!")
            else:  # entrepreneur
                print(f"✅ ✅ ✅ Routing to: ENTREPRENEUR EVALUATOR")
                evaluator = get_psychometric_evaluator()
                print(f"✅ Entrepreneur evaluator instance obtained")
                questions_data = evaluator.generate_questions(num_questions=num_questions)
                print(f"✅ ENTREPRENEUR questions generated successfully!")
            
            print(f"\n📝 Assessment Details:")
            print(f"   - Assessment ID: {questions_data.get('assessment_id')}")
            print(f"   - Title: {questions_data.get('title')}")
            print(f"   - Type: {questions_data.get('assessment_type', user_type)}")
            print(f"   - Total Questions: {questions_data.get('total_questions')}")
            
            # Optionally save to database
            if user_id:
                db_manager = get_database_manager()
                if db_manager:
                    try:
                        # Store the assessment for later retrieval
                        collection_name = (
                            'mentor_assessments' if user_type == 'mentor' 
                            else 'psychometric_assessments'
                        )
                        
                        print(f"\n💾 Saving to database collection: {collection_name}")
                        
                        assessment_record = {
                            "user_id": user_id,
                            "user_type": user_type,
                            "assessment_id": questions_data.get("assessment_id"),
                            "assessment_type": questions_data.get("assessment_type", user_type),
                            "questions_data": questions_data,
                            "status": "pending",
                            "generated_at": questions_data.get("generated_at")
                        }
                        
                        db_manager.db[collection_name].insert_one(assessment_record)
                        print(f"✅ {user_type.capitalize()} assessment saved to database")
                        logger.info(
                            f"{user_type.capitalize()} assessment saved to "
                            f"database for user {user_id}"
                        )
                    except Exception as e:
                        print(f"⚠️ WARNING: Failed to save assessment to DB: {e}")
                        logger.warning(f"Failed to save assessment to DB: {e}")
            
            print(f"\n✅ GENERATION COMPLETE - Returning response")
            print("="*70 + "\n")
            
            return jsonify({
                "success": True,
                "assessment_id": questions_data.get("assessment_id"),
                "assessment_type": user_type,
                "title": questions_data.get("title"),
                "description": questions_data.get("description"),
                "estimated_time_minutes": questions_data.get("estimated_time_minutes"),
                "total_questions": questions_data.get("total_questions"),
                "questions": questions_data.get("questions"),
                "generated_at": questions_data.get("generated_at")
            })
        
        except Exception as e:
            print(f"\n❌ ERROR in generate_psychometric_assessment:")
            print(f"   Error Type: {type(e).__name__}")
            print(f"   Error Message: {str(e)}")
            logger.error(f"Failed to generate assessment: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Failed to generate assessment",
                "details": str(e)
            }), 500
    
    
    @app.route('/api/psychometric/evaluate', methods=['POST'])
    def evaluate_psychometric_responses():
        """
        Evaluate psychometric assessment responses (entrepreneur or mentor)
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
            
            # Extract user_id first
            user_id = data.get('user_id', 'anonymous')
            
            # Step 2: Determine user type (now with database lookup)
            user_type = _determine_user_type(data, user_id=user_id)
            
            print(f"\n{'='*70}")
            print(f"🎭 USER TYPE FOR EVALUATION: **{user_type.upper()}**")
            print(f"{'='*70}")
            
            # Step 3: Validate required fields
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
            
            # Step 4: Extract data
            questions_data = data['questions_data']
            responses = data['responses']
            user_name = data.get('user_name', 'Anonymous User')
            assessment_id = data.get('assessment_id', questions_data.get('assessment_id', 'unknown'))
            mentor_background = data.get('mentor_background', None)
            
            print(f"\n👤 User ID: {user_id}")
            print(f"👤 User Name: {user_name}")
            print(f"👤 User Type: {user_type}")
            print(f"📝 Assessment ID: {assessment_id}")
            print(f"📊 Total Questions: {questions_data.get('total_questions', 0)}")
            print(f"✍️ Responses Received: {len(responses)}")
            
            logger.info(f"Evaluating {user_type} psychometric responses for user: {user_id}")
            logger.info(f"Received {len(responses)} responses")
            
            # Step 5: Route to appropriate evaluator
            print(f"\n🧠 Starting {user_type} evaluation process...")
            
            if user_type == 'mentor':
                print(f"✅ ✅ ✅ Using MENTOR EVALUATOR")
                evaluator = get_mentor_evaluator()
                print("✅ Mentor evaluator instance obtained")
                evaluation_result = evaluator.evaluate_responses(
                    questions_data, 
                    responses,
                    mentor_background
                )
            else:  # entrepreneur
                print(f"✅ ✅ ✅ Using ENTREPRENEUR EVALUATOR")
                evaluator = get_psychometric_evaluator()
                print("✅ Entrepreneur evaluator instance obtained")
                evaluation_result = evaluator.evaluate_responses(questions_data, responses)
            
            print(f"✅ Evaluation completed successfully")
            overall_score = evaluation_result.get('overall_score', evaluation_result.get('overall_mentor_score'))
            print(f"📊 Overall Score: {overall_score}/10")
            print(f"📈 Completion Rate: {evaluation_result.get('completion_rate')}%")
            
            # Add user information
            evaluation_result['user_id'] = user_id
            evaluation_result['user_name'] = user_name
            evaluation_result['user_type'] = user_type
            
            # Step 6: Save to database
            print(f"\n💾 Saving {user_type} evaluation to database...")
            db_manager = get_database_manager()
            evaluation_id = None
            
            if not db_manager:
                print("⚠️ WARNING: Database manager not available")
            else:
                print("✅ Database manager connected")
                
                try:
                    # 6.1: Save evaluation record to appropriate collection
                    collection_name = (
                        'mentor_evaluations' if user_type == 'mentor' 
                        else 'psychometric_evaluations'
                    )
                    
                    print(f"\n📝 Step 1: Saving to {collection_name}...")
                    
                    evaluation_record = {
                        "user_id": user_id,
                        "user_name": user_name,
                        "user_type": user_type,
                        "assessment_id": assessment_id,
                        "evaluation_result": evaluation_result,
                        "questions_answered": len(responses),
                        "overall_score": evaluation_result.get(
                            'overall_score', 
                            evaluation_result.get('overall_mentor_score')
                        ),
                        "completion_rate": evaluation_result.get('completion_rate'),
                        "evaluated_at": evaluation_result.get('evaluated_at')
                    }
                    
                    result = db_manager.db[collection_name].insert_one(evaluation_record)
                    evaluation_id = str(result.inserted_id)
                    print(f"✅ Evaluation saved with ID: {evaluation_id}")
                    logger.info(f"{user_type.capitalize()} evaluation saved with ID: {evaluation_id}")
                    
                    # 6.2: Update assessment status
                    print(f"\n📝 Step 2: Updating assessment status...")
                    assessment_collection = (
                        'mentor_assessments' if user_type == 'mentor' 
                        else 'psychometric_assessments'
                    )
                    
                    assessment_update_result = db_manager.db[assessment_collection].update_one(
                        {"assessment_id": assessment_id, "user_id": user_id},
                        {"$set": {"status": "completed", "evaluation_id": evaluation_id}}
                    )
                    print(f"✅ Assessment status updated (matched: {assessment_update_result.matched_count})")
                    
                    # 6.3: Update users collection
                    print(f"\n📝 Step 3: Updating users collection...")
                    from datetime import datetime, timezone
                    
                    overall_score = round(
                        evaluation_result.get('overall_score', evaluation_result.get('overall_mentor_score', 0)), 
                        2
                    )
                    completed_at = datetime.now(timezone.utc)
                    
                    print(f" - User ID: {user_id}")
                    print(f" - User Type: {user_type}")
                    print(f" - Score (rounded): {overall_score}")
                    print(f" - Completed At: {completed_at}")
                    
                    # Different fields based on user type
                    if user_type == 'mentor':
                        update_fields = {
                            "isPsychometricAnalysisDone": True,
                            "mentorPsychometricScore": overall_score,
                            "mentorPsychometricCompletedAt": completed_at,
                            "mentorTeachingStyle": evaluation_result.get('teaching_style', ''),
                            "mentorExpertiseDomains": evaluation_result.get('expertise_domains', []),
                            "mentorCapacity": evaluation_result.get('mentoring_capacity', '')
                        }
                        print(f"📝 Using MENTOR-specific fields for users collection")
                    else:  # entrepreneur
                        update_fields = {
                            "isPsychometricAnalysisDone": True,
                            "psychometricScore": overall_score,
                            "psychometricCompletedAt": completed_at
                        }
                        print(f"📝 Using ENTREPRENEUR-specific fields for users collection")
                    
                    user_update_result = db_manager.db.users.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$set": update_fields}
                    )
                    
                    if user_update_result.matched_count > 0:
                        print(f"✅ Users collection updated successfully")
                        print(f" - Matched: {user_update_result.matched_count}")
                        print(f" - Modified: {user_update_result.modified_count}")
                        logger.info(f"✅ Updated users collection for {user_type}: score={overall_score}")
                    else:
                        print(f"⚠️ WARNING: User {user_id} not found in users collection")
                        logger.warning(f"User {user_id} not found in users collection")
                    
                    # Verify update
                    print(f"\n🔍 Verifying user document update...")
                    updated_user = db_manager.db.users.find_one(
                        {"_id": ObjectId(user_id)},
                        {"_id": 1, "name": 1, "email": 1, "role": 1, **{k: 1 for k in update_fields.keys()}}
                    )
                    
                    if updated_user:
                        print(f"✅ User document verified:")
                        print(f" - _id: {updated_user.get('_id')}")
                        print(f" - name: {updated_user.get('name')}")
                        print(f" - role: {updated_user.get('role')}")
                        for key in update_fields.keys():
                            print(f" - {key}: {updated_user.get(key)}")
                    else:
                        print(f"⚠️ Could not verify - user not found")
                
                except Exception as e:
                    print(f"\n❌ ERROR saving to database: {e}")
                    logger.warning(f"Failed to save evaluation to DB: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Step 7: Create/update user profile
            print(f"\n👤 Creating/updating {user_type} profile...")
            profile_manager = get_user_profile_manager()
            user_profile = None
            
            try:
                user_profile = profile_manager.create_profile_from_psychometric(
                    user_id=user_id,
                    evaluation_result=evaluation_result,
                    user_type=user_type  # Pass user type to profile manager
                )
                print(f"✅ {user_type.capitalize()} profile created/updated successfully")
                logger.info(f"{user_type.capitalize()} profile created/updated for: {user_id}")
            except Exception as e:
                print(f"⚠️ WARNING: Failed to create {user_type} profile: {e}")
                logger.warning(f"Failed to create {user_type} profile: {e}")
            
            # Step 8: Prepare response
            print(f"\n📤 Preparing response...")
            response_data = {
                "success": True,
                "evaluation_id": evaluation_id,
                "user_type": user_type,
                "assessment_type": user_type,
                "profile_created": user_profile is not None,
                **evaluation_result
            }
            
            print(f"\n✅ {user_type.upper()} EVALUATION COMPLETE")
            print(f" - Overall Score: {evaluation_result.get('overall_score', evaluation_result.get('overall_mentor_score'))}/10")
            print(f" - Evaluation ID: {evaluation_id}")
            print(f" - Profile Created: {user_profile is not None}")
            print("="*70 + "\n")
            
            logger.info(f"{user_type.capitalize()} evaluation complete.")
            
            return jsonify(response_data)
        
        except Exception as e:
            print(f"\n❌ FATAL ERROR in evaluate_psychometric_responses:")
            print(f" Error Type: {type(e).__name__}")
            print(f" Error Message: {str(e)}")
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
        """Get all psychometric evaluations for a user (both types)"""
        try:
            db_manager = get_database_manager()
            if not db_manager:
                return jsonify({"error": "Database not available"}), 503
            
            limit = request.args.get('limit', 10, type=int)
            user_type_filter = request.args.get('user_type', 'all').lower()
            
            evaluations = []
            
            # Fetch entrepreneur evaluations
            if user_type_filter in ['all', 'entrepreneur']:
                entrepreneur_evals = list(
                    db_manager.db.psychometric_evaluations
                    .find({"user_id": user_id})
                    .sort("evaluated_at", -1)
                    .limit(limit)
                )
                for eval in entrepreneur_evals:
                    eval['_id'] = str(eval['_id'])
                    eval['type'] = 'entrepreneur'
                evaluations.extend(entrepreneur_evals)
            
            # Fetch mentor evaluations
            if user_type_filter in ['all', 'mentor']:
                mentor_evals = list(
                    db_manager.db.mentor_evaluations
                    .find({"user_id": user_id})
                    .sort("evaluated_at", -1)
                    .limit(limit)
                )
                for eval in mentor_evals:
                    eval['_id'] = str(eval['_id'])
                    eval['type'] = 'mentor'
                evaluations.extend(mentor_evals)
            
            # Sort combined results by date
            evaluations.sort(key=lambda x: x.get('evaluated_at', ''), reverse=True)
            evaluations = evaluations[:limit]
            
            types = list(set(eval.get('type') for eval in evaluations))
            
            return jsonify({
                "user_id": user_id,
                "evaluations": evaluations,
                "count": len(evaluations),
                "types": types
            })
        
        except Exception as e:
            logger.error(f"Failed to get user evaluations: {e}")
            return jsonify({
                "error": "Failed to retrieve evaluations",
                "details": str(e)
            }), 500
    
    
    @app.route('/api/psychometric/evaluation/<evaluation_id>', methods=['GET'])
    def get_evaluation_by_id(evaluation_id):
        """Get specific evaluation by ID (checks both collections)"""
        try:
            db_manager = get_database_manager()
            if not db_manager:
                return jsonify({"error": "Database not available"}), 503
            
            from bson import ObjectId
            
            # Try entrepreneur evaluations first
            evaluation = db_manager.db.psychometric_evaluations.find_one(
                {"_id": ObjectId(evaluation_id)}
            )
            
            if evaluation:
                evaluation['_id'] = str(evaluation['_id'])
                evaluation['type'] = 'entrepreneur'
                return jsonify(evaluation)
            
            # Try mentor evaluations
            evaluation = db_manager.db.mentor_evaluations.find_one(
                {"_id": ObjectId(evaluation_id)}
            )
            
            if evaluation:
                evaluation['_id'] = str(evaluation['_id'])
                evaluation['type'] = 'mentor'
                return jsonify(evaluation)
            
            return jsonify({"error": "Evaluation not found"}), 404
        
        except Exception as e:
            logger.error(f"Failed to get evaluation: {e}")
            return jsonify({
                "error": "Failed to retrieve evaluation",
                "details": str(e)
            }), 500
    
    
    @app.route('/api/profile/<user_id>', methods=['GET'])
    def get_user_profile(user_id):
        """Get user profile (entrepreneur or mentor or both)"""
        try:
            profile_type = request.args.get('profile_type', 'all').lower()
            profile_manager = get_user_profile_manager()
            
            response_data = {"user_id": user_id, "profile_types": []}
            
            # Get entrepreneur profile
            if profile_type in ['all', 'entrepreneur']:
                entrepreneur_profile = profile_manager.get_profile(user_id, user_type='entrepreneur')
                if entrepreneur_profile:
                    response_data['entrepreneur_profile'] = entrepreneur_profile
                    response_data['profile_types'].append('entrepreneur')
            
            # Get mentor profile
            if profile_type in ['all', 'mentor']:
                mentor_profile = profile_manager.get_profile(user_id, user_type='mentor')
                if mentor_profile:
                    response_data['mentor_profile'] = mentor_profile
                    response_data['profile_types'].append('mentor')
            
            if not response_data['profile_types']:
                return jsonify({
                    "error": "Profile not found",
                    "message": "User needs to complete psychometric assessment first"
                }), 404
            
            return jsonify(response_data)
        
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            return jsonify({
                "error": "Failed to retrieve profile",
                "details": str(e)
            }), 500
    
    
    @app.route('/api/profile/<user_id>/validation-context', methods=['GET'])
    def get_validation_context(user_id):
        """Get personalized validation context for a user"""
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
