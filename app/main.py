from flask import Flask
import demo

app = Flask(__name__)
app.register_blueprint(demo.bp)

if __name__ == '__main__':
    # Will make the server available externally as well
    app.run(host='0.0.0.0')
