from flask import Flask
      
app = Flask(__name__)
app.config['SECRET_KEY'] = '490f5b3a23c26ce4d4457c046abc58d2'  
      
@app.route('/')
def home():
    return 'Welcome to Anecdotes!'
      
if __name__ == '__main__':
    app.run(debug=True)