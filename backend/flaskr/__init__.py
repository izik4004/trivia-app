import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
        return response
    
    def pagination(request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        page_data = [data.format() for data in selection]
        curr_page = page_data[start:end]
        return curr_page
    
  
    @app.route('/categories', methods=['GET'])
    def categories():
        """Get all available categories"""

        get_categories = Category.query.all()

        if len(get_categories) == 0: abort(404)
        
        formatted_catgegory = \
        {category.format()['id'] : category.format()['type'] for category in get_categories}

        return jsonify({
            'categories': formatted_catgegory
        })
    
    @app.route('/questions', methods=['GET'])
    def questions():
     
        get_questions = Question.query.all()

        current_page = pagination(request, get_questions)

        if len(current_page) == 0: abort(404)

        get_categories = Category.query.all()

        return jsonify({
            'success': True,
            'questions': current_page,
            'totalQuestions': len(get_questions),
            'categories': {category.id: category.type for category in get_categories},
            'currentCategory': [category.type for category in get_categories]
        })

    
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def categories_questions(category_id):
        """get all the questions belonging to a specific category"""
        questions = Question.query.filter(Question.category == category_id)
        curr_page = pagination(request, questions)

        if len(curr_page) == 0: abort(404)

        current_Category = Category.query.filter(Category.id == category_id).one_or_none()

        return jsonify({
            'success': True,
            'questions': curr_page,
            'totalQuestions': questions.count(),
            'currentCategory': current_Category.format()['type']
        })
        
#  questios   

    @app.route('/questions', methods=['POST'])
    def add_question():
    
        body = request.get_json()

        question = body.get('question', None)
        answer = body.get('answer', None)
        difficulty = body.get('difficulty', None)
        category = body.get('category', None)

        if not (question and answer and difficulty and category): abort(400)

        try:
            quest = Question(
                question=question,
                answer=answer,
                difficulty=difficulty,
                category=category
            )

            quest.insert()

            return jsonify({
                'success': True,
                'created': quest.id
            }), 201

        except:
            abort(422)
            
            

    @app.route('/questions/search', methods=['POST'])
    def search():
        
        body = request.get_json()

        searchTerm = body.get('searchTerm', None)

        if not searchTerm: abort(400)

        try:
            quest = Question.query.filter(Question.question.ilike(f'%{searchTerm}%'))

            return jsonify({
                'success': True,
                'questions': [data.format() for data in quest],
                'totalQuestions': quest.count(),
                'currentCategory': None
            })
        except:
            abort(422)
            
            

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        """Delete a question from db and ensure it persists"""
        question = Question.query.filter(Question.id == question_id).one_or_none()

        if not question: abort(404)

        try:
            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except:
            abort(422)
            
            
    @app.route('/quizzes', methods=['POST'])
    def quizzes():
        body = request.get_json()

        quiz_category = body.get('quiz_category', None)
        previous_questions = body.get('previous_questions', None)

        if previous_questions is None: abort(400)

        try:
            quest = Question.query.filter(Question.id.notin_(previous_questions))
            question = None

            if quiz_category and quiz_category['id']:
                quest = quest.filter(Question.category == quiz_category['id'])

            if quest.count():
                question = quest[random.randint(0, quest.count() - 1)]
                question = question.format()

            return jsonify({
                'success': True,
                'question': question
            })
        except:
            abort(500)  
   
   
   
    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify({
                'success': False,
                'error': 400,
                'message': 'bad request',
            }),
            400
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({
                'success': False,
                'error': 404,
                'message': 'resource not found',
            }),
            404
        )

    @app.errorhandler(405)
    def not_allowed(error):
        return (
            jsonify({
                'success': False,
                'error': 405,
                'message': 'method not allowed',
            }),
            405
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({
                'success': False,
                'error': 422,
                'message': 'unprocessable',
            }),
            422
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        return (
            jsonify({
                'success': False,
                'error': 500,
                'message': 'internal server error',
            }),
            500
        )


    return app

