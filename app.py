from mydb import create_app
import os

app = create_app()

if __name__ == '__main__':
    print("app.py main")
    app.run(host='0.0.0.0')
