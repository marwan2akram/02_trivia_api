import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_cors import CORS
import random
from models import setup_db, Question, Category
from random import shuffle


QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE
  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions



def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app)

  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  # CORS Headers
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,PATCH,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response
  '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
  #Create an endpoint to handle GET requests for categories
  @app.route('/categories')
  def retrieve_categories():
    #get category dictionary
    categories = {}
    category = Category.query.all()
    for x in category:
      categories[str(x.id)] = x.type
    return jsonify({
      'success': True,
      'categories': categories,
      'total_categories': len(categories)
    })

  '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
  #Create an endpoint to handle GET requests for questions
  @app.route('/questions')
  def retrieve_questions():
    #get all questions
    selection = Question.query.order_by(Question.id).all()
    #allow pagination
    current_questions = paginate_questions(request, selection)
    #create a category dictionary
    categories = {}
    category = Category.query.all()
    for x in category:
      categories[str(x.id)] = x.type
    c = [z.category for z in selection]

    if len(current_questions) == 0:
      abort(404)

    else:
      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(Question.query.all()),
        'categories': categories,
        # 'currentCategory': c
      })


  '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
  #Create an endpoint to DELETE question using a question ID
  @app.route('/questions/<int:question_id>/delete', methods=['DELETE'])
  def delete_question(question_id):
    try:
      #get a question by id or get 404 error
      question = Question.query.filter_by(id=question_id).first_or_404()
      # delete this question.

      question.delete()
      #length of the remaning questions after you delete the question
      length_of_questions_list=Question.query.count()

      return jsonify({
        'success': True,
        'deleted': question_id,
        'total_questions': length_of_questions_list
      })
    #if somthing happend abort 422 error
    except:
      abort(422)




  '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''
  #Create an endpoint to POST a new question
  @app.route('/questions/add', methods=['POST'])
  def create_question():
    #get the question body
    body = request.get_json()
    question = body.get('question', None)
    answer = body.get('answer', None)
    category = body.get('category', None)
    difficulty = body.get('difficulty', None)
    #create a new question
    try:
      question = Question(
        question=question,
        answer=answer,
        category=category,
        difficulty=difficulty
      )
      question.insert()

      return jsonify({
        'success': True,
        'created': question.id,
      })

    except:
      abort(422)





  '''
  @TODO:
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''

  #Create a POST endpoint to get questions based on a search term
  @app.route('/questions/search', methods=['POST'])
  def retrieve_questions_by_search():
    #get the search term
    search_term = request.get_json().get('searchTerm')
    #use ilike to search
    selection = Question.query.filter(Question.question.ilike('%'+search_term+'%')).all()
    #allow pagination
    current_questions = paginate_questions(request, selection)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(current_questions)
    })



  '''
  @TODO:
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''

  #Create a GET endpoint to get questions based on category.
  @app.route('/questions/<int:question_category>')
  def retrieve_questions_by_category(question_category):
    #get Question based on category
    selection = Question.query.filter_by(category=question_category).all()
    #allow pagination
    current_questions = paginate_questions(request, selection)
    #check if there are questions in this category or not
    if len(current_questions) == 0:
      abort(404)

    else:
      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(selection)
      })




  '''
  @TODO:
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''

  #Create a POST endpoint to get questions to play the quiz.
  @app.route('/quizzes', methods=['POST'])
  def retrieve_quizzes_by_category():
    try:
      # get the quiz category
      quizcategory = request.get_json().get('quiz_category_id')
      #get previous questions
      previous_questions = request.get_json().get('previous_questions')
      #check if the category is "All" or a  single category
      if quizcategory == 0:
        #check if there is previous questions or not
        if len(previous_questions) == 0:
          #get all the questions in the case of all category
          questions = Question.query.all()
          # get arandom  questions
          random_number = random.sample(range(0, len(questions)), 1)
          selection = questions[random_number[0]]
        else:
          # get arandom unrepeated questions
          questions = Question.query.filter(~Question.id.in_(previous_questions)).all()
          random_number = random.sample(range(0, len(questions)), 1)
          selection = questions[random_number[0]]
      else:
        #in case of single category
        if len(previous_questions) == 0:
          questions = Question.query.filter_by(category=quizcategory).all()
          random_number = random.sample(range(0, len(questions)), 1)
          selection = questions[random_number[0]]

        else:
          # get arandom unrepeated questions
          questions = Question.query.filter_by(category=quizcategory).filter(~Question.id.in_(previous_questions)).all()
          random_number = random.sample(range(0, len(questions)), 1)
          selection = questions[random_number[0]]
      #return the question
      return jsonify({
        'success': True,
        'question': selection.format()
      })
    except:
      abort(422)


  '''
  @TODO:
  Create error handlers for all expected errors
  including 404 and 422.
  '''
  #create error handler for 404 error
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "resource not found"
    }), 404

  # create error handler for 422 error
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False,
      "error": 422,
      "message": "unprocessable"
    }), 422

  # create error handler for 400 error
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False,
      "error": 400,
      "message": "bad request"
    }), 400

  # create error handler for 405 error
  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      "success": False,
      "error": 405,
      "message": "method not allowed"
    }), 405


  return app
