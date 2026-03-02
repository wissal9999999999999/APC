from app.extensions import db

class Jalon(db.Model):
    __tablename__ = "jalon"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    savoir_agir_id = db.Column(
        db.Integer,
        db.ForeignKey("savoir_agir.id"),
        nullable=False
    )