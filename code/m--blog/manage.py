from info import create_app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import db
from info import models

# 工厂模式
app = create_app("development")
# app = create_app("production")

manage = Manager(app)
Migrate(app, db)
manage.add_command("db", MigrateCommand)

if __name__ == '__main__':
    # print(app.url_map)
    manage.run()
