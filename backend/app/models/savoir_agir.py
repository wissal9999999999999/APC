from app.extensions import db

class SavoirAgir(db.Model):
    __tablename__ = "savoir_agir"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    jalons = db.relationship("Jalon", backref="savoir_agir", cascade="all, delete")